# -*- coding: utf-8 -*-
"""地区詳細からつながる施策比較。指標レビュー等の入力フォームは非表示。"""
from __future__ import annotations
import pandas as pd
import streamlit as st
from utils.state import get_scored_data
from utils.config import COL_NAME, COL_SCORE, COL_RANK

st.title("施策検討")
st.caption("39地区分析 → 地区詳細 → 施策比較 → 予算・人員・想定効果の比較")
st.warning("地区の統計にはデモ値が含まれます。以下の費用・効果は試算用の仮定であり、実績・予測値ではありません。")
scored = get_scored_data()
names = scored[COL_NAME].astype(str).tolist()
if not names:
    st.error("地区データがありません。")
    st.stop()
selected = st.session_state.get("policy_target_district", names[0])
if selected not in names: selected=names[0]
district = st.selectbox("施策を検討する地区",names,index=names.index(selected),key="policy_district_select")
st.session_state["policy_target_district"]=district
row=scored.loc[scored[COL_NAME].astype(str)==district].iloc[0]
a,b=st.columns(2)
a.metric("地区の総合スコア",f"{row[COL_SCORE]:.1f} 点")
b.metric("地区順位",f"{int(row[COL_RANK])} / {len(scored)} 地区")
if st.button("← 地区詳細に戻る"):
    st.session_state["jump_to_district"]=district
    st.switch_page("pages/5_district_report.py")
st.divider()
st.subheader("1. 対応する課題と施策を選ぶ")
issue_choices=["買い物支援","通院・移動支援","見守り訪問","配食支援","その他"]
initial_issue=st.session_state.pop("policy_target_issue",issue_choices[0])
issue=st.selectbox("課題",issue_choices,index=issue_choices.index(initial_issue) if initial_issue in issue_choices else 0)
options={
"買い物支援":[("既存サービスの周知",100000,1,20,0.3),("移動販売",450000,2,35,0.5),("買い物送迎",700000,3,30,0.6)],
"通院・移動支援":[("既存の移動支援の案内",120000,1,15,0.3),("付き添い支援",550000,3,25,0.6),("送迎支援",900000,4,35,0.7)],
"見守り訪問":[("見守りサービスの周知",100000,1,20,0.3),("電話見守り",300000,2,35,0.5),("訪問見守り",650000,4,30,0.7)],
"配食支援":[("既存配食サービスの案内",100000,1,20,0.3),("配食の提供枠拡充",550000,3,35,0.6),("配食と安否確認の連携",700000,4,35,0.7)],
"その他":[("案A",100000,1,20,0.3),("案B",400000,2,30,0.5),("案C",700000,4,40,0.7)]}
base=options[issue]
st.caption("各案の数値は操作確認用の仮定です。対象者数×到達率は『仮の支援到達人数』であり、課題改善効果を意味しません。")
if "policy_drafts" not in st.session_state:st.session_state.policy_drafts={}
key=f"{district}|{issue}"
if key not in st.session_state.policy_drafts:
    st.session_state.policy_drafts[key]=pd.DataFrame([{"施策案":name,"実施主体":"未設定","実施時期":"未設定","実施場所":"未設定","実施頻度（回/月）":4,"実施期間（月）":12,"対象者数（仮）":n,"到達率（仮）":r,"費用（円・仮）":cost,"必要人員（人・仮）":people} for name,cost,people,n,r in base])
df=st.data_editor(st.session_state.policy_drafts[key],num_rows="dynamic",hide_index=True,use_container_width=True,key="editor_"+str(names.index(district))+"_"+str(list(options).index(issue)))
st.session_state.policy_drafts[key]=df.copy()
st.divider()
st.subheader("2. 利用可能な資源を設定する")
c1,c2=st.columns(2)
with c1:budget=st.number_input("予算上限（円）",min_value=0,value=1000000,step=50000)
with c2:staff=st.number_input("配置可能人数（人）",min_value=0,value=3,step=1,key="staff_capacity_v19_8_fix")
st.caption(f"現在の条件：予算 {budget:,} 円 ／ 配置可能人数 {staff} 人。入力後に Enter を押すと判定を更新します。")
only_feasible = st.checkbox("条件を満たす施策だけ表示", value=False, key="policy_only_feasible")
st.subheader("3. 費用・人員・想定到達人数を比較する")
st.caption("表内で実施主体・時期・場所・頻度・期間・費用・必要人員を直接編集できます。費用は入力した実施期間全体の総額として扱います。")
try:
    result=df.copy()
    for col in ["対象者数（仮）","到達率（仮）","費用（円・仮）","必要人員（人・仮）"]:result[col]=pd.to_numeric(result[col],errors="coerce")
    result["仮の支援到達人数"]= (result["対象者数（仮）"]*result["到達率（仮）"]).round(1)
    result["予算内"]=result["費用（円・仮）"]<=budget
    result["人員内"]=result["必要人員（人・仮）"]<=staff
    result["条件を満たす"]=result["予算内"] & result["人員内"]
    result["到達1人当たり費用（仮）"]=(result["費用（円・仮）"]/result["仮の支援到達人数"].replace(0,float("nan"))).round(0)
    feasible_mask=result["条件を満たす"].fillna(False)
    shortage_mask=(result["必要人員（人・仮）"]>staff).fillna(False)
    m1,m2,m3=st.columns(3)
    m1.metric("実施可能な施策数", f"{int(feasible_mask.sum())} / {len(result)} 件")
    m2.metric("人員不足の施策数", f"{int(shortage_mask.sum())} 件")
    m3.metric("配置可能人数", f"{staff} 人")
    display_result=result.loc[feasible_mask] if only_feasible else result
    st.dataframe(display_result,use_container_width=True,hide_index=True)
    if only_feasible and display_result.empty:
        st.info("現在の予算・人員の条件を満たす施策はありません。")
    st.subheader("4. 実施計画を組み合わせて比較する")
    st.caption("複数案を選択して、費用と必要人員の合計を試算します。同じ人員を複数施策で兼務できる場合は、実際の必要人数に修正してください。")
    selected_plans = st.multiselect("組み合わせる施策", result["施策案"].dropna().astype(str).tolist(), key=f"plan_selection_{district}_{issue}")
    chosen = result[result["施策案"].astype(str).isin(selected_plans)]
    total_cost = chosen["費用（円・仮）"].sum(min_count=1) if len(chosen) else 0
    total_people = chosen["必要人員（人・仮）"].sum(min_count=1) if len(chosen) else 0
    total_reach = chosen["仮の支援到達人数"].sum(min_count=1) if len(chosen) else 0
    c1,c2,c3=st.columns(3)
    c1.metric("組み合わせ費用（仮）", f"{total_cost:,.0f} 円")
    c2.metric("必要人員の単純合計（仮）", f"{total_people:,.0f} 人")
    c3.metric("到達人数の単純合計（仮）", f"{total_reach:,.1f} 人")
    if selected_plans:
        remaining=staff-total_people if pd.notna(total_people) else None
        if remaining is not None:
            if remaining >= 0: st.info(f"選択した施策の配置可能人数の残り：{remaining:,.0f} 人")
            else: st.warning(f"選択した施策は配置可能人数を {-remaining:,.0f} 人超過しています。")
        if pd.isna(total_cost) or pd.isna(total_people):
            st.warning("選択した施策に未入力の費用または人員があります。")
        elif total_cost <= budget and total_people <= staff:
            st.success("選択した施策の合計は、入力した予算・人員の上限内です。")
        else:
            st.warning("選択した施策の合計が予算または人員の上限を超えています。")
    st.caption("到達人数は施策間で同じ人を含む可能性があり、実人数や効果の推計ではありません。")
    if len(chosen):
        st.download_button("選択した実施計画をCSV保存", chosen.to_csv(index=False).encode("utf-8-sig"), file_name="houga_selected_plans.csv", mime="text/csv", key="download_selected_plans")
    feasible=result.loc[result["条件を満たす"] & result["仮の支援到達人数"].notna()]
    if len(feasible):
        st.info(f"入力した条件で実施可能と判定された案は {len(feasible)} 件です。費用・人数の単純比較であり、効果や実施可能性を保証しません。")
    else:st.warning("設定した予算・人員の範囲に収まる案がありません。")
    st.download_button("比較結果をCSV保存",result.to_csv(index=False).encode("utf-8-sig"),file_name="houga_policy_comparison.csv",mime="text/csv")
except (ValueError,TypeError,KeyError) as exc:
    st.error(f"入力内容を確認してください：{exc}")
st.caption("人員の兼務、施策間の対象者重複、移動時間、制度上の条件は自動調整されません。数値は試算用の仮定で、実施可能性や効果を保証しません。")
