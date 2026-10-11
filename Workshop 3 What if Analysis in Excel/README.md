# Workshop 3 - What-if Analysis

ไฟล์ส่งงานหลัก: **Workshop3_WhatIf_Completed.xlsx** และ **Workshop3_WhatIf_Report.pdf** (ภาษาไทย 5 หน้า)

ไฟล์ `Workshop3_WhatIf.xlsx` เดิมถูกเปิดค้างและล็อกโดย Excel จึงไม่เขียนทับ. เก็บสำรองตรงกับไฟล์ปัจจุบันก่อนแก้ใน `backups/Workshop3_WhatIf_current_before_functional_20261011_041659.xlsx`. ไม่แก้หลักฐาน native-before ของผู้ตรวจหลัก. ให้เปิด **Completed** แบบ fresh หลังจัดการหน้าต่างที่ค้าง และอย่าบันทึกหน่วยความจำของไฟล์เดิมทับ Completed.

Goal Seek: ราคาเดิม 400,000 บาทและค่างวดประมาณ 9,400 บาทได้รับการตรวจ native โดยผู้ตรวจหลักแล้ว. ผล **mathematical solver/PV** คือราคา **425,531.92056985485 บาท** ให้ PMT **10,000 บาท** โดยดาวน์ 20%, ดอกเบี้ยรายปี 18%, 4 ปี, rate=annual/12, type=0, fv=0. **ยังไม่ได้ Run Goal Seek native**. B5 ใน Completed เป็นผลคณิตศาสตร์ที่บันทึกไว้; สูตร/guard เดิมคงอยู่. B23 เก็บทางเลือกดอกเบี้ยคงต้นแยกไว้เพราะสไลด์ไม่ได้ระบุชนิดดอกเบี้ยชัดเจน.

มี Scenario Manager definitions แบบ SpreadsheetML จริง 4 แบบในชีต Scenario, changing cells **B5/B8**. ดาวน์ 20% และดอกเบี้ยรายปี 7%:

| Scenario | ราคา (บาท) | ปี | PMT (บาท/เดือน) |
|---|---:|---:|---:|
| 200k_15y | 200,000 | 15 | 1,438.12523336 |
| 200k_30y | 200,000 | 30 | 1,064.48399229 |
| 300k_15y | 300,000 | 15 | 2,157.18785005 |
| 300k_30y | 300,000 | 30 | 1,596.72598843 |

ชีต **Scenario Summary (authored comparison)** เขียนเอง มีสูตรเงินกู้/PMT/ดอกเบี้ยรวมและค่าคำนวณจริง เชื่อมเงินดาวน์/อัตรากับ Scenario!B6/B7. **ไม่ได้สร้างด้วย native Summary dialog**. ตาราง snapshot เดิมใน Scenario คงอยู่; ใช้ชีต Summary ใหม่เมื่อต้องการเปลี่ยน assumptions.

ตรวจสูตรอิสระ, package XML, 4 scenario/input pairs, สูตรเดิมและ styles/theme/sharedStrings, การเปลี่ยนอัตรา 5%, อัตราศูนย์ และ guard เมื่อเว้นว่างแล้ว. การ import/recalculate/render ตรวจแบบอ่านอย่างเดียว ไม่ export เปลี่ยน XLSX. ภาพ PDF เป็น file render ไม่ใช่ screenshot native. การอ่าน XML/openpyxl ผ่านไม่ใช่การรับรอง Excel GUI หรือ full XSD validation.

**ขั้นตอน native ที่ยังรอ:**

1. เปิด Completed fresh ตรวจว่าไม่มี repair dialog และมี 3 ชีต.
2. ที่ Goal Seek เปลี่ยน B5 กลับ 400000 แล้วใช้ Data > What-If Analysis > Goal Seek: Set B16, To 10000, Change B5. เก็บภาพการตั้งค่าและผลจริง.
3. ที่ Scenario เปิด Scenario Manager ตรวจครบ 4 ชื่อ, กด Show ทีละแบบ ตรวจ B5/B8/B16 ให้ตรงตาราง. ใช้ Summary โดย result cell B16 เพื่อสร้างสรุป native เพิ่ม และแยกจาก authored comparison.
4. บันทึก Completed ปิดและเปิดซ้ำ ตรวจค่าคำตอบ สูตร และ scenarios. เก็บภาพจริงเมื่อได้เห็นผล.

แหล่งโจทย์: `Presentation/BI04 Models for DS and BI.pdf` หน้า PDF 4-5 / สไลด์ 16-17. [Microsoft PMT](https://support.microsoft.com/en-us/excel/functions/pmt-function), [SpreadsheetML Scenarios](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.spreadsheet.scenarios?view=openxml-3.0.1). ข้อมูลตรวจใน `support/functional_completion.json`, `support/sdk_verification.json`. ไม่มีการใช้ GUI/COM/VBA เพื่อสร้างผลหรือภาพ native ในขั้นตอนนี้.
