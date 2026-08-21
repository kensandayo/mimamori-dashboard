# -*- coding: utf-8 -*-
"""
policy_loader.py
-------------------
他自治体の施策事例マスタ（data/policy_master.csv）を読み込むモジュールです。

評価項目（parameter_master.csv の param_id）と、施策事例の category列を
突き合わせることで、「この評価項目が弱い地区には、この施策例を出す」という
対応関係を、コードのif文ではなくデータ（CSV）として管理しています。

新しい評価項目を追加したときは、policy_master.csv に
category列がその項目のparam_idと一致する行を追加するだけで、
自動的にその項目の改善候補として表示されます。
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import List

from utils.config import POLICY_MASTER_PATH


def load_all_policies(path: Path = POLICY_MASTER_PATH) -> List[dict]:
    """施策マスタの全行を読み込みます。"""
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def get_policies_for_param(param_id: str, path: Path = POLICY_MASTER_PATH) -> List[dict]:
    """
    指定した評価項目（param_id）に関連する施策事例を返します。
    policy_master.csv の category 列が param_id と一致する行を探します。
    """
    return [p for p in load_all_policies(path) if p.get("category") == param_id]
