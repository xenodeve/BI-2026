import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {Presentation,PresentationFile} from '@oai/artifact-tool';
const skill='C:/Users/xenod/.codex/plugins/cache/openai-primary-runtime/presentations/26.1007.11041/skills/presentations';
process.env.RUNTIME_NODE_MODULES='C:/Users/xenod/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const {finalizePresentation,applyPresentationChartFont}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const folder=path.resolve(import.meta.dirname,'..');
const data=JSON.parse(await fs.readFile(path.join(import.meta.dirname,'presentation_data.json'),'utf8'));
const m=data.verification;
const presentation=Presentation.create({slideSize:{width:1280,height:720}});
const dark='#152B3B',teal='#197369',muted='#5F6E79',orange='#C3732B';
const label=s=>({'All':'Total','รถจักรยานยนต์':'Motorcycles','รถยนต์นั่งส่วนบุคคลไม่เกิน 7 คน':'Passenger cars ≤7 seats','รถยนต์บรรทุกส่วนบุคคล':'Private trucks'}[s]??s);
const num=(v,dec=2)=>Number(v).toLocaleString('en-US',{minimumFractionDigits:dec,maximumFractionDigits:dec});
const chartValue=v=>Number(Number(v).toFixed(2));
function text(slide,value,left,top,width,height,size=27,bold=false,color=dark){
  const shape=slide.shapes.add({geometry:'textbox',position:{left,top,width,height},fill:'none',line:{fill:'none',width:0}});
  shape.text=value;shape.text.style={fontSize:size,typeface:'Arial',bold,color,verticalAlignment:'top',autoFit:'none',wrap:'square',insets:0};return shape;
}
function slide(title,notes=''){
  const s=presentation.slides.add();s.background.fill='#FAFBFC';
  text(s,title,64,42,1150,76,44,true);
  text(s,`${presentation.slides.items.length}`,1180,676,40,22,16,false,muted);
  s.speakerNotes.text=`Sources: supplied DLT raw CSV (SHA256 ${m.source_sha256}), computed verification.json, ModelComparison.csv and HypothesisEvidence.csv. DLT catalog: ${m.source_url}. Course requirements: BI_Term_Project_2569.pdf pages 1–2. ${notes}`;
  return s;
}
function table(s,headers,rows,top=150,height=440,widths=null,size=23){
  const t=s.tables.add({rows:rows.length+1,columns:headers.length,left:64,top,width:1152,height,
    ...(widths?{columnWidths:widths}:{}),values:[headers,...rows]});
  t.cells.block({row:0,column:0,rowCount:rows.length+1,columnCount:headers.length}).assign({
    textStyle:{typeface:'Arial',fontSize:size,color:dark},margins:{left:12,right:12,top:9,bottom:9},anchor:'middle'});
  t.cells.block({row:0,column:0,rowCount:1,columnCount:headers.length}).assign({fill:'#E8EEF2',textStyle:{bold:true,typeface:'Arial',fontSize:size,color:dark}});
  t.borders.assign({style:'solid',fill:'#D8E0E5',width:1});
  for(let row=1;row<=rows.length;row++)t.cells.block({row,column:0,rowCount:1,columnCount:headers.length}).fill=row%2?'#FFFFFF':'#F4F7F9';
  return t;
}
function note(s,value,top=621){text(s,value,64,top,1120,48,20,false,muted)}
function chart(s,type,config){const c=s.charts.add(type,config);applyPresentationChartFont(c,{fontFamily:'Arial'});return c}

// 1 Cover
let s=slide('DLT brand and vehicle type analysis');
text(s,'A proposed decision support project',64,167,1100,70,52,true,teal);
text(s,'Measured brand composition and seven independent forecast series',64,268,1040,105,31);
text(s,'Business Intelligence Term Project\n11 October 2026',64,430,1020,85,28,false,muted);
text(s,'Group members, topic uniqueness and instructor approval pending',64,577,1110,54,25,false,orange);

// 2 Business question
s=slide('Brand and type detail changes the planning question');
text(s,'72.38%',64,150,540,126,91,true,teal);
text(s,'Motorcycle share of registrations\nin the complete years 2024–2025',64,292,620,113,31);
text(s,'A distributor needs category-specific evidence before translating national registrations into planning assumptions.',715,163,500,210,32);
text(s,'Compare brands within vehicle type.\nEvaluate forecast error for each segment.\nAdd inventory, sales and lead times before ordering.',715,410,500,192,28);
note(s,'Registration counts are a market-activity proxy. The source contains no transaction prices or inventory.');

// 3 Raw quality
s=slide('Source coverage and data quality');
table(s,['Check','Measured result'],[
  ['Original snapshot','68,398 rows and 9 columns'],['Observed periods','49 months. December 2023 missing'],
  ['Partial February 2026','6 source records and 18 registrations. Excluded'],['Missing model names','623 rows retained for brand/type totals'],
  ['Exact and natural-key duplicates','0'],['Complete modeling period','25 consecutive months. January 2024–January 2026']
],148,420,[420,732]);
note(s,'Public source: Department of Land Transport. Preserved raw snapshot and SHA256 support repeatable analysis.');

// 4 ETL and facts
s=slide('ETL reconciles source rows and monthly facts');
table(s,['Step','Rows'],[
  ['Original raw data','68,398'],['Complete analysis window','35,805'],['Date × brand × vehicle type fact','5,712'],
  ['Actual registration count','5,007,659 vehicles'],['Dimensions','421 brands and 16 vehicle types']
],146,365,[830,322]);
text(s,'FactRegistrations connects to Date, Brand and VehicleType. A separate Series dimension controls forecasts and model metrics.',64,552,1150,82,27);

// 5 Hypotheses
s=slide('Six hypotheses have measured outcomes');
table(s,['Hypothesis','Evidence','Outcome'],[
  ['Motorcycles exceed half of registrations','72.3830%','Supported'],
  ['Honda is the largest brand overall','61.7623% share','Supported'],
  ['Passenger car registrations decline in 2025','Actual change +3.9995%','Not supported'],
  ['Three brands exceed 70% of registrations','81.4304%','Supported'],
  ['January 2026 exceeds January 2025','+9.7903%','Supported'],
  ['Selected total method improves on Naive test MAE','11.0030% reduction','Supported']
],144,445,[624,298,230],22);
note(s,'Descriptive findings on the supplied snapshot. These results do not establish causation.');

// 6 Brand composition
s=slide('Honda leads the overall registration mix');
chart(s,'bar',{position:{left:65,top:142,width:1145,height:443},categories:data.top_brands.map(r=>r[0]),
  series:[{name:'Registrations 2024–2025',values:data.top_brands.map(r=>r[1]),fill:teal}],
  barOptions:{direction:'bar',grouping:'clustered',gapWidth:45},hasLegend:false,
  xAxis:{textStyle:{fontSize:24},majorGridlines:null},yAxis:{numberFormatCode:'#,##0',textStyle:{fontSize:20}},
  dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'#,##0',textStyle:{fontSize:20}}});
note(s,'Overall brand rankings mix motorcycles and passenger cars. A vehicle-type filter is essential for product decisions.');

// 7 Time safe modeling
s=slide('Validation selects the method before test evaluation');
text(s,'Train 12 months\nApr 2024–Mar 2025',64,148,370,100,31,true,teal);
text(s,'Validation 5 months\nApr–Aug 2025',465,148,365,100,31,true,teal);
text(s,'Test 5 months\nSep 2025–Jan 2026',865,148,350,100,31,true,orange);
table(s,['Method','Fixed setup'],[
  ['Linear Regression','Training-only scaling'],['Ridge Regression','Training-only scaling. Alpha 10'],
  ['Random Forest','200 trees. Depth 3. Leaf minimum 2. Seed 42'],['Gradient Boosting','200 rounds. Rate .03. Depth 2. Seed 42'],
  ['Naive baseline','Previous observed month. No model fit']
],281,286,[380,772],23);
note(s,'Lag1–Lag3, month sine/cosine and calendar index. Rolling one-month-ahead evaluation. No shuffle.');

// 8 all total methods
s=slide('The total method wins validation with MAE 9,436.51');
chart(s,'bar',{position:{left:65,top:145,width:1145,height:429},categories:data.total_models.map(r=>r.Model),
  series:[{name:'Validation MAE',values:data.total_models.map(r=>chartValue(r.ValidationMAE)),fill:teal},
          {name:'Held-out test MAE',values:data.total_models.map(r=>chartValue(r.TestMAE)),fill:orange}],
  barOptions:{direction:'bar',grouping:'clustered',gapWidth:50},hasLegend:true,legend:{position:'bottom',textStyle:{fontSize:22}},
  xAxis:{textStyle:{fontSize:22}},yAxis:{numberFormatCode:'#,##0',textStyle:{fontSize:20}}});
note(s,'Gradient Boosting remains selected. Random Forest has lower test MAE, which cannot be used to change selection.');

// 9 series outcomes
s=slide('Each segment retains its validation winner');
table(s,['Series','Method','Test MAE','Test R²','Feb 2026 forecast'],m.selected_models.map((r,i)=>[
  label(r.SegmentName),r.Model,num(r.TestMAE),num(r.TestR2,4),num(m.future_forecasts[i].ForecastRegistrations,0)
]),143,452,[300,270,185,150,247],22);
note(s,'Forecast series overlap. The total already contains the brand and vehicle-type series, so the seven forecasts cannot be added.');

// 10 actual forecast total
s=slide('The January peak creates a large total forecast error');
const totalForecast=data.total_forecast.filter(r=>r.DatasetSegment==='Test');
chart(s,'line',{position:{left:65,top:143,width:1145,height:435},categories:totalForecast.map(r=>r.Date.slice(2,7)),
  series:[
    {name:'Actual',values:totalForecast.map(r=>Number(r.ActualRegistrations)),smooth:false,line:{fill:dark,width:3},marker:{symbol:'circle',size:6,fill:dark}},
    {name:'Test prediction',values:totalForecast.map(r=>chartValue(r.ForecastRegistrations)),smooth:false,line:{fill:teal,width:3},marker:{symbol:'circle',size:7,fill:teal}}
  ],lineOptions:{smooth:false},displayBlanksAs:'gap',hasLegend:true,legend:{position:'bottom',textStyle:{fontSize:22}},
  xAxis:{textStyle:{fontSize:21}},yAxis:{min:150000,max:260000,numberFormatCode:'#,##0',textStyle:{fontSize:21},majorGridlines:{fill:'#E1E7EB',width:1}}});
note(s,'Five held-out months. January error 36,915.32. February forecast 227,934.33 with actual blank.');

// 11 errors
s=slide('Large errors identify segments needing investigation');
table(s,['Series','Month','Actual','Prediction','Absolute error'],data.worst_errors.map(r=>[
  label(r.SegmentName),r.Date.slice(0,7),num(r.ActualRegistrations,0),num(r.PredictedRegistrations),num(r.AbsoluteError)
]),151,319,[330,190,180,220,232],23);
text(s,'Only five test months support these error estimates. Lag/calendar features do not explain the cause of the January jump.',64,511,1136,101,30);

// 12 One actual native overview. Five main page captures are in the PDF appendix.
s=slide('Native Desktop pages and DAX agree with the results',
  'Actual native Desktop screenshot: BI Term Project/screenshots/Executive Summary.png. Native Full refresh and DAX receipts are copied in native_evidence. Totals and all7series match measured outputs. Direct page captures do not prove user-triggered parameter switching, hover tooltip, drillthrough or Back. Saved PBIX close/reopen and native Word pagination remain pending.');
const overviewBytes=await fs.readFile(path.join(folder,'screenshots','Executive Summary.png'));
s.images.add({blob:overviewBytes.buffer.slice(overviewBytes.byteOffset,overviewBytes.byteOffset+overviewBytes.byteLength),
  contentType:'image/png',alt:'Actual Power BI Desktop Executive Summary with measured complete-period counts',fit:'contain',
  position:{left:64,top:123,width:1152,height:535.7}});
text(s,'Full refresh and all 7 series pass native DAX. Saved PBIX and user interactions remain pending.',64,668,1080,26,17,false,muted);

// 13 decision and pending work
s=slide('Segment evidence guides planning');
text(s,'Motorcycles dominate overall registrations.\nPassenger cars grew 4.00% in 2025.\nForecast reliability differs across segments.',64,152,1120,211,37,true,teal);
text(s,'Business use needs inventory, sales, prices and supplier lead times.\nMore history and rolling validation are needed before stock commitments.',64,401,1120,107,28);
text(s,'Before submission: actual group identities and topic approval, saved PBIX reopen, real feature interactions and the final demonstration.',64,565,1120,82,26,false,orange);

const previewDir=path.join(import.meta.dirname,'previews');await fs.mkdir(previewDir,{recursive:true});
for(const [i,s] of presentation.slides.items.entries()){
  const png=await presentation.export({slide:s,format:'png',scale:1});
  await fs.writeFile(path.join(previewDir,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));
}
const candidatePath=path.join(import.meta.dirname,'candidate.pptx');
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);
const finalPath=path.join(folder,'presentation','DLT_Brand_Type_Project_Proposal.pptx');
const receiptPath=path.join(import.meta.dirname,'validation-native-overview.json');
const result=await finalizePresentation({workspaceDir:folder,candidatePath,finalPath,
  pythonExecutable:'C:/Users/xenod/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',
  integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...[3,4,5,7,9,11].flatMap(number=>['--require-native-table-slide',String(number)])],
  explicitTotalSlideCount:13,requiredNativeTableOwnerSlides:[3,4,5,7,9,11],requiredNativeChartOwnerSlides:[6,8,10],
  materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,receiptPath});
console.log(JSON.stringify({finalPath,result},null,2));
