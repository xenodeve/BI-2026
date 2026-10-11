"""Execute the term project in a fresh local Python kernel with saved outputs."""
from pathlib import Path
import json,sys,ast
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager

folder=Path(__file__).resolve().parent
source=(folder/'term_project.py').read_text(encoding='utf-8')
definitions={node.name:ast.get_source_segment(source,node) for node in ast.parse(source).body if isinstance(node,ast.FunctionDef)}
md=nbformat.v4.new_markdown_cell;code=nbformat.v4.new_code_cell
cells=[
    md('# โครงงานเสนอ DLT Brand and Vehicle Type Demand Analysis\n\n'
       '**สถานะ:** ข้อเสนอพร้อมผลคำนวณจริง สมาชิกกลุ่ม 2–5 คน การตรวจหัวข้อ/ชุดข้อมูลไม่ซ้ำ และการอนุมัติหัวข้อยังรอดำเนินการ '
       'ไม่มีการสมมติชื่อสมาชิกหรืออ้างว่าได้รับอนุมัติแล้ว\n\n'
       'วัตถุประสงค์: สนับสนุนการวางแผนตามยี่ห้อและประเภทรถ ใช้ยอดจดทะเบียนเป็นตัวชี้วัดการจดทะเบียน '
       'ไม่เรียกว่ายอดขายหรืออุปสงค์ทั้งหมด และไม่สรุปเหตุและผลจากข้อมูลนี้\n\n'
       'รันซ้ำ: ติดตั้ง `requirements.txt` ใน Python 3.11 วาง notebook ร่วมกับ raw CSV และ `term_project.py` '
       'จากนั้น Restart Kernel / Run All หรือรัน `python build_notebook.py`'),
    md('## 1 โหลดและตรวจข้อมูลจริง\nแหล่งตรวจสอบกรมการขนส่งทางบก: '
       '[DLT Data Catalog](https://gdcatalog.dlt.go.th/en/dataset/stat_1_1_01_first_regis_vehicles_car). '
       'สำเนา CSV นี้มาจากไฟล์ที่ได้รับในวิชา เก็บ hash เพื่อยืนยันไฟล์ที่ใช้จริง ไม่ได้ดาวน์โหลดข้อมูลใหม่มาปะปน'),
    code("from pathlib import Path\nimport pandas as pd, numpy as np\nfrom IPython.display import display, Image, FileLink\nfrom term_project import *\nfolder=Path.cwd()\nif not (folder/RAW_NAME).exists(): folder=folder/'BI Term Project'\nraw=pd.read_csv(folder/RAW_NAME,encoding='utf-8-sig')\nassert raw.shape==(68398,9)\nprint('Raw shape',raw.shape)\nprint('Missing values',raw.isna().sum().to_dict())\nprint('Exact duplicates',raw.duplicated().sum())\ndisplay(raw.head())"),
    md('## 2 ETL และตรวจ 25 เดือนต่อเนื่อง\nข้อกำหนด 24 เดือนผ่านจาก Jan2024–Jan2026 จำนวน25เดือน '
       'February2026 มี6records18คันและยังไม่ครบ จึงตัดออกจากactual ห้ามเติมDecember2023โดยเดา '
       'รุ่นที่ขาด623recordsเก็บไว้เป็นUnknown model ไม่ตัดยอดตามยี่ห้อ/ประเภทรถ'),
    code("fact,quality,etl=prepare_fact(raw)\nprint('Fact rows',len(fact),'Complete months',fact.Date.nunique())\nprint('Complete-window source records',fact.SourceRecords.sum())\nprint('Registrations',fact.Registrations.sum())\nassert fact.Date.nunique()==25\nassert fact.SourceRecords.sum()==35805\nassert fact.Registrations.sum()==5007659\ndisplay(etl)\ndisplay(quality.tail())\ndisplay(fact.head())"),
    md('## 3 อนุกรมยอดรวม ยี่ห้อ และประเภทรถ\nเลือก top3brands และ top3types จาก Jan2024–Mar2025 เท่านั้น '
       'ไม่ใช้ช่วงvalidation/testเลือกsegment เดือนที่ไฟล์รวมครบแต่ไม่มียี่ห้อนั้นให้0เพื่อระบุว่าไม่มีrecordsของcategory '
       'ไม่ได้ใช้0แทนเดือนที่sourceหายหรือไม่ครบ'),
    code(definitions['segment_series']+'\n\n'+definitions['choose_series']+"\n\nseries_list=choose_series(fact)\ndisplay(pd.DataFrame(series_list,columns=['SegmentType','SegmentName']))\ndisplay(segment_series(fact,'Brand','HONDA').head())"),
    md('## 4 Lag และ Train Validation Test\n22observationsแบ่ง12/5/5: Train Apr2024–Mar2025; '
       'Validation Apr–Aug2025; Test Sep2025–Jan2026 ห้ามshuffle เลือกโมเดลจากvalidationMAEก่อนเปิดผลtest '
       'การทดสอบเป็นrollingone-month-aheadโดยใช้ยอดจริงเดือนก่อนที่ทราบแล้วเป็นLag '
       'เพิ่มMonthSin/MonthCosกับTimeIndexที่ทราบจากปฏิทิน'),
    code(definitions['prepare_modeling']+"\n\nmodel_data,train,validation,test=prepare_modeling(segment_series(fact,'Total','All'))\nassert [len(model_data),len(train),len(validation),len(test)]==[22,12,5,5]\nfor name,frame in [('Train',train),('Validation',validation),('Test',test)]: print(name,frame.Date.min(),frame.Date.max(),len(frame))\ndisplay(model_data.head())"),
    md('## 5 เปรียบเทียบ4อัลกอริทึมพร้อมNaivebaseline\nLinearRegression, Ridge, RandomForest, GradientBoosting '
       'พารามิเตอร์กำหนดไว้ล่วงหน้า ไม่ปรับจากtest ทำStandardScalerเฉพาะข้อมูลฝึกภายในpipeline '
       'ผลทำนายติดลบถูกclipเป็น0เหมือนกันทั้งvalidation/test/future '
       'หลังเลือกโมเดล refittrain+validation17แถวเพื่อประเมินtest แล้วrefit22แถวเพื่อforecastFeb2026'),
    code(definitions['make_models']+'\n\n'+definitions['select_model']+"\n\nrun=main()\ncomparison=pd.read_csv(folder/'ModelComparison.csv')\nforecast=pd.read_csv(folder/'FactForecast.csv',parse_dates=['Date'])\ndisplay(comparison[comparison.SelectedModel])\ndisplay(forecast[forecast.DatasetSegment=='Future'])"),
    md('## 6 สมมติฐานและหลักฐานจริง\n6คำถามมีเกณฑ์ชัดเจน เป็นการประเมินเชิงพรรณนาบนrecordsที่ได้รับ '
       'ไม่มีการอ้างp-valueหรือเหตุและผล H3เมื่อผลจริงเพิ่มขึ้นต้องปฏิเสธสมมติฐานลดลง'),
    code("hypotheses=pd.read_csv(folder/'HypothesisEvidence.csv')\ndisplay(hypotheses)\nerrors=pd.read_csv(folder/'TestErrors.csv',parse_dates=['Date'])\ndisplay(errors.sort_values('AbsoluteError',ascending=False).head(10))"),
    md('## 7 กราฟจริงและความแตกต่างระหว่างsegment\nยอดรวม/ยี่ห้อ/ประเภทรถเป็นมุมมองซ้อนกัน '
       'ห้ามบวกforecastทั้ง7seriesเป็นยอดรวมของประเทศ ภาพกราฟนี้ยังไม่ใช่ภาพPowerBI'),
    code("for name in ['brand_type_composition.png','validation_test_errors.png','segment_forecasts.png']:\n    display(Image(filename=str(folder/name)))"),
    md('## 8 ตรวจไฟล์ส่งและnullablefutureactual\nบันทึกFact/Dimension, ETLcounts, dictionary, '
       'modelcomparison, forecast และhypothesesจากผลคำนวณจริง หน้าPowerBI5หน้า/8measures/3เทคนิค '
       'ยังต้องสร้างและตรวจในไฟล์.pbix รวมทั้งสมาชิกกลุ่มและtopicapproval'),
    code("assert len(comparison)==35\nassert len(forecast)==182\nassert comparison.groupby('SeriesKey').SelectedModel.sum().eq(1).all()\nassert forecast[forecast.DatasetSegment=='Future'].ActualRegistrations.isna().all()\nassert forecast.groupby('SeriesKey').DatasetSegment.value_counts().unstack().eq(pd.Series({'History':15,'Validation':5,'Test':5,'Future':1})).all().all()\nfor name in ['FactRegistrations.csv','DimDate.csv','DimBrand.csv','DimVehicleType.csv','DimSeries.csv','FactForecast.csv','ModelComparison.csv','DataDictionary.csv','ETL_Counts.csv','HypothesisEvidence.csv']:\n    path=folder/name\n    assert path.exists()\n    print(name,pd.read_csv(path).shape)\n    display(FileLink(str(path)))"),
]
notebook=nbformat.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','name':'python3','language':'python'},'language_info':{'name':'python','version':'3.11.9'}})
kernel_root=folder/'.jupyter'/'kernels';kernel_folder=kernel_root/'termproject';kernel_folder.mkdir(parents=True,exist_ok=True)
(kernel_folder/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],'display_name':'BI term project Python','language':'python'}),encoding='utf-8')
manager=KernelManager(kernel_name='termproject',kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(kernel_root)]))
NotebookClient(notebook,timeout=180,kernel_name='termproject',km=manager,resources={'metadata':{'path':str(folder)}}).execute()
nbformat.validate(notebook)
assert all(cell.execution_count is not None for cell in notebook.cells if cell.cell_type=='code')
assert not any(output.output_type=='error' for cell in notebook.cells if cell.cell_type=='code' for output in cell.outputs)
nbformat.write(notebook,folder/'DLT_Brand_Type_Term_Project.ipynb')
print('Fresh-kernel execution passed with saved outputs')
