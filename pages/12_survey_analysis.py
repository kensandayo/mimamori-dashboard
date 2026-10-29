import streamlit as st
import pandas as pd
from utils.official import load
from utils.survey_analysis import read_table, aggregate

st.title('アンケート取り込み・分析')
st.caption('自治体が保有するCSV・Excelを読み込み、地区別の回答傾向を集計します。読み込んだデータは現在のセッション内だけで利用し、公開統計CSVやSQLiteを上書きしません。')
st.warning('個人名・住所・電話番号などが含まれるファイルは、アップロード前に匿名化してください。試作版にはアクセス権限管理がありません。')
file=st.file_uploader('アンケートファイル（CSV / Excel）',type=['csv','xlsx','xls'],key='survey_upload')
if file is not None:
    try:
        raw=read_table(file.getvalue(),file.name)
        if raw.empty or len(raw.columns)<2:
            st.error('データ行と2列以上の列が必要です。'); st.stop()
        st.success(f'{len(raw):,}行・{len(raw.columns)}列を読み込みました。')
        st.caption('プライバシー保護のため個票は画面表示しません。列名のみ確認できます。')
        st.write('列名：',list(map(str,raw.columns)))
        mode=st.radio('データ形式',['個人別回答','地区別集計済み'],horizontal=True)
        district_col=st.selectbox('地区名の列',list(raw.columns))
        question_col=st.selectbox('分析する設問・集計値の列',[c for c in raw.columns if c!=district_col])
        source=st.text_input('出典・調査時期（必須）',placeholder='例：自治体アンケート 2025年度')
        minimum=st.number_input('表示する地区の最小回答数（個人別回答のみ）',min_value=5,value=5,step=1,disabled=mode!='個人別回答')
        if st.button('地区別に集計してAI相談へ反映',type='primary'):
            if not source.strip():
                st.error('出典・調査時期を入力してください。')
            else:
                table,hidden=aggregate(raw,district_col,question_col,'individual' if mode=='個人別回答' else 'summary',int(minimum))
                official=set(load()['district'].astype(str).str.strip())
                found=set(table['district'].astype(str))
                unknown=sorted(found-official)
                filtered=table[table['district'].isin(official)].copy()
                st.session_state['survey_evidence']={'table':filtered,'question':str(question_col),'mode':mode,'source':source.strip()}
                st.success(f'{filtered.district.nunique()}地区の集計結果をAI相談で参照できます。')
                if hidden: st.warning(f'回答数が少ないため非表示：{len(hidden)}地区')
                if unknown: st.warning('39地区と一致しない地区名：'+', '.join(unknown[:20]))
    except Exception as e:
        st.error(f'読み込み・集計エラー：{e}')

saved=st.session_state.get('survey_evidence')
if saved:
    st.subheader('現在の集計結果')
    st.caption(f"設問：{saved['question']} ／ 出典：{saved['source']}")
    st.dataframe(saved['table'],hide_index=True,use_container_width=True)
    st.download_button('地区別集計CSVをダウンロード',saved['table'].to_csv(index=False).encode('utf-8-sig'),'survey_district_summary.csv','text/csv')
    st.info('アンケートはAI相談の根拠にのみ追加します。評価重み・ランキングには自動反映しません。')
    if st.button('セッションのアンケート集計を削除'):
        del st.session_state['survey_evidence']; st.rerun()
else:
    st.info('まだアンケート集計結果は登録されていません。')
