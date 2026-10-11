"""Create an independent read-only data viewer; preserve all existing WS5 outputs."""
from pathlib import Path
import json,hashlib,shutil,xml.etree.ElementTree as E,copy
import pandas as pd
W=Path(__file__).resolve().parents[1];ROOT=W.parent;SOURCE=ROOT/'Workshop 4 การจัดเตรียมข้อมูล (Data Preparation)/heart_2020_prepared_native.csv'
DATA=W/'WS5_AutoModel_Heart_Native_Prepared.csv';OUT=W/'Workshop5_AutoModel_Data_Viewer.rmp';S=W/'support'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1048576),b''):h.update(c)
 return h.hexdigest()
protected=[p for p in W.iterdir() if p.is_file() and p not in [DATA,OUT]]
before={p.name:sha(p) for p in protected};source_hash=sha(SOURCE)
assert source_hash=='fafcc2ff71daf147d0ab3968887dd74330c645e3f6a2341c5a217e52b99658af'
if DATA.exists():assert sha(DATA)==source_hash,'Existing new-viewer copy differs; no overwrite'
else:shutil.copy2(SOURCE,DATA)
d=pd.read_csv(DATA);assert d.shape==(319795,19)
numeric=['BMI','PhysicalHealth','MentalHealth','SleepTime']
assert list(d.select_dtypes(include='number'))==numeric
assert d.HeartDisease.value_counts().to_dict()=={'No':292422,'Yes':27373}
assert set(d.AnyUnhealthyDays)=={'Yes','No'} and not d.isna().any().any()
assert 'SplitSet' not in d and 'SourceRow' not in d
baseline=E.parse(W/'Workshop5_Modeling_Evaluation.rmp')
oldreader=next(o for o in baseline.findall('.//operator') if o.get('class')=='read_csv')
meta=copy.deepcopy(oldreader.find("list[@key='data_set_meta_data_information']"))
meta.remove(next(p for p in meta if p.get('value').startswith('SplitSet.')))
assert len(meta)==19
for i,p in enumerate(meta):
 p.set('key',str(i));expected=d.columns[i]+'.true.'+('binominal' if d.columns[i]=='HeartDisease' else 'real' if d.columns[i] in numeric else 'polynominal')+'.attribute'
 assert p.get('value')==expected,(i,p.attrib,expected)
V='12.1.001';doc=E.Element('process',version=V);context=E.SubElement(doc,'context');[E.SubElement(context,k) for k in ['input','output','macros']]
root=E.SubElement(doc,'operator',activated='true',attrib={'class':'process','compatibility':V,'expanded':'true','name':'WS5 AutoModel Data Viewer'})
E.SubElement(root,'parameter',key='random_seed',value='2001');E.SubElement(root,'parameter',key='encoding',value='UTF-8')
p=E.SubElement(root,'process',expanded='true')
macro=E.SubElement(p,'operator',activated='true',attrib={'class':'generate_macro','compatibility':V,'expanded':'true','name':'Portable Source Path','height':'82','width':'90','x':'45','y':'170'})
functions=E.SubElement(macro,'list',key='function_descriptions');E.SubElement(functions,'parameter',key='viewer_source',value='replace(%{process_path}, %{process_file}, "WS5_AutoModel_Heart_Native_Prepared.csv")')
reader=E.SubElement(p,'operator',activated='true',attrib={'class':'read_csv','compatibility':V,'expanded':'true','name':'Read Actual WS4 Native Prepared Data','height':'82','width':'90','x':'179','y':'34'})
params={'csv_file':'%{viewer_source}','column_separators':',','trim_lines':'true','use_quotes':'true','quotes_character':'"','first_row_as_names':'true','parse_numbers':'true','decimal_character':'.','encoding':'UTF-8','read_all_values_as_polynominal':'false','read_not_matching_values_as_missings':'false'}
for k,v in params.items():E.SubElement(reader,'parameter',key=k,value=v)
reader.append(meta)
E.SubElement(p,'connect',from_op=reader.get('name'),from_port='output',to_port='result 1')
E.SubElement(p,'portSpacing',port='source_input 1',spacing='0');E.SubElement(p,'portSpacing',port='sink_result 1',spacing='0');E.SubElement(p,'portSpacing',port='sink_result 2',spacing='0')
E.SubElement(p,'description',align='left',color='yellow',colored='false',height='130',width='650',x='35',y='310').text='Read-only viewer for actual WS4 native preparation:319795 rows,19 regular attributes,4 numeric columns. No target role assigned, no transformations, sampling, model training or writes. Use Results Auto Model:Predict, HeartDisease target, positive Yes,18 inputs. Native Auto Model workflow/results will be recorded separately from prior direct-learner benchmarks.'
assert [o.get('class') for o in doc.findall('.//operator')]==['process','generate_macro','read_csv']
assert all(x.get('value').endswith('.attribute') for x in meta)
assert not OUT.exists(),'Viewer already exists; do not overwrite'
E.indent(doc,space='  ');E.ElementTree(doc).write(OUT,encoding='UTF-8',xml_declaration=True)
assert source_hash==sha(SOURCE)==sha(DATA)
assert before=={p.name:sha(p) for p in protected},'Existing WS5 artifacts changed'
proof={'verified_file_only':True,'viewer':str(OUT),'viewer_sha256':sha(OUT),'source_actual_WS4_native_prepared':str(SOURCE),'new_data_copy':str(DATA),'source_and_copy_sha256':source_hash,'source_copy_byte_identical':True,'rows':319795,'columns':19,'all_19_roles_regular':True,'HeartDisease_type':'binominal','HeartDisease_counts':d.HeartDisease.value_counts().to_dict(),'numeric_columns':numeric,'numeric_column_count':4,'AnyUnhealthyDays_type':'polynominal','AnyUnhealthyDays_values':sorted(d.AnyUnhealthyDays.unique()),'metadata_entries':[x.get('value') for x in meta],'installed_ReadCSV_schema_grounding':'Existing actual-native-validated WS4/WS5 reader data_set_meta_data_information and read_csv tutorial; column.true.ontology.attribute entries. generate_macro/read_csv/ReadCSV output port previously verified in actual installed12.1.1 engine.','no_role_assignment_or_selection_or_transform_or_sampling_or_model_or_writer':True,'existing_WS5_baselines_reports_comparisons_native_exports_unchanged':True,'native_viewer_Run_and_AutoModel_GUI_not_claimed':True}
(S/'automodel_viewer_verification.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
print(json.dumps({k:proof[k] for k in ['viewer','new_data_copy','rows','columns','numeric_columns','source_copy_byte_identical','existing_WS5_baselines_reports_comparisons_native_exports_unchanged']},indent=2))
