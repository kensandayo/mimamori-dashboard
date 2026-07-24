# -*- coding: utf-8 -*-
"""
data_loader.py
---------------
データの読み込み・書き出しを担当するモジュールです。

このアプリの「標準データ」は data/sample_data.csv です。
起動時はこのCSVファイルを読み込み、以後は画面編集やアップロードで
差し替えることができます。CSVファイルの中身を書き換えれば、
コードを一切変更せずに表示内容を更新できます。

将来、宇都宮市の公開データに置き換える場合は、
同じ列構成（utils.config.REQUIRED_COLUMNS）を保った上で
data/sample_data.csv を実データで上書きしてください。
"""

from __future__ import annotations

import io
from typing import Optional

import pandas as pd

from utils.config import DEFAULT_CSV_PATH

# CSV読み込み時に試す文字コードの候補（日本の自治体データはShift-JISのことも多い）
_CANDIDATE_ENCODINGS = ("utf-8-sig", "utf-8", "cp932", "shift_jis")


def load_default_data(csv_path=DEFAULT_CSV_PATH) -> pd.DataFrame:
    """
    標準データ（data/sample_data.csv）を読み込みます。
    アプリ起動時や「標準データに戻す」操作で使用します。
    """
    with open(csv_path, "rb") as f:
        raw_bytes = f.read()
    return _decode_csv_bytes(raw_bytes)


def read_uploaded_csv(uploaded_file) -> pd.DataFrame:
    """Streamlitのfile_uploaderで受け取ったCSVファイルを読み込みます。"""
    raw_bytes = uploaded_file.read()
    return _decode_csv_bytes(raw_bytes)


def _decode_csv_bytes(raw_bytes: bytes) -> pd.DataFrame:
    """複数の文字コードを順に試してCSVバイト列をDataFrameに変換します。"""
    last_error: Optional[Exception] = None
    for encoding in _CANDIDATE_ENCODINGS:
        try:
            return pd.read_csv(io.BytesIO(raw_bytes), encoding=encoding)
        except (UnicodeDecodeError, UnicodeError) as e:
            last_error = e
            continue
    raise ValueError(
        "CSVファイルの文字コードを判別できませんでした（UTF-8またはShift-JISで保存してください）。"
    ) from last_error


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """DataFrameをダウンロード用のCSVバイト列（UTF-8 BOM付き）に変換します。"""
    return df.to_csv(index=False).encode("utf-8-sig")


def save_dataframe_to_csv(df: pd.DataFrame, csv_path=DEFAULT_CSV_PATH) -> None:
    """
    DataFrameを標準データ（data/sample_data.csv）に上書き保存します。

    ここで保存した内容が、次回アプリ起動時に load_default_data() で
    読み込まれる「標準データ」になります。
    呼び出し側（settings.py）で事前にバリデーション（validate_dataframe）を
    済ませてから呼び出してください。
    """
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
