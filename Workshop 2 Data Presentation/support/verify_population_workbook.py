from pathlib import Path
import zipfile,xml.etree.ElementTree as ET,json,hashlib,posixpath
ROOT=Path(r'D:\Github\BI 2026');FOLDER=ROOT/'Workshop 2 Data Presentation';SOURCE=FOLDER/'สถิติจำนวนประชากร_พื้นที่ ทั่วประเทศ.xlsx';TARGET=FOLDER/'Workshop2_Data_Presentation.xlsx';SUP=FOLDER/'support';SUP.mkdir(exist_ok=True)
hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in [SOURCE,TARGET]}
def read_workbook(p):
    with zipfile.ZipFile(p)as z:
        wb=ET.fromstring(z.read('xl/workbook.xml'));ns=wb.tag.split('}')[0][1:];n={'s':ns};rels={e.get('Id'):e.get('Target')for e in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))};strings=[]
        if 'xl/sharedStrings.xml'in z.namelist():
            for si in ET.fromstring(z.read('xl/sharedStrings.xml')):strings.append(''.join(t.text or ''for t in si.iter()if t.tag.rsplit('}',1)[-1]=='t'))
        result={}
        for sheet in wb.find('s:sheets',n):
            rid=next(v for k,v in sheet.attrib.items()if k.rsplit('}',1)[-1]=='id');path=rels[rid];path=path.lstrip('/')if path.startswith('/')else posixpath.normpath('xl/'+path)
            xml=ET.fromstring(z.read(path));sn=xml.tag.split('}')[0][1:];names={'s':sn};cells={}
            for c in xml.findall('.//s:sheetData/s:row/s:c',names):
                v=c.find('s:v',names);value=v.text if v is not None else None;typ=c.get('t')
                if typ=='s':value=strings[int(value)]
                elif typ=='inlineStr':value=''.join(x.text or ''for x in c.find('s:is',names).iter()if x.tag.rsplit('}',1)[-1]=='t')
                elif value is not None and typ not in ['str','e']:value=float(value)
                cells[c.get('r')]={'value':value,'formula':c.findtext('s:f',default='',namespaces=names),'type':typ}
            result[sheet.get('name')]=cells
        charts=[]
        for name in z.namelist():
            if '/charts/chart'in name and name.endswith('.xml'):
                xml=ET.fromstring(z.read(name));formulas=[e.text for e in xml.iter()if e.tag.rsplit('}',1)[-1]=='f'];assert len(formulas)>=2;charts.append({'part':name,'bindings':formulas})
        return result,charts
src,_=read_workbook(SOURCE);out,charts=read_workbook(TARGET);assert list(out)==['Presentation','Province Ranking','Raw Data','Cleansed Data'];assert len(charts)==3
compared=0
for name in ['Raw Data','Cleansed Data']:
    for address,cell in src[name].items():
        if cell['value'] is not None:assert out[name].get(address,{}).get('value')==cell['value'],(name,address,cell,out[name].get(address));compared+=1
clean=out['Cleansed Data'];records=[]
for row in range(2,79):
    name=clean[f'A{row}']['value'];vals=[clean[f'{chr(66+i)}{row}']['value']for i in range(9)];records.append({'province':name,'values':vals})
assert len(records)==77 and len({r['province']for r in records})==77
for record in records:
    v=record['values'];assert v[0]+v[1]==v[2] and v[3]+v[4]==v[5] and v[6]+v[7]==v[8] and v[2]+v[5]==v[8]
totals=[sum(r['values'][i]for r in records)for i in range(9)];assert totals[8]==65788661 and totals[6]==32031832 and totals[7]==33756829 and totals[2]==64801647 and totals[5]==987014
rank=sorted(records,key=lambda r:r['values'][8],reverse=True);assert rank[0]['values'][8]==5419484 and sum(r['values'][8]for r in rank[:10])==21178217
assert all(cell['type']!='e'for cells in out.values()for cell in cells.values())
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
proof={'result':'passed','workbook':str(TARGET),'source':str(SOURCE),'source_and_output_unchanged':True,'sha256':hashes,'sheets':list(out),'charts':charts,'source_cells_compared_exactly':compared,'unique_provinces':77,'totals':{'all':int(totals[8]),'male':int(totals[6]),'female':int(totals[7]),'Thai':int(totals[2]),'nonThai':int(totals[5])},'top_province':rank[0]['province'],'top_province_population':int(rank[0]['values'][8]),'top10_population':int(sum(r['values'][8]for r in rank[:10])),'native_Excel_GUI_verification':'pending; this is OOXML/source/formula validation'}
(SUP/'functional_verification.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(proof,ensure_ascii=False,indent=2))
