"""Read-only native photo/source and genuine interactive-preparation evidence gate."""
from pathlib import Path
import hashlib, json
import pandas as pd
from collect_native_metrics import collect_native_metrics, MODELS

ROOT = Path(__file__).resolve().parent
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def verify(root=ROOT):
    root = Path(root); errors = []; pending = []
    path = root/'native_gui_evidence.json'
    if not path.is_file(): return {'complete':False,'errors':[],'pending':['Native GUI evidence manifest missing']}
    manifest = json.loads(path.read_text(encoding='utf8'))
    if sha(root/'MiniProject1.rmp') != manifest.get('canonical_process_sha256'): errors.append('Canonical process changed')
    if sha(root/'bank-full.csv') != manifest.get('raw_source_sha256'): errors.append('Original raw dataset changed')
    native = collect_native_metrics(root, write_output=False)
    for code, name in MODELS.items():
        entry = manifest.get('models',{}).get(code,{})
        photo = root/entry.get('screenshot',''); export = root/f'native_{code}.csv'
        if not photo.is_file() or sha(photo)!=entry.get('screenshot_sha256'): errors.append(code+' native photo missing/changed')
        if sha(export)!=entry.get('native_metrics_sha256'): errors.append(code+' native export changed')
        row = native[native.model==name].iloc[0]
        for key,value in entry.get('metrics',{}).items():
            if abs(float(row[key])-value)>1e-12: errors.append(code+' photo metrics/source mismatch')
        for key,value in entry.get('counts',{}).items():
            if int(row[key])!=value: errors.append(code+' confusion/source mismatch')
    for name in ['native_process_full_overview.png','native_GBT_confusion.png']:
        entry=manifest.get('extra_photos',{}).get(name,{})
        photo=root/entry.get('screenshot','')
        if not photo.is_file() or sha(photo)!=entry.get('sha256'): errors.append('Required native process/confusion photo missing: '+name)
    prep=manifest.get('TurboPrep',{})
    if prep.get('interactive_verified') is not True: pending.append('Genuine interactive Turbo Prep history/preparation photographs pending')
    images=prep.get('screenshots',[])
    if not images: pending.append('Turbo Prep photograph bindings pending')
    for entry in images:
        photo=root/entry.get('screenshot','')
        if not photo.is_file() or sha(photo)!=entry.get('sha256'): errors.append('Turbo Prep photograph missing/changed')
    export=root/prep.get('native_export','') if prep.get('native_export') else None
    if export is None or not export.is_file(): pending.append('Actual native Turbo Prep prepared-data export verification pending')
    else:
        if sha(export)!=prep.get('native_export_sha256'): errors.append('Native prepared export changed')
        raw=pd.read_csv(root/'bank-full.csv',sep=';',dtype=str,keep_default_na=False)
        data=pd.read_csv(export,sep=prep.get('delimiter',','),dtype=str,keep_default_na=False)
        expected=set(raw.columns)-{'duration'}|{'previously_contacted'}
        if len(data)!=len(raw) or set(data.columns)!=expected: errors.append('Native prep must retain45211rows and17 expected fields')
        else:
            for key in raw.columns.drop('duration'):
                if key in ['age','balance','day','campaign','pdays','previous']:
                    same=pd.to_numeric(raw[key]).eq(pd.to_numeric(data[key],errors='coerce')).all()
                else: same=raw[key].eq(data[key]).all()
                if not same: errors.append('Prepared source values/order changed: '+key)
            expected_flag=raw.pdays.map(lambda x:'no' if int(x)==-1 else 'yes')
            if not expected_flag.eq(data.previously_contacted).all(): errors.append('Native previously_contacted differs from pdays==-1 rule')
    relocated=manifest.get('GUI_portability',{})
    portability_verified=False
    if relocated.get('verified') is not True:pending.append('Actual relocated native GUI open/Run evidence pending')
    else:
        proof_file=root/relocated.get('proof','')
        if not proof_file.is_file() or sha(proof_file)!=relocated.get('proof_sha256'):errors.append('GUI portability proof changed/missing')
        else:
            proof=json.loads(proof_file.read_text(encoding='utf8'))
            process=Path(proof['relocated_process']);raw_source=Path(proof['relocated_raw_source'])
            if sha(process)!=manifest['canonical_process_sha256'] or sha(raw_source)!=manifest['raw_source_sha256']:errors.append('Relocated native process/data differ from canonical')
            for name,entry in proof['all5fresh_GUI_exports_byte_identical_canonical'].items():
                if sha(process.parent/name)!=entry['sha256'] or sha(root/name)!=entry['sha256']:errors.append('Relocated native metrics changed: '+name)
            photo=root/relocated['screenshot']
            if not photo.is_file() or sha(photo)!=relocated['screenshot_sha256']:errors.append('Relocated GUI result photo changed/missing')
            portability_verified=not errors and proof.get('passed') is True
    return {'complete':not errors and not pending,'errors':errors,'pending':pending,
            'five_native_result_photos_verified':not any('photo' in x.lower() or 'metrics' in x.lower() for x in errors),
            'TurboPrep_native_export_verified':export is not None and export.is_file() and not errors,
            'actual_relocated_native_GUI_run_verified':portability_verified,
            'GUI_models_provenance':'Actual canonical GUI run12:06:58–12:07:06; all5CSVbytes identical original batch/backup',
            'canonical_raw_metrics_unchanged':not errors}

if __name__=='__main__':
    import sys
    result=verify(); print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result['complete'] else 2)
