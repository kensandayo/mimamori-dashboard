from utils.active_weights import scored, score_caption
from utils.official import load,derived,LABELS
import streamlit as st
import pandas as pd
from utils.visual_comparison import render_difference
df=scored()
st.title('地区比較')
names=df.district.tolist();a,b=st.columns(2)
requested_a = st.session_state.pop('drill_comparison_a', None)
requested_b = st.session_state.pop('drill_comparison_b', None)
if requested_a in names: st.session_state['comparison_district_a'] = requested_a
if requested_b in names: st.session_state['comparison_district_b'] = requested_b
with a: x=st.selectbox('地区A',names,key='comparison_district_a')
with b: y=st.selectbox('地区B',names,index=1,key='comparison_district_b')
keys=list(LABELS)
out=pd.DataFrame({'指標':[LABELS[k] for k in keys],x:[df.set_index('district').loc[x,k] for k in keys],y:[df.set_index('district').loc[y,k] for k in keys]})
st.dataframe(out,hide_index=True,use_container_width=True)

st.subheader('現在の重みで比較')
score_caption()
st.dataframe(pd.DataFrame({'地区':[x,y],'見守り優先度スコア':[df.set_index('district').loc[n,'weighted_score'] for n in [x,y]],'指標カバー率（%）':[df.set_index('district').loc[n,'coverage_pct'] for n in [x,y]]}),hide_index=True,use_container_width=True)

st.divider()
st.subheader("各地区と39地区平均との差")
left, right = st.columns(2)
with left:
    st.markdown(f"### {x}")
    render_difference(df, x, "comparison_a")
with right:
    st.markdown(f"### {y}")
    render_difference(df, y, "comparison_b")
