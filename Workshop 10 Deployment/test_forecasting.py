"""Behavior checks: catch dropped records, temporal leakage and false actuals."""
from pathlib import Path
import pandas as pd
import numpy as np
import pytest
import importlib


def implementation():
    assert Path(__file__).with_name("forecasting.py").exists(), "Forecast pipeline not implemented"
    return importlib.import_module("forecasting")


def fixture_raw():
    # 25 complete months, two source records per month, plus a partial future.
    dates = pd.date_range("2024-01-01", "2026-01-01", freq="MS")
    rows = []
    for i, date in enumerate(dates):
        rows.extend([{ "Source_Year_BE": date.year + 543, "Source_Month": date.month,
                       "จำนวน": value} for value in [i + 1, 100]])
    rows.append({"Source_Year_BE": 2569, "Source_Month": 2, "จำนวน": 18})
    return pd.DataFrame(rows).sample(frac=1, random_state=9)


def test_monthly_aggregation_sums_records_and_converts_be_year():
    f = implementation()
    monthly = f.aggregate_monthly(fixture_raw())
    assert monthly.iloc[0]["Date"] == pd.Timestamp("2024-01-01")
    assert monthly.iloc[0]["TotalRegistrations"] == 101
    assert monthly.iloc[0]["Records"] == 2
    assert monthly.iloc[-1]["TotalRegistrations"] == 18


def test_lags_use_past_months_and_split_never_shuffles():
    f = implementation()
    source, modeling, train, test = f.prepare_model_data(f.aggregate_monthly(fixture_raw()))
    assert [len(t) for t in [source, modeling, train, test]] == [25, 22, 15, 7]
    assert modeling.iloc[0][["Lag1", "Lag2", "Lag3"]].tolist() == [103, 102, 101]
    assert train.Date.min() == pd.Timestamp("2024-04-01")
    assert train.Date.max() == pd.Timestamp("2025-06-01")
    assert test.Date.min() == pd.Timestamp("2025-07-01")
    assert test.Date.max() == pd.Timestamp("2026-01-01")


def test_future_and_later_test_changes_cannot_change_training_or_earlier_features():
    f = implementation()
    raw = fixture_raw()
    baseline = f.prepare_model_data(f.aggregate_monthly(raw))
    raw.loc[(raw.Source_Year_BE == 2569) & (raw.Source_Month == 2), "จำนวน"] = 999999999
    future_mutation = f.prepare_model_data(f.aggregate_monthly(raw))
    pd.testing.assert_frame_equal(baseline[1], future_mutation[1])
    raw.loc[(raw.Source_Year_BE == 2569) & (raw.Source_Month == 1), "จำนวน"] = 999999999
    later_mutation = f.prepare_model_data(f.aggregate_monthly(raw))
    pd.testing.assert_frame_equal(baseline[2], later_mutation[2])
    pd.testing.assert_frame_equal(baseline[3][f.FEATURES], later_mutation[3][f.FEATURES])


def test_missing_month_is_detected_and_not_silently_imputed():
    f = implementation()
    monthly = f.aggregate_monthly(fixture_raw())
    monthly = monthly[monthly.Date != pd.Timestamp("2024-12-01")]
    assert f.missing_months(monthly) == [pd.Timestamp("2024-12-01")]
    with pytest.raises(ValueError, match="continuous"):
        f.prepare_model_data(monthly)


def test_export_segments_keep_future_actual_blank_and_use_selected_predictions():
    f = implementation()
    source, modeling, train, test = f.prepare_model_data(f.aggregate_monthly(fixture_raw()))
    out = f.build_forecast_export(source, test, np.arange(7) + 50, "Naive Forecast", 125)
    assert out.columns.tolist() == ["Date", "ActualRegistrations", "ForecastRegistrations", "DatasetSegment", "Model"]
    assert out.DatasetSegment.value_counts().to_dict() == {"History": 18, "Test": 7, "Future": 1}
    future = out.iloc[-1]
    assert future.Date == pd.Timestamp("2026-02-01")
    assert pd.isna(future.ActualRegistrations)
    assert future.ForecastRegistrations == 125
    assert out[out.DatasetSegment == "History"].ForecastRegistrations.isna().all()
    assert out[out.DatasetSegment == "Test"].ForecastRegistrations.tolist() == list(range(50, 57))


def test_naive_winner_forecasts_without_a_fit_model():
    f = implementation()
    source, modeling, train, test = f.prepare_model_data(f.aggregate_monthly(fixture_raw()))
    result, model = f.forecast_next_month("Naive Forecast", {}, modeling, source)
    assert result == 125
    assert model is None
