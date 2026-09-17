# -*- coding: utf-8 -*-
"""
state.py
----------
st.session_state（ページをまたいで保持される状態）の初期化を一箇所にまとめるモジュールです。

【v8での変更点】
重みは以前は4項目固定の辞書でしたが、今後は評価項目数が可変なため、
parameter_loader.get_default_weights() から動的に初期値を組み立てます。
また「現在どの評価パターンを使っているか」も session_state で管理し、
パターンを切り替えると全画面のスコアが自動的に再計算されます。
"""

from __future__ import annotations

from typing import Dict, Optional

import pandas as pd
import streamlit as st

from utils.config import DATA_SOURCE_NAME, DATA_TARGET_YEAR, DATA_UPDATED_AT
from utils.data_loader import load_default_data
from utils.parameter_loader import get_default_weights
from utils.scoring import calculate_scores
from utils.patterns import get_pattern

RAW_DATA_KEY = "raw_data"
WEIGHTS_KEY = "weights"
DATA_SOURCE_INFO_KEY = "data_source_info"
CURRENT_PATTERN_KEY = "current_pattern_name"

Weights = Dict[str, float]


def init_state() -> None:
    """アプリ起動直後に一度だけ必要な初期値をセットします。"""
    if RAW_DATA_KEY not in st.session_state:
        st.session_state[RAW_DATA_KEY] = load_default_data()

    defaults = get_default_weights()
    if WEIGHTS_KEY not in st.session_state:
        st.session_state[WEIGHTS_KEY] = defaults
    else:
        # v18: 評価項目の追加・有効化後も重み辞書を自動同期する。
        # 旧項目は除外し、新規項目にはマスタ既定値を付与してから合計1に正規化する。
        current = st.session_state[WEIGHTS_KEY]
        synced = {k: float(current.get(k, v)) for k, v in defaults.items()}
        total = sum(synced.values())
        if total > 0:
            synced = {k: v / total for k, v in synced.items()}
        st.session_state[WEIGHTS_KEY] = synced

    if CURRENT_PATTERN_KEY not in st.session_state:
        st.session_state[CURRENT_PATTERN_KEY] = "標準"

    if DATA_SOURCE_INFO_KEY not in st.session_state:
        st.session_state[DATA_SOURCE_INFO_KEY] = {
            "source_name": DATA_SOURCE_NAME,
            "target_year": DATA_TARGET_YEAR,
            "updated_at": DATA_UPDATED_AT,
        }


def get_raw_data() -> pd.DataFrame:
    init_state()
    return st.session_state[RAW_DATA_KEY]


def set_raw_data(
    df: pd.DataFrame,
    source_name: Optional[str] = None,
    updated_at: Optional[str] = None,
    target_year: Optional[str] = None,
) -> None:
    st.session_state[RAW_DATA_KEY] = df
    if source_name is not None or updated_at is not None or target_year is not None:
        info = dict(st.session_state.get(DATA_SOURCE_INFO_KEY, {}))
        if source_name is not None:
            info["source_name"] = source_name
        if updated_at is not None:
            info["updated_at"] = updated_at
        if target_year is not None:
            info["target_year"] = target_year
        st.session_state[DATA_SOURCE_INFO_KEY] = info


def get_weights() -> Weights:
    init_state()
    return st.session_state[WEIGHTS_KEY]


def set_weights(weights: Weights) -> None:
    st.session_state[WEIGHTS_KEY] = weights
    # 重みを手動調整したら、以後は「カスタム」として扱う
    st.session_state[CURRENT_PATTERN_KEY] = "カスタム"


def get_current_pattern_name() -> str:
    init_state()
    return st.session_state[CURRENT_PATTERN_KEY]


def apply_pattern(name: str) -> bool:
    """
    保存済みの評価パターンを現在の重みに適用します。
    成功したらTrue、パターンが見つからなければFalseを返します。
    """
    pattern = get_pattern(name)
    if pattern is None:
        return False
    defaults = get_default_weights()
    supplied = pattern.get("weights", {})
    merged = {k: float(supplied.get(k, defaults[k])) for k in defaults}
    total = sum(merged.values())
    if total > 0:
        merged = {k: v / total for k, v in merged.items()}
    st.session_state[WEIGHTS_KEY] = merged
    st.session_state[CURRENT_PATTERN_KEY] = name
    return True


def get_scored_data() -> pd.DataFrame:
    """
    現在のデータと重みからスコア計算済みのDataFrameを取得します。
    評価項目は毎回マスタから読み込むため、設定画面で項目を追加・削除すると
    次にこの関数が呼ばれたときから自動的に反映されます。
    """
    df = get_raw_data()
    weights = get_weights()
    return calculate_scores(df, weights)


def get_data_source_info() -> dict:
    init_state()
    return st.session_state[DATA_SOURCE_INFO_KEY]


def reset_to_default_data() -> None:
    """標準データ（data/sample_data.csv）に戻します。"""
    set_raw_data(
        load_default_data(),
        source_name=DATA_SOURCE_NAME,
        updated_at=DATA_UPDATED_AT,
        target_year=DATA_TARGET_YEAR,
    )
