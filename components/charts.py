# -*- coding: utf-8 -*-
"""
charts.py
-----------
比較機能・地区詳細など複数のページで使い回す
Plotlyグラフ生成関数をまとめたコンポーネントです。
配色は青・白・グレー基調のテーマに合わせています。
"""

from __future__ import annotations

from typing import Dict, List

import pandas as pd
import plotly.graph_objects as go

from utils.config import (
    COL_AGING, COL_SINGLE_ELDERLY, COL_MEDICAL, COL_TRANSPORT,
    COLOR_PRIMARY, COLOR_PRIMARY_DARK,
)

RADAR_AXES = [
    ("高齢化率", COL_AGING),
    ("単身高齢者割合", COL_SINGLE_ELDERLY),
    ("医療アクセス", COL_MEDICAL),
    ("公共交通", COL_TRANSPORT),
]

# 複数系列を重ねる際の配色（青系グラデーション＋グレー）
_SERIES_COLORS = [COLOR_PRIMARY, "#94a3b8", "#5b8fc7", "#334155"]

_FONT = dict(family="sans-serif", color=COLOR_PRIMARY_DARK)


def build_radar_chart(series_list: List[dict]) -> go.Figure:
    """
    レーダーチャートを生成します。
    series_list: [{"name": "地区A", "row": pandas.Series}, ...]
    """
    fig = go.Figure()
    labels = [label for label, _ in RADAR_AXES]

    for i, series in enumerate(series_list):
        row = series["row"]
        values = [row[col] for _, col in RADAR_AXES]
        fig.add_trace(go.Scatterpolar(
            r=values + [values[0]],
            theta=labels + [labels[0]],
            fill="toself",
            name=series["name"],
            line=dict(color=_SERIES_COLORS[i % len(_SERIES_COLORS)]),
        ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        margin=dict(l=30, r=30, t=30, b=30),
        height=420,
        font=_FONT,
    )
    return fig


def build_bar_comparison(names: List[str], values_dict: Dict[str, list], title: str = "") -> go.Figure:
    """
    複数地区・複数指標の棒グラフを生成します。
    values_dict: {"高齢化率": [値1, 値2, ...], "医療アクセス": [...], ...}
    names: 棒グラフのグループ（地区名など）
    """
    fig = go.Figure()
    for i, (label, values) in enumerate(values_dict.items()):
        fig.add_trace(go.Bar(name=label, x=names, y=values,
                              marker_color=_SERIES_COLORS[i % len(_SERIES_COLORS)]))

    fig.update_layout(
        barmode="group",
        title=title,
        margin=dict(l=20, r=20, t=40, b=20),
        height=420,
        yaxis_title="値",
        font=_FONT,
    )
    return fig


def build_diff_bar_chart(labels: List[str], diffs: List[float], title: str = "市平均との差") -> go.Figure:
    """平均との差を色分け（プラス=赤系、マイナス=青系）した棒グラフを生成します。"""
    colors = ["#d64545" if d >= 0 else COLOR_PRIMARY for d in diffs]
    fig = go.Figure(go.Bar(
        x=labels, y=diffs, marker_color=colors,
        text=[f"{d:+.1f}" for d in diffs], textposition="outside",
    ))
    fig.update_layout(title=title, margin=dict(l=20, r=20, t=40, b=20), height=380,
                       yaxis_title="平均との差", font=_FONT)
    return fig
