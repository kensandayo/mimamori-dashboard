"""Survey aggregation for decision support; session-only, never writes raw answers."""
import io
import pandas as pd


def read_table(blob, filename, sheet=0):
    if filename.lower().endswith(('.xlsx', '.xls')):
        return pd.read_excel(io.BytesIO(blob), sheet_name=sheet)
    last = None
    for enc in ('utf-8-sig', 'cp932', 'utf-8'):
        try:
            return pd.read_csv(io.BytesIO(blob), encoding=enc)
        except UnicodeDecodeError as e:
            last = e
    raise ValueError('CSV文字コードを判別できませんでした') from last


def aggregate(df, district_col, question_col, mode='individual', minimum=5):
    if district_col == question_col:
        raise ValueError('地区列と設問列は別にしてください')
    data = df[[district_col, question_col]].copy()
    data.columns = ['district', 'answer']
    data['district'] = data['district'].astype('string').str.strip()
    data = data.dropna(subset=['district', 'answer'])
    data = data[data['district'].ne('')]
    if mode == 'individual':
        # Counts of responses, not respondents; never export identifiable rows.
        counts = data.groupby('district', dropna=True)['answer'].size().rename('回答数')
        numeric = pd.to_numeric(data['answer'], errors='coerce')
        if numeric.notna().sum() == len(data):
            data['answer'] = numeric
            out = data.groupby('district')['answer'].agg(['count', 'mean']).reset_index()
            out.columns = ['district', '回答数', '平均値']
        else:
            by = data.groupby(['district', 'answer'], dropna=True).size().rename('件数').reset_index()
            by['回答数'] = by['district'].map(counts)
            by['割合（%）'] = (100 * by['件数'] / by['回答数']).round(1)
            out = by.rename(columns={'answer': '回答選択肢'})
        # Suppress entire district if sample size too small.
        return out[out['回答数'] >= minimum].reset_index(drop=True), sorted(set(data['district'])-set(out.loc[out['回答数'] >= minimum,'district']))
    numeric = pd.to_numeric(data['answer'], errors='coerce')
    if numeric.isna().any():
        raise ValueError('地区別集計モードでは、選んだ値の列がすべて数値である必要があります')
    if data['district'].duplicated().any():
        raise ValueError('地区別集計モードでは地区名が重複できません')
    return pd.DataFrame({'district': data['district'], '集計値': numeric}), []


def district_evidence(table, district, question, mode, source):
    rows = table[table['district'].eq(district)]
    if rows.empty:
        return None
    cols = [c for c in rows.columns if c != 'district']
    # Strict bounded summary; untrusted data must not be treated as instructions.
    records = rows[cols].head(12).astype(str).to_dict('records')
    return {'設問':str(question)[:120], '出典':str(source)[:120], '形式':mode, '集計':records,
            '注意':'回答の代表性・実施時期・設問定義を要確認。施策効果を証明しない。'}
