from pathlib import Path
import json,csv,sys
from xml.sax.saxutils import escape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image,KeepTogether
from reportlab.graphics.shapes import Drawing,Rect,String,Line,Circle,PolyLine

ROOT=Path(r'D:\Github\BI 2026'); W8=ROOT/'Workshop 8 Data Analysis Expressions (DAX)'; W9=ROOT/'Workshop 9 Dashboard'
s8=json.loads((W8/'analysis/validated_values.json').read_text(encoding='utf-8'));s9=json.loads((W9/'analysis/validated_values.json').read_text(encoding='utf-8'))
pdfmetrics.registerFont(TTFont('Thai',r'C:\Windows\Fonts\tahoma.ttf',shapable=True));pdfmetrics.registerFont(TTFont('ThaiBold',r'C:\Windows\Fonts\tahomabd.ttf',shapable=True))
P=ParagraphStyle('body',fontName='Thai',fontSize=10,leading=17,shaping=1,spaceAfter=9,wordWrap='CJK')
H=ParagraphStyle('heading',parent=P,fontName='ThaiBold',fontSize=18,leading=26,textColor=colors.HexColor('#17324D'),spaceAfter=14)
SM=ParagraphStyle('small',parent=P,fontSize=8.5,leading=13)
def para(t,sty=P): return Paragraph(escape(t).replace('\n','<br/>'),sty)
def num(v,pct=False):return f'{v*100:,.2f}%' if pct else f'{v:,.2f}' if isinstance(v,float) else f'{v:,}'
def table(rows,widths=None):
    data=[[para(str(c),SM) for c in row] for row in rows]
    t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E5EDF4')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,0),0.5,colors.HexColor('#17324D')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F6F8FA')])]))
    return t
def chart(labels,values,title,other=None,pct=False,line=False):
    d=Drawing(500,230);left=112 if not line else 24;top=192;bottom=24;right=475
    d.add(String(0,215,title,fontName='Helvetica-Bold',fontSize=10,fillColor=colors.HexColor('#17324D')))
    if other is not None:d.add(String(0,201,'Blue = Total Sales | Gold = Total Profit | THB',fontName='Helvetica',fontSize=8,fillColor=colors.HexColor('#5C6670')))
    maximum=max(values+(other or []))*1.12
    if line:
        points=[]
        for i,(lab,val) in enumerate(zip(labels,values)):
            x=left+i*(right-left)/(len(values)-1);y=bottom+val/maximum*(top-bottom);points.extend([x,y])
            d.add(Circle(x,y,3,fillColor=colors.HexColor('#277C9B'),strokeColor=None));d.add(String(x-8,8,str(lab),fontSize=7));d.add(String(x-14,y+8,f'{val/1e6:.2f}M',fontSize=7))
        d.add(PolyLine(points,strokeColor=colors.HexColor('#277C9B'),strokeWidth=2));d.add(Line(left,bottom,right,bottom,strokeColor=colors.HexColor('#A6B4BE')))
    else:
        rowh=(top-bottom)/len(values)
        for i,(lab,val) in enumerate(zip(labels,values)):
            y=top-(i+1)*rowh+4
            d.add(String(0,y+3,str(lab),fontName='Helvetica',fontSize=8))
            width=val/maximum*(right-left-70);height=min(16,rowh-5) if other is None else min(8,(rowh-5)/2)
            d.add(Rect(left,y,width,height,fillColor=colors.HexColor('#277C9B'),strokeColor=None));d.add(String(left+width+4,y+2,num(val,pct),fontSize=7.5))
            if other is not None:
                w2=other[i]/maximum*(right-left-70)
                d.add(Rect(left,y-height-2,w2,height,fillColor=colors.HexColor('#B8873D'),strokeColor=None));d.add(String(left+w2+4,y-height,num(other[i]),fontSize=7.5))
    d.add(String(0,0,'Independent calculation from source Excel; this is not a Power BI screenshot.',fontSize=7,fillColor=colors.HexColor('#5C6670')))
    return d
def footer(c,d):
    c.setFont('Helvetica',8);c.setFillColor(colors.HexColor('#647482'));c.drawString(42,24,'BI 2026 | Desktop evidence + independent reconciliation');c.drawRightString(553,24,str(d.page))
def csvout(p,rows):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8-sig',newline='') as f:csv.writer(f).writerows(rows)
cases8=[
('H1','Online มียอดขายสูงที่สุด','Channel','Total Sales','ยอมรับ','Online 11,731,434.50 > Store 8,552,028.00 > Corporate 4,282,553.00 บาท','แผนภูมิแท่งแนวนอนเปรียบเทียบทุกช่องทางโดยเริ่มแกนที่ศูนย์'),
('H2','Computer มียอดขายสูงที่สุด','Category','Total Sales','ยอมรับ','Computer 11,138,040.00 บาท สูงสุด รองลงมา Mobile 6,360,405.00 บาท','กราฟคอลัมน์เปรียบเทียบหมวดสินค้าโดยใช้มาตราส่วนเดียวกัน'),
('H3','Bangkok มียอดขายสูงที่สุด','Region','Total Sales','ยอมรับ','Bangkok 4,577,602.50 บาท สูงกว่า East 4,363,430.50 บาท และภูมิภาคอื่น','แผนภูมิแท่งช่วยอ่านชื่อพื้นที่และยอดขายแต่ละพื้นที่ได้ชัดเจน'),
('H4','Store มีจำนวนคำสั่งซื้อสูงที่สุด','Channel','Total Orders','ไม่ยอมรับ','Online 673 คำสั่งซื้อ สูงกว่า Store 563 และ Corporate 264','กราฟคอลัมน์เปรียบเทียบจำนวนคำสั่งซื้อ ไม่ใช้จำนวนชิ้นสินค้าแทน'),
('H5','Corporate มีมูลค่าเฉลี่ยต่อคำสั่งซื้อสูงที่สุด','Channel','Average Order Value','ไม่ยอมรับ','Online 17,431.55 > Corporate 16,221.79 > Store 15,190.10 บาทต่อคำสั่งซื้อ','แผนภูมิแท่งเปรียบเทียบ AOV บนสเกลเดียวกัน'),
('H6','Accessories มี Gross Margin % สูงที่สุด','Category','Gross Margin %','ยอมรับ','Accessories 41.77% สูงกว่า Network 37.84% และ Audio 37.41%','แผนภูมิแท่งแสดงร้อยละและจัดอันดับหมวดสินค้าโดยใช้กำไรรวม/ยอดขายรวม'),
('H7','Q4 มียอดขายสูงที่สุด','Quarter','Total Sales','ไม่ยอมรับ','Q1 7,498,947.00 บาท สูงที่สุด ส่วน Q4 4,077,716.00 บาท','กราฟคอลัมน์เรียง Q1-Q4 ตามเวลา รวมไตรมาสชื่อเดียวกันข้ามปี'),
('H8','July มียอดขายสูงที่สุด','MonthName','Total Sales','ไม่ยอมรับ','March 3,037,399.50 บาท สูงกว่า July 2,955,582.00 บาท','กราฟเส้นเรียง Jan-Dec ตาม MonthNo เพื่ออ่านรูปแบบรายเดือน รวมเดือนข้ามปี'),
('H9','ยอดขายปี 2026 สูงกว่าปี 2025','Year','Total Sales','ไม่ยอมรับ','2025 = 13,997,390.00 บาท; 2026 = 10,568,625.50 บาท ตามข้อมูลที่มี','กราฟคอลัมน์แสดงสองปีโดยตรง ปี 2026 มีข้อมูลถึงสิงหาคมเท่านั้น ไม่ใช่การเปรียบเทียบการเติบโตเต็มปี'),
('H10','ช่องทางที่ยอดขายสูงที่สุดมีกำไรสูงที่สุดด้วย','Channel','Total Sales','ยอมรับ','Online สูงสุดทั้งยอดขาย 11,731,434.50 บาท และกำไร 2,347,494.50 บาท','กราฟคอลัมน์แบบกลุ่มแสดงยอดขายและกำไรบนแกนหน่วยบาทเดียวกัน ตรวจอันดับจากตัวเลขจริง')]
def native_visual8(h):
    """Crop an actual reviewed capture, preserving pixels/values; no original PNG is edited."""
    from PIL import Image as PILImage
    n=int(h[1:]);source=W8/'screenshots'/('H1-H5.png' if n<=5 else 'H6-H10.png')
    rects={1:(24,190,764,265),2:(812,190,764,265),3:(24,476,764,265),4:(812,476,764,265),5:(24,762,764,265),6:(24,190,764,310),7:(812,190,764,265),8:(24,520,764,221),9:(812,476,764,265),10:(24,762,764,265)}
    image=PILImage.open(source);assert image.size==(2602,1210),image.size
    scale=1210/1080;x,y,w,hh=rects[n];box=(round(204+x*scale),round(y*scale),round(204+(x+w)*scale),round((y+hh)*scale))
    target=W8/'analysis'/'report_assets'/(h+'_actual_desktop.png');target.parent.mkdir(parents=True,exist_ok=True);crop=image.crop(box);crop.save(target)
    return [Image(str(target),width=510,height=510*crop.height/crop.width),para('ภาพ Power BI Desktop จริง: '+source.name+' (ตัดเฉพาะกราฟจากภาพเดิม; ไม่เปลี่ยนค่าหรือองค์ประกอบกราฟ)',SM)]
def pbix_status(folder,name):
    p=folder/name;assert p.exists() and p.stat().st_size>0,p
    number='8' if folder==W8 else '9';proof=ROOT/'docs'/'execution'/('pbi-ws'+number+'-reopen-dax-result.json')
    envelope=json.loads(proof.read_text(encoding='utf-8'));assert not envelope.get('isError',False)
    result=json.loads(next(c['text']for c in envelope['content']if c['type']=='text'));row=result['data']['rows'][0]
    if folder==W8:assert row['[Sales]']==24566015.5 and row['[Profit]']==4968125.5 and row['[Orders]']==1500 and row['[Qty]']==3062 and abs(row['[AOV]']-row['[Sales]']/row['[Orders]'])<1e-8
    else:assert row['[Tourists]']==285016377 and row['[Countries]']==48
    assert (folder/'screenshots/native_saved_pbix_reopened.png').exists()
    return 'บันทึกไฟล์ '+name+' แล้ว ('+num(p.stat().st_size)+' bytes) และเปิดไฟล์ PBIX ใหม่ในDesktopสำเร็จ. DAXหลังเปิดใหม่ให้ค่าbaselineเดิมตรงครบ; มีภาพnative_saved_pbix_reopened.pngและผลDAX '+proof.name+' เป็นหลักฐาน.'
def build8():
    story=[para('Workshop 8 - ผลตรวจสมมติฐาน DAX',H),para('ข้อมูล: DAX_Lab.xlsx จาก named tables CustomersTable, DateTable, ProductsTable และ SalesTable รวมรายการขาย 1,500 แถว ลูกค้า 120 ราย และสินค้า 20 รายการ'),para('ช่วงปฏิทินของ Lab: มกราคม 2025-สิงหาคม 2026; วันที่ขายที่พบจริง 3 มกราคม 2025-31 สิงหาคม 2026. บริบทหลักของ H1-H10 คือทุกปี ทุกพื้นที่ และทุกช่องทาง โดยไม่เลือก Slicer และไม่เลือกจุดข้อมูลในกราฟ'),table([['KPI','ค่าตรวจสอบ'],*[ [k,num(v,k=='Gross Margin %')] for k,v in s8['Total'].items()]],[220,290]),Spacer(1,14),para('ตรวจ Power BI Desktop จริงแล้ว: เปิดโครงการและ Refresh สำเร็จ; DAX Total Sales 24,566,015.50, Total Profit 4,968,125.50, Orders 1,500, Quantity 3,062 และ AOV 16,377.3436667 ตรงกับการคำนวณต้นทาง. ตรวจภาพทั้ง 3 หน้าแล้ว; H6 แสดงครบ 8 หมวดและ H8 อ่านได้. กราฟ H1-H10 ในผลแต่ละข้อเป็นภาพจริงที่ตัดจาก screenshots ส่วนตัวเลขตารางคงความละเอียดจากต้นทาง.'),para(pbix_status(W8,'Workshop8_DAX.pbix')),PageBreak()]
    csvrows=[['Hypothesis','Statement','Dimension','Measure','Decision','Evidence','Filter Context','Visual Reason']]
    for h,title,key,m,decision,evidence,reason in cases8:
        group=s8[key]
        labels=list(group)
        if key=='MonthName':labels=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        elif key not in ('Quarter','Year'):labels=sorted(group,key=lambda k:group[k][m],reverse=True)
        values=[group[k][m] for k in labels];other=[group[k]['Total Profit'] for k in labels] if h=='H10' else None
        context='All Year / Region / Channel; '+('matching '+key+' combined across 2025-2026' if key in ['Quarter','MonthName'] else 'available source rows')
        story += [para(h+' - '+title,H),para('ผล: '+decision+'สมมติฐาน'),para(evidence),para('เหตุผลเลือก Visual: '+reason),para('Filter Context: '+context),*native_visual8(h),Spacer(1,8),table([[key,m]+(['Total Profit'] if other else []),*[[k,num(group[k][m],m=='Gross Margin %')]+([num(group[k]['Total Profit'])] if other else []) for k in labels]],[150,180,180] if other else [220,290]),PageBreak()]
        csvrows.append([h,title,key,m,decision,evidence,context,reason])
    story += [para('ผลตรวจ Desktop และการเปิด PBIX ใหม่',H),para('โมเดลใช้ความสัมพันธ์ 1:* แบบ Active และ Single จาก Products, Customers, Date ไปยัง Sales; OrderDate/Date เป็นวันที่จริง. UnitPrice/UnitCost เป็น RELATED, SalesAmount คิดส่วนลดระดับแถว, CostAmount ไม่หักส่วนลด, Profit = SalesAmount-CostAmount. Gross Margin % ใช้กำไรรวม/ยอดขายรวม ไม่เฉลี่ย ProfitMargin รายแถว.'),table([['Slicer condition','Expected Sales (THB)','Expected Orders'],*[[k,num(v['Total Sales']),v['Total Orders']] for k,v in s8['slicer_checks'].items()]],[235,155,120]),Spacer(1,12),para('ทดสอบ Slicer Year=2025 จริงแล้ว: Card แสดงยอดขาย 14.00M THB, Orders 873 และ Quantity 1,767; ล้างกลับ All สำเร็จ. ภาพ native_filter_year2025.png เป็นหลักฐาน. ค่า Region/Channel/เงื่อนไข AND ในตารางเป็นเกณฑ์จากต้นทาง แต่ยังไม่ได้บันทึกว่าทดสอบแต่ละเงื่อนไขใน GUI ผ่านแล้ว.'),para(pbix_status(W8,'Workshop8_DAX.pbix')),para('หลังเปิดไฟล์ที่บันทึกใหม่: Sales24,566,015.50, Profit4,968,125.50, Orders1,500, Quantity3,062 และAOV16,377.3436667 ตรงกับค่าก่อนบันทึก. Dashboardปรากฏในภาพเปิดใหม่. ขั้นตอนเปิดPBIP, Refresh, DAXbaseline, ตรวจ3หน้า, YearSlicer, SaveAsPBIXและเปิดใหม่มีหลักฐาน; เงื่อนไขSlicerเพิ่มเติมในตารางไม่ได้เหมารวมว่าทดสอบแล้ว.'),para('PBIR ผ่าน schema/visual roles; TMDL ผ่านทั้ง external TOM และ parser ที่ติดตั้งกับDesktop. มี4ตาราง3ความสัมพันธ์9measures6calculated columns. การเปิดใหม่ครั้งนี้ยืนยันผลจากไฟล์PBIXที่บันทึกจริง.')]
    appendshots(story,W8)
    SimpleDocTemplate(str(W8/'Workshop8_Report.pdf'),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=40,bottomMargin=42,title='Workshop 8 DAX Hypothesis Results',author='BI 2026').build(story,onFirstPage=footer,onLaterPages=footer)
    if '--export-csv' in sys.argv:csvout(W8/'analysis/Hypothesis_Results.csv',csvrows)
def appendshots(story,folder):
    shots=sorted((folder/'screenshots').glob('*.png')) if (folder/'screenshots').exists() else []
    if not shots:return
    from PIL import Image as PILImage
    for path in shots:
        image=PILImage.open(path)
        if image.size==(2602,1210):image=image.crop((204,0,1996,1210))
        elif path.name.startswith('native_filter_') and image.size==(1706,825):image=image.crop((144,160,1040,765))
        target=folder/'analysis'/'report_assets'/('appendix_'+path.name);target.parent.mkdir(parents=True,exist_ok=True);image.save(target);iw,ih=image.size;scale=min(510/iw,600/ih)
        caption='ภาพจริงที่ตรวจแล้ว; แสดงภาพเดิมหรือส่วนของภาพเดิม โดยไม่แก้ค่า/กราฟ. ภาพรวมยืนยันหน้าและบริบท ส่วนตัวเลขละเอียดอยู่ในผลวิเคราะห์.'
        if path.name=='native_filter_year2025.png':caption+=' Year=2025: Orders873, Quantity1767, Sales14.00M THB; คืนค่า All แล้ว.'
        if path.name=='native_filter_Australia.png':caption+=' Australia: กราฟแท่งแสดงประมาณ8M และ Pie100%; คืนค่า All แล้ว.'
        story.extend([PageBreak(),para('หลักฐานจาก Power BI Desktop',H),para(path.name,SM),Image(str(target),width=iw*scale,height=ih*scale),para(caption,SM)])
        if path.name=='native_saved_pbix_reopened.png':
            original=PILImage.open(path);title=original.crop((80,0,650,34));titlepath=folder/'analysis'/'report_assets'/'reopened_window_title.png';title.save(titlepath)
            caption='ขยายชื่อหน้าต่างจากภาพเดียวกัน: ไฟล์PBIXที่บันทึกถูกเปิดใหม่จริง; ค่าDAXหลังเปิดใหม่ยืนยันbaselineเดิม.'
            if folder==W9:caption+=' การเผยแพร่สาธารณะWS9ยังไม่ทำ.'
            story.extend([Spacer(1,8),Image(str(titlepath),width=510,height=510*title.height/title.width),para(caption,SM)])
def build9():
    y=s9['years'];co=s9['continents_2562'];ct=s9['countries_2562'];share=s9['East Asia Share 2562']
    cases=[('H1','ปี 2562 มีนักท่องเที่ยวมากกว่าปี 2553','ยอมรับ',f"2562 = {num(y['2562'])} คน > 2553 = {num(y['2553'])} คน",'ปี 2553 และ 2562; ทุกประเทศ/ทวีป','คอลัมน์เปรียบเทียบยอดรวมสองปี'),('H2','จำนวนนักท่องเที่ยวเพิ่มขึ้นทุกปี 2553-2562','ไม่ยอมรับ',f"2556 = {num(y['2556'])} คน -> 2557 = {num(y['2557'])} คน ลดลง {num(y['2556']-y['2557'])} คน ({(y['2557']/y['2556']-1)*100:.2f}%)",'ปี 2553-2562; ทุกประเทศ/ทวีป','กราฟเส้นเรียงปีและตรวจทุกคู่ปีต่อเนื่อง'),('H3','East Asia มียอดรวมสูงที่สุดในปี 2562','ยอมรับ',f"East Asia = {num(co['East Asia'])} คน; Europe = {num(co['Europe'])} คน",'Year = 2562; ทุกประเทศ/ทวีป','แท่งแนวนอนเรียงทวีปตามจำนวนคน'),('H4','East Asia มีสัดส่วนเกิน 50% ในปี 2562','ยอมรับ',f"{num(co['East Asia'])} / {num(y['2562'])} = {num(share,True)} > 50%",'Year = 2562; ทุกประเทศ/ทวีป','แท่งร้อยละแต่ละทวีปเพื่ออ่านเกณฑ์ 50%'),('H5','China เป็นประเทศต้นทางอันดับหนึ่งในปี 2562','ยอมรับ',f"China = {num(ct['China'])} คน; Malaysia = {num(ct['Malaysia'])} คน",'Year = 2562; ทุกประเทศ/ทวีป','แท่งเรียงประเทศตามจำนวนคนและแสดงประเทศทั้งหมด')]
    story=[para('Workshop 9 - Foreign Tourist Dashboard',H),para('ใช้ข้อมูลต้นฉบับ Foreign_tourists_En.xlsx ทั้ง 3 ชีต โดยคงหัวคอลัมน์ภาษาไทยและใช้ชื่อประเทศ/ทวีปภาษาอังกฤษ. แปลงปี ค.ศ. ที่ปนอยู่ในแถว Africa 2017-2019 เป็น พ.ศ. 2560-2562 ก่อนวิเคราะห์. จำนวนแถว fact = 540; ช่วงปี2553-2562ตรงกับ2010-2019.'),para('ทำความสะอาดตามLab: ลบEuropeที่ซ้ำ เหลือทวีป7แถว และกรองชื่อประเทศnull เหลือประเทศ54แถว. Fact grainคือทวีป-รหัสประเทศ-ปี. รหัสประเทศ15(Other Countries)ปรากฏหลายทวีปแต่ไม่ใช่ข้อมูลซ้ำ. รหัสประเทศที่มีข้อมูลจริง48ค่า; Other Countriesรวมหลายทวีปในการแสดงชื่อประเทศและยังอยู่ในยอดรวม.'),table([['Hypothesis','ผล','หลักฐาน'],*[[h,d,e] for h,t,d,e,c,r in cases]],[55,70,385]),Spacer(1,12),para('ตรวจ Desktop จริงแล้ว: เปิดและRefreshสำเร็จ; DAXรวม285,016,377คนและTotal Countries48. ตรวจภาพ6หน้า, ตารางlocalรวมถูกต้อง, Navigator6ปุ่ม และแกนH1แสดง2553/2562. ตัวเลขละเอียดในผลวิเคราะห์เป็นการคำนวณต้นทาง; ภาพจริงอยู่ภาคผนวก.'),para(pbix_status(W9,'Workshop9_Foreign_Tourists.pbix')),para('การPublish to webและลิงก์สาธารณะยังไม่ทำ; การเปิดPBIXใหม่และDAXbaselineผ่านแล้ว.'),PageBreak()]
    for h,title,decision,evidence,context,reason in cases:
        story.extend([para(h+' - '+title,H),para('ผล: '+decision+'สมมติฐาน'),para(evidence),para('Filter Context: '+context),para('เหตุผลเลือก Visual: '+reason)])
        if h in ['H1','H2']:
            labs=['2553','2562'] if h=='H1' else list(y);vals=[y[k] for k in labs]
            story.extend([chart(labs,vals,h+' Tourists by year (people)',line=h=='H2'),table([['ปี (พ.ศ.)','จำนวนคน','เปลี่ยนจากปีก่อน'],*[[k,num(y[k]),'-' if int(k)==2553 else num(y[k]-y[str(int(k)-1)])] for k in labs]],[125,190,195])])
        else:
            g=ct if h=='H5' else co;labs=sorted(g,key=g.get,reverse=True);vals=[g[k]/y['2562'] if h=='H4' else g[k] for k in labs]
            # All countries appear in the full source result table; chart shows top 12 for legible independent validation only.
            story.append(chart(labs[:12],vals[:12],h+' '+('Country ranking: first 12 of all countries' if h=='H5' else 'Continent ranking'),pct=h=='H4'))
            shown=labs[:12] if h=='H5' else labs
            story.append(table([['Country' if h=='H5' else 'Continent','จำนวนคน','สัดส่วน'],*[[k,num(g[k]),num(g[k]/y['2562'],True)] for k in shown]],[220,145,145]))
            if h=='H5':
                story.extend([PageBreak(),para('H5 - อันดับประเทศทั้งหมดในปี 2562',H),para('เรียงจากจำนวนคนมากไปน้อย: อ่านคอลัมน์ซ้ายก่อน แล้วต่อที่คอลัมน์ขวา. รวม Other Countries ตามต้นทาง; ไม่ตัดกลุ่มทิ้ง.')])
                half=(len(labs)+1)//2;full=[['Country','คน','Country','คน']]
                for i in range(half):
                    right=labs[i+half] if i+half<len(labs) else None
                    full.append([f'{i+1}. {labs[i]}',num(g[labs[i]]),f'{i+half+1}. {right}' if right else '',num(g[right]) if right else ''])
                story.append(table(full,[175,80,175,80]))
        story.append(PageBreak())
    story.extend([para('Lab ที่คงไว้และผลตรวจ Desktop',H),para('Overview คง KPI การเทียบประเทศและ Slicer. Azure Maps ถูก tenant ปิดการใช้งานจริงด้วยข้อจำกัดการส่งข้อมูลแผนที่ไปประมวลผลนอกภูมิภาค จึงเปลี่ยน Continent Analysis เป็น built-in Table แสดง Country, Continent และ Total Tourists เรียงยอดมากไปน้อย. ตาราง local รักษาการวิเคราะห์แหล่งประเทศ/ทวีป แต่ไม่ได้อ้างว่ามีแผนที่แสดงผล. ไม่เปลี่ยนการตั้งค่าความเป็นส่วนตัวหรือความปลอดภัย.'),para('Country Analysis ใช้ built-in Bar Chart แทน Animated Bar Chart Race และ built-in Pie แทน Drill Down Pie. สร้าง Lab ใหม่เพราะไม่พบ pbix เดิม; แบบฝึกหัดอนุญาต built-in ทั้งหมด. ทุกหน้าใหม่มี Slicer; ปีเป็น categorical axis และไม่ถูก SUM. H3-H5 ใช้ page filter2562.'),table([['เงื่อนไข','Expected Tourists (people)'],*[[k,num(v)] for k,v in s9['slicer_checks'].items()]],[320,190]),Spacer(1,12),para('ทดสอบ Country=Australia จริงแล้วใน Country Analysis: Barประมาณ8M และPie100%; คืนAllสำเร็จ. ภาพnative_filter_Australia.pngเป็นหลักฐาน. Australiaรวมจากต้นทาง/ตารางlocal=8,179,988คน. เงื่อนไขอื่นในตารางเป็นเกณฑ์จากต้นทาง; ไม่เหมารวมว่าทุกเงื่อนไขSlicerผ่านในGUI.'),para(pbix_status(W9,'Workshop9_Foreign_Tourists.pbix')),para('หลังเปิดไฟล์PBIXใหม่ DAXยืนยันTotal Tourists285,016,377และTotal Countries48. ส่วนการPublish to webยังไม่ทำ และไม่มีpublic URLที่เปิดทดสอบแบบไม่ลงชื่อเข้าใช้. ต้องได้รับคำยืนยันเผยแพร่ก่อนดำเนินการ; ถ้าองค์กรไม่อนุญาตให้บันทึกข้อจำกัดและขอวิธีส่งทดแทน. ไม่สร้างURLปลอม.'),para('PBIR/TMDLผ่านstructural validation; Desktopเปิด/Refresh/DAXbaseline/SaveAs/เปิดใหม่ผ่านแล้ว. ภาพ6หน้า, AustraliaSlicerและภาพเปิดPBIXใหม่อยู่ภาคผนวก. ไม่เพิ่มข้ออ้างว่าทดสอบSlicerทุกเงื่อนไขหรือเผยแพร่สำเร็จ.')])
    appendshots(story,W9)
    SimpleDocTemplate(str(W9/'Workshop9_Report.pdf'),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=40,bottomMargin=42,title='Workshop 9 Foreign Tourist Hypothesis Results',author='BI 2026').build(story,onFirstPage=footer,onLaterPages=footer)
    if '--export-csv' in sys.argv:csvout(W9/'analysis/Hypothesis_Results.csv',[['Hypothesis','Statement','Decision','Evidence','Filter Context','Visual Reason'],*cases])
if '--workshop9' not in sys.argv:build8()
if '--workshop8' not in sys.argv:build9()
print('Updated requested Power BI PDF reports with native Desktop evidence')
