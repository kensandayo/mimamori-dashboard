# -*- coding: utf-8 -*-
"""
1_🗺️_地域マップ.py
---------------------
地区ごとに優先度で色分けした地図を表示する画面です。
マーカーをクリックすると地区名・順位・総合スコア・優先度が確認できます。
"""

import streamlit as st
from streamlit_folium import st_folium

from utils.config import APP_TITLE, COL_NAME, COL_RANK, COL_SCORE, COL_PRIORITY
from utils.state import init_state, get_scored_data, get_weights
from utils.scoring import generate_reasons, generate_recommendations
from components.header import render_header, render_footer
from components.map_view import build_priority_map

st.set_page_config(page_title=f"地域マップ | {APP_TITLE}", page_icon="🗺️", layout="wide")
init_state()

st.title("🗺️ 地域マップ")
render_header()

scored_df = get_scored_data()
weights = get_weights()

st.caption("マーカーの色は優先度を表します（赤：高 / 黄：中 / 青：低）。クリックで詳細をポップアップ表示します。")

col_map, col_detail = st.columns([2, 1])

with col_map:
    fmap = build_priority_map(scored_df)
    map_state = st_folium(fmap, width=None, height=560, returned_objects=["last_object_clicked_tooltip"])

with col_detail:
    st.markdown("#### 地区詳細")
    # クリックされた地区名をツールチップ文字列から抽出（"地区名（優先度）"の形式）
    clicked_name = None
    if map_state and map_state.get("last_object_clicked_tooltip"):
        clicked_name = map_state["last_object_clicked_tooltip"].split("（")[0]

    if clicked_name is None:
        st.selectbox(
            "地図上のマーカーをクリックするか、ここから地区を選んでください",
            options=scored_df[COL_NAME].tolist(),
            key="map_district_fallback",
        )
        clicked_name = st.session_state["map_district_fallback"]

    detail_row = scored_df[scored_df[COL_NAME] == clicked_name]
    if not detail_row.empty:
        row = detail_row.iloc[0]
        st.markdown(f"### {row[COL_NAME]}")
        m1, m2 = st.columns(2)
        m1.metric("順位", f"{int(row[COL_RANK])} 位")
        m2.metric("総合スコア", f"{row[COL_SCORE]:.1f} 点")
        st.markdown(f"**優先度: {row[COL_PRIORITY]}**")

        st.markdown("**各指標**")
        st.write(f"- 高齢化率: {row['高齢化率']:.1f}%")
        st.write(f"- 単身高齢者割合: {row['単身高齢者割合']:.1f}%")
        st.write(f"- 医療アクセス指数: {row['医療アクセス']:.1f}")
        st.write(f"- 公共交通指数: {row['公共交通']:.1f}")

        st.markdown("**判定理由**")
        for reason in generate_reasons(row, scored_df):
            st.write(f"・{reason}")

        st.markdown("**推奨施策**")
        for rec in generate_recommendations(row, scored_df, weights):
            st.write(f"・{rec}")

render_footer()
