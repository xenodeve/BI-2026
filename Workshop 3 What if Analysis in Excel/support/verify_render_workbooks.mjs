import fs from 'node:fs/promises';
import {FileBlob,SpreadsheetFile} from '@oai/artifact-tool';
const root='D:/Github/BI 2026';
const w3=await SpreadsheetFile.importXlsx(await FileBlob.load(`${root}/Workshop 3 What if Analysis in Excel/Workshop3_WhatIf_Completed.xlsx`));
w3.recalculate();
const goal=w3.worksheets.getItem('Goal Seek'),scenario=w3.worksheets.getItem('Scenario'),summary=w3.worksheets.getItem('Scenario Summary');
const expected=[1438.1252333638831,1064.4839922866931,2157.1878500458247,1596.7259884300397];
const pmt=(p,d,a,y)=>a===0?p*(1-d)/(y*12):p*(1-d)*(a/12)/(1-Math.pow(1+a/12,-y*12));
const inspect=[];
let actual=summary.getRange('G6:G9').values.map(r=>r[0]);actual.forEach((v,i)=>{if(Math.abs(v-expected[i])>1e-7)throw new Error(`Base summary mismatch ${i}: ${v}`)});
scenario.getRange('B7').values=[[0.05]];
actual=summary.getRange('G6:G9').values.map(r=>r[0]);
[[200000,15],[200000,30],[300000,15],[300000,30]].forEach(([p,y],i)=>{if(Math.abs(actual[i]-pmt(p,.2,.05,y))>1e-7)throw new Error('Rate-change propagation failed')});
scenario.getRange('B7').values=[[0]];actual=summary.getRange('G6:G9').values.map(r=>r[0]);
[[200000,15],[200000,30],[300000,15],[300000,30]].forEach(([p,y],i)=>{if(Math.abs(actual[i]-p*.8/(y*12))>1e-7)throw new Error('Zero-rate boundary failed')});
scenario.getRange('B7').values=[[null]];
if(summary.getRange('G6').values[0][0]!=='ระบุ input ให้ครบ')throw new Error('Missing source-rate guard failed');
scenario.getRange('B7').values=[[.07]];
goal.getRange('B5').values=[[400000]];if(Math.abs(goal.getRange('B16').values[0][0]-9399.999874611907)>1e-7)throw new Error('Original-price PMT mismatch');
goal.getRange('B5').values=[[425531.92056985485]];w3.recalculate();
if(Math.abs(goal.getRange('B16').values[0][0]-10000)>1e-7)throw new Error('Solved-price PMT mismatch');
await fs.mkdir(`${root}/Workshop 3 What if Analysis in Excel/qa`,{recursive:true});
for(const [sheetName,range,name]of [['Goal Seek','A1:J38','file_render_goal.png'],['Goal Seek','A1:C24','file_render_goal_model.png'],['Scenario','A1:J42','file_render_scenario.png'],['Scenario Summary','A1:H17','file_render_summary.png']]){
 const blob=await w3.render({sheetName,range,scale:1.3,format:'png'});await fs.writeFile(`${root}/Workshop 3 What if Analysis in Excel/qa/${name}`,new Uint8Array(await blob.arrayBuffer()));
}
inspect.push({workbook:'WS3',readOnly_import_recalculate:true,base_payments_match:true,rate_change_propagates:true,zero_rate_boundary:true,missing_rate_guard:true,math_goal_matches:true,no_export_or_nativeGUI:true});
const w2=await SpreadsheetFile.importXlsx(await FileBlob.load(`${root}/Workshop 2 Data Presentation/Workshop2_Data_Presentation.xlsx`));w2.recalculate();
await fs.mkdir(`${root}/Workshop 2 Data Presentation/qa`,{recursive:true});
for(const [sheetName,range,name]of [['Presentation','A1:N69','file_render_presentation.png'],['Presentation','A1:N32','file_render_overview.png'],['Presentation','A33:N49','file_render_demographics.png'],['Province Ranking','A1:F18','file_render_ranking.png'],['Raw Data','A1:K12','file_render_raw.png'],['Cleansed Data','A1:K12','file_render_clean.png']]){
 const blob=await w2.render({sheetName,range,scale:1.2,format:'png'});await fs.writeFile(`${root}/Workshop 2 Data Presentation/qa/${name}`,new Uint8Array(await blob.arrayBuffer()));
}
const errors=await w2.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:50},maxChars:2500});
inspect.push({workbook:'WS2',readOnly_import_recalculate:true,error_scan:errors.ndjson,no_export_or_nativeGUI:true});
await fs.writeFile(`${root}/Workshop 3 What if Analysis in Excel/support/sdk_verification.json`,JSON.stringify(inspect,null,2));
console.log(JSON.stringify(inspect,null,2));


