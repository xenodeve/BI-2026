"""Tests catch segment double counts, time leakage and test-based selection."""
import importlib
from pathlib import Path
import pandas as pd
import pytest


def implementation():
    assert Path(__file__).with_name('term_project.py').exists(), 'Term project pipeline missing'
    return importlib.import_module('term_project')


def sample_raw():
    rows = []
    for i, date in enumerate(pd.date_range('2024-01-01','2026-01-01',freq='MS')):
        rows.append({'Source_Year_BE':date.year+543,'Source_Month':date.month,'จำนวน':100+i,'ยี่ห้อ':'A','ประเภทรถ':'Car','รุ่น':'One','Source_File':'source.csv'})
        if i != 2:
            rows.append({'Source_Year_BE':date.year+543,'Source_Month':date.month,'จำนวน':20,'ยี่ห้อ':'B','ประเภทรถ':'Bike','รุ่น':'Two','Source_File':'source.csv'})
    rows.append({'Source_Year_BE':2569,'Source_Month':2,'จำนวน':999999,'ยี่ห้อ':'NEW','ประเภทรถ':'Bike','รุ่น':'Two','Source_File':'source.csv'})
    return pd.DataFrame(rows)


def test_complete_month_fact_reconciles_and_excludes_partial_future():
    f=implementation()
    fact, dq, etl = f.prepare_fact(sample_raw())
    assert fact.Date.nunique() == 25
    assert fact.Date.max() == pd.Timestamp('2026-01-01')
    assert fact.Registrations.sum() == 3280
    assert fact.SourceRecords.sum() == 49


def test_absent_segment_is_zero_only_inside_verified_complete_months():
    f=implementation()
    fact, dq, etl = f.prepare_fact(sample_raw())
    series = f.segment_series(fact, 'Brand', 'B')
    assert len(series) == 25
    assert series.loc[series.Date == '2024-03-01','Registrations'].iloc[0] == 0
    assert series.loc[series.Date == '2024-04-01','Registrations'].iloc[0] == 20


def test_split_is_train_validation_test_with_lags_and_no_overlap():
    f=implementation()
    fact, dq, etl=f.prepare_fact(sample_raw())
    modeling, train, validation, test=f.prepare_modeling(f.segment_series(fact,'Total','All'))
    assert [len(x) for x in [modeling,train,validation,test]] == [22,12,5,5]
    assert train.Date.max() == pd.Timestamp('2025-03-01')
    assert validation.Date.min() == pd.Timestamp('2025-04-01')
    assert validation.Date.max() == pd.Timestamp('2025-08-01')
    assert test.Date.min() == pd.Timestamp('2025-09-01')
    assert modeling.iloc[0][['Lag1','Lag2','Lag3']].tolist() == [102,121,120]


def test_selection_cannot_choose_model_for_low_test_error():
    f=implementation()
    results=pd.DataFrame({'Model':['Validation Winner','Test Winner'],'ValidationMAE':[1,9],'TestMAE':[100,1]})
    assert f.select_model(results) == 'Validation Winner'


def test_segment_choice_only_uses_training_period():
    f=implementation()
    fact, dq, etl=f.prepare_fact(sample_raw())
    fact.loc[fact.Date>'2025-03-01','Brand'] = 'NewTestBrand'
    series=f.choose_series(fact)
    assert 'NewTestBrand' not in [value for kind,value in series if kind=='Brand']


def test_missing_source_month_is_rejected():
    f=implementation()
    raw=sample_raw()
    raw=raw[~((raw.Source_Year_BE==2567)&(raw.Source_Month==7))]
    with pytest.raises(ValueError,match='25 continuous'):
        f.prepare_fact(raw)
