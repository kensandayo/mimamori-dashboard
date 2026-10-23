import streamlit as st
import pandas as pd
from pathlib import Path
from utils.active_weights import scored,score_caption
st.title('地域マップ')
st.caption('検証済みの地区代表点を使って表示します。代表点は地区境界ではありません。座標を捏造しません。')
df=scored()
geo_path=Path(__file__).resolve().parent.parent/'data'/'district_coordinates.csv'
geo=None
if geo_path.exists():
 try:geo=pd.read_csv(geo_path,encoding='utf-8-sig')
 except Exception as e:st.error(f'座標CSVを読み込めません: {e}')
upload=st.file_uploader('検証済み地区代表点CSV（district,lat,lon）を読み込む',type=['csv'],key='coord_upload')
if upload is not None:
 try:geo=pd.read_csv(upload,encoding='utf-8-sig')
 except Exception as e:st.error(f'CSV読込失敗: {e}')
if geo is not None:
 if not {'district','lat','lon'}.issubset(geo.columns):st.error('district,lat,lon の3列が必要です。')
 else:
  geo=geo.copy();geo['lat']=pd.to_numeric(geo.lat,errors='coerce');geo['lon']=pd.to_numeric(geo.lon,errors='coerce')
  geo=geo.dropna(subset=['lat','lon']);geo=geo[geo.lat.between(35,38)&geo.lon.between(138,142)].drop_duplicates('district')
  joined=df.merge(geo[['district','lat','lon']],on='district',how='inner')
  st.write(f'座標確認済み: {len(joined)} / 39地区')
  if len(joined):
   st.map(joined,latitude='lat',longitude='lon',size=80)
   st.dataframe(joined[['district','weighted_score','coverage_pct','lat','lon']],hide_index=True,use_container_width=True)
  else:st.warning('地区名が一致する有効な座標がありません。')
else:st.info('正確な代表点の座標データがまだないため、ピンを表示していません。CSVをアップロードすると地図が復旧します。')
st.download_button('座標CSVテンプレートを取得',pd.DataFrame({'district':df.district,'lat':['']*len(df),'lon':['']*len(df)}).to_csv(index=False).encode('utf-8-sig'),'district_coordinates_template.csv','text/csv')
st.subheader('地区一覧');st.dataframe(df[['district','weighted_score','coverage_pct','aging_rate_pct','bus_stops']].sort_values('weighted_score',ascending=False),hide_index=True,use_container_width=True)
score_caption()
