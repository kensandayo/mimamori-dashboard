# -*- coding: utf-8 -*-
"""
app.py
--------
アプリのエントリーポイントです。st.navigation() / st.Page() でページを登録し、
サイドバーには「評価パターン」の切り替えプルダウンを常に表示します
（パターンを切り替えると、全画面のスコアが自動的に再計算されます）。

ページファイル名はすべて英数字（1_dashboard.py など）にし、日本語タイトルは
このファイル内の文字列として直接指定することで、文字化けの原因を構造的に
排除しています。
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from utils.config import APP_TITLE, APP_VERSION
from utils.state import init_state, get_current_pattern_name, apply_pattern
from utils.patterns import list_pattern_names
from components.style import inject_global_css, inject_compact_desktop_css

st.set_page_config(page_title=APP_TITLE, page_icon="🏘️", layout="wide")
inject_global_css()
inject_compact_desktop_css()
init_state()

PAGES_DIR = Path(__file__).resolve().parent / "pages"

pages = [
    st.Page(str(PAGES_DIR / "1_dashboard.py"), title="ダッシュボード", icon="🏠", default=True),
    st.Page(str(PAGES_DIR / "2_priority_map.py"), title="地域マップ", icon="🗺️"),
    st.Page(str(PAGES_DIR / "3_ranking.py"), title="ランキング", icon="📊"),
    st.Page(str(PAGES_DIR / "4_comparison.py"), title="比較", icon="📈"),
    st.Page(str(PAGES_DIR / "5_district_report.py"), title="地区詳細", icon="📋"),
    st.Page(str(PAGES_DIR / "6_simulation.py"), title="シミュレーション", icon="🔮"),
    st.Page(str(PAGES_DIR / "7_data_management.py"), title="設定・データ管理", icon="⚙️"),
#     st.Page(str(PAGES_DIR / "8_ai_consultation.py"), title="AI相談", icon="💬"),
    st.Page(str(PAGES_DIR / "9_city_analysis.py"), title="市全体分析", icon="🏙️"),
]

navigation = st.navigation(pages)

with st.sidebar:
    st.markdown(f"### 🏘️ {APP_TITLE}")
    st.caption("地区単位の見守り・施策検討支援ツール")
    st.markdown("---")

    # 評価パターンの切り替え（画面上部＝サイドバーに常時表示。全画面に即時反映される）
    pattern_names = list_pattern_names()
    if pattern_names:
        current = get_current_pattern_name()
        options = pattern_names if current in pattern_names else pattern_names + [current]
        selected_pattern = st.selectbox(
            "評価パターン", options=options, index=options.index(current), key="global_pattern_select",
        )
        if selected_pattern != current and selected_pattern in pattern_names:
            apply_pattern(selected_pattern)
            st.rerun()
    st.markdown("---")

navigation.run()

with st.sidebar:
    st.markdown("---")
    st.caption(f"バージョン: {APP_VERSION}")
