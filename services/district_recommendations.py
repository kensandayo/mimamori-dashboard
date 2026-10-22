"""Rule-based, explainable district characteristics and candidate interventions.
All comparisons are within the currently loaded district dataset, not clinical thresholds.
"""
from __future__ import annotations
import pandas as pd

RULES = [
    {"id":"shopping", "title":"買い物支援の検討", "keys":["買い物アクセス", "移動系"], "actions":["既存の買い物代行・配達サービスの周知", "移動販売の導入可能性の確認", "買い物時の送迎支援の検討"], "considerations":"店舗までの移動実態、既存サービス、利用希望者、実施事業者の対応力"},
    {"id":"watch", "title":"見守り体制の確認", "keys":["単身高齢者割合", "75歳以上人口割合"], "actions":["既存の見守り・緊急通報サービスの周知", "配食等の訪問機会を活用した安否確認の検討", "地域包括支援センター等の既存支援体制との連携検討"], "considerations":"本人の希望、既存の見守り状況、個人情報の取扱い、支援対象者の把握方法"},
    {"id":"outing", "title":"外出・社会参加の支援", "keys":["閉じこもりリスク", "通いの場参加割合"], "actions":["通いの場や地域サロンの情報提供", "移動手段・送迎の検討", "参加を妨げる移動・開催時間などの条件の整理"], "considerations":"アンケートの集計値と個人の把握は別。実際の参加意向と移動上の障壁"},
    {"id":"health", "title":"介護予防・健康づくり", "keys":["転倒リスク", "虚弱リスク", "要支援・要介護リスク"], "actions":["介護予防教室や運動機会の周知", "既存の健康づくり活動への参加支援", "既存の介護予防サービスの提供状況を整理"], "considerations":"年齢構成、調査対象と回答数、既存の介護予防活動、医療・介護職の意見"},
    {"id":"transport", "title":"移動支援の検討", "keys":["移動系", "医療アクセス"], "actions":["公共交通や既存送迎サービスの案内", "予約型交通・移送支援の実施可能性確認", "通院・買い物の移動手段と運行条件の整理"], "considerations":"利用可能な交通手段、移動先、運行費用、運行主体、既存制度との重複"},
]
# For low-is-bad columns, a low value signals attention.
LOW_IS_BAD = {"買い物アクセス", "移動系", "医療アクセス", "通いの場参加割合"}

def build_district_recommendations(district: str, row: pd.Series, df: pd.DataFrame, max_results: int = 4):
    features = []
    signals = {}
    for col in ["高齢化率", "75歳以上人口割合", "単身高齢者割合", "買い物アクセス", "移動系", "医療アクセス", "閉じこもりリスク", "通いの場参加割合", "転倒リスク", "虚弱リスク", "要支援・要介護リスク"]:
        if col not in df.columns or col not in row.index:
            continue
        vals = pd.to_numeric(df[col], errors="coerce").dropna()
        v = pd.to_numeric(pd.Series([row[col]]), errors="coerce").iloc[0]
        if pd.isna(v) or len(vals) < 4 or vals.nunique() < 2:
            continue
        q25, q75 = vals.quantile([0.25, 0.75])
        low_bad = col in LOW_IS_BAD
        attention = v < q25 if low_bad else v > q75
        if not attention:
            continue
        mean = vals.mean()
        direction = "低い" if low_bad else "高い"
        unit = "%" if col not in {"買い物アクセス", "移動系", "医療アクセス"} else ""
        info = {"key":col, "value":float(v), "average":float(mean), "direction":direction,
                "text":f"{col}が39地区内で相対的に{direction}（地区値 {v:.1f}{unit}／地区単純平均 {mean:.1f}{unit}）"}
        features.append(info)
        signals[col] = info
    proposals = []
    for rule in RULES:
        matches = [signals[k] for k in rule["keys"] if k in signals]
        if matches:
            proposals.append({"id":rule["id"], "title":rule["title"], "actions":rule["actions"],
                              "considerations":rule["considerations"], "evidence":matches, "strength":len(matches)})
    proposals.sort(key=lambda x:(-x["strength"], next(i for i,r in enumerate(RULES) if r["id"]==x["id"])))
    return {"district":district, "features":features, "proposals":proposals[:max_results]}
