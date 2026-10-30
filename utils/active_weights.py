"""Single source of truth for active evaluation pattern and district scores."""
import streamlit as st
from utils.weighted_official import METRICS, calculate
from utils.patterns import load_patterns

DEFAULT_WEIGHTS = {k: (1.0 if i < 3 else 0.0) for i, k in enumerate(METRICS)}
PRESETS = {
    '標準（公開指標）': {'aging_rate_pct': 1, 'late_elderly_rate_pct': 1, 'care_certification_rate_pct': 1},
    '高齢化重視': {'aging_rate_pct': 3, 'late_elderly_rate_pct': 2, 'age_85_plus_pct': 2},
    '介護・健康重視': {'care_certification_rate_pct': 3, 'age_85_plus_pct': 2, 'hospitals_clinics_per_10k': 2},
    '交通・買い物重視': {'bus_stops_per_10k': 3, 'supermarkets_drugstores_per_10k': 3, 'aging_rate_pct': 1},
    '地域資源重視': {'community_salons_per_10k': 3, 'hospitals_clinics_per_10k': 2, 'bus_stops_per_10k': 2},
}

def available_patterns():
    options = {n: {k: float(v.get(k, 0)) for k in METRICS} for n, v in PRESETS.items()}
    incompatible = []
    for name, obj in load_patterns().items():
        if not isinstance(obj, dict) or not isinstance(obj.get('weights'), dict):
            incompatible.append(name)
            continue
        weights = obj['weights']
        if not weights or any(k not in METRICS for k in weights):
            incompatible.append(name)
            continue
        options[name] = {k: float(weights.get(k, 0)) for k in METRICS}
    return options, incompatible

def get_weights():
    if 'weight_values' not in st.session_state:
        st.session_state.weight_values = DEFAULT_WEIGHTS.copy()
        st.session_state.active_weight_pattern = '標準（公開指標）'
    return st.session_state.weight_values

def apply_weights(weights, name='カスタム'):
    clean = {k: float(weights.get(k, 0)) for k in METRICS}
    if not any(v > 0 for v in clean.values()):
        raise ValueError('少なくとも1つの重みを0より大きくしてください。')
    st.session_state.weight_values = clean
    st.session_state.active_weight_pattern = name
    # Recreate editor widgets on every application so their values always match
    # the weights actually used by scored()/calculate().
    st.session_state['_weight_revision'] = st.session_state.get('_weight_revision', 0) + 1
    st.session_state['_weight_applied_revision'] = st.session_state['_weight_revision']

def apply_pattern(name):
    patterns, _ = available_patterns()
    if name not in patterns:
        raise ValueError('選択した評価パターンは現在の指標に対応していません。')
    apply_weights(patterns[name], name)

def effective_weights_table():
    """Exactly the same weight dictionary used by scored()/calculate()."""
    import pandas as pd
    weights = get_weights()
    total = sum(float(v) for v in weights.values() if float(v) > 0)
    return pd.DataFrame([
        {'指標': label, '適用中の重み': float(weights.get(key, 0)),
         '構成比（%）': round(float(weights.get(key, 0)) / total * 100, 1) if total else 0.0}
        for key, (label, _) in METRICS.items()
    ])

def scored():
    return calculate(get_weights())

def score_columns():
    return ['district', 'weighted_score', 'coverage_pct']

def score_caption():
    st.caption('適用中の評価パターン：' + st.session_state.get('active_weight_pattern', 'カスタム') + '。見守り優先度スコアが高いほど見守り検討の着目度が高くなります。0〜100の地区間相対スコアであり、施策効果や実際の支援順位の確定値ではありません。')
