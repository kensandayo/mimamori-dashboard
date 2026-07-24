# -*- coding: utf-8 -*-
"""
simulation.py (pages/)
------------------------
What-if分析画面です。
「もしこの施策で〇〇が改善したら、スコア・順位・地図はどう変わるか」を
簡易的に試算します。

【重要】
ここで設定する改善量はすべて仮定値です。実際の施策効果を保証するものではありません。
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from utils.config import COL_NAME, COL_RANK, COL_SCORE, COL_PRIORITY
from utils.state import get_raw_data, get_weights
from utils.simulation import simulate_improvement
from components.header import render_header, render_footer
from components.map_view import build_priority_map

st.title("シミュレーション（What-if分析）")
render_header()

st.warning(
    "この機能はWhat-if分析（仮定に基づく試算）です。設定する改善量はすべて仮定値であり、"
    "実際の施策効果を保証するものではありません。あくまで「指標が変化した場合にスコア・"
    "順位・地図がどう変わるか」を機械的に試算する参考情報です。",
    icon="⚠️",
)

df = get_raw_data()
weights = get_weights()

target = st.selectbox("シミュレーション対象の地区を選んでください", options=df[COL_NAME].tolist())

st.markdown("#### 施策による指標の改善量（仮定値）を設定してください")
s1, s2 = st.columns(2)
with s1:
    medical_delta = st.slider("医療アクセス指数の改善量（仮定）", 0, 50, 10,
                               help="例：巡回診療の導入などを仮定した場合の改善量です。")
    aging_delta = st.slider("高齢化率の変化量（仮定, %）", -10, 10, 0,
                             help="通常、施策で直接動かせる指標ではありませんが、参考として試算できます。")
with s2:
    transport_delta = st.slider("公共交通指数の改善量（仮定）", 0, 50, 10,
                                 help="例：デマンド交通の導入などを仮定した場合の改善量です。")
    single_elderly_delta = st.slider("単身高齢者割合の変化量（仮定, %）", -10, 10, 0)

run = st.button("What-if分析を実行", type="primary")

if run:
    result = simulate_improvement(
        df, weights, target,
        medical_delta=medical_delta,
        transport_delta=transport_delta,
        aging_delta=aging_delta,
        single_elderly_delta=single_elderly_delta,
    )
    before_row = result["before_row"]
    after_row = result["after_row"]

    st.markdown(f"### {target} の試算結果")
    c1, c2, c3 = st.columns(3)
    c1.metric(
        "総合スコア",
        f"{after_row[COL_SCORE]:.1f} 点",
        f"{after_row[COL_SCORE] - before_row[COL_SCORE]:+.1f} 点",
        delta_color="inverse",  # スコア低下＝リスク低下＝良いことなので色を反転
    )
    rank_change = int(before_row[COL_RANK]) - int(after_row[COL_RANK])
    c2.metric(
        "順位",
        f"{int(after_row[COL_RANK])} 位",
        f"{rank_change:+d} 位変化" if rank_change != 0 else "変化なし",
    )
    c3.metric("優先度", after_row[COL_PRIORITY], f"変更前：{before_row[COL_PRIORITY]}")

    st.markdown("#### 変更前後の比較")
    summary = pd.DataFrame({
        "項目": ["総合スコア", "順位", "優先度"],
        "変更前": [f"{before_row[COL_SCORE]:.1f}点", f"{int(before_row[COL_RANK])}位", before_row[COL_PRIORITY]],
        "変更後（仮定反映後）": [f"{after_row[COL_SCORE]:.1f}点", f"{int(after_row[COL_RANK])}位", after_row[COL_PRIORITY]],
    })
    st.dataframe(summary, use_container_width=True, hide_index=True)

    st.markdown("#### 地図の再計算結果（仮定反映後）")
    st.caption("仮定を反映した後の優先度で地図を再描画しています。対象地区を強調表示しています。")
    after_map = build_priority_map(result["after_df"], highlight_name=target)
    st_folium(after_map, width=None, height=480, returned_objects=[])
else:
    st.info("上記のスライダーで施策の仮定を設定し、「What-if分析を実行」ボタンを押してください。")

render_footer()
