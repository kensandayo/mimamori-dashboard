# -*- coding: utf-8 -*-
"""
report.py
-----------
地区を1つ選ぶと、以下をまとめて確認できる「地区詳細」画面です。

- 順位
- 総合スコア
- 4指標の値
- 平均との差
- 自動分析コメント（ルールベースの機械的な差分説明。AIによる判定ではありません）
- 推奨される対応例（ルールベースの参考案）
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from utils.config import COL_NAME, COL_RANK, COL_SCORE, COL_PRIORITY, INDICATORS, PRIORITY_COLORS, COLOR_PRIMARY
from utils.state import get_scored_data, get_weights
from utils.scoring import (
    get_city_average, get_contribution_breakdown, get_indicator_diffs,
    generate_analysis_comments, generate_recommendations,
)
from components.header import render_header, render_footer
from components.charts import build_diff_bar_chart

st.title("地区詳細")
render_header(page_caption="地区を選択すると、順位・スコア・平均との差・自動分析コメントを確認できます。")

scored_df = get_scored_data()
weights = get_weights()
city_avg = get_city_average(scored_df)

target = st.selectbox("詳細を見る地区を選んでください", options=scored_df[COL_NAME].tolist())
row = scored_df[scored_df[COL_NAME] == target].iloc[0]

# ------------------------------------------------------------
# サマリー
# ------------------------------------------------------------
priority_color = PRIORITY_COLORS.get(row[COL_PRIORITY], COLOR_PRIMARY)
st.markdown(f"## {target}")
c1, c2, c3 = st.columns(3)
c1.metric("総合スコア", f"{row[COL_SCORE]:.1f} 点", f"{row[COL_SCORE] - city_avg[COL_SCORE]:+.1f}（対平均）")
c2.metric("順位", f"{int(row[COL_RANK])} 位 / {len(scored_df)}地区")
c3.markdown(
    f"""
    <div style="padding-top:8px;">
        <span style="font-size:13px; color:#6b7280;">優先度</span><br>
        <span style="font-size:22px; font-weight:700; color:{priority_color};">{row[COL_PRIORITY]}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

# ------------------------------------------------------------
# 4指標と平均との差
# ------------------------------------------------------------
st.markdown("### 4指標の値と平均との差")
diffs = get_indicator_diffs(row, scored_df)

diff_cols = st.columns(len(diffs))
for col, d in zip(diff_cols, diffs):
    unit = "%" if d["unit"] == "%" else ""
    col.metric(d["label"], f"{d['value']:.1f}{unit}", f"{d['diff']:+.1f}（対平均）")

st.plotly_chart(
    build_diff_bar_chart([d["label"] for d in diffs], [d["diff"] for d in diffs]),
    use_container_width=True,
)

st.markdown("---")

# ------------------------------------------------------------
# スコア内訳（各指標が何点寄与しているか）
# ------------------------------------------------------------
st.markdown("### スコア内訳（各指標の寄与点）")
breakdown = get_contribution_breakdown(row, weights)

fig = go.Figure(go.Bar(
    x=[b["contribution"] for b in breakdown],
    y=[b["label"] for b in breakdown],
    orientation="h",
    marker_color=COLOR_PRIMARY,
    text=[f"{b['contribution']:.1f}点" for b in breakdown],
    textposition="outside",
))
fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=260, xaxis_title="寄与点")
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ------------------------------------------------------------
# 自動分析コメント
# ------------------------------------------------------------
st.markdown("### 自動分析コメント")
st.caption("※ AIによる判定ではなく、あらかじめ決めたルールに基づく機械的な差分説明です。")
for comment in generate_analysis_comments(row, scored_df):
    st.write(f"・{comment}")

st.markdown("---")

# ------------------------------------------------------------
# 推奨される対応例
# ------------------------------------------------------------
st.markdown("### 推奨される対応例")
for rec in generate_recommendations(row, scored_df, weights):
    st.write(f"✅ {rec}")

st.caption("※ 推奨される対応例はルールベースで生成された参考案です。最終判断は自治体職員が行ってください。")

st.markdown("---")

# ------------------------------------------------------------
# 各指標の説明・出典
# ------------------------------------------------------------
with st.expander("各指標の説明・出典を見る"):
    for indicator in INDICATORS:
        st.markdown(f"**{indicator['label']}**（{indicator['unit']}）")
        st.write(indicator["description"])
        st.caption(f"出典：{indicator['source']}")
        st.write("")

render_footer()
