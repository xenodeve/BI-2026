"""Extract saved native Auto Model results without changing the native repository."""
from pathlib import Path
import csv, hashlib, json, math, sys, xml.etree.ElementTree as ET
from collect_evidence import ROOT, MODELS, METRICS, NATIVE_ENGINE, dump, load_json

REPOSITORY = ROOT.parent / 'Native_AI_Repository' / 'MiniProject2_AutoModel_9Models'
NAMES = {'GLM': 'Generalized Linear Model', 'GBT': 'Gradient Boosted Trees', 'SVM': 'Support Vector Machine'}
CRITERIA = {'Accuracy': ('MultiClassificationPerformance', 0),
            'Precision': ('BinaryClassificationPerformance', 0),
            'Recall': ('BinaryClassificationPerformance', 1),
            'F1': ('BinaryClassificationPerformance', 4),
            'AUC': ('AreaUnderCurve$Neutral', None)}
READINGS = {
    'Naive Bayes':'Accuracy และ F1 ต่ำสุดใน checkpoint; ค้น Hospitalized ได้ประมาณ62% จึงมี FN มาก',
    'GLM':'Precision สูงกว่า Recall อย่างชัดเจน; เหมาะอ่านผลควบคู่กับ FN ของกลุ่ม Hospitalized',
    'Logistic Regression':'Precision สูงแต่ Recall ต่ำ; base coefficients ช่วยอ่านทิศทางตาม encoding ได้',
    'Fast Large Margin':'AUC ต่ำสุดใน checkpoint; ค่า Precision สูงกว่า Recall จึงต้องดู missed positives',
    'Deep Learning':'Accuracy F1 และ AUC สูงสุดใน checkpoint; Recall ยังต่ำกว่า RF และ GBT',
    'Decision Tree':'Accuracy สูงและ F1 รองจาก Deep Learning; มีเส้นทาง native tree อ่านได้',
    'Random Forest':'Recall สูงกว่าโมเดลเชิงเส้นแต่ Precision ต่ำกว่า; ต้องชั่ง FP และ FN',
    'GBT':'Recall สูงสุดแต่ Precision ต่ำสุดใน checkpoint; ค้น Hospitalized เพิ่มแลกกับ FP มาก',
    'SVM':'Precision สูงสุดแต่ Recall ต่ำสุดใน checkpoint; counterมีขนาดเล็กสุดจึงต้องระวังการเทียบ',
}

def read_native(path):
    content = path.read_bytes()
    return json.loads(content), hashlib.sha256(content).hexdigest()

def process_metadata(path):
    root = ET.parse(path).getroot()
    ops = list(root.iter('operator'))
    params = lambda op: {p.get('key'): p.get('value') for p in op.findall('parameter')}
    main = next(o for o in ops if o.get('class') == 'process')
    sample = next(o for o in ops if o.get('name') == 'Sample' and o.get('class') == 'sample_stratified')
    split = next(o for o in ops if o.get('name') == 'Split Data' and o.get('class') == 'split_data')
    batch = next(o for o in ops if o.get('name') == 'Generate Batch')
    loop = next(o for o in ops if o.get('name') == 'Performance for Hold-Out Sets')
    robust = next(o for o in ops if o.get('name') == 'Performance Average (Robust)')
    return {'source_process': str(path.relative_to(ROOT.parent)),
            'source_process_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'root_random_seed': int(params(main)['random_seed']),
            'initial_sample_operator': sample.get('class'),
            'initial_sample_size_cap': int(params(sample)['sample_size']),
            'initial_sample_use_local_seed': params(sample)['use_local_random_seed'],
            'main_split_ratios': [float(p.get('value')) for p in split.findall("enumeration[@key='partitions']/parameter")],
            'main_split_sampling_type': params(split)['sampling_type'],
            'main_split_local_seed': int(params(split)['local_random_seed']),
            'holdout_batch_count': int(params(batch)['number of batches']),
            'holdout_iterations': int(params(loop)['number_of_iterations']),
            'aggregation_operator': robust.get('class')}

def extract():
    raw_comparison = list(csv.DictReader((ROOT/'Native_Comparison_Raw.csv').open(encoding='utf-8-sig')))
    raw_by_name = {x['Model']: x for x in raw_comparison}
    records=[]; evidence={}; hashes={}
    for model in MODELS:
        folder=REPOSITORY/NAMES.get(model, model); source=folder/'Performance.rmperf'
        native, digest=read_native(source); hashes[source]=digest
        assert native['rm_object_type']=='com.rapidminer.operator.performance.PerformanceVector'
        values=native['averagesList']; metric_data={}
        for metric,(kind,type_code) in CRITERIA.items():
            criteria=[c for c in values if c['rm_object_type'].endswith('.'+kind) and c.get('type')==type_code]
            assert len(criteria)==1, (model,metric,len(criteria))
            c=criteria[0]; n=c['averageCount']; mean=c['meanSum']/n
            sd=math.sqrt(max(0,(c['meanSquaredSum']-c['meanSum']**2/n)/(n-1))) if n>1 else 0
            assert n==5 and 0<=mean<=1 and math.isfinite(sd)
            metric_data[metric]={'mean':mean,'sample_sd':sd,'average_count':n,
                                 'criterion_type':c['rm_object_type'],'type_code':c.get('type')}
            if metric!='Accuracy':
                assert c.get('positiveClass',c.get('positiveClassName'))=='Hospitalized'
        accuracy=next(c for c in values if c['rm_object_type'].endswith('.MultiClassificationPerformance') and c['type']==0)
        assert accuracy['classNames']==['Outpatient','Hospitalized']
        counter=accuracy['counter'];tn,fp=counter[0];fn,tp=counter[1]
        cm={'tn':int(tn),'fp':int(fp),'fn':int(fn),'tp':int(tp),'n':int(tn+fp+fn+tp),
            'actual_outpatient':int(tn+fp),'actual_hospitalized':int(fn+tp),
            'orientation':'true class rows, predicted class columns; [Outpatient, Hospitalized]'}
        combined={'Accuracy':(tn+tp)/cm['n'],'Precision':tp/(tp+fp),'Recall':tp/(tp+fn),'F1':2*tp/(2*tp+fp+fn)}
        raw=raw_by_name[folder.name]
        assert abs((1-float(raw['Classification Error']))-metric_data['Accuracy']['mean'])<1e-12
        assert abs(float(raw['Standard Deviation'])-metric_data['Accuracy']['sample_sd'])<1e-9
        metadata=process_metadata(folder/'process.rmp')
        source_relative=str(source.relative_to(ROOT.parent))
        note=(f"Native {folder.name}/Performance.rmperf; counter N={cm['n']:,}. "
              +READINGS[model]+'. ข้อสรุปนี้อธิบาย checkpoint ที่ใช้ Test ต่างชุด ยังไม่ใช่ final comparison.')
        record={'Model':model,**{m:metric_data[m]['mean'] for m in METRICS},
                **{m+'SD':metric_data[m]['sample_sd'] for m in METRICS},'Engine':NATIVE_ENGINE,
                'PositiveClass':'Hospitalized','TestSetID':'',
                'Screenshot':'screenshots/native_06_all9_completed.png','Notes':note,
                'NativePerformanceFile':source_relative,'NativePerformanceSHA256':digest,
                'CombinedConfusionN':cm['n'],'AverageCount':5,'HoldoutBatches':7}
        records.append(record)
        evidence[model]={'native_file':source_relative,'native_sha256':digest,'metrics':metric_data,
                         'confusion_matrix':cm,'combined_confusion_metrics':combined,
                         'mean_minus_combined':{m:metric_data[m]['mean']-combined[m] for m in combined},
                         'process':metadata,'raw_classification_error_crosscheck':True,
                         'raw_sd_crosscheck':True,'checkpoint_files_present':
                         {name:(folder/name).is_file() for name in ['process.rmp','Model.rmmodel','Production Model.rmmodel','Predictions.rmexpred','score.rmp']}}
    with (ROOT/'Native_Default_Model_Comparison.csv').open('w',newline='',encoding='utf-8-sig') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
    audit={'engine':NATIVE_ENGINE,'native_version':'12.1.1','positive_class':'Hospitalized',
           'mean_formula':'meanSum / averageCount',
           'sample_sd_formula':'sqrt((meanSquaredSum - meanSum^2 / averageCount) / (averageCount - 1))',
           'criterion_mapping':CRITERIA,'aggregation':'Native seven holdout batches; robust average retains five. It is not five-fold cross-validation.',
           'same_test_set_requirement_met':False,
           'same_test_set_reason':'Different initial sample caps BEFORE the 60/40 split and unequal saved confusion counts prove these nine summaries are not a common testing set.',
           'native_nb_gui_rounding_crosscheck':{m:round(evidence['Naive Bayes']['metrics'][m]['mean']*100,1) for m in METRICS},
           'models':evidence,'native_files_unchanged':all(hashlib.sha256(p.read_bytes()).hexdigest()==h for p,h in hashes.items())}
    dump(ROOT/'native_result_audit.json',audit)
    with (ROOT/'native_confusion_counts.csv').open('w',newline='',encoding='utf-8-sig') as stream:
        writer=csv.DictWriter(stream,fieldnames=['Model','TN','FP','FN','TP','N','ActualOutpatient','ActualHospitalized'])
        writer.writeheader()
        for model in MODELS:
            cm=evidence[model]['confusion_matrix'];writer.writerow({'Model':model,'TN':cm['tn'],'FP':cm['fp'],'FN':cm['fn'],'TP':cm['tp'],'N':cm['n'],'ActualOutpatient':cm['actual_outpatient'],'ActualHospitalized':cm['actual_hospitalized']})
    setup=load_json('native_default_setup.json') or load_json('native_setup.template.json')
    setup.update({'engine':NATIVE_ENGINE,'target':'PATIENT_TYPE','positive_class':'Hospitalized',
                  'target_mapping':{'1':'Outpatient','2':'Hospitalized'},'prepared_rows':1048575,
                  'inputs':load_json('raw_data_quality.json')['inputs'],'age_numeric_others_nominal':True,
                  'split_method':'Per-model initial stratified sample, then automatic 60/40 split with local seed1992; validation split into seven holdout batches, five retained by robust average',
                  'seed':2001,'split_local_seed':1992,'test_set_id':None,
                  'model_rows_used':None,'training_rows':None,'test_rows':None,
                  'sampling_or_license_limit':'Auto Model per-model caps differ: see native_result_audit.json; common testing-set requirement currently unmet',
                  'missing_code_policy':'Native nominal dictionaries retain original 98/99 categories plus native MISSING level; AGE remains numeric',
                  'setup_screenshots':['screenshots/native_02_turbo_prepared.png','screenshots/native_03_positive_target.png','screenshots/native_04_inputs15.png','screenshots/native_05_nine_models.png'],
                  'native_run_complete':True,'same_test_set_requirement_met':False,'native_metrics_available':True,
                  'per_model_result_metadata':'native_result_audit.json'})
    dump(ROOT/'native_default_setup.json',setup)
    reading=load_json('native_default_model_reading.json') or load_json('native_model_reading.template.json')
    logistic,_=read_native(REPOSITORY/'Logistic Regression'/'Model.rmmodel')
    base=logistic['baseModel']['baseModel']
    adapted=base['glmScore']['_dinfo']['_trainingAdaptedExampleSet']
    assert next(x for x in adapted['columns'] if x['name']=='PATIENT_TYPE')['dictionary']==[None,'Outpatient','Hospitalized']
    coefficients=list(zip(base['coefficientNames'],base['coefficients']))
    chosen=sorted([(name,weight) for name,weight in coefficients if name!='Intercept' and not name.endswith('.MISSING')],key=lambda x:abs(x[1]),reverse=True)[:6]
    chosen.extend((name,weight) for name,weight in coefficients if name=='AGE')
    reading['logistic_regression'].update({'coefficients':[{'feature':name,'weight':weight,
          'reference_category':'1 จาก encoded native names (inferred)' if '.' in name else 'อายุต่อ1ปี native normMul=null',
          'interpretation':('บวก' if weight>0 else 'ลบ')+' ต่อ base logit ของ Hospitalized; final model มี calibration และ cost wrapper'} for name,weight in chosen],
          'native_file':'Native_AI_Repository/MiniProject2_AutoModel_9Models/Logistic Regression/Model.rmmodel',
          'coefficient_layer':'baseModel.baseModel; full coefficients in native_logistic_coefficients.csv'})
    with (ROOT/'native_logistic_coefficients.csv').open('w',newline='',encoding='utf-8-sig') as stream:
        writer=csv.writer(stream);writer.writerow(['Coefficient','NativeWeight','NativeStandardizedWeight'])
        writer.writerows(zip(base['coefficientNames'],base['coefficients'],base['stdCoefficients']))
    tree,_=read_native(REPOSITORY/'Decision Tree'/'Model.rmmodel');tree=tree['baseModel']['baseModel']
    root=tree['root'];edge=root['children'][0];leaf=edge['child'];assert not leaf['children']
    reading['decision_tree'].update({'root':'PNEUMONIA','path_to_leaf':['PNEUMONIA = '+edge['condition']['valueString']],
          'leaf_prediction':leaf['label'],'leaf_training_counts':leaf['counterMap'],
          'native_file':'Native_AI_Repository/MiniProject2_AutoModel_9Models/Decision Tree/Model.rmmodel',
          'note':'Read from native serialized base tree; leaf counts are training-node counts, not the test confusion matrix.'})
    weights,_=read_native(REPOSITORY/'Random Forest'/'Weights.rmweights')
    assert {x['weight'] for x in weights['averagesList']}=={1.0}
    reading['random_forest']['note']='Saved Weights.rmweights assigns all15 inputs weight1.0; no ranked importance can be inferred. Model Simulator globalWeights=null. Actual native GUI importance remains pending.'
    dump(ROOT/'native_default_model_reading.json',reading)
    assert audit['native_files_unchanged']
    print('Extracted all nine native means/sample SDs; classification-error and SD exports crosschecked; common Test set requirement NOT met.')
    for row in records:print(row['Model'],*(f'{row[m]:.6f}' for m in METRICS),'N',row['CombinedConfusionN'])

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');extract()
