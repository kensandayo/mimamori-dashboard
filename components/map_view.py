# -*- coding: utf-8 -*-
"""
map_view.py
-------------
Foliumを使って地区ごとに色分けした地図を生成するコンポーネントです。
優先度（高・中・低）に応じてマーカーの色を変えます。
"""

import folium

from utils.config import (
    COL_NAME, COL_LAT, COL_LON, COL_SCORE, COL_RANK, COL_PRIORITY,
    PRIORITY_COLORS,
)


def build_priority_map(df) -> folium.Map:
    """
    優先度で色分けした地区マーカーを含むFoliumマップを生成します。
    """
    center_lat = df[COL_LAT].mean()
    center_lon = df[COL_LON].mean()

    fmap = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles="CartoDB positron")

    for _, row in df.iterrows():
        color = PRIORITY_COLORS.get(row[COL_PRIORITY], "#457b9d")

        popup_html = f"""
        <div style="font-size:13px; line-height:1.6;">
            <b>{row[COL_NAME]}</b><br>
            順位: {int(row[COL_RANK])}位<br>
            総合スコア: {row[COL_SCORE]:.1f}点<br>
            優先度: {row[COL_PRIORITY]}
        </div>
        """

        folium.CircleMarker(
            location=[row[COL_LAT], row[COL_LON]],
            radius=12,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.85,
            weight=2,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{row[COL_NAME]}（{row[COL_PRIORITY]}）",
        ).add_to(fmap)

    # 凡例をHTMLで地図左下に追加
    legend_html = """
    <div style="position: fixed; bottom: 30px; left: 30px; z-index:9999;
                background-color: white; padding: 10px 14px; border-radius:6px;
                box-shadow: 0 0 6px rgba(0,0,0,0.3); font-size:13px;">
        <b>優先度</b><br>
        <span style="color:#e63946;">●</span> 高<br>
        <span style="color:#f4a300;">●</span> 中<br>
        <span style="color:#457b9d;">●</span> 低
    </div>
    """
    fmap.get_root().html.add_child(folium.Element(legend_html))

    return fmap
