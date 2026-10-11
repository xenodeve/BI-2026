"""Validate actual common native exports and prepare truthful report inputs."""
from pathlib import Path
import csv, hashlib, json, math, sys
import pandas as pd
from collect_evidence import ROOT, MODELS, METRICS, dump, load_json

ENGINE='Native AI Studio official batch full common holdout'
CODES={'Naive Bayes':'NB','GLM':'GLM','Logistic Regression':'LR','Fast Large Margin':'FLM','Deep Learning':'DL','Decision Tree':'DT','Random Forest':'RF','GBT':'GBT','SVM':'SVM'}
NAMES={'GLM':'Generalized Linear Model','GBT':'Gradient Boosted Trees','SVM':'Support Vector Machine'}
FIELDS={'Accuracy':'accuracy','Precision':'precision_yes','Recall':'recall_yes','F1':'f1_yes','AUC':'roc_auc'}
NOTES={
 'Naive Bayes':'Precision0.6910/Recall0.6243/F10.6560 เป็น baseline native ที่ฝึกเร็ว; ยังพลาด Hospitalized860ราย',
 'GLM':'Accuracy0.9033/Precision0.8275 สูง แต่ Recall0.6225; ต้องพิจารณา FN864ราย',
 'Logistic Regression':'Precisionสูงสุด0.8731 แต่ Recall0.4329 และ FN1298ราย; coefficientของ common-fit ยังรอ model artifact',
 'Fast Large Margin':'AUC0.7215/F10.4902 ต่ำสุดในชุดนี้ และ FN1452ราย; ไม่เหมาะเมื่อเน้นค้น Hospitalized',
 'Deep Learning':'Accuracy Recall F1 และ AUC สูงสุดใน common test; Precision0.7746 แลกกับ FN677/FP469ราย',
 'Decision Tree':'Accuracy0.9028/F10.7077; กฎ common-fit จะอ่านจาก native model artifact เท่านั้น',
 'Random Forest':'Precision0.8249 แต่ Recall0.5435/F10.6553; genuine importance ต้องมาจาก learner weights port',
 'GBT':'F10.7114/Recall0.6579 เป็นสมดุลรองจาก DLในชุดนี้; FP439/FN783ราย',
 'SVM':'Precision0.8449/Accuracy0.9015 แต่ Recall0.5924; FN933ราย',
}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def validate():
    directory=ROOT/'common_test';audit=load_json('common_test/common_exports_validation.json')
    assert audit['verified'] is True and audit['all_exports_newer_than_run_start'] is True
    summary=pd.read_csv(directory/'Native_Common_Test_Model_Comparison.csv').set_index('model')
    models={};reference_train=None;reference_test=None;frames={}
    for name,code in CODES.items():
        rows={}
        for kind in ['metrics','predictions','train_ids','test_ids']:
            path=directory/f'{kind}_{code}.csv';assert sha(path)==audit['actual_export_sha256'][path.name]
            rows[kind]=pd.read_csv(path)
        train=rows['train_ids'];test=rows['test_ids'];pred=rows['predictions']
        pairs=lambda frame:set(zip(frame.COMMON_ROW_ID.astype(int),frame.PATIENT_TYPE))
        tr=pairs(train);te=pairs(test)
        assert len(train)==len(tr)==18000 and train.COMMON_ROW_ID.nunique()==18000
        assert len(test)==len(te)==12000 and test.COMMON_ROW_ID.nunique()==12000
        assert not set(train.COMMON_ROW_ID)&set(test.COMMON_ROW_ID)
        assert len(pred)==pred.COMMON_ROW_ID.nunique()==12000 and pairs(pred)==te
        if reference_train is None:reference_train=tr;reference_test=te
        else:assert tr==reference_train and te==reference_test
        y=pred.PATIENT_TYPE.eq('Hospitalized');p=pred['prediction(PATIENT_TYPE)'].eq('Hospitalized');score=pred['confidence(Hospitalized)']
        assert score.between(0,1).all() and p.equals(score.ge(.5))
        tp=int((y&p).sum());fp=int((~y&p).sum());fn=int((y&~p).sum());tn=int((~y&~p).sum())
        n1=int(y.sum());n0=len(y)-n1;ranks=score.rank(method='average')
        values={'Accuracy':(tp+tn)/len(pred),'Precision':tp/(tp+fp),'Recall':tp/(tp+fn),'F1':2*tp/(2*tp+fp+fn),'AUC':float((ranks[y].sum()-n1*(n1+1)/2)/(n1*n0))}
        native=rows['metrics'].set_index('Criterion')['Value'];criteria={'Accuracy':'accuracy','Precision':'precision','Recall':'recall','F1':'f_measure','AUC':'AUC'}
        sr=summary.loc[NAMES.get(name,name)]
        assert all(abs(values[m]-float(native[criteria[m]]))<1e-10 and abs(values[m]-float(sr[FIELDS[m]]))<1e-10 for m in METRICS)
        models[name]={'code':code,'train_rows':18000,'test_rows':12000,'metrics':{m:float(native[criteria[m]]) for m in METRICS},
                     'counts':{'tp':tp,'fp':fp,'fn':fn,'tn':tn},'test_id_label_hash':audit['models'][0]['test_id_label_sha256'],
                     'native_metrics_file':f'common_test/metrics_{code}.csv','native_predictions_file':f'common_test/predictions_{code}.csv',
                     'native_metrics_sha256':sha(directory/f'metrics_{code}.csv'),'native_predictions_sha256':sha(directory/f'predictions_{code}.csv')}
        frames[name]=pred
    expected={i:label for i,label in reference_train|reference_test};matched=0;source_rows=0
    source=ROOT/'COVID_Prepared_Native.csv';assert sha(source)==audit['prepared_source_membership']['prepared_source_sha256']
    with source.open(encoding='utf-8-sig') as stream:
        for i,row in enumerate(csv.DictReader(stream),1):
            source_rows=i
            if i in expected:assert row['PATIENT_TYPE']==expected[i];matched+=1
    assert source_rows==1048575 and matched==30000
    proof={'passed':True,'models':models,'source_directory':'common_test','actual_export_sha256':audit['actual_export_sha256'],
           'prepared_source':'COVID_Prepared_Native.csv','prepared_source_sha256':sha(source),'prepared_rows':source_rows,
           'model_rows':30000,'training_rows':18000,'test_rows':12000,'test_set_id':audit['models'][0]['test_id_label_sha256'],
           'source_audit':'common_test/common_exports_validation.json','source_audit_sha256':sha(directory/'common_exports_validation.json'),
           'comparison_source':'common_test/Native_Common_Test_Model_Comparison.csv','comparison_source_sha256':sha(directory/'Native_Common_Test_Model_Comparison.csv'),
           'engine':ENGINE,'execution_provenance':audit['execution_provenance'],'gui_common_results_verified':False,
           'source_id_special_not_input':True,'same_holdout_verified':True,'whole_holdout_not_robust_batches':True}
    return proof,frames

def main():
    proof,frames=validate();dump(ROOT/'common_test_verification.json',proof)
    records=[]
    for name in MODELS:
        model=proof['models'][name]
        records.append({'Model':name,**model['metrics'],'Engine':ENGINE,'PositiveClass':'Hospitalized','TestSetID':proof['test_set_id'],
                        'Screenshot':'','Notes':NOTES[name]+'. ผลจาก official native batch ไม่ใช่ภาพ GUI default เดิม.',
                        'NativePerformanceFile':model['native_metrics_file'],'NativePerformanceSHA256':model['native_metrics_sha256'],
                        'NativePredictionFile':model['native_predictions_file'],'NativeEvidenceContext':'Official batch common holdout; earlier GUI default images are context only'})
    with (ROOT/'native_model_comparison.csv').open('w',newline='',encoding='utf-8-sig') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
    setup=load_json('native_setup.template.json');setup.update({
        'engine':ENGINE,'prepared_rows':1048575,'model_rows_used':30000,'training_rows':18000,'test_rows':12000,
        'test_set_id':proof['test_set_id'],'split_method':'Same native stratified sample30000 with local seed2001; automatic split60/40 local seed1992; evaluate all12000 test rows once',
        'seed':2001,'split_local_seed':1992,'sampling_or_license_limit':'Full prepared1,048,575 rows preserved; modeling sample30,000 explicitly for compute cost, identical acrossall9',
        'inputs':load_json('raw_data_quality.json')['inputs'],'age_numeric_others_nominal':True,
        'missing_code_policy':'Nominal98/99 retained as coded categories; native MISSING category handles actual missing values; AGE numeric, ages97/98/99 not recoded as missing',
        'preprocessing_fit_scope':'Generated native feature/preprocessing fit is downstream of training split; ID role set after generic preprocessing and before sampling; validation transformed using training objects',
        'setup_screenshots':['screenshots/native_02_turbo_prepared.png','screenshots/native_03_positive_target.png','screenshots/native_04_inputs15.png'],
        'setup_screenshot_context':'Original GUI data preparation and target/input setup; not the batch common-result run',
        'selected_model':'Deep Learning','selection_reason':'Highest common-test Accuracy0.9045, Recall0.7042377, F10.7377574 and AUC0.9111739; balances FN677 with FP469. Selection uses this educational test comparison; no independent post-selection evaluation claimed.',
        'native_run_complete':True,'native_evaluations_complete':True,'native_gui_results_verified':False,'metric_scale':'fraction_0_to_1',
        'execution_provenance':proof['execution_provenance'],'common_proof':'common_test_verification.json'})
    log=ROOT.parent/'docs/execution/native-common-batch.log'
    assert log.is_file() and 'Process finished successfully' in log.read_text(encoding='utf8',errors='replace')
    setup['batch_log_success_verified']=True;dump(ROOT/'native_setup.json',setup)
    reading=load_json('native_model_reading.template.json');dl=proof['models']['Deep Learning'];pred=frames['Deep Learning']
    row=pred.loc[pred.COMMON_ROW_ID.eq(348)].iloc[0]
    assert row.PATIENT_TYPE==row['prediction(PATIENT_TYPE)']=='Hospitalized'
    inputs={k:float(row[k]) if k=='AGE' else str(row[k]) for k in setup['inputs']}
    reading['confusion_matrix'].update({'model':'Deep Learning',**dl['counts'],'test_set_id':proof['test_set_id'],
        'native_source':'common_test/predictions_DL.csv','native_metrics_source':'common_test/metrics_DL.csv','provenance':ENGINE})
    reading['scoring'].update({'model':'Deep Learning','record_inputs':inputs,'source_row_id':348,'actual_label':'Hospitalized',
        'prediction':row['prediction(PATIENT_TYPE)'],'confidence_hospitalized':float(row['confidence(Hospitalized)']),
        'confidence_outpatient':float(row['confidence(Outpatient)']),'threshold':.5,
        'native_source':'common_test/predictions_DL.csv','provenance':ENGINE,'gui_threshold_demo_verified':False})
    for section in ['logistic_regression','decision_tree','random_forest']:
        reading[section]['note']='PENDING same-evaluation-fit native explanation artifact. Do not substitute the earlier Default GUI model.'
    dump(ROOT/'native_model_reading.json',reading)
    print('Canonical report inputs created from verified common native batch exports. Same-fit LR/DT/RF artifacts and all common-result GUI screenshots remain pending.')

if __name__=='__main__':sys.stdout.reconfigure(encoding='utf8');main()
