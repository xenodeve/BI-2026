# Workshop 4 — submission files

การจัดเตรียมข้อมูลตามขอบเขตสไลด์ BI06 และข้อมูลที่อนุมัติ: ตรวจคุณภาพและเก็บผู้ตอบ 319,795 แถวครบเดิม เพิ่ม AnyUnhealthyDays โดยไม่ใช้ HeartDisease เป็นเงื่อนไข ผล native มี 19 คอลัมน์ ค่าเดิมทุกช่องและต้นฉบับทุก bytes ไม่เปลี่ยน ไม่ลบคำตอบที่เหมือนกัน ไม่ตัดค่าปลายและไม่สร้างแถวเทียม เหตุผลและจำนวน duplicates/outlier flags อยู่ในรายงาน

AI Studio 2026.1.1 native engine รัน RMP สำเร็จผ่าน official batch และรันจากโฟลเดอร์ที่ย้ายแล้วสำเร็จ ผล CSV ตรงกันทุก bytes ไม่อ้างว่าได้สร้างขั้นตอนผ่าน Turbo Prep GUI หรือมีภาพ GUI

BI06 หน้า PDF3/สไลด์10 ระบุ “สามารถบันทึกกระบวนการ (Process) เก็บไว้ใช้ได้” และอธิบายการนำ process ไปใช้ซ้ำ; หน้า PDF1/สไลด์4 และ PDF2/สไลด์5–6 ครอบคลุม Data Quality ไม่มีรายการให้ส่งภาพหน้าจอเฉพาะ WS4 ในสไลด์11หน้าที่ตรวจหรือ Classroom ที่มีเพียงชื่อ จึงไม่เพิ่มภาพสมมติหรืออ้างว่าประวัติ GUI ผ่านแล้ว

แตก ZIP ทั้งโฟลเดอร์ก่อนเปิด Workshop4_Data_Preparation.rmp เป็น local process ให้ heart_2020_cleaned.csv อยู่ข้าง RMP ชื่อเดิม พาธ input/output คำนวณจากตำแหน่งไฟล์ RMP โปรแกรมส่งออก heart_2020_prepared_native.csv ข้อมูล Target คือ HeartDisease (Yes/No)

ไฟล์หลัก: รายงาน PDF 3 หน้า, RMP, raw original CSV และ native prepared CSV. heart_2020_prepared.csv เป็นไฟล์ตรวจเตรียมประกอบที่รายงานอ้างถึง; data/heart_2020_cleaned.csv เป็นสำเนาต้นฉบับที่รายงานอ้างถึงและ bytes ตรงกัน ไม่ใช่คนละ Dataset. ไฟล์ notes/ ให้ source, dictionary, quality, native-run/relocation proof และ checksums. ไม่ได้รวมภาพ source/render ให้ดูเหมือนผล GUI ของผู้เรียน
