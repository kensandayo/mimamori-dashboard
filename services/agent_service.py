# -*- coding: utf-8 -*-
"""AIエージェント: 自然言語から許可済みのシステム操作を選択・実行する。"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from services.ai_service import _get_client, _get_model_name, AIServiceError
from utils.config import COL_NAME, COL_RANK, COL_SCORE, COL_PRIORITY
from utils.parameter_loader import load_all_parameters, update_parameter
from utils.patterns import load_patterns, save_pattern
from utils.state import get_scored_data, get_weights, set_weights, apply_pattern

WRITE_TOOLS = {"create_evaluation_pattern", "apply_evaluation_pattern", "set_parameter_active"}

TOOLS = [
    {"type":"function","name":"get_ranking","description":"現在の評価設定で地区ランキングを取得する。『上位5地区』『閉じこもりが高い地区』のうち、総合着目度ランキングを求める場合に使う。","parameters":{"type":"object","properties":{"limit":{"type":"integer","minimum":1,"maximum":39}},"required":["limit"],"additionalProperties":False},"strict":True},
    {"type":"function","name":"compare_districts","description":"指定した複数地区の現在のデータ、総合スコア、順位を比較する。","parameters":{"type":"object","properties":{"districts":{"type":"array","items":{"type":"string"},"minItems":2,"maxItems":5}},"required":["districts"],"additionalProperties":False},"strict":True},
    {"type":"function","name":"list_evaluation_patterns","description":"保存済みの評価パターン一覧と重みを確認する。","parameters":{"type":"object","properties":{},"required":[],"additionalProperties":False},"strict":True},
    {"type":"function","name":"list_parameters","description":"登録済み評価項目の一覧、ID、現在の有効/無効、既定重みを確認する。評価パターンを作る前の確認にも使う。","parameters":{"type":"object","properties":{},"required":[],"additionalProperties":False},"strict":True},
    {"type":"function","name":"create_evaluation_pattern","description":"指定された観点の評価パターンを新規保存する。重みは0以上で指定し、実行時に合計1へ正規化される。書き込み操作なのでユーザー確認後に実行する。","parameters":{"type":"object","properties":{"name":{"type":"string"},"description":{"type":"string"},"weights":{"type":"array","minItems":1,"items":{"type":"object","properties":{"param_id":{"type":"string"},"weight":{"type":"number","minimum":0}},"required":["param_id","weight"],"additionalProperties":False}}},"required":["name","description","weights"],"additionalProperties":False},"strict":True},
    {"type":"function","name":"apply_evaluation_pattern","description":"保存済み評価パターンを現在の評価に適用する。書き込み操作なのでユーザー確認後に実行する。","parameters":{"type":"object","properties":{"name":{"type":"string"}},"required":["name"],"additionalProperties":False},"strict":True},
    {"type":"function","name":"set_parameter_active","description":"既存評価項目を着目度計算に使う/使わないへ変更する。書き込み操作なのでユーザー確認後に実行する。","parameters":{"type":"object","properties":{"param_id":{"type":"string"},"active":{"type":"boolean"}},"required":["param_id","active"],"additionalProperties":False},"strict":True},
]

AGENT_INSTRUCTIONS = """あなたは自治体向け地域見守りシステムを操作するAIエージェントです。
ユーザーが「作って」「追加して」「設定して」「適用して」「変更して」など、システム操作を明確に依頼した場合は、説明や提案だけで終了せず、必ず対応するfunction toolを呼び出してください。
一方、「追加できる？」「どういう案がいい？」のような質問・相談だけなら、勝手に変更操作を開始しないでください。

評価パターン作成では、入力コンテキストの available_parameters に登録済みパラメータID・表示名・現在値が既に含まれています。作成前に list_parameters を呼ぶ必要はありません。available_parameters を直接参照してください。
『介護・認知症・閉じこもりを重視した評価パターンを作って』のような依頼では、対象に合う登録済みparam_idを選び、合理的な重みを決め、そのターンで create_evaluation_pattern を呼び出してください。
重みは0以上で、対象項目だけを使ってください。アプリ側で合計1へ正規化します。
データの変更・設定変更は確認後にアプリ側が実行するため、あなた自身は実行済みと断定しないでください。
単なる地域分析・相談でツールが不要なら通常の日本語回答を返してください。
"""


def _is_create_pattern_command(question: str) -> bool:
    """評価パターンを『作成してほしい』という明示的な操作依頼だけを検出する。"""
    q = str(question or "").strip()
    if not re.search(r"(評価)?パターン", q):
        return False
    # 可否・相談だけは書き込み操作にしない
    if re.search(r"(できる[？?]?$|可能[？?]?$|どう(すれば|したら|いう)|案(は|を提案)|おすすめ|教えて)", q):
        return False
    return bool(re.search(r"(作って|作成して|追加して|登録して|保存して|つくって|作成お願い|追加お願い)", q))



def _parse_args(raw: Any) -> dict:
    if isinstance(raw, dict): return raw
    try: return json.loads(raw or "{}")
    except Exception: return {}


def plan_action(question: str, context: dict, history: Optional[List[dict]] = None) -> dict:
    client = _get_client()
    compact = {
        "question": question,
        "selected_context": context,
        "available_parameters": [{"param_id":p["param_id"],"label":p["label"],"active":p["active"],"weight":p["weight"]} for p in load_all_parameters()],
        "saved_patterns": list(load_patterns().keys()),
    }
    try:
        # 明示的な「評価パターンを作って」は、提案文だけで終わらないよう
        # create_evaluation_pattern を必須ツールとしてAIに選ばせる。
        # 重み自体はAIが available_parameters を見て決定する。
        if _is_create_pattern_command(question):
            create_tool = next(t for t in TOOLS if t.get("name") == "create_evaluation_pattern")
            response = client.responses.create(
                model=_get_model_name(), instructions=AGENT_INSTRUCTIONS,
                input=json.dumps(compact, ensure_ascii=False, default=str),
                tools=[create_tool], tool_choice="required", parallel_tool_calls=False,
                max_output_tokens=1200,
            )
        else:
            response = client.responses.create(
                model=_get_model_name(), instructions=AGENT_INSTRUCTIONS,
                input=json.dumps(compact, ensure_ascii=False, default=str),
                tools=TOOLS, tool_choice="auto", parallel_tool_calls=False,
                max_output_tokens=1200,
            )
    except Exception as e:
        raise AIServiceError(f"AIエージェントの判断中にエラーが発生しました：{e}") from e
    for item in getattr(response, "output", []) or []:
        if getattr(item, "type", "") == "function_call":
            name = getattr(item, "name", "")
            return {"kind":"tool","name":name,"arguments":_parse_args(getattr(item,"arguments","{}")),"requires_confirmation":name in WRITE_TOOLS}
    text = getattr(response, "output_text", "") or ""
    return {"kind":"answer","content":str(text).strip()}


def _param_map() -> Dict[str, dict]:
    return {p["param_id"]: p for p in load_all_parameters()}


def _normalize_param_text(value: Any) -> str:
    """項目ID/表示名の照合用。空白・記号差を吸収する。"""
    return re.sub(r"[\s・･_/／\-－ー]+", "", str(value or "")).lower()


def _resolve_param_id(value: Any) -> Optional[str]:
    """AIがIDではなく表示名を返しても、必ず既存パラメータへ紐付ける。"""
    raw = str(value or "").strip()
    pmap = _param_map()
    if raw in pmap:
        return raw

    norm = _normalize_param_text(raw)
    for pid, p in pmap.items():
        if norm in {_normalize_param_text(pid), _normalize_param_text(p.get("label", ""))}:
            return pid

    # よくある表記揺れ。新規項目は作らず、既存項目だけに解決する。
    aliases = {
        "介護リスク": "care_risk",
        "要介護リスク": "care_risk",
        "要支援リスク": "care_risk",
        "要支援要介護リスク": "care_risk",
        "認知症リスク": "dementia_risk",
        "閉じこもりリスク": "homebound_risk",
    }
    return aliases.get(norm)


def _dedupe_weight_items(items: Any) -> List[dict]:
    """同じ既存項目が複数回返っても1件だけにする。最初の指定を採用。"""
    result: List[dict] = []
    seen = set()
    for item in items or []:
        if not isinstance(item, dict):
            continue
        pid = _resolve_param_id(item.get("param_id"))
        if not pid or pid in seen:
            continue
        try:
            weight = float(item.get("weight", 0))
        except (TypeError, ValueError):
            continue
        if weight < 0:
            continue
        seen.add(pid)
        result.append({"param_id": pid, "weight": weight})
    return result


def describe_action(action: dict) -> str:
    name, a = action.get("name"), action.get("arguments", {})
    pmap = _param_map()
    if name == "create_evaluation_pattern":
        parts=[]
        for item in _dedupe_weight_items(a.get("weights", [])):
            pid = item["param_id"]
            w = item["weight"]
            parts.append(f"{pmap.get(pid,{}).get('label',pid)} {w*100:.0f}%")
        return f"評価パターン「{a.get('name','')}」を追加します。\n\n" + " / ".join(parts)
    if name == "apply_evaluation_pattern": return f"評価パターン「{a.get('name','')}」を現在の評価に適用します。"
    if name == "set_parameter_active":
        p=pmap.get(a.get("param_id"),{}); state="使用する" if a.get("active") else "使用しない"
        return f"「{p.get('label',a.get('param_id'))}」を着目度計算に{state}設定へ変更します。"
    return f"{name} を実行します。"


def execute_action(action: dict) -> str:
    name, a = action.get("name"), action.get("arguments", {})
    if name == "get_ranking":
        df=get_scored_data().head(int(a.get("limit",5)))
        return "\n".join([f"{int(r[COL_RANK])}位 {r[COL_NAME]}：着目指数 {float(r[COL_SCORE]):.1f}（{r[COL_PRIORITY]}）" for _,r in df.iterrows()])
    if name == "compare_districts":
        df=get_scored_data(); lines=[]
        for d in a.get("districts",[]):
            hit=df[df[COL_NAME].astype(str)==str(d)]
            if hit.empty: lines.append(f"{d}：地区が見つかりません")
            else:
                r=hit.iloc[0]; lines.append(f"{d}：{int(r[COL_RANK])}位、着目指数 {float(r[COL_SCORE]):.1f}（{r[COL_PRIORITY]}）")
        return "\n".join(lines)
    if name == "list_evaluation_patterns":
        pats=load_patterns(); return "\n".join([f"・{n}：{v.get('description','')}" for n,v in pats.items()]) or "保存済みパターンはありません。"
    if name == "list_parameters":
        return "\n".join([f"・{p['label']}（ID: {p['param_id']} / {'使用中' if p['active'] else '未使用'} / 既定重み {p['weight']}）" for p in load_all_parameters()])
    if name == "create_evaluation_pattern":
        pmap=_param_map()
        raw={}
        for item in _dedupe_weight_items(a.get("weights", [])):
            # 同じ意味の項目は既存param_idへ解決済み。重複登録しない。
            raw[item["param_id"]] = item["weight"]
        if not raw or sum(raw.values())<=0: raise AIServiceError("有効な評価項目の重みがありません。")
        total=sum(raw.values()); weights={k:v/total for k,v in raw.items()}
        # 指定外の有効項目は0として保存し、意図した項目だけのパターンにする
        full={p['param_id']:weights.get(p['param_id'],0.0) for p in load_all_parameters() if p['active'] or p['param_id'] in weights}
        save_pattern(str(a.get("name") or "AI作成パターン"), full, str(a.get("description") or "AI相談から作成"))
        return f"評価パターン「{a.get('name')}」を保存しました。設定画面やAI相談から適用できます。"
    if name == "apply_evaluation_pattern":
        if not apply_pattern(str(a.get("name",""))): raise AIServiceError("指定された評価パターンが見つかりません。")
        return f"評価パターン「{a.get('name')}」を適用しました。ランキング等に反映されます。"
    if name == "set_parameter_active":
        pid=str(a.get("param_id","")); pmap=_param_map()
        if pid not in pmap: raise AIServiceError("指定された評価項目が見つかりません。")
        update_parameter(pid, active=bool(a.get("active")))
        # session_state重み同期は次回init_stateで行われる
        return f"「{pmap[pid]['label']}」の評価利用設定を変更しました。"
    raise AIServiceError("未対応の操作です。")
