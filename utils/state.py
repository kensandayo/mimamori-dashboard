# -*- coding: utf-8 -*-
"""
state.py
----------
st.session_state（ページをまたいで保持される状態）の初期化を
一箇所にまとめるモジュールです。

Streamlitはページごとにスクリプトが再実行されるため、
「元データ」「重み設定」などはすべてsession_stateに保存し、
どのページからでも同じ関数を呼べば初期化・取得できるようにしています。

標準データは data/sample_data.csv（config.DEFAULT_CSV_PATH）です。
アプリ起動時に一度だけ読み込み、以後はCSVアップロードや画面編集で
session_state上のデータを差し替えます（元のCSVファイル自体は変更しません）。
"""

from __future__ import annotations

from typing import Dict, Optional

import pandas as pd
import streamlit as st

from utils.config import DEFAULT_WEIGHTS, DATA_SOURCE_NAME, DATA_TARGET_YEAR, DATA_UPDATED_AT
from utils.data_loader import load_default_data
from utils.scoring import calculate_scores

RAW_DATA_KEY = "raw_data"
WEIGHTS_KEY = "weights"
DATA_SOURCE_INFO_KEY = "data_source_info"

Weights = Dict[str, float]


def init_state() -> None:
    """アプリ起動直後に一度だけ必要な初期値をセットします。"""
    if RAW_DATA_KEY not in st.session_state:
        st.session_state[RAW_DATA_KEY] = load_default_data()

    if WEIGHTS_KEY not in st.session_state:
        st.session_state[WEIGHTS_KEY] = dict(DEFAULT_WEIGHTS)

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
    """データを更新します（CSVアップロードや画面編集の反映時に使用）。"""
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


def get_scored_data() -> pd.DataFrame:
    """現在のデータと重みからスコア計算済みのDataFrameを取得します。"""
    df = get_raw_data()
    weights = get_weights()
    return calculate_scores(df, weights)


def get_data_source_info() -> dict:
    """データ出典・対象年度・更新日を返します（ダッシュボード・設定画面で表示）。"""
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
