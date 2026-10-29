from utils.active_weights import scored, score_caption
from utils.official import load,derived,LABELS
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.visual_comparison import render_difference
df=scored()

# Chart selections navigate directly to the chosen district report.
def open_district_from_chart(event, *, axis=None, custom=False):
    try:
        points = event.selection.points
        if not points:
            return
        point = points[0]
        district = (point.get('customdata') or [None])[0] if custom else point.get(axis)
        if district is not None and str(district) in df['district'].astype(str).values:
            st.session_state['drill_detail_district'] = str(district)
            st.switch_page('pages/5_district_report.py')
    except (AttributeError, KeyError, IndexError, TypeError):
        return

st.title('39地区ダッシュボード')
a,b,c=st.columns(3)
a.metric('地区数',len(df));b.metric('人口合計（資料記載時点）',f"{df.population.sum():,} 人");c.metric('人口加重の高齢化率',f"{(df.population*df.aging_rate_pct).sum()/df.population.sum():.1f}%")

st.subheader('選択地区の人口構成・指標プロフィール')
st.caption('過去版の地区レポートを参考に、円グラフとレーダーチャートを追加しました。')
profile_district = st.selectbox('グラフで見る地区', df['district'].dropna().astype(str).tolist(), key='dashboard_profile_district')
profile = df.loc[df['district'] == profile_district].iloc[0]
pie_col, radar_col = st.columns(2)
with pie_col:
    st.markdown('**人口構成（65歳以上／65歳未満）**')
    population = pd.to_numeric(pd.Series([profile.get('population')]), errors='coerce').iloc[0]
    aging = pd.to_numeric(pd.Series([profile.get('aging_rate_pct')]), errors='coerce').iloc[0]
    if pd.notna(population) and population > 0 and pd.notna(aging) and 0 <= aging <= 100:
        aged = population * aging / 100
        donut = px.pie(names=['65歳以上', '65歳未満'], values=[aged, population-aged], hole=0.48,
                       color_discrete_sequence=['#E8A33D', '#2C5C8F'])
        donut.update_traces(textinfo='percent+label', hovertemplate='%{label}: %{percent}<extra></extra>')
        donut.update_layout(height=355, margin=dict(l=35,r=35,t=35,b=35), legend=dict(orientation='h', y=-0.07, x=0.5, xanchor='center'), uniformtext_minsize=11, uniformtext_mode='hide')
        st.plotly_chart(donut, use_container_width=True, key='dashboard_population_donut')
        st.caption('高齢化率と人口から計算した構成比です。人数は推計値のため表示していません。')
    else:
        st.info('この地区は人口構成の表示に必要な値がありません。')
with radar_col:
    st.markdown('**地区の指標プロフィール（39地区内の百分位）**')
    import plotly.graph_objects as go
    radar_keys = [k for k in ('aging_rate_pct','late_elderly_rate_pct','care_certification_rate_pct','age_85_plus_pct')
                  if k in df.columns and pd.to_numeric(df[k],errors='coerce').notna().sum() >= 2]
    if len(radar_keys) >= 3:
        short_labels = {'aging_rate_pct':'高齢化率', 'late_elderly_rate_pct':'後期高齢者', 'care_certification_rate_pct':'要介護率', 'age_85_plus_pct':'85歳以上'}
        labels = [short_labels.get(k,LABELS.get(k,k)) for k in radar_keys]
        vals = [float(pd.to_numeric(df[k],errors='coerce').rank(pct=True).loc[profile.name]*100) for k in radar_keys]
        radar = go.Figure()
        radar.add_trace(go.Scatterpolar(r=vals+[vals[0]],theta=labels+[labels[0]],fill='toself',
                                        name=profile_district,line=dict(color='#2C5C8F')))
        radar.update_layout(height=355,margin=dict(l=48,r=48,t=35,b=35),showlegend=False,
                            polar=dict(domain=dict(x=[0.15,0.85],y=[0.10,0.90]),
                                       radialaxis=dict(visible=True,range=[0,100],tickfont=dict(size=10)),
                                       angularaxis=dict(tickfont=dict(size=11))))
        st.plotly_chart(radar,use_container_width=True,key='dashboard_profile_radar')
        st.caption('高いほど39地区内でその指標の値が高い位置です。優先度やリスクを直接示すものではありません。')
    else:
        st.info('レーダーチャートに必要な指標が不足しています。')

st.subheader('地区別の見守り優先度スコア（グラフ）')
score_caption()
ranked = df.dropna(subset=['weighted_score']).sort_values('weighted_score', ascending=False).head(15)
if not ranked.empty:
    fig = px.bar(ranked.sort_values('weighted_score'), x='weighted_score', y='district', orientation='h',
                 labels={'weighted_score': '見守り優先度スコア', 'district': '地区名'},
                 color_discrete_sequence=['#2C5C8F'])
    fig.update_layout(height=490, margin=dict(l=8,r=18,t=8,b=20), showlegend=False)
    selection = st.plotly_chart(fig, use_container_width=True, on_select='rerun', selection_mode='points', key='dashboard_ranking_chart')
    open_district_from_chart(selection, axis='y')
st.caption('棒をクリックすると、その地区の詳細ページに移動します。')

st.subheader('市全体分析｜39地区の指標分布')
st.caption('旧「市全体分析」をダッシュボードに統合しました。指標を切り替えて39地区の分布を確認できます。')
indicator = st.selectbox('分布を見る指標', list(LABELS), format_func=lambda k: LABELS[k], key='dashboard_city_indicator')
if indicator in df.columns:
    distribution = df[['district', indicator]].dropna().sort_values(indicator, ascending=False)
    if not distribution.empty:
        distribution_fig = px.bar(distribution, x='district', y=indicator,
            labels={'district': '地区名', indicator: LABELS[indicator]},
            color_discrete_sequence=['#2C5C8F'])
        distribution_fig.update_layout(height=410, margin=dict(l=8, r=12, t=12, b=80), showlegend=False)
        dist_selection = st.plotly_chart(distribution_fig, use_container_width=True, on_select='rerun', selection_mode='points', key='dashboard_city_distribution_chart')
        open_district_from_chart(dist_selection, axis='x')
st.caption('施設数などは地区面積を考慮していません。比較時には指標の定義・対象年度も確認してください。')

st.subheader('指標の分布と地区間の違い')
left, right = st.columns(2)
with left:
    st.markdown('**指標の分布（ヒストグラム）**')
    numeric_values = pd.to_numeric(df[indicator], errors='coerce').dropna() if indicator in df.columns else pd.Series(dtype=float)
    if not numeric_values.empty:
        hist = px.histogram(x=numeric_values, nbins=min(12, max(4, len(numeric_values)//3)),
                            labels={'x': LABELS.get(indicator, indicator), 'y':'地区数'},
                            color_discrete_sequence=['#2C5C8F'])
        hist.update_layout(height=320, margin=dict(l=10,r=10,t=12,b=20), showlegend=False)
        st.plotly_chart(hist, use_container_width=True, key='dashboard_histogram')
with right:
    st.markdown('**2指標の関係（散布図）**')
    numeric_indicators = [k for k in LABELS if k in df.columns and pd.to_numeric(df[k], errors='coerce').notna().sum() >= 3]
    if len(numeric_indicators) >= 2:
        x_metric = st.selectbox('横軸', numeric_indicators, format_func=lambda k: LABELS[k], key='dash_scatter_x', index=0)
        y_choices = [k for k in numeric_indicators if k != x_metric]
        y_metric = st.selectbox('縦軸', y_choices, format_func=lambda k: LABELS[k], key='dash_scatter_y')
        plot_data = df[['district',x_metric,y_metric]].copy()
        plot_data[x_metric] = pd.to_numeric(plot_data[x_metric],errors='coerce')
        plot_data[y_metric] = pd.to_numeric(plot_data[y_metric],errors='coerce')
        plot_data = plot_data.dropna()
        if not plot_data.empty:
            scatter = px.scatter(plot_data, x=x_metric, y=y_metric, hover_name='district', custom_data=['district'],
                                 labels={x_metric:LABELS[x_metric], y_metric:LABELS[y_metric]},
                                 color_discrete_sequence=['#2C5C8F'])
            scatter.update_layout(height=320, margin=dict(l=10,r=10,t=12,b=20))
            scatter_selection = st.plotly_chart(scatter, use_container_width=True, on_select='rerun', selection_mode='points', key='dashboard_scatter')
            open_district_from_chart(scatter_selection, custom=True)
st.caption('グラフは地区間の傾向を示します。相関関係があっても因果関係を意味しません。')

with st.expander('全39地区の見守り優先度スコアを見る'):
    score_caption()
    all_scores = df.dropna(subset=['weighted_score']).sort_values('weighted_score', ascending=False)
    if not all_scores.empty:
        all_fig = px.bar(all_scores.sort_values('weighted_score'), x='weighted_score', y='district', orientation='h',
            labels={'weighted_score': '見守り優先度スコア', 'district': '地区名'}, color_discrete_sequence=['#2C5C8F'])
        all_fig.update_layout(height=max(650, len(all_scores)*22), margin=dict(l=8,r=18,t=8,b=20), showlegend=False)
        all_selection = st.plotly_chart(all_fig, use_container_width=True, on_select='rerun', selection_mode='points', key='dashboard_all_scores_chart')
        open_district_from_chart(all_selection, axis='y')

st.subheader('高齢化率の高い地区')
st.dataframe(df.sort_values('aging_rate_pct',ascending=False)[['district','population','aging_rate_pct','care_certification_rate_pct','bus_stops','supermarkets_drugstores']].rename(columns={'district':'地区名',**LABELS}),hide_index=True,use_container_width=True)
st.caption('高齢化率だけで支援優先度は確定できません。地区の面積・移動時間・サービス利用状況等は別途確認が必要です。')

st.subheader('現在の重みに基づく見守り優先度スコア 上位10地区')
score_caption()
st.dataframe(df.sort_values('weighted_score',ascending=False)[['district','weighted_score','coverage_pct']].head(10).rename(columns={'district':'地区名','weighted_score':'見守り優先度スコア','coverage_pct':'指標カバー率（%）'}),hide_index=True,use_container_width=True)


st.divider()
st.subheader('地区を選んで詳しく調べる')
st.caption('選択した地区を引き継いで、地区詳細・地区比較に移動できます。')
districts = df['district'].dropna().astype(str).tolist()
chosen = st.selectbox('分析したい地区', districts, key='dashboard_drill_district')
render_difference(df, chosen, 'dashboard_difference')
comparison_candidates = [n for n in districts if n != chosen]
peer = st.selectbox('比較相手（比較画面で使用）', comparison_candidates, key='dashboard_drill_peer')
a, b = st.columns(2)
if a.button('📈 この地区を比較', use_container_width=True):
    st.session_state['drill_comparison_a'] = chosen
    st.session_state['drill_comparison_b'] = peer
    st.switch_page('pages/4_comparison.py')
if b.button('📋 地区詳細を見る', use_container_width=True):
    st.session_state['drill_detail_district'] = chosen
    st.switch_page('pages/5_district_report.py')
