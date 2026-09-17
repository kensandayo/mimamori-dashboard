# -*- coding: utf-8 -*-
"""
parameter_loader.py
----------------------
評価項目マスタ（data/parameter_master.csv）を読み書きするモジュールです。

【なぜこのファイルが必要か】
このシステムでは「高齢化率」「配食」のような評価項目を、Pythonコードの中に
if文で書くのではなく、CSV（マスタファイル）で管理しています。
そうすることで、職員ヒアリングで新しい指標が必要になったときも、
コードを直さずに「設定・データ管理」画面から項目を追加・削除できます。

呼び出す側（scoring.py・各画面）は、このモジュールの load_active_parameters()
が返すリストだけを見て動くように作られており、指標が何個あっても、
どんな名前でも、同じロジックで処理できます。

各パラメータは以下のキーを持つ辞書として扱います（以前の INDICATORS と互換）。
    key            : CSV上の列名（df[key] で値を取得する）
    label          : 画面に表示する名前
    category       : カテゴリID（utils.category_loaderのcategory_id。未分類は"other"）
    unit           : 単位（%、指数(0-100) など）
    data_type      : データ種別（公開データ／行政保有データ／アンケート／その他）
    risk_direction : "positive"（高いほど課題）/ "negative"（高いほど良い）
    target_year    : 対象年度（表示用の自由文字列。空欄可）
    description    : 説明文
    source         : 出典
    weight_key     : 重み辞書のキー（= param_id。マスタのCSV列名や表示名を
                      変更しても、保存済みの重み・評価パターンが壊れないよう、
                      表示名とは別の安定したIDとして使う）
    active         : スコア計算に使うかどうか（True/False）
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Optional

from utils.config import PARAMETER_MASTER_PATH, DATA_TYPE_OTHER
from utils.category_loader import UNCATEGORIZED_ID

_FIELDNAMES = [
    "param_id", "label", "category", "csv_column", "unit", "data_type",
    "risk_direction", "weight", "target_year", "description", "source", "active",
]


def _to_bool(value: str) -> bool:
    return str(value).strip().upper() in ("TRUE", "1", "YES")


def _row_to_param(row: dict) -> dict:
    return {
        "param_id": row["param_id"],
        "key": row["csv_column"],
        "label": row["label"],
        # category / data_type / target_year は v9以降の追加列。
        # 古いparameter_master.csv（これらの列が無いもの）を読み込んでも
        # 落ちないよう、無ければ既定値（未分類／その他／空欄）を補う。
        "category": (row.get("category") or "").strip() or UNCATEGORIZED_ID,
        "unit": row["unit"],
        "data_type": (row.get("data_type") or "").strip() or DATA_TYPE_OTHER,
        "risk_direction": row["risk_direction"],
        "weight": float(row["weight"]),
        "target_year": row.get("target_year", ""),
        "description": row.get("description", ""),
        "source": row.get("source", ""),
        "weight_key": row["param_id"],
        "active": _to_bool(row.get("active", "TRUE")),
    }


def load_all_parameters(path: Path = PARAMETER_MASTER_PATH) -> List[dict]:
    """マスタに登録されている全項目（無効化されたものも含む）を返します。"""
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return [_row_to_param(row) for row in reader]


def load_active_parameters(path: Path = PARAMETER_MASTER_PATH) -> List[dict]:
    """スコア計算に使う項目（active=TRUE）だけを返します。旧INDICATORSの代わりです。"""
    return [p for p in load_all_parameters(path) if p["active"]]


def get_required_columns(path: Path = PARAMETER_MASTER_PATH) -> List[str]:
    """CSVの必須列（地区名＋マスタに登録された全項目の列＋緯度経度）を返します。"""
    from utils.config import COL_NAME, COL_LAT, COL_LON
    cols = [COL_NAME] + [p["key"] for p in load_all_parameters(path)] + [COL_LAT, COL_LON]
    return cols


def get_default_weights(path: Path = PARAMETER_MASTER_PATH) -> Dict[str, float]:
    """マスタに登録された重みを、有効な項目についてだけ辞書として返します。"""
    return {p["weight_key"]: p["weight"] for p in load_active_parameters(path)}


def _write_all(params: List[dict], path: Path = PARAMETER_MASTER_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_FIELDNAMES)
        writer.writeheader()
        for p in params:
            writer.writerow({
                "param_id": p["param_id"],
                "label": p["label"],
                "category": p.get("category", UNCATEGORIZED_ID),
                "csv_column": p["key"],
                "unit": p["unit"],
                "data_type": p.get("data_type", DATA_TYPE_OTHER),
                "risk_direction": p["risk_direction"],
                "weight": p["weight"],
                "target_year": p.get("target_year", ""),
                "description": p.get("description", ""),
                "source": p.get("source", ""),
                "active": "TRUE" if p["active"] else "FALSE",
            })


def _generate_param_id(label: str, existing_ids: List[str]) -> str:
    """新しい評価項目のIDを自動採番します（custom_1, custom_2, ...）。"""
    n = 1
    while f"custom_{n}" in existing_ids:
        n += 1
    return f"custom_{n}"


def add_parameter(
    label: str, csv_column: str, unit: str, risk_direction: str,
    weight: float, category: str = UNCATEGORIZED_ID, data_type: str = DATA_TYPE_OTHER,
    target_year: str = "", description: str = "", source: str = "", active: bool = True,
    path: Path = PARAMETER_MASTER_PATH,
) -> str:
    """
    新しい評価項目をマスタに追加します。戻り値は自動採番されたparam_idです。
    項目名や列名は既存と重複していないか、呼び出し側（画面）で確認してください。
    category は utils.category_loader のcategory_id（未指定なら「その他」）、
    data_type は utils.config.DATA_TYPE_OPTIONS のいずれかを想定しています。
    """
    params = load_all_parameters(path)
    param_id = _generate_param_id(label, [p["param_id"] for p in params])
    params.append({
        "param_id": param_id, "key": csv_column, "label": label, "category": category,
        "unit": unit, "data_type": data_type, "risk_direction": risk_direction,
        "weight": weight, "target_year": target_year, "description": description,
        "source": source, "weight_key": param_id, "active": active,
    })
    _write_all(params, path)
    return param_id


def update_parameter(param_id: str, path: Path = PARAMETER_MASTER_PATH, **fields) -> None:
    """既存の評価項目を更新します。fieldsにはlabel/unit/risk_direction/weight/active等を渡します。"""
    params = load_all_parameters(path)
    for p in params:
        if p["param_id"] == param_id:
            if "csv_column" in fields:
                p["key"] = fields.pop("csv_column")
            p.update(fields)
    _write_all(params, path)


def delete_parameter(param_id: str, path: Path = PARAMETER_MASTER_PATH) -> None:
    """評価項目をマスタから削除します。"""
    params = [p for p in load_all_parameters(path) if p["param_id"] != param_id]
    _write_all(params, path)


def save_all_parameters(params: List[dict], path: Path = PARAMETER_MASTER_PATH) -> None:
    """評価項目一覧をまとめて保存します（評価項目管理画面の一括編集で使用）。"""
    _write_all(params, path)
