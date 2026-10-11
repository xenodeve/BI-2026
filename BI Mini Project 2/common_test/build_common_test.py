"""Reevaluate actual generated AutoModel templates on a reproducible common holdout."""
from pathlib import Path
import copy,csv,hashlib,json,xml.etree.ElementTree as E,zipfile
R=Path(__file__).resolve().parent
SOURCE=R.parents[1]/'Native_AI_Repository/MiniProject2_AutoModel_9Models'
PREPARED=R.parent/'COVID_Prepared_Native.csv'
MODELS={'NB':'Naive Bayes','GLM':'Generalized Linear Model','LR':'Logistic Regression','FLM':'Fast Large Margin','DL':'Deep Learning','DT':'Decision Tree','RF':'Random Forest','GBT':'Gradient Boosted Trees','SVM':'Support Vector Machine'}
V='12.1.001'
with PREPARED.open(encoding='utf-8-sig',newline='') as f:columns=next(csv.reader(f))
assert len(columns)==16 and 'AGE' in columns and 'PATIENT_TYPE' in columns
source_hashes={code:hashlib.sha256((SOURCE/name/'process.rmp').read_bytes()).hexdigest() for code,name in MODELS.items()}
def op(cls,name,x,y,params=None,lists=None):
 e=E.Element('operator',activated='true',attrib={'class':cls,'compatibility':V,'expanded':'true','height':'103','width':'90','name':name,'x':str(x),'y':str(y)})
 for k,v in (params or {}).items():E.SubElement(e,'parameter',key=k,value=str(v))
 for k,vals in (lists or {}).items():
  l=E.SubElement(e,'list',key=k)
  for a,b in vals:E.SubElement(l,'parameter',key=str(a),value=str(b))
 return e
def con(p,a,ap,b,bp):
 attrs={'from_port':ap,'to_port':bp}
 if a:attrs['from_op']=a
 if b:attrs['to_op']=b
 E.SubElement(p,'connect',attrs)
def insert_before_connections(p,new):
 at=next((i for i,c in enumerate(p) if c.tag!='operator'),len(p));p.insert(at,new)
def param(o,k,v):
 e=o.find(f"parameter[@key='{k}']")
 if e is None:E.SubElement(o,'parameter',key=k,value=str(v))
 else:e.attrib['value']=str(v)
def signature(n):return (n.tag,tuple(sorted(n.attrib.items())),(n.text or '').strip(),tuple(signature(c) for c in n))
def find_direct(p,name):return next(o for o in p.findall('operator') if o.attrib['name']==name)
manifest=[]
for code,name in MODELS.items():
 original=E.parse(SOURCE/name/'process.rmp');d=copy.deepcopy(original.getroot());root=d.find('operator');top=root.find('process')
 assert root.find("parameter[@key='random_seed']").attrib['value']=='2001'
 # Preserve every entire core training/encoding/evaluation subtree exactly.
 preserved_names=['Basic Feature Engineering','Handle Text Columns','Automatic Feature Engineering','Train Model','Transform Validation Data','Transform Scoring Data','Create Predictions and Explanations','Validate Model','Create Model Simulator','Create Production Model','Process Results']
 expected={n:signature(find_direct(top,n)) for n in preserved_names}
 oldcap=None
 load=find_direct(top,'Load and Process Data').find('process')
 retrieve=find_direct(load,'Retrieve Data');retrieve.attrib['class']='read_csv'
 for child in list(retrieve):retrieve.remove(child)
 for key,value in {'csv_file':'%{common_source}','column_separators':',','use_quotes':'true','quotes_character':'"','first_row_as_names':'true','trim_lines':'true','parse_numbers':'true','decimal_character':'.','encoding':'UTF-8','read_all_values_as_polynominal':'false','read_not_matching_values_as_missings':'false'}.items():E.SubElement(retrieve,'parameter',key=key,value=value)
 meta=E.SubElement(retrieve,'list',key='data_set_meta_data_information')
 for i,c in enumerate(columns):E.SubElement(meta,'parameter',key=str(i),value=f'{c}.true.'+('real' if c=='AGE' else 'polynominal')+'.attribute')
 paths=[('common_source','../COVID_Prepared_Native.csv')]+[(f'common_{kind}',f'{kind}_{code}.csv') for kind in ['metrics','predictions','test_ids','train_ids']]
 macro=op('generate_macro','Common Test Portable Paths',40,700,lists={'function_descriptions':[(k,f'replace(%{{process_path}}, %{{process_file}}, "{file}")') for k,file in paths]})
 load.insert(0,macro)
 sample=find_direct(load,'Sample');assert sample.attrib['class']=='sample_stratified'
 oldcap=sample.find("parameter[@key='sample_size']").attrib['value']
 param(sample,'sample_size','30000');param(sample,'use_local_random_seed','true');param(sample,'local_random_seed','2001')
 # ID is assigned after general preprocessing but BEFORE the label filter so the
 # empty scoring sidebranch carries the same special-ID schema as validation data.
 for conn in load.findall('connect'):
  if conn.attrib.get('from_op')=='Preprocessing' and conn.attrib.get('to_op')=='Filter Examples':load.remove(conn)
 index=list(load).index(find_direct(load,'Filter Examples'))
 new_id=[op('generate_id','Common Source Row ID',750,250,{'create_nominal_ids':'false','offset':'0'}),op('rename','Name Common Source Row ID',890,250,{'old_name':'id','new_name':'COMMON_ROW_ID'}),op('set_role','Protect Common Row ID',1030,250,{'attribute_name':'COMMON_ROW_ID','target_role':'id'})]
 for j,o in enumerate(new_id):load.insert(index+j,o)
 con(load,'Preprocessing','out 1','Common Source Row ID','example set input');con(load,'Common Source Row ID','example set output','Name Common Source Row ID','example set input');con(load,'Name Common Source Row ID','example set output','Protect Common Row ID','example set input');con(load,'Protect Common Row ID','example set output','Filter Examples','example set input')
 # Keep the exact main60/40 local1992 splitter and export both raw memberships.
 splitp=find_direct(top,'Create Validation Set').find('process');split=find_direct(splitp,'Split Data')
 assert {x.attrib['key']:x.attrib['value'] for x in split.findall('parameter')}=={'sampling_type':'automatic','use_local_random_seed':'true','local_random_seed':'1992'}
 assert [x.attrib['value'] for x in split.find('enumeration')]==['0.6','0.4']
 for kind,partition,remember,outport,ypos in [('train_ids',1,'Remember Training Data','out 2',200),('test_ids',2,'Remember Validation Data','out 1',430)]:
  for conn in splitp.findall('connect'):
   if conn.attrib.get('from_op')=='Split Data' and conn.attrib.get('from_port')==f'partition {partition}' and conn.attrib.get('to_op')==remember:splitp.remove(conn)
  multiply='Preserve and Audit '+kind;select='Select '+kind;writer='Write '+kind
  insert_before_connections(splitp,op('multiply',multiply,380,ypos))
  insert_before_connections(splitp,op('select_attributes',select,530,ypos,{'attribute_filter_type':'regular_expression','regular_expression':'\\QCOMMON_ROW_ID\\E|\\QPATIENT_TYPE\\E','invert_selection':'false','include_special_attributes':'true'}))
  insert_before_connections(splitp,op('write_csv',writer,680,ypos,{'csv_file':f'%{{common_{kind}}}','column_separator':',','write_attribute_names':'true','quote_nominal_values':'true','append_to_file':'false','encoding':'UTF-8'}))
  con(splitp,'Split Data',f'partition {partition}',multiply,'input');con(splitp,multiply,'output 1',remember,'store');con(splitp,multiply,'output 2',select,'example set input');con(splitp,select,'example set output',writer,'input');con(splitp,writer,'through',None,outport)
 # Extra full-holdout Apply/Performance preserves the original robust7 evaluation unchanged.
 full=op('subprocess','Evaluate All Common Test Rows',1860,340);fullp=E.SubElement(full,'process',expanded='true')
 fullp.append(op('recall','Recall Common Trained Model',30,30,{'name':'Model','io_object':'Model','remove_from_store':'false'}))
 fullp.append(op('recall','Recall Complete Validation Data',30,190,{'name':'Validation Data','io_object':'ExampleSet','remove_from_store':'false'}))
 # Copy the actual generated Apply Model operator, including native application settings.
 original_apply=next(x for x in find_direct(top,'Validate Model').findall('.//operator') if x.attrib.get('name')=='Apply Model')
 apply=copy.deepcopy(original_apply);apply.attrib.update(name='Apply Model Full Common Test',x='200',y='30');fullp.append(apply)
 fullp.append(op('performance_binominal_classification','Full Common Test Performance',350,30,{'main_criterion':'f_measure','manually_set_positive_class':'true','positive_class':'Hospitalized','accuracy':'true','precision':'true','recall':'true','f_measure':'true','AUC':'true','false_positive':'true','false_negative':'true','true_positive':'true','true_negative':'true','use_example_weights':'false'}))
 fullp.append(op('performance_to_data','Full Performance to Data',500,30))
 fullp.append(op('write_csv','Write Full Metrics',650,30,{'csv_file':'%{common_metrics}','column_separator':',','write_attribute_names':'true','quote_nominal_values':'true','append_to_file':'false','encoding':'UTF-8'}))
 fullp.append(op('write_csv','Write Full Test Predictions',500,210,{'csv_file':'%{common_predictions}','column_separator':',','write_attribute_names':'true','quote_nominal_values':'true','append_to_file':'false','encoding':'UTF-8'}))
 con(fullp,'Recall Common Trained Model','result','Apply Model Full Common Test','model');con(fullp,'Recall Complete Validation Data','result','Apply Model Full Common Test','unlabelled data');con(fullp,'Apply Model Full Common Test','labelled data','Full Common Test Performance','labelled data');con(fullp,'Full Common Test Performance','performance','Full Performance to Data','performance vector');con(fullp,'Full Performance to Data','performance vector',None,'out 1');con(fullp,'Full Performance to Data','example set','Write Full Metrics','input');con(fullp,'Write Full Metrics','through',None,'out 3');con(fullp,'Full Common Test Performance','example set','Write Full Test Predictions','input');con(fullp,'Write Full Test Predictions','through',None,'out 2')
 # Must run before production-model phase consumes Validation Data, and before result recalls.
 at=list(top).index(find_direct(top,'Validate Model'));top.insert(at,full)
 # Expose common full metrics first; retain the original21 outputs in their original order afterward.
 for conn in top.findall('connect'):
  if 'to_op' not in conn.attrib and conn.attrib.get('to_port','').startswith('result '):conn.attrib['to_port']='result '+str(int(conn.attrib['to_port'].split()[-1])+4)
 con(top,'Evaluate All Common Test Rows','out 1',None,'result 1');con(top,'Evaluate All Common Test Rows','out 2',None,'result 2');con(top,'Create Validation Set','out 1',None,'result 3');con(top,'Create Validation Set','out 2',None,'result 4');con(top,'Evaluate All Common Test Rows','out 3',None,'result 26')
 for n,sig in expected.items():assert signature(find_direct(top,n))==sig,n
 # No repository retrieval/writer survives; generated auxiliary artifacts remain in memory only.
 assert not d.findall(".//operator[@class='retrieve']") and not d.findall(".//operator[@class='store']")
 E.indent(d,space='  ');file=R/f'model_{code}.rmp';E.ElementTree(d).write(file,encoding='UTF-8',xml_declaration=True)
 E.parse(file)
 manifest.append({'code':code,'model':name,'original_path':str(SOURCE/name/'process.rmp'),'original_sha256':source_hashes[code],'new_rmp':file.name,'new_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'original_initial_cap':oldcap,'common_initial_cap':30000,'initial_use_local_random_seed':True,'initial_local_seed':2001,'root_global_seed':2001,'main_split':[.6,.4],'main_split_local_seed':1992,'preserved_subtrees':preserved_names,'learner_feature_engineering_normalization_and_robust_evaluation_unchanged':True,'id_role':'COMMON_ROW_ID as special id after preprocessing/before sample','output_files':{k:f'{k}_{code}.csv' for k in ['metrics','predictions','test_ids','train_ids']},'native_run_verified':False})
 # Original templates are checked after every generated copy; never written.
 assert hashlib.sha256((SOURCE/name/'process.rmp').read_bytes()).hexdigest()==source_hashes[code]

# Single sequential driver embeds native graphs with reversible address/storage namespacing.
# Current installed Execute Process only resolves Repository ProcessEntry, so it is deliberately
# not used for a portable local-file driver. Original learner settings are left untouched.
driver=E.Element('process',version=V);ctx=E.SubElement(driver,'context');[E.SubElement(ctx,k) for k in ['input','output','macros']]
root=E.SubElement(driver,'operator',activated='true',attrib={'class':'process','compatibility':V,'expanded':'true','name':'Common Test Driver'});E.SubElement(root,'parameter',key='random_seed',value='2001');E.SubElement(root,'parameter',key='encoding',value='UTF-8');dp=E.SubElement(root,'process',expanded='true')
namespace_proof=[]
def rewrite_reference(value,mapping):
 # Native optimizer entries use Operator.parameter; logs use operator.Operator.value.*.
 for old,new in sorted(mapping.items(),key=lambda x:len(x[0]),reverse=True):
  value=value.replace('operator.'+old+'.','operator.'+new+'.')
 for old,new in sorted(mapping.items(),key=lambda x:len(x[0]),reverse=True):
  if value.startswith(old+'.'):return new+value[len(old):]
 return value
previous=None
for i,(code,name) in enumerate(MODELS.items(),1):
 execute='Run '+code;splitter='Keep '+code+' Full Metrics'
 modeltree=E.parse(R/f'model_{code}.rmp');body=copy.deepcopy(modeltree.find('.//operator/process'))
 ops=body.findall('.//operator');oldnames=[o.attrib['name'] for o in ops];assert len(oldnames)==len(set(oldnames))
 mapping={n:code+'__'+n for n in oldnames};reverse={v:k for k,v in mapping.items()}
 before_namespace=copy.deepcopy(body)
 for o in ops:
  oldname=o.attrib['name'];o.attrib['name']=mapping[oldname]
  if o.attrib['class'] in ['remember','recall']:
   n=o.find("parameter[@key='name']")
   if n is not None:n.attrib['value']=code+'__MEM__'+n.attrib['value']
 for c in body.findall('.//connect'):
  for k in ['from_op','to_op']:
   if k in c.attrib:c.attrib[k]=mapping[c.attrib[k]]
 for n in body.findall('.//parameter'):
  n.attrib['key']=rewrite_reference(n.attrib['key'],mapping)
  n.attrib['value']=rewrite_reference(n.attrib['value'],mapping)
  if n.attrib['key'] in ['operator_name','source_operator','target_operator','operator','log_name'] and n.attrib['value'] in mapping:n.attrib['value']=mapping[n.attrib['value']]
 # Reverse all address changes and prove they do not modify original copied settings/logic.
 inverse=copy.deepcopy(body)
 for o in inverse.findall('.//operator'):
  o.attrib['name']=reverse[o.attrib['name']]
  if o.attrib['class'] in ['remember','recall']:
   n=o.find("parameter[@key='name']")
   if n is not None:n.attrib['value']=n.attrib['value'].removeprefix(code+'__MEM__')
 for c in inverse.findall('.//connect'):
  for k in ['from_op','to_op']:
   if k in c.attrib:c.attrib[k]=reverse[c.attrib[k]]
 for n in inverse.findall('.//parameter'):
  n.attrib['key']=rewrite_reference(n.attrib['key'],reverse);n.attrib['value']=rewrite_reference(n.attrib['value'],reverse)
  if n.attrib['key'] in ['operator_name','source_operator','target_operator','operator','log_name'] and n.attrib['value'] in reverse:n.attrib['value']=reverse[n.attrib['value']]
 assert signature(inverse)==signature(before_namespace),'Non-address native settings changed for '+code
 for c in body.findall('connect'):
  if 'to_op' not in c.attrib and c.attrib['to_port'].startswith('result '):c.attrib['to_port']=c.attrib['to_port'].replace('result ','out ',1)
 for old in body.findall('portSpacing'):body.remove(old)
 E.SubElement(body,'portSpacing',port='source_in 1',spacing='0')
 for j in range(1,28):E.SubElement(body,'portSpacing',port=f'sink_out {j}',spacing='0')
 wrapper=op('subprocess',execute,30+(i-1)*220,30);wrapper.append(body);dp.append(wrapper)
 dp.append(op('multiply',splitter,140+(i-1)*220,30))
 if previous:con(dp,previous,'output 2',execute,'in 1')
 con(dp,execute,'out 1',splitter,'input');con(dp,splitter,'output 1',None,f'result {i}');con(dp,execute,'out 2',None,f'result {i+9}');con(dp,execute,'out 3',None,f'result {i+18}');con(dp,execute,'out 4',None,f'result {i+27}')
 previous=splitter
 namespace_proof.append({'model':name,'code':code,'operator_count':len(ops),'operator_log_optimizer_reference_and_memory_namespace_reversible':True,'learner_parameters_and_random_seed_fields_unchanged':True})
assert len({o.attrib['name'] for o in dp.findall('.//operator')})==len(dp.findall('.//operator'))
E.SubElement(dp,'description',align='left',color='yellow',colored='false',height='130',width='1020',x='30',y='260').text='Run nine actual generated AutoModel templates sequentially with unique operator/memory namespaces. All use the full prepared1048575-row CSV, a30k initial modeling sample with local2001, main60/40 split1992, specialCOMMON_ROW_ID, and full-holdout metrics. Existing native robust7 evaluation is retained but supplemental. Original saved nine-model processes/models are not overwritten. Verify exported row-ID/label membership across allnine before accepting comparisons.'
for i in range(1,38):E.SubElement(dp,'portSpacing',port=f'sink_result {i}',spacing='0')
E.indent(driver,space='  ');E.ElementTree(driver).write(R/'MiniProject2_Common_Test_9Models.rmp',encoding='UTF-8',xml_declaration=True)
# Registry and public operator docs ground every new primitive and the Execute Process driver.
newclasses={'read_csv','generate_macro','generate_id','rename','set_role','multiply','select_attributes','write_csv','recall','performance_binominal_classification','performance_to_data','subprocess'}
registered=set()
for jar in Path(r'D:\AI Studio 2026.1.1\lib').rglob('*.jar'):
 with zipfile.ZipFile(jar) as z:
  for name in z.namelist():
   if name.endswith('.xml') and 'Operators' in name and 'Documentation' not in name and '/i18n/' not in name:
    try:t=E.fromstring(z.read(name))
    except E.ParseError:continue
    prefix=t.attrib.get('name','')
    for o in t.findall('.//operator'):
     key=o.findtext('key')
     if key:registered.add((prefix+':' if prefix and prefix not in ['core','rapidminer'] else '')+key)
for cls in newclasses:assert cls in registered or cls.split(':')[-1] in registered,cls
for code,name in MODELS.items():assert hashlib.sha256((SOURCE/name/'process.rmp').read_bytes()).hexdigest()==source_hashes[code]
(R/'common_test_build_manifest.json').write_text(json.dumps({'prepared_source':str(PREPARED),'prepared_source_sha256':hashlib.sha256(PREPARED.read_bytes()).hexdigest(),'models':manifest,'new_operator_registry_ids_verified':sorted(newclasses),'driver':'MiniProject2_Common_Test_9Models.rmp','driver_architecture':'sequential embedded native subprocesses; reversible operator/log/optimizer/memory namespaces','namespace_proof':namespace_proof,'root_global_seed':2001,'holdout_membership_verified_from_native_exports':False,'native_rerun_complete':False},indent=2),encoding='utf8')
print('CREATED nine model copies and one sequential driver; original sources unchanged')
print('Driver',R/'MiniProject2_Common_Test_9Models.rmp')
print('Common full evaluation uses every validation row; native exports/membership proof still pending')
