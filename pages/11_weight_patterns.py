import streamlit as st
import pandas as pd
from utils.patterns import load_patterns,save_pattern,delete_pattern
from utils.weighted_official import METRICS,calculate
from utils.active_weights import get_weights

st.title('評価重み・パターン保存')
st.caption('39地区の公開データを各指標0〜100に相対正規化した比較用スコアです。行政判断の確定的な優先順位・施策効果予測ではありません。')
patterns=load_patterns()
compatible={n:v for n,v in patterns.items() if isinstance(v,dict) and isinstance(v.get('weights'),dict) and all(k in METRICS for k in v['weights'])}
legacy={n:v for n,v in patterns.items() if n not in compatible}
if legacy:
 with st.expander('旧バージョンの未対応パターン（自動変換しません）'):
  st.write('現在の公開データ指標に存在しない項目が含まれるため、内容を保持してあります。')
  st.write(list(legacy))
choices=['新規・現在の設定']+list(compatible)
selected=st.selectbox('保存済みパターンを読み込む',choices,key='pattern_select')
get_weights()
if st.button('選択したパターンを適用',disabled=selected not in compatible):
 weights=compatible[selected]['weights']
 st.session_state.weight_values={k:float(weights.get(k,0)) for k in METRICS}
 st.rerun()
with st.form('weight_form'):
 st.subheader('指標ごとの重み')
 edited={}
 for k,(label,direction) in METRICS.items():
  edited[k]=st.slider(label,0.0,10.0,float(st.session_state.weight_values.get(k,0.0)),0.5,key='slider_'+k)
 apply=st.form_submit_button('重みを反映してランキングを更新')
if apply:
 st.session_state.weight_values=edited
weights=st.session_state.weight_values
st.caption('重みが0の指標は計算対象外。欠損値は0に置換せず、利用可能な重みで再配分します。')
if not any(v>0 for v in weights.values()):
 st.warning('1つ以上の重みを0より大きくしてください。')
else:
 df=calculate(weights).sort_values('weighted_score',ascending=False,na_position='last')
 df.insert(0,'順位',range(1,len(df)+1))
 st.dataframe(df[['順位','district','weighted_score','coverage_pct']].rename(columns={'district':'地区名','weighted_score':'相対比較スコア','coverage_pct':'利用可能な指標の重み割合（%）'}),hide_index=True,use_container_width=True)
 st.download_button('この重みでの結果をCSV保存',df.to_csv(index=False).encode('utf-8-sig'),'weighted_ranking.csv','text/csv')
st.divider()
st.subheader('パターンを保存')
name=st.text_input('パターン名（同名の場合は上書き）')
description=st.text_input('説明（任意）')
if st.button('現在の重みを保存'):
 if not name.strip():st.error('パターン名を入力してください。')
 elif name.strip() in legacy:st.error('旧パターンと同じ名前は使用できません。')
 else:
  try:
   save_pattern(name.strip(),weights,description)
   st.success('保存しました。')
   st.rerun()
  except OSError as e:st.error('保存できません。書き込み可能なフォルダで起動してください。')
if compatible:
 st.subheader('パターン削除')
 to_delete=st.selectbox('削除するパターン',list(compatible),key='delete_pattern')
 confirm=st.checkbox('削除を確認しました')
 if st.button('選択したパターンを削除',disabled=not confirm):
  try:
   delete_pattern(to_delete)
   st.rerun()
  except OSError:st.error('削除できません。保存先のアクセス権限を確認してください。')
