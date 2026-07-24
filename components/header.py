# -*- coding: utf-8 -*-
"""
header.py
-----------
どのページを開いても必ず表示される
「システムの目的の説明バナー」と「フッター（限界事項）」を提供します。

自治体向けシステムでは、
「これは何をするシステムで、何をしないシステムか」
を毎画面で明示することが誤解防止の観点から重要なため、
共通コンポーネント化しています。
"""

import streamlit as st

from utils.config import APP_TITLE, SYSTEM_DISCLAIMER, SYSTEM_LIMITATIONS


def render_header(page_title: str = ""):
    """ページ上部の共通ヘッダー（タイトル＋説明バナー）を表示します。"""
    st.markdown(
        f"""
        <div style="background-color:#eaf2fb; border-left:6px solid #1d4e89;
                    padding:14px 18px; border-radius:6px; margin-bottom:18px;">
            <div style="font-size:15px; color:#1d3557; line-height:1.7;">
                {SYSTEM_DISCLAIMER}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if page_title:
        st.markdown(f"## {page_title}")


def render_footer():
    """ページ下部の共通フッター（本システムの限界・注意事項）を表示します。"""
    st.markdown("---")
    items_html = "".join([f"<li>{item}</li>" for item in SYSTEM_LIMITATIONS])
    st.markdown(
        f"""
        <div style="background-color:#f5f5f5; border-left:6px solid #888;
                    padding:12px 18px; border-radius:6px; margin-top:10px;">
            <div style="font-size:13px; color:#333;">
                <strong>■ 本システムについて（ご利用にあたっての注意）</strong>
                <ul style="margin:6px 0 0 0; padding-left:20px;">
                    {items_html}
                </ul>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
