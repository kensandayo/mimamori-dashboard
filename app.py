# -*- coding: utf-8 -*-
"""
app.py
--------
アプリのエントリーポイントです。

【文字化け対策について】
以前はpages/フォルダ内のファイル名に日本語・絵文字を使っており、
実行環境（OSの文字コード設定など）によってサイドバーのメニュー表示が
文字化けすることがありました。

このファイルでは st.navigation() / st.Page() を使い、
- ページファイル名はすべて英数字（dashboard.py, map.py など）
- サイドバーに表示される日本語タイトルは、このファイル内の
  Pythonの文字列（UTF-8で保存されたソースコード）として直接指定
という構成にすることで、文字化けの原因を構造的に排除しています。
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from utils.config import APP_TITLE, APP_VERSION
from utils.state import init_state
from components.style import inject_global_css

# ページ全体の基本設定（タイトル・レイアウト・アイコン）
# st.set_page_config はスクリプト全体で最初に一度だけ呼び出す必要があります。
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🏘️",
    layout="wide",
)

# 全画面共通のCSS（青・白・グレー基調のデザイン）を注入
inject_global_css()

# session_stateの初期化（標準データ・重みの初期値をセット）
init_state()

# pages/ フォルダ内の各画面を、日本語タイトル・アイコン付きでナビゲーションに登録
PAGES_DIR = Path(__file__).resolve().parent / "pages"

pages = [
    st.Page(str(PAGES_DIR / "1_dashboard.py"), title="ダッシュボード", icon="🏠", default=True),
    st.Page(str(PAGES_DIR / "2_priority_map.py"), title="地域マップ", icon="🗺️"),
    st.Page(str(PAGES_DIR / "3_ranking.py"), title="ランキング", icon="📊"),
    st.Page(str(PAGES_DIR / "4_comparison.py"), title="比較", icon="📈"),
    st.Page(str(PAGES_DIR / "5_district_report.py"), title="地区詳細", icon="📋"),
    st.Page(str(PAGES_DIR / "6_simulation.py"), title="シミュレーション", icon="🔮"),
    st.Page(str(PAGES_DIR / "7_data_management.py"), title="設定・データ管理", icon="⚙️"),
]

navigation = st.navigation(pages)

# サイドバー最上部にアプリ名を表示
with st.sidebar:
    st.markdown(f"### 🏘️ {APP_TITLE}")
    st.caption("地区単位の見守り意思決定支援ツール")
    st.markdown("---")

navigation.run()

with st.sidebar:
    st.markdown("---")
    st.caption(f"バージョン: {APP_VERSION}")
