# -*- coding: utf-8 -*-
"""
map_view.py
-------------
Foliumを使って地区ごとに色分けした地図を生成するコンポーネントです。

【v8での変更点】
以前は「優先度（総合スコア由来）」の色分けのみでしたが、
display_param を指定すると、マスタに登録されている任意の評価項目の
健全度スコア（0〜100、高いほど良い）で色分け・ラベル表示できるようにしました。
新しい評価項目を登録すると、この選択肢にも自動的に追加されます
（呼び出し側のページが load_active_parameters() の結果をそのまま渡すため）。
"""

from __future__ import annotations

from typing import Optional

import folium
import pandas as pd

from utils.config import (
    COL_NAME, COL_LAT, COL_LON, COL_SCORE, COL_RANK, COL_PRIORITY,
    PRIORITY_COLORS, PRIORITY_HIGH, PRIORITY_MID, PRIORITY_LOW, COLOR_PRIMARY_DARK,
)
from utils.scoring import get_indicator_health_scores


def _health_color(score: float) -> str:
    """0〜100の健全度スコアを、優先度と同じ配色ルール（低いほど赤）に変換します。"""
    if score < 50:
        return PRIORITY_COLORS[PRIORITY_HIGH]
    if score < 70:
        return PRIORITY_COLORS[PRIORITY_MID]
    return PRIORITY_COLORS[PRIORITY_LOW]


def build_priority_map(
    df: pd.DataFrame,
    highlight_name: Optional[str] = None,
    display_param: Optional[dict] = None,
) -> folium.Map:
    """
    地区マーカーを含むFoliumマップを生成します。

    display_param: Noneなら「総合スコアの優先度」で色分け（従来通り）。
                    parameter_loader由来の項目辞書を渡すと、その項目の
                    健全度スコアで色分け・ラベル表示します。
    highlight_name: 検索などで強調したい地区名。
    """
    if highlight_name and highlight_name in df[COL_NAME].values:
        target = df[df[COL_NAME] == highlight_name].iloc[0]
        center_lat, center_lon, zoom = target[COL_LAT], target[COL_LON], 14
    else:
        center_lat, center_lon, zoom = df[COL_LAT].mean(), df[COL_LON].mean(), 12

    fmap = folium.Map(location=[center_lat, center_lon], zoom_start=zoom, tiles="CartoDB positron")

    for _, row in df.iterrows():
        is_highlighted = highlight_name is not None and row[COL_NAME] == highlight_name

        if display_param is not None:
            health = next(h for h in get_indicator_health_scores(row) if h["param_id"] == display_param["weight_key"])
            color = _health_color(health["score"])
            popup_metric_line = f"{display_param['label']}: {health['score']:.1f}点（健全度）"
            label_value = f"{health['score']:.0f}"
        else:
            color = PRIORITY_COLORS.get(row[COL_PRIORITY], PRIORITY_COLORS[PRIORITY_MID])
            popup_metric_line = f"優先度: <b>{row[COL_PRIORITY]}</b>"
            label_value = None

        popup_html = f"""
        <div style="font-size:13px; line-height:1.7; font-family:sans-serif;">
            <b style="font-size:14px;">{row[COL_NAME]}</b><br>
            順位: {int(row[COL_RANK])}位 ／ 総合スコア: {row[COL_SCORE]:.1f}点<br>
            {popup_metric_line}
        </div>
        """

        folium.CircleMarker(
            location=[row[COL_LAT], row[COL_LON]],
            radius=16 if is_highlighted else 11,
            color="#111827" if is_highlighted else color,
            fill=True, fill_color=color, fill_opacity=0.9,
            weight=3 if is_highlighted else 1.5,
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=f"{row[COL_NAME]}（{popup_metric_line.replace('<b>', '').replace('</b>', '')}）",
        ).add_to(fmap)

        label_text = f"{row[COL_NAME]}" + (f"（{label_value}）" if label_value else "")
        folium.map.Marker(
            location=[row[COL_LAT], row[COL_LON]],
            icon=folium.DivIcon(
                icon_size=(160, 20),
                icon_anchor=(0, -14) if is_highlighted else (0, -10),
                html=(
                    f'<div style="font-size:{"13px" if is_highlighted else "11px"}; '
                    f'font-weight:{"700" if is_highlighted else "500"}; '
                    f'color:{COLOR_PRIMARY_DARK}; white-space:nowrap; '
                    f'text-shadow:0 0 3px #fff, 0 0 3px #fff, 0 0 3px #fff;">'
                    f'{label_text}</div>'
                ),
            ),
        ).add_to(fmap)

    _add_legend(fmap, display_param)
    return fmap


def _add_legend(fmap: folium.Map, display_param: Optional[dict]) -> None:
    """
    凡例を地図左下に追加します。
    色の意味は「赤=課題が大きい／青=良好」でモードによらず統一しています。
    """
    if display_param:
        title = f"{display_param['label']}（健全度スコア）"
        high_line = f"{PRIORITY_COLORS[PRIORITY_HIGH]}::低（0〜49点・課題大）"
        mid_line = f"{PRIORITY_COLORS[PRIORITY_MID]}::中（50〜69点）"
        low_line = f"{PRIORITY_COLORS[PRIORITY_LOW]}::高（70点以上・良好）"
    else:
        title = "優先度（見守りニーズ）"
        high_line = f"{PRIORITY_COLORS[PRIORITY_HIGH]}::高（上位25%）"
        mid_line = f"{PRIORITY_COLORS[PRIORITY_MID]}::中"
        low_line = f"{PRIORITY_COLORS[PRIORITY_LOW]}::低（下位25%）"

    rows_html = ""
    for line in (high_line, mid_line, low_line):
        color, text = line.split("::")
        rows_html += f'<span style="color:{color};">●</span> {text}<br>'

    legend_html = f"""
    <div style="position: fixed; bottom: 30px; left: 30px; z-index:9999;
                background-color: white; padding: 12px 16px; border-radius:8px;
                border:1px solid #dde3ea;
                box-shadow: 0 2px 8px rgba(0,0,0,0.15); font-size:13px; font-family:sans-serif;">
        <b style="color:{COLOR_PRIMARY_DARK};">{title}</b><br>
        {rows_html}
    </div>
    """
    fmap.get_root().html.add_child(folium.Element(legend_html))
