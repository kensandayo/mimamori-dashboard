# -*- coding: utf-8 -*-
"""
validation.py
---------------
アップロードされたCSVや、画面上で編集されたデータに対して
入力チェック（バリデーション）を行うモジュールです。

チェック内容:
- 必須列が揃っているか
- 数値であるべき列に数値以外が入っていないか
- 欠損値がないか
- 割合系の指標が0〜100%の範囲に収まっているか
- 緯度経度が欠損していないか
"""

import pandas as pd

from utils.config import (
    REQUIRED_COLUMNS, PERCENT_COLUMNS, COL_NAME, COL_LAT, COL_LON,
)


def validate_dataframe(df: pd.DataFrame):
    """
    DataFrameを検証し、(is_valid: bool, errors: list[str]) を返します。
    エラーがあってもここでは例外を投げず、エラー一覧を返すだけにしています。
    （画面側でまとめて分かりやすく表示するため）
    """
    errors = []

    if df is None or df.empty:
        return False, ["データが空です。CSVファイルの内容を確認してください。"]

    # 1. 必須列の存在チェック
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        errors.append(f"必須列が不足しています: {', '.join(missing_cols)}")
        # 必須列が無い時点でこれ以上の詳細チェックは意味がないため打ち切る
        return False, errors

    # 2. 地区名の欠損チェック
    if df[COL_NAME].isna().any() or (df[COL_NAME].astype(str).str.strip() == "").any():
        errors.append("地区名が空欄の行があります。")

    # 3. 地区名の重複チェック
    dup_names = df[COL_NAME][df[COL_NAME].duplicated()].unique().tolist()
    if dup_names:
        errors.append(f"地区名が重複しています: {', '.join(map(str, dup_names))}")

    # 4. 数値列のチェック（数値変換できるか、欠損がないか）
    numeric_cols = PERCENT_COLUMNS + [COL_LAT, COL_LON]
    for col in numeric_cols:
        converted = pd.to_numeric(df[col], errors="coerce")
        non_numeric_rows = df[converted.isna() & df[col].notna()]
        if not non_numeric_rows.empty:
            errors.append(f"「{col}」に数値以外の値が含まれています（該当行の地区名: "
                          f"{', '.join(map(str, non_numeric_rows[COL_NAME].tolist()))}）。")
        missing_rows = df[converted.isna()]
        if not missing_rows.empty:
            errors.append(f"「{col}」に欠損値があります（該当行の地区名: "
                          f"{', '.join(map(str, missing_rows[COL_NAME].tolist()))}）。")

    # 5. 割合系（%）指標が0〜100の範囲か
    for col in PERCENT_COLUMNS:
        converted = pd.to_numeric(df[col], errors="coerce")
        out_of_range = df[(converted < 0) | (converted > 100)]
        if not out_of_range.empty:
            errors.append(f"「{col}」が0〜100の範囲外の値になっています（該当行の地区名: "
                          f"{', '.join(map(str, out_of_range[COL_NAME].tolist()))}）。")

    # 6. 緯度経度の妥当な範囲チェック（日本国内のおおまかな範囲）
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
