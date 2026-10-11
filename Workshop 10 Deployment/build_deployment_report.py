"""Build the Workshop 10 report after root confirms native Desktop acceptance."""
from pathlib import Path
import json,html
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

folder=Path(__file__).resolve().parent
results=json.loads((folder/'forecast_verification.json').read_text(encoding='utf-8'))
proof_path=folder/'offline'/'native_acceptance.json'
if not proof_path.exists():
    raise SystemExit('Native acceptance receipt required before publishing the report')
proof=json.loads(proof_path.read_text(encoding='utf-8'))
assert proof['refresh_passed'] and proof['pbix_saved'] and proof['pbix_reopened']
assert proof['forecast_rows']==26 and proof['model_rows']==5
assert proof['selected_model']=='Random Forest' and proof['future_forecast']==204586
assert proof['future_actual_is_blank']
assert proof['card_forecast_exact'] and proof['card_mae_two_decimals'] and proof['line_data_labels_hidden']
shot=Path(proof['screenshot'])
pbix=Path(proof['pbix'])
assert shot.is_file() and pbix.is_file()
pdfmetrics.registerFont(TTFont('ReportArial','C:/Windows/Fonts/tahoma.ttf',shapable=True))
pdfmetrics.registerFont(TTFont('ReportArialBold','C:/Windows/Fonts/tahomabd.ttf',shapable=True))
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyReport',fontName='ReportArial',fontSize=11,leading=16,spaceAfter=9,wordWrap='CJK',shaping=True))
styles.add(ParagraphStyle(name='TitleReport',fontName='ReportArialBold',fontSize=21,leading=29,spaceAfter=16,shaping=True))
styles.add(ParagraphStyle(name='HeadReport',fontName='ReportArialBold',fontSize=14,leading=20,spaceBefore=10,spaceAfter=9,shaping=True))
styles.add(ParagraphStyle(name='CellReport',fontName='ReportArial',fontSize=10,leading=15,wordWrap='CJK',shaping=True))
styles.add(ParagraphStyle(name='HeaderReport',fontName='ReportArialBold',fontSize=10,leading=15,shaping=True))
def p(text,style='BodyReport'):
    return Paragraph(html.escape(str(text)).replace('\n','<br/>'),styles[style])
def table(headers,rows,widths):
    content=[[p(x,'HeaderReport') for x in headers]]+[[p(x,'CellReport') for x in row] for row in rows]
    t=Table(content,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.4,colors.HexColor('#D9D9D9')),
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E9EEF2')),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F7F9FA')]),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),('TOPPADDING',(0,0),(-1,-1),7),
        ('BOTTOMPADDING',(0,0),(-1,-1),7),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7)]))
    return t
story=[
    p('การพยากรณ์รถจดทะเบียนครั้งแรก','TitleReport'),
    p('รายงาน Workshop 10 Deployment ตรวจผลวันที่ 11 ตุลาคม 2569'),
    p(f'ผลเปรียบเทียบ 5 วิธีจากข้อมูลจริงเลือก Random Forest เพราะมี MAE ทดสอบต่ำที่สุด เมื่อฝึกใหม่ด้วยข้อมูลแบบจำลองทั้งหมด พยากรณ์กุมภาพันธ์ 2569 ได้ {results["future_prediction_unrounded"]:,.6f} คัน ส่งออกและแสดงบนการ์ดเป็น {results["future_prediction_rounded"]:,} คัน ได้ตรวจ Refresh ใน Power BI Desktop บันทึกไฟล์ PBIX ปิดและเปิดซ้ำ พร้อมตรวจตัวเลขอีกครั้งแล้ว'),
    p('ข้อมูลต้นฉบับและการเตรียมรายเดือน','HeadReport'),
    table(['รายการตรวจ','ผลที่คำนวณได้'],[
        ['ข้อมูลต้นฉบับ','68,398 แถว 9 คอลัมน์'],['รวมยอดรายเดือน','49 เดือน ใช้ปีและเดือนจาก Source'],
        ['เดือนที่ขาดหาย','ธันวาคม 2566'],['เดือนข้อมูลไม่ครบที่ตัดออก','กุมภาพันธ์ 2569 มี 6 records รวม 18 คัน'],
        ['ช่วงต่อเนื่องที่ใช้','มกราคม 2567 ถึงมกราคม 2569 รวม 25 เดือน'],
        ['Lag1 ถึง Lag3','เหลือ 22 ตัวอย่างสำหรับสร้างแบบจำลอง'],['ชุดฝึก','เมษายน 2567 ถึงมิถุนายน 2568 รวม 15 เดือน'],
        ['ชุดทดสอบ','กรกฎาคม 2568 ถึงมกราคม 2569 รวม 7 เดือน'],
    ],[180,324]),Spacer(1,12),
    p('จำนวนคันคือค่าที่นำมารวม ส่วน records คือจำนวนแถวต้นทางตามประเภทรถ ยี่ห้อและรุ่น จึงไม่ใช่หน่วยเดียวกัน ไม่เติมเดือนที่ขาดหรือข้อมูลไม่ครบเป็นยอดจริงศูนย์'),
    p('วิธีแบ่งข้อมูลและประเมิน','HeadReport'),
    p('เรียงตามเวลาและไม่สุ่มสลับแถว ทุกวิธีใช้ชุดฝึก 15 เดือนและชุดทดสอบ 7 เดือนเดียวกัน การทดสอบพยากรณ์ล่วงหน้าทีละหนึ่งเดือน ใช้ยอดจริงเดือนก่อนที่ทราบแล้วเป็น Lag ได้ แต่ไม่ใช้ยอดจริงของเดือนเป้าหมายหรืออนาคตมาฝึก จึงไม่ใช่การพยากรณ์ 7 เดือนพร้อมกันจากจุดเริ่มต้นเดียว'),
    p('ไฟล์ต้นทาง '+results['source_file']+'\nSHA256 '+results['source_sha256']),
    PageBreak(),
    p('ผลเปรียบเทียบและค่าพยากรณ์','HeadReport'),
    table(['วิธี','MAE คัน','RMSE คัน','R²'],[[r['Model'],f'{r["MAE"]:,.2f}',f'{r["RMSE"]:,.2f}',f'{r["R2"]:.4f}'] for r in results['comparison']],[180,108,108,108]),Spacer(1,12),
    p('พารามิเตอร์และการฝึกครั้งสุดท้าย','HeadReport'),
    p('Linear Regression ใช้ค่าปริยาย Ridge ใช้ alpha=1.0 Random Forest ใช้ 100 ต้นไม้ ความลึกสูงสุด 3 และ seed=42 ส่วน Gradient Boosting ใช้ 100 รอบ learning_rate=0.05 ความลึก 2 และ seed=42 วิธี Naive ใช้ Lag1 โดยไม่ต้องฝึกโมเดล'),
    p('หลังประเมินจึงฝึก Random Forest ใหม่ด้วย 22 ตัวอย่างทั้งหมด ใช้ยอดมกราคม 2569 จำนวน 250,212 คัน ธันวาคม 2568 จำนวน 184,093 คัน และพฤศจิกายน 2568 จำนวน 177,066 คันเป็น Lag1 ถึง Lag3 ตามลำดับ โดยไม่ใช้ข้อมูลกุมภาพันธ์ที่ไม่ครบเป็น Actual'),
    Image(str(folder/'actual_vs_forecast.png'),width=504,height=233),Spacer(1,10),
    p('ผลที่คำนวณเองตรงกับตัวอย่างในสไลด์โดยไม่ได้ใช้ไฟล์ตัวอย่าง .xls แทนการคำนวณ เดือนมกราคม 2569 มียอดจริง 250,212 คัน แต่ทำนายได้ 200,390.88 คัน จึงมีความคลาดเคลื่อนสูง ค่า R²=0.2040 เป็นการอธิบายความแปรปรวนเทียบค่าเฉลี่ยของชุดทดสอบ ไม่ใช่ความแม่นยำ 20.4%'),
    PageBreak(),
    p('ผลตรวจใน Power BI Desktop','HeadReport'),
    table(['รายการตรวจจริง','ผลที่ตรวจพบ'],[
        ['Refresh','ผ่านการ Refresh แบบ Full'],['จำนวนแถวและวิธี','Forecast 26 แถว และ Comparison 5 วิธี'],['โมเดลที่เลือก','Random Forest'],
        ['MAE และ RMSE',f'{proof["mae"]:,.6f} และ {proof["rmse"]:,.6f} คัน'],['R²',f'{proof["r2"]:.10f}'],
        ['การ์ด Future และ Actual','204,586 คัน และ Actual ว่าง'],['ไฟล์ที่บันทึกและเปิดซ้ำ',pbix.name],
    ],[180,324]),Spacer(1,12),
    Image(str(shot),width=504,height=234),Spacer(1,10),
    p('ภาพจริงจาก Power BI หลังแก้รูปแบบ การ์ดแสดง MAE 14,208.36 และ Forecast 204,586 โดยไม่ย่อเป็น K ซ่อนป้ายซ้ำที่เคยถูกตัด และปิดป้ายตัวเลขบนเส้นเพื่อให้ดูแนวโน้มชัดเจน เมื่อตรวจตัวกรอง Future พบเฉพาะจุดพยากรณ์และไม่มี Actual บันทึกตัวกรองกลับเป็น All แล้ว'),
    p('ข้อจำกัดและไฟล์ประกอบ','HeadReport'),
    p('แบบจำลองมีเพียง 22 ตัวอย่าง ชุดทดสอบ 7 เดือน ใช้ยอดย้อนหลัง 3 เดือนและไม่มีปัจจัยภายนอก การเลือกโมเดลใช้ชุดทดสอบเดียวกันโดยยังไม่มีชุด Validation อิสระ ผลจึงเหมาะกับการเรียนรู้และควรตรวจเพิ่มก่อนใช้วางแผนจริง'),
    p('ไฟล์ประกอบมี Notebook ที่รันครบ ข้อมูลดิบ CSV ที่คำนวณเอง 2 ไฟล์ สรุปหนึ่งย่อหน้าและ PBIX การทดสอบข้อมูลผ่าน 6 ข้อ เก็บไฟล์ .xls ต้นฉบับไว้เป็นตัวอย่าง'),
]
def footer(canvas,document):
    canvas.setFont('ReportArial',9);canvas.setFillColor(colors.HexColor('#606C76'))
    canvas.drawString(54,25,'Workshop 10 Vehicle Registration Forecasting')
    canvas.drawRightString(558,25,f'Page {document.page}')
path=folder/'Workshop10_Deployment_Report.pdf'
SimpleDocTemplate(str(path),pagesize=letter,leftMargin=54,rightMargin=54,topMargin=42,bottomMargin=42).build(story,onFirstPage=footer,onLaterPages=footer)
print(path)
