# -*- coding: utf-8 -*-
"""
simulation.py
---------------
What-if分析（施策シミュレーション）を行うモジュールです。

【v8での変更点】
以前は医療アクセス・公共交通など特定の4項目だけを対象にしていましたが、
今後はマスタに登録されているどの評価項目でもシミュレーションできるように
一般化しました。

「デマンド交通を導入したら+10点」のような根拠のない自動加点はせず、
あくまで「評価項目の値がユーザーの指定した想定値まで改善したら、
総合スコアはどう変わるか」を機械的に計算するだけです。
"""

from __future__ import annotations

from typing import Dict, List, Optional, TypedDict

import pandas as pd

from utils.config import COL_NAME
from utils.parameter_loader import load_active_parameters
from utils.scoring import calculate_scores, health_score_to_raw_value, get_indicator_health_scores

Weights = Dict[str, float]


class SimulationResult(TypedDict):
    before_df: pd.DataFrame
    after_df: pd.DataFrame
    before_row: pd.Series
    after_row: pd.Series
    param_label: str
    before_health_score: float
    after_health_score: float


def simulate_parameter_change(
    df: pd.DataFrame,
    weights: Weights,
    target_district: str,
    param_id: str,
    target_health_score: float,
    parameters: Optional[List[dict]] = None,
) -> SimulationResult:
    """
    指定した地区の、指定した評価項目が「target_health_score」（0〜100、高いほど良い
    共通スケール）まで改善したと仮定した場合の、スコア・順位の変化を試算します。

    target_health_score はあくまでユーザーがスライダーで指定した仮定の値です。
    """
    parameters = parameters if parameters is not None else load_active_parameters()
    param = next((p for p in parameters if p["weight_key"] == param_id), None)
    if param is None:
        raise ValueError(f"評価項目「{param_id}」が見つかりません。")

    before_df = calculate_scores(df, weights, parameters)
    idx = df[df[COL_NAME] == target_district].index
    if len(idx) == 0:
        raise ValueError(f"地区「{target_district}」がデータ内に見つかりません。")

    before_row_raw = df.loc[idx[0]]
    before_health = get_indicator_health_scores(before_row_raw, parameters)
    before_health_score = next(h["score"] for h in before_health if h["param_id"] == param_id)

    sim_df = df.copy()
    new_raw_value = health_score_to_raw_value(target_health_score, param)
    sim_df.loc[idx, param["key"]] = new_raw_value

    after_df = calculate_scores(sim_df, weights, parameters)

    before_row = before_df[before_df[COL_NAME] == target_district].iloc[0]
    after_row = after_df[after_df[COL_NAME] == target_district].iloc[0]

    return {
        "before_df": before_df,
        "after_df": after_df,
        "before_row": before_row,
        "after_row": after_row,
        "param_label": param["label"],
        "before_health_score": before_health_score,
        "after_health_score": round(target_health_score, 1),
    }
