# -*- coding: utf-8 -*-
"""
header.py
-----------
どのページを開いても必ず表示される「システムの目的の説明バナー」と
「フッター（限界事項）」を提供する共通コンポーネントです。
"""

from __future__ import annotations

import streamlit as st

from utils.config import (
    SYSTEM_DISCLAIMER, SYSTEM_LIMITATIONS, COLOR_PRIMARY, COLOR_PRIMARY_DARK,
    COLOR_ACCENT_BG, COLOR_TEXT_SUB,
)


def render_header(page_title: str = "", page_caption: str = "") -> None:
    st.markdown(
        f"""
        <div style="background-color:{COLOR_ACCENT_BG}; border-left:6px solid {COLOR_PRIMARY};
                    padding:11px 16px; border-radius:8px; margin-bottom:16px;">
            <div style="font-size:13px; color:{COLOR_PRIMARY_DARK}; line-height:1.6;">
                {SYSTEM_DISCLAIMER}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if page_title:
        st.markdown(f"## {page_title}")
    if page_caption:
        st.caption(page_caption)


def render_footer() -> None:
    st.markdown("---")
    items_html = "".join([f"<li>{item}</li>" for item in SYSTEM_LIMITATIONS])
    st.markdown(
        f"""
        <div style="background-color:#f3f4f6; border-left:6px solid {COLOR_TEXT_SUB};
                    padding:10px 16px; border-radius:8px; margin-top:8px;">
            <div style="font-size:12.5px; color:#374151;">
                <strong>本システムについて（ご利用にあたっての注意）</strong>
                <ul style="margin:5px 0 0 0; padding-left:20px;">
                    {items_html}
                </ul>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
