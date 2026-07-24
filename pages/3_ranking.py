# -*- coding: utf-8 -*-
"""
ranking.py
------------
全地区を一覧表示し、並び替え・検索・優先度フィルターができる画面です。
"""

from __future__ import annotations

import streamlit as st

from utils.config import (
    COL_NAME, COL_RANK, COL_SCORE, COL_PRIORITY,
    COL_AGING, COL_SINGLE_ELDERLY, COL_MEDICAL, COL_TRANSPORT,
)
from utils.state import get_scored_data
from components.header import render_header, render_footer

st.title("ランキング")
render_header(page_caption="全地区の総合スコア・各指標を一覧で確認できます。")

scored_df = get_scored_data()

# ------------------------------------------------------------
# フィルター（検索・優先度・指標の範囲）
# ------------------------------------------------------------
with st.expander("🔍 絞り込み条件", expanded=True):
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        search_text = st.text_input("地区名で検索", "")
    with f2:
        priority_filter = st.multiselect(
            "優先度で絞り込み", options=["高", "中", "低"], default=["高", "中", "低"]
        )
    with f3:
        aging_range = st.slider("高齢化率の範囲(%)", 0, 100, (0, 100))
    with f4:
        single_range = st.slider("単身高齢者割合の範囲(%)", 0, 100, (0, 100))

filtered = scored_df.copy()
if search_text:
    filtered = filtered[filtered[COL_NAME].str.contains(search_text, case=False, na=False)]
filtered = filtered[filtered[COL_PRIORITY].isin(priority_filter)]
filtered = filtered[
    (filtered[COL_AGING] >= aging_range[0]) & (filtered[COL_AGING] <= aging_range[1]) &
    (filtered[COL_SINGLE_ELDERLY] >= single_range[0]) & (filtered[COL_SINGLE_ELDERLY] <= single_range[1])
]

st.caption(f"該当地区数：{len(filtered)} ／ 全{len(scored_df)}地区")

# ------------------------------------------------------------
# 並び替え可能なテーブル表示
# ------------------------------------------------------------
sort_col = st.selectbox(
    "並び替え基準",
    options=[COL_RANK, COL_SCORE, COL_AGING, COL_SINGLE_ELDERLY, COL_MEDICAL, COL_TRANSPORT],
    index=0,
)
ascending = st.checkbox("昇順で並び替え", value=(sort_col == COL_RANK))

display_cols = [COL_RANK, COL_NAME, COL_SCORE, COL_PRIORITY, COL_AGING, COL_SINGLE_ELDERLY, COL_MEDICAL, COL_TRANSPORT]
table = filtered.sort_values(sort_col, ascending=ascending)[display_cols]

st.dataframe(
    table,
    use_container_width=True,
    hide_index=True,
    column_config={
        COL_SCORE: st.column_config.ProgressColumn(COL_SCORE, min_value=0, max_value=100, format="%.1f"),
    },
)

render_footer()
