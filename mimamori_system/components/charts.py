# -*- coding: utf-8 -*-
"""
charts.py
-----------
比較機能・地区レポートなど複数のページで使い回す
Plotlyグラフ生成関数をまとめたコンポーネントです。
"""

import plotly.graph_objects as go

from utils.config import COL_AGING, COL_SINGLE_ELDERLY, COL_MEDICAL, COL_TRANSPORT

RADAR_AXES = [
    ("高齢化率", COL_AGING),
    ("単身高齢者割合", COL_SINGLE_ELDERLY),
    ("医療アクセス", COL_MEDICAL),
    ("公共交通", COL_TRANSPORT),
]


def build_radar_chart(series_list: list) -> go.Figure:
    """
    レーダーチャートを生成します。
    series_list: [{"name": "地区A", "row": pandas.Series}, ...]
    """
    fig = go.Figure()
    labels = [label for label, _ in RADAR_AXES]

    for series in series_list:
        row = series["row"]
        values = [row[col] for _, col in RADAR_AXES]
        fig.add_trace(go.Scatterpolar(
            r=values + [values[0]],
            theta=labels + [labels[0]],
            fill="toself",
            name=series["name"],
        ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        margin=dict(l=30, r=30, t=30, b=30),
        height=420,
    )
    return fig


def build_bar_comparison(names: list, values_dict: dict, title: str = "") -> go.Figure:
    """
    複数地区・複数指標の棒グラフを生成します。
    values_dict: {"高齢化率": [値1, 値2, ...], "医療アクセス": [...], ...}
    names: 棒グラフのグループ（地区名など）
    """
    fig = go.Figure()
    for label, values in values_dict.items():
        fig.add_trace(go.Bar(name=label, x=names, y=values))

    fig.update_layout(
        barmode="group",
        title=title,
        margin=dict(l=20, r=20, t=40, b=20),
        height=420,
        yaxis_title="値",
    )
    return fig


def build_diff_bar_chart(labels: list, diffs: list, title: str = "市平均との差") -> go.Figure:
    """平均との差を色分け（プラス=赤系、マイナス=青系）した棒グラフを生成します。"""
    colors = ["#e63946" if d >= 0 else "#457b9d" for d in diffs]
    fig = go.Figure(go.Bar(
        x=labels, y=diffs, marker_color=colors,
        text=[f"{d:+.1f}" for d in diffs], textposition="outside",
    ))
    fig.update_layout(title=title, margin=dict(l=20, r=20, t=40, b=20), height=380,
                       yaxis_title="平均との差")
    return fig
