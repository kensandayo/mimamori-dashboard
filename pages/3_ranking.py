"""District monitoring-attention rankings (higher composite score = higher priority)."""
import pandas as pd
import streamlit as st
from utils.active_weights import scored, get_weights, score_caption
from utils.official import LABELS
from utils.weighted_official import METRICS

get_weights()
df = scored()
st.title('見守り優先度ランキング')
st.caption('見守り優先度スコアが高い地区ほど、現在の評価パターンでは見守り・支援の検討優先度が高いと評価されます。これは公開統計に基づく暫定的な着目度であり、地区の優劣や実際の支援順位を確定するものではありません。')
st.info('適用中の評価パターン：' + st.session_state.get('active_weight_pattern', '標準（公開指標）'))
choices = {'weighted_score': '見守り優先度の見守り優先度スコア', **LABELS,
           'supermarkets_drugstores_per_10k': '人口1万人当たりスーパー・ドラッグストア数',
           'hospitals_clinics_per_10k': '人口1万人当たり医療施設数',
           'bus_stops_per_10k': '人口1万人当たりバス停数'}
key = st.selectbox('比較する指標', list(choices), format_func=lambda x: choices[x])
# For a risk-related metric, rank 1 always means the highest risk/attention, not the highest raw value.
if key == 'weighted_score':
    priority_ascending = False
    st.caption('見守り優先度スコア：高いほど見守り優先度が高い（1位が最高スコア）')
else:
    direction = METRICS.get(key, (None, 'high'))[1]
    priority_ascending = direction == 'low'
    st.caption('指標別の参考順位：' + ('数値が小さい地区を上位に表示' if priority_ascending else '数値が大きい地区を上位に表示') + '。見守り優先度スコアの順位とは異なります。')
ranked = df.sort_values(key, ascending=priority_ascending, na_position='last', kind='stable').copy()
ranked.insert(0, '順位', range(1, len(ranked) + 1))
ranked[key] = pd.to_numeric(ranked[key], errors='coerce').round(1)
ranked = ranked[['順位', 'district', key]].rename(columns={'district': '地区名', key: choices[key]})
st.dataframe(ranked, hide_index=True, use_container_width=True, height=570)
score_caption()
