# -*- coding: utf-8 -*-
"""
dashboard.py
--------------
ダッシュボード画面です。地区数・高優先地区数・平均スコア・TOP5・
データ情報・現在の評価パターンを簡潔に表示します。
"""

from __future__ import annotations

import streamlit as st

from utils.config import COL_SCORE, COL_PRIORITY, COL_RANK, COL_NAME, PRIORITY_HIGH
from utils.state import get_scored_data, get_data_source_info, get_current_pattern_name
from components.header import render_header, render_footer
from components.cards import render_metric_cards, render_info_strip

st.title("ダッシュボード")
render_header(page_caption="市内全地区の現状を一目で確認できます。")

scored_df = get_scored_data()
source_info = get_data_source_info()

st.caption(f"現在の評価パターン：**{get_current_pattern_name()}**（「設定・データ管理」画面で切り替えできます）")

n_districts = len(scored_df)
n_high_priority = int((scored_df[COL_PRIORITY] == PRIORITY_HIGH).sum())
avg_score = scored_df[COL_SCORE].mean()

render_metric_cards([
    {"label": "地区数", "value": f"{n_districts} 地区"},
    {"label": "高優先地区数", "value": f"{n_high_priority} 地区", "caption": "優先度「高」の地区数"},
    {"label": "平均スコア", "value": f"{avg_score:.1f} 点", "caption": "全地区の総合スコア平均"},
])

st.write("")
st.markdown("#### 優先度が高い地区（TOP5）")
top5 = scored_df.sort_values(COL_RANK).head(5)[[COL_RANK, COL_NAME, COL_SCORE, COL_PRIORITY]]
st.dataframe(
    top5, use_container_width=True, hide_index=True,
    column_config={COL_SCORE: st.column_config.ProgressColumn(COL_SCORE, min_value=0, max_value=100, format="%.1f点")},
)

st.write("")
st.markdown("#### データ情報")
render_info_strip([
    {"label": "データ出典", "value": source_info["source_name"]},
    {"label": "対象年度", "value": source_info["target_year"]},
    {"label": "データ更新日", "value": source_info["updated_at"]},
])

st.write("")
st.info(
    "左側のメニューから「地域マップ」「ランキング」「比較」「地区詳細」"
    "「シミュレーション」「設定・データ管理」「AI相談」「市全体分析」の各画面に移動できます。",
    icon="👈",
)

render_footer()
