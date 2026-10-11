from pathlib import Path
import json, uuid, hashlib, datetime, collections, csv
import openpyxl

ROOT=Path(r'D:\Github\BI 2026')
W8=ROOT/'Workshop 8 Data Analysis Expressions (DAX)'
W9=ROOT/'Workshop 9 Dashboard'
def write(p,s):
    p.parent.mkdir(parents=True,exist_ok=True); p.write_text(s,encoding='utf-8')
def jwrite(p,x): write(p,json.dumps(x,ensure_ascii=False,indent=2))
def uid(): return uuid.uuid4().hex[:20]
def tq(s): return "'"+s.replace("'","''")+"'"
def readbook(p):
    wb=openpyxl.load_workbook(p,data_only=True)
    return {s.title:[dict(zip(list(s.values)[0],r)) for r in list(s.values)[1:] if any(v is not None for v in r)] for s in wb.worksheets}
def hashfile(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def model(folder,name,tables,relationships):
    md=folder/(name+'.SemanticModel'); definition=md/'definition'
    jwrite(md/'definition.pbism',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json','version':'4.0','settings':{}})
    jwrite(md/'.platform',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json','metadata':{'type':'SemanticModel','displayName':name},'config':{'version':'2.0','logicalId':str(uuid.uuid4())}})
    write(definition/'database.tmdl','database\n\tcompatibilityLevel: 1601\n')
    write(definition/'model.tmdl',"model Model\n\tculture: en-US\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n\tsourceQueryCulture: en-US\n\tdataAccessOptions\n\t\tlegacyRedirects\n\t\treturnErrorValuesAsNull\n\n"+''.join('ref table '+tq(t['name'])+'\n' for t in tables))
    for t in tables:
        s='table '+tq(t['name'])+'\n'
        if t.get('date'): s+='\tdataCategory: Time\n'
        for n,expr,fmt in t.get('measures',[]):
            s+='\n\tmeasure '+tq(n)+' = '+expr+'\n\t\tformatString: '+fmt+'\n'
        for c in t['cols']:
            n,typ=c[:2]; calc=c[2] if len(c)>2 else None
            s+='\n\tcolumn '+tq(n)+((' = '+calc) if calc else '')+'\n\t\tdataType: '+typ+'\n'
            if typ=='dateTime': s+='\t\tformatString: Short Date\n'
            if n in ('ProfitMargin',): s+='\t\tformatString: 0.00%\n'
            s+='\t\tsummarizeBy: none\n'
            if n=='MonthName': s+='\t\tsortByColumn: MonthNo\n'
            if n=='ชื่อประเทศ': s+='\t\tdataCategory: Country\n'
            if not calc: s+='\t\tsourceColumn: '+n+'\n'
        s+='\n\tpartition '+tq(t['name'])+' = m\n\t\tmode: import\n\t\tsource =\n'+''.join('\t\t\t'+line+'\n' for line in t['m'].splitlines())
        write(definition/'tables'/(t['name']+'.tmdl'),s)
    s=''
    for ft,fc,tt,tc in relationships:
        s+='relationship '+str(uuid.uuid4())+'\n\tfromColumn: '+tq(ft)+'.'+tq(fc)+'\n\ttoColumn: '+tq(tt)+'.'+tq(tc)+'\n\tcrossFilteringBehavior: oneDirection\n\n'
    write(definition/'relationships.tmdl',s)
    return md
def msource(path,item,kind,cols,year=False):
    p=str(path).replace('\\','/')
    pairs=', '.join('{"'+n+'", '+('type text' if typ=='string' else 'type date' if typ=='dateTime' else 'Int64.Type' if typ=='int64' else 'type number')+'}' for n,typ,*_ in cols if not _)
    s=f'let\n    Source = Excel.Workbook(File.Contents("{p}"), null, true),\n    Raw = Source{{[Item="{item}",Kind="{kind}"]}}[Data],\n'
    step='Raw'
    if kind=='Sheet': s+='    Headers = Table.PromoteHeaders(Raw, [PromoteAllScalars=true]),\n'; step='Headers'
    if item=='ทวีป': s+='    Clean = Table.Distinct(Headers, {"ชื่อทวีป"}),\n'; step='Clean'
    if item=='ประเทศ': s+='    Clean = Table.SelectRows(Headers, each [ชื่อประเทศ] <> null and Text.Lower(Text.Trim([ชื่อประเทศ])) <> "null" and Text.Trim([ชื่อประเทศ]) <> ""),\n'; step='Clean'
    if year:
        s+=f'    Years = Table.TransformColumns({step}, {{ {{"ปี", each let y=Number.From(_) in if y < 2400 then y+543 else y, Int64.Type}} }}),\n'; step='Years'
    s+='    Typed = Table.TransformColumnTypes('+step+', {'+pairs+'})\nin\n    Typed'
    return s
def field(table,col,measure=False,source=None):
    return {('Measure' if measure else 'Column'):{'Expression':{'SourceRef':({'Source':source} if source else {'Entity':table})},'Property':col}}
def proj(table,col,measure=False):
    return {'field':field(table,col,measure),'queryRef':table+'.'+col,'nativeQueryRef':col}
def lit(v):
    if isinstance(v,bool): s='true' if v else 'false'
    elif isinstance(v,str): s="'"+v.replace("'","''")+"'"
    elif isinstance(v,int): s=str(v)+'L'
    else: s=str(v)+'D'
    return {'expr':{'Literal':{'Value':s}}}
def obj(**p): return [{'properties':{k:lit(v) for k,v in p.items()}}]
def filt(table,col,values,label=None):
    return {'name':uid(),'field':field(table,col),'type':'Categorical','displayName':label or col,'filter':{'Version':2,'From':[{'Name':'s','Entity':table,'Type':0}],'Where':[{'Condition':{'In':{'Expressions':[field(table,col,source='s')],'Values':[[{'Literal':{'Value':str(v)+'L' if isinstance(v,int) else "'"+v+"'"}}] for v in values]}}}]},'howCreated':'User'}
SCHEMA='https://developer.microsoft.com/json-schemas/fabric/item/report/definition/'
class Report:
    def __init__(self,folder,name):
        self.base=folder/(name+'.Report')/'definition'; self.pages=[]; self.names=[]
    def page(self,title,context,filters=None):
        id=uid(); self.pages.append(id); self.names.append(title); p=self.base/'pages'/id
        data={'$schema':SCHEMA+'page/2.1.0/schema.json','name':id,'displayName':title,'displayOption':'FitToPage','height':1080,'width':1600}
        if filters: data['filterConfig']={'filters':filters}
        jwrite(p/'page.json',data)
        self.p=p; self.z=0
        self.text(title+' | '+context,24,12,1552,60,size=20)
        return id
    def visual(self,typ,title,roles,x,y,w,h,sort=None,filters=None,objects=None):
        id=uid(); self.z+=1
        v={'visualType':typ,'query':{'queryState':{role:{'projections':[proj(*f) for f in fields]} for role,fields in roles.items()}},'visualContainerObjects':{'title':obj(show=True,text=title,fontSize=13,bold=True,titleWrap=True),'background':[{'properties':{'color':{'solid':{'color':lit('#FFFFFF')}},'transparency':lit(0)}}]}}
        if sort: v['query']['sortDefinition']={'sort':[{'field':field(*sort[:3]),'direction':sort[3]}],'isDefaultSort':False}
        if objects: v['objects']=objects
        if typ in ('clusteredColumnChart','clusteredBarChart','lineChart','donutChart','pieChart'):
            v.setdefault('objects',{})['labels']=obj(show=True,labelDisplayUnits=0,labelPrecision=2 if 'THB' in title or '%' in title else 0,fontSize=10)
        a={'$schema':SCHEMA+'visualContainer/2.7.0/schema.json','name':id,'position':{'x':x,'y':y,'z':self.z,'width':w,'height':h,'tabOrder':self.z},'visual':v,'howCreated':'Default'}
        if filters: a['filterConfig']={'filters':filters}
        jwrite(self.p/'visuals'/id/'visual.json',a)
        return id
    def chart(self,typ,title,dim,measures,x,y,w,h,chrono=False,filters=None):
        return self.visual(typ,title,{'Category':[(*dim,False)],'Y':[(t,m,True) for t,m in measures]},x,y,w,h,sort=(*dim,False,'Ascending') if chrono else (*measures[0],True,'Descending'),filters=filters)
    def card(self,title,t,m,x,y,w,h): return self.visual('card',title,{'Values':[(t,m,True)]},x,y,w,h,objects={'labels':obj(labelDisplayUnits=0,labelPrecision=2 if 'THB' in title else 0,fontSize=25)})
    def slicer(self,title,t,c,x,y,w=490,h=95): return self.visual('slicer',title,{'Values':[(t,c,False)]},x,y,w,h,sort=(t,c,False,'Ascending'),objects={'data':obj(mode='Dropdown'),'selection':obj(singleSelect=False,selectAllCheckboxEnabled=True)})
    def text(self,text,x,y,w,h,size=13):
        id=uid();self.z+=1
        jwrite(self.p/'visuals'/id/'visual.json',{'$schema':SCHEMA+'visualContainer/2.7.0/schema.json','name':id,'position':{'x':x,'y':y,'z':self.z,'width':w,'height':h,'tabOrder':self.z},'visual':{'visualType':'textbox','objects':{'general':[{'properties':{'paragraphs':[{'textRuns':[{'value':text,'textStyle':{'fontFamily':'Segoe UI','fontSize':str(size)+'pt','color':'#17324D'}}]}]}}]}}})
    def finish(self):
        # Delete the one empty scaffold page only; all authored pages have unique IDs.
        import shutil
        for p in (self.base/'pages').iterdir():
            if p.is_dir() and p.name not in self.pages: shutil.rmtree(p)
        jwrite(self.base/'pages'/'pages.json',{'$schema':SCHEMA+'pagesMetadata/1.1.0/schema.json','pageOrder':self.pages,'activePageName':self.pages[0]})
    def navigation(self):
        self.visual('pageNavigator','',{},24,1032,1548,40,objects={'pages':obj(showHiddenPages=False,showTooltipPages=False,showByDefault=True),'layout':obj(orientation=0,cellPadding=4),'text':obj(fontSize=11)})

data8=readbook(W8/'DAX_Lab.xlsx'); prod={r['ProductID']:r for r in data8['Products']}; cust={r['CustomerID']:r for r in data8['Customers']}
sales=[]
for r in data8['Sales']:
    p=prod[r['ProductID']]; d=r['OrderDate']; price=r['Quantity']*p['UnitPrice']*(1-r['Discount']);cost=r['Quantity']*p['UnitCost']
    sales.append(dict(r,Category=p['Category'],Region=cust[r['CustomerID']]['Region'],Year=d.year,Quarter='Q'+str((d.month-1)//3+1),MonthNo=d.month,MonthName=d.strftime('%b'),SalesAmount=price,CostAmount=cost,Profit=price-cost))
def metrics(rows):
    s=sum(r['SalesAmount'] for r in rows);c=sum(r['CostAmount'] for r in rows);o=len(set(r['OrderID'] for r in rows))
    return {'Total Sales':round(s,2),'Total Cost':round(c,2),'Total Profit':round(s-c,2),'Total Orders':o,'Total Quantity':sum(r['Quantity'] for r in rows),'Average Order Value':round(s/o,2) if o else 0,'Gross Margin %':(s-c)/s if s else 0}
def group8(key):
    return {str(k):metrics([r for r in sales if r[key]==k]) for k in sorted(set(r[key] for r in sales))}
summary8={k:group8(k) for k in ['Channel','Category','Region','Year','Quarter','MonthName']}
summary8['Total']=metrics(sales)
summary8['coverage']={'minimum':min(r['OrderDate'] for r in sales).isoformat(),'maximum':max(r['OrderDate'] for r in sales).isoformat(),'rows':len(sales),'customers':len(cust),'products':len(prod)}
summary8['slicer_checks']={label:metrics(rows) for label,rows in [('Year=2025',[r for r in sales if r['Year']==2025]),('Region=Bangkok',[r for r in sales if r['Region']=='Bangkok']),('Channel=Store',[r for r in sales if r['Channel']=='Store']),('Year=2025 AND Region=Bangkok AND Channel=Store',[r for r in sales if r['Year']==2025 and r['Region']=='Bangkok' and r['Channel']=='Store'])]}
money='#,0.00 "THB"'; counts='#,0'; pct='0.00%'
cols8={'CustomersTable':[('CustomerID','string'),('CustomerName','string'),('Region','string')],'ProductsTable':[('ProductID','string'),('ProductName','string'),('Category','string'),('UnitPrice','int64'),('UnitCost','int64')],'DateTable':[('Date','dateTime'),('Year','int64'),('Quarter','string'),('MonthNo','int64'),('MonthName','string')],'SalesTable':[('OrderID','string'),('OrderDate','dateTime'),('ProductID','string'),('CustomerID','string'),('Quantity','int64'),('Discount','double'),('Channel','string'),('UnitPrice','int64','RELATED(ProductsTable[UnitPrice])'),('UnitCost','int64','RELATED(ProductsTable[UnitCost])'),('SalesAmount','double','SalesTable[Quantity] * SalesTable[UnitPrice] * (1 - SalesTable[Discount])'),('CostAmount','double','SalesTable[Quantity] * SalesTable[UnitCost]'),('Profit','double','SalesTable[SalesAmount] - SalesTable[CostAmount]'),('ProfitMargin','double','DIVIDE(SalesTable[Profit], SalesTable[SalesAmount], 0)')]}
measures8=[('Total Sales','SUM(SalesTable[SalesAmount])',money),('Total Cost','SUM(SalesTable[CostAmount])',money),('Total Profit','[Total Sales] - [Total Cost]',money),('Gross Margin %','DIVIDE([Total Profit], [Total Sales], 0)',pct),('Total Orders','DISTINCTCOUNT(SalesTable[OrderID])',counts),('Average Order Value','DIVIDE([Total Sales], [Total Orders], 0)',money),('Total Quantity','SUM(SalesTable[Quantity])',counts),('Online Sales','CALCULATE([Total Sales], SalesTable[Channel] = "Online")',money),('Store Sales','CALCULATE([Total Sales], SalesTable[Channel] = "Store")',money)]
model(W8/'offline','Workshop8_DAX',[{'name':n,'cols':c,'m':msource(W8/'DAX_Lab.xlsx',n,'Table',c),'measures':measures8 if n=='SalesTable' else [],'date':n=='DateTable'} for n,c in cols8.items()],[('SalesTable','ProductID','ProductsTable','ProductID'),('SalesTable','CustomerID','CustomersTable','CustomerID'),('SalesTable','OrderDate','DateTable','Date')])
r8=Report(W8/'offline','Workshop8_DAX')
def slicers8():
    r8.slicer('Year | All for baseline','DateTable','Year',24,80);r8.slicer('Region | All for baseline','CustomersTable','Region',548,80);r8.slicer('Channel | All for baseline','SalesTable','Channel',1072,80)
r8.page('Dashboard','Lab reconstruction | THB, orders, units | January 2025-August 2026');slicers8()
for i,(m,unit) in enumerate([('Total Sales','THB'),('Total Profit','THB'),('Total Orders','orders'),('Total Quantity','units'),('Average Order Value','THB/order')]): r8.card(m+' ('+unit+')','SalesTable',m,24+i*314,188,298,110)
for title,dim,typ,x,y in [('Sales by Channel',('SalesTable','Channel'),'clusteredColumnChart',24,320),('Sales by Category',('ProductsTable','Category'),'clusteredColumnChart',812,320),('Sales by Region',('CustomersTable','Region'),'clusteredBarChart',24,685),('Monthly Sales (months combined across years)',('DateTable','MonthName'),'lineChart',812,685)]:r8.chart(typ,title+' (THB)',dim,[('SalesTable','Total Sales')],x,y,764,340,chrono=dim[1]=='MonthName')
spec8=[(1,'Online highest sales','Channel','Total Sales','clusteredBarChart'),(2,'Computer highest sales','Category','Total Sales','clusteredColumnChart'),(3,'Bangkok highest sales','Region','Total Sales','clusteredBarChart'),(4,'Store highest orders','Channel','Total Orders','clusteredColumnChart'),(5,'Corporate highest AOV','Channel','Average Order Value','clusteredBarChart'),(6,'Accessories highest margin','Category','Gross Margin %','clusteredBarChart'),(7,'Q4 highest sales','Quarter','Total Sales','clusteredColumnChart'),(8,'July highest sales','MonthName','Total Sales','lineChart'),(9,'2026 sales exceed 2025','Year','Total Sales','clusteredColumnChart'),(10,'Same leading sales and profit channel','Channel','Total Sales','clusteredColumnChart')]
for start,name in [(0,'H1-H5'),(5,'H6-H10')]:
    r8.page(name,'Baseline: All Year / Region / Channel | 2026 ends in August');slicers8()
    for index,(h,title,dim,m,typ) in enumerate(spec8[start:start+5]):
        t='DateTable' if dim in ['Quarter','MonthName','Year'] else 'CustomersTable' if dim=='Region' else 'ProductsTable' if dim=='Category' else 'SalesTable'
        ms=[('SalesTable',m)]+([('SalesTable','Total Profit')] if h==10 else [])
        r8.chart(typ,f'H{h} {title} ({"%" if h==6 else "orders" if h==4 else "THB/order" if h==5 else "THB"})',(t,dim),ms,24+(index%2)*788,190+(index//2)*286,764,265,chrono=dim in ['Quarter','MonthName','Year'])
    r8.text('Filter context: all data by default; slicers combine with AND. H7/H8 combine matching quarters/months across years. H9 compares a full 2025 with Jan-Aug 2026; this is not full-year growth. H10 uses one THB axis; compare the actual values and ranks.',812,762,764,245)
r8.finish()
jwrite(W8/'analysis'/'validated_values.json',summary8)

data9=readbook(W9/'Foreign_tourists_En.xlsx');continents={r['รหัสทวีป']:r['ชื่อทวีป'] for r in data9['ทวีป']};countries={r['รหัสประเทศ']:r['ชื่อประเทศ'] for r in data9['ประเทศ']}; facts=[]
for row in data9['นักท่องเที่ยวต่างชาติ']:
    y=int(row['ปี']);y=y+543 if y<2400 else y
    assert 2553<=y<=2562
    facts.append(dict(row,ปี=y,Continent=continents[row['รหัสทวีป']],Country=countries[row['รหัสประเทศ']]))
assert len({(r['รหัสทวีป'],r['รหัสประเทศ'],r['ปี']) for r in facts})==len(facts)
year9={str(y):sum(r['จำนวนคน'] for r in facts if r['ปี']==y) for y in range(2553,2563)}
last9=[r for r in facts if r['ปี']==2562]
continent9={n:sum(r['จำนวนคน'] for r in last9 if r['Continent']==n) for n in continents.values()}
country9={n:sum(r['จำนวนคน'] for r in last9 if r['Country']==n) for n in sorted(set(r['Country'] for r in last9))}
summary9={'years':year9,'continents_2562':continent9,'countries_2562':country9,'Total Tourists':sum(r['จำนวนคน'] for r in facts),'Total Countries':len(set(r['รหัสประเทศ'] for r in facts)),'East Asia Share 2562':continent9['East Asia']/year9['2562'],'coverage':{'fact_rows':len(facts),'country_dimension_rows':len(countries),'years':'2553-2562 BE (2010-2019 CE)'},'slicer_checks':{'Year=2562':year9['2562'],'Year=2562 AND Continent=East Asia':continent9['East Asia'],'Year=2562 AND Country=China':country9['China'],'Country=Taiwan (all years)':sum(r['จำนวนคน'] for r in facts if r['Country']=='Taiwan')}}
cols9={'ทวีป':[('รหัสทวีป','int64'),('ชื่อทวีป','string')],'ประเทศ':[('รหัสประเทศ','int64'),('ชื่อประเทศ','string')],'นักท่องเที่ยวต่างชาติ':[('รหัสทวีป','int64'),('รหัสประเทศ','int64'),('ปี','int64'),('จำนวนคน','int64')]}
measures9=[('Total Tourists',"SUM('นักท่องเที่ยวต่างชาติ'[จำนวนคน])",'#,0 "people"'),('Total Countries',"DISTINCTCOUNT('นักท่องเที่ยวต่างชาติ'[รหัสประเทศ])",counts),('Tourist Share %',"DIVIDE([Total Tourists], CALCULATE([Total Tourists], REMOVEFILTERS('ทวีป')), 0)",pct)]
model(W9/'offline','Workshop9_Foreign_Tourists',[{'name':n,'cols':c,'m':msource(W9/'Foreign_tourists_En.xlsx',n,'Sheet',c,year=n=='นักท่องเที่ยวต่างชาติ'),'measures':measures9 if n=='นักท่องเที่ยวต่างชาติ' else []} for n,c in cols9.items()],[('นักท่องเที่ยวต่างชาติ','รหัสประเทศ','ประเทศ','รหัสประเทศ'),('นักท่องเที่ยวต่างชาติ','รหัสทวีป','ทวีป','รหัสทวีป')])
r9=Report(W9/'offline','Workshop9_Foreign_Tourists');F='นักท่องเที่ยวต่างชาติ';M=[(F,'Total Tourists')]
def slicers9(country=False):
    r9.slicer('Year (BE) | 2553-2562',F,'ปี',24,80)
    r9.slicer('Country | English names' if country else 'Continent | English names','ประเทศ' if country else 'ทวีป','ชื่อประเทศ' if country else 'ชื่อทวีป',548,80,1000)
r9.page('Overview','Original Lab content rebuilt with built-in visuals | people');slicers9()
r9.card('Total Tourists (people)',F,'Total Tourists',24,190,760,130);r9.card('Total Countries (countries)',F,'Total Countries',812,190,760,130)
r9.chart('clusteredBarChart','Total Tourists by Country (people)',('ประเทศ','ชื่อประเทศ'),M,24,340,1000,690)
r9.chart('clusteredColumnChart','Total Tourists by Year (people)',(F,'ปี'),M,1048,340,524,330,True)
r9.chart('donutChart','Total Tourists by Continent (people)',('ทวีป','ชื่อทวีป'),M,1048,695,524,335)
r9.page('Continent Analysis','Lab geography and continent comparison | people');slicers9()
r9.visual('azureMap','Tourist origins: English country names (people)',{'Category':[('ประเทศ','ชื่อประเทศ',False)],'Size':[(F,'Total Tourists',True)],'Tooltips':[(F,'Total Tourists',True)]},24,190,1000,610,objects={'bubbleLayer':obj(show=True,sizeByValue=True)})
r9.chart('clusteredBarChart','Tourists by Continent (people)',('ทวีป','ชื่อทวีป'),M,1048,190,524,610)
r9.text('Lab geography retained using built-in Azure Maps (current replacement for legacy Bing Map); country names carry Country data category. Map rendering depends on Desktop map security settings and online geocoding. Ranking chart remains available for verification.',24,830,1548,190)
r9.page('Country Analysis','Lab country comparison and pie breakdown | people');slicers9(True)
r9.chart('clusteredBarChart','Country ranking (people) | built-in replacement for Bar Chart Race',('ประเทศ','ชื่อประเทศ'),M,24,190,1000,620)
r9.chart('pieChart','Country composition (people) | built-in replacement for Drill Down Pie',('ประเทศ','ชื่อประเทศ'),M,1048,190,524,620)
r9.text('Departure from Lab custom visuals: static built-in country ranking replaces Animated Bar Chart Race; built-in Pie replaces Drill Down Pie. Year and Country slicers retain the analysis/filter context. No third-party visual dependency.',24,830,1548,190)
r9.page('04 Year Insights','H1-H2 | baseline: all continents / countries | people');slicers9()
r9.chart('clusteredColumnChart','H1 Total tourists: 2553 versus 2562 (people)',(F,'ปี'),M,24,190,764,680,True,[filt(F,'ปี',[2553,2562])])
r9.chart('lineChart','H2 Tourists by every year 2553-2562 (people)',(F,'ปี'),M,812,190,764,680,True)
r9.text('H1 compares endpoints; H2 checks every consecutive year. Baseline includes all countries/continents and no slicer selections. Years are Buddhist Era (CE + 543), used as categories and never summed.',24,900,1548,120)
r9.page('05 Continent Insights','H3-H4 | page filter Year = 2562 BE | people / %',[filt(F,'ปี',[2562],'Year = 2562 BE')]);slicers9()
r9.chart('clusteredBarChart','H3 Continent ranking in 2562 (people)',('ทวีป','ชื่อทวีป'),M,24,190,764,680)
r9.chart('clusteredBarChart','H4 Continent share in 2562 (%) | compare East Asia to 50%',('ทวีป','ชื่อทวีป'),[(F,'Tourist Share %')],812,190,764,680)
r9.text('Baseline: Year=2562; all continents and countries. Share = tourists for each continent / tourists for all continents in the same year. Changing a continent slicer keeps the denominator across continents; clear slicers before assessing H3/H4.',24,900,1548,120)
r9.page('06 Country Insights','H5 | page filter Year = 2562 BE | people',[filt(F,'ปี',[2562],'Year = 2562 BE')]);slicers9(True)
r9.chart('clusteredBarChart','H5 Country ranking in 2562 (people) | is China highest?',('ประเทศ','ชื่อประเทศ'),M,24,190,1548,720)
r9.text('Baseline: Year=2562; all countries/continents. Compare all country totals in descending order. The source contains Other country-group rows; they remain included in totals and ranking rather than silently discarded.',24,930,1548,110)
for id in r9.pages:
    r9.p=r9.base/'pages'/id
    r9.navigation()
r9.finish();jwrite(W9/'analysis'/'validated_values.json',summary9)
for w,name,summ in [(W8,'DAX_Lab.xlsx',summary8),(W9,'Foreign_tourists_En.xlsx',summary9)]:
    jwrite(w/'analysis'/'source_integrity.json',{'file':str(w/name),'sha256':hashfile(w/name),'analysis_timestamp':datetime.datetime.now().isoformat(),'read_only':True})
print(json.dumps({'WS8':summary8,'WS9':summary9},ensure_ascii=False,indent=2))
