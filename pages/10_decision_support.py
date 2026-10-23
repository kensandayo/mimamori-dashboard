import streamlit as st
import pandas as pd
from utils.active_weights import scored,score_caption
from utils.official import LABELS
st.title('施策意思決定支援')
df=scored(); fields={'買い物支援':['population','aging_rate_pct','supermarkets_drugstores'],'移動支援':['population','late_elderly_rate_pct','bus_stops','weekday_bus_services','stations'],'介護・健康支援':['aging_rate_pct','care_certification_rate_pct','hospitals_clinics','community_support_centers'],'地域交流':['aging_rate_pct','community_salons','community_halls']}
st.caption('地区選択 → 課題根拠の確認 → 施策候補の整理 → 予算・人員の比較。提案は検討候補であり、実施効果の予測ではありません。')
handoff=st.session_state.get('policy_handoff')
areas=df.district.tolist()
selected=areas.index(handoff['district']) if handoff and handoff['district'] in areas else 0
area=st.selectbox('対象地区',areas,index=selected);row=df.set_index('district').loc[area]
if handoff and handoff['district']==area: st.info('AI相談から引き継いだ施策案があります。下の入力欄に反映しています。')
st.metric('現在の重みによる相対スコア',f'{row.weighted_score:.1f}' if pd.notna(row.weighted_score) else '算出不可')
kinds=list(fields)
kind_map={'買い物支援':'買い物支援','移動支援':'移動支援','介護・健康支援':'介護・健康支援','地域交流':'地域交流'}
kind=st.selectbox('施策分野',kinds,index=kinds.index(kind_map[handoff['field']]) if handoff and handoff['district']==area and handoff['field'] in kind_map else 0)
st.dataframe(pd.DataFrame([{'指標':LABELS.get(k,k),'値':row[k]} for k in fields[kind]]),hide_index=True,use_container_width=True)
options={'買い物支援':['既存宅配・配食サービスの周知','移動販売の実施可能性調査','買い物同行の試行'],'移動支援':['既存公共交通の利用支援','送迎・移動支援の需要調査','運行事業者との協議'],'介護・健康支援':['相談窓口の周知','予防教室の試行','地域包括支援センターとの連携'],'地域交流':['地域サロンの周知','交流イベントの試行','参加障壁の聞き取り']}[kind]
st.subheader('施策候補（一般的な検討案・効果未検証）')
choice=st.selectbox('候補',options+['その他（自由記入）'])
if 'plans_v26' not in st.session_state:st.session_state.plans_v26=[]
with st.form('policy_form_v26'):
 title=st.text_input('施策名',value=handoff['title'] if handoff and handoff['district']==area and handoff['field']==kind else choice if choice!='その他（自由記入）' else '')
 detail=st.text_area('具体的な実施内容',value=handoff['detail'] if handoff and handoff['district']==area and handoff['field']==kind else '');owner=st.text_input('担当主体',value=handoff['owner'] if handoff and handoff['district']==area and handoff['field']==kind else '');start=st.text_input('開始時期・期間')
 c1,c2=st.columns(2)
 with c1:budget=st.number_input('想定総予算（円・利用者入力）',min_value=0,step=10000)
 with c2:staff=st.number_input('必要人数（人・利用者入力）',min_value=0,step=1)
 evidence=st.text_area('実施根拠・ニーズ調査',value=handoff['evidence'] if handoff and handoff['district']==area and handoff['field']==kind else '');verify=st.text_area('効果検証指標・測定方法',value=handoff['verify'] if handoff and handoff['district']==area and handoff['field']==kind else '')
 if st.form_submit_button('施策案を比較表に追加'):
  if not title.strip():st.error('施策名を入力してください')
  else:
   st.session_state.plans_v26.append({'地区':area,'分野':kind,'施策名':title,'内容':detail,'担当主体':owner,'開始時期':start,'想定総予算_利用者入力':budget,'必要人数_利用者入力':staff,'実施根拠':evidence,'検証方法':verify});st.success('追加しました')
if st.session_state.plans_v26:
 plans=pd.DataFrame(st.session_state.plans_v26);st.subheader('複数施策の比較');st.dataframe(plans,hide_index=True,use_container_width=True)
 st.metric('比較表の想定予算合計（重複計上に注意）',f"{int(plans['想定総予算_利用者入力'].sum()):,}円")
 st.download_button('施策比較CSV',plans.to_csv(index=False).encode('utf-8-sig'),'policy_comparison.csv','text/csv')
 if st.button('施策比較表をクリア'):st.session_state.plans_v26=[];st.rerun()
st.warning('指標だけで施策の必要性や効果は確定しません。住民ニーズ、既存事業、移動時間、対象人数を確認してください。')
score_caption()
