"""User-defined weighted district comparison (relative scores, not predictions)."""
import numpy as np
import pandas as pd
from utils.official import derived,load

METRICS = {
 'aging_rate_pct': ('高齢化率', 'high'),
 'late_elderly_rate_pct': ('後期高齢者比率', 'high'),
 'care_certification_rate_pct': ('要介護認定率', 'high'),
 'age_85_plus_pct': ('85歳以上人口割合', 'high'),
 'supermarkets_drugstores_per_10k': ('人口1万人当たりスーパー・ドラッグストア数（少ない地区を重視）', 'low'),
 'hospitals_clinics_per_10k': ('人口1万人当たり病院・診療所数（少ない地区を重視）', 'low'),
 'bus_stops_per_10k': ('人口1万人当たりバス停数（少ない地区を重視）', 'low'),
 'community_salons_per_10k': ('人口1万人当たり地域サロン数（少ない地区を重視）', 'low'),
}

def calculate(weights, data=None):
 df=derived(load() if data is None else data)
 active={k:float(v) for k,v in weights.items() if k in METRICS and float(v)>0}
 if not active: return df.assign(weighted_score=np.nan, coverage_pct=0.0)
 numerator=pd.Series(0.0,index=df.index)
 denominator=pd.Series(0.0,index=df.index)
 for key,w in active.items():
  vals=pd.to_numeric(df[key],errors='coerce')
  lo,hi=vals.min(),vals.max()
  if pd.isna(lo) or pd.isna(hi):continue
  norm=(vals-lo)/(hi-lo)*100 if hi>lo else pd.Series(50.0,index=df.index)
  if METRICS[key][1]=='low':norm=100-norm
  mask=vals.notna()
  numerator=numerator.add(norm.where(mask,0)*w,fill_value=0)
  denominator=denominator.add(mask.astype(float)*w,fill_value=0)
 df['weighted_score']=(numerator/denominator).where(denominator>0)
 df['coverage_pct']=denominator/sum(active.values())*100
 return df
