"""Chart real official native batch exports using bundled ReportLab and Poppler."""
from pathlib import Path
import csv, hashlib, json, sys, subprocess, zipfile
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import HorizontalBarChart
from reportlab.graphics import renderPDF
from PIL import Image as PILImage

OUT=Path(__file__).resolve().parent
PROJECT=OUT.parent
sys.path.insert(0,str(PROJECT))
from collect_evidence import validate_common_proof, validate_same_fit_readings, MODELS, METRICS

POPPLER=Path(r'C:\Users\xenod\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe')
BLUE='#214d78';TEAL='#187b73';INK='#203040';GRAY='#66727e';ORANGE='#c6762b';PALE='#edf2f5'
FULL={'GLM':'Generalized Linear Model','GBT':'Gradient Boosted Trees','SVM':'Support Vector Machine'}
CODES={'Naive Bayes':'NB','GLM':'GLM','Logistic Regression':'LR','Fast Large Margin':'FLM','Deep Learning':'DL','Decision Tree':'DT','Random Forest':'RF','GBT':'GBT','SVM':'SVM'}
W,H=1008,576
pdfmetrics.registerFont(TTFont('Chart',r'C:\Windows\Fonts\tahoma.ttf'))
pdfmetrics.registerFont(TTFont('ChartBold',r'C:\Windows\Fonts\tahomabd.ttf'))

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def text(c,x,y,value,size=13,color=INK,bold=False,align='left'):
    c.setFont('ChartBold' if bold else 'Chart',size);c.setFillColor(colors.toColor(color))
    getattr(c,{'left':'drawString','right':'drawRightString','center':'drawCentredString'}[align])(x,y,str(value))
def lines(c,x,y,values,size=12,color=GRAY,leading=20):
    for i,value in enumerate(values):text(c,x,y-i*leading,value,size,color)
def new_figure(filename,title,detail):
    vector=OUT/'vector_sources'/filename.replace('.png','.pdf');c=canvas.Canvas(str(vector),pagesize=(W,H))
    text(c,45,530,title,25,bold=True)
    text(c,45,493,'OFFICIAL AI STUDIO BATCH RESULTS | Common test: 12,000 | Positive: Hospitalized',13,BLUE)
    text(c,45,466,detail,11)
    text(c,45,34,'Chart of saved native exports; NOT an AI Studio GUI screenshot.',12)
    text(c,45,14,'Pipeline train: 18,000 | Modeling sample: 30,000 | Prepared source: 1,048,575 | No new model run',10)
    return c,vector

def hbars(c,labels,values,x,y,width,height,minimum=0,maximum=1,step=.2,fmt='%.4f',font=13,value_column=None,manual_categories=False):
    d=Drawing(W,H);b=HorizontalBarChart();b.x=x;b.y=y;b.width=width;b.height=height
    b.data=[list(values)[::-1]];b.categoryAxis.categoryNames=list(labels)[::-1]
    b.valueAxis.valueMin=minimum;b.valueAxis.valueMax=maximum;b.valueAxis.valueStep=step
    b.bars[0].fillColor=colors.HexColor(TEAL);b.bars[0].strokeColor=None
    b.categoryAxis.labels.fontName='Chart';b.categoryAxis.labels.fontSize=font
    b.valueAxis.labels.fontName='Chart';b.valueAxis.labels.fontSize=11
    b.valueAxis.strokeColor=colors.HexColor(GRAY);b.categoryAxis.strokeColor=None
    b.barLabels.fontName='ChartBold';b.barLabels.fontSize=font;b.barLabelFormat=fmt if value_column is None else None
    if manual_categories:b.categoryAxis.visibleLabels=0
    b.barLabels.nudge=8
    b.barWidth=24;b.groupSpacing=18;b.barSpacing=4
    d.add(b);renderPDF.draw(d,c,0,0)
    if value_column is not None:
        for i,(label,value) in enumerate(zip(labels,values)):
            yy=y+height*(len(values)-i-.5)/len(values)
            text(c,value_column,yy-4,fmt%value,font,bold=True,align='right')
            if manual_categories:text(c,x-12,yy-4,label,font,align='right')

def finish(c,vector,filename,items,caption,sources,values):
    c.showPage();c.save()
    subprocess.run([str(POPPLER),'-r','144','-singlefile','-png',str(vector),str((OUT/filename).with_suffix(''))],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,creationflags=0x08000000)
    items.append({'file':filename,'vector_source':str(vector.relative_to(OUT)),'caption':caption,'sources':sources,'displayed_values':values,'sha256':sha(OUT/filename)})

def model_figure(name,row,proof,items,index):
    filename=f'{index:02d}_{CODES[name]}_native_batch_metrics.png'
    c,v=new_figure(filename,FULL.get(name,name),'Five metrics on the same full holdout; values are fractions from 0 to 1.')
    values=[float(row[m]) for m in METRICS];hbars(c,METRICS,values,130,116,435,302)
    text(c,344,74,'Native performance value (0 to 1)',12,GRAY,align='center')
    text(c,670,410,'Actual native test counts',17,bold=True)
    counts=proof['models'][name]['counts']
    for i,(key,label) in enumerate([('tp','True positives'),('fp','False positives'),('fn','False negatives'),('tn','True negatives')]):
        text(c,670,357-i*54,label,13);text(c,945,357-i*54,f"{counts[key]:,}",20,bold=True,align='right')
    lines(c,670,133,['Hospitalized: 2,289','Outpatient: 9,711'],12)
    if name=='Deep Learning':text(c,670,78,'Selected in this comparison',12,TEAL,bold=True)
    finish(c,v,filename,items,FULL.get(name,name)+' native metrics',[row['NativePerformanceFile'],row['NativePredictionFile']],{m:float(row[m]) for m in METRICS}|counts)

def confusion(reading,proof,items):
    cm=reading['confusion_matrix'];filename='10_DL_native_batch_confusion.png'
    c,v=new_figure(filename,'Deep Learning confusion matrix','Rows are ACTUAL classes; columns are PREDICTED classes. Hospitalized confidence threshold: 0.50.')
    x,y,size=155,125,152
    cells=[(0,1,'TN',cm['tn'],BLUE),(1,1,'FP',cm['fp'],PALE),(0,0,'FN',cm['fn'],PALE),(1,0,'TP',cm['tp'],TEAL)]
    for col,row,label,value,fill in cells:
        c.setFillColor(colors.HexColor(fill));c.setStrokeColor(colors.white);c.rect(x+col*size,y+row*size,size,size,fill=1,stroke=1)
        color='white' if fill in [BLUE,TEAL] else INK;text(c,x+col*size+size/2,y+row*size+94,label,17,color,bold=True,align='center');text(c,x+col*size+size/2,y+row*size+58,f'{value:,}',29,color,bold=True,align='center')
    text(c,230,102,'Outpatient',13,align='center');text(c,382,102,'Hospitalized',13,align='center');text(c,307,76,'Predicted class',12,GRAY,align='center')
    text(c,145,351,'Outpatient',12,align='right');text(c,145,199,'Hospitalized',12,align='right');text(c,75,442,'Actual class',11,GRAY)
    text(c,625,412,'Verified 12,000-row holdout',17,bold=True)
    for i,key in enumerate(METRICS):text(c,625,358-i*38,f"{key}: {proof['models']['Deep Learning']['metrics'][key]:.4f}",17)
    lines(c,625,120,['False negatives: 677 of 2,289','actual Hospitalized records.','The four cells sum to 12,000.'],12)
    finish(c,v,filename,items,'Selected Deep Learning native confusion matrix',[cm['native_source'],cm['native_metrics_source']],cm)

def scoring(reading,items):
    s=reading['scoring'];filename='11_DL_native_batch_scoring.png'
    c,v=new_figure(filename,'Deep Learning native scoring example','Audit row 348: actual Hospitalized; predicted Hospitalized. Audit ID is excluded from inputs.')
    vals=[s['confidence_hospitalized'],s['confidence_outpatient']];hbars(c,['Hospitalized','Outpatient'],vals,160,235,380,145,fmt='%.6f')
    c.setStrokeColor(colors.HexColor(ORANGE));c.setDash(5,4);c.line(350,223,350,394);c.setDash()
    text(c,350,407,'Hospitalized threshold 0.50',11,ORANGE,align='center')
    text(c,355,199,'Native exported confidence',12,GRAY,align='center')
    text(c,85,139,f'{vals[0]:.6f} >= 0.50  =>  Hospitalized',18,TEAL,bold=True)
    text(c,680,425,'Actual exported inputs',16,bold=True)
    for i,(key,value) in enumerate(s['record_inputs'].items()):text(c,680,395-i*20,f'{key}: {value:g}' if isinstance(value,(int,float)) else f'{key}: {value}',11)
    finish(c,v,filename,items,'One actual native scored row and threshold interpretation',[s['native_source']],s)

def importance(reading,items):
    rf=reading['random_forest'];weights=list(csv.DictReader((PROJECT/rf['native_artifact']).open(encoding='utf-8-sig')));weights.sort(key=lambda r:float(r['Weight']),reverse=True)
    filename='12_RF_native_gain_ratio_importance.png';c,v=new_figure(filename,'Random Forest native feature importance','Genuine learner weights output | criterion: gain_ratio | 15 normalized weights sum to 1.')
    hbars(c,[r['Attribute'] for r in weights],[float(r['Weight']) for r in weights],225,111,550,321,maximum=.55,step=.1,fmt='%.6f',font=11,value_column=925)
    text(c,925,443,'Native weight',11,GRAY,align='right')
    text(c,520,77,'Native normalized importance weight',12,GRAY,align='center')
    finish(c,v,filename,items,'Genuine evaluated-fit Random Forest native gain-ratio importance',[rf['native_artifact']],weights)

def coefficients(reading,items):
    lr=reading['logistic_regression'];filename='13_LR_native_coefficients.png'
    c,v=new_figure(filename,'Logistic Regression native coefficients','Evaluated common fit: base logit for Hospitalized. Final scores also use native calibration/cost wrappers.')
    labels=[r['feature'] for r in lr['coefficients']];values=[r['weight'] for r in lr['coefficients']]
    hbars(c,labels,values,235,162,550,255,minimum=-4.5,maximum=8.5,step=2,fmt='%+.6f',value_column=925,manual_categories=True)
    text(c,925,430,'Coefficient',11,GRAY,align='right')
    text(c,520,133,'Native base coefficient (logit scale)',12,GRAY,align='center')
    lines(c,235,99,['Categorical level 1 is the omitted reference (inferred from native encoded names); AGE is per year.','Coefficient size depends on units/coding. Signs are not evidence of a causal effect.'],10.5,leading=17)
    finish(c,v,filename,items,'Actual evaluated-fit native Logistic Regression base coefficients',[lr['native_artifact'],'native_logistic_coefficients_common.csv'],lr['coefficients'])

def tree_path(reading,items):
    t=reading['decision_tree'];filename='14_DT_native_root_leaf_path.png'
    c,v=new_figure(filename,'Decision Tree native root-to-leaf path','One actual path; other branches are not shown. Leaf counts are training-node counts, not test counts.')
    c.setStrokeColor(colors.HexColor(BLUE));c.setLineWidth(2);c.rect(65,206,270,155)
    text(c,200,320,'ROOT',14,GRAY,align='center');text(c,200,269,t['root'],25,bold=True,align='center')
    c.setStrokeColor(colors.HexColor(TEAL));c.line(350,279,625,279);c.line(625,279,613,286);c.line(625,279,613,272)
    text(c,488,307,'PNEUMONIA = 1',17,TEAL,bold=True,align='center')
    c.rect(645,164,300,238);text(c,795,365,'LEAF PREDICTION',13,GRAY,align='center');text(c,795,316,t['leaf_prediction'],25,TEAL,bold=True,align='center')
    counts=t['leaf_training_counts'];lines(c,699,262,['Training leaf counts',f"Hospitalized: {counts['Hospitalized']:,}",f"Outpatient: {counts['Outpatient']:,}"],15,INK,leading=29)
    finish(c,v,filename,items,'Actual evaluated-fit native Decision Tree path',[t['native_artifact']],t)

def appendix(items,records):
    from reportlab.lib.pagesizes import A4,landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image
    from xml.sax.saxutils import escape
    body=ParagraphStyle('Body',fontName='Chart',fontSize=10,leading=15,spaceAfter=9)
    title=ParagraphStyle('Title',parent=body,fontSize=22,leading=28,spaceAfter=15)
    story=[Paragraph('Mini Project 2 native batch result figures',title),Paragraph('This appendix charts actual saved official AI Studio batch results. It contains derived figures, not AI Studio GUI screenshots, and does not complete the 14 pending GUI photographs.',body),Paragraph('All nine algorithms share identical 18,000 training and 12,000 testing ID/label pairs. Positive class Hospitalized: 2,289 positive and 9,711 negative test rows. Modeling sample: 30,000; full prepared source: 1,048,575. Native metrics, fitted artifacts and source hashes were verified live before authoring.',body)]
    data=[['Model']+METRICS]+[[FULL.get(r['Model'],r['Model'])]+[f"{float(r[m]):.4f}" for m in METRICS] for r in records]
    table=Table(data,colWidths=[230]+[99]*5,repeatRows=1,hAlign='LEFT');table.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),'Chart'),('FONTSIZE',(0,0),(-1,-1),10),('BACKGROUND',(0,0),(-1,0),colors.HexColor(BLUE)),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#d9d9d9')),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    story+=[table,Spacer(1,12),Paragraph('Deep Learning is selected in the educational common-test comparison. A single test comparison is not independent post-selection validation or proof of clinical deployment suitability. No repeated-run SD or confidence interval is inferred. AUC uses native confidence scores, not class labels.',body),Paragraph('Sources: canonical native_model_comparison.csv; common_test metric/prediction exports; same-fit native LR/DT/RF artifacts and RF learner weights in common_test/explanation_run. Exact values and per-figure source SHA256 are in figure_sources_and_values.json.',body)]
    for item in items:
        story+=[PageBreak(),Paragraph(escape(item['caption']),body)];w,h=PILImage.open(OUT/item['file']).size;scale=min(760/w,475/h);story.append(Image(str(OUT/item['file']),width=w*scale,height=h*scale))
    def footer(c,doc):c.setFont('Chart',8);c.drawString(28,15,'Derived result figures only - the required common GUI photographs remain pending');c.drawRightString(815,15,str(doc.page))
    p=OUT/'MiniProject2_Native_Batch_Result_Figures_Appendix.pdf';SimpleDocTemplate(str(p),pagesize=landscape(A4),leftMargin=28,rightMargin=28,topMargin=28,bottomMargin=28).build(story,onFirstPage=footer,onLaterPages=footer);return p

def main():
    (OUT/'vector_sources').mkdir(exist_ok=True)
    proof=load(PROJECT/'common_test_verification.json');reading=load(PROJECT/'native_model_reading.json')
    assert not validate_common_proof(proof) and not validate_same_fit_readings(reading)
    protected=[PROJECT/p for p in ['MiniProject2_Report_Draft.pdf','MiniProject2_Report_Draft.docx','collect_evidence.py','build_report.py','native_model_comparison.csv','native_model_reading.json','native_setup.json','common_test_verification.json','evidence_status.json','common_test/MiniProject2_Common_Test_9Models.rmp']]
    protected += [PROJECT/'common_test'/name for name in proof['actual_export_sha256']]
    before={str(p.relative_to(PROJECT)):sha(p) for p in protected}
    records=list(csv.DictReader((PROJECT/'native_model_comparison.csv').open(encoding='utf-8-sig')));assert [r['Model'] for r in records]==MODELS
    for r in records:assert r['Engine']==proof['engine'] and r['PositiveClass']=='Hospitalized' and r['TestSetID']==proof['test_set_id'] and all(abs(float(r[m])-proof['models'][r['Model']]['metrics'][m])<1e-12 for m in METRICS)
    items=[]
    for i,r in enumerate(records,1):model_figure(r['Model'],r,proof,items,i)
    confusion(reading,proof,items);scoring(reading,items);importance(reading,items);coefficients(reading,items);tree_path(reading,items)
    pdf=appendix(items,records)
    sourcefiles=[PROJECT/p for p in ['native_model_comparison.csv','native_model_reading.json','common_test_verification.json','common_test/explanation_run/explanation_results_verification.json']]+[PROJECT/reading[k]['native_artifact'] for k in ['random_forest','logistic_regression','decision_tree']]
    lineage={'created_local':datetime.now().isoformat(),'artifact_type':'Derived charts of official native AI Studio batch exports; NOT GUI screenshots','figure_count':len(items),'common_test_rows':12000,'positive_class':'Hospitalized','test_id_label_hash':proof['test_set_id'],'native_source_hashes_live_verified':True,'new_model_run_performed':False,'GUI_photographs_created':False,'14_GUI_photograph_requirements_completed':False,'source_sha256':{str(p.relative_to(PROJECT)):sha(p) for p in sourcefiles},'protected_before_after_unchanged':all(sha(PROJECT/p)==digest for p,digest in before.items()),'protected_sha256':before,'figures':items,'appendix_file':pdf.name,'appendix_sha256':sha(pdf),'visual_review_status':'PENDING PNG/PDF inspection'}
    assert lineage['protected_before_after_unchanged']
    (OUT/'figure_sources_and_values.json').write_text(json.dumps(lineage,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
    (OUT/'README.md').write_text('# Native batch result charts\n\nFourteen derived figures and a standalone PDF appendix chart real official AI Studio batch results on the common12,000-row test, positive Hospitalized. These are **not GUI screenshots** and do not satisfy the14 pending GUI photographs. The current Draft report, canonical native exports and all strict gates remain unchanged.\n\nExact values, source SHA256 and per-figure lineage are in `figure_sources_and_values.json`. No model was trained/run by this builder. Native RF importance is genuine gain_ratio learner output; LR/DT readings use the evaluated common fit. Vector source PDFs are internal rendering inputs.\n\nRebuild with the bundled Python and `build_result_figures.py`. Charts use ReportLab; bundled Poppler produces PNGs.\n',encoding='utf8')
    archive=OUT/'MiniProject2_Native_Batch_Result_Figures.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for p in [OUT/x['file'] for x in items]+[pdf,OUT/'figure_sources_and_values.json',OUT/'README.md',Path(__file__).resolve()]:z.write(p,p.name)
    print(f'Created {len(items)} derived figures, appendix and ZIP. Current Draft/canonical/gates unchanged. Visual QA pending.')

if __name__=='__main__':main()
