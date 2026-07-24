# -*- coding: utf-8 -*-
"""
data_loader.py
---------------
データの読み込み・書き出し・サンプルデータ生成を担当するモジュールです。

このファイルが担当すること:
1. 起動時に使うダミー（サンプル）データの生成
2. ユーザーがアップロードしたCSVの読み込み
3. 編集後のデータをCSVとして書き出すための変換
"""

import io
import numpy as np
import pandas as pd

from utils.config import (
    COL_NAME, COL_AGING, COL_SINGLE_ELDERLY, COL_MEDICAL, COL_TRANSPORT,
    COL_LAT, COL_LON, REQUIRED_COLUMNS,
)

# サンプルデータの中心座標（宇都宮市付近を想定した架空の地区配置）
BASE_LAT = 36.5551
BASE_LON = 139.8828

# サンプル地区名（架空の地区名。実在の行政区域データではありません）
SAMPLE_DISTRICT_NAMES = [
    "中央地区", "北部地区", "南部地区", "東部地区", "西部地区",
    "緑ヶ丘地区", "川沿い地区", "山手地区", "駅前地区", "新興住宅地区",
    "田園地区", "臨海地区",
]


def generate_sample_data(seed: int = 42) -> pd.DataFrame:
    """
    デモ用のダミーデータを生成します。

    実在の統計データではなく、プロトタイプの動作確認用に
    ランダム生成した架空の数値です。CSVアップロード機能を使えば
    実際のデータに差し替えることができます。
    """
    rng = np.random.default_rng(seed)
    n = len(SAMPLE_DISTRICT_NAMES)

    # 高齢化率: 20%〜45%程度でばらつかせる
    aging = rng.uniform(20, 45, n).round(1)
    # 単身高齢者割合: 5%〜35%程度
    single_elderly = rng.uniform(5, 35, n).round(1)
    # 医療アクセス指数: 20〜95（高いほど良い）
    medical = rng.uniform(20, 95, n).round(1)
    # 公共交通指数: 15〜95（高いほど良い）
    transport = rng.uniform(15, 95, n).round(1)

    # 緯度経度は中心から少しずつずらして配置（地図表示用のダミー座標）
    lat_offsets = rng.uniform(-0.06, 0.06, n)
    lon_offsets = rng.uniform(-0.08, 0.08, n)
    lats = (BASE_LAT + lat_offsets).round(6)
    lons = (BASE_LON + lon_offsets).round(6)

    df = pd.DataFrame({
        COL_NAME: SAMPLE_DISTRICT_NAMES,
        COL_AGING: aging,
        COL_SINGLE_ELDERLY: single_elderly,
        COL_MEDICAL: medical,
        COL_TRANSPORT: transport,
        COL_LAT: lats,
        COL_LON: lons,
    })
    return df


def read_csv_file(uploaded_file) -> pd.DataFrame:
    """
    アップロードされたCSVファイルを読み込みます。
    文字コードはUTF-8とShift-JISの両方に対応を試みます。
    """
    raw_bytes = uploaded_file.read()
    for encoding in ("utf-8-sig", "utf-8", "cp932", "shift_jis"):
        try:
            df = pd.read_csv(io.BytesIO(raw_bytes), encoding=encoding)
            return df
        except (UnicodeDecodeError, UnicodeError):
            continue
    # すべて失敗した場合は例外を送出する（呼び出し側でエラー表示する）
    raise ValueError("CSVファイルの文字コードを判別できませんでした（UTF-8またはShift-JISで保存してください）。")


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """DataFrameをダウンロード用のCSVバイト列（UTF-8 BOM付き）に変換します。"""
    return df.to_csv(index=False).encode("utf-8-sig")


def get_required_columns():
    """必須列のリストを返します（validation.pyから利用）。"""
    return list(REQUIRED_COLUMNS)
