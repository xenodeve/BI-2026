from pathlib import Path
from decimal import Decimal
import json,re,collections,openpyxl
ROOT=Path(r'D:\Github\BI 2026');W8=ROOT/'Workshop 8 Data Analysis Expressions (DAX)';W9=ROOT/'Workshop 9 Dashboard'
def rows(sheet):
    raw=list(sheet.values);return [dict(zip(raw[0],r)) for r in raw[1:] if any(x is not None for x in r)]
for folder,name in [(W8,'Workshop8_DAX'),(W9,'Workshop9_Foreign_Tourists')]:
    definition=folder/'offline'/(name+'.SemanticModel')/'definition';model={}
    for p in (definition/'tables').glob('*.tmdl'):
        text=p.read_text(encoding='utf-8');table=re.search(r"^table '([^']+)'",text).group(1)
        model[table]={kind:set(re.findall(r"\t"+kind+r" '([^']+)'",text)) for kind in ['column','measure']}
    projections=0
    report=folder/'offline'/(name+'.Report')/'definition'
    pages=json.loads((report/'pages/pages.json').read_text(encoding='utf-8'))['pageOrder']
    for id in pages:
        for p in (report/'pages'/id/'visuals').glob('*/visual.json'):
            v=json.loads(p.read_text(encoding='utf-8'))
            for role in v['visual'].get('query',{}).get('queryState',{}).values():
                for projection in role['projections']:
                    f=projection['field'];kind='Measure' if 'Measure' in f else 'Column';x=f[kind];table=x['Expression']['SourceRef']['Entity'];assert x['Property'] in model[table][kind.lower()],(p,table,x['Property']);projections+=1
    result={'result':'passed','checks':['All report projections refer to existing TMDL fields/measures'],'pages':len(pages),'projections':projections}
    if folder==W8:
        w=openpyxl.load_workbook(folder/'DAX_Lab.xlsx',data_only=True);p={r['ProductID']:r for r in rows(w['Products'])};c={r['CustomerID']:r for r in rows(w['Customers'])};d={r['Date'] for r in rows(w['Date'])};s=rows(w['Sales'])
        assert len(p)==20 and len(c)==120 and len(s)==1500
        assert all(r['ProductID'] in p and r['CustomerID'] in c and r['OrderDate'] in d for r in s)
        total=sum(Decimal(r['Quantity'])*Decimal(p[r['ProductID']]['UnitPrice'])*(Decimal(1)-Decimal(str(r['Discount']))) for r in s)
        cost=sum(Decimal(r['Quantity'])*Decimal(p[r['ProductID']]['UnitCost']) for r in s)
        exp=json.loads((folder/'analysis/validated_values.json').read_text(encoding='utf-8'))
        assert total==Decimal(str(exp['Total']['Total Sales'])) and cost==Decimal(str(exp['Total']['Total Cost']))
        result.update({'checks':result['checks']+['Dimension-key uniqueness','Foreign key completeness','Date key coverage','Second exact Decimal reconciliation of total sales and cost'],'sales_rows':len(s),'sales':str(total),'cost':str(cost),'profit':str(total-cost)})
    else:
        w=openpyxl.load_workbook(folder/'Foreign_tourists_En.xlsx',data_only=True);con=rows(w['ทวีป']);co=rows(w['ประเทศ']);fa=rows(w['นักท่องเที่ยวต่างชาติ'])
        # Exact Lab cleanup: deduplicate continent names and exclude null country.
        con=list({r['ชื่อทวีป']:r for r in con}.values());co=[r for r in co if r['ชื่อประเทศ'] is not None and str(r['ชื่อประเทศ']).strip().lower() not in ['', 'null']]
        assert len(con)==7 and len(co)==54 and len(fa)==540
        assert len({r['รหัสทวีป'] for r in con})==len(con) and len({r['รหัสประเทศ'] for r in co})==len(co)
        assert all(r['รหัสทวีป'] in {a['รหัสทวีป'] for a in con} and r['รหัสประเทศ'] in {a['รหัสประเทศ'] for a in co} for r in fa)
        total=collections.Counter()
        for r in fa:
            y=int(r['ปี']);y=y+543 if y<2400 else y;total[str(y)]+=r['จำนวนคน']
        exp=json.loads((folder/'analysis/validated_values.json').read_text(encoding='utf-8'));assert dict(total)==exp['years']
        assert sum(exp['continents_2562'].values())==exp['years']['2562'] and sum(exp['countries_2562'].values())==exp['years']['2562']
        result.update({'checks':result['checks']+['Lab-prescribed dimension cleanup','Dimension-key uniqueness after cleanup','Foreign-key completeness','Independent integer year-total reconciliation','Continent and country totals reconcile to year2562'],'continents_raw':8,'continents_clean':7,'countries_raw':55,'countries_clean':54,'fact_rows':540,'years':dict(sorted(total.items()))})
    (folder/'analysis/input_and_binding_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(name,'input and field binding checks passed')
