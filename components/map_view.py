# -*- coding: utf-8 -*-
"""
map_view.py
-------------
Foliumを使って地区ごとに色分けした地図を生成するコンポーネントです。
このアプリの中心機能のため、以下を重視して作成しています。

- 優先度（高・中・低）に応じたマーカーの色分け
- 地区名を地図上に常時ラベル表示（クリックしなくても地区名が分かる）
- 凡例の表示（config.PRIORITY_COLORS と完全に一致させる）
- 地区検索と連動したハイライト表示（検索した地区を強調し、地図を寄せる）
"""

from __future__ import annotations

from typing import Optional

import folium
import pandas as pd

from utils.config import (
    COL_NAME, COL_LAT, COL_LON, COL_SCORE, COL_RANK, COL_PRIORITY,
    PRIORITY_COLORS, PRIORITY_HIGH, PRIORITY_MID, PRIORITY_LOW,
    COLOR_PRIMARY_DARK,
)


def build_priority_map(df: pd.DataFrame, highlight_name: Optional[str] = None) -> folium.Map:
    """
    優先度で色分けした地区マーカーを含むFoliumマップを生成します。

    highlight_name: 地区検索などで強調したい地区名。指定すると、
                     その地区にズームし、マーカーを大きく・枠太めに表示します。
    """
    if highlight_name and highlight_name in df[COL_NAME].values:
        target = df[df[COL_NAME] == highlight_name].iloc[0]
        center_lat, center_lon, zoom = target[COL_LAT], target[COL_LON], 14
    else:
        center_lat, center_lon, zoom = df[COL_LAT].mean(), df[COL_LON].mean(), 12

    fmap = folium.Map(location=[center_lat, center_lon], zoom_start=zoom, tiles="CartoDB positron")

    for _, row in df.iterrows():
        color = PRIORITY_COLORS.get(row[COL_PRIORITY], PRIORITY_COLORS[PRIORITY_MID])
        is_highlighted = highlight_name is not None and row[COL_NAME] == highlight_name

        popup_html = f"""
        <div style="font-size:13px; line-height:1.7; font-family:sans-serif;">
            <b style="font-size:14px;">{row[COL_NAME]}</b><br>
            順位: {int(row[COL_RANK])}位 ／ 優先度: <b>{row[COL_PRIORITY]}</b><br>
            総合スコア: {row[COL_SCORE]:.1f}点<br>
            高齢化率: {row['高齢化率']:.1f}% ／ 単身高齢者割合: {row['単身高齢者割合']:.1f}%<br>
            医療アクセス: {row['医療アクセス']:.1f} ／ 公共交通: {row['公共交通']:.1f}
        </div>
        """

        folium.CircleMarker(
            location=[row[COL_LAT], row[COL_LON]],
            radius=16 if is_highlighted else 11,
            color="#111827" if is_highlighted else color,
            fill=True,
            fill_color=color,
            fill_opacity=0.9,
            weight=3 if is_highlighted else 1.5,
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=f"{row[COL_NAME]}（優先度: {row[COL_PRIORITY]}）",
        ).add_to(fmap)

        # 地区名を常時ラベル表示（クリックしなくても地図上で地区名が分かるようにする）
        folium.map.Marker(
            location=[row[COL_LAT], row[COL_LON]],
            icon=folium.DivIcon(
                icon_size=(150, 20),
                icon_anchor=(0, -14) if is_highlighted else (0, -10),
                html=(
                    f'<div style="font-size:{"13px" if is_highlighted else "11px"}; '
                    f'font-weight:{"700" if is_highlighted else "500"}; '
                    f'color:{COLOR_PRIMARY_DARK}; white-space:nowrap; '
                    f'text-shadow:0 0 3px #fff, 0 0 3px #fff, 0 0 3px #fff;">'
                    f'{row[COL_NAME]}</div>'
                ),
            ),
        ).add_to(fmap)

    _add_legend(fmap)
    return fmap


def _add_legend(fmap: folium.Map) -> None:
    """凡例をHTMLで地図左下に追加します（色は config.PRIORITY_COLORS と連動）。"""
    legend_html = f"""
    <div style="position: fixed; bottom: 30px; left: 30px; z-index:9999;
                background-color: white; padding: 12px 16px; border-radius:8px;
                border:1px solid #dde3ea;
                box-shadow: 0 2px 8px rgba(0,0,0,0.15); font-size:13px; font-family:sans-serif;">
        <b style="color:{COLOR_PRIMARY_DARK};">優先度（見守りニーズ）</b><br>
        <span style="color:{PRIORITY_COLORS[PRIORITY_HIGH]};">●</span> 高（上位25%）<br>
        <span style="color:{PRIORITY_COLORS[PRIORITY_MID]};">●</span> 中<br>
        <span style="color:{PRIORITY_COLORS[PRIORITY_LOW]};">●</span> 低（下位25%）
    </div>
    """
    fmap.get_root().html.add_child(folium.Element(legend_html))
