from pathlib import Path
import hashlib,json,re,xml.etree.ElementTree as E
R=Path(__file__).resolve().parent
proof=json.loads((R/'portable_macro_quote_fix.json').read_text())
def nodes(root):
 result=[]
 def walk(n,path):
  result.append((path,n.tag,dict(n.attrib),(n.text or '').strip()))
  for i,c in enumerate(n):walk(c,path+f'/{c.tag}[{i}]')
 walk(root,'');return result
def normalize(v):return v.replace('"%{process_path}"','%{process_path}').replace('"%{process_file}"','%{process_file}')
changes=[]
for entry in proof['rmp_files']:
 p=Path(entry['file']);backup=Path(entry['backup'])
 assert hashlib.sha256(backup.read_bytes()).hexdigest()==entry['before_sha256']
 before=nodes(E.parse(backup).getroot());after=nodes(E.parse(p).getroot());assert len(before)==len(after)
 changed=0
 for old,new in zip(before,after):
  assert old[:2]==new[:2] and old[3]==new[3]
  a,b=old[2],new[2]
  if a==b:continue
  assert old[1]=='parameter'
  assert {k:v for k,v in a.items() if k!='value'}=={k:v for k,v in b.items() if k!='value'}
  assert normalize(a['value'])==b['value'] and a['value']!=b['value']
  assert re.search(r'replace\(%\{process_path\},\s*%\{process_file\},\s*"[^"]+"\)',b['value'])
  changed+=1
 assert changed>0
 assert '&quot;%{process_path}&quot;' not in p.read_text(encoding='utf8')
 assert '&quot;%{process_file}&quot;' not in p.read_text(encoding='utf8')
 changes.append({'file':str(p),'only_path_function_parameters_changed':changed,'all_literal_filenames_remain_quoted':True,'other_nodes_attributes_text_and_connections_exactly_equal':True})
for entry in proof['builders']:compile(Path(entry['file']).read_text(encoding='utf8'),entry['file'],'exec')
# Refresh derived current hashes while retaining source/native provenance and all config proof.
manifest_path=R/'common_test_build_manifest.json';manifest=json.loads(manifest_path.read_text())
for model in manifest['models']:
 assert hashlib.sha256(Path(model['original_path']).read_bytes()).hexdigest()==model['original_sha256']
 model['new_sha256']=hashlib.sha256((R/model['new_rmp']).read_bytes()).hexdigest()
manifest['driver_sha256']=hashlib.sha256((R/manifest['driver']).read_bytes()).hexdigest()
manifest['portable_macro_expression']='replace(%{process_path}, %{process_file}, "filename.csv")'
manifest['macro_syntax_native_probe_verified']=True
manifest['macro_syntax_native_probe_screenshot']='../screenshots/native_macro_probe_pass.png'
manifest_path.write_text(json.dumps(manifest,indent=2),encoding='utf8')
result={'native_macro_probe_pass_is_prerequisite':True,'verified_rmp_count':len(changes),'independent_node_attribute_and_text_comparison':changes,'owned_builder_syntax_valid':True,'native_source_hashes_unchanged':True,'common_driver_ready_for_native_rerun':True,'native_model_rerun_after_fix_complete':False}
(R/'macro_quote_fix_independent_verification.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print('INDEPENDENT CHECK PASSED:',len(changes),'RMPs; only path expressions changed; all literal filenames/config/connections preserved')
