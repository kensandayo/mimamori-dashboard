# -*- coding: utf-8 -*-
"""
scoring.py
------------
地区ごとの「見守りニーズ総合スコア」を計算するモジュールです。

スコアの考え方:
- 高齢化率・単身高齢者割合は「高いほどリスク（ニーズ）が高い」指標
- 医療アクセス・公共交通は「高いほどリスクが低い」指標なので自動的に反転して計算する
- 各指標を重み付けして合計し、0〜100点のスコアにする

【将来の拡張方法】
新しい指標を追加する場合は、config.py の INDICATORS に情報を追加したうえで、
calculate_scores() 内の risk_direction の分岐処理がそのまま使えるように
DataFrameに新しい列を用意すれば動作します（計算式自体は共通化されています）。
"""

import pandas as pd

from utils.config import (
    INDICATORS, COL_SCORE, COL_RANK, COL_PRIORITY,
    PRIORITY_HIGH, PRIORITY_MID, PRIORITY_LOW,
    PRIORITY_HIGH_QUANTILE, PRIORITY_LOW_QUANTILE,
)


def _risk_value(row, indicator):
    """
    指標の「リスク値」を返します。
    risk_direction が negative の指標（医療アクセス・公共交通など）は
    100から引くことで自動的に反転させます。
    """
    raw = row[indicator["key"]]
    if indicator["risk_direction"] == "negative":
        return 100 - raw
    return raw


def calculate_scores(df: pd.DataFrame, weights: dict) -> pd.DataFrame:
    """
    各地区の総合スコア・順位・優先度・各指標の寄与点を計算して
    列を追加したDataFrameを返します。

    weights: {"aging": 0.3, "single_elderly": 0.3, "medical": 0.2, "transport": 0.2}
             のような重み辞書（合計1.0を想定）
    """
    result = df.copy()

    # 各指標ごとの「寄与点」（重み × リスク値）を計算して列として保持する
    # これは地区レポート画面で「どの指標が何点効いているか」を見せるために使う
    contribution_cols = []
    for indicator in INDICATORS:
        weight = weights.get(indicator["weight_key"], 0)
        contrib_col = f"__contrib_{indicator['key']}"
        result[contrib_col] = result.apply(
            lambda row, ind=indicator, w=weight: _risk_value(row, ind) * w, axis=1
        )
        contribution_cols.append(contrib_col)

    # 総合スコア = 各指標の寄与点の合計
    result[COL_SCORE] = result[contribution_cols].sum(axis=1).round(1)

    # 順位（スコアが高い＝ニーズが高い地区を1位とする）
    result[COL_RANK] = result[COL_SCORE].rank(ascending=False, method="min").astype(int)
    result = result.sort_values(COL_RANK).reset_index(drop=True)

    # 優先度（上位25% = 高、下位25% = 低、それ以外 = 中）
    high_th = result[COL_SCORE].quantile(PRIORITY_HIGH_QUANTILE)
    low_th = result[COL_SCORE].quantile(PRIORITY_LOW_QUANTILE)

    def classify(score):
        if score >= high_th:
            return PRIORITY_HIGH
        elif score <= low_th:
            return PRIORITY_LOW
        else:
            return PRIORITY_MID

    result[COL_PRIORITY] = result[COL_SCORE].apply(classify)

    return result


def get_contribution_breakdown(row: pd.Series, weights: dict) -> list:
    """
    1地区分の行から、各指標の寄与点の内訳をリストで返します。
    [{"label": "高齢化率", "contribution": 12.3, "raw_value": 41.0, "unit": "%"}, ...]
    """
    breakdown = []
    for indicator in INDICATORS:
        weight = weights.get(indicator["weight_key"], 0)
        contribution = round(_risk_value(row, indicator) * weight, 1)
        breakdown.append({
            "label": indicator["label"],
            "contribution": contribution,
            "raw_value": row[indicator["key"]],
            "unit": indicator["unit"],
            "risk_direction": indicator["risk_direction"],
        })
    # 寄与点が大きい順に並び替え（＝そのスコアに最も効いている指標が先頭に来る）
    breakdown.sort(key=lambda x: x["contribution"], reverse=True)
    return breakdown


def generate_reasons(row: pd.Series, df: pd.DataFrame, threshold: float = 3.0) -> list:
    """
    「なぜこの順位・優先度になったのか」を説明する文章のリストを生成します。
    市平均との差が threshold ポイント以上ある指標について理由文を作ります。

    例: "高齢化率が市平均より7.2ポイント高い"
    """
    reasons = []
    for indicator in INDICATORS:
        col = indicator["key"]
        avg = df[col].mean()
        diff = row[col] - avg

        if indicator["risk_direction"] == "positive":
            # 高いほどリスクが高い指標 → 平均より高ければニーズが高い理由になる
            if diff >= threshold:
                reasons.append(f"{indicator['label']}が市平均より{diff:.1f}ポイント高い")
            elif diff <= -threshold:
                reasons.append(f"{indicator['label']}は市平均より{abs(diff):.1f}ポイント低く、良好")
        else:
            # 高いほどリスクが低い指標 → 平均より低ければニーズが高い理由になる
            if diff <= -threshold:
                reasons.append(f"{indicator['label']}が市平均より{abs(diff):.1f}ポイント低い（アクセスが弱い）")
            elif diff >= threshold:
                reasons.append(f"{indicator['label']}は市平均より{diff:.1f}ポイント高く、良好")

    if not reasons:
        reasons.append("各指標がおおむね市平均並みであり、突出した要因は見られません。")

    return reasons


def generate_recommendations(row: pd.Series, df: pd.DataFrame, weights: dict) -> list:
    """
    ルールベースで推奨施策のリストを生成します。
    スコアへの寄与が大きい指標に応じて、対応する施策を提示します。
    """
    breakdown = get_contribution_breakdown(row, weights)
    top_factors = [b["label"] for b in breakdown[:2] if b["contribution"] > 0]

    recommendations = []

    if "高齢化率" in top_factors or "単身高齢者割合" in top_factors:
        recommendations.append("地域包括支援センターとの連携強化")
        recommendations.append("見守りイベント・声かけ活動の開催")
        recommendations.append("民生委員による重点訪問の実施")

    if "医療アクセス" in top_factors:
        recommendations.append("巡回診療・オンライン診療の導入検討")
        recommendations.append("通院支援（送迎サービス）の整備")

    if "公共交通" in top_factors:
        recommendations.append("デマンド型交通・コミュニティバスの導入検討")
        recommendations.append("移動販売・買い物支援サービスの誘致")

    # どの地区にも共通して提示する基本施策
    recommendations.append("地域ボランティア・見守り協力員の募集")

    # 重複を除きつつ順序を保持
    seen = set()
    unique_recommendations = []
    for r in recommendations:
        if r not in seen:
            unique_recommendations.append(r)
            seen.add(r)

    return unique_recommendations


def get_city_average(df: pd.DataFrame) -> pd.Series:
    """全地区の指標平均値を返します（比較機能で使用）。"""
    from utils.config import COL_AGING, COL_SINGLE_ELDERLY, COL_MEDICAL, COL_TRANSPORT
    cols = [COL_AGING, COL_SINGLE_ELDERLY, COL_MEDICAL, COL_TRANSPORT, "総合スコア"]
    cols = [c for c in cols if c in df.columns]
    return df[cols].mean()
