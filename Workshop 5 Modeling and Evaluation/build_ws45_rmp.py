from pathlib import Path
import xml.etree.ElementTree as E,json,shutil
W5=Path(__file__).resolve().parent;W4=W5.parent/'Workshop 4 การจัดเตรียมข้อมูล (Data Preparation)'
V='12.1.001'
def start():
 d=E.Element('process',version=V);ctx=E.SubElement(d,'context');[E.SubElement(ctx,n) for n in ['input','output','macros']]
 r=E.SubElement(d,'operator',activated='true',attrib={'class':'process','compatibility':V,'expanded':'true','name':'Root'});E.SubElement(r,'parameter',key='random_seed',value='2026');E.SubElement(r,'parameter',key='encoding',value='UTF-8');p=E.SubElement(r,'process',expanded='true');return d,p
def op(p,cls,name,x,y,params=None,lists=None,compat=V):
 e=E.SubElement(p,'operator',activated='true',attrib={'class':cls,'compatibility':compat,'expanded':'true','height':'103','width':'90','name':name,'x':str(x),'y':str(y)})
 for k,v in (params or {}).items():E.SubElement(e,'parameter',key=k,value=str(v))
 for k,rows in (lists or {}).items():
  l=E.SubElement(e,'list',key=k)
  for a,b in rows:E.SubElement(l,'parameter',key=str(a),value=str(b))
 return e
def con(p,a,ap,b,bp):
 x={'from_port':ap,'to_port':bp}
 if a:x['from_op']=a
 if b:x['to_op']=b
 E.SubElement(p,'connect',x)
columns=['HeartDisease','BMI','Smoking','AlcoholDrinking','Stroke','PhysicalHealth','MentalHealth','DiffWalking','Sex','AgeCategory','Race','Diabetic','PhysicalActivity','GenHealth','SleepTime','Asthma','KidneyDisease','SkinCancer']
numeric={'BMI','PhysicalHealth','MentalHealth','SleepTime'}
def csv(p,name,filename,x,y,extra=None):
 cols=columns+(extra or []);metadata=[(i,f'{c}.true.'+('real' if c in numeric else 'binominal' if c=='HeartDisease' else 'polynominal')+'.attribute') for i,c in enumerate(cols)]
 op(p,'read_csv',name,x,y,{'csv_file':'%{dataset_path}','column_separators':',','first_row_as_names':'true','parse_numbers':'true','decimal_character':'.','trim_lines':'true','use_quotes':'true','encoding':'UTF-8','read_not_matching_values_as_missings':'false'},{'data_set_meta_data_information':metadata})
def portable(p,filename,additional=None):
 entries=[('dataset_path',f'replace(%{{process_path}}, %{{process_file}}, "{filename}")')]
 for k,v in (additional or {}).items():entries.append((k,f'replace(%{{process_path}}, %{{process_file}}, "{v}")'))
 op(p,'generate_macro','Portable Paths',30,30,lists={'function_descriptions':entries})
def save(d,p,path,count):
 E.SubElement(p,'portSpacing',port='source_input 1',spacing='0')
 for i in range(1,count+2):E.SubElement(p,'portSpacing',port=f'sink_result {i}',spacing='0')
 E.indent(d,space='  ');E.ElementTree(d).write(path,encoding='UTF-8',xml_declaration=True)
 names={x.attrib['name'] for x in p.findall('operator')}
 for c in p.findall('connect'):
  for field in ['from_op','to_op']:assert field not in c.attrib or c.attrib[field] in names
 return sorted({x.attrib['class'] for x in p.findall('operator')})
# WS4 prepares raw data in native operators; it preserves all respondents and all original fields.
d,p=start();portable(p,'heart_2020_cleaned.csv',{'prepared_path':'heart_2020_prepared_native.csv'})
csv(p,'Read Original 2020 Heart Data','heart_2020_cleaned.csv',30,180)
op(p,'multiply','Keep Raw View',180,180)
op(p,'generate_attributes','Any Unhealthy Days',330,110,{'keep_all':'true'},{'function_descriptions':[('AnyUnhealthyDays','if((PhysicalHealth > 0) || (MentalHealth > 0), "Yes", "No")')]})
op(p,'write_csv','Export Prepared Native CSV',480,110,{'csv_file':'%{prepared_path}','column_separator':',','write_attribute_names':'true','quote_nominal_values':'true','append_to_file':'false','encoding':'UTF-8'})
op(p,'set_role','HeartDisease Label',630,110,{'attribute_name':'HeartDisease','target_role':'label'})
con(p,'Read Original 2020 Heart Data','output','Keep Raw View','input');con(p,'Keep Raw View','output 1','Any Unhealthy Days','example set input');con(p,'Keep Raw View','output 2',None,'result 2');con(p,'Any Unhealthy Days','example set output','Export Prepared Native CSV','input');con(p,'Export Prepared Native CSV','through','HeartDisease Label','example set input');con(p,'HeartDisease Label','example set output',None,'result 1')
E.SubElement(p,'description',align='left',color='yellow',colored='false',height='140',width='820',x='30',y='380').text='WS4 follows BI06 Data Quality/Turbo Prep. Retain all319795 anonymous survey respondents: matching profiles are not proven duplicate identities. No imputation: missing0. Retain numeric extremes and review IQR flags. Create AnyUnhealthyDays without label. Raw original filename and bytes preserved. Native TurboPrep screenshots and Run still require actual app evidence.'
classes4=save(d,p,W4/'Workshop4_Data_Preparation.rmp',2)
# WS5 consumes the prepared fixed group split, keeping identical predictor profiles in one partition.
d,p=start();exports={f'export_{n}':f'native_{n}.csv' for n in ['NB','LR','DT','RF','GBT']};portable(p,'heart_2020_modeling.csv',exports)
csv(p,'Read Prepared Group Split','heart_2020_modeling.csv',30,180,['AnyUnhealthyDays','SplitSet'])
op(p,'set_role','HeartDisease Label',170,180,{'attribute_name':'HeartDisease','target_role':'label'})
op(p,'filter_examples','Fixed Shared Group Holdout',310,180,lists={'filters_list':[('filters_entry_key','SplitSet.equals.train')]})
op(p,'select_attributes','Remove SplitSet Train',450,85,{'attribute_filter_type':'single','attribute':'SplitSet','invert_selection':'true','include_special_attributes':'true'})
op(p,'select_attributes','Remove SplitSet Test',450,285,{'attribute_filter_type':'single','attribute':'SplitSet','invert_selection':'true','include_special_attributes':'true'})
op(p,'nominal_to_numerical','Fit Training Encoding',590,85,{'attribute_filter_type':'all','include_special_attributes':'false','coding_type':'dummy coding','use_comparison_groups':'false','use_underscore_in_name':'true','return_preprocessing_model':'true'})
op(p,'normalize','Fit Training Scaling',730,85,{'attribute_filter_type':'all','include_special_attributes':'false','method':'Z-transformation','return_preprocessing_model':'true'})
op(p,'apply_model','Apply Training Encoding to Test',590,285,{'create_view':'false'})
op(p,'apply_model','Apply Training Scaling to Test',730,285,{'create_view':'false'})
op(p,'multiply','Same Training Five Models',870,85);op(p,'multiply','Same Test Five Models',870,285)
con(p,'Read Prepared Group Split','output','HeartDisease Label','example set input');con(p,'HeartDisease Label','example set output','Fixed Shared Group Holdout','example set input');con(p,'Fixed Shared Group Holdout','example set output','Remove SplitSet Train','example set input');con(p,'Fixed Shared Group Holdout','unmatched example set','Remove SplitSet Test','example set input');con(p,'Remove SplitSet Train','example set output','Fit Training Encoding','example set input');con(p,'Remove SplitSet Test','example set output','Apply Training Encoding to Test','unlabelled data');con(p,'Fit Training Encoding','example set output','Fit Training Scaling','example set input');con(p,'Fit Training Encoding','preprocessing model','Apply Training Encoding to Test','model');con(p,'Fit Training Scaling','preprocessing model','Apply Training Scaling to Test','model');con(p,'Apply Training Encoding to Test','labelled data','Apply Training Scaling to Test','unlabelled data');con(p,'Fit Training Scaling','example set output','Same Training Five Models','input');con(p,'Apply Training Scaling to Test','labelled data','Same Test Five Models','input')
models=[('naive_bayes','Naive Bayes','NB',{'laplace_correction':'true'},V),('h2o:logistic_regression','Logistic Regression','LR',{'reproducible':'true','maximum_number_of_threads':'2','max_iterations':'100','standardize':'false','remove_collinear_columns':'true','compute_p-values':'false'},'11.0.003'),('concurrency:parallel_decision_tree','Decision Tree','DT',{'criterion':'gain_ratio','maximal_depth':'8','minimal_leaf_size':'30','apply_pruning':'true'},V),('concurrency:parallel_random_forest','Random Forest','RF',{'number_of_trees':'100','maximal_depth':'12','minimal_leaf_size':'10','use_local_random_seed':'true','local_random_seed':'2026','enable_parallel_execution':'false'},V),('h2o:gradient_boosted_trees','Gradient Boosted Trees','GBT',{'number_of_trees':'60','maximal_depth':'3','learning_rate':'0.1','distribution':'bernoulli','reproducible':'true','maximum_number_of_threads':'2','use_local_random_seed':'true','local_random_seed':'2026','early_stopping':'false'},'11.0.003')]
for i,(cls,name,slug,pars,compat) in enumerate(models,1):
 y=30+(i-1)*155;score='Score '+slug;perf='Performance '+slug;ptd='Performance to Data '+slug;writer='Export Native '+slug
 op(p,cls,name,1020,y,pars,compat=compat);op(p,'apply_model',score,1160,y,{'create_view':'false'});op(p,'performance_binominal_classification',perf,1300,y,{'main_criterion':'f_measure','accuracy':'true','precision':'true','recall':'true','f_measure':'true','AUC':'true','false_positive':'true','false_negative':'true','true_positive':'true','true_negative':'true','manually_set_positive_class':'true','positive_class':'Yes','use_example_weights':'false'});op(p,'performance_to_data',ptd,1440,y);op(p,'write_csv',writer,1580,y,{'csv_file':f'%{{export_{slug}}}','column_separator':',','write_attribute_names':'true','quote_nominal_values':'true','append_to_file':'false','encoding':'UTF-8'})
 con(p,'Same Training Five Models',f'output {i}',name,'training set');con(p,'Same Test Five Models',f'output {i}',score,'unlabelled data');con(p,name,'model',score,'model');con(p,score,'labelled data',perf,'labelled data');con(p,perf,'performance',ptd,'performance vector');con(p,ptd,'performance vector',None,f'result {i}');con(p,ptd,'example set',writer,'input');con(p,writer,'through',None,f'result {15+i}');con(p,perf,'example set',None,f'result {5+i}');con(p,score,'model',None,f'result {10+i}')
E.SubElement(p,'description',align='left',color='yellow',colored='false',height='150',width='980',x='30',y='840').text='WS5 slide-based disclosed assumption: five common classification models. HeartDisease positiveYes. FixedSplitSet generated reproducibly by stratified10-fold predictor-profile grouping, seed2026, folds0-2test. Same training/test for allmodels. SplitSetremoved from learners. Encoding/scalingfittraining only and applied to test. Performance exports native_NB/LR/DT/RF/GBT.csv only after actual Run. Keep original heart_2020_cleaned.csv and derived heart_2020_modeling.csv with this RMP. Native Run and relocation still pending.'
classes5=save(d,p,W5/'Workshop5_Modeling_Evaluation.rmp',20)
# All class IDs are verified against actual installed operator registries, including new filter/export operators.
regs={}
for f in (W5.parent/'BI Mini Project 1/operator-evidence').glob('*Operators*.xml'):
 try:
  t=E.parse(f).getroot();prefix=t.attrib.get('name','')
  for e in t.findall('.//operator'):
   key=e.findtext('key')
   if key:regs[(prefix+':' if prefix and prefix not in ['core','rapidminer'] else '')+key]=f.name
 except E.ParseError:pass
allclasses=set(classes4+classes5)
for cls in allclasses:assert cls in regs or cls.split(':')[-1] in regs,cls
evidence={cls:regs.get(cls,regs.get(cls.split(':')[-1])) for cls in allclasses}
(W5/'rmp_operator_evidence.json').write_text(json.dumps(evidence,indent=2),encoding='utf8');(W4/'rmp_operator_evidence.json').write_text(json.dumps({cls:evidence[cls] for cls in classes4},indent=2),encoding='utf8')
print('RMP4 andRMP5 created; operator IDs/ports grounded; native Run pending')

