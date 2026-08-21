# -*- coding: utf-8 -*-
"""
simulation.py (pages/)
------------------------
What-if分析画面です。任意の評価項目を選び、「改善後の想定値」をスライダーで
指定すると、総合スコア・順位・地図がどう変わるかを試算します。

【重要】
「デマンド交通を導入したら+10点」のような根拠のない自動加点はしていません。
あくまで「評価項目の値が指定した想定値まで改善したと仮定した場合」の
機械的な再計算であり、施策の実際の効果を予測するものではありません。
"""

from __future__ import annotations

import streamlit as st
from streamlit_folium import st_folium

from utils.config import COL_NAME, COL_RANK, COL_SCORE, COL_PRIORITY
from utils.state import get_raw_data, get_weights
from utils.parameter_loader import load_active_parameters
from utils.scoring import get_indicator_health_scores
from utils.simulation import simulate_parameter_change
from components.header import render_header, render_footer
from components.map_view import build_priority_map

st.title("シミュレーション（What-if分析）")
render_header()

st.warning(
    "この機能はWhat-if分析（仮定に基づく試算）です。「改善後の想定値」は職員の方が任意に"
    "設定する仮の値であり、施策の実際の効果を予測するものではありません。あくまで「評価項目が"
    "改善した場合にスコア・順位・地図がどう変わるか」を機械的に試算する参考情報です。",
    icon="⚠️",
)

df = get_raw_data()
weights = get_weights()
parameters = load_active_parameters()

target = st.selectbox("シミュレーション対象の地区を選んでください", options=df[COL_NAME].tolist())
target_row = df[df[COL_NAME] == target].iloc[0]

param_labels = [p["label"] for p in parameters]
param_choice = st.selectbox("改善を仮定する評価項目を選んでください", options=param_labels)
param = next(p for p in parameters if p["label"] == param_choice)

current_health = next(
    h for h in get_indicator_health_scores(target_row, parameters) if h["param_id"] == param["weight_key"]
)

st.markdown(f"#### 現在の「{param['label']}」健全度スコア：{current_health['score']:.1f} 点")
target_health_score = st.slider(
    "改善後の想定値（0〜100点、高いほど良い共通スケール）",
    min_value=0, max_value=100, value=int(min(100, current_health["score"] + 20)),
    help="この値は職員の方が仮定として設定する想定値です。実際に施策を導入した場合の効果を保証するものではありません。",
)

run = st.button("What-if分析を実行", type="primary")

if run:
    result = simulate_parameter_change(df, weights, target, param["weight_key"], target_health_score, parameters)
    before_row = result["before_row"]
    after_row = result["after_row"]

    st.markdown(f"### {target} の試算結果")
    st.markdown(
        f"**{param['label']}**　{result['before_health_score']:.1f}点　→　改善後想定値　{result['after_health_score']:.1f}点"
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("総合スコア", f"{after_row[COL_SCORE]:.1f} 点",
              f"{after_row[COL_SCORE] - before_row[COL_SCORE]:+.1f} 点", delta_color="inverse")
    rank_change = int(before_row[COL_RANK]) - int(after_row[COL_RANK])
    c2.metric("順位", f"{int(after_row[COL_RANK])} 位",
              f"{rank_change:+d} 位変化" if rank_change != 0 else "変化なし")
    c3.metric("優先度", after_row[COL_PRIORITY], f"変更前：{before_row[COL_PRIORITY]}")

    st.markdown(f"地区総合スコア　{before_row[COL_SCORE]:.1f} → {after_row[COL_SCORE]:.1f}")

    st.markdown("#### 地図の再計算結果（仮定反映後）")
    st.caption("仮定を反映した後の優先度で地図を再描画しています。対象地区を強調表示しています。")
    after_map = build_priority_map(result["after_df"], highlight_name=target)
    st_folium(after_map, width=None, height=480, returned_objects=[])

    st.caption("※ これは施策の実際の効果を予測するものではなく、指標が改善した場合の仮想シミュレーションです。")
else:
    st.info("評価項目と改善後の想定値を設定し、「What-if分析を実行」ボタンを押してください。")

render_footer()
