# -*- coding: utf-8 -*-
"""
city_analysis.py (pages/)
----------------------------
「市全体分析」画面です。地区単位ではなく、宇都宮市全体で見たときに
どの評価項目が確認候補になっているか、どの地区が特に該当するか、
参考になる他自治体施策は何かをまとめて確認できます。

このシステムは「この項目に対応が必要」と断定するものではなく、
自治体職員が施策を検討する際の参考情報を提示するものです。
"""

from __future__ import annotations

import streamlit as st

from utils.config import COL_NAME, COL_SCORE, COL_RANK
from utils.state import get_scored_data
from utils.parameter_loader import load_active_parameters
from utils.scoring import (
    get_city_health_scores, get_policy_candidates, get_indicator_health_scores,
    get_city_category_health_scores,
)
from components.header import render_header, render_footer
from components.charts import build_health_score_bar

st.title("市全体分析（施策検討）")
render_header(page_caption="宇都宮市全体で見たときの確認候補となる評価項目と、施策検討の参考情報をまとめます。"
                          "現在の評価パターンに基づいて算出しています。")

scored_df = get_scored_data()
parameters = load_active_parameters()

city_score = scored_df[COL_SCORE].mean()
st.markdown("### 宇都宮市 総合スコア（全地区平均）")
st.markdown(f"## {city_score:.1f} / 100")
st.caption("本スコアは地域の状況を比較・検討するための参考指標であり、行政サービスの良し悪しを正式に評価する点数ではありません。")

st.markdown("---")

# ------------------------------------------------------------
# カテゴリ別の状況（人口・世帯／介護・健康／移動・生活環境…）
# ------------------------------------------------------------
st.markdown("### カテゴリ別の状況（市全体平均）")
st.caption(
    "評価項目を「人口・世帯」「移動・生活環境」などのカテゴリで束ね、カテゴリ単位の傾向を確認できます。"
    "カテゴリの構成は「設定・データ管理」画面の評価項目管理で変更できます。"
)
city_category_scores = get_city_category_health_scores(scored_df, parameters)
if city_category_scores:
    cat_cols = st.columns(len(city_category_scores))
    for col, c in zip(cat_cols, city_category_scores):
        col.metric(c["label"], f"{c['score']:.1f}点", f"項目数 {c['param_count']}")
else:
    st.caption("有効な評価項目が登録されていません。")

st.markdown("---")

# ------------------------------------------------------------
# 確認候補となる項目（市全体平均）
# ------------------------------------------------------------
st.markdown("### 確認候補となる項目（市全体平均）")
st.caption("評価項目を「高いほど良い」共通スケール（0〜100点）で比較し、点数が相対的に低い項目を確認候補として表示しています。")
city_health = get_city_health_scores(scored_df, parameters)
st.plotly_chart(
    build_health_score_bar([h["label"] for h in city_health], [h["score"] for h in city_health],
                           title="評価項目別 市全体平均スコア（高いほど良い）"),
    use_container_width=True,
)
for i, h in enumerate(city_health, start=1):
    st.write(f"{i}位　{h['label']}　{h['score']:.1f}点")

st.markdown("---")

# ------------------------------------------------------------
# 確認候補ごとの詳細（対象候補地区・参考事例）
# ------------------------------------------------------------
st.markdown("### 確認候補ごとの詳細")
top_weak = [h for h in city_health if h["score"] < 70][:3]

if not top_weak:
    st.success("市全体で見て、すべての評価項目が70点以上であり、特に確認候補となる項目は見当たりません。")
else:
    candidates = get_policy_candidates(top_weak)
    for weak in top_weak:
        st.markdown(f"#### 「{weak['label']}」について確認する余地があります")
        st.write(f"宇都宮市全体で見ると、{weak['label']}のスコアが相対的に低い状況です（市全体平均：{weak['score']:.1f}点）。")

        district_scores = []
        for _, row in scored_df.iterrows():
            h = next(x for x in get_indicator_health_scores(row, parameters) if x["param_id"] == weak["param_id"])
            district_scores.append({"地区名": row[COL_NAME], "スコア": h["score"], "順位": row[COL_RANK]})
        district_scores.sort(key=lambda x: x["スコア"])
        worst_districts = district_scores[:3]

        policies = candidates.get(weak["param_id"], [])

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**確認候補となる地区**")
            for d in worst_districts:
                st.write(f"・{d['地区名']}（{weak['label']}：{d['スコア']:.1f}点）")
        with c2:
            st.markdown("**参考自治体**")
            if not policies:
                st.caption("現在、この評価項目に対応する参考事例は登録されていません。")
            else:
                for policy in policies:
                    pref = policy.get("prefecture", "")
                    st.write(f"・{pref} {policy['municipality']}：{policy['policy_name']}")

        if policies:
            st.markdown("**関連する施策事例**")
            for policy in policies:
                pref = policy.get("prefecture", "")
                with st.expander(f"{pref} {policy['municipality']}：{policy['policy_name']}"):
                    st.write(policy.get("description", policy.get("summary", "")))
                    st.caption(f"対象：{policy['target']}")
                    if policy.get("cost"):
                        st.write(f"💰 料金：{policy['cost']}")
                    if policy.get("frequency"):
                        st.write(f"🔁 利用回数・頻度：{policy['frequency']}")
                    if policy.get("features"):
                        st.write(f"📝 特徴：{policy['features']}")
                    url = policy.get("url") or policy.get("official_url")
                    if url:
                        st.markdown(f"[自治体公式ページを確認]({url})")
                    updated = policy.get("updated_at") or policy.get("last_checked", "未確認")
                    st.caption(f"情報確認日：{updated}")

        st.warning(
            f"上記は{weak['label']}のスコアが相対的に低い地区・他自治体の実施例をもとにした参考情報です。"
            "この評価だけで施策の必要性を判断するものではなく、実際の施策検討では地域の状況・既存サービス・"
            "利用実績・住民ニーズ等を合わせて確認する必要があります。",
            icon="⚠️",
        )
        st.markdown("---")

render_footer()
