"""Raw-data audit and native-only evidence intake. No model training is performed."""
from pathlib import Path
import argparse, csv, hashlib, json, math, sys
import pandas as pd

ROOT = Path(__file__).resolve().parent
MODELS = ['Naive Bayes', 'GLM', 'Logistic Regression', 'Fast Large Margin',
          'Deep Learning', 'Decision Tree', 'Random Forest', 'GBT', 'SVM']
METRICS = ['Accuracy', 'Precision', 'Recall', 'F1', 'AUC']
DROP = ['PREGNANT', 'DATE_DIED', 'INTUBED', 'ICU', 'CLASIFFICATION_FINAL']
SOURCE_URL = 'https://www.kaggle.com/datasets/meirnizri/covid19-dataset'
NATIVE_ENGINE = 'Altair AI Studio Auto Model'
BATCH_ENGINE = 'Native AI Studio official batch full common holdout'

def validate_common_proof(proof):
    """A batch label is accepted only while its actual source/export hashes hold."""
    errors=[]
    if not proof or proof.get('passed') is not True or set(proof.get('models', {})) != set(MODELS):
        return ['Actual common-holdout proof is absent, failed or does not cover all nine models.']
    if proof.get('engine') != BATCH_ENGINE or proof.get('whole_holdout_not_robust_batches') is not True:
        errors.append('Common proof does not identify the truthful full-holdout native batch engine.')
    files=proof.get('actual_export_sha256', {})
    if len(files)!=36:errors.append('Common proof requires all36 original export file hashes.')
    for relative,digest in files.items():
        p=(ROOT/proof.get('source_directory','')/relative).resolve()
        if not p.is_relative_to(ROOT) or not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:
            errors.append('Common native export changed or is missing: '+relative)
    for key in ['prepared_source','source_audit','comparison_source']:
        p=(ROOT/proof.get(key,'')).resolve();expected=proof.get(key+'_sha256')
        if not p.is_relative_to(ROOT) or not p.is_file() or not expected or hashlib.sha256(p.read_bytes()).hexdigest()!=expected:
            errors.append('Common proof source changed/missing: '+key)
    audit_path=ROOT/proof.get('source_audit','')
    if audit_path.is_file():
        audit=json.loads(audit_path.read_text(encoding='utf-8-sig'))
        driver=ROOT/'common_test/MiniProject2_Common_Test_9Models.rmp'
        if not driver.is_file() or hashlib.sha256(driver.read_bytes()).hexdigest()!=audit.get('driver_sha256'):
            errors.append('Canonical common native driver changed after the verified run.')
    return errors

def validate_same_fit_readings(reading):
    errors=[];proof_path=ROOT/'common_test/explanation_run/explanation_results_verification.json'
    if not proof_path.is_file():return ['Same-fit explanation native proof is not available.']
    proof=json.loads(proof_path.read_text(encoding='utf-8-sig'))
    if not all(proof.get(k) is True for k in ['passed','all36_variant_exports_byte_identical_to_canonical','native_process_finished_successfully']):
        return ['Same-fit native explanation proof has not passed.']
    for name,digest in proof.get('canonical_export_sha256',{}).items():
        baseline=ROOT/'common_test'/name;variant=ROOT/'common_test/explanation_run'/name
        if not all(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==digest for p in [baseline,variant]):
            errors.append('Same-fit replay export changed/missing: '+name)
    if len(proof.get('canonical_export_sha256',{}))!=36:errors.append('Same-fit replay proof must cover all36 exports.')
    for section,code in [('logistic_regression','LR'),('decision_tree','DT'),('random_forest','RF')]:
        entry=reading.get(section,{})
        evidence=proof.get('rf_native_weights',{}) if code=='RF' else proof.get('model_artifacts',{}).get(code,{})
        path=(ROOT/entry.get('native_artifact','')).resolve()
        if entry.get('source_fit')!='common_evaluation' or entry.get('native_artifact')!=evidence.get('path') or entry.get('native_artifact_sha256')!=evidence.get('sha256') or not path.is_relative_to(ROOT) or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=evidence.get('sha256'):
            errors.append(section+': saved native artifact does not match the evaluated common fit proof.')
    weights_path=ROOT/proof.get('rf_native_weights',{}).get('path','')
    if weights_path.is_file():
        actual=sorted(list(csv.DictReader(weights_path.open(encoding='utf-8-sig'))),key=lambda x:float(x['Weight']),reverse=True)[:3]
        declared=reading.get('random_forest',{}).get('top3_importance',[])
        if len(declared)!=3 or any(x.get('feature')!=y['Attribute'] or abs(float(x.get('importance',-1))-float(y['Weight']))>1e-12 for x,y in zip(declared,actual)):
            errors.append('Declared RF top3 importance does not equal the genuine native weights export.')
        if reading.get('random_forest',{}).get('criterion')!=proof['rf_native_weights'].get('criterion'):
            errors.append('RF importance criterion differs from the captured native learner.')
    def unwrap(value):
        while isinstance(value.get('baseModel'),dict):value=value['baseModel']
        return value
    lr_path=ROOT/proof.get('model_artifacts',{}).get('LR',{}).get('path','')
    if lr_path.is_file():
        lr=unwrap(json.loads(lr_path.read_text(encoding='utf8')))
        actual=dict(zip(lr['coefficientNames'],lr['coefficients']))
        for x in reading.get('logistic_regression',{}).get('coefficients',[]):
            if x.get('feature') not in actual or abs(float(x.get('weight',0))-actual[x['feature']])>1e-12:
                errors.append('Declared LR coefficient differs from evaluated native model: '+str(x.get('feature')))
    dt_path=ROOT/proof.get('model_artifacts',{}).get('DT',{}).get('path','')
    if dt_path.is_file():
        tree=unwrap(json.loads(dt_path.read_text(encoding='utf8')))['root'];entry=reading.get('decision_tree',{})
        root_names={e['condition']['attributeName'] for e in tree.get('children',[])}
        if root_names!={entry.get('root')}:errors.append('Declared DT root differs from evaluated native model.')
        node=tree
        for rule in entry.get('path_to_leaf',[]):
            matches=[e for e in node.get('children',[]) if e['condition']['attributeName']+' = '+str(e['condition'].get('valueString',e['condition'].get('value')))==rule]
            if len(matches)!=1:errors.append('Declared DT path differs from evaluated native model.');break
            node=matches[0]['child']
        if node.get('children') or node.get('label')!=entry.get('leaf_prediction') or node.get('counterMap')!=entry.get('leaf_training_counts'):
            errors.append('Declared DT leaf/counters differ from evaluated native model.')
    return errors

def common_gui_screenshot_verified(model,value,proof):
    if value and Path(value).name in ['native_01_raw_import.png','native_02_turbo_prepared.png','native_03_positive_target.png','native_04_inputs15.png','native_05_nine_models.png','native_06_all9_completed.png','native_NB_performance.png','native_common_test_process.png']:
        return False
    manifest=load_json('common_gui_evidence.json') or {}
    entry=manifest.get('models',{}).get(model,{})
    if not screenshot_exists(value) or entry.get('screenshot')!=value or entry.get('test_set_id')!=proof.get('test_set_id'):
        return False
    return entry.get('common_result_context_verified') is True and entry.get('native_metrics_sha256')==proof.get('models',{}).get(model,{}).get('native_metrics_sha256') and entry.get('sha256')==hashlib.sha256((ROOT/value).read_bytes()).hexdigest()

def reading_gui_screenshot_verified(section,reading,proof):
    manifest=load_json('common_gui_evidence.json') or {}
    entry=manifest.get('readings',{}).get(section,{})
    value=reading.get(section,{}).get('screenshot')
    if value and Path(value).name in ['native_01_raw_import.png','native_02_turbo_prepared.png','native_03_positive_target.png','native_04_inputs15.png','native_05_nine_models.png','native_06_all9_completed.png','native_NB_performance.png','native_common_test_process.png']:
        return False
    if not screenshot_exists(value) or entry.get('screenshot')!=value or entry.get('test_set_id')!=proof.get('test_set_id') or entry.get('common_result_context_verified') is not True:
        return False
    if entry.get('sha256')!=hashlib.sha256((ROOT/value).read_bytes()).hexdigest():return False
    if section in ['logistic_regression','decision_tree','random_forest']:
        return entry.get('native_artifact_sha256')==reading[section].get('native_artifact_sha256')
    return entry.get('native_predictions_sha256')==proof.get('models',{}).get('Deep Learning',{}).get('native_predictions_sha256')

def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')

def write_if_absent(path, value):
    if not path.exists():
        dump(path, value)

def analyze_raw():
    source = ROOT / 'data' / 'Covid Data.csv'
    header = pd.read_csv(source, nrows=0).columns.tolist()
    raw = pd.read_csv(source, dtype={c: 'int16' for c in header if c != 'DATE_DIED'})
    prepared = raw.drop(columns=DROP)
    inputs = [c for c in prepared if c != 'PATIENT_TYPE']
    target_counts = {str(k): int(v) for k, v in raw.PATIENT_TYPE.value_counts().sort_index().items()}
    quality = {
        'source_file': 'data/Covid Data.csv', 'source_url': SOURCE_URL,
        'source_url_provenance': 'Course plan; this collector does not download or verify live website content',
        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'raw_rows': len(raw), 'raw_columns': len(raw.columns),
        'planned_prepared_rows_without_dropping_records': len(prepared),
        'planned_prepared_columns': len(prepared.columns), 'planned_input_count': len(inputs),
        'removed_columns': DROP, 'inputs': inputs, 'target': 'PATIENT_TYPE',
        'target_mapping': {'1': 'Outpatient', '2': 'Hospitalized'},
        'positive_class': 'Hospitalized', 'target_counts': target_counts,
        'hospitalized_fraction': target_counts.get('2', 0) / len(raw),
        'majority_class_accuracy_baseline': max(target_counts.values()) / len(raw),
        'blank_cells': int(raw.isna().sum().sum()),
        'exact_duplicate_raw_rows': int(raw.duplicated().sum()),
        'duplicate_prepared_profiles_including_target': int(prepared.duplicated().sum()),
        'duplicate_input_profiles_excluding_target': int(prepared[inputs].duplicated().sum()),
        'age': {'min': int(raw.AGE.min()), 'max': int(raw.AGE.max()),
                'mean': float(raw.AGE.mean()), 'median': float(raw.AGE.median())},
        'missing_code_counts': {c: {str(code): int((raw[c] == code).sum()) for code in (97, 98, 99)}
                                for c in raw.columns if c not in ('DATE_DIED', 'AGE')},
        'missing_code_interpretation': '97/98/99 are coded unavailable/not applicable responses in categorical fields; inspect the source dictionary before combining meanings. AGE 97/98/99 are valid numeric ages, not missing codes.',
        'row_policy': 'Retain anonymous profiles. Duplicate profiles do not establish duplicate people; no patient identifier is available. Do not duplicate or synthesize rows to meet the requirement.',
        'native_preparation_verified_by_collector': False,
    }
    dump(ROOT / 'raw_data_quality.json', quality)
    with (ROOT / 'missing_code_audit.csv').open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f); writer.writerow(['Attribute', 'Code97', 'Code98', 'Code99', 'AllCodedUnavailable'])
        for c, counts in quality['missing_code_counts'].items():
            writer.writerow([c, counts['97'], counts['98'], counts['99'], sum(counts.values())])
    with (ROOT / 'data_dictionary.csv').open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f); writer.writerow(['Attribute', 'ModelRole', 'PlannedType', 'Interpretation'])
        for c in raw.columns:
            role = 'Excluded' if c in DROP else 'Target' if c == 'PATIENT_TYPE' else 'Input'
            meaning = ('Admission outcome: 1 Outpatient, 2 Hospitalized; positive Hospitalized' if c == 'PATIENT_TYPE'
                       else 'Age in years; numeric values 97/98/99 remain ages' if c == 'AGE'
                       else 'Removed from pre-admission model' if c in DROP
                       else 'Categorical code; do not treat numerical code as a continuous quantity')
            writer.writerow([c, role, 'numeric' if c == 'AGE' else 'nominal', meaning])
    return quality

def create_templates():
    path = ROOT / 'native_model_comparison.template.csv'
    if not path.exists():
        with path.open('w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=['Model'] + METRICS + ['Engine', 'PositiveClass', 'TestSetID', 'Screenshot', 'Notes'])
            writer.writeheader()
            for model in MODELS:
                writer.writerow({'Model': model, 'Engine': NATIVE_ENGINE, 'PositiveClass': 'Hospitalized'})
    write_if_absent(ROOT / 'native_setup.template.json', {
        'engine': NATIVE_ENGINE, 'target': 'PATIENT_TYPE', 'positive_class': 'Hospitalized',
        'target_mapping': {'1': 'Outpatient', '2': 'Hospitalized'},
        'prepared_rows': None, 'model_rows_used': None, 'training_rows': None, 'test_rows': None,
        'test_set_id': None, 'split_method': None, 'seed': None,
        'sampling_or_license_limit': None, 'inputs': None, 'age_numeric_others_nominal': None,
        'missing_code_policy': None, 'preprocessing_fit_scope': None,
        'setup_screenshots': [], 'selected_model': None,
        'selection_reason': None, 'metric_scale': 'fraction_0_to_1', 'native_run_complete': False,
    })
    write_if_absent(ROOT / 'native_model_reading.template.json', {
        'logistic_regression': {'coefficients': [], 'screenshot': None,
            'note': 'Each entry: feature, reference_category if applicable, weight, interpretation; sign refers to Hospitalized positive class'},
        'decision_tree': {'root': None, 'path_to_leaf': [], 'leaf_prediction': None, 'screenshot': None},
        'random_forest': {'top3_importance': [], 'screenshot': None},
        'confusion_matrix': {'model': None, 'tp': None, 'fp': None, 'fn': None, 'tn': None,
                             'test_set_id': None, 'screenshot': None},
        'scoring': {'model': None, 'record_inputs': None, 'prediction': None,
                    'confidence_hospitalized': None, 'threshold': 0.50, 'screenshot': None},
    })

def load_json(name):
    p = ROOT / name
    return json.loads(p.read_text(encoding='utf-8-sig')) if p.exists() else None

def screenshot_exists(value):
    if not value:
        return False
    p = (ROOT / value).resolve()
    return p.is_relative_to(ROOT) and p.is_file() and p.suffix.lower() in ('.png', '.jpg', '.jpeg')

def collect_native():
    pending = []; errors = []; rows = []
    common_proof=load_json('common_test_verification.json')
    common_errors=validate_common_proof(common_proof)
    common_verified=not common_errors
    setup = load_json('native_setup.json'); reading = load_json('native_model_reading.json')
    path = ROOT / 'native_model_comparison.csv'
    if not path.exists():
        pending.append('No authoritative native_model_comparison.csv; common-holdout comparison remains pending.')
    else:
        rows = list(csv.DictReader(path.open(encoding='utf-8-sig')))
        required = {'Model', *METRICS, 'Engine', 'PositiveClass', 'TestSetID', 'Screenshot'}
        if rows and not required.issubset(rows[0]):
            errors.append('Native comparison schema is missing required columns.')
        models = [r.get('Model') for r in rows]
        if len(models) != len(set(models)) or set(models) - set(MODELS):
            errors.append('Duplicate or unrecognized model names; use the nine template names.')
        for row in rows:
            model = row.get('Model', '?')
            if row.get('Engine') not in [NATIVE_ENGINE,BATCH_ENGINE] or row.get('PositiveClass') != 'Hospitalized':
                errors.append(f'{model}: native engine/positive class is missing or wrong.')
            if row.get('Engine')==BATCH_ENGINE:
                if not common_verified:
                    errors.extend(common_errors)
                else:
                    source=common_proof['models'].get(model,{})
                    if row.get('TestSetID')!=common_proof['test_set_id'] or row.get('NativePerformanceFile')!=source.get('native_metrics_file') or row.get('NativePerformanceSHA256')!=source.get('native_metrics_sha256'):
                        errors.append(model+': batch provenance does not match verified native files/test set.')
                    for metric in METRICS:
                        try:
                            if abs(float(row[metric])-source['metrics'][metric])>1e-10:errors.append(model+': '+metric+' differs from verified native metric.')
                        except (ValueError,KeyError,TypeError):errors.append(model+': verified native metric comparison failed for '+metric)
            if not row.get('TestSetID'):
                pending.append(f'{model}: shared TestSetID missing.')
            for metric in METRICS:
                try:
                    value = float(row.get(metric, ''))
                    if not math.isfinite(value) or not 0 <= value <= 1:
                        raise ValueError()
                except (ValueError, TypeError):
                    pending.append(f'{model}: {metric} missing/invalid; metrics must be fractions 0 to 1.')
            if row.get('Engine')==BATCH_ENGINE and not common_gui_screenshot_verified(model,row.get('Screenshot'),common_proof or {}):
                pending.append(f'{model}: common-result GUI screenshot pending; original Default GUI images are context only.')
            elif row.get('Engine')!=BATCH_ENGINE and not screenshot_exists(row.get('Screenshot')):
                pending.append(f'{model}: actual native result screenshot missing.')
            if not row.get('Notes', '').strip():
                pending.append(f'{model}: native-result interpretation missing.')
        if len({r.get('TestSetID') for r in rows if r.get('TestSetID')}) > 1:
            errors.append('Models do not share the same declared testing set.')
        for model in set(MODELS) - set(models):
            pending.append(f'{model}: native result row missing.')
    if setup is None:
        pending.append('Native setup/row usage/split evidence missing.')
    else:
        for field in ['prepared_rows', 'model_rows_used', 'training_rows', 'test_rows', 'test_set_id',
                      'split_method', 'inputs', 'missing_code_policy', 'preprocessing_fit_scope', 'selected_model', 'selection_reason']:
            if setup.get(field) is None or setup.get(field) == '':
                pending.append('Native setup missing ' + field)
        if not setup.get('native_run_complete'):
            pending.append('Native run has not been declared complete.')
        if setup.get('engine') not in [NATIVE_ENGINE,BATCH_ENGINE] or setup.get('positive_class') != 'Hospitalized':
            errors.append('Setup native engine/positive class mismatch.')
        if setup.get('engine')==BATCH_ENGINE and not common_verified:errors.extend(common_errors)
        if rows and any(row.get('Engine')!=setup.get('engine') for row in rows):errors.append('Setup and comparison native execution provenance differ.')
        if setup.get('target') != 'PATIENT_TYPE' or setup.get('target_mapping') != {'1': 'Outpatient', '2': 'Hospitalized'}:
            errors.append('Setup target or target mapping mismatch.')
        if setup.get('metric_scale') != 'fraction_0_to_1':
            errors.append('Setup metric scale must explicitly be fraction_0_to_1.')
        if rows and setup.get('test_set_id') is not None and any(x.get('TestSetID') != setup['test_set_id'] for x in rows):
            errors.append('Setup and model results do not share the same TestSetID.')
        counts = [setup.get(k) for k in ('model_rows_used', 'training_rows', 'test_rows')]
        if all(isinstance(x, int) and x > 0 for x in counts) and counts[0] != counts[1] + counts[2]:
            errors.append('Training rows plus testing rows do not reconcile to model rows used.')
        for key in ('prepared_rows', 'model_rows_used', 'training_rows', 'test_rows'):
            if setup.get(key) is not None and (not isinstance(setup[key], int) or setup[key] <= 0):
                errors.append('Native row count must be a positive integer: ' + key)
        if isinstance(setup.get('prepared_rows'), int) and setup['prepared_rows'] < 1_000_000:
            errors.append('Prepared dataset is below the stricter one-million-row requirement.')
        if setup.get('inputs') is not None:
            expected = set(load_json('raw_data_quality.json')['inputs'])
            if set(setup['inputs']) != expected:
                errors.append('Native input set differs from the agreed 15 pre-admission inputs.')
        if setup.get('age_numeric_others_nominal') is not True:
            pending.append('Native data types not confirmed: AGE numeric, remaining fields nominal.')
        if not setup.get('setup_screenshots') or not all(screenshot_exists(x) for x in setup['setup_screenshots']):
            pending.append('Actual Predict/Target/Inputs/split setup screenshots missing.')
        if setup.get('selected_model') is not None and setup['selected_model'] not in MODELS:
            errors.append('Selected model is not one of the required nine models.')
    if rows:
        if not common_verified:
            pending.append('Actual common-holdout row ID/label/prediction verification missing or failed.')
    if reading is None:
        pending.append('Native coefficient/tree/importance/confusion/scoring evidence missing.')
    else:
        checks = [('logistic_regression', 'coefficients'), ('decision_tree', 'root'),
                  ('decision_tree', 'path_to_leaf'), ('random_forest', 'top3_importance'),
                  ('scoring', 'record_inputs'), ('scoring', 'prediction'), ('scoring', 'confidence_hospitalized')]
        for section, field in checks:
            if reading.get(section, {}).get(field) is None or reading.get(section, {}).get(field) in ('', [], 'PENDING'):
                pending.append(f'Native reading missing {section}.{field}')
        for entry in reading.get('logistic_regression', {}).get('coefficients', []):
            if not entry.get('feature') or not isinstance(entry.get('weight'), (int, float)) or not math.isfinite(entry['weight']) or not entry.get('interpretation'):
                pending.append('Logistic coefficient needs feature, finite numeric weight and interpretation.')
        for entry in reading.get('random_forest', {}).get('top3_importance', []):
            if not entry.get('feature') or not isinstance(entry.get('importance'), (int, float)) or not math.isfinite(entry['importance']) or entry['importance'] < 0:
                pending.append('Random Forest importance needs feature and finite nonnegative numeric value.')
        if not reading.get('decision_tree', {}).get('leaf_prediction'):
            pending.append('Decision Tree leaf prediction missing.')
        for section in ['logistic_regression', 'decision_tree', 'random_forest', 'confusion_matrix', 'scoring']:
            if setup and setup.get('engine')==BATCH_ENGINE and not reading_gui_screenshot_verified(section,reading,common_proof or {}):
                pending.append('Matching common-fit native GUI reading screenshot pending '+section)
            elif (not setup or setup.get('engine')!=BATCH_ENGINE) and not screenshot_exists(reading.get(section, {}).get('screenshot')):
                pending.append('Native reading screenshot missing ' + section)
        cm = reading.get('confusion_matrix', {})
        if setup and setup.get('selected_model') is not None and cm.get('model') != setup['selected_model']:
            errors.append('Confusion matrix must belong to the selected final model.')
        if setup and setup.get('test_set_id') is not None and cm.get('test_set_id') != setup['test_set_id']:
            errors.append('Confusion matrix TestSetID differs from the shared testing set.')
        counts = [cm.get(k) for k in ('tp', 'fp', 'fn', 'tn')]
        if not all(isinstance(x, int) and x >= 0 for x in counts):
            pending.append('Native confusion counts missing or invalid.')
        else:
            tp, fp, fn, tn = counts; total = sum(counts)
            recomputed = {'Accuracy': (tp+tn)/total if total else None,
                          'Precision': tp/(tp+fp) if tp+fp else 0,
                          'Recall': tp/(tp+fn) if tp+fn else 0,
                          'F1': 2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0}
            chosen = next((x for x in rows if x.get('Model') == cm.get('model')), None)
            if chosen:
                for metric, value in recomputed.items():
                    try:
                        if value is None or abs(float(chosen[metric])-value) > .002:
                            errors.append('Confusion matrix does not reconcile to ' + metric)
                    except (ValueError, KeyError): pass
            if setup and setup.get('test_rows') is not None and total != setup['test_rows']:
                errors.append('Confusion matrix count differs from declared test rows.')
        if len(reading.get('random_forest', {}).get('top3_importance', [])) != 3:
            pending.append('Random Forest needs exactly three ranked importance entries.')
        if reading.get('scoring', {}).get('threshold') != .5:
            errors.append('Scoring threshold must be the required 0.50.')
        score = reading.get('scoring', {})
        if setup and setup.get('selected_model') is not None and score.get('model') != setup['selected_model']:
            errors.append('Scoring example must use the selected final model.')
        confidence = score.get('confidence_hospitalized')
        if isinstance(confidence, (int, float)):
            if not 0 <= confidence <= 1 or not math.isfinite(confidence):
                errors.append('Positive confidence must be a finite fraction from 0 to 1.')
            elif score.get('prediction') != ('Hospitalized' if confidence >= .5 else 'Outpatient'):
                errors.append('Scoring prediction disagrees with positive confidence at threshold 0.50.')
        else:
            pending.append('Scoring needs finite numeric Hospitalized confidence.')
        if not isinstance(score.get('record_inputs'), dict) or not score['record_inputs']:
            pending.append('Scoring record_inputs must contain the actual input field values.')
        if setup and setup.get('engine')==BATCH_ENGINE:
            fit_errors=validate_same_fit_readings(reading)
            if fit_errors:errors.extend(fit_errors)
            selected=common_proof.get('models',{}).get(setup.get('selected_model'),{}) if common_proof else {}
            if any(cm.get(k)!=v for k,v in selected.get('counts',{}).items()):errors.append('Selected confusion counts differ from actual verified native predictions.')
            source=ROOT/selected.get('native_predictions_file','')
            if source.is_file():
                record=next((x for x in csv.DictReader(source.open(encoding='utf-8-sig')) if int(float(x['COMMON_ROW_ID']))==score.get('source_row_id')),None)
                if record is None:errors.append('Actual native scoring source row not found.')
                else:
                    for key,value in score.get('record_inputs',{}).items():
                        if key=='AGE':match=abs(float(record[key])-float(value))<1e-10
                        else:match=str(record.get(key))==str(value)
                        if not match:errors.append('Scoring input differs from native row: '+key)
                    if score.get('prediction')!=record['prediction(PATIENT_TYPE)'] or score.get('actual_label')!=record['PATIENT_TYPE'] or abs(float(score.get('confidence_hospitalized',-1))-float(record['confidence(Hospitalized)']))>1e-12:
                        errors.append('Scoring class/confidence differs from actual native prediction row.')
    status = {'status': 'COMPLETE_NATIVE_EVIDENCE' if not pending and not errors else 'PENDING_NATIVE_EVIDENCE',
              'pending': sorted(set(pending)), 'errors': errors,
              'native_metrics_rows': len(rows), 'models_required': MODELS,
              'quality_report_is_offline': True, 'no_proxy_metrics': True,
              'screenshots_present': sorted(str(p.relative_to(ROOT)) for p in (ROOT/'screenshots').glob('*.png'))}
    status['common_holdout_numeric_verified']=common_verified and len(rows)==9 and not errors
    status['native_execution_provenance']=setup.get('engine') if setup else None
    status['common_gui_result_photos_verified']=all(common_gui_screenshot_verified(row.get('Model'),row.get('Screenshot'),common_proof or {}) for row in rows) if rows else False
    status['same_evaluation_fit_model_artifacts_verified']=not validate_same_fit_readings(reading or {}) if setup and setup.get('engine')==BATCH_ENGINE else False
    default_audit = load_json('native_result_audit.json')
    if default_audit:
        status['default_native_checkpoint_available'] = True
        status['default_native_metrics_rows'] = len(default_audit.get('models', {}))
        status['default_native_same_test_set_requirement_met'] = default_audit.get('same_test_set_requirement_met')
        status['default_native_authoritative_for_final_comparison'] = False
    dump(ROOT / 'evidence_status.json', status)
    return status, rows, setup, reading

def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--require-complete', action='store_true'); args = parser.parse_args()
    create_templates()
    if not (ROOT/'raw_data_quality.json').exists(): analyze_raw()
    status, _, _, _ = collect_native()
    print(json.dumps(status, ensure_ascii=False, indent=2))
    if status['errors'] or (args.require_complete and status['pending']): return 2
    return 0

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8'); raise SystemExit(main())
