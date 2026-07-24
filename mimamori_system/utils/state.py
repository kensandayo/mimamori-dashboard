# -*- coding: utf-8 -*-
"""
state.py
----------
st.session_state（ページをまたいで保持される状態）の初期化を
一箇所にまとめるモジュールです。

Streamlitはページごとにスクリプトが再実行されるため、
「元データ」「重み設定」などはすべてsession_stateに保存し、
どのページからでも同じ関数を呼べば初期化・取得できるようにしています。
"""

import streamlit as st

from utils.config import DEFAULT_WEIGHTS
from utils.data_loader import generate_sample_data
from utils.scoring import calculate_scores

RAW_DATA_KEY = "raw_data"
WEIGHTS_KEY = "weights"
DATA_SOURCE_INFO_KEY = "data_source_info"


def init_state():
    """アプリ起動直後に一度だけ必要な初期値をセットします。"""
    if RAW_DATA_KEY not in st.session_state:
        st.session_state[RAW_DATA_KEY] = generate_sample_data()

    if WEIGHTS_KEY not in st.session_state:
        st.session_state[WEIGHTS_KEY] = dict(DEFAULT_WEIGHTS)

    if DATA_SOURCE_INFO_KEY not in st.session_state:
        st.session_state[DATA_SOURCE_INFO_KEY] = {
            "source_name": "サンプルデータ（デモ用ダミーデータ）",
            "updated_at": "2026-04-01",
        }


def get_raw_data():
    init_state()
    return st.session_state[RAW_DATA_KEY]


def set_raw_data(df, source_name: str = None, updated_at: str = None):
    """データを更新します（CSVアップロードや画面編集の反映時に使用）。"""
    st.session_state[RAW_DATA_KEY] = df
    if source_name is not None or updated_at is not None:
        info = st.session_state.get(DATA_SOURCE_INFO_KEY, {})
        if source_name is not None:
            info["source_name"] = source_name
        if updated_at is not None:
            info["updated_at"] = updated_at
        st.session_state[DATA_SOURCE_INFO_KEY] = info


def get_weights():
    init_state()
    return st.session_state[WEIGHTS_KEY]


def set_weights(weights: dict):
    st.session_state[WEIGHTS_KEY] = weights


def get_scored_data():
    """現在のデータと重みからスコア計算済みのDataFrameを取得します。"""
    df = get_raw_data()
    weights = get_weights()
    return calculate_scores(df, weights)


def get_data_source_info():
    init_state()
    return st.session_state[DATA_SOURCE_INFO_KEY]
