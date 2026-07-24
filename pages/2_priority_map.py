# -*- coding: utf-8 -*-
"""
map.py
--------
地域マップ画面です。このアプリの中心機能として、以下を提供します。

- 地区ごとの優先度による色分け
- 地区名の常時ラベル表示
- 凡例表示
- 地区検索（入力すると地図がその地区にズームし、マーカーを強調表示）
- マーカー／地区一覧のクリックによる詳細表示（自動分析コメント・推奨対応例つき）
"""

from __future__ import annotations

import streamlit as st
from streamlit_folium import st_folium

from utils.config import COL_NAME, COL_RANK, COL_SCORE, COL_PRIORITY
from utils.state import get_scored_data, get_weights
from utils.scoring import generate_analysis_comments, generate_recommendations
from components.header import render_header, render_footer
from components.map_view import build_priority_map

st.title("地域マップ")
render_header(page_caption="マーカーの色は優先度を表します（赤：高 / 黄：中 / 青：低）。クリックで詳細をポップアップ表示します。")

scored_df = get_scored_data()
weights = get_weights()
district_names = scored_df[COL_NAME].tolist()

# ------------------------------------------------------------
# 地区検索（見つかった地区にズーム＆ハイライト）
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
    fmap = build_priority_map(scored_df, highlight_name=highlight_name)
    map_state = st_folium(fmap, width=None, height=580, returned_objects=["last_object_clicked_tooltip"])

with col_detail:
    st.markdown("#### 地区詳細")

    # クリックされた地区名をツールチップ文字列から抽出（"地区名（優先度: 高）"の形式）
    clicked_name = None
    if map_state and map_state.get("last_object_clicked_tooltip"):
        clicked_name = map_state["last_object_clicked_tooltip"].split("（")[0]

    # クリック・検索がなければ地区選択セレクトボックスで補う
    default_name = clicked_name or highlight_name
    if default_name not in district_names:
        default_name = district_names[0]

    selected_name = st.selectbox(
        "地図上のマーカーをクリックするか、ここから地区を選んでください",
        options=district_names,
        index=district_names.index(default_name),
        key="map_district_select",
    )

    row = scored_df[scored_df[COL_NAME] == selected_name].iloc[0]

    st.markdown(f"### {row[COL_NAME]}")
    m1, m2 = st.columns(2)
    m1.metric("順位", f"{int(row[COL_RANK])} 位")
    m2.metric("総合スコア", f"{row[COL_SCORE]:.1f} 点")
    st.markdown(f"**優先度：{row[COL_PRIORITY]}**")

    st.markdown("**各指標**")
    st.write(f"- 高齢化率：{row['高齢化率']:.1f}%")
    st.write(f"- 単身高齢者割合：{row['単身高齢者割合']:.1f}%")
    st.write(f"- 医療アクセス指数：{row['医療アクセス']:.1f}")
    st.write(f"- 公共交通指数：{row['公共交通']:.1f}")

    st.markdown("**自動分析コメント**")
    for comment in generate_analysis_comments(row, scored_df):
        st.write(f"・{comment}")

    st.markdown("**推奨される対応例**")
    for rec in generate_recommendations(row, scored_df, weights):
        st.write(f"・{rec}")

render_footer()
