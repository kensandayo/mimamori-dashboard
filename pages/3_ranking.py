from utils.active_weights import scored, score_caption
from utils.official import load,derived,LABELS
import streamlit as st
import pandas as pd
df=scored()
st.title('指標別ランキング')
choices={'weighted_score':'総合スコア（保存した重みを反映）',**LABELS,'supermarkets_drugstores_per_10k':'人口1万人当たりスーパー・ドラッグストア数','hospitals_clinics_per_10k':'人口1万人当たり医療施設数','bus_stops_per_10k':'人口1万人当たりバス停数'}
key=st.selectbox('比較する実データ指標',list(choices),format_func=lambda x:choices[x]);asc=st.checkbox('小さい順に並べる',value=False)
st.caption('これは選択した指標の順位です。支援必要度の総合順位ではありません。')
st.dataframe(df.sort_values(key,ascending=asc,na_position='last')[['district',key]].rename(columns={'district':'地区名',key:choices[key]}),hide_index=True,use_container_width=True)

score_caption()
