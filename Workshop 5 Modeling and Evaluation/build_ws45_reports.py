from pathlib import Path
import html,json
import pandas as pd
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image
W5=Path(__file__).resolve().parent;W4=W5.parent/'Workshop 4 การจัดเตรียมข้อมูล (Data Preparation)'
Q=json.loads((W4/'data_quality.json').read_text());S=json.loads((W5/'split_verification.json').read_text());M=pd.read_csv(W5/'model_comparison.csv')
from collect_native_metrics import collect_native_metrics,MODELS
N=collect_native_metrics(W5) if any((W5/f'native_{code}.csv').exists() for code in MODELS) else None
N4=json.loads((W4/'native_batch_verification.json').read_text()) if (W4/'native_batch_verification.json').exists() else None
portability_file=W5.parent/'docs/execution/native-portability-verification.json'
PORTABLE=json.loads(portability_file.read_text()).get('all_three_actual_native_relocations_pass',False) if portability_file.exists() else False
pdfmetrics.registerFont(TTFont('Thai',r'C:\Windows\Fonts\tahoma.ttf',shapable=True));pdfmetrics.registerFont(TTFont('ThaiBold',r'C:\Windows\Fonts\tahomabd.ttf',shapable=True))
body=ParagraphStyle('Body',fontName='Thai',fontSize=10.1,leading=17,spaceAfter=9,wordWrap='CJK',shaping=1,textColor=colors.HexColor('#253342'))
heading=ParagraphStyle('Heading',parent=body,fontName='ThaiBold',fontSize=14,leading=21,spaceBefore=5,spaceAfter=12,keepWithNext=True,textColor=colors.black)
title=ParagraphStyle('Title',parent=heading,fontSize=20,leading=30,spaceAfter=18)
small=ParagraphStyle('Small',parent=body,fontSize=8.4,leading=13,spaceAfter=6)
cell=ParagraphStyle('Cell',parent=small,fontSize=8.5,leading=13,spaceAfter=0)
head=ParagraphStyle('Head',parent=cell,fontName='ThaiBold',textColor=colors.white)
def P(t,style=body):return Paragraph(html.escape(str(t)),style)
def table(story,heads,rows,widths,padding=6):
 data=[[P(x,head) for x in heads]]+[[P(x,cell) for x in row] for row in rows]
 t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT');styles=[('BACKGROUND',(0,0),(-1,0),colors.HexColor('#203A5F')),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#D9D9D9')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),padding),('BOTTOMPADDING',(0,0),(-1,-1),padding)]
 for i in range(2,len(data),2):styles.append(('BACKGROUND',(0,i),(-1,i),colors.HexColor('#F0F4F8')))
 t.setStyle(TableStyle(styles));story.extend([t,Spacer(1,10)])
def h(story,t):story.append(P(t,heading))
def para(story,t,style=body):story.append(P(t,style))
def page(story):story.append(PageBreak())
def sources(story,lesson):
 h(story,'แหล่งข้อมูลและบทเรียน')
 para(story,'Kamil Pytlak  Indicators of Heart Disease  Kaggle  https://www.kaggle.com/datasets/kamilpytlak/personal-key-indicators-of-heart-disease  ใช้ heart_2020_cleaned.csv จำนวน 319,795 ระเบียน ไม่เปลี่ยนเป็นไฟล์ปี 2022 ตามชื่อหน้าปัจจุบัน',small)
 para(story,'CDC BRFSS 2020  https://www.cdc.gov/brfss/annual_data/annual_2020.html และ Summary Matrix of Calculated Variables  https://www.cdc.gov/brfss/annual_data/2020/Summary_Matrix_20.html  นิยามคำตอบประวัติโรคหัวใจมาจาก coronary heart disease หรือ myocardial infarction',small)
 para(story,'บทเรียน '+lesson+' และขอบเขตที่อนุมัติให้ใช้ข้อมูลที่อาจารย์เคยโพสต์ Classroom ไม่ได้ให้คำสั่งไฟล์หรือจำนวนโมเดลเฉพาะงานนี้',small)
def screenshots(story,folder):
 from PIL import Image as PILImage
 for f in sorted((folder/'screenshots').glob('*.png')) if (folder/'screenshots').exists() else []:
  page(story);h(story,'หลักฐานหน้าจอ '+f.stem.replace('_',' '))
  with PILImage.open(f) as im:w,hei=im.size
  ratio=min(515/w,675/hei);story.append(Image(str(f),width=w*ratio,height=hei*ratio))
def make_pdf(story,path,label):
 def foot(c,d):c.saveState();c.setFont('Thai',8);c.setFillColor(colors.HexColor('#687788'));c.drawString(40,25,label);c.drawRightString(A4[0]-40,25,str(d.page));c.restoreState()
 SimpleDocTemplate(str(path),pagesize=A4,leftMargin=40,rightMargin=40,topMargin=38,bottomMargin=42,title=label,author='').build(story,onFirstPage=foot,onLaterPages=foot)
dictionary=[('HeartDisease','หมวดหมู่ 2 ค่า','ประวัติโรคหัวใจตามคำตอบแบบสำรวจ Yes เป็น positive class','Target'),('BMI','ตัวเลข','ดัชนีมวลกายตามไฟล์','Input'),('Smoking','Yes หรือ No','ประวัติสูบบุหรี่ตามคำถามแบบสำรวจ','Input'),('AlcoholDrinking','Yes หรือ No','การดื่มหนักตามตัวแปรแบบสำรวจ','Input'),('Stroke','Yes หรือ No','ประวัติโรคหลอดเลือดสมองตามคำตอบ','Input'),('PhysicalHealth','ตัวเลข','จำนวนวันที่สุขภาพกายไม่ดีใน 30 วันที่ผ่านมา','Input'),('MentalHealth','ตัวเลข','จำนวนวันที่สุขภาพจิตไม่ดีใน 30 วันที่ผ่านมา','Input'),('DiffWalking','Yes หรือ No','มีความลำบากในการเดินหรือขึ้นบันได','Input'),('Sex','หมวดหมู่','Female หรือ Male ตามไฟล์','Input'),('AgeCategory','หมวดหมู่','ช่วงอายุ 13 ระดับจาก 18–24 ถึง 80 or older','Input'),('Race','หมวดหมู่','กลุ่มเชื้อชาติ 6 ระดับตามไฟล์','Input'),('Diabetic','หมวดหมู่','4 ค่า รวม borderline และ during pregnancy ไม่ยุบเป็น 2 ค่า','Input'),('PhysicalActivity','Yes หรือ No','การมีกิจกรรมทางกายตามแบบสำรวจ','Input'),('GenHealth','หมวดหมู่','การประเมินสุขภาพทั่วไป 5 ระดับ','Input'),('SleepTime','ตัวเลข','ชั่วโมงการนอนตามคำตอบ','Input'),('Asthma','Yes หรือ No','ประวัติหอบหืดตามคำตอบ','Input'),('KidneyDisease','Yes หรือ No','ประวัติโรคไตตามคำตอบ','Input'),('SkinCancer','Yes หรือ No','ประวัติมะเร็งผิวหนังตามคำตอบ','Input'),('AnyUnhealthyDays','หมวดหมู่ 2 ค่า','Yes เมื่อ PhysicalHealth>0 หรือ MentalHealth>0 สร้างโดยไม่ใช้ Target','Derived'),('SplitSet','train หรือ test','ตัวควบคุมการแบ่งข้อมูลของ Workshop 5 ตัดออกก่อนฝึก','Excluded')]
pd.DataFrame(dictionary[:-1],columns=['attribute','type_th','definition_th','role']).to_csv(W4/'data_dictionary.csv',index=False,encoding='utf-8-sig');pd.DataFrame(dictionary,columns=['attribute','type_th','definition_th','role']).to_csv(W5/'data_dictionary.csv',index=False,encoding='utf-8-sig')

# Workshop4 report
a=[P('การเตรียมข้อมูลสุขภาพหัวใจ',title)];para(a,'Workshop 4  Data Preparation  ชุดข้อมูลปี 2020')
para(a,'งานนี้ตรวจคุณภาพ heart_2020_cleaned.csv และสร้างข้อมูลที่ทำซ้ำได้สำหรับ Workshop 5 โดยรักษาคำตอบและจำนวนผู้ตอบครบเดิม ผลเตรียมผ่าน AI Studio native engine แบบ official batch ตรวจแล้วว่าครบ 319,795 แถว 19 คอลัมน์ และค่าเดิมทุกช่องไม่เปลี่ยน ส่วนการใช้ Turbo Prep และภาพหน้าจอ GUI ยังรอหลักฐานจริง' if N4 else 'งานนี้ตรวจคุณภาพและเตรียมข้อมูลจากไฟล์จริง ส่วน native engine และ Turbo Prep GUI ยังรอการยืนยัน')
h(a,'ขอบเขตและข้อมูลต้นทาง');para(a,'เลือกไฟล์ปี 2020 จาก Dataset ที่อาจารย์โพสต์ตามขอบเขตที่ผู้ใช้อนุมัติ ไม่อ้างว่า Classroom ระบุเวอร์ชันนี้โดยละเอียด เป้าหมาย HeartDisease เป็นการจำแนกคำตอบประวัติโรคหัวใจย้อนหลัง เป็น label Yes/No ไม่ใช่วันเกิดโรคในอนาคต')
table(a,['รายการ','ก่อนเตรียม','หลังเตรียม'],[['ระเบียน','319,795','319,795'],['คอลัมน์','18','19'],['ค่าว่างจริง','0','0'],['Yes','27,373','27,373'],['No','292,422','292,422'],['แถวซ้ำทุกคอลัมน์','18,078','18,078']],[225,145,145])
para(a,'เก็บต้นฉบับทั้ง bytes ไว้ data/heart_2020_cleaned.csv และสำเนาชื่อเดิมข้าง .rmp ไฟล์ heart_2020_prepared.csv เป็นผลเตรียมที่แยกออกมา มีตัวแปรใหม่ AnyUnhealthyDays โดยคอลัมน์เดิมทุกค่าและ Target ไม่เปลี่ยน')
h(a,'เหตุผลการจัดการคุณภาพ');para(a,'ไม่เติมค่าว่างเพราะไม่พบค่าว่าง ไม่ลบ 18,078 แถวที่มีค่าตรงกันทุกช่องเพราะข้อมูลไม่มีรหัสผู้ตอบ คนต่างคนอาจมี profile เดียวกัน การลบอาจเปลี่ยนน้ำหนักเชิงจำนวนของคำตอบ สำหรับการแบ่งโมเดลจะจัด profile ที่มี inputs เหมือนกันไว้ชุดเดียวกันเพื่อป้องกันการปะปนข้าม train/test')
para(a,'ค่าปลายของ BMI และชั่วโมงนอนไม่ถูกลบโดยอัตโนมัติ เกณฑ์ IQR ใช้ระบุค่าที่ควรทบทวน ไม่ได้พิสูจน์ว่าค่าทางสุขภาพผิด จึงเก็บค่าเดิมและบันทึกจำนวน flag')
page(a);h(a,'พจนานุกรมข้อมูล');table(a,['ตัวแปร','ชนิด','ความหมาย'],[[x[0],x[1],x[2]] for x in dictionary[:-1]],[110,90,315]);page(a)
h(a,'ผลตรวจตัวเลขและค่าผิดปกติ');table(a,['ตัวแปร','ต่ำสุด','มัธยฐาน','สูงสุด','IQR flags'],[[c,f'{v["min"]:g}',f'{v["median"]:g}',f'{v["max"]:g}',f'{v["iqr_flag_count"]:,}'] for c,v in Q['numeric'].items()],[155,80,95,80,105],padding=4)
para(a,'สูตร flag คือค่าต่ำกว่า Q1 − 1.5×IQR หรือสูงกว่า Q3 + 1.5×IQR ไม่มีการ winsorize หรือ drop แถว พบ BMI ตั้งแต่ 12.02 ถึง 94.85 และ SleepTime 1 ถึง 24 ชั่วโมง ซึ่งควรตรวจบริบทต้นทาง แต่ไม่มีหลักฐานรายแถวว่าผิด จึงยังไม่แก้ค่า')
para(a,'การตรวจตรรกะพบ 0 แถวที่ BMI≤0, PhysicalHealth/MentalHealth อยู่นอก 0–30 วัน หรือ SleepTime อยู่นอก 0–24 ชั่วโมง ตัวเลขนี้เป็นการตรวจขอบเขตคำตอบ ไม่ใช่การรับรองความถูกต้องทางการแพทย์')
h(a,'การเปลี่ยนแปลงที่ทำจริง');table(a,['ขั้นตอน','แถวหลังขั้นตอน','การดำเนินการ'],[['นำเข้าต้นฉบับ','319,795','อ่าน comma CSV และตรวจชนิด'],['ค่าว่างและแถวซ้ำ','319,795','ตรวจและเก็บทุกแถวตามเหตุผล'],['Outlier','319,795','บันทึก flags ไม่ตัดค่า'],['สร้าง AnyUnhealthyDays','319,795','Yes ถ้ามี PhysicalHealth>0 หรือ MentalHealth>0'],['ส่งต่อ Workshop 5','319,795','เพิ่ม fixed group split แยกใน modeling CSV']],[160,100,255],padding=4)
para(a,'ตรวจแล้วว่า prepared CSV รักษาคอลัมน์เดิมทุกค่าและ Target counts ครบเดิม SHA-256 ของต้นฉบับกับสำเนาตรงกัน Feature ใหม่สร้างโดยไม่ใช้ Target')
h(a,'ผล native และหลักฐานที่ยังต้องทำ');para(a,'AI Studio 2026.1.1 official batch รัน RMP สำเร็จวันที่ 11 ตุลาคม 2026 ได้ heart_2020_prepared_native.csv ผลตรวจยืนยันค่าเดิมทั้งหมดและ AnyUnhealthyDays ทุกแถว บันทึกอยู่ใน native_batch.log และ native_batch_verification.json')
para(a,'ย้ายสำเนาไปอีกโฟลเดอร์และรันด้วย native batch สำเร็จ ผล CSV ตรงกับการรันหลักทุก bytes ต้นฉบับคง bytes เดิม ส่วน Turbo Prep GUI และภาพ process/results ยังรอหลักฐานจริง' if PORTABLE else 'หลักฐาน Turbo Prep GUI ภาพ process/results และการย้ายทั้งโฟลเดอร์แล้วรันซ้ำยังรอการตรวจจริง ต้นฉบับยังคง bytes เดิม')
sources(a,'BI06 Data Preparation หน้า PDF 1–3 สไลด์ 1–11 โดยเฉพาะ Data Quality และ Turbo Prep สไลด์ 4 และ 9–11');screenshots(a,W4);make_pdf(a,W4/'Workshop4_Data_Preparation_Report.pdf','Workshop 4  Heart Data Preparation')

# Workshop5 report
b=[P('การสร้างและประเมินโมเดลสุขภาพหัวใจ',title)];para(b,'Workshop 5  Modeling and Evaluation  ต่อจากข้อมูล Workshop 4')
para(b,'เลือกใช้ 5 เทคนิคทั่วไปตามสไลด์และขอบเขตที่อนุมัติ Classroom ไม่มีรายละเอียดจำนวนโมเดลเฉพาะ จึงไม่อ้างว่าอาจารย์ยืนยัน 5 เทคนิค ผลหลักมาจาก AI Studio native engine ผ่าน official batch แยกจาก Python reference ภาพ GUI และ Turbo Prep ยังรอหลักฐานจริง' if N is not None else 'เลือก 5 เทคนิคตามขอบเขตที่อนุมัติ ผลปัจจุบันเป็น Python reference ส่วน native engine และภาพ GUI ยังรอยืนยัน')
h(b,'เป้าหมายและ Inputs');para(b,'HeartDisease เป็น label สองค่า โดย Yes เป็น positive class ใช้ตัวแปรเดิม 17 ตัวและ AnyUnhealthyDays รวม 18 inputs ไม่ใช้ Target หรือ SplitSet เป็น inputs และไม่ใส่ SourceRow/hash เป็นตัวแปรทำนาย งานเป็นการเรียนจำแนกคำตอบประวัติในไฟล์ ไม่ใช่การประมาณโอกาสเกิดโรคอนาคต')
h(b,'การแบ่งข้อมูลและป้องกันข้อมูลรั่ว');para(b,'จัดกลุ่มด้วยค่าของ 17 predictors เดิมทั้งหมด โดยไม่ใช้ label เป็นตัวกำหนด profile แล้วใช้ StratifiedGroupKFold 10 folds, shuffle seed 2026 เลือก folds 0–2 เป็น test และ 3–9 เป็น train ทำให้ profile เดียวกันไม่ปรากฏข้ามชุดโดยยังเก็บทุกผู้ตอบ')
table(b,['รายการ','Train','Test'],[['ระเบียน',f'{S["train_rows"]:,}',f'{S["test_rows"]:,}'],['HeartDisease Yes',f'{S["train_positive"]:,}',f'{S["test_positive"]:,}'],['สัดส่วน Yes',f'{S["train_positive_rate"]:.4%}',f'{S["test_positive_rate"]:.4%}'],['profile ข้ามชุด','0','0']],[225,145,145])
para(b,'ทุกโมเดลใช้ split เดียวกันตรงกับ SplitSet ใน heart_2020_modeling.csv และ split_assignment.csv Encoding กับ scaling fit เฉพาะ train แล้ว apply test ทดสอบค่า BMI สุดโต่งและหมวดหมู่ที่เกิดเฉพาะ held-out ว่าไม่ถูกเรียนรู้ใน training parameters แล้วคืนข้อมูลก่อนรันจริง')
para(b,'สัดส่วนระเบียนใน cleaned extract เป็นสถิติของไฟล์นี้ ไม่มี survey weights ในชุดคอลัมน์นี้ จึงไม่ตีความ 8.56% เป็นความชุกของประชากรสหรัฐ จาก CDC BRFSS ต้นฉบับมีวิธีสุ่มและ weighting ที่ต้องใช้อย่างเหมาะสมเมื่อประมาณระดับประชากร')
if N is not None:
 page(b);h(b,'ผลหลักจาก native AI Studio official batch')
 para(b,'รันกระบวนการจริงด้วย ai-studio-batch.bat ใน AI Studio 2026.1.1 ใช้ training 223,855 และ test 95,940 แถวตาม fixed profile split เดียวกันทุกโมเดล positive class คือ HeartDisease Yes การตรวจ metrics ใช้ confusion counts ของ native exports')
 table(b,['โมเดล','Accuracy','Precision Yes','Recall Yes','F1 Yes','ROC AUC'],[[r.model]+[f'{getattr(r,c):.4f}' for c in ['accuracy','precision_yes','recall_yes','f1_yes','roc_auc']] for r in N.itertuples()],[130,75,80,75,75,80])
 table(b,['โมเดล','TN','FP','FN','TP'],[[r.model]+[f'{getattr(r,c):,}' for c in ['tn','fp','fn','tp']] for r in N.itertuples()],[195,80,80,80,80])
 winner=N.sort_values('f1_yes',ascending=False).iloc[0]
 para(b,f"เมื่อใช้ F1 Yes เป็นเกณฑ์ {winner['model']} สูงสุด {winner['f1_yes']:.4f} โดย Precision {winner['precision_yes']:.4f} และ Recall {winner['recall_yes']:.4f} พลาด Yes {int(winner['fn']):,} แถว จึงต้องอ่านความผิดพลาดร่วมกับ Accuracy และไม่ตีความเป็นการทำนายโรคในอนาคต")
 runnerup=N.sort_values('f1_yes',ascending=False).iloc[1];rf=N[N.model.eq('Random Forest')].iloc[0]
 para(b,f"F1 ของสองอันดับแรกต่างกัน {winner['f1_yes']-runnerup['f1_yes']:.4f} จึงไม่ใช่หลักฐานความต่างอย่างมีนัยสำคัญ ส่วน Random Forest มี Accuracy {rf['accuracy']:.4f} แต่ Recall {rf['recall_yes']:.4f} และ FN {int(rf['fn']):,} แสดงว่าการเลือกจาก Accuracy เพียงค่าเดียวอาจมองข้ามความผิดพลาดของกลุ่ม Yes",small)
 para(b,'ครั้งแรกเกิด Java heap OOM ที่ Random Forest แบบ parallel จึงปิด enable_parallel_execution ตามคำแนะนำของ installed operator manual แล้วรันใหม่ด้วย heap 3 GB คง 100 trees, depth 12, leaf 10, seed 2026 และข้อมูลทุกแถวเดิม ไม่ลดขนาด train/test ตารางนี้ใช้ exports ใหม่จากการรันที่สำเร็จครบห้าโมเดลเท่านั้น',small)
page(b);h(b,'โมเดลและผล Python reference');para(b,'ใช้ scikit-learn จาก runtime ที่เตรียมไว้ positive Yes, threshold 0.5 ไม่ปรับ hyperparameter หรือ threshold จาก test นี้ เลือกทั้งห้าเพื่อเปรียบเทียบพฤติกรรมของโมเดล ไม่ใช่ผล Auto Model ที่เก็บจาก GUI')
table(b,['โมเดล','ค่าตั้งต้น Python reference'],[['Naive Bayes','GaussianNB var_smoothing=1e−9'],['Logistic Regression','C=1 balanced weights max_iter=1500'],['Decision Tree','depth=8 leaf=30 balanced weights'],['Random Forest','100 trees depth=12 leaf=10 balanced weights'],['Gradient Boosted Trees','60 trees depth=3 leaf=20 learning_rate=0.1']],[155,360])
table(b,['โมเดล','Accuracy','Precision Yes','Recall Yes','F1 Yes','Average Precision'],[[r.model]+[f'{getattr(r,c):.4f}' for c in ['accuracy','precision_yes','recall_yes','f1_yes','average_precision']] for r in M.itertuples()],[125,70,80,70,70,100])
para(b,'Baseline ทาย No ทั้งหมดได้ Accuracy '+f'{1-S["test_positive_rate"]:.4f}'+' แต่ Recall และ F1 ของ Yes เป็น 0 ค่า Average Precision ของการจัดอันดับสุ่มมีฐานประมาณ '+f'{S["test_positive_rate"]:.4f}'+'. Class imbalance จึงต้องอ่าน Precision/Recall/F1 และความผิดพลาดร่วมกับ Accuracy',small)
storyimg=Image(str(W5/'reference_model_comparison.png'),width=510,height=245);b.append(storyimg);para(b,'รูปจากผล Python reference เท่านั้น ไม่ใช่ภาพ Results ของ AI Studio',small)
page(b);h(b,'การประเมินและข้อผิดพลาดของ Python reference');table(b,['โมเดล','TN','FP','FN','TP'],[[r.model]+[f'{getattr(r,c):,}' for c in ['tn','fp','fn','tp']] for r in M.itertuples()],[195,80,80,80,80])
para(b,'TN คือทาย No ถูก FP คือทาย Yes แต่จริง No FN คือพลาด Yes และ TP คือทาย Yes ถูก ทุกแถวในตารางรวมเป็น 95,940 test rows และตรวจคำนวณ metrics กลับจาก confusion counts ได้')
para(b,'Random Forest มี F1 0.3477 และ Logistic Regression 0.3476 ต่างกันประมาณ 0.0001 จึงยังไม่มีหลักฐานเพียงพอให้เลือกจากช่อง F1 นี้เพียงอย่างเดียว Logistic Regression มี Average Precision 0.3444 และ ROC AUC 0.8387 สูงสุดใน reference ชุดนี้ พร้อมโมเดลที่อธิบายสัมประสิทธิ์ได้ จึงเป็นตัวเลือกเพื่อศึกษาต่อภายใต้เกณฑ์เชิงการเรียนรู้')
para(b,'อย่างไรก็ตาม Logistic Regression มี FP 22,009 และ Precision 0.2241 จึงเห็นผลของการใช้ balanced class weights และความไม่สมดุล ส่วน Gradient Boosted Trees มี Accuracy 0.9159 และ Precision 0.5566 แต่ Recall เพียง 0.0862 พลาด Yes 7,504 แถว จึงไม่ควรเลือกจาก Accuracy สูงสุดเพียงค่าเดียว')
para(b,'Decision Tree ให้ Recall 0.7921 สูงสุด แต่มี FP 26,765 ขณะที่ Naive Bayes ให้ Recall 0.7140 และ F1 0.3321 ผลทั้งหมดเป็น association ในคำตอบย้อนหลัง ไม่มีการทดสอบภายนอกหรือข้อมูลในอนาคตเพื่อยืนยันการใช้งานอื่น')
h(b,'การนำผลไปใช้ต่อ');para(b,'สำหรับ Workshop ใช้ความต่างของโมเดลอธิบาย tradeoff และตรวจผลจากโปรแกรมจริง ขั้นต่อไปควรเลือก threshold ด้วย validation ที่แยกจาก test, ประเมินความคงที่ของผล และทบทวนความหมายของ features ที่เกี่ยวกับโรคเดิม เป้าหมายคืออธิบายสิ่งที่โมเดลเรียนได้จากข้อมูลนี้ก่อนขยายขอบเขต')
page(b);h(b,'กระบวนการและหลักฐาน native AI Studio');para(b,'Workshop5_Modeling_Evaluation.rmp อ่าน heart_2020_modeling.csv และกำหนด HeartDisease label ใช้ Filter Examples แบ่ง SplitSet=train ออกทาง matched ส่วน test ออกทาง unmatched จากนั้นตัด SplitSet ก่อน training-only encoding/scaling และใช้ชุดเดียวกันในห้าแขนง')
para(b,'ใช้ Naive Bayes core, H2O Logistic Regression, parallel Decision Tree, parallel Random Forest และ H2O Gradient Boosted Trees ที่ตรวจ operator IDs/ports จากไฟล์ติดตั้งจริง Python และ native implementations/weights/defaults ต่างกัน จึงต้องบันทึกผล native แยก ไม่อ้างว่าผลจะเท่าตาราง reference')
para(b,'พอร์ต Result 1–5 คือ Performance, 6–10 คือ scored test, 11–15 คือ models และ 16–20 คือ metric tables หลัง Run จริง Performance to Data ส่งออก native_NB.csv, native_LR.csv, native_DT.csv, native_RF.csv และ native_GBT.csv ผ่าน Write CSV โดยไม่ต้องถอดตัวเลขจากภาพ')
para(b,'ต้องเปิด .rmp แบบไฟล์ในเครื่องพร้อม original heart_2020_cleaned.csv และ derived heart_2020_modeling.csv ในโฟลเดอร์เดียวกัน ตรวจ macros ที่อ้าง process_path/process_file แล้ว Run ทั้งกระบวนการ เก็บภาพ setup, process และ performance/confusion matrix ทั้งห้า จากนั้นย้ายทั้งโฟลเดอร์และเปิด Run ใหม่')
para(b,('สถานะ: native batch รันสำเร็จครบห้าโมเดล ส่งออก native_NB/LR/DT/RF/GBT.csv และผ่านการตรวจ confusion reconciliation จำนวน test 95,940 และ positive Yes 8,212 ทุกโมเดล รวม hash/เวลา exports ใน native_metrics_provenance.json ผล Python reference เก็บแยก '+('การย้ายสำเนาไปโฟลเดอร์ใหม่และ native batch รันซ้ำผ่านแล้ว ผลห้าโมเดลตรงกับการรันหลัก ดู docs/execution/native-portability-verification.json ภาพ GUI และ Turbo Prep ยังรอหลักฐานจริง' if PORTABLE else 'ภาพ GUI, Turbo Prep และ relocated Run ยังรอหลักฐานจริง')) if N is not None else 'สถานะ: native engine และหลักฐาน GUI ยังรอการยืนยัน')
sources(b,'BI07 Data Model หน้า PDF 4 สไลด์ 13–15 เรื่อง train/test หน้า 12 สไลด์ 45–46 เรื่อง imbalance และหน้า 15 สไลด์ 57–60 เรื่อง Logistic Regression');screenshots(b,W5);make_pdf(b,W5/'Workshop5_Modeling_Evaluation_Report.pdf','Workshop 5  Heart Modeling and Evaluation')
print('WS4 and WS5 Thai PDFs created with distinct native batch, Python reference and pending GUI provenance')
