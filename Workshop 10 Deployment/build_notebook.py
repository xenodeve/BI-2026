"""Build and execute the submission notebook in a fresh dedicated kernel."""
from pathlib import Path
import ast
import json
import sys
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager

folder = Path(__file__).resolve().parent
source = (folder / "forecasting.py").read_text(encoding="utf-8")
parsed = ast.parse(source)
definitions = {node.name: ast.get_source_segment(source, node)
               for node in parsed.body if isinstance(node, ast.FunctionDef)}
md = nbformat.v4.new_markdown_cell
code = nbformat.v4.new_code_cell
cells = [
    md("# Workshop 10: DLT Vehicle Registration Forecasting\n\n"
       "ข้อมูลต้นฉบับ: `DLT_First_Registration_Monthly_Original_Combined.csv` จากกรมการขนส่งทางบก "
       "ทำตามสไลด์ `DLT_Vehicle_Forecasting.pptx` หน้า 67–74 และรายการส่งหน้า 50 "
       "เปรียบเทียบ 5 วิธีด้วยชุดทดสอบเดียวกัน เลือกจาก MAE จริง แล้วพยากรณ์ล่วงหน้า 1 เดือน\n\n"
       "**วิธีรันซ้ำ:** ติดตั้ง `requirements.txt` ใน Python 3.11 เปิด notebook ในโฟลเดอร์นี้ "
       "และเลือก Restart Kernel / Run All โดยมีไฟล์ต้นฉบับกับ `forecasting.py` อยู่ด้วย "
       "หรือรัน `python build_notebook.py` เพื่อสร้างและรัน notebook ใหม่ใน kernel ของ Python ที่ใช้รันคำสั่ง "
       "CSV `.xls` ของอาจารย์เก็บไว้เป็นตัวอย่างเท่านั้นและไม่ใช่ input ของการคำนวณ\n\n"
       "**การทดสอบ:** โมเดลเรียนรู้ครั้งเดียวจาก Apr 2024–Jun 2025 และทำนายทีละหนึ่งเดือน "
       "ใน Jul 2025–Jan 2026 โดยใช้ยอดจริงของเดือนก่อนที่ทราบแล้วเป็น Lag "
       "จึงไม่ใช่การพยากรณ์หลายเดือนพร้อมกันจากจุดเริ่มต้นเดียว"),
    md("## 1. Load and verify raw data\nตรวจขนาด คอลัมน์ ยอดรวม และบันทึกเวอร์ชันที่ใช้จริง"),
    code("from pathlib import Path\nimport hashlib, json, platform\nimport pandas as pd\nimport numpy as np\nimport sklearn\nfrom sklearn.base import clone\nfrom sklearn.linear_model import LinearRegression, Ridge\nfrom sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor\nfrom sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score\nfrom IPython.display import display, Image, FileLink\nfrom forecasting import create_charts, write_outputs\n\nFEATURES = ['Lag1', 'Lag2', 'Lag3']\nRAW_NAME = 'DLT_First_Registration_Monthly_Original_Combined.csv'\nfolder = Path.cwd()\nif not (folder / RAW_NAME).exists():\n    folder = folder / 'Workshop 10 Deployment'\nassert (folder / RAW_NAME).exists(), 'Place the notebook next to the source CSV'\nraw = pd.read_csv(folder / RAW_NAME, encoding='utf-8-sig')\nassert raw.shape == (68398, 9)\nprint('Raw shape:', raw.shape)\nprint('Columns:', raw.columns.tolist())\nprint('Versions:', platform.python_version(), pd.__version__, np.__version__, sklearn.__version__)\nprint('SHA256:', hashlib.sha256((folder / RAW_NAME).read_bytes()).hexdigest())\ndisplay(raw.head())"),
    md("## 2. Aggregate monthly and check gaps\nใช้ Source_Year_BE ลบ 543 เพื่อสร้างปี ค.ศ. และรวมจำนวนพร้อมนับ records "
       "ตรวจทุกเดือนระหว่างเดือนแรกกับเดือนสุดท้าย ห้ามเติมช่องว่างโดยเดา"),
    code(definitions["aggregate_monthly"] + "\n\n" + definitions["missing_months"] + "\n\nmonthly = aggregate_monthly(raw)\ngaps = missing_months(monthly)\nprint('Monthly rows:', len(monthly))\nprint('Missing months:', [date.strftime('%Y-%m-%d') for date in gaps])\nassert len(monthly) == 49\nassert gaps == [pd.Timestamp('2023-12-01')]\nassert monthly.TotalRegistrations.sum() == pd.to_numeric(raw['จำนวน']).sum()\npartial = monthly[monthly.Date == '2026-02-01']\nassert partial.Records.iloc[0] == 6 and partial.TotalRegistrations.iloc[0] == 18\ndisplay(monthly.head())\ndisplay(partial)"),
    md("## 3. Choose complete months, create lags, split chronologically\nเลือก Jan 2024–Jan 2026 จำนวน 25 เดือน "
       "สร้าง Lag1–Lag3 จากอดีตเท่านั้น เหลือ 22 แถว แบ่งตามตำแหน่งเป็น 15/7 ห้าม shuffle "
       "เดือน February 2026 ไม่ได้เป็น actual ที่สมบูรณ์จึงไม่ใช้ฝึกหรือทดสอบ"),
    code(definitions["prepare_model_data"] + "\n\nforecast_data, model_data, train, test = prepare_model_data(monthly)\nassert [len(forecast_data), len(model_data), len(train), len(test)] == [25, 22, 15, 7]\nassert train.Date.max() < test.Date.min()\nprint('Source:', forecast_data.Date.min(), 'to', forecast_data.Date.max(), len(forecast_data))\nprint('Train:', train.Date.min(), 'to', train.Date.max(), len(train))\nprint('Test:', test.Date.min(), 'to', test.Date.max(), len(test))\ndisplay(model_data.head())\ndisplay(test)"),
    md("## 4. Train and compare five methods\nNaive ใช้ Lag1 โดยไม่ต้อง fit "
       "Ridge alpha=1.0, Random Forest 100 trees/depth 3/seed 42, "
       "Gradient Boosting 100 rounds/learning rate 0.05/depth 2/seed 42 ตามสไลด์ 70 "
       "MAE และ RMSE วัดจำนวนคันที่ผิดพลาด R² ไม่ใช่เปอร์เซ็นต์ความแม่นยำ"),
    code(definitions["make_models"] + "\n\n" + definitions["evaluate_models"] + "\n\nmodels = make_models()\ncomparison, predictions = evaluate_models(models, train, test)\nbest_model_name = comparison.iloc[0].Model\nassert comparison.SelectedModel.sum() == 1\nprint('Selected by lowest MAE:', best_model_name)\ndisplay(comparison)"),
    md("## 5. Retrain selected model and predict February 2026\nหลังจบการประเมินจึงฝึกใหม่ด้วย 22 observations "
       "ใช้ Jan 2026 / Dec 2025 / Nov 2025 เป็น Lag1–Lag3 "
       "หาก Naive ชนะจะใช้เดือนล่าสุดโดยไม่เรียก fit โมเดล"),
    code(definitions["forecast_next_month"] + "\n\nfuture_prediction, final_model = forecast_next_month(best_model_name, models, model_data, forecast_data)\nforecast_month = forecast_data.Date.max() + pd.DateOffset(months=1)\nfuture_input = pd.DataFrame({f'Lag{i}': [forecast_data.TotalRegistrations.iloc[-i]] for i in range(1, 4)})\ndisplay(future_input)\nprint('Forecast month:', forecast_month.strftime('%Y-%m'))\nprint('Unrounded forecast:', future_prediction)\nprint('Forecast vehicles:', round(future_prediction))"),
    md("## 6. Export the required Power BI CSVs and verify saved files\nHistory 18 แถว / Test 7 แถว / Future 1 แถว "
       "เว้น Actual ของ Future ว่าง ไม่ใช้ 0 และไม่เอา 18 คันจากข้อมูลไม่ครบมาเป็น Ground Truth "
       "ชื่อโมเดลและ prediction ทุกส่วนใช้โมเดลที่ได้รับเลือกจริง"),
    code("powerbi, verification = write_outputs(folder, raw, monthly, forecast_data, model_data, train, test, comparison, predictions, future_prediction)\ncomparison_path = folder / 'DLT_Model_Comparison_PowerBI.csv'\nforecast_path = folder / 'DLT_Vehicle_Forecast_PowerBI.csv'\nsaved_comparison = pd.read_csv(comparison_path, encoding='utf-8-sig')\nsaved_forecast = pd.read_csv(forecast_path, encoding='utf-8-sig', parse_dates=['Date'])\nassert saved_comparison.columns.tolist() == ['Model','MAE','RMSE','R2','SelectedModel']\nassert saved_forecast.columns.tolist() == ['Date','ActualRegistrations','ForecastRegistrations','DatasetSegment','Model']\nassert saved_forecast.DatasetSegment.value_counts().to_dict() == {'History':18,'Test':7,'Future':1}\nassert saved_forecast[saved_forecast.DatasetSegment == 'Future'].ActualRegistrations.isna().all()\nassert saved_forecast.Model.eq(best_model_name).all()\nprint('Saved:', comparison_path.resolve(), comparison_path.exists())\nprint('Saved:', forecast_path.resolve(), forecast_path.exists())\ndisplay(saved_forecast.tail(8))\ndisplay(FileLink(str(comparison_path)))\ndisplay(FileLink(str(forecast_path)))"),
    md("## 7. Review model comparison and actual vs forecast\nMAE เรียงน้อยไปมาก "
       "เส้น Actual ใช้ Date จริง ส่วน forecast แสดง Test และแยก Future ที่ไม่มี actual "
       "ภาพรวมนี้เป็นภาพตรวจผลการคำนวณ งาน Power BI .pbix ต้องเปิดและตรวจแยกต่างหาก"),
    code("display(Image(filename=str(folder / 'model_comparison.png')))\ndisplay(Image(filename=str(folder / 'actual_vs_forecast.png')))\ndisplay(Image(filename=str(folder / 'Workshop10_Forecast_Dashboard.png')))"),
    md("## 8. Compare the observed result with the slide example\nค่าตัวอย่างเป็น benchmark สำหรับตรวจสอบเท่านั้น "
       "ไม่ได้กำหนดผลที่โมเดลต้องคืน ถ้าไม่เท่าต้องรายงานผลจริงและตรวจช่วงข้อมูล พารามิเตอร์ seed และเวอร์ชัน"),
    code("rf = comparison[comparison.Model == 'Random Forest'].iloc[0]\nbenchmark = verification['slide_expected_rf']\nprint('RF MAE difference from slide:', rf.MAE - benchmark['MAE'])\nprint('RF RMSE difference from slide:', rf.RMSE - benchmark['RMSE'])\nprint('RF R2 difference from slide:', rf.R2 - benchmark['R2'])\nprint('Rounded forecast difference from slide:', round(future_prediction) - benchmark['forecast_rounded'])\nprint('The computed values reproduce the slide benchmark.' if np.allclose([rf.MAE,rf.RMSE,rf.R2],[benchmark['MAE'],benchmark['RMSE'],benchmark['R2']]) and round(future_prediction) == benchmark['forecast_rounded'] else 'The computed results differ; preserve and explain the measured results.')"),
    md("## 9. สรุปผลหนึ่งย่อหน้าและข้อจำกัด\nข้อจำกัดการทดสอบช่วงเดียวและการใช้ test เลือกโมเดล "
       "ควรมี rolling-origin validation และข้อมูลภายนอกเพิ่มก่อนใช้งานจริง"),
    code("print((folder / 'summary.txt').read_text(encoding='utf-8'))"),
]
notebook = nbformat.v4.new_notebook(cells=cells, metadata={
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.11.9"},
})
kernel_root = folder / ".jupyter" / "kernels"
kernel_folder = kernel_root / "workshop10"
kernel_folder.mkdir(parents=True, exist_ok=True)
(kernel_folder / "kernel.json").write_text(json.dumps({
    "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
    "display_name": "Workshop 10 dedicated Python", "language": "python"
}), encoding="utf-8")
manager = KernelManager(kernel_name="workshop10", kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(kernel_root)]))
client = NotebookClient(notebook, timeout=180, kernel_name="workshop10", km=manager,
                        resources={"metadata": {"path": str(folder)}})
client.execute()
nbformat.validate(notebook)
output = folder / "DLT_Vehicle_Registration_Forecasting.ipynb"
nbformat.write(notebook, output)
code_cells = [cell for cell in notebook.cells if cell.cell_type == "code"]
assert all(cell.execution_count is not None for cell in code_cells)
assert not any(output.output_type == "error" for cell in code_cells for output in cell.outputs)
print(f"Fresh kernel Run All passed: {len(code_cells)} executable cells; saved {output}")
