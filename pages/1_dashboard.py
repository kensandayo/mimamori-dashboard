# -*- coding: utf-8 -*-
"""
dashboard.py
--------------
ヒアリング・デモ向けに1画面で全体状況を把握しやすくしたダッシュボード。
"""

from __future__ import annotations

import streamlit as st

from utils.config import (
    COL_SCORE, COL_PRIORITY, COL_RANK, COL_NAME, PRIORITY_HIGH,
    SYSTEM_LIMITATIONS,
)
from utils.state import get_scored_data, get_data_source_info, get_current_pattern_name
from components.header import render_header
from components.cards import render_metric_cards


# ダッシュボード画面専用：セクション間の余白調整
# (他ページには影響しない。st.container(key=...)は対象のstVerticalBlockに
#  直接 "st-key-<key>" クラスを付与するため、そのクラスへ margin / gap を
#  指定するだけで、各セクション間の余白をピンポイントに調整できる)
st.markdown(
    """
    <style>
    /* 「市内全地区の現状～」「現在の評価パターン～」の2行は同じグループなので
       内部の間隔(gap)は詰め、グループ全体の下だけに適度な余白を持たせる */
    .st-key-dash_intro {
        gap: 0 !important;
        margin-bottom: 6px !important;
    }
    /* 【根本原因 その1】青い説明ボックス自体だけでなく、それを包む
       Streamlit標準の [data-testid="stMarkdownContainer"] にも
       margin-bottom: -1rem（-16px）がStreamlit側のデフォルトCSSとして
       適用されている。この負のmarginがflexアイテム(このstElementContainer)
       の高さ計算にそのまま反映され、実際のボックスの見た目の高さより
       16px短く扱われてしまい、次の要素がボックスの内側に食い込んで
       いた。ボックス本体(div)とstMarkdownContainerの両方の
       margin-bottomを明示的に0へ打ち消す。 */
    .st-key-dash_intro [data-testid="stElementContainer"]:nth-child(1) [data-testid="stMarkdownContainer"] {
        margin-bottom: 0 !important;
    }
    .st-key-dash_intro [data-testid="stElementContainer"]:nth-child(1) [data-testid="stMarkdownContainer"] > div {
        margin-bottom: 0 !important;
    }
    /* 1行目「市内全地区の現状を一目で確認できます。」
       独立したブロックとして扱い、ボックスとの間隔・line-heightを指定する。

       【根本原因】st.caption() が実際に生成する要素は
       data-testid="stCaptionContainer" であり、クラス名 ".stCaption" は
       存在しない。そのため、これまでの margin-top/line-height の指定は
       一度も適用されていなかった。
       さらに、Streamlit標準のCSS（st-emotion-cache-lid8r9）が
       stCaptionContainer に margin-bottom: -1rem（-16px）を標準で
       適用しており、この負のmarginがflexコンテナ(.st-key-dash_introの
       gap:0設定)の高さ計算にそのまま反映されるため、
       このキャプションのflex上の占有領域が実際の文字の高さより16px分
       小さく計算され、文字が上の青いボックスの領域へ visually
       はみ出す（重なる）結果になっていた。
       今回は正しいセレクタ(stCaptionContainer)を指定し、
       このStreamlit標準の負のmarginを明示的に0へ打ち消したうえで、
       margin-topのみで間隔を確定させる。目安: ボックス→1行目 = 12〜16px */
    .st-key-dash_intro [data-testid="stElementContainer"]:nth-child(2) [data-testid="stCaptionContainer"] {
        margin-top: 14px !important;
        margin-bottom: 0 !important;
    }
    .st-key-dash_intro [data-testid="stElementContainer"]:nth-child(2) [data-testid="stCaptionContainer"] p {
        margin: 0 !important;
        line-height: 1.45 !important;
    }
    /* 2行目「現在の評価パターン：標準～」
       同じ理由（stCaptionContainerの標準margin-bottom:-16pxの打ち消し）で
       正しいセレクタに修正。独立したブロックとして扱う。
       目安: 1行目→2行目 = 4〜6px */
    .st-key-dash_intro [data-testid="stElementContainer"]:nth-child(3) [data-testid="stCaptionContainer"] {
        margin-top: 5px !important;
        margin-bottom: 0 !important;
    }
    .st-key-dash_intro [data-testid="stElementContainer"]:nth-child(3) [data-testid="stCaptionContainer"] p {
        margin: 0 !important;
        line-height: 1.45 !important;
    }
    /* サマリーカード行の下に、次のセクションへ向けた余白を追加 */
    .st-key-dash_kpi {
        margin-bottom: 5px !important;
    }
    /* 「着目度が高い地区（TOP5）」見出しとテーブルの間隔を詰める
       (見出し上側の余白は変更しない) */
    .st-key-dash_top5_heading h3 {
        margin-bottom: 0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🏠 ダッシュボード")

with st.container(key="dash_intro"):
    render_header(page_caption="市内全地区の現状を一目で確認できます。")
    st.caption(
        f"現在の評価パターン：**{get_current_pattern_name()}**"
        "（「設定・データ管理」画面で切り替えできます）"
    )

scored_df = get_scored_data()
source_info = get_data_source_info()

n_districts = len(scored_df)
n_high_priority = int((scored_df[COL_PRIORITY] == PRIORITY_HIGH).sum())
avg_score = scored_df[COL_SCORE].mean()

with st.container(key="dash_kpi"):
    render_metric_cards([
        {"label": "地区数", "value": f"{n_districts} 地区"},
        {"label": "高着目地区数", "value": f"{n_high_priority} 地区", "caption": "着目度「高」の地区数"},
        {"label": "平均スコア", "value": f"{avg_score:.1f} 点", "caption": "全地区の総合スコア平均"},
    ])

with st.container(key="dash_top5_heading"):
    st.markdown("### 着目度が高い地区（TOP5）")

top5 = scored_df.sort_values(COL_RANK).head(5)[
    [COL_RANK, COL_NAME, COL_SCORE, COL_PRIORITY]
]

st.dataframe(
    top5,
    use_container_width=True,
    hide_index=True,
    height=185,
    column_config={
        COL_RANK: st.column_config.NumberColumn("順位", width="small"),
        COL_NAME: st.column_config.TextColumn("地区名", width="medium"),
        COL_SCORE: st.column_config.ProgressColumn(
            "総合スコア",
            min_value=0,
            max_value=100,
            format="%.1f点",
            width="large",
        ),
        COL_PRIORITY: st.column_config.TextColumn("着目度", width="small"),
    },
)

# 注意事項を赤丸部分に収めるため2列表示
items_html = "".join(f"<li>{item}</li>" for item in SYSTEM_LIMITATIONS)
st.markdown(
    f"""
    <div class="dashboard-compact-panel">
        <div class="dashboard-compact-panel-title">
            ℹ️ 本システムについて（ご利用にあたっての注意）
        </div>
        <ul>{items_html}</ul>
    </div>

    <div class="dashboard-source-row">
        <div class="dashboard-source-item">
            <div class="dashboard-source-label">データ出典</div>
            <div class="dashboard-source-value">{source_info["source_name"]}</div>
        </div>
        <div class="dashboard-source-item">
            <div class="dashboard-source-label">対象年度</div>
            <div class="dashboard-source-value">{source_info["target_year"]}</div>
        </div>
        <div class="dashboard-source-item">
            <div class="dashboard-source-label">データ更新日</div>
            <div class="dashboard-source-value">{source_info["updated_at"]}</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
