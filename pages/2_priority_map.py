# -*- coding: utf-8 -*-
"""
priority_map.py
------------------
地域マップ画面です。このアプリの中心機能として、以下を提供します。

- 総合スコア（優先度）だけでなく、任意の評価項目で色分け表示を切り替え可能（動的）
- 地区名の常時ラベル表示・凡例表示
- 地区検索（ヒットした地区にズーム＆ハイライト）
- マーカー／地区一覧のクリックによる詳細表示
- 「地区詳細を見る」から地区詳細画面へ遷移
"""

from __future__ import annotations

import streamlit as st
from streamlit_folium import st_folium

from utils.config import COL_NAME, COL_RANK, COL_SCORE, COL_PRIORITY
from utils.state import get_scored_data
from utils.parameter_loader import load_active_parameters
from utils.scoring import generate_analysis_comments
from components.header import render_header, render_footer
from components.map_view import build_priority_map

st.title("地域マップ")
render_header(page_caption="マーカーの色は表示中の項目の状況を表します（赤：課題あり／黄：中／青：良好）。")

scored_df = get_scored_data()
parameters = load_active_parameters()
district_names = scored_df[COL_NAME].tolist()

# ------------------------------------------------------------
# 表示する項目の切り替え（動的：マスタに登録された評価項目が自動で選択肢になる）
# ------------------------------------------------------------
display_options = ["総合スコア（優先度）"] + [p["label"] for p in parameters]
display_choice = st.selectbox("マップに表示する項目", options=display_options)
display_param = None
if display_choice != "総合スコア（優先度）":
    display_param = next(p for p in parameters if p["label"] == display_choice)

# ------------------------------------------------------------
# 地区検索
# ------------------------------------------------------------
search_col, _ = st.columns([2, 3])
with search_col:
    search_text = st.text_input("🔍 地区名で検索", "", placeholder="例：中央地区")

highlight_name = None
if search_text:
    matches = [name for name in district_names if search_text in name]
    if matches:
        highlight_name = matches[0]
        if len(matches) > 1:
            st.caption(f"「{search_text}」に一致する地区が{len(matches)}件見つかりました。最初の一致（{highlight_name}）を表示しています。")
    else:
        st.warning(f"「{search_text}」に一致する地区が見つかりませんでした。")

col_map, col_detail = st.columns([2, 1])

with col_map:
    fmap = build_priority_map(scored_df, highlight_name=highlight_name, display_param=display_param)
    map_state = st_folium(fmap, width=None, height=580, returned_objects=["last_object_clicked_tooltip"])

with col_detail:
    st.markdown("#### 地区詳細")

    clicked_name = None
    if map_state and map_state.get("last_object_clicked_tooltip"):
        clicked_name = map_state["last_object_clicked_tooltip"].split("（")[0]

    default_name = clicked_name or highlight_name
    if default_name not in district_names:
        default_name = district_names[0]

    selected_name = st.selectbox(
        "地図上のマーカーをクリックするか、ここから地区を選んでください",
        options=district_names, index=district_names.index(default_name), key="map_district_select",
    )

    row = scored_df[scored_df[COL_NAME] == selected_name].iloc[0]

    st.markdown(f"### {row[COL_NAME]}")
    m1, m2 = st.columns(2)
    m1.metric("順位", f"{int(row[COL_RANK])} 位")
    m2.metric("総合スコア", f"{row[COL_SCORE]:.1f} 点")
    st.markdown(f"**優先度：{row[COL_PRIORITY]}**")

    st.markdown("**各評価項目**")
    for p in parameters:
        st.write(f"- {p['label']}：{row[p['key']]:.1f}{p['unit'] if p['unit'] == '%' else ''}")

    st.markdown("**自動分析コメント**")
    for comment in generate_analysis_comments(row, scored_df, parameters):
        st.write(f"・{comment}")

    if st.button("📋 この地区の詳細を見る", use_container_width=True):
        st.session_state["jump_to_district"] = selected_name
        st.switch_page("pages/5_district_report.py")

render_footer()
