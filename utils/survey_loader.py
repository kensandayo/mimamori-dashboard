# -*- coding: utf-8 -*-
"""
survey_loader.py
-------------------
自治体が既に保有しているアンケート調査結果（CSV/Excel）を取り込むためのモジュールです。

【設計方針】
「公共交通利用率」「地域活動参加率」のような具体的な質問項目名は、
このファイルは一切知りません（コード内に固定しません）。
このモジュールがやることは次の2つだけです。

1. アップロードされたCSV/Excelファイルを、列名も中身もそのままの
   pandas.DataFrameとして読み込む（read_survey_file）
2. 「どの列を地区名として使うか」「取り込んだ値を、どの地区名の
   行にマージするか」を、地区名文字列を突き合わせて行う（merge_survey_into_data）

「取り込んだ列をどの評価項目として使うか」（既存項目に紐付けるか、
新規項目として登録するか）は、pages/7_data_management.py の画面側で
utils.parameter_loader.add_parameter() 等を呼び出して決定します。
このファイルはあくまで「ファイルを読み、地区名で結合する」ことだけに専念します。
"""

from __future__ import annotations

import io
from typing import List, Tuple

import pandas as pd


def read_survey_file(uploaded_file) -> pd.DataFrame:
    """
    アップロードされたアンケート結果ファイル（CSVまたはExcel）を読み込みます。
    列名・行の中身はそのまま（変換しません）。呼び出し側で好きな列を選べます。
    """
    name = (uploaded_file.name or "").lower()
    raw_bytes = uploaded_file.read()

    if name.endswith((".xlsx", ".xls")):
        try:
            return pd.read_excel(io.BytesIO(raw_bytes))
        except Exception as e:  # noqa: BLE001 - 職員向けに分かりやすいメッセージに変換する
            raise ValueError(f"Excelファイルの読み込みに失敗しました：{e}") from e

    for encoding in ("utf-8-sig", "utf-8", "cp932", "shift_jis"):
        try:
            return pd.read_csv(io.BytesIO(raw_bytes), encoding=encoding)
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise ValueError("CSVファイルの文字コードを判別できませんでした（UTF-8またはShift-JISで保存してください）。")


def preview_columns(df: pd.DataFrame) -> List[str]:
    """アップロードされたファイルの列名一覧を返します（地区名列・取込列の選択に使用）。"""
    return list(df.columns)


def merge_survey_into_data(
    base_df: pd.DataFrame,
    base_name_col: str,
    survey_df: pd.DataFrame,
    survey_name_col: str,
    column_mapping: dict,
) -> Tuple[pd.DataFrame, List[str]]:
    """
    アンケート結果を、地区名で突き合わせて既存データにマージします。

    column_mapping: {アンケート側の列名: マージ後にシステムで使う列名(=CSV列名/param_id)}
        例: {"地域活動参加率": "community_participation"}
        アンケート側の列名とシステム側の列名が同じでも構いません。

    戻り値: (マージ後のDataFrame, 地区名が一致しなかったアンケート側の地区名リスト)
    """
    survey_work = survey_df[[survey_name_col] + list(column_mapping.keys())].copy()
    survey_work = survey_work.rename(columns={survey_name_col: base_name_col, **column_mapping})

    # 数値化できる列は数値化しておく（アンケート集計値が文字列で入っていることがあるため）
    for col in column_mapping.values():
        survey_work[col] = pd.to_numeric(survey_work[col], errors="coerce")

    base_names = set(base_df[base_name_col].astype(str).str.strip())
    survey_names = set(survey_work[base_name_col].astype(str).str.strip())
    unmatched = sorted(survey_names - base_names)

    merged = base_df.merge(survey_work, on=base_name_col, how="left", suffixes=("", "_survey"))

    # 既に同名の列が存在していた場合（既存評価項目への紐付け＝再取込）は
    # 新しい値で上書きする
    for col in column_mapping.values():
        survey_col = f"{col}_survey"
        if survey_col in merged.columns:
            merged[col] = merged[survey_col].combine_first(merged[col]) if col in base_df.columns else merged[survey_col]
            merged = merged.drop(columns=[survey_col])

    return merged, unmatched
