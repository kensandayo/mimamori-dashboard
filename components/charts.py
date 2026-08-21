# -*- coding: utf-8 -*-
"""
charts.py
-----------
比較機能・地区詳細など複数のページで使い回すPlotlyグラフ生成関数です。
レーダーチャートの軸は、固定4項目ではなく渡された評価項目リストから動的に作ります。
"""

from __future__ import annotations

from typing import Dict, List

import plotly.graph_objects as go

from utils.config import COLOR_PRIMARY, COLOR_PRIMARY_DARK

_SERIES_COLORS = [COLOR_PRIMARY, "#94a3b8", "#5b8fc7", "#334155"]
_FONT = dict(family="sans-serif", color=COLOR_PRIMARY_DARK)


def build_radar_chart(series_list: List[dict], axes: List[tuple]) -> go.Figure:
    """
    レーダーチャートを生成します。
    series_list: [{"name": "地区A", "row": pandas.Series}, ...]
    axes       : [(表示ラベル, 列名), ...] 動的な評価項目リストから組み立てる
    """
    fig = go.Figure()
    labels = [label for label, _ in axes]

    for i, series in enumerate(series_list):
        row = series["row"]
        values = [row[col] for _, col in axes]
        fig.add_trace(go.Scatterpolar(
            r=values + [values[0]], theta=labels + [labels[0]], fill="toself",
            name=series["name"], line=dict(color=_SERIES_COLORS[i % len(_SERIES_COLORS)]),
        ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True, margin=dict(l=30, r=30, t=30, b=30), height=420, font=_FONT,
    )
    return fig


def build_bar_comparison(names: List[str], values_dict: Dict[str, list], title: str = "") -> go.Figure:
    fig = go.Figure()
    for i, (label, values) in enumerate(values_dict.items()):
        fig.add_trace(go.Bar(name=label, x=names, y=values,
                              marker_color=_SERIES_COLORS[i % len(_SERIES_COLORS)]))
    fig.update_layout(barmode="group", title=title, margin=dict(l=20, r=20, t=40, b=20),
                       height=420, yaxis_title="値", font=_FONT)
    return fig


def build_diff_bar_chart(labels: List[str], diffs: List[float], title: str = "市平均との差") -> go.Figure:
    colors = ["#d64545" if d >= 0 else COLOR_PRIMARY for d in diffs]
    fig = go.Figure(go.Bar(
        x=labels, y=diffs, marker_color=colors,
        text=[f"{d:+.1f}" for d in diffs], textposition="outside",
    ))
    fig.update_layout(title=title, margin=dict(l=20, r=20, t=40, b=20), height=380,
                       yaxis_title="平均との差", font=_FONT)
    return fig


def build_health_score_bar(labels: List[str], scores: List[float], title: str = "評価項目別スコア（高いほど良い）") -> go.Figure:
    """確認候補の表示用：0〜100の健全度スコアを横棒グラフで見せます（低いほど確認候補になりやすい）。"""
    colors = ["#d64545" if s < 50 else ("#e8a33d" if s < 70 else COLOR_PRIMARY) for s in scores]
    fig = go.Figure(go.Bar(
        x=scores, y=labels, orientation="h", marker_color=colors,
        text=[f"{s:.1f}点" for s in scores], textposition="outside",
    ))
    fig.update_layout(title=title, margin=dict(l=10, r=30, t=40, b=10), height=320,
                       xaxis=dict(range=[0, 100]), font=_FONT)
    return fig
