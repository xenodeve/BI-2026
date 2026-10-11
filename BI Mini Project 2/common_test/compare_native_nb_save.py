"""Read-only semantic comparison of native-dialog save and authored backup."""
from pathlib import Path
import json,hashlib,xml.etree.ElementTree as E
R=Path(__file__).resolve().parent
a=R/'model_NB_before_native_dialog_save.rmp';b=R/'model_NB.rmp'
def walk(el,path=''):
    path=path+'/'+el.tag
    if el.tag=='operator':path+='['+el.get('name','')+']'
    elif el.tag in ('parameter','list'):path+='['+el.get('key','')+']'
    elif el.tag=='connect':path+='['+str(sorted(el.attrib.items()))+']'
    yield path,dict(el.attrib),(el.text or '').strip()
    for i,c in enumerate(el):yield from walk(c,path+('['+str(i)+']' if c.tag not in ('operator','parameter','list','connect') else ''))
aa=list(walk(E.parse(a).getroot()));bb=list(walk(E.parse(b).getroot()))
# Compare named operator configuration independent of layout and element ordering.
def config(p):
    root=E.parse(p).getroot();out={}
    for op in root.iter('operator'):
        out[op.get('name')]={'class':op.get('class'),'compatibility':op.get('compatibility'),'activated':op.get('activated'),
            'parameters':{v.get('key'):v.get('value') for v in op.findall('parameter')},
            'lists':{v.get('key'):[dict(q.attrib) for q in v] for v in op.findall('list')},
            'connections':[[dict(q.attrib) for q in proc.findall('connect')] for proc in op.findall('process')]}
    return out
ca,cb=config(a),config(b);diff=[]
for name in sorted(set(ca)|set(cb)):
    if ca.get(name)!=cb.get(name):diff.append({'operator':name,'before':ca.get(name),'after':cb.get(name)})
result={'backup':str(a),'saved':str(b),'backup_sha256':hashlib.sha256(a.read_bytes()).hexdigest(),'saved_sha256':hashlib.sha256(b.read_bytes()).hexdigest(),'operators_before':len(ca),'operators_after':len(cb),'configuration_changes':diff}
(R/'native_nb_dialog_save_comparison.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps(result,indent=2))
