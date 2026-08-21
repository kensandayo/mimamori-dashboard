# -*- coding: utf-8 -*-
"""
validation.py
---------------
アップロードされたCSVや、画面上で編集されたデータを検証するモジュールです。

必須列・数値チェックの対象は、parameter_master.csv に登録されている
評価項目から動的に決まります。指標を追加・削除しても、このファイルは
変更する必要がありません。
"""

from __future__ import annotations

from typing import List, Tuple

import pandas as pd

from utils.config import COL_NAME, COL_LAT, COL_LON
from utils.parameter_loader import load_all_parameters, get_required_columns


def validate_dataframe(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    DataFrameを検証し、(is_valid, errors) を返します。
    """
    errors: List[str] = []

    if df is None or df.empty:
        return False, ["データが空です。CSVファイルの内容を確認してください。"]

    required_columns = get_required_columns()
    missing_cols = [c for c in required_columns if c not in df.columns]
    if missing_cols:
        errors.append(f"必須列が不足しています: {', '.join(missing_cols)}")
        return False, errors

    if df[COL_NAME].isna().any() or (df[COL_NAME].astype(str).str.strip() == "").any():
        errors.append("地区名が空欄の行があります。")

    dup_names = df[COL_NAME][df[COL_NAME].duplicated()].unique().tolist()
    if dup_names:
        errors.append(f"地区名が重複しています: {', '.join(map(str, dup_names))}")

    # 評価項目（マスタ登録済みの列）の数値チェック
    param_columns = [p["key"] for p in load_all_parameters()]
    numeric_cols = param_columns + [COL_LAT, COL_LON]
    for col in numeric_cols:
        if col not in df.columns:
            continue
        converted = pd.to_numeric(df[col], errors="coerce")
        non_numeric_rows = df[converted.isna() & df[col].notna()]
        if not non_numeric_rows.empty:
            errors.append(f"「{col}」に数値以外の値が含まれています（該当行の地区名: "
                          f"{', '.join(map(str, non_numeric_rows[COL_NAME].tolist()))}）。")
        missing_rows = df[converted.isna()]
        if not missing_rows.empty:
            errors.append(f"「{col}」に欠損値があります（該当行の地区名: "
                          f"{', '.join(map(str, missing_rows[COL_NAME].tolist()))}）。")

    # 評価項目（%・指数など0〜100想定の列）の範囲チェック
    for col in param_columns:
        if col not in df.columns:
            continue
        converted = pd.to_numeric(df[col], errors="coerce")
        out_of_range = df[(converted < 0) | (converted > 100)]
        if not out_of_range.empty:
            errors.append(f"「{col}」が0〜100の範囲外の値になっています（該当行の地区名: "
                          f"{', '.join(map(str, out_of_range[COL_NAME].tolist()))}）。")

    # 緯度経度の妥当な範囲チェック（日本国内のおおまかな範囲）
    if COL_LAT in df.columns and COL_LON in df.columns:
        lat_conv = pd.to_numeric(df[COL_LAT], errors="coerce")
        lon_conv = pd.to_numeric(df[COL_LON], errors="coerce")
        bad_lat = df[(lat_conv < 20) | (lat_conv > 46)]
        bad_lon = df[(lon_conv < 122) | (lon_conv > 154)]
        if not bad_lat.empty:
            errors.append(f"「{COL_LAT}」が日本国内の範囲から外れている可能性があります（該当行の地区名: "
                          f"{', '.join(map(str, bad_lat[COL_NAME].tolist()))}）。")
        if not bad_lon.empty:
            errors.append(f"「{COL_LON}」が日本国内の範囲から外れている可能性があります（該当行の地区名: "
                          f"{', '.join(map(str, bad_lon[COL_NAME].tolist()))}）。")

    is_valid = len(errors) == 0
    return is_valid, errors
