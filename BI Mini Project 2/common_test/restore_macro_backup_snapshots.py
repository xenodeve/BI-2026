from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parent
p=R/'empty_scoring_id_fix.json';proof=json.loads(p.read_text())
restored=[];main=[]
for record in proof['files']:
 if '_before_unquoted_macro_fix.rmp' not in record['file']:main.append(record);continue
 target=R/record['file'];source=R/record['backup']
 assert target.resolve().parent==R.resolve() and source.resolve().parent==R.resolve()
 b=source.read_bytes();assert hashlib.sha256(b).hexdigest()==record['old_sha256']
 target.write_bytes(b);assert hashlib.sha256(target.read_bytes()).hexdigest()==record['old_sha256']
 restored.append({'file':target.name,'restored_exact_prior_bytes':True,'sha256':record['old_sha256']})
proof['files']=main
proof['backup_selector_correction']={'cause':'Initial wildcard included macro snapshots; exact nine-code list now used','macro_snapshots_restored_before_handoff':restored}
p.write_text(json.dumps(proof,indent=2),encoding='utf8')
print('RESTORED',len(restored),'macro backup snapshots byte-for-byte;10mainRMPsretainminimalIDfix')
