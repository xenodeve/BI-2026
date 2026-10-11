from pathlib import Path
import xml.etree.ElementTree as ET,json,zipfile
R=Path(__file__).resolve().parent
V='12.1.001'
doc=ET.Element('process',version=V)
context=ET.SubElement(doc,'context');[ET.SubElement(context,k) for k in ['input','output','macros']]
root=ET.SubElement(doc,'operator',activated='true',attrib={'class':'process','compatibility':V,'expanded':'true','name':'Root'})
ET.SubElement(root,'parameter',key='random_seed',value='2026');ET.SubElement(root,'parameter',key='encoding',value='UTF-8')
p=ET.SubElement(root,'process',expanded='true')
def op(cls,name,x,y,params=None,lists=None,compat=V):
 e=ET.SubElement(p,'operator',activated='true',attrib={'class':cls,'compatibility':compat,'expanded':'true','height':'103','width':'90','name':name,'x':str(x),'y':str(y)})
 for k,v in (params or {}).items():ET.SubElement(e,'parameter',key=k,value=str(v))
 for k,vals in (lists or {}).items():
  l=ET.SubElement(e,'enumeration' if k=='partitions' else 'list',key=k)
  for key,value in vals:ET.SubElement(l,'parameter',key=str(key),value=str(value))
 return e
def connect(fo,fp,to,tp):
 a={'from_port':fp,'to_port':tp}
 if fo:a['from_op']=fo
 if to:a['to_op']=to
 ET.SubElement(p,'connect',a)
# Built-in process_path/process_file macros documented in installed Generate Macro manual.
export_codes=['NB','LR','DT','RF','GBT']
portable_macros=[('dataset_path','replace(%{process_path}, %{process_file}, "bank-full.csv")')]+[(f'export_{code}',f'replace(%{{process_path}}, %{{process_file}}, "native_{code}.csv")') for code in export_codes]
op('generate_macro','Portable Dataset Path',35,30,lists={'function_descriptions':portable_macros})
columns=['age','job','marital','education','default','balance','housing','loan','contact','day','month','duration','campaign','pdays','previous','poutcome','y']
numeric={'age','balance','day','duration','campaign','pdays','previous'}
metadata=[(i,f'{c}.true.'+('integer' if c in numeric else 'binominal' if c in {'default','housing','loan','y'} else 'polynominal')+'.attribute') for i,c in enumerate(columns)]
op('read_csv','Read Original bank-full.csv',35,170,{'csv_file':'%{dataset_path}','column_separators':';','trim_lines':'true','use_quotes':'true','quotes_character':'"','first_row_as_names':'true','parse_numbers':'true','decimal_character':'.','encoding':'UTF-8','read_not_matching_values_as_missings':'false'}, {'data_set_meta_data_information':metadata})
op('set_role','Target y',165,170,{'attribute_name':'y','target_role':'label'})
op('select_attributes','Exclude Post-call Duration',295,170,{'attribute_filter_type':'single','attribute':'duration','invert_selection':'true','include_special_attributes':'true'})
op('generate_attributes','Prior Contact Flag',425,170,{'keep_all':'true'}, {'function_descriptions':[('previously_contacted','if(pdays == -1, "no", "yes")')]})
op('split_data','Shared Stratified Split 70 30',555,170,{'sampling_type':'stratified sampling','use_local_random_seed':'true','local_random_seed':'2026'},{'partitions':[('ratio','.7'),('ratio','.3')]})
op('nominal_to_numerical','Fit Training Encoding',685,85,{'attribute_filter_type':'all','include_special_attributes':'false','coding_type':'dummy coding','use_comparison_groups':'false','use_underscore_in_name':'true','return_preprocessing_model':'true'})
op('normalize','Fit Training Scaling',815,85,{'attribute_filter_type':'all','include_special_attributes':'false','method':'Z-transformation','return_preprocessing_model':'true'})
op('apply_model','Apply Training Encoding to Test',685,280,{'create_view':'false'})
op('apply_model','Apply Training Scaling to Test',815,280,{'create_view':'false'})
op('multiply','Same Training for Five Models',945,85)
op('multiply','Same Test for Five Models',945,280)
connect('Read Original bank-full.csv','output','Target y','example set input');connect('Target y','example set output','Exclude Post-call Duration','example set input');connect('Exclude Post-call Duration','example set output','Prior Contact Flag','example set input');connect('Prior Contact Flag','example set output','Shared Stratified Split 70 30','example set')
connect('Shared Stratified Split 70 30','partition 1','Fit Training Encoding','example set input');connect('Shared Stratified Split 70 30','partition 2','Apply Training Encoding to Test','unlabelled data')
connect('Fit Training Encoding','example set output','Fit Training Scaling','example set input');connect('Fit Training Encoding','preprocessing model','Apply Training Encoding to Test','model')
connect('Apply Training Encoding to Test','labelled data','Apply Training Scaling to Test','unlabelled data');connect('Fit Training Scaling','preprocessing model','Apply Training Scaling to Test','model')
connect('Fit Training Scaling','example set output','Same Training for Five Models','input');connect('Apply Training Scaling to Test','labelled data','Same Test for Five Models','input')
models=[
 ('naive_bayes','Naive Bayes',{'laplace_correction':'true'},V),
 ('h2o:logistic_regression','Logistic Regression',{'reproducible':'true','maximum_number_of_threads':'2','standardize':'false','max_iterations':'100','remove_collinear_columns':'true','compute_p-values':'false'},'11.0.003'),
 ('concurrency:parallel_decision_tree','Decision Tree',{'criterion':'gain_ratio','maximal_depth':'8','minimal_leaf_size':'20','apply_pruning':'true','apply_prepruning':'true'},V),
 ('concurrency:parallel_random_forest','Random Forest',{'number_of_trees':'100','maximal_depth':'12','minimal_leaf_size':'5','use_local_random_seed':'true','local_random_seed':'2026','enable_parallel_execution':'true'},V),
 ('h2o:gradient_boosted_trees','Gradient Boosted Trees',{'number_of_trees':'100','maximal_depth':'3','learning_rate':'0.1','distribution':'bernoulli','reproducible':'true','maximum_number_of_threads':'2','use_local_random_seed':'true','local_random_seed':'2026','early_stopping':'false'},'11.0.003'),
]
for i,(cls,name,params,compat) in enumerate(models,1):
 y=30+(i-1)*155
 op(cls,name,1090,y,params,compat=compat);apply='Score '+name;perf='Performance '+name
 op('apply_model',apply,1230,y,{'create_view':'false'})
 op('performance_binominal_classification',perf,1370,y,{'main_criterion':'f_measure','accuracy':'true','precision':'true','recall':'true','f_measure':'true','AUC':'true','false_positive':'true','false_negative':'true','true_positive':'true','true_negative':'true','manually_set_positive_class':'true','positive_class':'yes','use_example_weights':'false'})
 code=export_codes[i-1];ptd='Performance to Data '+code;writer='Export Native '+code
 op('performance_to_data',ptd,1510,y)
 op('write_csv',writer,1650,y,{'csv_file':f'%{{export_{code}}}','column_separator':',','write_attribute_names':'true','quote_nominal_values':'true','append_to_file':'false','encoding':'UTF-8'})
 connect('Same Training for Five Models',f'output {i}',name,'training set');connect('Same Test for Five Models',f'output {i}',apply,'unlabelled data');connect(name,'model',apply,'model');connect(apply,'labelled data',perf,'labelled data');connect(perf,'performance',ptd,'performance vector');connect(ptd,'performance vector',None,f'result {i}');connect(ptd,'example set',writer,'input');connect(writer,'through',None,f'result {i+15}');connect(perf,'example set',None,f'result {i+5}');connect(apply,'model',None,f'result {i+10}')
ET.SubElement(p,'description',align='left',color='yellow',colored='false',height='90',width='780',x='40',y='800').text='Bank Marketing: pre-call prediction, positive yes. One shared split; encoding/scaling fitted on training only and applied to test. Python reference results are separate. Open this file as a local .rmp and keep original bank-full.csv beside it. Verify native Run and relocation before submission.'
for i in range(1,22):ET.SubElement(p,'portSpacing',port=f'sink_result {i}',spacing='0')
ET.SubElement(p,'portSpacing',port='source_input 1',spacing='0')
ET.indent(doc,space='  ');ET.ElementTree(doc).write(R/'MiniProject1.rmp',encoding='UTF-8',xml_declaration=True)
# Ground every operator ID in installed operator registry XML.
registries={}
for f in (R/'operator-evidence').glob('*Operators*.xml'):
 try:
  t=ET.parse(f).getroot();prefix=t.attrib.get('name','')
  for e in t.findall('.//operator'):
   key=e.findtext('key')
   if key:registries[(prefix+':' if prefix and prefix not in ['core','rapidminer'] else '')+key]=str(f.name)
 except ET.ParseError:pass
classes={e.attrib['class'] for e in doc.findall('.//operator')}-{'process'}
missing=[k for k in classes if k not in registries and k.split(':')[-1] not in registries]
if missing:raise ValueError('Unverified operator IDs '+str(missing))
evidence={k:registries.get(k,registries.get(k.split(':')[-1])) for k in classes}
(R/'rmp_operator_evidence.json').write_text(json.dumps(evidence,indent=2),encoding='utf8')
names={e.attrib['name'] for e in p.findall('operator')}
for c in p.findall('connect'):
 assert not c.attrib.get('from_op') or c.attrib['from_op'] in names
 assert not c.attrib.get('to_op') or c.attrib['to_op'] in names
assert len([e for e in p.findall('operator') if e.attrib['class']=='performance_binominal_classification'])==5
print('RMP schema grounded in installed tutorials; operator IDs verified; native runtime pending')
print('Portable expression: replace(process_path, process_file, bank-full.csv); local-file open and relocation Run required')
