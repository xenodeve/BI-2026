"""Fail-closed intake of actual native nine-model full-holdout exports."""
from pathlib import Path
import hashlib,json,math,re,time,argparse,datetime,csv,collections,xml.etree.ElementTree as E
from zoneinfo import ZoneInfo
import numpy as np,pandas as pd
from sklearn.metrics import roc_auc_score,average_precision_score
R=Path(__file__).resolve().parent
MODELS={'NB':'Naive Bayes','GLM':'Generalized Linear Model','LR':'Logistic Regression','FLM':'Fast Large Margin','DL':'Deep Learning','DT':'Decision Tree','RF':'Random Forest','GBT':'Gradient Boosted Trees','SVM':'Support Vector Machine'}
LABEL='PATIENT_TYPE';ID='COMMON_ROW_ID';POS='Hospitalized';NEG='Outpatient'
def normalize(s):return re.sub('[^a-z0-9]+','_',str(s).lower()).strip('_')
def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()

def prepared_source_membership(train,test):
 manifest=json.loads((R/'common_test_build_manifest.json').read_text())
 source=Path(manifest['prepared_source']);before=digest(source)
 if before!=manifest['prepared_source_sha256']:raise ValueError('Full native prepared source CSV changed')
 required=train|test;found=set();counts=collections.Counter();population=0
 with source.open(encoding='utf-8-sig',newline='') as f:
  reader=csv.reader(f);header=next(reader);label_index=header.index(LABEL)
  for row_id,row in enumerate(reader,1):
   population=row_id;label=row[label_index];counts[label]+=1
   if row_id in required:
    if required[row_id]!=label:raise ValueError(f'ID{row_id}: exported label differs from full prepared source row')
    found.add(row_id)
 if population!=1048575 or dict(counts)!={NEG:848544,POS:200031}:raise ValueError('Full prepared population count/labels differ from native TurboPrep result')
 if found!=set(required) or len(found)!=30000:raise ValueError('Common modelling IDs not covered by full prepared source')
 if digest(source)!=before:raise ValueError('Prepared source changed during verification')
 return {'full_source_rows':population,'full_source_label_counts':dict(counts),'prepared_source_sha256':before,'all_30000_sample_ids_and_labels_match_source_row_positions':True}
def membership(frame,expected_rows,filename):
 if ID not in frame or LABEL not in frame:raise ValueError(f'{filename}: missing ID or true-label column')
 if len(frame)!=expected_rows:raise ValueError(f'{filename}: rows{len(frame)} expected{expected_rows}')
 ids=pd.to_numeric(frame[ID],errors='raise')
 if ids.isna().any() or not np.isfinite(ids).all() or not np.equal(ids,np.floor(ids)).all():raise ValueError(f'{filename}: invalid source IDs')
 if ids.duplicated().any():raise ValueError(f'{filename}: duplicate source IDs')
 if not ids.between(1,1048575).all():raise ValueError(f'{filename}: IDs outside full prepared source')
 if frame[LABEL].isna().any() or set(frame[LABEL])!={POS,NEG}:raise ValueError(f'{filename}: invalid true labels')
 pairs={int(i):str(y) for i,y in zip(ids,frame[LABEL])}
 canonical=''.join(f'{i}\t{pairs[i]}\n' for i in sorted(pairs)).encode()
 return pairs,hashlib.sha256(canonical).hexdigest()
def source_checks():
 manifest=json.loads((R/'common_test_build_manifest.json').read_text())
 for m in manifest['models']:
  if digest(Path(m['original_path']))!=m['original_sha256']:raise ValueError('Original native source changed: '+m['model'])
 d=E.parse(R/manifest['driver']);top=d.find('.//operator/process');checks=[]
 for code in MODELS:
  wrapper=next(o for o in top.findall('operator') if o.attrib['name']=='Run '+code)
  load=next(o for o in wrapper.findall('.//operator') if o.attrib['name']==code+'__Load and Process Data').find('process')
  names=[o.attrib['name'] for o in load.findall('operator')]
  if not names.index(code+'__Preprocessing')<names.index(code+'__Common Source Row ID')<names.index(code+'__Filter Examples')<names.index(code+'__Sample'):raise ValueError('ID injection order invalid: '+code)
  role=next(o for o in load.findall('operator') if o.attrib['name']==code+'__Protect Common Row ID')
  if role.find("parameter[@key='target_role']").attrib['value']!='id':raise ValueError('ID not special: '+code)
  forbidden=[]
  for o in wrapper.findall('.//operator'):
   if o.attrib['class']=='set_role':
    attr=o.find("parameter[@key='attribute_name']");target=o.find("parameter[@key='target_role']")
    if attr is not None and attr.attrib['value']==ID and target is not None and target.attrib['value']!='id':forbidden.append(o.attrib['name'])
   if o.attrib['class'] in ['naive_bayes','h2o:generalized_linear_model','h2o:logistic_regression','logistic_regression','h2o:deep_learning','concurrency:parallel_decision_tree','concurrency:parallel_random_forest','h2o:gradient_boosted_trees','support_vector_machine','linear_svm']:
    if ID in E.tostring(o,encoding='unicode'):forbidden.append(o.attrib['name'])
  if forbidden:raise ValueError('ID referenced as learner/regular input: '+str(forbidden))
  checks.append({'model':MODELS[code],'id_is_special_after_general_preprocessing_before_filter_and_sample':True,'no_explicit_learner_parameter_or_regular_role_uses_ID':True})
 return checks
def collect(directory=R,not_before=None):
 directory=Path(directory)
 required=[directory/f'{kind}_{code}.csv' for code in MODELS for kind in ['metrics','predictions','train_ids','test_ids']]
 missing=[p.name for p in required if not p.is_file()]
 if missing:raise FileNotFoundError('Native comparison unavailable; missing exports: '+', '.join(missing))
 if not_before is not None:
  stale=[p.name for p in required if p.stat().st_mtime<not_before]
  if stale:raise ValueError('Exports predate required native run start: '+', '.join(stale))
 hashes_before={p.name:digest(p) for p in required}
 base_train=base_test=None;records=[];rows=[]
 for code,name in MODELS.items():
  train=pd.read_csv(directory/f'train_ids_{code}.csv');test=pd.read_csv(directory/f'test_ids_{code}.csv');pred=pd.read_csv(directory/f'predictions_{code}.csv');metric=pd.read_csv(directory/f'metrics_{code}.csv')
  tr,trhash=membership(train,18000,f'train_ids_{code}.csv');te,tehash=membership(test,12000,f'test_ids_{code}.csv');pr,prhash=membership(pred,12000,f'predictions_{code}.csv')
  if set(tr)&set(te):raise ValueError('Train/test overlap: '+code)
  if pr!=te:raise ValueError('Prediction ID/label coverage differs from full test: '+code)
  if base_train is None:base_train,base_test=tr,te
  if tr!=base_train or te!=base_test:raise ValueError('Common train/test ID+label membership mismatch: '+code)
  pred_column='prediction(PATIENT_TYPE)'
  if pred_column not in pred:
   matches=[c for c in pred if normalize(c)=='prediction_patient_type']
   if len(matches)!=1:raise ValueError(f'{code}: prediction column missing; actual{list(pred.columns)}')
   pred_column=matches[0]
  if pred[pred_column].isna().any() or not set(pred[pred_column]).issubset({POS,NEG}):raise ValueError('Invalid predicted labels: '+code)
  actual=pred[LABEL].eq(POS).to_numpy();guess=pred[pred_column].eq(POS).to_numpy()
  tp=int((actual&guess).sum());tn=int((~actual&~guess).sum());fp=int((~actual&guess).sum());fn=int((actual&~guess).sum())
  calc={'accuracy':(tp+tn)/12000,'precision_yes':tp/(tp+fp) if tp+fp else 0,'recall_yes':tp/(tp+fn) if tp+fn else 0,'f1_yes':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0}
  cols={normalize(c):c for c in metric}
  if 'criterion' not in cols or 'value' not in cols:raise ValueError('Unknown native Performance-to-Data schema: '+code)
  keys=metric[cols['criterion']].map(normalize)
  if keys.duplicated().any():raise ValueError('Duplicate native criterion: '+code)
  values=dict(zip(keys,pd.to_numeric(metric[cols['value']],errors='raise')))
  aliases={'accuracy':['accuracy'],'precision_yes':['precision'],'recall_yes':['recall','sensitivity'],'f1_yes':['f_measure','f1','f1_score'],'roc_auc':['auc'],'tn':['true_negative','true_negatives'],'fp':['false_positive','false_positives'],'fn':['false_negative','false_negatives'],'tp':['true_positive','true_positives']}
  out={'model':name,'engine':'Native AI Studio official batch full common holdout','positive_class':POS,'sample_rows':30000,'train_rows':18000,'test_rows':12000}
  for field,possible in aliases.items():
   found=[values[k] for k in possible if k in values]
   if not found or not math.isfinite(float(found[0])):raise ValueError(f'{code}: missing/nonfinite native criterion{field}')
   out[field]=float(found[0])
  for field,value in calc.items():
   if not 0<=out[field]<=1 or abs(out[field]-value)>1e-6:raise ValueError(f'{code}: native{field} does not reconcile to full prediction export')
  for field,value in {'tn':tn,'fp':fp,'fn':fn,'tp':tp}.items():
   if abs(out[field]-value)>1e-7:raise ValueError(f'{code}: native{field} count differs from full prediction export')
   out[field]=value
  conf=[c for c in pred if normalize(c)=='confidence_hospitalized']
  if len(conf)!=1:raise ValueError(f'{code}: Hospitalized confidence column missing')
  scores=pd.to_numeric(pred[conf[0]],errors='raise').to_numpy()
  if not np.isfinite(scores).all():raise ValueError('Nonfinite confidence: '+code)
  independent_auc=roc_auc_score(actual,scores)
  if not 0<=out['roc_auc']<=1:raise ValueError('Native AUC outside0–1: '+code)
  # Native AUC may use a different tie convention. Preserve it and expose an independent check.
  out['auc_recomputed_from_native_confidences']=independent_auc;out['auc_difference']=out['roc_auc']-independent_auc;out['average_precision_from_native_confidences']=average_precision_score(actual,scores)
  if abs(out['auc_difference'])>1e-4:raise ValueError(f'{code}: native AUC materially differs from saved confidence scores')
  records.append({'model':name,'train_rows':18000,'test_rows':12000,'train_id_label_sha256':trhash,'test_id_label_sha256':tehash,'prediction_id_label_sha256':prhash,'train_test_disjoint':True,'exact_common_train_and_test_pairs':True,'full_prediction_coverage':True,'test_positive_hospitalized':tp+fn,'test_negative_outpatient':tn+fp,'native_metrics_reconciled_to_predictions':True})
  rows.append(out)
 if hashes_before!={p.name:digest(p) for p in required}:raise RuntimeError('Exports changed during collection; wait for native writes to complete')
 checks=source_checks()
 source_membership=prepared_source_membership(base_train,base_test)
 verification={'verified':True,'all_nine_exports_complete':True,'all_nine_identical_train_ids_and_labels':True,'all_nine_identical_test_ids_and_labels':True,'all_nine_train_test_disjoint':True,'all_nine_predictions_exact_full_holdout_coverage':True,'full_test_rows':12000,'full_training_rows':18000,'modeling_sample_rows':30000,'positive_class':POS,'models':records,'source_ID_exclusion_checks':checks,'native_source_repository_hashes_unchanged':True,'actual_export_sha256':hashes_before,'actual_export_mtime_utc':{p.name:datetime.datetime.fromtimestamp(p.stat().st_mtime,datetime.timezone.utc).isoformat() for p in required},'required_native_run_start_epoch':not_before,'all_exports_newer_than_run_start':not_before is not None,'robust_seven_batch_results_used_for_comparison':False}
 verification['execution_provenance']={'mode':'official installed AI Studio batch runner','launcher':'D:/AI Studio 2026.1.1/scripts/ai-studio-batch.bat','entrypoint':'com.rapidminer.launcher.CommandLineLauncher','engine_version':'12.1.1 / AI Studio 2026.1.1','log':'docs/execution/native-common-batch.log','gui_run_or_gui_screenshot_claim':False,'original_nine_GUI_AutoModel_default_results_are_separate':True}
 verification['prepared_source_membership']=source_membership
 verification['driver_sha256']=digest(R/'MiniProject2_Common_Test_9Models.rmp')
 verification['collector_sha256']=digest(Path(__file__))
 (directory/'common_exports_validation.json').write_text(json.dumps(verification,indent=2),encoding='utf8')
 pd.DataFrame(rows).to_csv(directory/'Native_Common_Test_Model_Comparison.csv',index=False)
 return verification,pd.DataFrame(rows)
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--run-start',help='ISO local Asia/Bangkok time, for example2026-10-11T03:40:32');args=parser.parse_args()
 cutoff=datetime.datetime.fromisoformat(args.run_start).replace(tzinfo=ZoneInfo('Asia/Bangkok')).timestamp() if args.run_start else None
 verification,table=collect(not_before=cutoff);print('VERIFIED common full holdout for all9models');print(table.to_string(index=False))
