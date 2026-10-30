import streamlit as st
from pathlib import Path
st.set_page_config(page_title='地域見守りアプリ',page_icon='🏘️',layout='wide')
from components.style import inject_global_css, inject_no_transform_compact_css
inject_global_css()
inject_no_transform_compact_css()
from utils.active_weights import get_weights, available_patterns, apply_pattern
get_weights()
# Shared session state: sidebar selection and the evaluation-pattern page both use apply_pattern().
with st.sidebar:
    st.markdown('#### ⚖️ 評価パターン')
    options, incompatible = available_patterns()
    names = list(options)
    active = st.session_state.get('active_weight_pattern', '標準（公開指標）')
    if active not in names:
        names = [active] + names
    # Apply only on a genuine user selection change, never on a rerun.
    # A rerun after saving a new pattern must not restore an older sidebar choice.
    if st.session_state.get('sidebar_pattern_choice') != active:
        st.session_state['sidebar_pattern_choice'] = active
    def _on_sidebar_pattern_change():
        chosen = st.session_state['sidebar_pattern_choice']
        if chosen in available_patterns()[0]:
            apply_pattern(chosen)
    st.selectbox('評価パターンを切り替える', names,
                 key='sidebar_pattern_choice', on_change=_on_sidebar_pattern_change)
    st.caption('適用中：' + st.session_state.get('active_weight_pattern', '標準（公開指標）'))
    st.caption('パターンの編集・保存は「評価重み・保存」から行えます。')
st.info('【データ出典】宇都宮市「地域別データ分析ブック」。人口は主に令和3年9月30日時点、地域資源は資料中のR3/R4等。2026年現在の実態とは限りません。欠損値は0として扱いません。')
p = Path(__file__).parent / 'pages'
# ダッシュボードは1階層。分析・設定のみを折りたたみ表示する。
page_defs = {
    'dashboard': st.Page(str(p/'1_dashboard.py'), title='ダッシュボード', icon='🏠', default=True),
    'map': st.Page(str(p/'2_priority_map.py'), title='地域マップ', icon='🗺️'),
    'ranking': st.Page(str(p/'3_ranking.py'), title='ランキング', icon='📊'),
    'comparison': st.Page(str(p/'4_comparison.py'), title='地区比較', icon='📈'),
    'detail': st.Page(str(p/'5_district_report.py'), title='地区詳細', icon='📋'),
    'ai': st.Page(str(p/'8_ai_consultation.py'), title='AIに聞く', icon='🤖'),
    'survey': st.Page(str(p/'12_survey_analysis.py'), title='アンケート分析', icon='📝'),
    'simulation': st.Page(str(p/'6_simulation.py'), title='データシミュレーション', icon='🔮'),
    'weights': st.Page(str(p/'11_weight_patterns.py'), title='評価重み・パターン', icon='⚖️'),
    'data': st.Page(str(p/'7_data_management.py'), title='データ管理', icon='🗃️'),
}
nav = st.navigation(list(page_defs.values()), position='hidden')
with st.sidebar:
    st.divider()
    st.page_link(page_defs['dashboard'], label='🏠 ダッシュボード', use_container_width=True)
    with st.expander('📊 分析', expanded=True):
        for key in ('map', 'ranking', 'detail', 'survey', 'ai'):
            st.page_link(page_defs[key], use_container_width=True)
    with st.expander('⚙️ 設定', expanded=False):
        for key in ('weights', 'data'):
            st.page_link(page_defs[key], use_container_width=True)
nav.run()
