from utils.active_weights import scored, score_caption
from utils.official import load,derived,LABELS
import streamlit as st
import pandas as pd
df=scored()
st.title('市全体分析')
key=st.selectbox('分布を見る指標',list(LABELS),format_func=lambda k:LABELS[k]);st.bar_chart(df.set_index('district')[[key]])
st.caption('全39地区の分布。施設数などは地区面積を考慮していません。')

st.subheader('現在の重みでの39地区の比較')
score_caption()
st.bar_chart(df.sort_values('weighted_score',ascending=False).set_index('district')[['weighted_score']])
