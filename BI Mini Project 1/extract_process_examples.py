from pathlib import Path
import xml.etree.ElementTree as ET,zipfile
b=Path(__file__).parent/'operator-evidence'
names=['read_csv','nominal_to_numerical','split_data','performance_binominal_classification','parallel_decision_tree','parallel_random_forest','gradient_boosted_trees','logistic_regression']
for name in names:
 fs=[p for p in b.glob('*.xml') if p.name.endswith('__'+name+'.xml') and 'multi_language' not in p.name]
 for p in fs:
  t=ET.parse(p)
  proc=t.find('.//tutorialProcess/process')
  if proc is None: proc=t.find('.//process')
  if proc is not None:
   (b/(name+'-'+p.name.split('__')[0]+'.rmp')).write_bytes(ET.tostring(proc,encoding='utf8',xml_declaration=True))
   print(name,p.name,'PARAMETERS',[(x.attrib.get('key'),x.attrib.get('value')) for x in proc.findall('.//operator/parameter')][:40])
   print('CLASSES',[(x.attrib.get('class'),x.attrib.get('name')) for x in proc.findall('.//operator')])
   print('PORTS',[x.attrib for x in proc.findall('.//connect')][:20])
# needed extra public manuals
with zipfile.ZipFile(r'D:\AI Studio 2026.1.1\lib\rapidminer-studio-reference-manual-12.1.1.jar') as z:
 for name in ['generate_attributes','normalize','set_role','select_attributes','apply_model','multiply','extract_macro','generate_macro']:
  files=[p for p in z.namelist() if p.endswith('/'+name+'.xml')]
  for p in files:
   (b/('extra-'+name+'.xml')).write_bytes(z.read(p))
print('Extra manuals extracted')
