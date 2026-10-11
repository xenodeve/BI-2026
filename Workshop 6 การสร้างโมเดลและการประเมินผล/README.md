# Workshop6 - เกณฑ์ประเมินโมเดล

ไฟล์หลัก: [Workshop6_Evaluation_Criteria_Report.pdf](<D:/Github/BI 2026/Workshop 6 การสร้างโมเดลและการประเมินผล/Workshop6_Evaluation_Criteria_Report.pdf>) จำนวน8หน้า อธิบาย Precision, Recall, Accuracy, F1 และ AUC พร้อมสูตรและตัวอย่าง Naive Bayes จริงจาก Mini Project2.

Positive=Hospitalized; Negative=Outpatient. Native robust means: Precision71.109069%, Recall62.068102%, Accuracy87.950319%, F1 66.280408%, AUC0.881848251. Confusion counts: TN228013, FP14416, FN21684, TP35480, N299593. รายงานแยกค่าเฉลี่ย5batches, pooled positive-class metric และ class macro อย่างชัดเจน; ไม่เรียก5batchesนี้ว่าfive-fold cross-validation.

- `evidence/native_NB_performance.png` เป็นสำเนา byte-identical ของภาพจริงเดิมจากMini2.
- `support/metrics_verification.json` เก็บค่าเฉลี่ย/SD/counts/class-macro และAUCที่คำนวณซ้ำจากจุดROCจริงทั้ง5ชุด.
- `support/build_workshop6_report.py` สร้างPDFซ้ำด้วย bundled Python; ไม่ฝึกโมเดลหรือทำnativeRun.
- `qa/` เป็นภาพ render ทุกหน้าและ contact sheet สำหรับตรวจรูปแบบ.

อ่านโจทย์จาก `1.txt`. BI06 PDFเป็นพื้นฐานTurboPrep; แนวคิดเกณฑ์/ConfusionMatrix/F1อ้าง BI08 PDFหน้า19-21. ค่าจริงมาจาก `D:/Github/BI 2026/Native_AI_Repository/MiniProject2_AutoModel_9Models/Naive Bayes/Performance.rmperf` และตรวจเทียบnative auditของMini2.

ตรวจคำนวณและrender/reviewครบทุกหน้าแล้ว. งานนี้ไม่ได้Runใหม่ ไม่เปลี่ยนMini2หรือnative repository และไม่อ้างว่าการเปรียบเทียบ9โมเดลบนTestingSetร่วมกันเสร็จแล้ว. ไม่มีการเผยแพร่หรือส่งข้อมูล.
