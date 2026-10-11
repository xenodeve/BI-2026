from pathlib import Path
import json,hashlib,zipfile,shutil,datetime,xml.etree.ElementTree as E,zlib
import pandas as pd
from pypdf import PdfReader
W=Path(__file__).resolve().parents[1];ROOT=W.parent;S=W/'support'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1048576),b''):h.update(c)
 return h.hexdigest()
raw_path=W/'heart_2020_cleaned.csv';prepared_path=W/'heart_2020_prepared_native.csv';rmp=W/'Workshop4_Data_Preparation.rmp';pdf=W/'Workshop4_Data_Preparation_Report.pdf'
before={p.name:sha(p) for p in [raw_path,prepared_path,rmp,pdf]}
raw=pd.read_csv(raw_path);native=pd.read_csv(prepared_path)
assert raw.shape==(319795,18) and native.shape==(319795,19)
assert list(native.columns)==list(raw.columns)+['AnyUnhealthyDays']
pd.testing.assert_frame_equal(raw,native[raw.columns],check_dtype=False,check_exact=True)
derived=((raw.PhysicalHealth>0)|(raw.MentalHealth>0)).map({True:'Yes',False:'No'})
assert native.AnyUnhealthyDays.equals(derived.rename('AnyUnhealthyDays'))
assert native.HeartDisease.value_counts().to_dict()=={'No':292422,'Yes':27373}
assert int(raw.isna().sum().sum())==int(native.isna().sum().sum())==0
assert int(raw.duplicated().sum())==int(native.duplicated().sum())==18078
q=json.loads((W/'data_quality.json').read_text())
for col in ['BMI','PhysicalHealth','MentalHealth','SleepTime']:
 v=raw[col];q1,q3=v.quantile([.25,.75]);iqr=q3-q1
 assert int(((v<q1-1.5*iqr)|(v>q3+1.5*iqr)).sum())==q['numeric'][col]['iqr_flag_count']
 assert native[col].min()==v.min() and native[col].max()==v.max()
assert before[raw_path.name]=='90a1e2e8bdcb4aba54314a41d35d2ac3be4763e459df33951e08e415f527f5a8'
proof=json.loads((W/'native_batch_verification.json').read_text());assert proof['verified'] and proof['process_finished_successfully'] and not proof['gui_TurboPrep_claim']
assert proof['raw_sha256']==before[raw_path.name] and proof['native_prepared_sha256']==before[prepared_path.name] and proof['process_sha256']==before[rmp.name]
port=json.loads((ROOT/'docs/execution/native-portability-verification.json').read_text());p4=next(x for x in port['tasks'] if x['task']=='WS4')
assert p4['actual_official_native_batch_relocated_run_successful'] and p4['native_prepared_byte_identical_to_primary']
assert p4['native_prepared_sha256']==before[prepared_path.name] and p4['process_sha256']==before[rmp.name]
tree=E.parse(rmp);operators=tree.findall('.//operator');names={o.get('name') for o in operators}
assert not any(o.get('class') in ['filter_examples','remove_duplicates','replace_missing_values','normalize','sample_stratified','sample'] for o in operators)
macro=next(o for o in operators if o.get('class')=='generate_macro')
functions={p.get('key'):p.get('value') for p in macro.findall('list/parameter')}
assert functions['dataset_path']=='replace(%{process_path}, %{process_file}, "heart_2020_cleaned.csv")'
assert functions['prepared_path']=='replace(%{process_path}, %{process_file}, "heart_2020_prepared_native.csv")'
for c in tree.findall('.//connect'):
 for key in ['from_op','to_op']:assert key not in c.attrib or c.get(key) in names
reader=PdfReader(pdf);assert len(reader.pages)==3
text='\n'.join(p.extract_text() for p in reader.pages)
assert 'official batch' in text and 'native batch' in text and '319,795' in text and '18,078' in text
assert 'Turbo Prep GUI' in text and 'ยังรอหลักฐานจริง' in text
review={'file_deliverable_scope_pass':True,'teacher_acceptance_or_Classroom_submission_claim':False,'source_requirement_basis':'BI06 PDF3/slide10 describes saved Process reuse; PDF1/slide4 and PDF2/slides5-6 cover Data Quality; no screenshot delivery instruction in all11 slides/title-only WS4Classroom. User approved available-slides scope and source dataset.','raw_rows':319795,'raw_columns':18,'native_prepared_columns':19,'all_original_values_exactly_preserved':True,'derived_rule_exact_all_rows':True,'no_row_deletion_or_fabrication':True,'missing_cells':0,'duplicate_rows_retained_and_disclosed':18078,'no_clipping_imputation_or_deduplication':True,'native_engine_execution_proved':True,'actual_relocation_proved':True,'interactive_TurboPrep_creation_not_claimed':True,'PDF3pages_visually_reviewed_and_truthful':True,'canonical_sha256':before}
(S/'submission_final_review.json').write_text(json.dumps(review,indent=2),encoding='utf-8')
readme='''# Workshop 4 — submission files

การจัดเตรียมข้อมูลตามขอบเขตสไลด์ BI06 และข้อมูลที่อนุมัติ: ตรวจคุณภาพและเก็บผู้ตอบ 319,795 แถวครบเดิม เพิ่ม AnyUnhealthyDays โดยไม่ใช้ HeartDisease เป็นเงื่อนไข ผล native มี 19 คอลัมน์ ค่าเดิมทุกช่องและต้นฉบับทุก bytes ไม่เปลี่ยน ไม่ลบคำตอบที่เหมือนกัน ไม่ตัดค่าปลายและไม่สร้างแถวเทียม เหตุผลและจำนวน duplicates/outlier flags อยู่ในรายงาน

AI Studio 2026.1.1 native engine รัน RMP สำเร็จผ่าน official batch และรันจากโฟลเดอร์ที่ย้ายแล้วสำเร็จ ผล CSV ตรงกันทุก bytes ไม่อ้างว่าได้สร้างขั้นตอนผ่าน Turbo Prep GUI หรือมีภาพ GUI

BI06 หน้า PDF3/สไลด์10 ระบุ “สามารถบันทึกกระบวนการ (Process) เก็บไว้ใช้ได้” และอธิบายการนำ process ไปใช้ซ้ำ; หน้า PDF1/สไลด์4 และ PDF2/สไลด์5–6 ครอบคลุม Data Quality ไม่มีรายการให้ส่งภาพหน้าจอเฉพาะ WS4 ในสไลด์11หน้าที่ตรวจหรือ Classroom ที่มีเพียงชื่อ จึงไม่เพิ่มภาพสมมติหรืออ้างว่าประวัติ GUI ผ่านแล้ว

แตก ZIP ทั้งโฟลเดอร์ก่อนเปิด Workshop4_Data_Preparation.rmp เป็น local process ให้ heart_2020_cleaned.csv อยู่ข้าง RMP ชื่อเดิม พาธ input/output คำนวณจากตำแหน่งไฟล์ RMP โปรแกรมส่งออก heart_2020_prepared_native.csv ข้อมูล Target คือ HeartDisease (Yes/No)

ไฟล์หลัก: รายงาน PDF 3 หน้า, RMP, raw original CSV และ native prepared CSV. heart_2020_prepared.csv เป็นไฟล์ตรวจเตรียมประกอบที่รายงานอ้างถึง; data/heart_2020_cleaned.csv เป็นสำเนาต้นฉบับที่รายงานอ้างถึงและ bytes ตรงกัน ไม่ใช่คนละ Dataset. ไฟล์ notes/ ให้ source, dictionary, quality, native-run/relocation proof และ checksums. ไม่ได้รวมภาพ source/render ให้ดูเหมือนผล GUI ของผู้เรียน
'''
(S/'SUBMISSION_README.md').write_text(readme,encoding='utf-8')
files={
 'Workshop4_Data_Preparation_Report.pdf':pdf,
 'Workshop4_Data_Preparation.rmp':rmp,
 'heart_2020_cleaned.csv':raw_path,
 'heart_2020_prepared_native.csv':prepared_path,
 'heart_2020_prepared.csv':W/'heart_2020_prepared.csv',
 'data/heart_2020_cleaned.csv':raw_path,
 'README.md':S/'SUBMISSION_README.md',
 'notes/source.txt':W/'source.txt',
 'notes/data_dictionary.csv':W/'data_dictionary.csv',
 'notes/data_quality.json':W/'data_quality.json',
 'notes/numeric_quality.csv':W/'numeric_quality.csv',
 'notes/preparation_log.csv':W/'preparation_log.csv',
 'notes/native_batch_verification.json':W/'native_batch_verification.json',
 'notes/submission_final_review.json':S/'submission_final_review.json'}
relative_port={'task':'WS4','execution_mode':'official installed native AI Studio batch','actual_relocated_execution':True,'prepared_byte_identical':True,'process_sha256':p4['process_sha256'],'raw_sha256':before[raw_path.name],'prepared_sha256':p4['native_prepared_sha256'],'rows':319795,'columns':19,'GUI_creation_claim':False}
manifest={n:{'bytes':p.stat().st_size,'sha256':sha(p)} for n,p in files.items()}
target=W/'Workshop4_Submission_Ready.zip'
if target.exists():
 backup=W/'backups';backup.mkdir(exist_ok=True);stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');shutil.copy2(target,backup/f'Workshop4_Submission_Ready_before_{stamp}.zip')
with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for n,p in files.items():z.write(p,n)
 z.writestr('notes/native_relocation_verification.json',json.dumps(relative_port,indent=2))
 z.writestr('notes/checksums.json',json.dumps(manifest,indent=2))
with zipfile.ZipFile(target) as z:
 assert z.testzip() is None
 for n,p in files.items():assert hashlib.sha256(z.read(n)).hexdigest()==manifest[n]['sha256'],n
 assert not any('..' in Path(i.filename).parts or i.filename.startswith('/') for i in z.infolist())
 archive_files=[{'name':i.filename,'bytes':i.file_size,'crc32':f'{i.CRC:08x}'} for i in z.infolist()]
assert before=={p.name:sha(p) for p in [raw_path,prepared_path,rmp,pdf]}
verification={'verified':True,'file_deliverable_scope_pass':True,'zip':str(target),'zip_bytes':target.stat().st_size,'zip_sha256':sha(target),'crc_test_all_members_pass':True,'every_source_member_sha256_matches':True,'canonical_artifacts_unchanged':True,'files':archive_files,'readiness_review':review}
(S/'submission_zip_verification.json').write_text(json.dumps(verification,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in verification.items() if k not in ['files','readiness_review']},indent=2))
