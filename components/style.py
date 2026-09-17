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

def inject_no_transform_compact_css() -> None:
    """
    アプリ全体のレイアウト用CSS（旧: inject_tight_vertical_spacing_css /
    inject_dashboard_compact_css の内容を統合したもの）。

    方針:
    - transform: scale() / CSS zoom / width:125% / min-height:125vh のような
      疑似的な縮小表示は一切使わない（ブラウザ表示倍率は常に100%を前提とする）。
    - Streamlit上部の固定ツールバーにタイトルが隠れないよう、block-container の
      padding-top を十分に確保する。
    - 行間(line-height)は最低1.3を基本とし、要素同士の間隔(gap/margin)も
      文字が重ならない余裕を持たせる。固定heightや極端に小さいgapは使わない。
    - 画面の高さに応じてさらに詰める@media (max-height...)の類は使わない
      （収まりきらない場合は素直にスクロールさせる）。
    - `.block-container` と `[data-testid="stMainBlockContainer"]`
      （Streamlitのバージョンによって呼び名が異なる同一要素）の両方に
      同じ値を指定し、ページ側の個別CSSに上書きされにくくしている。
    - ここで定義するfont-size / padding / gapが「アプリ全体共通の表示密度
      （タイポグラフィ・スペーシングルール）」であり、各ページはこれに
      従うことを基本とする（ページ固有CSSは最小限に留める）。
    """
    st.markdown(
        """
        <style>
        .block-container,
        [data-testid="stMainBlockContainer"] {
            max-width: 1700px !important;
            padding-top: 3.2rem !important;
            padding-left: 1.2rem !important;
            padding-right: 1.2rem !important;
            padding-bottom: 1.6rem !important;
        }

        h1 {
            font-size: 1.42rem !important;
            line-height: 1.35 !important;
            margin: 0 0 0.5rem 0 !important;
            overflow: visible !important;
            white-space: normal !important;
        }

        h2 {
            font-size: 1.14rem !important;
            line-height: 1.35 !important;
            margin-top: 0.75rem !important;
            margin-bottom: 0.42rem !important;
            overflow: visible !important;
        }

        h3 {
            font-size: 1.00rem !important;
            line-height: 1.35 !important;
            margin-top: 0.6rem !important;
            margin-bottom: 0.35rem !important;
            overflow: visible !important;
        }

        /* 縦方向のブロック間隔。文字が重ならない程度の余裕を持たせつつ、
           以前よりやや詰めた「共通のセクション間隔」の基準値 */
        [data-testid="stVerticalBlock"] {
            gap: 0.5rem !important;
        }

        [data-testid="stHorizontalBlock"] {
            gap: 0.7rem !important;
        }

        /* 本文・キャプションの共通タイポグラフィ */
        .stMarkdown p {
            font-size: 0.92rem !important;
            margin-top: 0.2rem !important;
            margin-bottom: 0.35rem !important;
            line-height: 1.5 !important;
        }

        .stCaption {
            font-size: 0.82rem !important;
            margin-top: 0.2rem !important;
            margin-bottom: 0.35rem !important;
            line-height: 1.5 !important;
        }

        /* ボタン共通サイズ（少しコンパクトに） */
        div.stButton > button, div.stDownloadButton > button {
            padding: 0.42rem 0.9rem !important;
            font-size: 0.88rem !important;
        }

        /* 入力欄（selectbox / text_input / number_input）のラベル文字 */
        [data-testid="stWidgetLabel"] p {
            font-size: 0.86rem !important;
        }

        /* st.metric（設定・データ管理／地区詳細画面などで使用） */
        [data-testid="stMetric"] {
            padding: 0.5rem 0.75rem !important;
            min-width: 0 !important;
        }

        [data-testid="stMetricLabel"] p {
            font-size: 0.76rem !important;
            line-height: 1.3 !important;
            white-space: normal !important;
            overflow: visible !important;
            text-overflow: clip !important;
        }

        [data-testid="stMetricValue"] {
            font-size: 1.32rem !important;
            line-height: 1.3 !important;
            overflow: visible !important;
            text-overflow: clip !important;
        }

        [data-testid="stMetricDelta"] {
            font-size: 0.72rem !important;
            line-height: 1.3 !important;
        }

        [data-testid="stDataFrame"] {
            margin-top: 0.25rem !important;
            margin-bottom: 0.3rem !important;
            font-size: 0.9rem !important;
        }

        hr {
            margin-top: 0.6rem !important;
            margin-bottom: 0.6rem !important;
        }

        [data-testid="stExpander"],
        [data-testid="stSelectbox"],
        [data-testid="stNumberInput"],
        [data-testid="stTextInput"] {
            margin-top: 0.15rem !important;
            margin-bottom: 0.25rem !important;
        }

        [data-testid="stSidebar"] {
            min-width: 225px !important;
            max-width: 270px !important;
        }

        /* --- サイドバー：内容がviewportの高さを超えた場合のみ、
           サイドバー内部だけを縦スクロール可能にする ---
           Streamlit標準のサイドバーDOM構造は
             section[data-testid="stSidebar"]
               └ div[data-testid="stSidebarContent"]  ← 実際にスクロールする要素
                   ├ div[data-testid="stSidebarHeader"]
                   ├ div[data-testid="stSidebarNav"]（ナビゲーション項目）
                   └ div[data-testid="stSidebarUserContent"]（システム名／
                     説明文／評価パターン／バージョン情報）
           となっており、stSidebarContent がサイドバー内の全コンテンツを
           包む実際のスクロールコンテナ。ここに overflow-y: auto を明示し、
           内容が収まっている通常時は何も変化せず、収まらない場合だけ
           サイドバー内部のみが縦スクロールするようにする。
           固定height・transform・zoom・overflow:hiddenは使用しない。
           評価パターンのドロップダウン(react-aria-ComboBoxのポップアップ)は
           position:fixedでbody直下に描画されるため、このoverflow設定の
           影響を受けず、通常通り操作できる。 */
        [data-testid="stSidebarContent"] {
            overflow-y: auto !important;
        }

        /* サイドバー全体のフォントサイズ（ナビゲーション・ブランド文言・
           入力欄ラベルなどをまとめてやや小さく） */
        [data-testid="stSidebar"] {
            font-size: 0.86rem !important;
        }
        [data-testid="stSidebar"] h1 {
            font-size: 1.15rem !important;
        }
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] label {
            font-size: 0.86rem !important;
            line-height: 1.4 !important;
        }

        /* --- サイドバー：上下の余白を詰めて1画面に収まりやすくする --- */
        [data-testid="stSidebarUserContent"] {
            padding-top: 10px !important;
            padding-bottom: 20px !important;
        }

        /* --- サイドバー：ナビゲーション項目（ダッシュボード／地域マップ…） ---
           実測したところ実際の行要素は li(高さ約23px+margin-bottom 2px)。
           font-size / line-height / margin-bottom を少し詰めて
           1項目あたりの高さを約10〜15%圧縮する。アイコンと文字は同じ比率
           で縮小し、バランスは維持する。 */
        [data-testid="stSidebarNav"] {
            padding-top: 4px !important;
            padding-bottom: 4px !important;
        }
        [data-testid="stSidebarNav"] li {
            margin-bottom: 0px !important;
            min-height: 22px !important;
        }
        [data-testid="stSidebarNav"] a {
            font-size: 0.8rem !important;
            line-height: 1.5rem !important;
            padding: 0 0.5rem !important;
            min-height: 22px !important;
        }
        [data-testid="stSidebarNav"] span {
            font-size: 0.8rem !important;
        }

        /* --- サイドバー：ブランドタイトル「地域見守り意思決定支援システム」 ---
           st.markdown("### ...") で生成されるh3。サイドバー専用に少しだけ
           縮小し、行間を詰める（文字が潰れない範囲で調整）。 */
        [data-testid="stSidebar"] h3 {
            font-size: 0.94rem !important;
            line-height: 1.35 !important;
            margin-top: 6px !important;
            margin-bottom: 4px !important;
        }

        /* --- サイドバー：説明文「地区単位の見守り・施策検討支援ツール」 ---
           st.caption()の実体は[data-testid="stCaptionContainer"]であり、
           Streamlit標準でmargin-bottom:-1remが付与されている。サイドバーの
           他要素とは詰め方が違う独立した余白調整のため、ここで明示的に
           0へ打ち消してからmargin-topのみで間隔を決める。 */
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
            margin-bottom: 0 !important;
        }
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
            font-size: 0.78rem !important;
            line-height: 1.35 !important;
            margin: 2px 0 0 0 !important;
        }

        /* --- サイドバー：区切り線（st.markdown("---")）---
           上下の余白がやや大きかったため少し減らす。 */
        [data-testid="stSidebar"] hr {
            margin-top: 6px !important;
            margin-bottom: 6px !important;
        }

        /* --- サイドバー：「評価パターン」セレクトボックス ---
           ラベル文字とプルダウン本体の高さを少し詰める。クリック操作の
           妨げにならない範囲（36px程度）に留める。 */
        [data-testid="stSidebar"] [data-testid="stSelectbox"] {
            margin-top: 2px !important;
            margin-bottom: 4px !important;
        }
        [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
            font-size: 0.8rem !important;
            margin-bottom: 2px !important;
        }
        [data-testid="stSidebar"] [data-testid="stSelectbox"] .react-aria-ComboBox {
            min-height: 2.25rem !important;
        }
        [data-testid="stSidebar"] [data-testid="stSelectbox"] .react-aria-ComboBox > div {
            height: 2.25rem !important;
            min-height: 2.25rem !important;
        }
        [data-testid="stSidebar"] [data-testid="stSelectbox"] .react-aria-ComboBox input,
        [data-testid="stSidebar"] [data-testid="stSelectbox"] .react-aria-ComboBox button {
            min-height: 2.25rem !important;
            height: 2.25rem !important;
            font-size: 0.85rem !important;
        }

        /* --- ダッシュボード画面（1_dashboard.py）専用のカード/パネル --- */

        .dashboard-kpi-card {
            min-height: 70px;
            padding: 8px 12px !important;
        }

        .dashboard-compact-panel {
            background: #ffffff;
            border: 1px solid #dbe3ec;
            border-radius: 9px;
            padding: 10px 12px;
            margin-top: 8px;
            box-shadow: 0 1px 3px rgba(15,23,42,0.04);
        }

        .dashboard-compact-panel-title {
            color: #1d3557;
            font-size: 13px;
            line-height: 1.4;
            font-weight: 700;
            margin-bottom: 5px;
        }

        .dashboard-compact-panel ul {
            margin: 4px 0 0 0;
            padding-left: 20px;
            columns: 2;
            column-gap: 24px;
        }

        .dashboard-compact-panel li {
            color: #374151;
            font-size: 11.5px;
            line-height: 1.5;
            margin-bottom: 3px;
            break-inside: avoid;
        }

        .dashboard-source-row {
            display: grid;
            grid-template-columns: 2fr 1fr 1fr;
            gap: 9px;
            margin-top: 9px;
        }

        .dashboard-source-item {
            background: #f6f8fa;
            border: 1px solid #dbe3ec;
            border-radius: 7px;
            padding: 7px 9px;
        }

        .dashboard-source-label {
            color: #6b7280;
            font-size: 10.5px;
            line-height: 1.4;
        }

        .dashboard-source-value {
            color: #1d3557;
            font-size: 11.5px;
            font-weight: 600;
            margin-top: 3px;
            line-height: 1.4;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

