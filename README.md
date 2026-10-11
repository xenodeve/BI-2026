# BI 2026 — 040223406 Business Intelligence

งานของวิชา **040223406 Business Intelligence** (ภาคเรียน 1/2569) คณะ/มหาวิทยาลัย KMUTNB
เป็นงานรายบุคคลทั้งหมด ยกเว้น Term Project ที่ยังอยู่ระหว่างดำเนินการ

> เก็บเป็นพอร์ตโฟลิโอแสดงความสามารถด้าน Business Intelligence / Data Analytics (Power BI, DAX, Python ML, Altair AI Studio)
> รวมสไลด์และโจทย์ของอาจารย์ผู้สอนไว้ด้วย ซึ่งผู้สอนอนุญาตให้นำไปใช้ได้

## สถานะงาน

| งาน | หัวข้อ | โฟลเดอร์ | สถานะ |
|---|---|---|---|
| Workshop 1 | สถิติประชากรประเทศไทย | `Workshop 1 สถิติประชากรประเทศไทย/` | เสร็จสิ้น |
| Workshop 2 | Data Presentation | `Workshop 2 Data Presentation/` | เสร็จสิ้น |
| Workshop 3 | What-if Analysis in Excel | `Workshop 3 What if Analysis in Excel/` | เสร็จสิ้น |
| Workshop 4 | Data Preparation | `Workshop 4 …(Data Preparation)/` | เสร็จสิ้น |
| Workshop 5 | Modeling and Evaluation | `Workshop 5 Modeling and Evaluation/` | เสร็จสิ้น |
| Workshop 6 | การสร้างโมเดลและการประเมินผล | `Workshop 6 …/` | เสร็จสิ้น |
| Workshop 7 | Data Visualization (Power BI) | `Workshop 7 Data Visualization/` | เสร็จสิ้น |
| Workshop 8 | Data Analysis Expressions (DAX) | `Workshop 8 Data Analysis Expressions (DAX)/` | เสร็จสิ้น |
| Workshop 9 | Dashboard นักท่องเที่ยวต่างชาติ | `Workshop 9 Dashboard/` | เสร็จสิ้น |
| Workshop 10 | Deployment — พยากรณ์ทะเบียนรถ (กรมการขนส่งทางบก) | `Workshop 10 Deployment/` | เสร็จสิ้น |
| Mini Project 1 | CRISP-DM, ≥5 โมเดล (Altair AI Studio) | `BI Mini Project 1/` | เสร็จสิ้น |
| Mini Project 2 | Binary classification, Auto Model 9 โมเดล | `BI Mini Project 2/` | เสร็จสิ้น |
| Term Project | DLT Brand/Type (Power BI + Python) | `BI Term Project/` | ฉบับร่าง |

## โครงสร้าง repository

```
Workshop 1–10 …/            ไฟล์งาน (xlsx, pbix, ipynb, csv, pdf รายงาน) และโจทย์
BI Mini Project 1/          .rmp, รายงาน, ZIP พร้อมส่ง
BI Mini Project 2/          .rmp, ชุดข้อมูล COVID, รายงาน, ZIP พร้อมส่ง
BI Term Project/            notebook, .pbix, ตารางข้อมูล, DAX measures, ร่างรายงาน
Native_AI_Repository/       Repository ของ Altair AI Studio (เฉพาะไฟล์ process/ข้อมูลขนาดเล็ก)
Presentation/               สไลด์ประกอบวิชา (BI00–BI11)
.mcp.json                   ตั้งค่า MCP ของ Power BI Modeling สำหรับ Claude Code
```

## เครื่องมือที่ใช้

- **Power BI Desktop** (Workshop 7–10, Term) — โมเดลสร้างด้วย DAX และตรวจผ่าน Power BI Modeling MCP
- **Python 3.11** — pandas / scikit-learn สำหรับพยากรณ์ใน Workshop 10 และ Term (notebook `.ipynb`)
- **Altair AI Studio 2026.1.1** — Turbo Prep, Auto Model และ process `.rmp` ของ Workshop 4–6 และ Mini Project 1–2
- **Excel** — Workshop 1–3

## สิ่งที่ไม่ได้อยู่ใน repository

เพื่อให้ขนาดพอเหมาะ (ไม่เกินข้อจำกัด 100 MB ต่อไฟล์ของ GitHub) `.gitignore` ตัดไฟล์ต่อไปนี้ออก ซึ่งสร้างใหม่ได้โดยรัน process:

- Python virtual environment (`.bi-runtime/`) และ cache ต่าง ๆ
- ไฟล์ผลลัพธ์ขนาดใหญ่ที่ AI Studio สร้างเอง: `*.rmhdf5table`, `*.rmmodel`, `*.rmexpred`, `*.rmliftchart`, `*.rmmodelsim`, `*.rmstats`, `*.rmperf`, `*.ioo`
- ไฟล์ log, สำเนา backup ก่อนแก้, ผลตรวจ QA อัตโนมัติ และไฟล์ทดสอบระหว่างพัฒนา (เก็บเฉพาะผลงานสุดท้าย)

ชุดข้อมูลดิบที่ดาวน์โหลดจากแหล่งสาธารณะเก็บไว้ในโฟลเดอร์งานของแต่ละชิ้นเท่าที่ไม่เกินขีดจำกัด

## การรันซ้ำ

- เปิด `.pbix` ด้วย Power BI Desktop (ข้อมูลฝังอยู่ในไฟล์; แหล่งต้นฉบับอยู่ข้าง ๆ เช่น `DAX_Lab.xlsx`)
- เปิด `.ipynb` ด้วย Jupyter หลังติดตั้ง `pandas scikit-learn matplotlib`
- เปิด `.rmp` ด้วย AI Studio โดยวางไฟล์ข้อมูลไว้โฟลเดอร์เดียวกัน (process ใช้ path สัมพัทธ์เพื่อย้ายโฟลเดอร์ได้)

## หมายเหตุ

งานนี้ทำโดยนักศึกษาเป็นผู้รับผิดชอบเนื้อหา โดยใช้ Claude Code / Codex ช่วยสร้างและตรวจไฟล์

## License

โค้ด รายงาน และไฟล์งานที่ผู้เขียนสร้างเองอยู่ภายใต้ [MIT License](LICENSE) สไลด์/โจทย์เป็นเอกสารของผู้สอน (ผู้สอนอนุญาตให้นำไปใช้ได้) และชุดข้อมูลต้นทางเป็นของเจ้าของข้อมูล (เช่น กรมการขนส่งทางบก, แหล่งข้อมูลสาธารณะที่ระบุในรายงาน) และไม่อยู่ภายใต้สัญญาอนุญาตนี้
