# ผลเปรียบเทียบ 9 โมเดลด้วยชุดทดสอบเดียวกัน

ตัวเลขชุดนี้มาจาก **AI Studio 2026.1.1 native engine ผ่าน batch runner ที่ติดตั้งมากับโปรแกรม** (`ai-studio-batch.bat` → `CommandLineLauncher`) เริ่มรันวันที่ 11 ตุลาคม 2026 เวลา 03:54:45 Asia/Bangkok ใช้ RMP ที่ต่อยอดจากกระบวนการ AutoModel จริงทั้ง 9 โมเดล ไม่ใช่ผลอ้างอิงจาก Python และไม่อ้างว่าเป็นการรันหรือภาพหน้าจอของ GUI การรัน AutoModel เดิมใน GUI และผล Default เดิมเก็บแยกไว้โดยไม่แก้ไข

ข้อมูลหลัง Native TurboPrep ยังคงมี **1,048,575 แถว** (Outpatient 848,544 / Hospitalized 200,031) กระบวนการนี้อ่านข้อมูลเต็มก่อนสุ่มข้อมูลสำหรับสร้างโมเดล 30,000 แถว เพื่อให้ SVM ใช้เวลาที่เหมาะสม จึงต้องแยกจำนวนข้อมูลหลังเตรียมออกจากจำนวนข้อมูลที่นำมาสร้างโมเดลอย่างชัดเจน

ทั้ง 9 โมเดลใช้ initial stratified sample 30,000 แถว seed 2001 และแบ่ง training/test 60/40 seed 1992 ตามการแบ่งหลักของ native AutoModel: training 18,000 แถว และ test 12,000 แถว กำหนด Hospitalized เป็น positive class ส่วน samplers สำหรับ feature engineering และ calibration ทำงานภายใน training ตามโครงสร้างเดิม ไม่เปลี่ยน learner, normalization หรือพารามิเตอร์การฝึกเดิม

| โมเดล | Accuracy | Precision | Recall | F1 | AUC |
|---|---:|---:|---:|---:|---:|
| Naive Bayes | 87.5083% | 0.691006 | 0.624290 | 0.655956 | 0.880906 |
| Generalized Linear Model | 90.3250% | 0.827526 | 0.622543 | 0.710546 | 0.901519 |
| Logistic Regression | 87.9833% | 0.873128 | 0.432940 | 0.578855 | 0.905527 |
| Fast Large Margin | 85.4917% | 0.743339 | 0.365662 | 0.490190 | 0.721479 |
| Deep Learning | 90.4500% | 0.774628 | 0.704238 | 0.737757 | 0.911174 |
| Decision Tree | 90.2750% | 0.829225 | 0.617300 | 0.707739 | 0.799719 |
| Random Forest | 89.0917% | 0.824934 | 0.543469 | 0.655254 | 0.905060 |
| Gradient Boosted Trees | 89.8167% | 0.774293 | 0.657929 | 0.711384 | 0.904637 |
| Support Vector Machine | 90.1500% | 0.844860 | 0.592398 | 0.696456 | 0.871270 |

Deep Learning ได้ F1, Recall, Accuracy และ AUC สูงสุดบนชุดทดสอบนี้: TP 1,612, FN 677, FP 469, TN 9,242 ส่วน Logistic Regression ได้ Precision สูงสุด แต่ Recall ต่ำกว่า จึงพลาด Hospitalized มากกว่า การเลือกโมเดลในรายงานควรอ้าง F1/Recall ประกอบ Accuracy เพราะ positive class มีเพียง 2,289 จาก 12,000 แถว

ตัวเลขหลักเป็นผลจาก Performance (Binominal Classification) บน **test ทั้ง 12,000 แถว** และส่งออกด้วย Performance to Data → Write CSV ไม่ใช้ค่าเฉลี่ยจาก robust 7-batch เดิมที่ตัดชุดดีที่สุด/แย่ที่สุดออก ซึ่งอาจทำให้แต่ละโมเดลถูกประเมินบนแถวที่ต่างกัน ส่วน robust evaluation เดิมคงไว้เป็นผลประกอบ

หลักฐานที่ตรวจจากไฟล์จริง:

- CSV 36 ไฟล์สร้างหลังเวลาเริ่มรันที่กำหนด และค่า hash ไม่เปลี่ยนระหว่างตรวจ
- ทั้ง 9 โมเดลมี train/test ID ไม่ซ้ำและไม่ทับกัน และใช้คู่ ID + actual label ตรงกันทุกแถว
- predictions ของทุกโมเดลครอบคลุม test ทั้ง 12,000 แถวตรงกัน มี Hospitalized 2,289 และ Outpatient 9,711
- ID ทั้ง 30,000 และ actual label ตรงกับตำแหน่งแถวจริงใน `COVID_Prepared_Native.csv` ข้อมูลเต็มและ RMP ใน Native repository เดิมมี hash ตรงกับก่อนเริ่ม
- Accuracy, Precision, Recall, F1 และ TP/TN/FP/FN ของ native Performance ตรงกับค่าที่คำนวณตรวจจาก predictions; native AUC ตรงกับ AUC ที่ตรวจจาก confidence(Hospitalized) โดยต่างไม่เกิน 3.2×10⁻¹⁵
- `COMMON_ROW_ID` สร้างหลัง preprocessing ทั่วไป และกำหนด role `id` ก่อนสุ่ม/แบ่งข้อมูล ไม่มีพารามิเตอร์ learner หรือการตั้ง role regular ที่นำ ID ไปเป็น predictor

ไฟล์ตัวเลขหลัก: `Native_Common_Test_Model_Comparison.csv` (เก็บค่าความละเอียดเต็ม) และ `metrics_<CODE>.csv` จาก native engine โดยตรง ไฟล์พิสูจน์: `common_exports_validation.json` รวม hash ของ exports, RMP driver, collector และข้อมูลเต็ม วิธีตรวจซ้ำ:

```powershell
& 'D:\Github\BI 2026\.bi-runtime\Scripts\python.exe' 'D:\Github\BI 2026\BI Mini Project 2\common_test\collect_common_exports.py' --run-start '2026-10-11T03:54:45'
```

Python ในขั้นตอนนี้ใช้ตรวจไฟล์ผลลัพธ์และความสอดคล้องเท่านั้น ไม่ได้ฝึกโมเดลแทน AI Studio บันทึกการทำงานของ native runner อยู่ที่ `docs/execution/native-common-batch.log` ส่วนภาพ GUI ในรายงานต้องอ้างภาพจริงของงาน GUI ที่ถ่ายไว้เท่านั้น
