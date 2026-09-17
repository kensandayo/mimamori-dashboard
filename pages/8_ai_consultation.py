# -*- coding: utf-8 -*-
"""
AI相談ページ
------------
・対象地区と比較地区を選択
・地域データをOpenAI APIへ渡して質問
・会話履歴はChatGPT風に表示
・質問入力は st.chat_input() で画面下部に固定
"""

from __future__ import annotations

import streamlit as st

from utils.config import COL_NAME
from utils.state import get_scored_data
from components.header import render_footer
from services.ai_service import (
    AIServiceConfigError,
    AIServiceError,
    build_prompt_context,
    ask_ai_cached,
    get_daily_limit,
    is_ai_configured,
)
from services.usage_tracker import get_today_usage, increment_usage


CHAT_HISTORY_KEY = "ai_chat_history"
PENDING_QUESTION_KEY = "ai_pending_question"
TARGET_KEY = "ai_target_district"
COMPARE_KEY = "ai_compare_district"

QUICK_QUESTIONS = [
    "この地区の特徴をデータから説明して",
    "総合スコアがこの値になっている理由は？",
    "比較地区と比べてどこが違う？",
    "追加で確認した方がよい情報は？",
    "地域カルテも含めて特徴を整理して",
]

# AI相談専用：100%表示でも1画面を広く使う
st.markdown("""
<style>
.ai-page-title{display:flex;align-items:center;gap:.6rem;margin:0 0 .4rem;}
.ai-page-title h1{font-size:1.42rem!important;margin:0!important;line-height:1.1;}
.ai-page-title p{margin:.16rem 0 0;color:#64748b;font-size:.8rem;}
.ai-title-icon{font-size:1.5rem;}
.ai-clear-spacer{height:1.6rem;}
.ai-usage{background:#eaf3ff;border:1px solid #d7e7fb;border-radius:10px;padding:.48rem .68rem;font-size:.78rem;line-height:1.4;margin-top:.05rem;}
.ai-usage span{color:#1457a6;font-weight:700;}
.ai-quick-label{font-size:.78rem;font-weight:700;margin:.15rem 0 .8rem;color:#243b5a;}
[data-testid="stChatMessage"]{border:1px solid #e2e8f0;border-radius:12px;padding:.5rem .68rem;margin:.34rem 0;background:#fff;}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]){background:#eef6ff;}
[data-testid="stChatMessageContent"] p{margin-bottom:.26rem!important;font-size:.9rem!important;}
[data-testid="stChatMessageContent"] ul{margin-top:.14rem!important;margin-bottom:.22rem!important;}
[data-testid="stChatInput"]{border:1px solid #d9e2ec!important;border-radius:12px!important;box-shadow:0 2px 10px rgba(15,23,42,.08);}
/* AIページ固有の調整：下部は固定入力欄(st.chat_input)の分だけ余白を確保する。
   上部のpaddingは共通レイアウト(.block-container)の値をそのまま使うため、
   ここでは指定しない（指定するとタイトルがヘッダーに隠れる原因になる）。 */
[data-testid="stMainBlockContainer"]{padding-bottom:4.2rem!important;}
[data-testid="stVerticalBlock"]{gap:.26rem!important;}
[data-testid="stSelectbox"]{margin-bottom:0!important;}
div.stButton>button{min-height:2.1rem;padding:.26rem .5rem;font-size:.78rem;}
hr{margin:.28rem 0!important;}
</style>
""", unsafe_allow_html=True)


def _clear_chat_if_context_changed(target_name: str, compare_name: str) -> None:
    """地区を変更したとき、前の地区の会話が混ざらないよう履歴をリセットする。"""
    context_key = "ai_last_context"
    new_context = (target_name, compare_name)
    old_context = st.session_state.get(context_key)

    if old_context is not None and old_context != new_context:
        st.session_state[CHAT_HISTORY_KEY] = []

    st.session_state[context_key] = new_context


st.markdown("""
<div class="ai-page-title">
  <div class="ai-title-icon">🤖</div>
  <div><h1>AI相談</h1><p>地域データについて質問すると、AIがデータに基づいて回答します</p></div>
</div>
""", unsafe_allow_html=True)

if CHAT_HISTORY_KEY not in st.session_state:
    st.session_state[CHAT_HISTORY_KEY] = []

# ------------------------------------------------------------
# 地区データ準備
# ------------------------------------------------------------
scored_df = get_scored_data()
district_names = scored_df[COL_NAME].astype(str).tolist()

if not district_names:
    st.error("地区データがありません。")
    st.stop()

selector_col1, selector_col2, selector_col3 = st.columns([2.2, 2.2, 1.0])

with selector_col1:
    target_name = st.selectbox(
        "地区選択",
        options=district_names,
        key=TARGET_KEY,
    )

with selector_col2:
    compare_name = st.selectbox(
        "比較する地区（任意）",
        options=["（比較しない）"] + district_names,
        key=COMPARE_KEY,
    )

with selector_col3:
    st.markdown('<div class="ai-clear-spacer"></div>', unsafe_allow_html=True)
    if st.button("会話履歴をクリア", use_container_width=True, key="ai_clear_top"):
        st.session_state[CHAT_HISTORY_KEY] = []
        st.rerun()

target_row = scored_df[scored_df[COL_NAME].astype(str) == str(target_name)].iloc[0]

compare_row = None
if compare_name != "（比較しない）" and compare_name != target_name:
    compare_row = scored_df[
        scored_df[COL_NAME].astype(str) == str(compare_name)
    ].iloc[0]

_clear_chat_if_context_changed(str(target_name), str(compare_name))

# ------------------------------------------------------------
# API状態・利用回数 / 質問例
# ------------------------------------------------------------
daily_limit = get_daily_limit()
today_usage = get_today_usage()
remaining = max(daily_limit - today_usage, 0)

status_col, usage_col = st.columns([4.8, 1.2])
with status_col:
    context_caption = f'AIには「{target_name}」の地域データを渡します。'
    if compare_row is not None:
        context_caption += f' 比較対象：「{compare_name}」'
    if is_ai_configured():
        st.caption("✅ OpenAI API 接続済み　｜　" + context_caption)
    else:
        st.warning("OpenAI APIキーが未設定です。ローカルは .env、Streamlit Cloud は Settings → Secrets に OPENAI_API_KEY を設定してください。", icon="🔑")

with usage_col:
    st.markdown(
        f'<div class="ai-usage"><b>API利用状況</b><br>利用回数：{today_usage} / {daily_limit}回<br><span>残り：{remaining}回</span></div>',
        unsafe_allow_html=True,
    )

st.markdown('<div class="ai-quick-label">質問例（クリックで送信）</div>', unsafe_allow_html=True)
qcols = st.columns(5)
for i, quick_question in enumerate(QUICK_QUESTIONS):
    with qcols[i]:
        if st.button(quick_question, key=f"ai_quick_{i}", use_container_width=True):
            st.session_state[PENDING_QUESTION_KEY] = quick_question
            st.rerun()


# ------------------------------------------------------------
# チャット履歴
# ------------------------------------------------------------
if not st.session_state[CHAT_HISTORY_KEY]:
    st.markdown(
        """
        <div style="
            text-align:center;
            padding:2.8rem 1rem 2rem 1rem;
            opacity:0.72;
        ">
            <div style="font-size:2.2rem;">💬</div>
            <div style="font-size:1.15rem;font-weight:600;margin-top:.6rem;">
                地域データについて質問してください
            </div>
            <div style="font-size:.9rem;margin-top:.45rem;">
                画面下部の入力欄から続けて質問できます
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

for turn in st.session_state[CHAT_HISTORY_KEY]:
    role = turn.get("role", "assistant")
    with st.chat_message(role, avatar="👤" if role == "user" else "🤖"):
        st.markdown(turn.get("content", ""))

# ------------------------------------------------------------
# 下部固定入力
# ------------------------------------------------------------
pending_question = st.session_state.pop(PENDING_QUESTION_KEY, None)

typed_question = st.chat_input(
    "地域データについて質問する…",
    disabled=(not is_ai_configured()) or (remaining <= 0),
)

question = pending_question or typed_question

if question:
    question = str(question).strip()

    if not question:
        st.stop()

    if remaining <= 0:
        st.error(
            f"本日の利用回数が上限（{daily_limit}回）に達しました。"
        )
        st.stop()

    # AIには、今回の質問を追加する前の直近3往復を渡す
    recent_history = st.session_state[CHAT_HISTORY_KEY][-6:]

    # 画面と履歴にユーザー質問を表示
    st.session_state[CHAT_HISTORY_KEY].append(
        {"role": "user", "content": question}
    )

    with st.chat_message("user", avatar="👤"):
        st.markdown(question)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("地域データを確認しています…"):
            try:
                context = build_prompt_context(
                    target_row,
                    scored_df,
                    compare_row=compare_row,
                )

                answer, was_cached = ask_ai_cached(
                    question,
                    context,
                    history=recent_history,
                )

                st.markdown(answer)

                if was_cached:
                    st.caption("以前の同一質問への回答を再利用しました。")
                else:
                    increment_usage()

                st.session_state[CHAT_HISTORY_KEY].append(
                    {"role": "assistant", "content": answer}
                )

            except AIServiceConfigError as e:
                error_message = f"AI相談機能を使うには設定が必要です：{e}"
                st.error(error_message)
                st.session_state[CHAT_HISTORY_KEY].append(
                    {"role": "assistant", "content": error_message}
                )

            except AIServiceError as e:
                error_message = str(e)
                st.error(error_message)
                st.session_state[CHAT_HISTORY_KEY].append(
                    {"role": "assistant", "content": error_message}
                )

            except Exception as e:
                error_message = f"予期しないエラーが発生しました：{e}"
                st.error(error_message)
                st.session_state[CHAT_HISTORY_KEY].append(
                    {"role": "assistant", "content": error_message}
                )

    st.rerun()

