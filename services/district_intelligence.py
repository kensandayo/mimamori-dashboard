"""Deterministic district evidence and policy suggestions (not outcome predictions)."""
from __future__ import annotations
import pandas as pd
from utils.config import COL_NAME
from utils.parameter_loader import load_all_parameters

ISSUES = {
    "買い物支援": ["shopping_access", "single_elderly", "mobility"],
    "通院・移動支援": ["medical", "mobility", "old75"],
    "見守り訪問": ["single_elderly", "social_participation", "aging"],
    "配食支援": ["single_elderly", "shopping_access", "aging"],
}

def indicators(df):
    return [p for p in load_all_parameters() if p['key'] in df.columns and pd.to_numeric(df[p['key']],errors='coerce').notna().sum() >= 2]

def evidence(df, district):
    rows=df.loc[df[COL_NAME].astype(str)==str(district)]
    if rows.empty: return []
    row=rows.iloc[0]
    result=[]
    for p in indicators(df):
        col=p['key']; vals=pd.to_numeric(df[col],errors='coerce').dropna()
        v=pd.to_numeric(pd.Series([row[col]]),errors='coerce').iloc[0]
        if pd.isna(v): continue
        mean=float(vals.mean()); n=len(vals)
        # Percentile rank of numeric values (ties share a rank).
        pct=float((vals<=v).sum()/n)
        issue_pct=pct if p['risk_direction']=='positive' else 1-pct
        rank=int((vals>v).sum()+1)
        result.append({'id':p['param_id'],'指標':p['label'],'数値':round(float(v),2),
            '単位':p['unit'],'地区平均':round(mean,2),'平均との差':round(float(v)-mean,2),
            '高い順順位':rank,'比較地区数':n,'課題方向の相対位置':round(issue_pct,3),
            '解釈':'高いほど支援課題の可能性' if p['risk_direction']=='positive' else '低いほど支援課題の可能性'})
    return sorted(result,key=lambda x:x['課題方向の相対位置'],reverse=True)

def search_districts(df, indicator_id, direction='課題が大きい順', limit=10):
    p=next((p for p in indicators(df) if p['param_id']==indicator_id),None)
    if p is None: return pd.DataFrame()
    subset=df[[COL_NAME,p['key']]].copy()
    subset[p['key']]=pd.to_numeric(subset[p['key']],errors='coerce')
    subset=subset.dropna(subset=[p['key']])
    bad_high=p['risk_direction']=='positive'
    ascending=not bad_high if direction=='課題が大きい順' else bad_high
    subset=subset.sort_values(p['key'],ascending=ascending).head(limit)
    return subset.rename(columns={p['key']:p['label']}).reset_index(drop=True)

def issue_suggestions(evidence_rows):
    byid={r['id']:r for r in evidence_rows}
    suggestions=[]
    for issue,ids in ISSUES.items():
        found=[byid[i] for i in ids if i in byid]
        if not found: continue
        score=sum(r['課題方向の相対位置'] for r in found)/len(found)
        suggestions.append({'課題':issue,'相対的な着目度':round(score,2),
            '根拠': '、'.join(f"{r['指標']}（{r['数値']}{r['単位']}・高い順{r['高い順順位']}位）" for r in found),
            '確認事項':'既存サービスの利用状況・対象者の実際のニーズ・実施主体を確認'})
    return sorted(suggestions,key=lambda x:x['相対的な着目度'],reverse=True)

def evidence_context(df,district):
    ev=evidence(df,district)
    sug=issue_suggestions(ev)
    lines=[f"【Pythonで計算した地区分析】対象地区: {district}、比較対象: データがある地区（指標ごとに欠損除外）。",'上位の着目指標（相対評価は施策効果の予測ではない）:']
    lines += [f"- {r['指標']}: {r['数値']}{r['単位']}、平均{r['地区平均']}{r['単位']}、高い順{r['高い順順位']}/{r['比較地区数']}位、指標の解釈:{r['解釈']}" for r in ev[:12]]
    lines += ['施策カテゴリの検討候補（数値は複数指標の相対位置の単純平均であり、施策必要性や効果の推定ではない）:']
    lines += [f"- {s['課題']}: 相対位置{s['相対的な着目度']}, 根拠 {s['根拠']}" for s in sug]
    lines += ['注意: データには仮データが含まれる。実際の需要・事業者・予算・効果を断定しない。']
    return '\n'.join(lines)
