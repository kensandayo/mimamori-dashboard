import streamlit as st
import pandas as pd
from utils.official import load,derived
from utils.weighted_official import METRICS
st.title('設定・データ管理')
df=derived(load())
st.download_button('39地区の公開統計CSV',load().to_csv(index=False).encode('utf-8-sig'),'official_39_districts.csv','text/csv')
st.subheader('指標一覧と欠損状況')
st.dataframe(pd.DataFrame({'指標':df.columns,'欠損件数':[int(df[c].isna().sum()) for c in df.columns]}),hide_index=True,use_container_width=True)
st.subheader('利用者独自指標の登録・比較')
st.caption('アップロードした独自指標は公開統計ではありません。現在のセッションでのみ使用し、公式CSVを上書きしません。')
file=st.file_uploader('地区名と独自指標を含むCSV（district列が必須）',type='csv')
if file:
 try:
  custom=pd.read_csv(file,encoding='utf-8-sig')
  if 'district' not in custom.columns:st.error('district列がありません')
  elif custom.district.duplicated().any():st.error('地区名が重複しています')
  else:
   fields=[c for c in custom if c!='district' and c not in df.columns]
   if not fields:st.warning('独自指標列がありません。公式指標と同じ列名は上書きしません。')
   else:
    merged=df[['district']].merge(custom[['district']+fields],on='district',how='left')
    st.dataframe(merged,hide_index=True,use_container_width=True)
    st.download_button('独自指標と地区の結合CSV',merged.to_csv(index=False).encode('utf-8-sig'),'custom_indicator_review.csv','text/csv')
    st.info('独自指標を重み付き総合スコアに加える処理は未接続です。元データの定義と向きを確認してから追加してください。')
 except Exception as e:st.error(f'CSVの読込に失敗: {e}')
st.subheader('評価対象の公式指標')
st.write({v[0]:k for k,v in METRICS.items()})
