# -*- coding: utf-8 -*-
"""
services/usage_tracker.py
----------------------------
「AI相談」機能の1日あたりの利用回数を管理するモジュールです。
data/ai_usage.json に「日付」と「その日の利用回数」だけを保存し、
アプリを再起動しても引き継がれるようにしています。日付が変わったら自動的に0回にリセットされます。
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import TypedDict

USAGE_FILE_PATH = Path(__file__).resolve().parent.parent / "data" / "ai_usage.json"


class UsageData(TypedDict):
    date: str
    count: int


def _today_str() -> str:
    return date.today().isoformat()


def _load_usage() -> UsageData:
    if not USAGE_FILE_PATH.exists():
        return {"date": _today_str(), "count": 0}
    try:
        with open(USAGE_FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"date": _today_str(), "count": 0}
    if data.get("date") != _today_str():
        return {"date": _today_str(), "count": 0}
    return {"date": data.get("date", _today_str()), "count": int(data.get("count", 0))}


def _save_usage(data: UsageData) -> None:
    USAGE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(USAGE_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def get_today_usage() -> int:
    return _load_usage()["count"]


def increment_usage() -> int:
    data = _load_usage()
    data["count"] += 1
    _save_usage(data)
    return data["count"]
