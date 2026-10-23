"""Evidence-linked policy options, not outcome predictions or causal claims."""
import pandas as pd

POLICIES = [
 ('買い物支援','買い物環境の実態確認と既存サービスの活用', ['supermarkets_drugstores_per_10k','aging_rate_pct'], ['既存の宅配・移動販売・買い物代行の提供範囲を確認','利用者への周知と利用障壁の聞き取り','不足が確認された区域で事業者と小規模試行を協議'], '高齢福祉担当・地域包括支援センター・配達事業者','店舗までの移動時間、利用希望、既存サービスの利用率','周知件数、相談件数、試行利用者数'),
 ('移動支援','移動手段の利用実態調査と移動支援', ['bus_stops_per_10k','weekday_bus_services','late_elderly_rate_pct'], ['路線・時刻・停留所への到達状況を確認','通院・買い物の移動先と困りごとを調査','既存交通の案内を先行し、必要なら移送・予約型交通を協議'], '交通政策担当・高齢福祉担当・交通事業者','地区内運行本数だけではアクセスを測れない。徒歩距離・運行方向・時間帯を確認','交通相談件数、利用者数、目的地到達の改善'),
 ('介護・健康支援','介護予防・相談支援の重点確認', ['care_certification_rate_pct','age_85_plus_pct','community_support_centers'], ['地域包括支援センター等の既存支援状況を確認','介護予防教室・相談窓口の周知を検討','参加しにくい住民への支援方法を関係者と協議'], '高齢福祉担当・地域包括支援センター・医療介護関係者','認定率は年齢構成等に左右される。実際の未充足ニーズを確認','相談到達数、参加者数、継続参加率'),
 ('地域交流','地域サロンへの参加障壁の確認', ['community_salons_per_10k','aging_rate_pct'], ['サロン等の開催場所・頻度を確認','参加希望と移動・開催時間の障壁を聞き取り','既存の交流機会の周知または小規模開催を検討'], '地域団体・社会福祉協議会・高齢福祉担当','サロン数だけでは参加状況や孤立を測れない','案内到達数、参加人数、継続率'),
]

LABELS={'supermarkets_drugstores_per_10k':'スーパー・ドラッグストア数（人口1万人当たり）','aging_rate_pct':'高齢化率（%）','bus_stops_per_10k':'バス停数（人口1万人当たり）','weekday_bus_services':'平日バス運行本数（地区内集計）','late_elderly_rate_pct':'後期高齢者比率（%）','care_certification_rate_pct':'要介護認定率（%）','age_85_plus_pct':'85歳以上人口割合（%）','community_support_centers':'地域包括支援センター数','community_salons_per_10k':'地域サロン数（人口1万人当たり）'}
LOW={'supermarkets_drugstores_per_10k','bus_stops_per_10k','weekday_bus_services','community_support_centers','community_salons_per_10k'}

def build(name, df):
    df=df.copy()
    if name not in df['district'].values: raise ValueError('地区が見つかりません')
    row=df.set_index('district').loc[name]
    for key,source in [('supermarkets_drugstores_per_10k','supermarkets_drugstores'),('bus_stops_per_10k','bus_stops'),('community_salons_per_10k','community_salons')]:
        if key not in df: df[key]=df[source]/df['population'].where(df['population']>0)*10000
    row=df.set_index('district').loc[name]
    proposals=[]
    for field,title,keys,actions,owner,unknowns,kpi in POLICIES:
        evidence=[]
        for k in keys:
            values=pd.to_numeric(df[k],errors='coerce').dropna()
            value=pd.to_numeric(pd.Series([row[k]]),errors='coerce').iloc[0]
            if pd.isna(value) or len(values)<10: continue
            rank=float((values<value).sum()/len(values))
            direction='少ない' if k in LOW else '多い'
            relevant=(rank<=0.25 if k in LOW else rank>=0.75)
            evidence.append({'label':LABELS[k], 'value':float(value), 'median':float(values.median()),'flag':bool(relevant),'text':f'{LABELS[k]}：{value:.1f}（39地区の中央値 {values.median():.1f}）' + (f'。相対的に{direction}ため確認候補' if relevant else '。これだけで課題とは断定できない')})
        proposals.append({'field':field,'title':title,'evidence':evidence,'signals':sum(e['flag'] for e in evidence),'actions':actions,'owner':owner,'unknowns':unknowns,'kpi':kpi})
    proposals.sort(key=lambda p:-p['signals'])
    return proposals

def format_for_ai(name, proposals):
    lines=[f'地区：{name}','以下は実データから作成した検討候補。順位は地区間相対指標の注意信号数であり、政策効果・住民需要の証明ではない。']
    for i,p in enumerate(proposals,1):
        lines += [f'{i}. {p["title"]}（分野：{p["field"]}、相対的な注意信号：{p["signals"]}件）','根拠：'+'；'.join(e['text'] for e in p['evidence']), '実施手順：'+' → '.join(p['actions']),f'実施主体候補：{p["owner"]}',f'追加調査：{p["unknowns"]}',f'検証指標：{p["kpi"]}']
    return '\n'.join(lines)
