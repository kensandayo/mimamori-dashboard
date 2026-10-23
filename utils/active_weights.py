"""Shared current weights and scores for all pages."""
import streamlit as st
from utils.weighted_official import METRICS, calculate

DEFAULT_WEIGHTS={k:(1.0 if i<3 else 0.0) for i,k in enumerate(METRICS)}

def get_weights():
    if 'weight_values' not in st.session_state:
        st.session_state.weight_values=DEFAULT_WEIGHTS.copy()
    return st.session_state.weight_values

def scored():
    return calculate(get_weights())

def score_columns():
    return ['district','weighted_score','coverage_pct']

def score_caption():
    st.caption('共通の評価重みを使用中。0〜100の地区間相対スコアであり、施策効果・支援必要度の確定値ではありません。重みの変更は「評価重み・保存」で行えます。')
