# -*- coding: utf-8 -*-
"""
ranking.py
------------
全地区を一覧表示し、並び替え・検索・優先度フィルターができる画面です。
指標の列・フィルターは、マスタに登録されている評価項目から動的に作られます。
"""

from __future__ import annotations

import streamlit as st

from utils.config import COL_NAME, COL_RANK, COL_SCORE, COL_PRIORITY
from utils.state import get_scored_data
from utils.parameter_loader import load_active_parameters
from components.header import render_header, render_footer

st.title("ランキング")
render_header(page_caption="全地区の総合スコア・各評価項目を一覧で確認できます。")

scored_df = get_scored_data()
parameters = load_active_parameters()

# ------------------------------------------------------------
# フィルター（検索・優先度・評価項目の範囲は動的に生成）
# ------------------------------------------------------------
with st.expander("🔍 絞り込み条件", expanded=True):
    f1, f2 = st.columns(2)
    with f1:
        search_text = st.text_input("地区名で検索", "")
    with f2:
        priority_filter = st.multiselect("優先度で絞り込み", options=["高", "中", "低"], default=["高", "中", "低"])

    range_filters = {}
    param_cols = st.columns(min(len(parameters), 4)) if parameters else []
    for i, p in enumerate(parameters):
        with param_cols[i % len(param_cols)]:
            range_filters[p["key"]] = st.slider(f"{p['label']}の範囲", 0, 100, (0, 100), key=f"range_{p['weight_key']}")

filtered = scored_df.copy()
if search_text:
    filtered = filtered[filtered[COL_NAME].str.contains(search_text, case=False, na=False)]
filtered = filtered[filtered[COL_PRIORITY].isin(priority_filter)]
for col, (lo, hi) in range_filters.items():
    filtered = filtered[(filtered[col] >= lo) & (filtered[col] <= hi)]

st.caption(f"該当地区数：{len(filtered)} ／ 全{len(scored_df)}地区")

# ------------------------------------------------------------
# 並び替え可能なテーブル表示
# ------------------------------------------------------------
sort_options = [COL_RANK, COL_SCORE] + [p["key"] for p in parameters]
sort_col = st.selectbox("並び替え基準", options=sort_options, index=0)
ascending = st.checkbox("昇順で並び替え", value=(sort_col == COL_RANK))

display_cols = [COL_RANK, COL_NAME, COL_SCORE, COL_PRIORITY] + [p["key"] for p in parameters]
table = filtered.sort_values(sort_col, ascending=ascending)[display_cols]

st.dataframe(
    table, use_container_width=True, hide_index=True,
    column_config={COL_SCORE: st.column_config.ProgressColumn(COL_SCORE, min_value=0, max_value=100, format="%.1f")},
)

render_footer()
