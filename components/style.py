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

def inject_compact_desktop_css() -> None:
    """100%表示でも情報が収まりやすい、少し引き気味のデスクトップUI。"""
    st.markdown(
        """
        <style>
        .block-container {
            max-width: 1600px !important;
            padding-top: 1.0rem !important;
            padding-left: 1.25rem !important;
            padding-right: 1.25rem !important;
            padding-bottom: 1.5rem !important;
        }

        h1 { font-size: 1.85rem !important; line-height: 1.25 !important; }
        h2 { font-size: 1.55rem !important; line-height: 1.30 !important; }
        h3 { font-size: 1.20rem !important; line-height: 1.30 !important; }

        [data-testid="stMetric"] {
            padding: 0.50rem 0.55rem !important;
            min-width: 0 !important;
        }
        [data-testid="stMetricLabel"] p {
            font-size: 0.76rem !important;
            white-space: normal !important;
            overflow: visible !important;
            text-overflow: clip !important;
            line-height: 1.12 !important;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.48rem !important;
            line-height: 1.12 !important;
        }
        [data-testid="stMetricDelta"] {
            font-size: 0.76rem !important;
        }

        [data-testid="stHorizontalBlock"] {
            gap: 0.55rem !important;
        }

        [data-testid="stSidebar"] {
            min-width: 240px !important;
            max-width: 280px !important;
        }

        [data-testid="stDataFrame"] {
            font-size: 0.90rem !important;
        }

        @media (max-width: 1100px) {
            .block-container {
                padding-left: 0.75rem !important;
                padding-right: 0.75rem !important;
            }
            [data-testid="stMetricValue"] { font-size: 1.30rem !important; }
            [data-testid="stMetricLabel"] p { font-size: 0.70rem !important; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

