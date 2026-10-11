from pathlib import Path
import tempfile,json,hashlib,xml.etree.ElementTree as E
import pandas as pd
from collect_native_metrics import collect_native_metrics,MODELS
R=Path(__file__).resolve().parent
before=E.parse(R/'MiniProject1_before_native_exports.rmp');after=E.parse(R/'MiniProject1.rmp')
oldops={o.attrib['name']:o for o in before.findall('.//operator')};newops={o.attrib['name']:o for o in after.findall('.//operator')}
def signature(e):return (e.tag,sorted(e.attrib.items()),(e.text or '').strip(),[signature(c) for c in e])
for name,old in oldops.items():
 if name=='Root':continue
 if name=='Portable Dataset Path':
  oldentry=old.find("list[@key='function_descriptions']/parameter[@key='dataset_path']")
  newentry=newops[name].find("list[@key='function_descriptions']/parameter[@key='dataset_path']")
  expected=dict(oldentry.attrib)
  expected['value']=expected['value'].replace('"%{process_path}"','%{process_path}').replace('"%{process_file}"','%{process_file}')
  assert expected==newentry.attrib
 elif name=='Shared Stratified Split 70 30':
  import copy
  expected=copy.deepcopy(old);expected.find("list[@key='partitions']").tag='enumeration'
  assert signature(expected)==signature(newops[name]),name
 else:assert signature(old)==signature(newops[name]),name
newconnects={tuple(sorted(c.attrib.items())) for c in after.findall('.//connect')}
for c in before.findall('.//connect'):
 if c.attrib.get('from_port')=='performance' and c.attrib.get('to_port','').startswith('result '):continue
 assert tuple(sorted(c.attrib.items())) in newconnects,c.attrib
assert len(after.findall(".//operator[@class='performance_to_data']"))==5
assert len(after.findall(".//operator[@class='write_csv']"))==5
for i,code in enumerate(MODELS,1):
 writer=newops['Export Native '+code]
 assert writer.find("parameter[@key='csv_file']").attrib['value']==f'%{{export_{code}}}'
 assert writer.find("parameter[@key='append_to_file']").attrib['value']=='false'
 assert any(c.attrib=={'from_op':'Performance to Data '+code,'from_port':'performance vector','to_port':f'result {i}'} for c in after.findall('.//connect'))
 assert any(c.attrib=={'from_op':'Export Native '+code,'from_port':'through','to_port':f'result {15+i}'} for c in after.findall('.//connect'))
checks=[]
existing_exports={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in R.glob('native_*.csv')}
# Small synthetic fixture only, isolated from actual project exports. Deleted after tests.
with tempfile.TemporaryDirectory(prefix='.native-export-fixture-',dir=R) as tmp:
 T=Path(tmp).resolve();assert R.resolve() in T.parents
 try:collect_native_metrics(T,write_output=False)
 except FileNotFoundError:checks.append('missing_exports_rejected')
 else:raise AssertionError('Missing exports accepted')
 values={'accuracy':.8,'precision':2/3,'recall':2/3,'f_measure':2/3,'AUC':.9,'true_negative':4,'false_positive':2,'false_negative':2,'true_positive':4}
 fixture=pd.DataFrame({'Criterion':list(values),'Value':list(values.values()),'Standard Deviation':0,'Variance':0})
 # TN4+TP4 / total12 gives accuracy2/3; make fixture internally consistent.
 fixture.loc[fixture.Criterion=='accuracy','Value']=2/3
 for code in MODELS:fixture.to_csv(T/f'native_{code}.csv',index=False)
 result=collect_native_metrics(T,write_output=False);assert len(result)==5 and result.test_rows.eq(12).all();assert not (T/'native_model_comparison.csv').exists();checks.append('valid_fixture_maps_without_output_write')
 fixture[fixture.Criterion!='AUC'].to_csv(T/'native_NB.csv',index=False)
 try:collect_native_metrics(T,write_output=False)
 except ValueError:checks.append('missing_criterion_rejected')
 else:raise AssertionError('Missing AUC accepted')
 bad=fixture.copy();bad.loc[bad.Criterion=='precision','Value']=float('nan');bad.to_csv(T/'native_NB.csv',index=False)
 try:collect_native_metrics(T,write_output=False)
 except ValueError:checks.append('nonfinite_metric_rejected')
 else:raise AssertionError('NaN accepted')
 bad=fixture.copy();bad.loc[bad.Criterion=='f_measure','Value']=.2;bad.to_csv(T/'native_NB.csv',index=False)
 try:collect_native_metrics(T,write_output=False)
 except ValueError:checks.append('confusion_inconsistent_metric_rejected')
 else:raise AssertionError('Inconsistent F1 accepted')
 fixture.to_csv(T/'native_NB.csv',index=False);pd.concat([fixture,fixture.iloc[:1]]).to_csv(T/'native_LR.csv',index=False)
 try:collect_native_metrics(T,write_output=False)
 except ValueError:checks.append('duplicate_criterion_rejected')
 else:raise AssertionError('Duplicate criterion accepted')
assert existing_exports=={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in R.glob('native_*.csv')}
native_proof=json.loads((R/'native_metrics_provenance.json').read_text()) if (R/'native_metrics_provenance.json').exists() else {}
result={'backup_file':'MiniProject1_before_native_exports.rmp','backup_sha256':hashlib.sha256((R/'MiniProject1_before_native_exports.rmp').read_bytes()).hexdigest(),'updated_process_sha256':hashlib.sha256((R/'MiniProject1.rmp').read_bytes()).hexdigest(),'original_model_operator_configs_preserved':True,'original_nonperformance_connections_preserved':True,'native_export_operator_count':5,'result1_to15_preserved_with_performance_passthrough':True,'result16_to20_exported_tables':True,'portable_macros_verified':True,'split_container_schema_corrected_to_installed_enumeration':True,'split_ratios_and_seed_unchanged':True,'collector_fixture_checks':checks,'fixture_only_no_real_native_outputs_created':True,'native_engine_batch_run_verified':bool(native_proof.get('process_finished_successfully')),'native_GUI_run_verified':False}
(R/'native_export_verification.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result,indent=2))
