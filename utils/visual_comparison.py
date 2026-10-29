"""39地区の実データを使った、平均との差の可視化部品。"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from utils.official import LABELS

RED = '#C74747'
BLUE = '#3267B1'
NEUTRAL = '#8292A5'

# 指標の方向を推測しない。色は単純に平均との差の符号を表す。
DISPLAY_KEYS = [
    'aging_rate_pct', 'late_elderly_rate_pct', 'care_certification_rate_pct',
    'age_85_plus_pct', 'weekday_bus_services', 'bus_stops',
    'hospitals_clinics', 'supermarkets_drugstores', 'community_salons',
]

def comparison_frame(df, district, keys=None):
    keys = keys or DISPLAY_KEYS
    indexed = df.set_index('district')
    records = []
    for key in keys:
        if key not in df.columns or key not in LABELS:
            continue
        series = pd.to_numeric(df[key], errors='coerce')
        value = pd.to_numeric(pd.Series([indexed.loc[district, key]]), errors='coerce').iloc[0]
        avg = series.mean()
        if pd.isna(value) or pd.isna(avg):
            continue
        diff = float(value - avg)
        records.append({'指標': LABELS[key], '地区値': float(value), '39地区平均': float(avg),
                        '平均との差': diff, '判定': '平均より高い' if diff > 0 else ('平均より低い' if diff < 0 else '平均と同じ'),
                        '色': RED if diff > 0 else (BLUE if diff < 0 else NEUTRAL)})
    return pd.DataFrame(records)

def render_difference(df, district, key_prefix):
    st.markdown('#### 39地区平均との差')
    st.caption('赤：39地区の単純平均より高い／青：低い。色は良し悪しや支援の必要性を表しません。')
    data = comparison_frame(df, district)
    if data.empty:
        st.info('比較できる数値データがありません。')
        return
    # 異なる単位を混ぜて一本の軸にしない。%系と件数系を分ける。
    for title, part in [('割合・比率（ポイント差）', data[data['指標'].str.contains('（%）')]),
                        ('件数・本数（元の単位での差）', data[~data['指標'].str.contains('（%）')])]:
        if part.empty:
            continue
        st.markdown(f'**{title}**')
        fig = go.Figure(go.Bar(
            x=part['平均との差'], y=part['指標'], orientation='h',
            marker_color=part['色'],
            customdata=part[['地区値', '39地区平均', '判定']].to_numpy(),
            hovertemplate='%{y}<br>平均との差：%{x:+.2f}<br>地区値：%{customdata[0]:.2f}<br>39地区平均：%{customdata[1]:.2f}<br>%{customdata[2]}<extra></extra>',
            text=[f'{v:+.1f}' for v in part['平均との差']], textposition='outside', cliponaxis=False,
        ))
        fig.add_vline(x=0, line_color='#8292A5', line_width=1)
        fig.update_layout(height=max(210, 64 + len(part)*47), margin=dict(l=12,r=65,t=12,b=22),
                          xaxis_title='平均との差（' + ('ポイント' if '割合' in title else '各指標の単位') + '）',
                          yaxis=dict(autorange='reversed'), showlegend=False)
        st.plotly_chart(fig, use_container_width=True, key=f'{key_prefix}_{"rate" if "割合" in title else "count"}')
    view = data.drop(columns=['色']).copy()
    for col in ['地区値','39地区平均','平均との差']:
        view[col] = view[col].round(2)
    st.dataframe(view, hide_index=True, use_container_width=True,
                 column_config={'平均との差': st.column_config.NumberColumn(format='%+.2f')})
    st.caption('平均は39地区の単純平均です。人口加重の市全体値ではありません。施設件数・バス停数は地区面積や人口を考慮していないため、アクセスの良し悪しを直接示しません。')
