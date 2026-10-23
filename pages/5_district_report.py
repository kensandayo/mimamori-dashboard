from utils.active_weights import scored, score_caption
from utils.official import load,derived,LABELS
import streamlit as st
import pandas as pd
df=scored()
st.title('地区詳細')
name=st.selectbox('地区',df.district.tolist());row=df.set_index('district').loc[name]
a,b,c=st.columns(3);a.metric('人口',f"{int(row.population):,} 人");b.metric('高齢化率',f"{row.aging_rate_pct}%");c.metric('要介護認定率',f"{row.care_certification_rate_pct}%")
st.dataframe(pd.DataFrame({'指標':[LABELS[k] for k in LABELS],'値':[row[k] for k in LABELS]}),hide_index=True,use_container_width=True)
st.caption(f"出典: {row.source_pdf} / 人口基準: {row.population_reference} / 地域資源: {row.resource_reference}")

st.subheader('現在の重みでの評価')
score_caption()
st.metric('相対比較スコア',f"{row.weighted_score:.1f}" if pd.notna(row.weighted_score) else '算出不可')
st.caption(f"利用可能な指標の重み割合：{row.coverage_pct:.1f}%")
