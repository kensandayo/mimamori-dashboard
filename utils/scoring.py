# -*- coding: utf-8 -*-
"""
scoring.py
------------
地区ごとの「見守りニーズ総合スコア」や、施策検討に使う各種指標を計算するモジュールです。

【v8での変更点】
以前は高齢化率・単身高齢者割合・医療アクセス・公共交通の4指標を関数の中で
名指しして扱っていましたが、今後は評価項目が増減する前提のため、
すべての関数が「parameters（評価項目のリスト）」を引数として受け取り、
その中身が何であっても同じロジックで動くようにしています
（parametersを省略した場合は utils.parameter_loader.load_active_parameters() を使います）。

推奨施策（旧: generate_recommendations）も、以前は
「高齢化率が高ければこの施策」のようなif文を並べていましたが、
今後は data/policy_master.csv の内容から動的に組み立てます
（get_policy_candidates を参照）。
"""

from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd

from utils.config import (
    COL_NAME, COL_SCORE, COL_RANK, COL_PRIORITY,
    PRIORITY_HIGH, PRIORITY_MID, PRIORITY_LOW,
    PRIORITY_HIGH_QUANTILE, PRIORITY_LOW_QUANTILE,
)
from utils.parameter_loader import load_active_parameters
from utils.policy_loader import get_policies_for_param

Weights = Dict[str, float]
Parameters = List[dict]


def _risk_value(row: pd.Series, param: dict) -> float:
    """
    評価項目の「リスク値」（高いほど課題が大きい値）を返します。
    risk_direction が negative の項目（医療アクセスなど、高いほど良い項目）は
    100から引くことで自動的に反転させます。
    """
    raw = row[param["key"]]
    if param["risk_direction"] == "negative":
        return 100 - raw
    return raw


def calculate_scores(df: pd.DataFrame, weights: Weights, parameters: Optional[Parameters] = None) -> pd.DataFrame:
    """
    各地区の総合スコア・順位・優先度を計算して列を追加したDataFrameを返します。
    parametersを省略すると、その時点でマスタに登録されている有効な評価項目を使います
    （＝評価項目管理画面で項目を追加・削除すると、次の計算から自動的に反映されます）。
    """
    parameters = parameters if parameters is not None else load_active_parameters()
    result = df.copy()

    contribution_cols = []
    for param in parameters:
        weight = weights.get(param["weight_key"], 0)
        contrib_col = f"__contrib_{param['weight_key']}"
        result[contrib_col] = result.apply(
            lambda row, p=param, w=weight: _risk_value(row, p) * w, axis=1
        )
        contribution_cols.append(contrib_col)

    if contribution_cols:
        result[COL_SCORE] = result[contribution_cols].sum(axis=1).round(1)
    else:
        result[COL_SCORE] = 0.0

    # 計算に使った一時列（__contrib_*）は最終結果に残さない
    result = result.drop(columns=contribution_cols)

    result[COL_RANK] = result[COL_SCORE].rank(ascending=False, method="min").astype(int)
    result = result.sort_values(COL_RANK).reset_index(drop=True)

    high_th = result[COL_SCORE].quantile(PRIORITY_HIGH_QUANTILE)
    low_th = result[COL_SCORE].quantile(PRIORITY_LOW_QUANTILE)

    def classify(score):
        if score >= high_th:
            return PRIORITY_HIGH
        elif score <= low_th:
            return PRIORITY_LOW
        return PRIORITY_MID

    result[COL_PRIORITY] = result[COL_SCORE].apply(classify)
    return result


def get_contribution_breakdown(row: pd.Series, weights: Weights, parameters: Optional[Parameters] = None) -> list:
    """1地区分の行から、各評価項目の総合スコアへの寄与点の内訳をリストで返します。"""
    parameters = parameters if parameters is not None else load_active_parameters()
    breakdown = []
    for param in parameters:
        weight = weights.get(param["weight_key"], 0)
        contribution = round(_risk_value(row, param) * weight, 1)
        breakdown.append({
            "param_id": param["weight_key"],
            "label": param["label"],
            "contribution": contribution,
            "raw_value": row[param["key"]],
            "unit": param["unit"],
            "risk_direction": param["risk_direction"],
        })
    breakdown.sort(key=lambda x: x["contribution"], reverse=True)
    return breakdown


def get_indicator_diffs(row: pd.Series, df: pd.DataFrame, parameters: Optional[Parameters] = None) -> list:
    """各評価項目の「値」と「全地区平均との差」をリストで返します。"""
    parameters = parameters if parameters is not None else load_active_parameters()
    diffs = []
    for param in parameters:
        avg = df[param["key"]].mean()
        value = row[param["key"]]
        diffs.append({
            "param_id": param["weight_key"],
            "label": param["label"],
            "unit": param["unit"],
            "value": value,
            "avg": avg,
            "diff": value - avg,
            "risk_direction": param["risk_direction"],
        })
    return diffs


def get_indicator_health_scores(row: pd.Series, parameters: Optional[Parameters] = None) -> list:
    """
    各評価項目を「高いほど良い」0〜100点の共通スケールに揃えて返します（確認候補の判定用）。
    値が低いほど、その項目が確認候補になりやすいことを意味します。
    """
    parameters = parameters if parameters is not None else load_active_parameters()
    scores = []
    for param in parameters:
        risk = _risk_value(row, param)
        health = round(100 - risk, 1)
        scores.append({
            "param_id": param["weight_key"],
            "label": param["label"],
            "score": health,
            "raw_value": row[param["key"]],
            "unit": param["unit"],
        })
    scores.sort(key=lambda x: x["score"])  # 低い順（＝改善余地が大きい順）
    return scores


def health_score_to_raw_value(health_score: float, param: dict) -> float:
    """
    「高いほど良い」共通スケールの点数を、その項目本来の生データの値に逆算します。
    シミュレーション画面で「改善後の想定値」をスライダーで指定したときに使います。
    """
    health_score = max(0.0, min(100.0, health_score))
    if param["risk_direction"] == "negative":
        return health_score
    return 100 - health_score


def generate_analysis_comments(row: pd.Series, df: pd.DataFrame, parameters: Optional[Parameters] = None,
                                threshold: float = 3.0) -> list:
    """「なぜこの順位・優先度になったのか」を説明する自動分析コメントのリストを生成します。"""
    parameters = parameters if parameters is not None else load_active_parameters()
    comments = []
    for param in parameters:
        col = param["key"]
        avg = df[col].mean()
        diff = row[col] - avg

        if param["risk_direction"] == "positive":
            if diff >= threshold:
                comments.append(f"{param['label']}が市平均より{diff:.1f}ポイント高い")
            elif diff <= -threshold:
                comments.append(f"{param['label']}は市平均より{abs(diff):.1f}ポイント低く、良好")
        else:
            if diff <= -threshold:
                comments.append(f"{param['label']}が市平均より{abs(diff):.1f}ポイント低い（弱い）")
            elif diff >= threshold:
                comments.append(f"{param['label']}は市平均より{diff:.1f}ポイント高く、良好")

    if not comments:
        comments.append("各項目がおおむね市平均並みであり、突出した要因は見られません。")
    return comments


def get_city_average(df: pd.DataFrame, parameters: Optional[Parameters] = None) -> pd.Series:
    """全地区の指標平均値を返します（比較機能・地区詳細で使用）。"""
    parameters = parameters if parameters is not None else load_active_parameters()
    cols = [p["key"] for p in parameters] + [COL_SCORE]
    cols = [c for c in cols if c in df.columns]
    return df[cols].mean()


def get_city_health_scores(df: pd.DataFrame, parameters: Optional[Parameters] = None) -> list:
    """
    市全体で見たときの、評価項目ごとの平均健全度スコアを返します（低い順）。
    「宇都宮市全体では移動系の確認候補になっている」といった市全体分析に使います。
    """
    parameters = parameters if parameters is not None else load_active_parameters()
    avg_row = get_city_average(df, parameters)
    return get_indicator_health_scores(avg_row, parameters)


def get_indicator_status(target_row: pd.Series, df: pd.DataFrame, parameters: Optional[Parameters] = None) -> list:
    """
    地区詳細画面向けに、評価項目ごとの「現在値・健全度スコア・市平均との差・市内順位」を
    まとめて返します（① 地区基本情報・② 評価項目別の状況 の共通データソース）。
    市内順位は健全度スコアが高いほうを1位とします（＝良好な地区が1位）。
    """
    parameters = parameters if parameters is not None else load_active_parameters()
    result = []
    for param in parameters:
        col = param["key"]
        value = target_row[col]
        avg = df[col].mean()
        diff = value - avg
        health = round(100 - _risk_value(target_row, param), 1)

        health_series = df.apply(lambda r, p=param: 100 - _risk_value(r, p), axis=1)
        rank_series = health_series.rank(ascending=False, method="min").astype(int)
        target_idx = df.index[df[COL_NAME] == target_row[COL_NAME]]
        rank = int(rank_series.loc[target_idx[0]]) if len(target_idx) else None

        result.append({
            "param_id": param["weight_key"], "label": param["label"], "unit": param["unit"],
            "value": value, "score": health, "avg": avg, "diff": diff,
            "rank": rank, "total_count": len(df), "risk_direction": param["risk_direction"],
        })
    return result


# ============================================================
# 施策候補（他自治体施策マスタと連携）
# ------------------------------------------------------------
# 「高齢化率が高ければこの施策」のようなif文を並べるのではなく、
# 弱い評価項目のparam_idをキーに data/policy_master.csv を検索して
# 候補を組み立てます。新しい評価項目・新しい施策を追加しても、
# この関数は変更不要です。
# ============================================================
def get_policy_candidates(weak_params: list, limit_per_param: int = 4) -> Dict[str, list]:
    """
    弱い評価項目のリスト（get_indicator_health_scores()の一部）を受け取り、
    {param_id: [施策事例, ...]} の形で候補を返します。
    """
    candidates = {}
    for wp in weak_params:
        policies = get_policies_for_param(wp["param_id"])
        candidates[wp["param_id"]] = policies[:limit_per_param]
    return candidates


def build_policy_reason(row: pd.Series, df: pd.DataFrame, weak_param: dict) -> list:
    """
    「なぜこの施策事例を参考情報として表示しているか」の理由（地区固有の根拠）を
    組み立てます。数値の根拠のみを示し、断定的な表現は使いません。
    """
    label = weak_param["label"]
    score = weak_param["score"]
    reasons = [f"{label}のスコアが{score:.1f}点で、評価項目の中でも確認候補になっているため"]

    col = None
    for param in load_active_parameters():
        if param["weight_key"] == weak_param["param_id"]:
            col = param["key"]
            break
    if col is not None:
        avg = df[col].mean()
        raw = row[col]
        diff = raw - avg
        if abs(diff) >= 1:
            direction = "高い" if diff > 0 else "低い"
            reasons.append(f"「{label}」の生データも市平均より{abs(diff):.1f}ポイント{direction}")

    return reasons
