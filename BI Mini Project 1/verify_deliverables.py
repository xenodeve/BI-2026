from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET,shutil,csv
import pandas as pd
from pypdf import PdfReader
R=Path(__file__).resolve().parent
raw=pd.read_csv(R/'data/bank-full.csv',sep=';');clean=pd.read_csv(R/'bank-clean.csv',sep=';')
assert len(raw)==len(clean)==45211
assert 'duration' in raw and 'duration' not in clean
assert (clean.previously_contacted==raw.pdays.ne(-1).map({True:'yes',False:'no'})).all()
sha=hashlib.sha256((R/'data/bank-full.csv').read_bytes()).hexdigest()
assert hashlib.sha256((R/'bank-full.csv').read_bytes()).hexdigest()==sha
split=pd.read_csv(R/'split_assignment.csv');assert split.source_row.is_unique and set(split.split)=={'train','test'}
metrics=pd.read_csv(R/'model_comparison.csv');pred=pd.read_csv(R/'reference_predictions.csv')
assert len(metrics)==5 and pred.source_row.is_unique
for row in metrics.itertuples():
 assert row.tp+row.fp+row.tn+row.fn==row.test_rows==len(pred)
 assert abs(row.accuracy-(row.tp+row.tn)/row.test_rows)<1e-8
 assert abs(row.precision_yes-row.tp/(row.tp+row.fp))<1e-8
 assert abs(row.recall_yes-row.tp/(row.tp+row.fn))<1e-8
 assert abs(row.f1_yes-2*row.tp/(2*row.tp+row.fp+row.fn))<1e-8
tree=ET.parse(R/'MiniProject1.rmp');reader=next(x for x in tree.findall('.//operator') if x.attrib.get('class')=='read_csv')
assert reader.find("parameter[@key='csv_file']").attrib['value']=='%{dataset_path}'
assert len(tree.findall(".//operator[@class='performance_binominal_classification']"))==5
assert all(x.find("parameter[@key='positive_class']").attrib['value']=='yes' for x in tree.findall(".//operator[@class='performance_binominal_classification']"))
portability=R/'portability-check';portability.mkdir(exist_ok=True)
for f in ['MiniProject1.rmp','bank-full.csv']:shutil.copy2(R/f,portability/f)
process_path=str(portability/'MiniProject1.rmp');process_file=Path(process_path).name
resolved=Path(process_path.replace(process_file,'bank-full.csv'))
assert resolved.is_file() and hashlib.sha256(resolved.read_bytes()).hexdigest()==sha
pdf=PdfReader(R/'MiniProject1_Report.pdf');text='\n'.join(p.extract_text() for p in pdf.pages)
assert all(x in text for x in ['Business Understanding','Data Understanding','Data Preparation','Modeling','Evaluation','Deployment'])
assert '0.4421' in text and '0.4585' in text and 'Python' in text
native=json.loads((R/'native_metrics_provenance.json').read_text()) if (R/'native_metrics_provenance.json').exists() else {}
portable_file=R.parent/'docs/execution/native-portability-verification.json'
portable=json.loads(portable_file.read_text()) if portable_file.exists() else {}
result={'data_rows':45211,'original_hash_matches_copy':True,'clean_has_no_duration':True,'derived_feature_verified':True,'shared_reference_split_assignments_unique':True,'reference_metric_values_reconcile_to_confusion_counts':True,'rmp_xml_parses':True,'all5_positive_yes':True,'offline_path_resolution_after_copy':True,'native_portability_batch_run':bool(portable.get('all_three_actual_native_relocations_pass')),'pdf_pages':len(pdf.pages),'native_turboprep_GUI':False,'native_ai_studio_engine_batch_run':bool(native.get('process_finished_successfully')),'native_GUI_run':False}
(R/'deliverable_verification.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps(result,indent=2))
