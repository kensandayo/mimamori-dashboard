# -*- coding: utf-8 -*-
"""
app.py
--------
アプリのエントリーポイントです。
Streamlitのマルチページアプリでは、このファイルが最初に表示される
「①ダッシュボード」画面を兼ねています。

他のページ（地域マップ、ランキングなど）は pages/ フォルダの中にあり、
画面左のサイドバーから切り替えられます。
"""

import streamlit as st

from utils.config import APP_TITLE, COL_SCORE, COL_PRIORITY, COL_AGING, COL_SINGLE_ELDERLY, PRIORITY_HIGH
from utils.state import init_state, get_scored_data, get_data_source_info
from components.header import render_header, render_footer

# ページ全体の基本設定（タイトル・レイアウト・アイコン）
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🏘️",
    layout="wide",
)

# session_stateの初期化（サンプルデータ・重みの初期値をセット）
init_state()

st.title(f"🏘️ {APP_TITLE}")
render_header()

# 現在のデータにスコアを計算して取得
scored_df = get_scored_data()
source_info = get_data_source_info()

st.markdown("### 📊 ダッシュボード")
st.caption("市内全地区の現状を一目で確認できます。")

# ------------------------------------------------------------
# カード形式のサマリー表示
# ------------------------------------------------------------
n_districts = len(scored_df)
avg_score = scored_df[COL_SCORE].mean()
n_high_priority = (scored_df[COL_PRIORITY] == PRIORITY_HIGH).sum()
avg_aging = scored_df[COL_AGING].mean()
avg_single_elderly = scored_df[COL_SINGLE_ELDERLY].mean()

card_style = """
<div style="background-color:white; border:1px solid #dbe3ec; border-radius:10px;
            padding:16px; text-align:center; box-shadow:0 1px 3px rgba(0,0,0,0.06);">
    <div style="font-size:13px; color:#556; margin-bottom:6px;">{label}</div>
    <div style="font-size:26px; font-weight:700; color:#1d3557;">{value}</div>
</div>
"""

row1 = st.columns(3)
with row1[0]:
    st.markdown(card_style.format(label="地区数", value=f"{n_districts} 地区"), unsafe_allow_html=True)
with row1[1]:
    st.markdown(card_style.format(label="平均優先度スコア", value=f"{avg_score:.1f} 点"), unsafe_allow_html=True)
with row1[2]:
    st.markdown(card_style.format(label="優先度「高」の地区数", value=f"{n_high_priority} 地区"), unsafe_allow_html=True)

st.write("")
row2 = st.columns(3)
with row2[0]:
    st.markdown(card_style.format(label="平均高齢化率", value=f"{avg_aging:.1f} %"), unsafe_allow_html=True)
with row2[1]:
    st.markdown(card_style.format(label="平均単身高齢者割合", value=f"{avg_single_elderly:.1f} %"), unsafe_allow_html=True)
with row2[2]:
    st.markdown(card_style.format(label="データ更新日時", value=source_info["updated_at"]), unsafe_allow_html=True)

st.caption(f"データ出典: {source_info['source_name']}")

st.write("")
st.info(
    "左側のメニューから「地域マップ」「ランキング」「比較」「地区レポート」"
    "「シミュレーション」「設定・データ管理」の各画面に移動できます。",
    icon="👈",
)

# ------------------------------------------------------------
# 優先度上位地区の簡易プレビュー
# ------------------------------------------------------------
st.markdown("### ⚠️ 優先度が高い地区（上位5地区）")
top5 = scored_df.sort_values("順位").head(5)[["順位", "地区名", "総合スコア", "優先度"]]
st.dataframe(top5, use_container_width=True, hide_index=True)

render_footer()
