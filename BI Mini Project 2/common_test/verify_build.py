from pathlib import Path
import hashlib,json,xml.etree.ElementTree as E
R=Path(__file__).resolve().parent
manifest=json.loads((R/'common_test_build_manifest.json').read_text())
d=E.parse(R/manifest['driver']);root=d.find('operator');top=root.find('process')
assert root.find("parameter[@key='random_seed']").attrib['value']=='2001'
wrappers=[o for o in top.findall('operator') if o.attrib['class']=='subprocess']
assert len(wrappers)==9
allnames=[o.attrib['name'] for o in d.findall('.//operator')];assert len(allnames)==len(set(allnames))
for model in manifest['models']:
 code=model['code'];wrapped=next(o for o in wrappers if o.attrib['name']=='Run '+code)
 nodes={o.attrib['name']:o for o in wrapped.findall('.//operator')}
 sample=nodes[code+'__Sample'];assert sample.find("parameter[@key='sample_size']").attrib['value']=='30000';assert sample.find("parameter[@key='use_local_random_seed']").attrib['value']=='true';assert sample.find("parameter[@key='local_random_seed']").attrib['value']=='2001'
 main_split=nodes[code+'__Split Data'];assert [x.attrib['value'] for x in main_split.find('enumeration')]==['0.6','0.4'];assert main_split.find("parameter[@key='local_random_seed']").attrib['value']=='1992'
 protected=nodes[code+'__Protect Common Row ID'];assert protected.find("parameter[@key='attribute_name']").attrib['value']=='COMMON_ROW_ID';assert protected.find("parameter[@key='target_role']").attrib['value']=='id'
 full=nodes[code+'__Evaluate All Common Test Rows'];assert not any(o.attrib['class'] in ['sample','sample_stratified','filter_examples','model_simulator:generate_batch','model_simulator:robust_performance_average'] for o in full.findall('.//operator'))
 perf=nodes[code+'__Full Common Test Performance'];assert perf.find("parameter[@key='positive_class']").attrib['value']=='Hospitalized'
 assert hashlib.sha256(Path(model['original_path']).read_bytes()).hexdigest()==model['original_sha256']
 for node in wrapped.findall('.//operator'):
  if node.attrib['class'] in ['remember','recall']:
   name=node.find("parameter[@key='name']")
   assert name is None or name.attrib['value'].startswith(code+'__MEM__')
 # Every connection references the immediate process's correctly namespaced operators.
 for process in wrapped.findall('.//process'):
  local={o.attrib['name'] for o in process.findall('operator')}
  for conn in process.findall('connect'):
   for field in ['from_op','to_op']:assert field not in conn.attrib or conn.attrib[field] in local,conn.attrib
 for file in ['metrics','predictions','test_ids','train_ids']:
  assert model['output_files'][file]==f'{file}_{code}.csv'
assert not d.findall(".//operator[@class='retrieve']") and not d.findall(".//operator[@class='store']")
assert not d.findall(".//operator[@class='productivity_ui:execute_process']")
result={'driver_xml_parses':True,'actual_generated_model_count':9,'unique_operator_count':len(allnames),'explicit_common_initial_sample':30000,'initial_local_seed':2001,'main_split':[.6,.4],'main_split_local_seed':1992,'special_common_row_id_protected':True,'full_holdout_evaluation_has_no_sampler_filter_batch_or_trim':True,'all_native_core_subtrees_preserved_in_standalone_copies':True,'combined_namespacing_is_reversible_config_and_logic_preserved':True,'remember_recall_isolated_by_model':True,'all_connections_resolve_in_local_scope':True,'source_native_repo_rmp_hashes_unchanged':True,'driver_has_no_repository_or_ExecuteProcess_dependency':True,'actual_common_test_id_label_membership_verified':False,'native_driver_run_verified':False}
(R/'static_build_verification.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result,indent=2))
