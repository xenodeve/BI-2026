"""Collect real AI Studio Performance-to-Data exports; reject partial/invalid results."""
from pathlib import Path
import json,re,math,hashlib,datetime
import pandas as pd
ROOT=Path(__file__).resolve().parent
MODELS={'NB':'Naive Bayes','LR':'Logistic Regression','DT':'Decision Tree','RF':'Random Forest','GBT':'Gradient Boosted Trees'}
ALIASES={'accuracy':['accuracy'],'precision_yes':['precision'],'recall_yes':['recall','sensitivity'],'f1_yes':['f_measure','f1','f1_score'],'roc_auc':['auc'],'tn':['true_negative','true_negatives'],'fp':['false_positive','false_positives'],'fn':['false_negative','false_negatives'],'tp':['true_positive','true_positives']}
POSITIVE='yes'
EXPECTED_TEST_ROWS=None
EXPECTED_TEST_POSITIVE=None
PROCESS_FILE='MiniProject1.rmp'
def normalize(value):return re.sub('[^a-z0-9]+','_',str(value).lower()).strip('_')
def collect_native_metrics(source_dir=ROOT,write_output=True):
 source_dir=Path(source_dir);required=[source_dir/f'native_{code}.csv' for code in MODELS]
 missing=[f.name for f in required if not f.is_file()]
 if missing:raise FileNotFoundError('Native Run exports missing: '+', '.join(missing))
 run_start=None;log=source_dir/'native_batch.log'
 if write_output:
  log_text=log.read_text(encoding='utf-8-sig')
  if 'Process finished successfully' not in log_text:raise ValueError('Official batch process completion not confirmed')
  run_start=datetime.datetime.fromisoformat(log_text.splitlines()[0].split('=',1)[1]).timestamp()
  if any(f.stat().st_mtime<run_start for f in required):raise ValueError('Native exports predate current batch run')
 before={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in required}
 rows=[];sources=[]
 for code,name in MODELS.items():
  f=source_dir/f'native_{code}.csv';d=pd.read_csv(f);cols={normalize(c):c for c in d.columns}
  if 'criterion' not in cols or 'value' not in cols:raise ValueError(f'{f.name}: unexpected columns {list(d.columns)}')
  keys=d[cols['criterion']].map(normalize)
  if keys.duplicated().any():raise ValueError(f'{f.name}: duplicate criterion names')
  metrics=dict(zip(keys,pd.to_numeric(d[cols['value']],errors='raise')))
  row={'model':name,'engine':'AI Studio official native batch Performance to Data','positive_class':POSITIVE}
  for key,aliases in ALIASES.items():
   found=[metrics[a] for a in aliases if a in metrics]
   if not found:raise ValueError(f'{f.name}: missing {key}; actual criteria {list(metrics)}')
   value=float(found[0])
   if not math.isfinite(value):raise ValueError(f'{f.name}: non-finite {key}')
   row[key]=value
  for key in ['accuracy','precision_yes','recall_yes','f1_yes','roc_auc']:
   if not 0<=row[key]<=1:raise ValueError(f'{f.name}: {key} outside0–1')
  for key in ['tn','fp','fn','tp']:
   value=row[key]
   if value<0 or abs(value-round(value))>1e-7:raise ValueError(f'{f.name}: {key} must be nonnegative integer count')
   row[key]=int(round(value))
  total=sum(row[k] for k in ['tn','fp','fn','tp'])
  if total<=0:raise ValueError(f'{f.name}: no scored test examples')
  tp,fp,fn=row['tp'],row['fp'],row['fn']
  expected={'accuracy':(tp+row['tn'])/total,'precision_yes':tp/(tp+fp) if tp+fp else 0,'recall_yes':tp/(tp+fn) if tp+fn else 0,'f1_yes':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0}
  for key,value in expected.items():
   if abs(row[key]-value)>1e-6:raise ValueError(f'{f.name}: {key} does not reconcile to confusion counts')
  row['test_rows']=total;rows.append(row);sources.append({'model':name,'file':f.name,'bytes':f.stat().st_size})
 result=pd.DataFrame(rows)
 if result.test_rows.nunique()!=1:raise ValueError('Native models did not score equal-sized test sets')
 if (result.tp+result.fn).nunique()!=1 or (result.tn+result.fp).nunique()!=1:raise ValueError('Native test actual-label counts differ across models')
 if EXPECTED_TEST_ROWS is not None and not result.test_rows.eq(EXPECTED_TEST_ROWS).all():raise ValueError('Native test row count differs from fixed assignment')
 if EXPECTED_TEST_POSITIVE is not None and not (result.tp+result.fn).eq(EXPECTED_TEST_POSITIVE).all():raise ValueError('Native positive-label count differs from fixed assignment')
 if before!={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in required}:raise ValueError('Native exports changed during collection')
 if write_output:
  result.to_csv(source_dir/'native_model_comparison.csv',index=False)
  (source_dir/'native_metrics_provenance.json').write_text(json.dumps({'actual_source_exports':sources,'actual_export_sha256':before,'positive_class':POSITIVE,'confusion_reconciliation':True,'same_test_row_count':int(result.test_rows.iloc[0]),'same_test_positive_count':int((result.tp+result.fn).iloc[0]),'execution_mode':'official installed AI Studio native batch','run_start_epoch':run_start,'all_exports_newer_than_run_start':True,'process_finished_successfully':True,'process_sha256':hashlib.sha256((source_dir/PROCESS_FILE).read_bytes()).hexdigest(),'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest(),'gui_Run_or_TurboPrep_claim':False},indent=2),encoding='utf8')
 return result
if __name__=='__main__':print(collect_native_metrics().to_string(index=False))
