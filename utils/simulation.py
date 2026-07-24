# -*- coding: utf-8 -*-
"""
simulation.py
---------------
「医療アクセスを改善したらスコアがどう変わるか」
「公共交通を改善したら順位がどう変わるか」
といった、簡易的な政策効果シミュレーションを行うモジュールです。

あくまで試験的な機能であり、実際の政策効果を保証するものではありません。
"""

import pandas as pd

from utils.config import COL_NAME, COL_MEDICAL, COL_TRANSPORT, COL_AGING, COL_SINGLE_ELDERLY
from utils.scoring import calculate_scores


def simulate_improvement(df: pd.DataFrame, weights: dict, target_district: str,
                          medical_delta: float = 0.0, transport_delta: float = 0.0,
                          aging_delta: float = 0.0, single_elderly_delta: float = 0.0) -> dict:
    """
    指定した地区の指標を仮に変化させた場合の、スコア・順位の変化をシミュレーションします。

    delta引数はすべて「変化量」です。
    - medical_delta, transport_delta: プラスの値を渡すと改善（アクセス向上）
    - aging_delta, single_elderly_delta: マイナスの値を渡すと改善（比率低下）

    戻り値:
        {
            "before_df": 変更前の全地区スコアDataFrame,
            "after_df": 変更後の全地区スコアDataFrame,
            "before_row": 対象地区の変更前の行,
            "after_row": 対象地区の変更後の行,
        }
    """
    before_df = calculate_scores(df, weights)

    sim_df = df.copy()
    idx = sim_df[sim_df[COL_NAME] == target_district].index

    if len(idx) == 0:
        raise ValueError(f"地区「{target_district}」がデータ内に見つかりません。")

    # 0〜100の範囲に収まるようにクリップしながら値を更新する
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
