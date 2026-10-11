from pathlib import Path
import hashlib,json,shutil,sys
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold
ROOT=Path(__file__).resolve().parent
WS5=ROOT.parent/'Workshop 5 Modeling and Evaluation'
rawpath=ROOT/'data/heart_2020_cleaned.csv'
NUM=['BMI','PhysicalHealth','MentalHealth','SleepTime']
raw=pd.read_csv(rawpath);sha=hashlib.sha256(rawpath.read_bytes()).hexdigest()
assert raw.shape==(319795,18) and set(raw.HeartDisease)=={'No','Yes'}
assert not raw.isna().any().any()
prepared=raw.copy();prepared['AnyUnhealthyDays']=np.where((raw.PhysicalHealth>0)|(raw.MentalHealth>0),'Yes','No')
quality={'rows_before':len(raw),'rows_after':len(prepared),'columns_before':18,'columns_after':19,'missing_cells_before':int(raw.isna().sum().sum()),'missing_cells_after':int(prepared.isna().sum().sum()),'exact_duplicate_rows_before':int(raw.duplicated().sum()),'exact_duplicate_rows_after':int(prepared.duplicated().sum()),'duplicate_predictor_rows':int(raw.drop(columns='HeartDisease').duplicated().sum()),'target_before':raw.HeartDisease.value_counts().to_dict(),'target_after':prepared.HeartDisease.value_counts().to_dict(),'raw_sha256':sha,'numeric':{},'categories':{c:raw[c].value_counts().to_dict() for c in raw.columns if c not in NUM}}
for c in NUM:
 s=raw[c];q1,q3=s.quantile([.25,.75]);lo=q1-1.5*(q3-q1);hi=q3+1.5*(q3-q1)
 quality['numeric'][c]={'min':float(s.min()),'max':float(s.max()),'median':float(s.median()),'mean':float(s.mean()),'q1':float(q1),'q3':float(q3),'iqr_low':float(lo),'iqr_high':float(hi),'iqr_flag_count':int(((s<lo)|(s>hi)).sum())}
quality['logical_invalid_counts']={'BMI_nonpositive':int((raw.BMI<=0).sum()),'PhysicalHealth_outside_0_30':int(((raw.PhysicalHealth<0)|(raw.PhysicalHealth>30)).sum()),'MentalHealth_outside_0_30':int(((raw.MentalHealth<0)|(raw.MentalHealth>30)).sum()),'SleepTime_outside_0_24':int(((raw.SleepTime<0)|(raw.SleepTime>24)).sum())}
(ROOT/'data_quality.json').write_text(json.dumps(quality,ensure_ascii=False,indent=2),encoding='utf8')
pd.DataFrame(quality['numeric']).T.to_csv(ROOT/'numeric_quality.csv',index_label='attribute')
pd.DataFrame([['Read original',len(raw),18,0,'Preserve all original bytes'],['Missing review',len(raw),18,0,'No blank cells; no imputation'],['Duplicate review',len(raw),18,0,'Anonymous matching survey profiles are not proven same people'],['Outlier review',len(raw),18,0,'Retain; IQR flag is not invalidity'],['Create AnyUnhealthyDays',len(prepared),19,0,'Yes if PhysicalHealth>0 or MentalHealth>0; no target used']],columns=['step','rows_after','columns_after','rows_removed','reason']).to_csv(ROOT/'preparation_log.csv',index=False)
prepared.to_csv(ROOT/'heart_2020_prepared.csv',index=False)
shutil.copy2(rawpath,ROOT/'heart_2020_cleaned.csv');shutil.copy2(rawpath,WS5/'heart_2020_cleaned.csv');shutil.copy2(ROOT/'heart_2020_prepared.csv',WS5/'heart_2020_prepared.csv')
print('QUALITY',json.dumps({k:v for k,v in quality.items() if k not in ['numeric','categories']},ensure_ascii=True),flush=True)
# Group by predictor profile, never by label. Verify no hash collision in this actual file.
predictors=raw.drop(columns='HeartDisease');groups=pd.util.hash_pandas_object(predictors,index=False).to_numpy()
assert np.unique(groups).size==len(predictors.drop_duplicates())
y=(raw.HeartDisease=='Yes').to_numpy().astype(int)
folds=np.full(len(raw),-1,dtype=int)
splitter=StratifiedGroupKFold(n_splits=10,shuffle=True,random_state=2026)
for f,(_,ids) in enumerate(splitter.split(predictors,y,groups)):
 folds[ids]=f
assert (folds>=0).all()
test=folds<3;train=~test
assert not np.intersect1d(np.unique(groups[train]),np.unique(groups[test])).size
assert abs(y[train].mean()-y[test].mean())<.002
assignment=pd.DataFrame({'source_row':np.arange(len(raw))+1,'predictor_profile_hash':groups.astype(str),'fold':folds,'SplitSet':np.where(test,'test','train')})
assignment.to_csv(WS5/'split_assignment.csv',index=False)
modeling=prepared.copy();modeling['SplitSet']=assignment.SplitSet
modeling.to_csv(WS5/'heart_2020_modeling.csv',index=False)
splitinfo={'method':'StratifiedGroupKFold 10 folds, shuffled seed2026; folds0-2 test, folds3-9 train','group_definition':'All 17 original predictor fields; target excluded','train_rows':int(train.sum()),'test_rows':int(test.sum()),'train_positive':int(y[train].sum()),'test_positive':int(y[test].sum()),'train_positive_rate':float(y[train].mean()),'test_positive_rate':float(y[test].mean()),'identical_predictor_profiles_crossing_split':0,'group_hash_collisions_observed':0,'source_rows':len(raw),'raw_sha256':sha,'native_run':False}
(WS5/'split_verification.json').write_text(json.dumps(splitinfo,indent=2),encoding='utf8')
pd.testing.assert_frame_equal(raw,pd.read_csv(ROOT/'heart_2020_prepared.csv')[raw.columns],check_dtype=False)
assert hashlib.sha256(rawpath.read_bytes()).hexdigest()==sha
assert hashlib.sha256((ROOT/'heart_2020_cleaned.csv').read_bytes()).hexdigest()==sha
assert hashlib.sha256((WS5/'heart_2020_cleaned.csv').read_bytes()).hexdigest()==sha
source='Dataset: Indicators of Heart Disease, Kamil Pytlak, Kaggle\nhttps://www.kaggle.com/datasets/kamilpytlak/personal-key-indicators-of-heart-disease\nFile pinned: heart_2020_cleaned.csv (2020 cleaned extract), 319795 rows, 18 columns. Current Kaggle title may mention2022; this task does not silently switch files.\nCDC 2020 BRFSS source documentation https://www.cdc.gov/brfss/annual_data/annual_2020.html\nCDC2020 calculatedvariables https://www.cdc.gov/brfss/annual_data/2020/Summary_Matrix_20.html\n'+sha+'\n'
(ROOT/'source.txt').write_text(source,encoding='utf8');(WS5/'source.txt').write_text(source,encoding='utf8')
print('SPLIT',json.dumps(splitinfo),flush=True)
print('PREPARATION VERIFIED; raw bytes and target preserved',flush=True)
