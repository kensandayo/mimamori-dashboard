"""What-if changes to published indicator values; no intervention effect prediction."""
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from utils.official import load, LABELS
from utils.active_weights import get_weights, score_caption
from utils.weighted_official import calculate, METRICS

st.title('データシミュレーション')
st.caption('指標の将来想定値を入力し、見守り優先度スコアや順位がどのように変化するかを確認できます。将来値や施策効果を予測する機能ではありません。')
original = load()
weights = get_weights()
baseline = calculate(weights, original)
districts = original['district'].tolist()
district = st.selectbox('対象地区', districts)
editable = [k for k in ('aging_rate_pct','late_elderly_rate_pct','care_certification_rate_pct','age_85_plus_pct',
                       'supermarkets_drugstores','hospitals_clinics','bus_stops','community_salons') if k in original.columns]
active = [k for k in editable if (k in METRICS and weights.get(k,0)>0) or
          (k+'_per_10k' in METRICS and weights.get(k+'_per_10k',0)>0)]
if active:
    st.caption('現在の評価パターンに使われている指標：' + '、'.join(LABELS.get(k,k) for k in active))
else:
    st.warning('現在の評価パターンで使用中の指標を確認してください。')
selected_metrics = st.multiselect(
    'シミュレーション対象指標（複数選択可）', editable,
    default=[k for k in editable if k in active][:2] or editable[:2],
    format_func=lambda k: LABELS.get(k,k), key='simulation_selected_metrics')
if not selected_metrics:
    st.info('変更する指標を1つ以上選択してください。')
    st.stop()
scenario = original.copy()
changes = []
for metric in selected_metrics:
    current = original.loc[original['district']==district,metric].iloc[0]
    if pd.isna(current):
        st.warning(f'{LABELS.get(metric,metric)}：元データが欠損しているため変更対象から除外します。')
        continue
    current = float(current)
    is_pct = metric.endswith('_pct')
    label = LABELS.get(metric,metric)
    if is_pct:
        proposed = st.number_input(f'想定{label}（%）', min_value=0.0, max_value=100.0,
                                   value=current, step=0.5, key=f'simulation_value_{district}_{metric}')
    else:
        proposed = st.number_input(f'想定{label}（件・箇所）', min_value=0, max_value=100000,
                                   value=int(current), step=1, key=f'simulation_value_{district}_{metric}')
    scenario.loc[scenario['district']==district,metric] = proposed
    changes.append({'指標':label,'変更前':current,'変更後':float(proposed),
                    '差分':float(proposed)-current,'現在の評価に使用': 'はい' if metric in active else 'いいえ'})
if not changes:
    st.warning('有効な変更対象がありません。')
    st.stop()
st.subheader('変更する指標の一覧')
st.dataframe(pd.DataFrame(changes), hide_index=True, use_container_width=True)
changed = calculate(weights, scenario)
old_row = baseline.set_index('district').loc[district]
new_row = changed.set_index('district').loc[district]
old_score = old_row['weighted_score']; new_score = new_row['weighted_score']
old_rank = baseline['weighted_score'].rank(ascending=False,method='min').loc[baseline['district']==district].iloc[0]
new_rank = changed['weighted_score'].rank(ascending=False,method='min').loc[changed['district']==district].iloc[0]
a,b,c = st.columns(3)
a.metric('変更前の見守り優先度スコア',f'{old_score:.1f}' if pd.notna(old_score) else '算出不可')
b.metric('変更後の見守り優先度スコア',f'{new_score:.1f}' if pd.notna(new_score) else '算出不可',
         delta=f'{new_score-old_score:+.1f}点' if pd.notna(old_score) and pd.notna(new_score) else None,
         delta_color='off')
c.metric('39地区内の順位',f'{int(old_rank)}位 → {int(new_rank)}位' if pd.notna(old_rank) and pd.notna(new_rank) else '算出不可')
if any(row['現在の評価に使用']=='いいえ' for row in changes):
    st.info('現在の評価パターンに含まれない指標は、変更してもスコアに直接反映されません。')
fig = go.Figure()
fig.add_bar(name='変更前',x=['見守り優先度スコア'],y=[old_score],marker_color='#2C5C8F')
fig.add_bar(name='変更後',x=['見守り優先度スコア'],y=[new_score],marker_color='#E8A33D')
fig.update_layout(barmode='group',yaxis=dict(range=[0,100],title='スコア（点）'),height=320,margin=dict(l=10,r=10,t=15,b=15))
left_chart, _ = st.columns([2, 1])
with left_chart:
    st.plotly_chart(fig,use_container_width=True)
st.caption('変更後は39地区全体で指標を再正規化し、同じ評価重みで再計算しています。そのため、対象地区以外の相対スコアや順位も変わる場合があります。')
st.caption('この操作は画面上の仮定です。公式CSV・保存済みデータは変更されません。')
score_caption()
