# -*- coding: utf-8 -*-
"""
comparison.py
---------------
比較機能画面です。以下2種類の比較ができます。
①選択地区 VS 全地区平均
②任意の2〜4地区比較
評価項目はマスタから動的に取得するため、項目を追加・削除しても自動的に反映されます。
"""

from __future__ import annotations

import streamlit as st

from utils.config import COL_NAME, COL_RANK, COL_SCORE, COL_PRIORITY
from utils.state import get_scored_data
from utils.parameter_loader import load_active_parameters
from utils.scoring import get_city_average
from components.header import render_header, render_footer
from components.charts import build_radar_chart, build_bar_comparison, build_diff_bar_chart

st.title("比較")
render_header(page_caption="地区どうし、または地区と全地区平均を比較できます。")

scored_df = get_scored_data()
parameters = load_active_parameters()
INDICATOR_COLS = [p["key"] for p in parameters]
INDICATOR_LABELS = [p["label"] for p in parameters]
AXES = list(zip(INDICATOR_LABELS, INDICATOR_COLS))

tab1, tab2 = st.tabs(["① 選択地区 VS 全地区平均", "② 任意の地区どうしの比較（2〜4地区）"])

with tab1:
    target = st.selectbox("比較する地区を選んでください", options=scored_df[COL_NAME].tolist(), key="vs_avg_target")
    target_row = scored_df[scored_df[COL_NAME] == target].iloc[0]
    city_avg = get_city_average(scored_df, parameters)

    c1, c2, c3 = st.columns(3)
    c1.metric("総合スコア", f"{target_row[COL_SCORE]:.1f} 点", f"{target_row[COL_SCORE] - city_avg[COL_SCORE]:+.1f}（対平均）")
    c2.metric("順位", f"{int(target_row[COL_RANK])} 位 / {len(scored_df)}地区")
    c3.metric("着目度", target_row[COL_PRIORITY])

    st.markdown("#### 指標別：平均との差")
    diffs = [target_row[col] - city_avg[col] for col in INDICATOR_COLS]
    st.plotly_chart(build_diff_bar_chart(INDICATOR_LABELS, diffs), use_container_width=True)

    st.markdown("#### 棒グラフ比較")
    bar_values = {label: [target_row[col], city_avg[col]] for label, col in AXES}
    st.plotly_chart(build_bar_comparison([target, "全地区平均"], bar_values, title=f"{target} と全地区平均の比較"), use_container_width=True)

    st.markdown("#### レーダーチャート比較")
    st.plotly_chart(
        build_radar_chart([{"name": target, "row": target_row}, {"name": "全地区平均", "row": city_avg}], AXES),
        use_container_width=True,
    )

with tab2:
    selected = st.multiselect(
        "比較したい地区を2〜4地区選んでください", options=scored_df[COL_NAME].tolist(),
        default=scored_df[COL_NAME].tolist()[:2], max_selections=4,
    )

    if len(selected) < 2:
        st.warning("比較には2地区以上選択してください。")
    else:
        rows = [scored_df[scored_df[COL_NAME] == name].iloc[0] for name in selected]

        st.markdown("#### 棒グラフ比較")
        bar_values = {label: [row[col] for row in rows] for label, col in AXES}
        st.plotly_chart(build_bar_comparison(selected, bar_values, title="選択地区の比較"), use_container_width=True)

        st.markdown("#### レーダーチャート比較")
        st.plotly_chart(
            build_radar_chart([{"name": name, "row": row} for name, row in zip(selected, rows)], AXES),
            use_container_width=True,
        )

        st.markdown("#### 総合スコア比較表")
        compare_table = scored_df[scored_df[COL_NAME].isin(selected)][
            [COL_NAME, COL_RANK, COL_SCORE, COL_PRIORITY] + INDICATOR_COLS
        ].sort_values(COL_RANK)
        st.dataframe(compare_table, use_container_width=True, hide_index=True)

render_footer()
