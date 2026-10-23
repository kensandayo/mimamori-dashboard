import streamlit as st
import pandas as pd
from utils.active_weights import scored,score_caption
st.title('施策シミュレーション')
st.caption('以下は利用者が入力した仮定による容量・費用の試算です。政策効果の因果的な予測ではありません。')
df=scored(); district=st.selectbox('対象地区',df.district.tolist()); r=df.set_index('district').loc[district]
st.metric('現在の重みによる相対比較スコア',f"{r.weighted_score:.1f}" if pd.notna(r.weighted_score) else '算出不可')
kind=st.selectbox('施策分野',['買い物支援','移動支援','介護・健康支援','地域交流','その他'])
a,b=st.columns(2)
with a:
 target=st.number_input('対象候補者数（仮定、人）',0,1000000,100,10)
 uptake=st.slider('想定利用率（%）',0,100,30)
 capacity=st.number_input('担当者1人が対応できる人数（仮定）',1,10000,10)
with b:
 cost=st.number_input('利用者1人当たり月額変動費（円、仮定）',0,10000000,5000,1000)
 fixed=st.number_input('月額固定費（円、仮定）',0,100000000,0,10000)
 budget=st.number_input('月額予算上限（円、仮定）',0,1000000000,200000,10000)
 staff=st.number_input('確保可能な担当者数（人、仮定）',0,10000,3)
 demand=round(target*uptake/100)
 staff_cap=staff*capacity
 budget_cap=max(0,(budget-fixed)//cost) if cost else (1000000000 if budget>=fixed else 0)
 served=max(0,min(demand,staff_cap,budget_cap))
 needed=(demand+capacity-1)//capacity if demand else 0
 monthly=fixed+served*cost
 st1,st2,st3,st4=st.columns(4)
 st1.metric('想定利用希望者',f'{demand:,}人');st2.metric('予算・人員内で対応可能',f'{served:,}人');st3.metric('希望者全員への必要担当者',f'{needed:,}人');st4.metric('対応可能人数での月額費用',f'{monthly:,}円')
if budget<fixed:st.warning('予算が固定費を下回っています。')
if served<demand:st.warning(f'想定利用希望者に対し {demand-served:,} 人分の対応枠が不足します。')
if cost==0:st.info('変動費0円の仮定です。実際の人件費・設備費などを含むか確認してください。')
scenario={'地区':district,'施策分野':kind,'対象候補者_仮定':target,'想定利用率_pct':uptake,'想定利用希望者':demand,'担当者1人当たり対応人数_仮定':capacity,'確保可能担当者_仮定':staff,'月額固定費_仮定':fixed,'利用者当たり月額変動費_仮定':cost,'月額予算上限_仮定':budget,'対応可能人数_試算':served,'必要担当者_試算':needed,'月額費用_試算':monthly}
if 'scenario_v26' not in st.session_state:st.session_state.scenario_v26=[]
if st.button('この試算を比較表に追加'):st.session_state.scenario_v26.append(scenario);st.success('比較表に追加しました')
if st.session_state.scenario_v26:
 st.subheader('保存した試算の比較（このセッション内）');st.dataframe(pd.DataFrame(st.session_state.scenario_v26),use_container_width=True,hide_index=True)
 st.download_button('試算CSVを保存',pd.DataFrame(st.session_state.scenario_v26).to_csv(index=False).encode('utf-8-sig'),'scenario_comparison.csv','text/csv')
 if st.button('試算一覧をクリア'):st.session_state.scenario_v26=[];st.rerun()
score_caption()
