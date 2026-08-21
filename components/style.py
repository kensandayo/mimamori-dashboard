# -*- coding: utf-8 -*-
"""
style.py
----------
アプリ全体の見た目（配色・余白・カード・サイドバーなど）を統一するための
グローバルCSSを注入するモジュールです。青・白・グレー基調の行政向けダッシュボードを目指します。
"""

import streamlit as st

from utils.config import (
    COLOR_PRIMARY, COLOR_PRIMARY_DARK, COLOR_ACCENT_BG, COLOR_BORDER, COLOR_TEXT_SUB,
)


def inject_global_css() -> None:
    st.markdown(
        f"""
        <style>
        .stApp {{ background-color: #f6f8fa; }}
        .block-container {{ padding-top: 2rem; padding-bottom: 3rem; max-width: 1200px; }}

        section[data-testid="stSidebar"] {{
            background-color: #f0f2f5;
            border-right: 1px solid {COLOR_BORDER};
        }}
        section[data-testid="stSidebar"] * {{ color: {COLOR_PRIMARY_DARK}; }}

        h1 {{ color: {COLOR_PRIMARY_DARK}; font-weight: 700; font-size: 1.7rem !important; }}
        h2, h3 {{ color: {COLOR_PRIMARY_DARK}; font-weight: 600; }}

        div.stButton > button, div.stDownloadButton > button {{
            background-color: {COLOR_PRIMARY};
            color: #ffffff;
            border-radius: 6px;
            border: none;
            font-weight: 600;
            padding: 0.5rem 1.1rem;
        }}
        div.stButton > button:hover, div.stDownloadButton > button:hover {{
            background-color: {COLOR_PRIMARY_DARK};
            color: #ffffff;
        }}

        button[data-baseweb="tab"] {{ font-weight: 600; color: {COLOR_TEXT_SUB}; }}
        button[data-baseweb="tab"][aria-selected="true"] {{ color: {COLOR_PRIMARY_DARK}; }}

        div[data-testid="stDataFrame"] {{ border: 1px solid {COLOR_BORDER}; border-radius: 8px; }}
        details {{ background-color: #ffffff; border: 1px solid {COLOR_BORDER}; border-radius: 8px; }}
        div[data-testid="stMetric"] {{
            background-color: #ffffff;
            border: 1px solid {COLOR_BORDER};
            border-radius: 10px;
            padding: 14px 16px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def inject_interview_scale_css() -> None:
    """
    ヒアリング用UI。
    ブラウザの表示倍率100%のまま、Streamlitアプリ本体を80%へ縮小表示する。
    transformを使うため、CSS zoomよりブラウザ差の影響を受けにくい。
    """
    st.markdown(
        """
        <style>
        /* Streamlitアプリ本体を80%に縮小 */
        [data-testid="stAppViewContainer"] {
            transform: scale(0.80);
            transform-origin: top left;
            width: 125% !important;
            min-height: 125vh !important;
        }

        /* メイン領域を横に広く使う */
        .block-container {
            max-width: 1900px !important;
            padding-top: 0.8rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-bottom: 1.2rem !important;
        }

        /* 評価カードの省略を減らす */
        [data-testid="stMetric"] {
            min-width: 0 !important;
        }

        [data-testid="stMetricLabel"] p {
            white-space: normal !important;
            overflow: visible !important;
            text-overflow: clip !important;
            line-height: 1.15 !important;
        }

        [data-testid="stMetricValue"] {
            overflow: visible !important;
            text-overflow: clip !important;
        }

        /* 横並びカード間の余白を少しだけ縮小 */
        [data-testid="stHorizontalBlock"] {
            gap: 0.7rem !important;
        }

        /* サイドバーも少し細め */
        [data-testid="stSidebar"] {
            min-width: 245px !important;
            max-width: 270px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

