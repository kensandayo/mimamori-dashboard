# -*- coding: utf-8 -*-
"""
data_loader.py
---------------
データの読み込み・書き出しを担当するモジュールです。

このファイルが担当すること:
1. data/sample_data.csv の読み込み
2. ユーザーがアップロードしたCSVの読み込み
3. 編集後のデータをCSVとして書き出すための変換
"""

import io
import os

import pandas as pd

from utils.config import REQUIRED_COLUMNS


def load_sample_csv() -> pd.DataFrame:
    """
    プロジェクト内の data/sample_data.csv を読み込みます。

    Excelで「CSV UTF-8」として保存したファイルにも対応するため、
    utf-8-sigを使用しています。
    """
    # 現在のファイル:
    # mimamori_system/utils/data_loader.py
    #
    # 読み込みたいファイル:
    # mimamori_system/data/sample_data.csv
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(base_dir, "data", "sample_data.csv")

    if not os.path.exists(csv_path):
        raise FileNotFoundError(
            f"CSVファイルが見つかりません。\n"
            f"次の場所を確認してください:\n{csv_path}"
        )

    # UTF-8 BOM付き、UTF-8、Shift-JISの順に試す
    encodings = ("utf-8-sig", "utf-8", "cp932", "shift_jis")

    for encoding in encodings:
        try:
            return pd.read_csv(csv_path, encoding=encoding)
        except UnicodeDecodeError:
            continue

    raise ValueError(
        "sample_data.csvの文字コードを判別できませんでした。"
        "Excelで「CSV UTF-8（コンマ区切り）」として保存してください。"
    )


def read_csv_file(uploaded_file) -> pd.DataFrame:
    """
    画面からアップロードされたCSVファイルを読み込みます。

    UTF-8、UTF-8 BOM付き、Shift-JISに対応しています。
    """
    raw_bytes = uploaded_file.read()

    encodings = ("utf-8-sig", "utf-8", "cp932", "shift_jis")

    for encoding in encodings:
        try:
            return pd.read_csv(
                io.BytesIO(raw_bytes),
                encoding=encoding,
            )
        except (UnicodeDecodeError, UnicodeError):
            continue

    raise ValueError(
        "CSVファイルの文字コードを判別できませんでした。"
        "UTF-8またはShift-JISで保存してください。"
    )


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """
    DataFrameをダウンロード用CSVへ変換します。

    Excelで日本語が文字化けしにくいように、
    UTF-8 BOM付きで出力します。
    """
    return df.to_csv(
        index=False,
    ).encode("utf-8-sig")


def get_required_columns():
    """
    CSVに必要な列名の一覧を返します。
    validation.pyなどから利用します。
    """
    return list(REQUIRED_COLUMNS)