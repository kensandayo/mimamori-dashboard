# -*- coding: utf-8 -*-
"""
data_loader.py
---------------
データの読み込み・書き出しを担当するモジュールです。

・起動時は data/sample_data.csv（標準データ）を読み込みます
・CSVアップロード時は、アップロードされたファイルを読み込みます
・「保存」操作をすると、標準データ（data/sample_data.csv）に上書き保存します
"""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd

from utils.config import DEFAULT_CSV_PATH


def load_default_data(csv_path: Path = DEFAULT_CSV_PATH) -> pd.DataFrame:
    """標準データ（data/sample_data.csv）を読み込みます。"""
    return pd.read_csv(csv_path, encoding="utf-8-sig")


def read_uploaded_csv(uploaded_file) -> pd.DataFrame:
    """
    アップロードされたCSVファイルを読み込みます。
    文字コードはUTF-8とShift-JISの両方に対応を試みます。
    """
    raw_bytes = uploaded_file.read()
    for encoding in ("utf-8-sig", "utf-8", "cp932", "shift_jis"):
        try:
            return pd.read_csv(io.BytesIO(raw_bytes), encoding=encoding)
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise ValueError("CSVファイルの文字コードを判別できませんでした（UTF-8またはShift-JISで保存してください）。")


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """DataFrameをダウンロード用のCSVバイト列（UTF-8 BOM付き）に変換します。"""
    return df.to_csv(index=False).encode("utf-8-sig")


def save_dataframe_to_csv(df: pd.DataFrame, csv_path: Path = DEFAULT_CSV_PATH) -> None:
    """DataFrameを標準データ（data/sample_data.csv）に上書き保存します。"""
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
