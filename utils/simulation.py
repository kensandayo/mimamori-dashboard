# -*- coding: utf-8 -*-
"""
simulation.py
---------------
What-if分析（政策効果シミュレーション）を行うモジュールです。

「もしこの施策で医療アクセスが〇〇改善したら、スコア・順位はどう変わるか」
「もし公共交通の利便性が〇〇改善したら、順位はどう変わるか」
といった、指標の変化量（仮定値）に対するスコア・順位の再計算を行います。

【重要】
ここで入力する改善量はすべて「仮定値」です。
実際にその施策でどの程度指標が改善するかを保証するものではなく、
あくまで機械的な試算（What-if分析）であることに留意してください。
"""

from __future__ import annotations

from typing import Dict, TypedDict

import pandas as pd

from utils.config import COL_NAME, COL_MEDICAL, COL_TRANSPORT, COL_AGING, COL_SINGLE_ELDERLY
from utils.scoring import calculate_scores

Weights = Dict[str, float]


class SimulationResult(TypedDict):
    before_df: pd.DataFrame
    after_df: pd.DataFrame
    before_row: pd.Series
    after_row: pd.Series


def simulate_improvement(
    df: pd.DataFrame,
    weights: Weights,
    target_district: str,
    medical_delta: float = 0.0,
    transport_delta: float = 0.0,
    aging_delta: float = 0.0,
    single_elderly_delta: float = 0.0,
) -> SimulationResult:
    """
    指定した地区の指標を仮に変化させた場合の、スコア・順位の変化をWhat-if分析します。

    delta引数はすべて「仮定の変化量」です。
    - medical_delta, transport_delta: プラスの値を渡すと改善（アクセス向上）を仮定
    - aging_delta, single_elderly_delta: マイナスの値を渡すと改善（比率低下）を仮定

    戻り値には変更前後の全地区スコア（地図の再描画に使用）と、
    対象地区の変更前後の行を含みます。
    """
    before_df = calculate_scores(df, weights)

    sim_df = df.copy()
    idx = sim_df[sim_df[COL_NAME] == target_district].index

    if len(idx) == 0:
        raise ValueError(f"地区「{target_district}」がデータ内に見つかりません。")

    # 0〜100の範囲に収まるようにクリップしながら値を更新する（仮定値の反映）
    sim_df.loc[idx, COL_MEDICAL] = (sim_df.loc[idx, COL_MEDICAL] + medical_delta).clip(0, 100)
    sim_df.loc[idx, COL_TRANSPORT] = (sim_df.loc[idx, COL_TRANSPORT] + transport_delta).clip(0, 100)
    sim_df.loc[idx, COL_AGING] = (sim_df.loc[idx, COL_AGING] + aging_delta).clip(0, 100)
    sim_df.loc[idx, COL_SINGLE_ELDERLY] = (sim_df.loc[idx, COL_SINGLE_ELDERLY] + single_elderly_delta).clip(0, 100)

    after_df = calculate_scores(sim_df, weights)

    before_row = before_df[before_df[COL_NAME] == target_district].iloc[0]
    after_row = after_df[after_df[COL_NAME] == target_district].iloc[0]

    return {
        "before_df": before_df,
        "after_df": after_df,
        "before_row": before_row,
        "after_row": after_row,
    }
