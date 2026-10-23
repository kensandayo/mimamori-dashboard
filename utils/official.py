from pathlib import Path
import pandas as pd
CSV=Path(__file__).resolve().parent.parent/'data'/'official_39_districts.csv'
LABELS={'population':'人口（人）','households':'世帯数','aging_rate_pct':'高齢化率（%）','late_elderly_rate_pct':'後期高齢者比率（%）','care_certification_rate_pct':'要介護認定率（%）','weekday_bus_services':'平日バス本数','bus_stops':'バス停数','stations':'駅数','supermarkets_drugstores':'スーパー・ドラッグストア数','hospitals_clinics':'病院・診療所数','dental_clinics':'歯科診療所数','community_salons':'地域サロン数','community_support_centers':'地域包括支援センター数','community_halls':'地域集会所数','age_85_plus_pct':'85歳以上人口割合（%）'}
def load():
 d=pd.read_csv(CSV,encoding='utf-8-sig')
 assert len(d)==39 and d.district.nunique()==39
 return d

def derived(d):
 d=d.copy()
 for col in ('supermarkets_drugstores','hospitals_clinics','bus_stops','community_salons'):
  d[col+'_per_10k']=d[col]/d['population']*10000
 return d
