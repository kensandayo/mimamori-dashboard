from utils.active_weights import scored, score_caption
from utils.official import load,derived,LABELS
import streamlit as st
import pandas as pd
df=scored()
st.title('地区比較')
names=df.district.tolist();a,b=st.columns(2)
with a: x=st.selectbox('地区A',names,index=0)
with b: y=st.selectbox('地区B',names,index=1)
keys=list(LABELS)
out=pd.DataFrame({'指標':[LABELS[k] for k in keys],x:[df.set_index('district').loc[x,k] for k in keys],y:[df.set_index('district').loc[y,k] for k in keys]})
st.dataframe(out,hide_index=True,use_container_width=True)

st.subheader('現在の重みで比較')
score_caption()
st.dataframe(pd.DataFrame({'地区':[x,y],'相対比較スコア':[df.set_index('district').loc[n,'weighted_score'] for n in [x,y]],'指標カバー率（%）':[df.set_index('district').loc[n,'coverage_pct'] for n in [x,y]]}),hide_index=True,use_container_width=True)
