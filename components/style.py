# -*- coding: utf-8 -*-
"""
style.py
----------
アプリ全体の見た目（配色・余白・カード・サイドバーなど）を統一するための
グローバルCSSを注入するモジュールです。

狙っているトーン:
- 派手な演出はせず、自治体職員が業務でそのまま使える「行政向けダッシュボード」
- 配色は青・白・グレーの3色を基調に統一
- カードや余白を揃えることで、Lovable等のモダンなダッシュボードに近い
  整った印象にしつつ、シンプルさを崩さない

このCSSは app.py の冒頭で一度だけ呼び出します（inject_global_css()）。
"""

import streamlit as st

from utils.config import (
    COLOR_PRIMARY, COLOR_PRIMARY_DARK, COLOR_ACCENT_BG, COLOR_BORDER, COLOR_TEXT_SUB,
)


def inject_global_css() -> None:
    """アプリ全体に適用するグローバルCSSを注入します。"""
    st.markdown(
        f"""
        <style>
        /* ---------- 全体の背景・余白 ---------- */
        .stApp {{
            background-color: #f6f8fa;
        }}
        .block-container {{
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1200px;
        }}

        /* ---------- サイドバー（グレー基調） ---------- */
        section[data-testid="stSidebar"] {{
            background-color: #f0f2f5;
            border-right: 1px solid {COLOR_BORDER};
        }}
        section[data-testid="stSidebar"] * {{
            color: {COLOR_PRIMARY_DARK};
        }}

        /* ---------- 見出し ---------- */
        h1 {{
            color: {COLOR_PRIMARY_DARK};
            font-weight: 700;
            font-size: 1.7rem !important;
        }}
        h2, h3 {{
            color: {COLOR_PRIMARY_DARK};
            font-weight: 600;
        }}

        /* ---------- ボタン（青基調） ---------- */
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

        /* ---------- タブ ---------- */
        button[data-baseweb="tab"] {{
            font-weight: 600;
            color: {COLOR_TEXT_SUB};
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            color: {COLOR_PRIMARY_DARK};
        }}

        /* ---------- データフレーム／テーブル ---------- */
        div[data-testid="stDataFrame"] {{
            border: 1px solid {COLOR_BORDER};
            border-radius: 8px;
        }}

        /* ---------- expander（絞り込み条件など） ---------- */
        details {{
            background-color: #ffffff;
            border: 1px solid {COLOR_BORDER};
            border-radius: 8px;
        }}

        /* ---------- metric ---------- */
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
