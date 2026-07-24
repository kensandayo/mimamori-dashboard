# -*- coding: utf-8 -*-
"""
5_🔮_シミュレーション.py
--------------------------
「医療アクセスを改善したらスコアがどう変わるか」
「公共交通を改善したら順位がどう変わるか」を
簡易的に試算できる、試験的な機能です。
"""

import streamlit as st
import pandas as pd

from utils.config import APP_TITLE, COL_NAME, COL_RANK, COL_SCORE, COL_PRIORITY
from utils.state import init_state, get_raw_data, get_weights
from utils.simulation import simulate_improvement
from components.header import render_header, render_footer

st.set_page_config(page_title=f"シミュレーション | {APP_TITLE}", page_icon="🔮", layout="wide")
init_state()

st.title("🔮 政策効果シミュレーション（試験的機能）")
render_header()

st.warning(
    "この機能は試験的なものです。実際の政策効果を保証するものではなく、"
    "あくまで「指標が変化した場合にスコア・順位がどう変わるか」を機械的に試算するものです。",
    icon="⚠️",
)

df = get_raw_data()
weights = get_weights()

target = st.selectbox("シミュレーション対象の地区を選んでください", options=df[COL_NAME].tolist())

st.markdown("#### 施策による指標の改善量を設定してください")
s1, s2 = st.columns(2)
with s1:
    medical_delta = st.slider("医療アクセス指数の改善量", 0, 50, 10, help="値を上げるほどアクセスが改善する想定です。")
    aging_delta = st.slider("高齢化率の変化量(%)", -10, 10, 0, help="通常は施策では動かせない指標ですが、参考として試算できます。")
with s2:
    transport_delta = st.slider("公共交通指数の改善量", 0, 50, 10, help="値を上げるほど公共交通の利便性が改善する想定です。")
    single_elderly_delta = st.slider("単身高齢者割合の変化量(%)", -10, 10, 0)

if st.button("シミュレーションを実行", type="primary"):
    result = simulate_improvement(
        df, weights, target,
        medical_delta=medical_delta,
        transport_delta=transport_delta,
        aging_delta=aging_delta,
        single_elderly_delta=single_elderly_delta,
    )
    before_row = result["before_row"]
    after_row = result["after_row"]

    st.markdown(f"### {target} のシミュレーション結果")
    c1, c2, c3 = st.columns(3)
    c1.metric(
        "総合スコア",
        f"{after_row[COL_SCORE]:.1f} 点",
        f"{after_row[COL_SCORE] - before_row[COL_SCORE]:+.1f} 点",
        delta_color="inverse",  # スコアが下がる＝リスク低下＝良いことなので色を反転
    )
    c2.metric(
        "順位",
        f"{int(after_row[COL_RANK])} 位",
        f"{int(before_row[COL_RANK]) - int(after_row[COL_RANK]):+d} 位改善" if before_row[COL_RANK] != after_row[COL_RANK] else "変化なし",
    )
    c3.metric("優先度", after_row[COL_PRIORITY], f"（変更前: {before_row[COL_PRIORITY]}）")

    st.markdown("#### 変更前後の比較")
    summary = pd.DataFrame({
        "項目": ["総合スコア", "順位", "優先度"],
        "変更前": [f"{before_row[COL_SCORE]:.1f}点", f"{int(before_row[COL_RANK])}位", before_row[COL_PRIORITY]],
        "変更後": [f"{after_row[COL_SCORE]:.1f}点", f"{int(after_row[COL_RANK])}位", after_row[COL_PRIORITY]],
    })
    st.dataframe(summary, use_container_width=True, hide_index=True)
else:
    st.info("上記のスライダーで施策の想定を設定し、「シミュレーションを実行」ボタンを押してください。")

render_footer()
