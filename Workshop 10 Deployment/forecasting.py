"""Workshop 10 DLT monthly forecasting, following slides 67–74.

Evaluation is a fixed-model, rolling one-month-ahead test: observed previous
test months can be lags, but model training only uses Apr 2024–Jun 2025.
"""
from pathlib import Path
import hashlib
import json
import platform
import numpy as np
import pandas as pd
import sklearn
from sklearn.base import clone
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

FEATURES = ["Lag1", "Lag2", "Lag3"]
RAW_NAME = "DLT_First_Registration_Monthly_Original_Combined.csv"


def aggregate_monthly(raw):
    """Sum registrations and count source records, using source period fields."""
    required = ["Source_Year_BE", "Source_Month", "จำนวน"]
    if not set(required).issubset(raw.columns):
        raise ValueError("Missing required source columns")
    data = raw.copy()
    for column in required:
        data[column] = pd.to_numeric(data[column], errors="raise")
    if data[required].isna().any().any() or (data["จำนวน"] < 0).any():
        raise ValueError("Null source period/count or negative registrations")
    monthly = data.groupby(required[:2], as_index=False).agg(
        TotalRegistrations=("จำนวน", "sum"), Records=("จำนวน", "size")
    ).sort_values(required[:2]).reset_index(drop=True)
    monthly["Date"] = pd.to_datetime(dict(
        year=monthly.Source_Year_BE - 543, month=monthly.Source_Month, day=1
    ))
    return monthly


def missing_months(monthly):
    complete = pd.date_range(monthly.Date.min(), monthly.Date.max(), freq="MS")
    return complete.difference(monthly.Date).tolist()


def prepare_model_data(monthly):
    source = monthly[monthly.Date.between("2024-01-01", "2026-01-01")].copy()
    source = source.sort_values("Date").reset_index(drop=True)
    expected = pd.date_range("2024-01-01", "2026-01-01", freq="MS")
    if source.Date.tolist() != expected.tolist():
        raise ValueError("Model period must contain 25 continuous complete months")
    modeling = source[["Date", "TotalRegistrations"]].copy()
    for lag in range(1, 4):
        modeling[f"Lag{lag}"] = modeling.TotalRegistrations.shift(lag)
    modeling = modeling.dropna().reset_index(drop=True)
    split_index = int(len(modeling) * 0.70)
    train = modeling.iloc[:split_index].copy()
    test = modeling.iloc[split_index:].copy()
    return source, modeling, train, test


def make_models():
    return {
        "Linear Regression": LinearRegression(),
        "Ridge Regression": Ridge(alpha=1.0),
        "Random Forest": RandomForestRegressor(n_estimators=100, max_depth=3, random_state=42),
        "Gradient Boosting": GradientBoostingRegressor(
            n_estimators=100, learning_rate=0.05, max_depth=2, random_state=42
        ),
    }


def evaluate_models(models, train, test):
    predictions = {"Naive Forecast": test.Lag1.to_numpy()}
    for name, model in models.items():
        model.fit(train[FEATURES], train.TotalRegistrations)
        predictions[name] = model.predict(test[FEATURES])
    results = []
    for name, predicted in predictions.items():
        results.append({
            "Model": name,
            "MAE": float(mean_absolute_error(test.TotalRegistrations, predicted)),
            "RMSE": float(np.sqrt(mean_squared_error(test.TotalRegistrations, predicted))),
            "R2": float(r2_score(test.TotalRegistrations, predicted)),
        })
    comparison = pd.DataFrame(results).sort_values("MAE", kind="stable").reset_index(drop=True)
    comparison["SelectedModel"] = comparison.Model == comparison.iloc[0].Model
    return comparison, predictions


def forecast_next_month(best_name, models, modeling, source):
    if best_name == "Naive Forecast":
        return float(source.TotalRegistrations.iloc[-1]), None
    final_model = clone(models[best_name])
    final_model.fit(modeling[FEATURES], modeling.TotalRegistrations)
    latest = source.TotalRegistrations.iloc[-3:]
    future_input = pd.DataFrame({
        "Lag1": [latest.iloc[-1]], "Lag2": [latest.iloc[-2]], "Lag3": [latest.iloc[-3]]
    })
    return float(final_model.predict(future_input)[0]), final_model


def build_forecast_export(source, test, test_predictions, best_name, future_prediction):
    export = source[["Date", "TotalRegistrations"]].rename(
        columns={"TotalRegistrations": "ActualRegistrations"}
    ).copy()
    export["ForecastRegistrations"] = np.nan
    export["DatasetSegment"] = "History"
    test_rows = export.Date.isin(test.Date)
    export.loc[test_rows, "ForecastRegistrations"] = test_predictions
    export.loc[test_rows, "DatasetSegment"] = "Test"
    future = pd.DataFrame({
        "Date": [source.Date.max() + pd.DateOffset(months=1)],
        "ActualRegistrations": [np.nan],
        "ForecastRegistrations": [round(future_prediction)],
        "DatasetSegment": ["Future"],
    })
    export = pd.concat([export, future], ignore_index=True)
    export["Model"] = best_name
    return export


def create_charts(comparison, export, output_dir):
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.ticker import StrMethodFormatter
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
    best = comparison.iloc[0]
    fig, ax = plt.subplots(figsize=(11, 5.5))
    bars = ax.barh(comparison.Model, comparison.MAE,
                  color=["#197369" if value else "#8395a7" for value in comparison.SelectedModel])
    ax.invert_yaxis()
    ax.bar_label(bars, labels=[f"{value:,.2f}" for value in comparison.MAE], padding=6)
    ax.set_xlim(0, comparison.MAE.max() * 1.22)
    ax.set_xlabel("Mean absolute error (vehicles per month)")
    ax.set_title("DLT model comparison — same 7 test months", loc="left", fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(output_dir / "model_comparison.png", dpi=180)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(13, 6))
    ax.plot(export.Date, export.ActualRegistrations, color="#294e74", marker="o", label="Actual")
    test = export[export.DatasetSegment == "Test"]
    future = export[export.DatasetSegment == "Future"].iloc[0]
    ax.plot(test.Date, test.ForecastRegistrations, color="#197369", marker="s",
            linestyle="--", label=f"Test forecast: {best.Model}")
    ax.scatter([future.Date], [future.ForecastRegistrations], marker="D", s=75,
               color="#c3732b", label="Future forecast (actual unavailable)", zorder=5)
    ax.axvspan(test.Date.min() - pd.Timedelta(days=15), test.Date.max() + pd.Timedelta(days=15),
               alpha=0.06, color="#197369")
    ax.annotate(f"Feb 2026: {future.ForecastRegistrations:,.0f}",
                (future.Date, future.ForecastRegistrations), xytext=(-155, 38),
                textcoords="offset points", arrowprops={"arrowstyle": "->", "color": "#c3732b"})
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    ax.set_ylabel("Vehicle registrations")
    ax.set_title("DLT monthly registrations — actual and selected model forecast", loc="left", fontweight="bold")
    ax.legend(loc="lower left")
    ax.grid(axis="y", alpha=.2)
    ax.spines[["top", "right"]].set_visible(False)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(output_dir / "actual_vs_forecast.png", dpi=180)
    plt.close(fig)
    # Static review dashboard. This is an image, not evidence of Power BI completion.
    fig = plt.figure(figsize=(16, 10), facecolor="#f5f7f9")
    gs = fig.add_gridspec(3, 2, height_ratios=[0.7, 2, 2], left=.16, right=.97, top=.92,
                         bottom=.07, hspace=.6, wspace=.45)
    fig.suptitle("DLT Vehicle Registration Forecast", x=.06, ha="left", fontsize=23, fontweight="bold")
    card = fig.add_subplot(gs[0, 0]); card.axis("off")
    card.text(0, .85, "Selected model", color="#536271", fontsize=12)
    card.text(0, .15, str(best.Model), color="#197369", fontsize=22, fontweight="bold")
    forecast_card = fig.add_subplot(gs[0, 1]); forecast_card.axis("off")
    forecast_card.text(0, .85, "Forecast for February 2026 (vehicles)", color="#536271", fontsize=12)
    forecast_card.text(0, .1, f"{future.ForecastRegistrations:,.0f}", color="#c3732b", fontsize=30, fontweight="bold")
    ax = fig.add_subplot(gs[1, 0])
    ax.barh(comparison.Model, comparison.MAE, color=["#197369"] + ["#8395a7"] * 4)
    ax.invert_yaxis(); ax.set_title("Test MAE, smallest first", loc="left")
    ax.xaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    ax.set_xlabel("Vehicles per month")
    ax = fig.add_subplot(gs[1, 1]); ax.axis("off")
    ax.text(0, .95, f"MAE: {best.MAE:,.2f}\nRMSE: {best.RMSE:,.2f}\nR²: {best.R2:.4f}", fontsize=20, va="top", linespacing=1.8)
    ax.text(0, .1, "15 training months / 7 test months\nJan 2024–Jan 2026 source period", fontsize=12, color="#536271")
    ax = fig.add_subplot(gs[2, :])
    ax.plot(export.Date, export.ActualRegistrations, marker="o", color="#294e74", label="Actual")
    ax.plot(test.Date, test.ForecastRegistrations, marker="s", linestyle="--", color="#197369", label="Test forecast")
    ax.scatter([future.Date], [future.ForecastRegistrations], color="#c3732b", marker="D", s=65, label="Future forecast")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    ax.legend(loc="lower left"); ax.set_title("Actual vs forecast", loc="left")
    ax.grid(axis="y", alpha=.2)
    fig.text(.06, .015, "Future actual is blank. Partial February source excluded. Static review image; Power BI report must be verified separately.", fontsize=10, color="#536271")
    fig.savefig(output_dir / "Workshop10_Forecast_Dashboard.png", dpi=180)
    plt.close(fig)


def write_outputs(output_dir, raw, monthly, source, modeling, train, test, comparison, predictions, forecast):
    best_name = comparison.iloc[0].Model
    export = build_forecast_export(source, test, predictions[best_name], best_name, forecast)
    comparison.to_csv(output_dir / "DLT_Model_Comparison_PowerBI.csv", index=False, encoding="utf-8-sig")
    export.to_csv(output_dir / "DLT_Vehicle_Forecast_PowerBI.csv", index=False, encoding="utf-8-sig", date_format="%Y-%m-%d")
    monthly.to_csv(output_dir / "monthly_data_quality.csv", index=False, encoding="utf-8-sig", date_format="%Y-%m-%d")
    modeling.to_csv(output_dir / "modeling_data.csv", index=False, encoding="utf-8-sig", date_format="%Y-%m-%d")
    audit = test[["Date", "TotalRegistrations"]].rename(columns={"TotalRegistrations": "ActualRegistrations"}).copy()
    for name, values in predictions.items():
        audit[name] = values
    audit.to_csv(output_dir / "test_predictions_all_models.csv", index=False, encoding="utf-8-sig", date_format="%Y-%m-%d")
    create_charts(comparison, export, output_dir)
    best = comparison.iloc[0]
    summary = (f"จากข้อมูลรถจดทะเบียนครั้งแรกของกรมการขนส่งทางบก {len(raw):,} แถว 9 คอลัมน์ "
        f"เมื่อรวมเป็นรายเดือนได้ {len(monthly)} เดือน พบเดือนธันวาคม 2566 ขาดหาย และข้อมูลกุมภาพันธ์ 2569 "
        "มีเพียง 6 รายการรวม 18 คัน จึงเลือกข้อมูลที่ต่อเนื่องตั้งแต่มกราคม 2567 ถึงมกราคม 2569 จำนวน 25 เดือน "
        "สร้าง Lag1–Lag3 เหลือ 22 ตัวอย่าง และแบ่งตามเวลาเป็นชุดฝึก 15 เดือนและชุดทดสอบ 7 เดือนโดยไม่สุ่ม "
        f"เมื่อเปรียบเทียบ 5 วิธี {best_name} ให้ MAE ต่ำที่สุดเท่ากับ {best.MAE:,.2f} คันต่อเดือน "
        f"RMSE {best.RMSE:,.2f} คัน และ R² {best.R2:.4f} จึงเลือกและฝึกใหม่ด้วยข้อมูลแบบจำลองทั้งหมด "
        f"เพื่อพยากรณ์กุมภาพันธ์ 2569 ได้ {round(forecast):,} คัน ซึ่งเป็นค่าพยากรณ์และเว้น Actual ของเดือนอนาคตว่าง "
        "การทดสอบเป็นการพยากรณ์ล่วงหน้าทีละหนึ่งเดือนโดยใช้ยอดจริงเดือนก่อนที่ทราบแล้วเป็น Lag "
        "ข้อจำกัดคือข้อมูลแบบจำลองและชุดทดสอบมีจำนวนน้อย ใช้เพียงข้อมูลย้อนหลัง 3 เดือน ไม่มีปัจจัยภายนอก "
        "และทดสอบเพียงช่วงเดียว การเลือกโมเดลจากชุดทดสอบเดียวกันยังไม่มีชุดตรวจสอบอิสระ "
        "R² จึงต้องอ่านเป็นการอธิบายความแปรปรวน ไม่ใช่เปอร์เซ็นต์ความแม่นยำ ผลเหมาะกับการเรียนรู้และควรตรวจสอบเพิ่มก่อนใช้งานจริง")
    (output_dir / "summary.txt").write_text(summary + "\n", encoding="utf-8")
    future_partial = monthly[monthly.Date == pd.Timestamp("2026-02-01")].iloc[0]
    manifest = {
        "source_file": RAW_NAME,
        "source_sha256": hashlib.sha256((output_dir / RAW_NAME).read_bytes()).hexdigest(),
        "raw_rows": len(raw), "raw_columns": len(raw.columns), "monthly_rows": len(monthly),
        "missing_months": [value.strftime("%Y-%m-%d") for value in missing_months(monthly)],
        "excluded_partial_month": {"date": "2026-02-01", "records": int(future_partial.Records), "registrations": int(future_partial.TotalRegistrations)},
        "source_period": ["2024-01-01", "2026-01-01"], "source_months": len(source),
        "model_observations": len(modeling), "train_observations": len(train), "test_observations": len(test),
        "train_period": [str(train.Date.min().date()), str(train.Date.max().date())],
        "test_period": [str(test.Date.min().date()), str(test.Date.max().date())],
        "evaluation": "Fixed training fit; rolling one-month-ahead test using observed preceding months as lag inputs.",
        "selected_model": best_name, "future_month": "2026-02-01",
        "future_prediction_unrounded": forecast, "future_prediction_rounded": round(forecast),
        "future_lags": {f"Lag{i}": int(source.TotalRegistrations.iloc[-i]) for i in range(1, 4)},
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__, "scikit-learn": sklearn.__version__},
        "comparison": comparison.to_dict("records"),
        "slide_expected_rf": {"MAE": 14208.358696711997, "RMSE": 20836.620066511627, "R2": 0.20399610771490717, "forecast_rounded": 204586},
    }
    (output_dir / "forecast_verification.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return export, manifest


def main():
    folder = Path(__file__).resolve().parent
    raw = pd.read_csv(folder / RAW_NAME, encoding="utf-8-sig")
    monthly = aggregate_monthly(raw)
    source, modeling, train, test = prepare_model_data(monthly)
    models = make_models()
    comparison, predictions = evaluate_models(models, train, test)
    future_prediction, _ = forecast_next_month(comparison.iloc[0].Model, models, modeling, source)
    export, manifest = write_outputs(folder, raw, monthly, source, modeling, train, test, comparison, predictions, future_prediction)
    print(comparison.to_string(index=False))
    print(json.dumps({"forecast": future_prediction, "rounded": round(future_prediction), "versions": manifest["versions"]}, indent=2))
    return manifest


if __name__ == "__main__":
    main()
