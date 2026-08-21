# -*- coding: utf-8 -*-
"""
patterns.py
-------------
「評価パターン」（重みの組み合わせ）を data/patterns.json に保存・読み込みする
モジュールです。

「標準」「移動重視」「見守り重視」のように、職員が重視したい観点ごとに
重みのセットを保存しておき、プルダウンで切り替えられるようにします。
パターンを切り替えると、スコア・ランキング・マップ・地区詳細などが
自動的に再計算されます（各画面は utils.state.get_scored_data() 経由で
現在選択中のパターンの重みを使うため）。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

from utils.config import PATTERNS_PATH


def load_patterns(path: Path = PATTERNS_PATH) -> Dict[str, dict]:
    """保存されている全パターンを {パターン名: {"description":..., "weights":...}} で返します。"""
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_pattern(name: str, weights: Dict[str, float], description: str = "", path: Path = PATTERNS_PATH) -> None:
    """現在の重みを、指定した名前のパターンとして保存します（同名があれば上書き）。"""
    patterns = load_patterns(path)
    patterns[name] = {"description": description, "weights": weights}
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(patterns, f, ensure_ascii=False, indent=2)


def delete_pattern(name: str, path: Path = PATTERNS_PATH) -> None:
    """指定したパターンを削除します。"""
    patterns = load_patterns(path)
    patterns.pop(name, None)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(patterns, f, ensure_ascii=False, indent=2)


def get_pattern(name: str, path: Path = PATTERNS_PATH) -> Optional[dict]:
    """指定した名前のパターンを1つ返します（無ければNone）。"""
    return load_patterns(path).get(name)


def list_pattern_names(path: Path = PATTERNS_PATH) -> list:
    """保存されているパターン名の一覧を返します。"""
    return list(load_patterns(path).keys())
