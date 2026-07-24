# -*- coding: utf-8 -*-
"""
cards.py
----------
ダッシュボードや地区詳細画面で使う「カード形式の指標表示」を
共通化したコンポーネントです。

以前はページごとにHTML文字列を個別に組み立てていましたが、
デザインの一貫性と保守性を高めるためにここへ集約しています。
"""

from __future__ import annotations

from typing import List, Optional, TypedDict

import streamlit as st

from utils.config import COLOR_PRIMARY_DARK, COLOR_BORDER, COLOR_TEXT_SUB


class CardData(TypedDict, total=False):
    label: str
    value: str
    caption: Optional[str]


_CARD_TEMPLATE = """
<div style="background-color:#ffffff; border:1px solid {border}; border-radius:12px;
            padding:18px 16px; text-align:center; box-shadow:0 1px 4px rgba(15,23,42,0.06);
            height:100%;">
    <div style="font-size:13px; color:{sub}; margin-bottom:8px; font-weight:600;">{label}</div>
    <div style="font-size:28px; font-weight:700; color:{primary};">{value}</div>
    {caption_html}
</div>
"""


def render_metric_cards(cards: List[CardData], columns: Optional[int] = None) -> None:
    """
    カード形式で指標を横並び表示します。
    cards: [{"label": "地区数", "value": "12 地区", "caption": "任意の補足"}, ...]
    """
    n = columns or len(cards)
    cols = st.columns(n)
    for col, card in zip(cols, cards):
        caption_html = ""
        if card.get("caption"):
            caption_html = f'<div style="font-size:12px; color:{COLOR_TEXT_SUB}; margin-top:6px;">{card["caption"]}</div>'
        with col:
            st.markdown(
                _CARD_TEMPLATE.format(
                    border=COLOR_BORDER,
                    sub=COLOR_TEXT_SUB,
                    primary=COLOR_PRIMARY_DARK,
                    label=card["label"],
                    value=card["value"],
                    caption_html=caption_html,
                ),
                unsafe_allow_html=True,
            )


def render_info_strip(items: List[CardData]) -> None:
    """データ出典・対象年度・更新日など、小さな情報チップを横並びで表示します。"""
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        with col:
            st.markdown(
                f"""
                <div style="background-color:#f6f8fa; border:1px solid {COLOR_BORDER};
                            border-radius:8px; padding:8px 12px;">
                    <div style="font-size:11px; color:{COLOR_TEXT_SUB};">{item['label']}</div>
                    <div style="font-size:13px; color:{COLOR_PRIMARY_DARK}; font-weight:600;">{item['value']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
