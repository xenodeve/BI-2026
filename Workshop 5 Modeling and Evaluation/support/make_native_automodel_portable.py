"""Necessary source binding translation only; native saved processes remain untouched."""
from pathlib import Path
import json,hashlib,shutil,copy,xml.etree.ElementTree as E,zipfile,datetime
W=Path(__file__).resolve().parents[1];ROOT=W.parent;N=ROOT/'Native_AI_Repository/Workshop5_AutoModel_20261011';P=W/'Native_AutoModel_Portable'
MODELS={'NB':'Naive Bayes','LR':'Logistic Regression','DT':'Decision Tree','RF':'Random Forest','GBT':'Gradient Boosted Trees'}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1048576),b''):h.update(c)
 return h.hexdigest()
def sig(e):return(e.tag,tuple(sorted(e.attrib.items())),(e.text or '').strip(),tuple(sig(c) for c in e))
source=W/'WS5_AutoModel_Heart_Native_Prepared.csv';assert sha(source)=='fafcc2ff71daf147d0ab3968887dd74330c645e3f6a2341c5a217e52b99658af'
old={p.name:sha(p) for p in W.iterdir() if p.is_file()}
originals={code:N/name/'process.rmp' for code,name in MODELS.items()};native_hashes={code:sha(p) for code,p in originals.items()}
P.mkdir(exist_ok=True);B=P/'backups';B.mkdir(exist_ok=True)
target_source=P/source.name
if target_source.exists():assert sha(target_source)==sha(source)
else:shutil.copy2(source,target_source)
viewer=E.parse(W/'Workshop5_AutoModel_Data_Viewer.rmp')
reader_template=viewer.find(".//operator[@class='read_csv']")
records=[]
for code,name in MODELS.items():
 original=originals[code];tree=E.parse(original);root=tree.getroot();before=copy.deepcopy(root)
 retrieves=root.findall(".//operator[@class='retrieve']");assert len(retrieves)==1
 retrieve=retrieves[0];assert retrieve.get('name')=='Retrieve Data'
 parent=next(p for p in root.iter() if retrieve in list(p));index=list(parent).index(retrieve)
 binding=retrieve.find("parameter[@key='repository_entry']").get('value')
 assert binding=='../Read Actual WS4 Native Prepared Data Temp 21436'
 assert len(root.findall(".//parameter[@key='repository_entry']"))==1
 backup=B/f'WS5_AutoModel_{code}_original_native.rmp'
 if backup.exists():assert sha(backup)==sha(original)
 else:shutil.copy2(original,backup)
 replacement=E.Element('operator',dict(retrieve.attrib));replacement.set('class','read_csv')
 for child in reader_template:replacement.append(copy.deepcopy(child))
 replacement.find("parameter[@key='csv_file']").set('value','%{portable_source}')
 macro=E.Element('operator',activated='true',attrib={'class':'generate_macro','compatibility':'12.1.001','expanded':'true','name':'Portable Native Source Path','height':'82','width':'90','x':'45','y':'170'})
 functions=E.SubElement(macro,'list',key='function_descriptions')
 E.SubElement(functions,'parameter',key='portable_source',value='replace(%{process_path}, %{process_file}, "WS5_AutoModel_Heart_Native_Prepared.csv")')
 parent.remove(retrieve);parent.insert(index,macro);parent.insert(index+1,replacement)
 # Reversal proves every native node/list/parameter/connection except the initial
 # source binding is unchanged, including native14 inputs, caps, seeds, splits.
 inverse=copy.deepcopy(root);im=inverse.find(".//operator[@name='Portable Native Source Path']");ir=inverse.find(".//operator[@name='Retrieve Data']");ip=next(p for p in inverse.iter() if im in list(p));ii=list(ip).index(im)
 ip.remove(im);ip.remove(ir);ip.insert(ii,copy.deepcopy(retrieve));assert sig(inverse)==sig(before)
 assert not root.findall(".//parameter[@key='repository_entry']")
 out=P/f'WS5_AutoModel_{code}.rmp'
 if out.exists():
  stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');shutil.copy2(out,B/f'{out.stem}_before_{stamp}.rmp')
 E.indent(root,space='  ');E.ElementTree(root).write(out,encoding='UTF-8',xml_declaration=True)
 ops={o.get('name'):o for o in root.findall('.//operator')}
 dropped=ops['Remove Columns'].find("parameter[@key='regular_expression']").get('value')
 assert dropped==r'\QStroke\E|\QAlcoholDrinking\E|\QKidneyDisease\E|\QSkinCancer\E'
 assert ops['Define Target'].find("parameter[@key='attribute_name']").get('value')=='HeartDisease'
 assert ops['Define Positive Class'].find("parameter[@key='positive_value']").get('value')=='Yes'
 records.append({'model':name,'native_original_sha256':native_hashes[code],'portable_file':out.name,'portable_sha256':sha(out),'only_initial_repository_source_replaced':True,'all_native_parameters_seeds_caps_splits_14_input_selection_preserved':True,'external_repository_bindings_remaining':0,'default_initial_cap':ops['Sample'].find("parameter[@key='sample_size']").get('value')})
assert native_hashes=={code:sha(p) for code,p in originals.items()}
assert old=={p.name:sha(p) for p in W.iterdir() if p.is_file()},'Existing WS5 files changed'
proof={'file_translation_verified':True,'native_actual_GUI_AutoModel_saved_source':str(N),'source_dataset':source.name,'source_sha256':sha(source),'source_copy_exact':sha(source)==sha(target_source),'native_saved_RMPs_unchanged':True,'existing_WS5_baselines_reports_native_exports_unchanged':True,'target':'HeartDisease','positive_class':'Yes','native_selected_inputs':14,'native_dropped_inputs':['AlcoholDrinking','Stroke','KidneyDisease','SkinCancer'],'same_common_holdout_claim':False,'portable_native_execution_pending':True,'processes':records}
(W/'support/native_automodel_portability_check.json').write_text(json.dumps(proof,indent=2),encoding='utf8')
archive=P/'Workshop5_AutoModel_Submission.zip'
if archive.exists():shutil.copy2(archive,B/('Workshop5_AutoModel_Submission_before_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.zip'))
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for code in MODELS:z.write(P/f'WS5_AutoModel_{code}.rmp',f'WS5_AutoModel_{code}.rmp')
 z.write(target_source,target_source.name)
with zipfile.ZipFile(archive) as z:assert z.testzip() is None and len(z.namelist())==6
print(json.dumps({'zip':str(archive),'zip_bytes':archive.stat().st_size,'zip_sha256':sha(archive),'portable_process_folder':str(P),'dependency':'AI Studio2026.1.1 installed native AutoModel/model_simulator,H2O,concurrency operators; no repository data binding remains. Minimal native portable Run still pending root/batch verification.','native_input_count':14},indent=2))
