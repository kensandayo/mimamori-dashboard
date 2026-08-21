# -*- coding: utf-8 -*-
"""
services/ai_service.py
-------------------------
「AI相談」画面が使う、AIとのやり取りをまとめたモジュールです。

このファイルが担当すること:
1. 選択された地区のデータだけを、AIに渡す「文脈（コンテキスト）」に変換する
   （CSV全体は渡さない。評価項目はマスタから動的に取得するため、項目が
   増減しても自動的に反映される）
2. AIの振る舞いルール（自治体職員向け・推測禁止など）を定めたシステムプロンプト
3. OpenAI APIを呼び出して回答を受け取る処理（コスト最小化の設定を含む）
4. APIキー未設定・課金不足・通信エラー・タイムアウトを、画面側が分かりやすく
   表示できる形にする
5. 同じ地区・同じ質問（会話1問目）に対するキャッシュ（API再呼び出しの削減）

1日の利用回数の管理は services/usage_tracker.py に分離しています。
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Dict, List, Optional, TypedDict

import pandas as pd

from utils.config import COL_NAME, COL_RANK, COL_SCORE, COL_PRIORITY
from utils.parameter_loader import load_active_parameters
from utils.scoring import generate_analysis_comments

try:
    from openai import (
        OpenAI, APIConnectionError, APITimeoutError, RateLimitError, AuthenticationError,
    )
    _OPENAI_IMPORT_ERROR: Optional[Exception] = None
except ImportError as e:  # pragma: no cover
    OpenAI = None  # type: ignore
    APIConnectionError = APITimeoutError = RateLimitError = AuthenticationError = Exception  # type: ignore
    _OPENAI_IMPORT_ERROR = e

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class AIServiceError(Exception):
    """AIサービス関連の共通エラーです。画面側はこれをキャッチしてst.errorで表示します。"""


class AIServiceConfigError(AIServiceError):
    """APIキー未設定など、設定不備が原因のエラーです。"""


class ChatTurn(TypedDict):
    role: str
    content: str


# ============================================================
# 設定（コスト最小化のための定数。変更したい場合はここだけ直せばよい）
# ============================================================
DEFAULT_MODEL = "gpt-4o-mini"
MAX_OUTPUT_TOKENS = 400
TEMPERATURE = 0.2
REQUEST_TIMEOUT_SECONDS = 30
DEFAULT_DAILY_LIMIT = 50


def _get_model_name() -> str:
    return os.getenv("OPENAI_MODEL", DEFAULT_MODEL)


def get_daily_limit() -> int:
    raw = os.getenv("DAILY_AI_LIMIT")
    if raw is None:
        return DEFAULT_DAILY_LIMIT
    try:
        return int(raw)
    except ValueError:
        return DEFAULT_DAILY_LIMIT


def _get_client() -> "OpenAI":
    if OpenAI is None:
        raise AIServiceConfigError(
            "openai ライブラリがインストールされていません。"
            "「pip install -r requirements.txt」を実行してください。"
        ) from _OPENAI_IMPORT_ERROR
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise AIServiceConfigError(
            "OPENAI_API_KEY が設定されていません。"
            "プロジェクト直下に .env ファイルを作成し、"
            "OPENAI_API_KEY=sk-xxxxx のようにAPIキーを設定してください。"
        )
    return OpenAI(api_key=api_key)


# ============================================================
# AIの振る舞いルール（システムプロンプト。短いほどコスト削減になる）
# ============================================================
SYSTEM_PROMPT = """あなたは自治体職員向け「地域見守り意思決定支援システム」のAI相談機能です。
必ず守ること：
・渡された地区データの範囲内でのみ回答し、推測で情報を作らない
・データに無いことは「判断できません」と答える
・個人への対応は断定しない。地区単位の参考情報として回答する
・施策の必要性は断定せず、参考情報・確認候補として述べる

回答は300〜500文字程度で簡潔にし、冗長な説明はしないこと。
次の見出しで構成すること（注意事項は必要な場合のみ最後に加える）。
【結論】
【根拠】
【考えられる対応】
"""


# ============================================================
# 地区データ → AIに渡す文脈（コンテキスト）の変換
# ============================================================
def build_district_context(row: pd.Series, scored_df: pd.DataFrame) -> dict:
    """1地区分のデータを、AIに渡すための辞書に変換します。評価項目はマスタから動的に取得します。"""
    parameters = load_active_parameters()
    indicators = {p["label"]: row[p["key"]] for p in parameters}
    return {
        "地区名": row[COL_NAME],
        "順位": f"{int(row[COL_RANK])}位 / 全{len(scored_df)}地区",
        "総合スコア": round(float(row[COL_SCORE]), 1),
        "優先度": row[COL_PRIORITY],
        "評価項目": indicators,
        "自動分析コメント": generate_analysis_comments(row, scored_df, parameters),
    }


def build_prompt_context(
    target_row: pd.Series, scored_df: pd.DataFrame, compare_row: Optional[pd.Series] = None,
) -> dict:
    context = {"対象地区": build_district_context(target_row, scored_df)}
    if compare_row is not None:
        context["比較地区"] = build_district_context(compare_row, scored_df)
    return context


# ============================================================
# AIへの問い合わせ
# ============================================================
def ask_ai(question: str, context: dict, history: Optional[List[ChatTurn]] = None) -> str:
    client = _get_client()
    history = history or []

    messages: List[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend({"role": turn["role"], "content": turn["content"]} for turn in history)

    user_content = (
        "以下はシステムから渡される地区データです。この範囲の情報のみを事実として"
        "回答してください。ここに無い情報は「分からない」としてください。\n\n"
        f"【地区データ】\n```json\n{json.dumps(context, ensure_ascii=False, indent=2)}\n```\n\n"
        f"【質問】\n{question}"
    )
    messages.append({"role": "user", "content": user_content})

    try:
        response = client.chat.completions.create(
            model=_get_model_name(), messages=messages,
            temperature=TEMPERATURE, max_tokens=MAX_OUTPUT_TOKENS, timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except AuthenticationError as e:
        raise AIServiceConfigError("APIキーが正しくありません。.envのOPENAI_API_KEYを確認してください。") from e
    except RateLimitError as e:
        raise AIServiceError(
            "APIの利用上限、またはOpenAIアカウントの課金残高不足の可能性があります。"
            "OpenAIアカウントの請求設定をご確認ください。"
        ) from e
    except APITimeoutError as e:
        raise AIServiceError("AIサーバーへの応答がタイムアウトしました。しばらくしてから再度お試しください。") from e
    except APIConnectionError as e:
        raise AIServiceError("通信エラーが発生しました。ネットワーク接続をご確認のうえ、再度お試しください。") from e
    except Exception as e:  # noqa: BLE001
        raise AIServiceError(f"AIへの問い合わせ中にエラーが発生しました：{e}") from e

    answer = response.choices[0].message.content
    if not answer:
        raise AIServiceError("AIから空の回答が返されました。もう一度お試しください。")
    return answer


# ============================================================
# キャッシュ（同じ地区・同じ質問なら再度APIを呼ばない。会話1問目のみ対象）
# ============================================================
_answer_cache: Dict[str, str] = {}


def _build_cache_key(question: str, context: dict) -> str:
    normalized_context = json.dumps(context, ensure_ascii=False, sort_keys=True)
    raw_key = f"{question.strip()}||{normalized_context}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def ask_ai_cached(question: str, context: dict, history: Optional[List[ChatTurn]] = None) -> "tuple[str, bool]":
    """ask_ai() のキャッシュ付きラッパー。戻り値は (回答, キャッシュ利用有無)。"""
    history = history or []
    if not history:
        cache_key = _build_cache_key(question, context)
        if cache_key in _answer_cache:
            return _answer_cache[cache_key], True
        answer = ask_ai(question, context, history=[])
        _answer_cache[cache_key] = answer
        return answer, False
    return ask_ai(question, context, history=history), False
