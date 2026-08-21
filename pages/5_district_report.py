# -*- coding: utf-8 -*-
"""
district_report.py
---------------------
地区詳細画面です。以下の順で表示します。

① 地区基本情報（地区名・総合スコア・順位・各評価項目の値とスコア）
② 評価項目別の状況（現在値・スコア・市内平均との比較・市内順位、レーダー/棒グラフ）
③ 確認候補（スコアをもとに、確認・改善を検討する候補となる項目。断定はしない）
④ 関連する施策事例（他自治体施策マスタと連携。参考情報として提示）

このシステムは「この地区にはこの施策が必要」と断定するものではなく、
自治体職員が施策を検討する際の参考情報を提示するものです。

地域マップから「この地区の詳細を見る」で遷移してきた場合は、
その地区が自動的に選択されます。
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from utils.config import COL_NAME, COL_RANK, COL_SCORE, COL_PRIORITY, PRIORITY_COLORS, COLOR_PRIMARY
from utils.state import get_raw_data, get_scored_data, get_weights
from utils.parameter_loader import load_active_parameters
from utils.patterns import load_patterns
from utils.scoring import (
    get_city_average, get_city_health_scores, get_contribution_breakdown, get_indicator_status,
    get_policy_candidates, build_policy_reason, generate_analysis_comments, calculate_scores,
)
from components.header import render_header, render_footer
from components.charts import build_diff_bar_chart, build_health_score_bar, build_radar_chart

st.title("地区詳細")
render_header(page_caption="地区を選択すると、評価項目別の状況・確認候補・関連する施策事例を確認できます。")

scored_df = get_scored_data()
raw_df = get_raw_data()
weights = get_weights()
parameters = load_active_parameters()
city_avg = get_city_average(scored_df, parameters)
city_health_by_param = {h["param_id"]: h["score"] for h in get_city_health_scores(scored_df, parameters)}

district_names = scored_df[COL_NAME].tolist()
jump_target = st.session_state.pop("jump_to_district", None)
default_index = district_names.index(jump_target) if jump_target in district_names else 0

target = st.selectbox("詳細を見る地区を選んでください", options=district_names, index=default_index)
row = scored_df[scored_df[COL_NAME] == target].iloc[0]
status_list = get_indicator_status(row, scored_df, parameters)

# ============================================================
# ① 地区基本情報
# ============================================================
st.markdown("## ① 地区基本情報")

priority_color = PRIORITY_COLORS.get(row[COL_PRIORITY], COLOR_PRIMARY)
st.markdown(f"### {target}")
c1, c2, c3 = st.columns(3)
c1.metric("総合スコア", f"{row[COL_SCORE]:.1f} 点", f"{row[COL_SCORE] - city_avg[COL_SCORE]:+.1f}（対平均）")
c2.metric("順位", f"{int(row[COL_RANK])} 位 / {len(scored_df)}地区")
c3.markdown(
    f"""<div style="padding-top:8px;"><span style="font-size:13px; color:#6b7280;">優先度</span><br>
    <span style="font-size:22px; font-weight:700; color:{priority_color};">{row[COL_PRIORITY]}</span></div>""",
    unsafe_allow_html=True,
)

st.markdown("**評価項目一覧（値・スコア）**")
st.caption("評価項目は「評価項目管理」画面の登録内容から自動的に取得しています。項目を追加すると、ここにも自動的に表示されます。")
if status_list:
    basic_table_cols = st.columns(len(status_list))
    for col, s in zip(basic_table_cols, status_list):
        unit = "%" if s["unit"] == "%" else ""
        col.metric(s["label"], f"{s['value']:.1f}{unit}", f"{s['score']:.1f}点")

st.markdown("---")

# ============================================================
# ② 評価項目別の状況
# ============================================================
st.markdown("## ② 評価項目別の状況")
st.caption("現在値・スコア（高いほど良い共通スケール）・市内平均との比較・市内順位をまとめています。")

status_table = [{
    "評価項目": s["label"],
    "現在値": round(s["value"], 1),
    "スコア": s["score"],
    "市内平均との差": round(s["diff"], 1),
    "市内順位": f"{s['rank']} / {s['total_count']}",
} for s in status_list]
st.dataframe(status_table, use_container_width=True, hide_index=True)

chart_col1, chart_col2 = st.columns(2)
with chart_col1:
    st.plotly_chart(
        build_diff_bar_chart([s["label"] for s in status_list], [s["diff"] for s in status_list],
                             title="市平均との差"),
        use_container_width=True,
    )
with chart_col2:
    axes = [(p["label"], p["key"]) for p in parameters]
    st.plotly_chart(
        build_radar_chart([{"name": target, "row": row}, {"name": "市内平均", "row": city_avg}], axes),
        use_container_width=True,
    )

st.markdown("---")

# ============================================================
# ③ 確認候補
# ============================================================
st.markdown("## ③ 確認候補")
st.caption(
    "評価項目を「高いほど良い」共通スケール（0〜100点）で比較し、点数が相対的に低い項目を"
    "確認候補として表示しています。特定の対応が必要と判定するものではありません。"
)

sorted_status = sorted(status_list, key=lambda s: s["score"])
confirm_candidates = [s for s in sorted_status if s["score"] < 70][:3]

st.plotly_chart(
    build_health_score_bar([s["label"] for s in sorted_status], [s["score"] for s in sorted_status]),
    use_container_width=True,
)

if not confirm_candidates:
    st.success("すべての評価項目が70点以上であり、特に確認候補となる項目は見当たりません。")
else:
    for i, s in enumerate(confirm_candidates, start=1):
        city_score = city_health_by_param.get(s["param_id"])
        city_score_text = f"{city_score:.1f}点" if city_score is not None else "算出不可"
        st.markdown(f"**{i}. {s['label']}**")
        st.write(f"　スコア：{s['score']:.1f}点　／　市内平均：{city_score_text}")
        st.write(f"　→ {s['label']}について確認する余地があります。")

st.markdown("---")

# ============================================================
# ④ 関連する施策事例
# ============================================================
st.markdown("## ④ 関連する施策事例")
if not confirm_candidates:
    st.caption("現時点で確認候補となる評価項目がないため、関連する施策事例の表示はありません。")
else:
    candidates = get_policy_candidates(confirm_candidates)
    for s in confirm_candidates:
        policies = candidates.get(s["param_id"], [])
        st.markdown(f"#### {s['label']}に関連する参考事例")

        if not policies:
            st.caption("現在、この評価項目に対応する参考事例は登録されていません。")
            continue

        st.caption(
            f"この地区では「{s['label']}」が確認候補として抽出されているため、関連する他自治体の"
            "取り組みを参考情報として表示しています。この情報だけで施策の必要性や導入の適否を判断するものではありません。"
        )

        for policy in policies:
            with st.container(border=True):
                pref = policy.get("prefecture", "")
                st.markdown(f"**{pref} {policy['municipality']}：{policy['policy_name']}**")
                st.write(policy.get("description", policy.get("summary", "")))
                st.caption(f"対象：{policy['target']}")
                if policy.get("cost"):
                    st.write(f"💰 料金：{policy['cost']}")
                if policy.get("frequency"):
                    st.write(f"🔁 利用回数・頻度：{policy['frequency']}")
                if policy.get("features"):
                    st.write(f"📝 特徴：{policy['features']}")

                with st.expander("表示理由を見る"):
                    st.write(
                        f"この地区では「{s['label']}」の評価が市内平均と比較して低いため、"
                        "関連する他自治体の事例を参考情報として表示しています。"
                    )
                    for reason_line in build_policy_reason(row, scored_df, s):
                        st.write(f"・{reason_line}")
                    st.warning(
                        "この評価だけで施策の必要性を判断するものではありません。実際の施策検討では、"
                        "地域の状況・既存サービス・利用実績・住民ニーズ等を合わせて確認する必要があります。",
                        icon="⚠️",
                    )

                url = policy.get("url") or policy.get("official_url")
                if url:
                    st.markdown(f"[自治体公式ページを確認]({url})")
                updated = policy.get("updated_at") or policy.get("last_checked", "未確認")
                st.caption(f"情報確認日：{updated}　／　情報源：{policy.get('source', '自治体公式Webサイト')}"
                          "（掲載情報は変更されている場合があるため、検討時は必ず公式情報をご確認ください）")

        if len(policies) >= 2:
            with st.expander(f"「{s['label']}」の事例を比較する"):
                compare_rows = [{
                    "自治体": f"{p.get('prefecture', '')} {p['municipality']}",
                    "施策名": p["policy_name"],
                    "対象": p["target"],
                    "料金": p.get("cost") or "—",
                    "利用回数": p.get("frequency") or "—",
                    "特徴": p.get("features") or "—",
                } for p in policies]
                st.dataframe(compare_rows, use_container_width=True, hide_index=True)
        st.write("")

    st.info("上記は他自治体での実施例をもとにした参考情報であり、宇都宮市への導入を推奨するものではありません。", icon="ℹ️")

st.markdown("---")

# ============================================================
# （既存）スコア内訳
# ============================================================
st.markdown("### スコア内訳（各評価項目の寄与点）")
breakdown = get_contribution_breakdown(row, weights, parameters)
fig = go.Figure(go.Bar(
    x=[b["contribution"] for b in breakdown], y=[b["label"] for b in breakdown], orientation="h",
    marker_color=COLOR_PRIMARY, text=[f"{b['contribution']:.1f}点" for b in breakdown], textposition="outside",
))
fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=260, xaxis_title="寄与点")
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ============================================================
# （既存）自動分析コメント
# ============================================================
st.markdown("### 自動分析コメント")
st.caption("※ AIによる判定ではなく、あらかじめ決めたルールに基づく機械的な差分説明です。")
for comment in generate_analysis_comments(row, scored_df, parameters):
    st.write(f"・{comment}")

st.markdown("---")

# ============================================================
# （既存）評価パターン比較
# ============================================================
st.markdown("### 評価パターン比較")
st.caption("重視する観点（評価パターン）を変えた場合に、この地区の総合スコアがどう変わるかを比較できます。")
patterns = load_patterns()
if not patterns:
    st.caption("保存された評価パターンがありません。「設定・データ管理」画面で作成できます。")
else:
    pattern_cols = st.columns(len(patterns))
    for col, (name, pattern) in zip(pattern_cols, patterns.items()):
        pattern_scored = calculate_scores(raw_df, pattern["weights"], parameters)
        pattern_row = pattern_scored[pattern_scored[COL_NAME] == target].iloc[0]
        with col:
            st.metric(name, f"{pattern_row[COL_SCORE]:.1f} 点", f"{int(pattern_row[COL_RANK])}位")

st.markdown("---")

with st.expander("各評価項目の説明・出典を見る"):
    for p in parameters:
        st.markdown(f"**{p['label']}**（{p['unit']}）")
        st.write(p["description"])
        st.caption(f"出典：{p['source']}")
        st.write("")

render_footer()
