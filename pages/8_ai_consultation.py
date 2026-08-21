# -*- coding: utf-8 -*-
"""
ai_consultation.py (pages/)
------------------------------
「AI相談」画面です。自治体職員が、選択した地区のデータについて
チャット形式でAIに質問できます。

AIに渡すのは「選択した地区（＋比較地区）のデータだけ」です。
CSV全体を毎回渡すことはしません（services/ai_service.py 参照）。
評価項目はマスタから動的に取得されるため、項目を追加・削除しても
コード変更なしにAIへの文脈に反映されます。

コスト管理のため、1日の利用回数に上限があり（services/usage_tracker.py）、
同じ地区・同じ質問（会話の1問目のみ）はキャッシュから回答します。
"""

from __future__ import annotations

import streamlit as st

from utils.config import COL_NAME
from utils.state import get_scored_data
from components.header import render_header, render_footer
from services.ai_service import (
    AIServiceConfigError, AIServiceError,
    build_prompt_context, ask_ai_cached, get_daily_limit,
)
from services.usage_tracker import get_today_usage, increment_usage

st.title("AI相談")
render_header(page_caption="選択した地区のデータについて、AIにチャット形式で質問できます。")

QUICK_QUESTIONS = [
    "この地区の見守り優先度が高い理由は？",
    "この地区の特徴を教えて",
    "比較地区と比べてどう違う？",
    "優先度を下げるために考えられる施策は？",
    "新人職員向けに説明して",
]

CHAT_HISTORY_KEY = "ai_chat_history"
QUESTION_INPUT_KEY = "ai_question_input"

if CHAT_HISTORY_KEY not in st.session_state:
    st.session_state[CHAT_HISTORY_KEY] = []


def _set_quick_question(question_text: str) -> None:
    st.session_state[QUESTION_INPUT_KEY] = question_text


scored_df = get_scored_data()
district_names = scored_df[COL_NAME].tolist()

col1, col2 = st.columns(2)
with col1:
    target_name = st.selectbox("地区選択", options=district_names, key="ai_target_district")
with col2:
    compare_name = st.selectbox("比較地区（任意）", options=["（比較しない）"] + district_names, key="ai_compare_district")

target_row = scored_df[scored_df[COL_NAME] == target_name].iloc[0]
compare_row = None
if compare_name != "（比較しない）" and compare_name != target_name:
    compare_row = scored_df[scored_df[COL_NAME] == compare_name].iloc[0]

st.caption(
    f"AIには「{target_name}」" + (f"と「{compare_name}」" if compare_row is not None else "")
    + "のデータのみが渡されます（他の地区のデータは渡されません）。"
)

daily_limit = get_daily_limit()
today_usage = get_today_usage()
remaining = max(daily_limit - today_usage, 0)
st.info(f"本日の利用回数：{today_usage} / {daily_limit}回　残り：{remaining}回", icon="📊")

st.markdown("##### 質問例")
qa_cols = st.columns(len(QUICK_QUESTIONS))
for col, q in zip(qa_cols, QUICK_QUESTIONS):
    with col:
        st.button(q, key=f"quick_{q}", on_click=_set_quick_question, args=(q,), use_container_width=True)

st.markdown("##### 質問を入力")
question = st.text_area(
    "質問内容", key=QUESTION_INPUT_KEY, height=90,
    placeholder="例：この地区の見守り優先度が高い理由は？", label_visibility="collapsed",
)

ask_col, clear_col = st.columns([1, 1])
with ask_col:
    ask_clicked = st.button("🤖 AIへ質問する", type="primary", use_container_width=True)
with clear_col:
    if st.button("会話履歴をクリア", use_container_width=True):
        st.session_state[CHAT_HISTORY_KEY] = []
        st.rerun()

if ask_clicked:
    if today_usage >= daily_limit:
        st.error(f"本日の利用回数が上限（{daily_limit}回）に達しました。明日以降もう一度お試しください。")
    elif not question.strip():
        st.warning("質問を入力してください。")
    else:
        context = build_prompt_context(target_row, scored_df, compare_row=compare_row)
        recent_history = st.session_state[CHAT_HISTORY_KEY][-6:]  # 直近3往復のみ送信

        with st.spinner("AIが回答を作成しています..."):
            try:
                answer, was_cached = ask_ai_cached(question, context, history=recent_history)
                if not was_cached:
                    increment_usage()
                st.session_state[CHAT_HISTORY_KEY].append({"role": "user", "content": question})
                st.session_state[CHAT_HISTORY_KEY].append({"role": "assistant", "content": answer})
                st.session_state[QUESTION_INPUT_KEY] = ""
                st.rerun()
            except AIServiceConfigError as e:
                st.error(f"AI相談機能を使うには設定が必要です：{e}")
            except AIServiceError as e:
                st.error(str(e))

st.markdown("---")
st.markdown("##### チャット履歴")

if not st.session_state[CHAT_HISTORY_KEY]:
    st.caption("まだ質問はありません。上の質問例ボタン、または質問入力欄からご質問ください。")

for turn in st.session_state[CHAT_HISTORY_KEY]:
    with st.chat_message("user" if turn["role"] == "user" else "assistant"):
        st.markdown(turn["content"])
        if turn["role"] == "assistant":
            st.caption("⚠️ AIは意思決定を支援するものであり、最終判断は職員が行ってください。")

render_footer()
