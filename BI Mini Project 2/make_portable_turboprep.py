"""Replace only native repository source, retaining all Turbo Prep steps verbatim."""
from pathlib import Path
import csv,hashlib,json,re,shutil,xml.etree.ElementTree as E,zipfile
R=Path(__file__).resolve().parent
native=R/'MiniProject2_TurboPrep_Native.rmp';portable=R/'MiniProject2_TurboPrep_Portable.rmp'
raw=R/'data/Covid Data.csv';local_raw=R/'Covid Data.csv'
native_bytes=native.read_bytes();text=native_bytes.decode('utf8');native_sha=hashlib.sha256(native_bytes).hexdigest()
with raw.open(encoding='utf-8-sig',newline='') as f:
 reader=csv.reader(f);columns=next(reader);sample=[next(reader) for _ in range(1000)]
assert len(columns)==len(set(columns))==21 and columns.count('DATE_DIED')==1
for row in sample:
 assert len(row)==21
 for name,value in zip(columns,row):
  if name!='DATE_DIED':int(value)
raw_sha=hashlib.sha256(raw.read_bytes()).hexdigest()
if local_raw.exists():assert hashlib.sha256(local_raw.read_bytes()).hexdigest()==raw_sha,'Existing raw copy differs; not overwriting'
else:shutil.copy2(raw,local_raw)
pattern=re.compile(r'<operator\b[^>]*\bclass="retrieve"[^>]*>.*?</operator>',re.S)
matches=list(pattern.finditer(text));assert len(matches)==1
match=matches[0];original_source=E.fromstring(match.group());assert original_source.attrib['name']=='Retrieve'
macro=E.Element('operator',activated='true',attrib={'class':'generate_macro','compatibility':'12.1.001','expanded':'true','height':'82','name':'Portable CSV Path','width':'90','x':'45','y':'170'})
functions=E.SubElement(macro,'list',key='function_descriptions')
E.SubElement(functions,'parameter',key='dataset_path',value='replace(%{process_path}, %{process_file}, "Covid Data.csv")')
reader_attrib=dict(original_source.attrib);reader_attrib['class']='read_csv'
source=E.Element('operator',reader_attrib)
params={'csv_file':'%{dataset_path}','column_separators':',','trim_lines':'true','use_quotes':'true','quotes_character':'"','first_row_as_names':'true','parse_numbers':'true','decimal_character':'.','encoding':'UTF-8','read_all_values_as_polynominal':'false','read_not_matching_values_as_missings':'false'}
for key,value in params.items():E.SubElement(source,'parameter',key=key,value=value)
meta=E.SubElement(source,'list',key='data_set_meta_data_information')
for i,name in enumerate(columns):E.SubElement(meta,'parameter',key=str(i),value=f'{name}.true.'+('polynominal' if name=='DATE_DIED' else 'integer')+'.attribute')
E.SubElement(source,'description',align='center',color='transparent',colored='false',width='126').text='Read original Covid Data.csv beside this local process; source name retained to preserve native connections.'
def fragment(node):
 E.indent(node,space='  ')
 lines=E.tostring(node,encoding='unicode').splitlines()
 return lines[0]+''.join('\r\n      '+line for line in lines[1:])
new_source=fragment(macro)+'\r\n      '+fragment(source)
portable_text=text[:match.start()]+new_source+text[match.end():]
portable.write_bytes(portable_text.encode('utf8'))
# Strict byte-fragment proof: every byte outside the original Retrieve node is retained.
assert portable_text[:match.start()]==text[:match.start()]
new_end=match.start()+len(new_source)
assert portable_text[new_end:]==text[match.end():]
old=E.fromstring(native_bytes);new=E.fromstring(portable.read_bytes())
def sig(node):return (node.tag,sorted(node.attrib.items()),(node.text or '').strip(),[sig(c) for c in node])
oldops={o.attrib['name']:o for o in old.findall('.//operator')};newops={o.attrib['name']:o for o in new.findall('.//operator')}
assert set(newops)==set(oldops)|{'Portable CSV Path'}
preserved=[]
for name,node in oldops.items():
 if name in ['Process','Retrieve']:continue
 assert sig(node)==sig(newops[name]),name
 preserved.append({'name':name,'class':node.attrib['class']})
assert [c.attrib for c in old.findall('.//connect')]==[c.attrib for c in new.findall('.//connect')]
assert not new.findall(".//operator[@class='retrieve']")
assert newops['Retrieve'].attrib['class']=='read_csv'
# Installed public registry/manual IDs and CSV metadata schema, read without modifying installation.
registry_jar=Path(r'D:\AI Studio 2026.1.1\lib\rapidminer-studio-core-12.1.1.jar')
with zipfile.ZipFile(registry_jar) as z:
 registry=E.fromstring(z.read('com/rapidminer/resources/OperatorsCore.xml'))
 keys={n.findtext('key') for n in registry.findall('.//operator')}
 assert {'read_csv','generate_macro'}<=keys
manual_jar=Path(r'D:\AI Studio 2026.1.1\lib\rapidminer-studio-reference-manual-12.1.1.jar')
with zipfile.ZipFile(manual_jar) as z:
 csvdoc=E.fromstring(z.read('core/data_access/files/read/read_csv.xml'))
 example=csvdoc.find('.//tutorialProcess/process')
 csv_example=example.find(".//operator[@class='read_csv']")
 assert csv_example.find("list[@key='data_set_meta_data_information']") is not None
 assert any(c.attrib.get('from_port')=='output' for c in example.findall('.//connect'))
assert native.read_bytes()==native_bytes
assert hashlib.sha256(raw.read_bytes()).hexdigest()==raw_sha
assert hashlib.sha256(local_raw.read_bytes()).hexdigest()==raw_sha
proof={'native_file':'MiniProject2_TurboPrep_Native.rmp','native_sha256_before':native_sha,'native_sha256_after':hashlib.sha256(native.read_bytes()).hexdigest(),'native_bytes_unchanged':True,'portable_file':portable.name,'portable_sha256':hashlib.sha256(portable.read_bytes()).hexdigest(),'only_repository_source_replaced':True,'all_other_native_source_text_verbatim':True,'preserved_operator_steps':preserved,'all_native_connections_exactly_preserved':True,'reader_operator_name_retained':'Retrieve','reader_class':'read_csv','raw_file':local_raw.name,'raw_sha256':raw_sha,'raw_copy_byte_identical':True,'numeric_column_count':20,'nominal_column':'DATE_DIED','raw_column_order':columns,'sample_1000_numeric_types_verified':True,'source_schema_grounded_in_installed_manual':True,'native_run_of_portable_copy_verified':False}
(R/'MiniProject2_TurboPrep_Portable.verify.json').write_text(json.dumps(proof,indent=2),encoding='utf8')
print(json.dumps(proof,indent=2))
