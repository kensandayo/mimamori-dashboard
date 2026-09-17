# -*- coding: utf-8 -*-
"""
category_loader.py
----------------------
評価項目を束ねる「カテゴリ」マスタ（data/category_master.csv）を読み書きするモジュールです。

【なぜこのファイルが必要か】
評価項目（parameter_master.csv）が増えてくると、フラットな一覧だけでは
「人口・世帯」「移動・生活環境」のような観点別の傾向が見えにくくなります。
一方で、カテゴリの種類（名前・数・並び順）を自治体ごとに変えたい可能性も
あるため、parameter_loader.py と同じ考え方で、カテゴリ自体もCSVマスタとして
管理し、コードを直さずに「設定・データ管理」画面から追加・編集・削除できる
ようにしています。

各評価項目（utils.parameter_loader の各dict）は "category" キーに
このマスタの category_id を持ちます。category_id がマスタに存在しない、
または空文字の場合は、呼び出し側で自動的に "other"（その他）として扱われます
（＝カテゴリ列が無い古いparameter_master.csvとの後方互換のため）。
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Optional

from utils.config import CATEGORY_MASTER_PATH

_FIELDNAMES = ["category_id", "label", "display_order"]

UNCATEGORIZED_ID = "other"
UNCATEGORIZED_LABEL = "その他"


def load_all_categories(path: Path = CATEGORY_MASTER_PATH) -> List[dict]:
    """カテゴリマスタの全行を、display_order順で返します。"""
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = [
            {
                "category_id": row["category_id"],
                "label": row["label"],
                "display_order": int(row.get("display_order") or 999),
            }
            for row in reader
        ]
    rows.sort(key=lambda r: r["display_order"])
    # "other"（その他）は必ず一覧の最後に存在させる（未分類の評価項目の受け皿）
    if not any(r["category_id"] == UNCATEGORIZED_ID for r in rows):
        rows.append({"category_id": UNCATEGORIZED_ID, "label": UNCATEGORIZED_LABEL,
                     "display_order": 999})
    return rows


def get_category_label(category_id: Optional[str], path: Path = CATEGORY_MASTER_PATH) -> str:
    """category_id から表示名を返します。未登録・空文字の場合は「その他」を返します。"""
    if not category_id:
        return UNCATEGORIZED_LABEL
    for c in load_all_categories(path):
        if c["category_id"] == category_id:
            return c["label"]
    return UNCATEGORIZED_LABEL


def get_category_map(path: Path = CATEGORY_MASTER_PATH) -> Dict[str, str]:
    """{category_id: label} の辞書を返します（表示用のルックアップに使います）。"""
    return {c["category_id"]: c["label"] for c in load_all_categories(path)}


def _write_all(categories: List[dict], path: Path = CATEGORY_MASTER_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_FIELDNAMES)
        writer.writeheader()
        for c in categories:
            writer.writerow({
                "category_id": c["category_id"],
                "label": c["label"],
                "display_order": c["display_order"],
            })


def _generate_category_id(existing_ids: List[str]) -> str:
    n = 1
    while f"category_{n}" in existing_ids:
        n += 1
    return f"category_{n}"


def add_category(label: str, display_order: Optional[int] = None,
                  path: Path = CATEGORY_MASTER_PATH) -> str:
    """新しいカテゴリを追加します。戻り値は自動採番されたcategory_idです。"""
    categories = load_all_categories(path)
    category_id = _generate_category_id([c["category_id"] for c in categories])
    if display_order is None:
        # "その他"の手前に挿入されるよう、その他より1つ小さい順序にする
        others = [c["display_order"] for c in categories if c["category_id"] != UNCATEGORIZED_ID]
        display_order = (max(others) + 1) if others else 1
    categories = [c for c in categories if c["category_id"] != UNCATEGORIZED_ID]
    categories.append({"category_id": category_id, "label": label, "display_order": display_order})
    categories.append({"category_id": UNCATEGORIZED_ID, "label": UNCATEGORIZED_LABEL, "display_order": 999})
    _write_all(categories, path)
    return category_id


def update_category(category_id: str, path: Path = CATEGORY_MASTER_PATH, **fields) -> None:
    """既存カテゴリのlabel/display_orderを更新します。"""
    categories = load_all_categories(path)
    for c in categories:
        if c["category_id"] == category_id:
            c.update(fields)
    _write_all(categories, path)


def delete_category(category_id: str, path: Path = CATEGORY_MASTER_PATH) -> None:
    """
    カテゴリを削除します（"other"は削除できません）。
    このカテゴリを使っている評価項目は、呼び出し側の表示時に自動的に
    「その他」として扱われます（parameter_master.csv 側の値は変更しません）。
    """
    if category_id == UNCATEGORIZED_ID:
        return
    categories = [c for c in load_all_categories(path) if c["category_id"] != category_id]
    _write_all(categories, path)
