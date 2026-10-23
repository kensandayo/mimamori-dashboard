from utils.active_weights import scored, score_caption
from utils.official import load,derived,LABELS
import streamlit as st
import pandas as pd
df=scored()
st.title('39地区ダッシュボード')
a,b,c=st.columns(3)
a.metric('地区数',len(df));b.metric('人口合計（資料記載時点）',f"{df.population.sum():,} 人");c.metric('人口加重の高齢化率',f"{(df.population*df.aging_rate_pct).sum()/df.population.sum():.1f}%")
st.subheader('高齢化率の高い地区')
st.dataframe(df.sort_values('aging_rate_pct',ascending=False)[['district','population','aging_rate_pct','care_certification_rate_pct','bus_stops','supermarkets_drugstores']].rename(columns={'district':'地区名',**LABELS}),hide_index=True,use_container_width=True)
st.caption('高齢化率だけで支援優先度は確定できません。地区の面積・移動時間・サービス利用状況等は別途確認が必要です。')

st.subheader('現在の重みに基づく相対比較スコア 上位10地区')
score_caption()
st.dataframe(df.sort_values('weighted_score',ascending=False)[['district','weighted_score','coverage_pct']].head(10).rename(columns={'district':'地区名','weighted_score':'相対比較スコア','coverage_pct':'指標カバー率（%）'}),hide_index=True,use_container_width=True)
