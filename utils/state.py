# -*- coding: utf-8 -*-
"""
state.py
----------
st.session_stateを使用して、
ページをまたいで保持するデータを管理するモジュールです。

保持する情報:
1. 地区データ
2. スコア計算用の重み
3. データ出典や更新日時
"""

import streamlit as st

from utils.config import DEFAULT_WEIGHTS
from utils.data_loader import load_sample_csv
from utils.scoring import calculate_scores


RAW_DATA_KEY = "raw_data"
WEIGHTS_KEY = "weights"
DATA_SOURCE_INFO_KEY = "data_source_info"


def init_state():
    """
    アプリ起動時に必要な初期値を設定します。

    地区データがまだsession_stateに入っていない場合、
    data/sample_data.csvを読み込みます。
    """
    if RAW_DATA_KEY not in st.session_state:
        st.session_state[RAW_DATA_KEY] = load_sample_csv()

    if WEIGHTS_KEY not in st.session_state:
        st.session_state[WEIGHTS_KEY] = dict(DEFAULT_WEIGHTS)

    if DATA_SOURCE_INFO_KEY not in st.session_state:
        st.session_state[DATA_SOURCE_INFO_KEY] = {
            "source_name": "data/sample_data.csv",
            "updated_at": "2026-07-22",
        }


def reload_csv_data():
    """
    data/sample_data.csvを再読み込みします。

    CSVを書き換えた後、画面上から再読み込みする場合に使用できます。
    """
    st.session_state[RAW_DATA_KEY] = load_sample_csv()

    st.session_state[DATA_SOURCE_INFO_KEY] = {
        "source_name": "data/sample_data.csv",
        "updated_at": "CSV再読み込み時点",
    }


def get_raw_data():
    """
    現在使用している地区データを返します。
    """
    init_state()
    return st.session_state[RAW_DATA_KEY]


def set_raw_data(
    df,
    source_name: str = None,
    updated_at: str = None,
):
    """
    地区データを更新します。

    CSVアップロードや、画面上で編集した内容を
    アプリに反映するときに使用します。
    """
    st.session_state[RAW_DATA_KEY] = df

    if source_name is not None or updated_at is not None:
        info = st.session_state.get(
            DATA_SOURCE_INFO_KEY,
            {},
        )

        if source_name is not None:
            info["source_name"] = source_name

        if updated_at is not None:
            info["updated_at"] = updated_at

        st.session_state[DATA_SOURCE_INFO_KEY] = info


def get_weights():
    """
    現在の重み設定を返します。
    """
    init_state()
    return st.session_state[WEIGHTS_KEY]


def set_weights(weights: dict):
    """
    重み設定を更新します。
    """
    st.session_state[WEIGHTS_KEY] = weights


def get_scored_data():
    """
    現在の地区データと重みを使い、
    スコア計算済みのDataFrameを返します。
    """
    df = get_raw_data()
    weights = get_weights()

    return calculate_scores(df, weights)


def get_data_source_info():
    """
    データ出典と更新日時を返します。
    """
    init_state()
    return st.session_state[DATA_SOURCE_INFO_KEY]