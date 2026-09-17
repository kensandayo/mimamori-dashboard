# -*- coding: utf-8 -*-
"""
services/ai_service.py
----------------------
地域データをOpenAI APIに渡し、自治体職員向けに回答するサービス層。

v11:
- NumPy / pandas 型をJSON化できない問題を修正
- OpenAI Responses APIを使用
- ローカル .env と Streamlit Cloud Secrets の両方に対応
- APIキーをコード・GitHubへ保存しない
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Dict, List, Optional, TypedDict, Any

import numpy as np
import pandas as pd

from utils.config import COL_NAME, COL_RANK, COL_SCORE, COL_PRIORITY
from utils.parameter_loader import load_active_parameters, load_all_parameters
from utils.scoring import generate_analysis_comments

try:
    import streamlit as st
except ImportError:  # pragma: no cover
    st = None  # type: ignore

try:
    from openai import (
        OpenAI,
        APIConnectionError,
        APITimeoutError,
        RateLimitError,
        AuthenticationError,
        BadRequestError,
    )
    _OPENAI_IMPORT_ERROR: Optional[Exception] = None
except ImportError as e:  # pragma: no cover
    OpenAI = None  # type: ignore
    APIConnectionError = APITimeoutError = RateLimitError = AuthenticationError = BadRequestError = Exception  # type: ignore
    _OPENAI_IMPORT_ERROR = e

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class AIServiceError(Exception):
    pass


class AIServiceConfigError(AIServiceError):
    pass


class ChatTurn(TypedDict):
    role: str
    content: str


DEFAULT_MODEL = "gpt-5.6-luna"
MAX_OUTPUT_TOKENS = 1500
REQUEST_TIMEOUT_SECONDS = 45
DEFAULT_DAILY_LIMIT = 50


def _read_secret(name: str) -> Optional[str]:
    """環境変数 → Streamlit Secrets の順で安全に設定値を取得する。"""
    value = os.getenv(name)
    if value:
        return value

    if st is not None:
        try:
            secret_value = st.secrets.get(name)
            if secret_value is not None:
                return str(secret_value)
        except Exception:
            pass
    return None


def _get_model_name() -> str:
    return _read_secret("OPENAI_MODEL") or DEFAULT_MODEL


def get_daily_limit() -> int:
    raw = _read_secret("DAILY_AI_LIMIT")
    if raw is None:
        return DEFAULT_DAILY_LIMIT
    try:
        return max(1, int(raw))
    except (TypeError, ValueError):
        return DEFAULT_DAILY_LIMIT


def is_ai_configured() -> bool:
    return bool(_read_secret("OPENAI_API_KEY"))


def _get_client() -> "OpenAI":
    if OpenAI is None:
        raise AIServiceConfigError(
            "openaiライブラリがインストールされていません。"
            "pip install -r requirements.txt を実行してください。"
        ) from _OPENAI_IMPORT_ERROR

    api_key = _read_secret("OPENAI_API_KEY")
    if not api_key:
        raise AIServiceConfigError(
            "OPENAI_API_KEY が設定されていません。"
            "ローカルでは .env、Streamlit Cloudでは Settings → Secrets に設定してください。"
        )
    return OpenAI(api_key=api_key, timeout=REQUEST_TIMEOUT_SECONDS)


SYSTEM_PROMPT = """あなたは自治体職員向け「地域見守り・施策検討支援システム」のAI相談機能です。
次のルールを必ず守ってください。
- 提供された地区データだけを事実として扱い、存在しない数値や制度を作らない。
- データだけでは判断できないことは「このデータだけでは判断できません」と明示する。
- スコアや順位は行政サービスの良否を断定するものではなく、確認候補を探す参考指標として扱う。
- 「この施策を導入すべき」と断定しない。職員の検討材料として説明する。
- 個人単位の判断や対応を行わない。
- 元データと評価スコアを混同しない。
回答は日本語で簡潔にし、原則として次の順で書いてください。
【結論】
【データから確認できること】
【検討時に追加で確認したいこと】
"""


def _json_default(value: Any) -> Any:
    """NumPy / pandas値をJSON標準型へ変換する。"""
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        value = float(value)
        return None if np.isnan(value) else value
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if value is pd.NA:
        return None
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return str(value)


def _json_dumps(value: Any, *, indent: Optional[int] = None, sort_keys: bool = False) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        indent=indent,
        sort_keys=sort_keys,
        default=_json_default,
        allow_nan=False,
    )


def _safe_scalar(value: Any) -> Any:
    """Seriesから取り出した値をコンテキスト用の標準Python型にする。"""
    if value is None or value is pd.NA:
        return None
    if isinstance(value, float) and np.isnan(value):
        return None
    try:
        converted = _json_default(value)
        return converted
    except Exception:
        return str(value)


def build_district_context(row: pd.Series, scored_df: pd.DataFrame) -> dict:
    # AI相談では、着目度計算に使う項目だけでなく「地域カルテ」の参考指標も渡す。
    # スコア計算はactive=Trueの項目だけ、AIの説明材料は全登録項目を対象とする。
    parameters = load_all_parameters()

    indicators = {}
    for p in parameters:
        key = p["key"]
        raw_value = _safe_scalar(row.get(key))
        indicators[p["label"]] = {
            "元データ": raw_value,
            "単位": p.get("unit", ""),
            "意味": p.get("description", ""),
            "評価方向": "高いほど課題" if p.get("risk_direction") == "positive" else "高いほど良好",
            "着目度計算に使用": bool(p.get("active", False)),
            "データ種別": p.get("data_type", ""),
            "対象年度": p.get("target_year", ""),
            "出典": p.get("source", ""),
        }

    score_parameters = [p for p in parameters if p.get("active", False)]
    comments = generate_analysis_comments(row, scored_df, score_parameters)
    if not isinstance(comments, (list, tuple)):
        comments = [str(comments)]

    return {
        "地区名": str(row[COL_NAME]),
        "順位": f"{int(row[COL_RANK])}位 / 全{len(scored_df)}地区",
        "総合スコア": round(float(row[COL_SCORE]), 1),
        "着目度": str(row[COL_PRIORITY]),
        "評価項目": indicators,
        "自動分析コメント": [str(x) for x in comments],
        "注意": "総合スコア・順位は確認候補を探す参考指標であり、行政サービスの良否を断定するものではありません。",
    }


def build_prompt_context(
    target_row: pd.Series,
    scored_df: pd.DataFrame,
    compare_row: Optional[pd.Series] = None,
) -> dict:
    context = {"対象地区": build_district_context(target_row, scored_df)}
    if compare_row is not None:
        context["比較地区"] = build_district_context(compare_row, scored_df)
    return context


def _build_input(question: str, context: dict, history: List[ChatTurn]) -> list[dict]:
    input_items: list[dict] = []

    # 過去の会話は最大6メッセージ程度を想定。役割はuser/assistantのみ。
    for turn in history:
        role = "assistant" if turn.get("role") == "assistant" else "user"
        input_items.append({"role": role, "content": str(turn.get("content", ""))})

    context_json = _json_dumps(context, indent=2)
    user_text = (
        "以下の地区データを根拠に回答してください。"
        "データにない事実を補わないでください。\n\n"
        f"【地区データ】\n{context_json}\n\n"
        f"【質問】\n{question.strip()}"
    )
    input_items.append({"role": "user", "content": user_text})
    return input_items


def ask_ai(question: str, context: dict, history: Optional[List[ChatTurn]] = None) -> str:
    client = _get_client()
    history = history or []

    try:
        response = client.responses.create(
            model=_get_model_name(),
            instructions=SYSTEM_PROMPT,
            input=_build_input(question, context, history),
            max_output_tokens=MAX_OUTPUT_TOKENS,
        )
    except AuthenticationError as e:
        raise AIServiceConfigError(
            "OpenAI APIキーが正しくありません。OPENAI_API_KEYを確認してください。"
        ) from e
    except RateLimitError as e:
        raise AIServiceError(
            "OpenAI APIの利用上限または課金残高を確認してください。"
        ) from e
    except APITimeoutError as e:
        raise AIServiceError(
            "AIの応答がタイムアウトしました。少し待ってから再度お試しください。"
        ) from e
    except APIConnectionError as e:
        raise AIServiceError(
            "OpenAI APIとの通信に失敗しました。ネットワーク接続を確認してください。"
        ) from e
    except BadRequestError as e:
        raise AIServiceError(
            f"AIへのリクエスト内容に問題があります：{e}"
        ) from e
    except Exception as e:  # noqa: BLE001
        raise AIServiceError(f"AIへの問い合わせ中にエラーが発生しました：{e}") from e

    answer = getattr(response, "output_text", None)
    if not answer or not str(answer).strip():
        raise AIServiceError("AIから回答本文を取得できませんでした。もう一度お試しください。")
    return str(answer).strip()


_answer_cache: Dict[str, str] = {}


def _build_cache_key(question: str, context: dict) -> str:
    normalized_context = _json_dumps(context, sort_keys=True)
    raw_key = f"{question.strip()}||{normalized_context}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def ask_ai_cached(
    question: str,
    context: dict,
    history: Optional[List[ChatTurn]] = None,
) -> "tuple[str, bool]":
    history = history or []
    if not history:
        cache_key = _build_cache_key(question, context)
        if cache_key in _answer_cache:
            return _answer_cache[cache_key], True
        answer = ask_ai(question, context, history=[])
        _answer_cache[cache_key] = answer
        return answer, False

    return ask_ai(question, context, history=history), False
