import streamlit as st
from pathlib import Path
st.set_page_config(page_title='HOU-GA 地域見守り意思決定支援',page_icon='🏘️',layout='wide')
st.sidebar.title('HOU-GA v26.0')
st.sidebar.caption('39地区・公開統計に基づく分析')
st.info('【データ出典】宇都宮市「地域別データ分析ブック」。人口は主に令和3年9月30日時点、地域資源は資料中のR3/R4等。2026年現在の実態とは限りません。欠損値は0として扱いません。')
p=Path(__file__).parent/'pages'
pages=[st.Page(str(p/'1_dashboard.py'),title='ダッシュボード',icon='🏠',default=True),st.Page(str(p/'2_priority_map.py'),title='地域マップ',icon='🗺️'),st.Page(str(p/'3_ranking.py'),title='ランキング',icon='📊'),st.Page(str(p/'4_comparison.py'),title='比較',icon='📈'),st.Page(str(p/'5_district_report.py'),title='地区詳細',icon='📋'),st.Page(str(p/'6_simulation.py'),title='施策シミュレーション',icon='🔮'),st.Page(str(p/'7_data_management.py'),title='設定・データ管理',icon='⚙️'),st.Page(str(p/'8_ai_consultation.py'),title='AI相談',icon='💬'),st.Page(str(p/'9_city_analysis.py'),title='市全体分析',icon='🏙️'),st.Page(str(p/'10_decision_support.py'),title='施策検討',icon='🧭'),st.Page(str(p/'11_weight_patterns.py'),title='評価重み・保存',icon='⚖️')]
st.navigation(pages).run()
