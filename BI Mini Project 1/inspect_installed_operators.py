from pathlib import Path
import zipfile, json
base=Path(r'D:\AI Studio 2026.1.1')
out=Path(__file__).parent/'operator-evidence'
out.mkdir(exist_ok=True)
hits=[]
for jar in base.rglob('*.jar'):
 try:
  with zipfile.ZipFile(jar) as z:
   for name in z.namelist():
    if name.endswith(('.xml','.rmp','.properties')) and any(k in name.lower() for k in ['operators','naive','logistic','gradient','read_csv','split_data','random_forest','decision_tree','performance_binominal','nominal_to_numerical','relative']):
     if name.endswith('.properties') and 'operators' not in name: continue
     blob=z.read(name)
     if name.endswith('.xml') or name.endswith('.rmp'):
      target=out/(jar.stem+'__'+name.replace('/','__'))
      target.write_bytes(blob)
     hits.append({'jar':str(jar),'name':name,'bytes':len(blob)})
 except zipfile.BadZipFile: pass
(out/'inventory.json').write_text(json.dumps(hits,indent=2),encoding='utf8')
print(json.dumps(hits[:80],indent=2))
