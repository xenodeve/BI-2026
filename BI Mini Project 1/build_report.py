from pathlib import Path
import csv,json,html,argparse
import pandas as pd
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT,TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image,KeepTogether,Flowable
R=Path(__file__).resolve().parent
Q=json.loads((R/'data_quality.json').read_text())
M=pd.read_csv(R/'model_comparison.csv')
RUN=json.loads((R/'reference_run.json').read_text())
from collect_native_metrics import collect_native_metrics,MODELS
native_exports=[R/f'native_{code}.csv' for code in MODELS]
# Partial exports raise instead of silently reusing an old aggregate or reference numbers.
N=collect_native_metrics(R,write_output=False) if any(f.exists() for f in native_exports) else None
from verify_native_gui_evidence import verify
GUI_STATUS=verify(R)
args=argparse.ArgumentParser();args.add_argument('--require-complete',action='store_true');args=args.parse_args()
if args.require_complete and not GUI_STATUS['complete']:
 raise SystemExit('REFUSED FINAL REPORT: '+str(GUI_STATUS['pending']+GUI_STATUS['errors']))
portability_file=R.parent/'docs/execution/native-portability-verification.json'
PORTABLE=json.loads(portability_file.read_text()).get('all_three_actual_native_relocations_pass',False) if portability_file.exists() else False
pdfmetrics.registerFont(TTFont('Thai',r'C:\Windows\Fonts\tahoma.ttf',shapable=True))
pdfmetrics.registerFont(TTFont('ThaiBold',r'C:\Windows\Fonts\tahomabd.ttf',shapable=True))
body=ParagraphStyle('Body',fontName='Thai',fontSize=10.3,leading=17,spaceAfter=8,wordWrap='CJK',shaping=1,textColor=colors.HexColor('#253342'))
heading=ParagraphStyle('Heading',parent=body,fontName='ThaiBold',fontSize=14,leading=21,spaceBefore=6,spaceAfter=12,keepWithNext=True,textColor=colors.black)
title=ParagraphStyle('Title',parent=heading,fontSize=20,leading=30,spaceAfter=18)
small=ParagraphStyle('Small',parent=body,fontSize=8.4,leading=13,spaceAfter=5)
cellstyle=ParagraphStyle('Cell',parent=small,fontSize=8.5,leading=13,spaceAfter=0)
cellhead=ParagraphStyle('CellHead',parent=cellstyle,fontName='ThaiBold',textColor=colors.white)
story=[]
def p(t,style=body):return Paragraph(html.escape(str(t)),style)
def para(t,style=body):story.append(p(t,style))
def h(t):story.append(p(t,heading))
def table(headers,rows,widths):
 data=[[p(x,cellhead) for x in headers]]+[[p(x,cellstyle) for x in row] for row in rows]
 t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
 commands=[('BACKGROUND',(0,0),(-1,0),colors.HexColor('#203A5F')),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#D9D9D9')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]
 for i in range(2,len(data),2):commands.append(('BACKGROUND',(0,i),(-1,i),colors.HexColor('#F0F4F8')))
 t.setStyle(TableStyle(commands));story.append(t);story.append(Spacer(1,10))
def page():story.append(PageBreak())
descriptions=[
('age','จำนวนเต็ม','อายุลูกค้า หน่วยปี','ใช้'),('job','หมวดหมู่','ประเภทอาชีพ รวม unknown','ใช้'),('marital','หมวดหมู่','สถานภาพสมรส divorced รวมหม้าย','ใช้'),('education','หมวดหมู่','ระดับการศึกษา รวม unknown','ใช้'),('default','สองค่า','มีสินเชื่อผิดนัด yes/no','ใช้'),('balance','จำนวนเต็ม','ยอดเงินเฉลี่ยรายปี หน่วยยูโร ติดลบได้','ใช้'),('housing','สองค่า','มีสินเชื่อที่อยู่อาศัย yes/no','ใช้'),('loan','สองค่า','มีสินเชื่อส่วนบุคคล yes/no','ใช้'),('contact','หมวดหมู่','ช่องทางติดต่อ cellular/telephone/unknown','ใช้'),('day','จำนวนเต็ม','วันที่ของเดือนที่ติดต่อครั้งสุดท้าย','ใช้ตามสมมติฐาน'),('month','หมวดหมู่','เดือนที่ติดต่อครั้งสุดท้าย ไม่มีปีแยก','ใช้ตามสมมติฐาน'),('duration','จำนวนเต็ม','ระยะเวลาการโทรครั้งสุดท้าย หน่วยวินาที','ตัดออก'),('campaign','จำนวนเต็ม','จำนวนติดต่อแคมเปญนี้ รวมครั้งสุดท้าย','ใช้ตามสมมติฐาน'),('pdays','จำนวนเต็ม','วันจากแคมเปญก่อนหน้า −1 หมายถึงไม่เคยติดต่อ','ใช้'),('previous','จำนวนเต็ม','จำนวนติดต่อก่อนแคมเปญนี้','ใช้'),('poutcome','หมวดหมู่','ผลแคมเปญก่อนหน้า รวม unknown','ใช้'),('y','สองค่า','สมัครเงินฝากประจำหรือไม่ yes/no','Target'),('previously_contacted','สองค่า','สร้างจาก pdays ≠ −1 เป็น yes มิฉะนั้น no','ตัวแปรใหม่')]
pd.DataFrame(descriptions,columns=['attribute','type_th','meaning_th','model_role_th']).to_csv(R/'data_dictionary.csv',index=False,encoding='utf-8-sig')
raw=pd.read_csv(R/'data/bank-full.csv',sep=';')
insights=raw.groupby('poutcome').y.agg(count='size',yes=lambda x:(x=='yes').sum())
insights['yes_rate']=insights['yes']/insights['count'];insights.to_csv(R/'source_insights.csv')

story.append(p('การทำนายการสมัครเงินฝากประจำ',title))
para('Mini Project 1  การวิเคราะห์ข้อมูลตามกระบวนการ CRISP-DM')
para('รายงานนี้ศึกษาข้อมูล Bank Marketing ของ UCI จำนวน 45,211 ระเบียน และเปรียบเทียบโมเดลจำแนก 5 เทคนิค โดยใช้ y เป็นเป้าหมายและตัด duration เพื่อหลีกเลี่ยงการใช้ข้อมูลหลังโทรในการทำนายก่อนโทร')
if N is None:
 para('สถานะผลทดลองในรายงาน: Python scikit-learn reference ที่รันจริง ยังไม่ใช่ผลยืนยันจาก AI Studio ส่วน Turbo Prep การกด Run กระบวนการและการย้ายโฟลเดอร์ยังรอหลักฐาน native')
else:
 para('ผลหลักมาจาก AI Studio native engine ผ่าน official batch runner ที่ติดตั้งมากับโปรแกรม แยกจาก Python reference และยืนยันซ้ำด้วย native GUI Run12:06:58–12:07:06 ทั้ง5โมเดล ภาพ PerformanceVector และผลCSVตรงกับ batch เดิมแบบ byte-for-byte')
 para('หลักฐาน Turbo Prep interactive และข้อมูล prepared ผ่านการตรวจแล้ว' if GUI_STATUS['complete'] else 'ยังรอหลักฐาน Turbo Prep interactive/history และการตรวจ exported prepared data; ภาพผลโมเดลไม่ใช้แทนขั้นตอน Turbo Prep')
h('1 Business Understanding')
para('ปัญหาธุรกิจคือทีมธนาคารต้องจัดลำดับลูกค้าที่น่าจะสมัครเงินฝากประจำเพื่อลดการโทรที่ไม่เกิดผล ประเภทงานเป็น binary classification โดย positive class = yes สมมติว่าข้อมูลลูกค้า ประวัติแคมเปญก่อน และกำหนดการติดต่อครั้งที่จะพิจารณาทราบแล้วก่อนเริ่มโทร')
para('เกณฑ์เปรียบเทียบ native ใช้ F1 ของ yes เป็นหลักเพื่อดูสมดุล Precision กับ Recall และ ROC AUC เพื่อดูการจัดอันดับ ส่วน Python reference มี Average Precision ประกอบ กลุ่ม yes มีเพียง 11.70% จึงอ่าน Accuracy ร่วมกับ Confusion Matrix ยังไม่มีต้นทุนการโทรหรือมูลค่าสัญญาจริง จึงไม่สรุปผลตอบแทนทางการเงิน')
h('2 Data Understanding')
table(['ข้อมูล','ค่าที่ตรวจจากไฟล์จริง'],[['แหล่งที่มา','UCI Bank Marketing เวอร์ชัน bank-full.csv'],['ขนาด','45,211 แถว 17 คอลัมน์ = 16 input เดิมและ 1 target'],['Target yes','5,289 คน 11.70%'],['Target no','39,922 คน 88.30%'],['ชนิดไฟล์','CSV คั่นด้วย semicolon มี header และ quoted strings'],['ค่าว่างจริงและแถวซ้ำทั้งแถว','0 เซลล์ว่าง และ 0 แถวซ้ำทั้งแถว']],[190,325])
para('unknown เป็นหมวดหมู่ที่มีความหมายว่าไม่ทราบตามคำอธิบายชุดข้อมูล ไม่ถือว่าเป็นข้อมูลว่างที่เติมค่าได้โดยอัตโนมัติ ตัวอย่างนี้เป็นข้อมูลธนาคารในโปรตุเกส จึงไม่อ้างว่ารูปแบบความสัมพันธ์เหมือนลูกค้าไทย')
page()
h('พจนานุกรมข้อมูล')
table(['ตัวแปร','ชนิด','ความหมาย','บทบาท'],descriptions,[98,72,245,100])
para('คำอธิบายอ้างอิง bank-names.txt ที่มาพร้อมชุดข้อมูล ตัวแปร derived สร้างโดยกฎที่กำหนดล่วงหน้าและไม่ใช้ y ข้อมูลปัจจุบันไม่มีรหัสลูกค้าหรือปีของแต่ละแถวสำหรับการแบ่งตามบุคคลหรือสร้างวันเต็ม',small)
page()
h('3 Data Preparation')
para('เก็บ data/bank-full.csv เป็นต้นฉบับ และสำเนา bank-full.csv แบบ byte-identical ไว้ข้าง MiniProject1.rmp ตามเกณฑ์ส่งงาน bank-clean.csv เป็นไฟล์เตรียมที่แยกออกมา มีจำนวนแถวเท่าเดิม ตัด duration และเพิ่ม previously_contacted ใช้ −1 ของ pdays เป็น sentinel ตามแหล่งข้อมูล')
table(['ปัญหาที่ตรวจ','จำนวน','วิธีจัดการ'],[['unknown ใน job','288','เก็บเป็นหมวดหมู่'],['unknown ใน education','1,857','เก็บเป็นหมวดหมู่'],['unknown ใน contact','13,020','เก็บเป็นหมวดหมู่'],['unknown ใน poutcome','36,959','เก็บเป็นหมวดหมู่'],['balance ติดลบ','3,766','เก็บ ไม่ตีความว่าผิดโดยอัตโนมัติ'],['pdays = −1','36,954','เก็บ sentinel และสร้าง prior contact flag'],['input ซ้ำเมื่อตัด duration','16','ไม่ลบ เพราะไม่ทราบว่าเป็นลูกค้าคนเดียวกัน']],[225,60,230])
para('ตรวจ outlier ด้วยเกณฑ์ 1.5 × IQR พบ age 487 แถว และ balance 4,729 แถว ค่านี้เป็นเพียง flag สำหรับทบทวน ไม่ใช่หลักฐานว่าข้อมูลผิด จึงไม่ลบหรือตัดปลายค่า ส่วน pdays และ previous มี IQR เป็นศูนย์เพราะส่วนใหญ่ไม่เคยติดต่อ การ flag ด้วย IQR จึงต้องอ่านตามความหมายทางธุรกิจ')
para('Python reference แบ่ง stratified 70/30 ด้วย seed 2026 ได้ train 31,647 แถวและ test 13,564 แถว ใช้ row indices ชุดเดียวกับทุกโมเดล ไม่ย้ายแถวระหว่างโมเดล Encoding และ StandardScaler fit เฉพาะ train แล้ว transform test; หมวดหมู่ใหม่ที่ไม่เคยพบใน train เข้ารหัสเป็นศูนย์')
para('ตรวจยืนยันก่อน training: label มีเพียง no/yes, ไม่มีแถวร่วมระหว่าง train/test, duration และ y ไม่อยู่ใน inputs, ค่าเฉลี่ย scaler เท่ากับ training mean และ synthetic test-only category ไม่ถูกเรียนรู้ ตัวแปรจำนวนรวมของแคมเปญ day และ month ใช้ได้ภายใต้สมมติฐานว่าทราบกำหนดการติดต่อครั้งนั้น หากต้องจัดลำดับก่อนเริ่มทั้งแคมเปญต้องทบทวนตัวแปรเหล่านี้ใหม่')
para('Turbo Prep native interactive ที่ตรวจแล้ว: เปิด original45,211แถว/17fields ตัด duration และสร้าง previously_contacted จาก if(pdays == -1,"no","yes") โดยเก็บต้นฉบับไว้ Export prepared data ตรวจเทียบค่าต้นฉบับ/จำนวนแถว/flagผ่านครบ' if GUI_STATUS['complete'] else 'Turbo Prep ที่ต้องยืนยันในแอป: เปิด original CSV ตรวจจำนวนแถว/ชนิดข้อมูล/unknown/duplicates/outliers แล้วตัด duration สร้าง previously_contacted และส่งออกโดยรักษาต้นฉบับ ยังไม่อ้างว่าขั้นตอน Turbo Prep interactive ผ่านแล้ว')
if GUI_STATUS['complete']:
 para('Native History มี2ขั้นตอนที่ Commitจริงเท่านั้น: Remove duration ทำให้17เหลือ16fields แล้ว Generate previously_contacted กลับเป็น17fields รวม45,211แถว/11nominal6numeric Export bank_turboprep_GUI.csv ตรวจทุก16ค่าคอลัมน์เดิมและflagทุกแถวตรงกับ bank-clean.csv โดยnormalizeรูปแบบตัวเลข x.0และลำดับคอลัมน์ก่อนเทียบ')
 para('ภาพ Cleanse เป็นการเปิดดู AGEเพียง1คอลัมน์แล้ว Cancel ไม่มี Commit replace missing/remove duplicates/remove outliers ค่าว่าง0และexactduplicates0เป็นการตรวจไฟล์ต้นฉบับทั้งชุดด้วยoffline audit ไม่ใช่ผลcountsจากGUI; unknownและค่าปลายช่วงที่ถูกต้องยังคงเดิม')
 para('Turbo Prep interactive นี้เป็นการทำซ้ำworkflowจริงให้เทียบกับcanonical preparation ไม่อ้างว่า MiniProject1.rmp เดิมสร้างด้วยGUIหรือโมเดล12:06ฝึกจากexport12:39 Canonicalอ่านrawและทำRemove/Generateที่เทียบเท่ากัน; RawViewerใช้แสดงข้อมูลเดิมเท่านั้น')
page()
if N is not None:
 h('4 Modeling / 5 Evaluation ผลหลักจาก native batch')
 native_test=int(N.test_rows.iloc[0]);native_positive=int((N.tp+N.fn).iloc[0])
 para(f'รัน MiniProject1.rmp จริงด้วย official ai-studio-batch.bat ของ AI Studio 2026.1.1 กระบวนการใช้ Split Data stratified 70/30 seed 2026 เพียงครั้งเดียวก่อน encoding/scaling และ Multiply ไปห้าโมเดล native test มี {native_test:,} แถว yes {native_positive:,} และ no {native_test-native_positive:,} ใช้ yes เป็น positive class ทุกโมเดล ผลเก็บจาก Performance to Data โดยตรง')
 table(['โมเดล','Accuracy','Precision yes','Recall yes','F1 yes','ROC AUC'],[[r.model]+[f'{getattr(r,c):.4f}' for c in ['accuracy','precision_yes','recall_yes','f1_yes','roc_auc']] for r in N.itertuples()],[130,75,80,75,75,80])
 table(['โมเดล','TN','FP','FN','TP'],[[r.model]+[f'{getattr(r,c):,}' for c in ['tn','fp','fn','tp']] for r in N.itertuples()],[195,80,80,80,80])
 native_winner=N.sort_values('f1_yes',ascending=False).iloc[0]
 para(f"เมื่อใช้ F1 yes ตามเกณฑ์ที่ประกาศ {native_winner['model']} สูงสุด {native_winner['f1_yes']:.4f} ด้วย Precision {native_winner['precision_yes']:.4f} และ Recall {native_winner['recall_yes']:.4f} มี FP {int(native_winner['fp']):,} และ FN {int(native_winner['fn']):,} ควรใช้ validation แยกเพื่อพิจารณา threshold ตามกำลังโทรและต้นทุนก่อนทดลองใช้งาน")
 para(f"โมเดลที่ F1 สูงสุดมี Accuracy {native_winner['accuracy']:.4f} เทียบกับ baseline ทาย no ทั้งหมด {1-native_positive/native_test:.4f} ซึ่งมี F1 yes เท่ากับ 0 จึงเห็นเหตุผลที่ต้องประเมินกลุ่ม yes ร่วมด้วย",small)
 para('ตรวจครบห้า exports ว่าสร้างหลังเวลาเริ่มรัน บันทึกยืนยัน Process finished successfully และคำนวณ Accuracy/Precision/Recall/F1 กลับจาก confusion counts ได้ จำนวน test และ actual yes/no ตรงกันทุกโมเดลรายละเอียด hash และ provenance อยู่ใน native_metrics_provenance.json Python ในขั้นตอนตรวจไม่ได้ฝึกโมเดลแทน native engine',small)
 page()
h('4 Modeling ผลอ้างอิง Python')
para('โมเดลทั้งหมดใช้ชุด test เดียวกัน และ positive class = yes ผลต่อไปนี้มาจาก scikit-learn '+RUN['sklearn_version']+' ด้วย threshold 0.5 ไม่มีการปรับ threshold หรือค้น hyperparameters จาก test ชุดที่ใช้รายงาน')
table(['เทคนิค','การตั้งค่า Python reference'],[['Naive Bayes','GaussianNB var_smoothing 1e−9'],['Logistic Regression','C=1 max_iter=2000 balanced class weights'],['Decision Tree','max_depth=8 min_samples_leaf=20 balanced weights'],['Random Forest','200 trees max_depth=12 leaf=5 balanced weights'],['Gradient Boosted Trees','150 trees learning_rate=0.1 depth=3 leaf=10']],[145,370])
table(['โมเดล','Accuracy','Precision yes','Recall yes','F1 yes','Avg Precision'],[[r.model]+[f'{getattr(r,c):.4f}' for c in ['accuracy','precision_yes','recall_yes','f1_yes','average_precision']] for r in M.itertuples()],[130,70,80,70,70,95])
para('Baseline ทาย no ทั้งหมดได้ Accuracy 0.8830 แต่ Recall และ F1 ของ yes เป็น 0 ขณะที่ baseline การจัดอันดับสุ่มมี Average Precision ประมาณ 0.1170 ทุกโมเดลมี Average Precision สูงกว่าฐานนี้ แต่มีเพียง GBT ที่ Accuracy สูงกว่าฐาน no ทั้งหมด',small)
story.append(Image(str(R/'reference_model_comparison.png'),width=510,height=245))
para('รูปเปรียบเทียบ Python reference เท่านั้น ไม่ใช่ภาพ Results ของ AI Studio',small)
page()
h('5 Evaluation ของ Python reference')
table(['โมเดล','TN','FP','FN','TP','ข้อผิดพลาดสำคัญ'],[[r.model,str(r.tn),str(r.fp),str(r.fn),str(r.tp),('พลาด yes จำนวนมาก' if r.recall_yes<.3 else 'แจ้ง yes ผิดจำนวนมาก')] for r in M.itertuples()],[130,50,50,50,50,185])
para('TN คือทาย no ถูก FP คือทาย yes แต่จริง no FN คือพลาดลูกค้าที่จริง yes และ TP คือทาย yes ถูก ชุด test มี yes 1,587 และ no 11,977 ดังนั้นค่า Recall สูงขึ้นอาจแลกกับการโทรที่ไม่เกิดผลมากขึ้น',small)
para('ถ้าใช้ F1 ที่ threshold 0.5 ตามเกณฑ์ที่กำหนด Random Forest สูงสุด 0.4421 ด้วย Precision 0.3443 และ Recall 0.6175 จึงเป็นตัวเลือก reference สำหรับการใช้งานที่ต้องรักษาสมดุล อย่างไรก็ตาม FP 1,866 แสดงว่ายังต้องจัดกำลังโทรและกำหนด threshold จากชุด validation ตามต้นทุนจริงก่อนใช้งาน')
para('Gradient Boosted Trees มี Average Precision สูงสุด 0.4585 และ ROC AUC 0.7989 เหมาะจะศึกษาเป็นคะแนนจัดลำดับ แต่ threshold 0.5 ให้ Recall เพียง 0.2445 และพลาด yes 1,199 คน จึงไม่เลือกจาก Accuracy 0.8963 โดยละเลยลูกค้าที่พลาด Logistic Regression ให้ Recall สูงสุด 0.6377 แต่ Precision เพียง 0.2669 ส่วน Decision Tree ให้ F1 0.4248 และ Naive Bayes ให้ F1 0.3828')
h('Insight จากข้อมูลต้นทาง')
table(['ผลแคมเปญก่อน','ระเบียน','yes','สัดส่วน yes'],[[idx,f'{r["count"]:,.0f}',f'{r["yes"]:,.0f}',f'{r["yes_rate"]:.2%}'] for idx,r in insights.iterrows()],[200,95,95,125])
para('ตารางเป็นความสัมพันธ์เชิงพรรณนา ไม่ใช่ผลเชิงสาเหตุหรือประสิทธิภาพบน test ลูกค้าที่มีผลแคมเปญก่อน success มีสัดส่วนสมัครสูงกว่าในไฟล์นี้ จึงเป็นประวัติที่มีเหตุผลให้ทีมธุรกิจพิจารณา แต่ unknown มีจำนวนมากและควรตรวจความครบถ้วนของการเก็บประวัติ')
para('ข้อจำกัด: random split ใช้เพื่อเปรียบเทียบทางการศึกษา ไม่ใช่หลักฐานทำนายอนาคต ข้อมูลไม่มี client ID จึงยังยืนยันการแยกคนละบุคคลไม่ได้ มี input rows ซ้ำ 16 รายการหลังตัด duration และไม่มีปีรายแถวสำหรับ temporal holdout ที่ถูกต้อง ยังไม่มี external validation')
page()
h('6 Deployment')
para('นำโมเดลไปช่วยจัดคิวการติดต่อ ขั้นต่อไปควรใช้ชุด validation เพื่อเลือก threshold ตามกำลังโทรและต้นทุน false positive/false negative แล้วประเมิน temporal holdout และข้อมูลใหม่ก่อนทดลองใช้ในงานจริง')
para('ความหมายของโมเดลทั้ง 5: Naive Bayes เป็น baseline ที่ฝึกเร็ว Logistic Regression ให้ความสัมพันธ์เชิงเส้นที่ตรวจค่าสัมประสิทธิ์ได้ Decision Tree ให้กฎแบ่งกลุ่ม Random Forest รวมหลายต้นไม้เพื่อสมดุลความแม่นยำและการค้น yes ส่วน GBT เรียนรู้ข้อผิดพลาดต่อเนื่องและให้คะแนนจัดอันดับที่ดีที่สุดใน reference ชุดนี้ ผลเหล่านี้ยังไม่พิสูจน์กำไรหรือเหตุและผล')
para('ติดตามสัดส่วน yes, missing/unknown, การกระจาย input, Precision/Recall เมื่อผลจริงกลับมา และความแตกต่างระหว่างกลุ่มลูกค้า บันทึกเวอร์ชันข้อมูล สคริปต์ seed และโมเดล ก่อนนำไปฝึกใหม่เมื่อพฤติกรรมหรือแคมเปญเปลี่ยน')
h('กระบวนการ AI Studio และหลักฐานที่ต้องยืนยัน')
para('MiniProject1.rmp ประกอบด้วย Read CSV → Target y → ตัด duration → prior contact flag → split เดียว → fit encoding/scaling train → apply preprocessing test → Multiply train/test สำหรับ 5 learners → Apply Model → Performance positive yes')
para('ใช้ native Naive Bayes, H2O Logistic Regression, parallel Decision Tree, parallel Random Forest และ H2O Gradient Boosted Trees Operator IDs และ ports อ้างจาก registries กับ tutorial XML ที่ติดตั้งใน AI Studio 2026.1.1 ไม่ได้แทนด้วย Execute Python แต่ implementation, random split และ hyperparameters ต่างจาก Python reference จึงคาดว่าค่า performance อาจต่างกัน')
para('ต้องเปิด .rmp แบบไฟล์ในเครื่อง เก็บ original bank-full.csv ไว้ข้างไฟล์ แล้ว Run จริง พอร์ต Result 1–5 เป็น Performance, 6–10 เป็น scored test, 11–15 เป็น models และ 16–20 เป็น metric tables จาก Performance to Data ซึ่งส่งออก native_NB/LR/DT/RF/GBT.csv อัตโนมัติ พาธคำนวณจาก built-in process_path/process_file macros ต้องยืนยันว่าขยายเป็นไฟล์ในโฟลเดอร์ปัจจุบันได้')
para('การย้ายสำเนา RMP พร้อมข้อมูลเดิมไปโฟลเดอร์ใหม่และรัน native batch ซ้ำสำเร็จครบห้าโมเดล ผล metrics/confusion counts ตรงกับการรันหลัก ต้นฉบับและพารามิเตอร์ไม่เปลี่ยน พิสูจน์ไว้ใน docs/execution/native-portability-verification.json; native GUI model/process photographs ยืนยันแยกใน native_gui_evidence.json' if PORTABLE else 'การย้ายทั้งโฟลเดอร์และรันซ้ำยังไม่ยืนยัน; ภาพ GUI process/results ไม่ใช้แทนการทดสอบย้ายตำแหน่ง')
if GUI_STATUS.get('actual_relocated_native_GUI_run_verified'):
 para('ActualGUIหลังย้ายโฟลเดอร์Runผ่าน:5CSVเวลา12:42:08–12:42:14ตรงcanonicalแบบbyte-identical ภาพnative_relocated_all5_completed.pngแสดงpathใหม่และResultsครบ; raw/RMPไม่เปลี่ยน proofในnative_GUI_portability_verification.json',small)
if N is not None:
 h('แหล่งผล native และสถานะหลักฐาน')
 para('ผลหลักอ่านจาก native_NB.csv native_LR.csv native_DT.csv native_RF.csv และ native_GBT.csv จาก official native batch; native_batch.log เก็บการทำงานจริง ผลCSVจาก fresh nativeGUIตรงกันทั้ง5ไฟล์ ภาพ Results/Process ยืนยันแยกด้วยSHAใน native_gui_evidence.json ส่วน Python reference แยกตามimplementation/defaults/random generator ไม่ใช้แทน native',small)
 for item in GUI_STATUS['pending']+GUI_STATUS['errors']:para('PENDING / FAILED '+item,small)
h('แหล่งข้อมูลและเอกสารอ้างอิง')
para('UCI Machine Learning Repository  Bank Marketing  https://archive.ics.uci.edu/dataset/222/bank+marketing',small)
para('Moro S Laureano R and Cortez P 2011  Using Data Mining for Bank Direct Marketing An Application of the CRISP-DM Methodology  ESM 2011 pages 117–121  http://hdl.handle.net/1822/14838  อ้างตาม bank-names.txt',small)
para('ข้อกำหนด BI_Mini_Project 1.pdf หน้า1–2; dictionary bank-names.txt; process macros อ้างเอกสาร AI Studio',small)
imgs=sorted((R/'screenshots').glob('*.png')) if (R/'screenshots').exists() else []
class NativeClip(Flowable):
 def __init__(self,source,roi,maxheight=600):
  Flowable.__init__(self);self.source,self.roi=source,roi
  from PIL import Image as PILImage
  self.w,self.h=PILImage.open(source).size;l,t,r,b=roi
  self.scale=min(515/(r-l),maxheight/(b-t));self.width=(r-l)*self.scale;self.height=(b-t)*self.scale
 def draw(self):
  c=self.canv;c.saveState();clip=c.beginPath();clip.rect(0,0,self.width,self.height);c.clipPath(clip,stroke=0)
  l,t,r,b=self.roi;c.drawImage(str(self.source),-l*self.scale,(b-self.h)*self.scale,width=self.w*self.scale,height=self.h*self.scale);c.restoreState()
if imgs:
 for img in imgs:
  page();h('หลักฐานหน้าจอ '+img.stem.replace('_',' '))
  from PIL import Image as PILImage
  with PILImage.open(img) as im:w,hei=im.size
  if img.name.startswith('native_') and img.name.endswith('_performance.png'):
   code=img.name.split('_')[1];tabs={'NB':(610,95,1160,130),'LR':(0,95,615,130),'DT':(590,126,1160,160),'RF':(0,126,590,160),'GBT':(459,156,1160,190)}
   story.append(NativeClip(img,tabs[code],35));story.append(Spacer(1,6));story.append(NativeClip(img,(0,338,640,1008),575))
   para('Native GUI PerformanceVector จริง positive=yes บน Test13,564แถว ภาพรายงานใช้การ clipping ของ pixelsต้นฉบับ ไม่แก้ไขภาพเต็ม; confusion rows predicted/columns true',small)
  elif img.name=='native_GBT_confusion.png':
   story.append(NativeClip(img,(270,390,1160,565),300));para('Native GBT confusion rows predicted/columns true; TN11091 FP886 FN786 TP801',small)
  elif img.name=='native_turboprep_feature_formula.png':
   story.append(NativeClip(img,(290,210,1320,650),350));para('สูตรจริงที่ nativeGenerate preview: if(pdays == -1,"no","yes"); Commitพิสูจน์แยกในHistory/export ไม่สร้างภาพGUIใหม่',small)
  elif img.name in ['native_turboprep_original.png','native_turboprep_duration_removed.png','native_turboprep_prepared.png']:
   ratio=min(515/w,670/hei);story.append(Image(str(img),width=w*ratio,height=hei*ratio));story.append(Spacer(1,8));story.append(NativeClip(img,(5,270,285,445),155));para('ภาพจริงและรายละเอียดnativeRows/Columns/LastChangeจากpixelsเดิม; ไม่แก้ไขไฟล์ภาพต้นฉบับ',small)
  elif img.name=='native_turboprep_quality_review.png':
   ratio=min(515/w,670/hei);story.append(Image(str(img),width=w*ratio,height=hei*ratio));para('Contextonly: AGEselected1column/CleanseopenedและCancel; ไม่มีCommitdedup/outlierremove/missingreplacement และไม่ใช้ภาพนี้อ้างcountsทั้งdataset',small)
  elif img.name in ['native_turboprep_history.png','native_turboprep_history_detail.png']:
   ratio=min(515/w,600/hei);story.append(Image(str(img),width=w*ratio,height=hei*ratio));para('Historyจริง2steps: Removeduration และ Generatepreviously_contacted; ไม่มีขั้นตอนCleanseที่Commit',small)
  elif img.name=='native_turboprep_export_result.png':
   ratio=min(515/w,600/hei);story.append(Image(str(img),width=w*ratio,height=hei*ratio));para('NativeExportFinished; bank_turboprep_GUI.csvเทียบทุก45,211แถวผ่านในturboprep_export_verification.json',small)
  else:
   ratio=min(515/w,670/hei);story.append(Image(str(img),width=w*ratio,height=hei*ratio))
   captions={'native_process_before_run.png':'Nativeprocessก่อนRunแสดงprep/splitบางส่วน เป็นcontextก่อนRun',
    'native_process_completed.png':'NativeprocessหลังRunที่67% เห็น5branchesแต่ด้านขวาบางส่วนถูกตัด; ใช้full_overviewประกอบ',
    'native_process_full_overview.png':'Nativefullprocessที่50% เห็น5learnerbranchesและResultportsครบ; workflowและชื่อoperatorอธิบายในรายงาน',
    'native_all5_completed.png':'NativeResultsหลังRunสำเร็จเห็น5PerformanceVectors/models/scoredsets/metricexports',
    'native_raw_import.png':'NativeRawViewerResults45,211×17ก่อนเปิดTurboPrep ไม่มีการclean/filter/labelในviewer',
    'native_turboprep_duration_selected.png':'GenuineinteractiveTransformเลือกdurationเพียง1column ก่อนRemove/Commit; ผลหลังCommitอยู่ในภาพduration_removed',
    'native_relocated_all5_completed.png':'ActualGUIเปิดRMPจากrelocatedpathในtitlebarและRunสำเร็จครบ5โมเดล; 5freshCSVตรงcanonical'}
   para(captions.get(img.name,'ภาพที่เก็บจากnativeแอปจริง แสดงเฉพาะขั้นตอนและค่าที่ปรากฏในภาพ'),small)
def footer(c,d):
 c.saveState();c.setFont('Thai',8);c.setFillColor(colors.HexColor('#687788'));c.drawString(40,25,'Bank Marketing  Mini Project 1');c.drawRightString(A4[0]-40,25,str(d.page));c.restoreState()
output_name='MiniProject1_Report.pdf' if GUI_STATUS['complete'] else 'MiniProject1_Report_Draft.pdf'
doc=SimpleDocTemplate(str(R/output_name),pagesize=A4,leftMargin=40,rightMargin=40,topMargin=38,bottomMargin=42,title='การทำนายการสมัครเงินฝากประจำ',author='')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print('PDF report generated with Thai font shaping')
