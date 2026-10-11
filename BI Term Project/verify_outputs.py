"""Independent CSV verification using original records and hand-derived contracts."""
from pathlib import Path
from collections import Counter,defaultdict
import csv,json,math,hashlib
import numpy as np
import pandas as pd
import term_project as project

folder=Path(__file__).resolve().parent
def read(name):
    with (folder/name).open(encoding='utf-8-sig',newline='') as file:return list(csv.DictReader(file))

raw=read(project.RAW_NAME)
complete=[r for r in raw if (2024,1)<=(int(r['Source_Year_BE'])-543,int(r['Source_Month']))<=(2026,1)]
source_sum=sum(int(r['จำนวน']) for r in complete)
fact=read('FactRegistrations.csv')
assert len(raw)==68398 and len(complete)==35805
assert source_sum==5007659
assert sum(int(r['Registrations']) for r in fact)==source_sum
assert sum(int(r['SourceRecords']) for r in fact)==len(complete)
assert len({r['Date'] for r in fact})==25
assert len({(r['Date'],r['BrandKey'],r['VehicleTypeKey']) for r in fact})==len(fact)
assert set(r['BrandKey'] for r in fact)<=set(r['BrandKey'] for r in read('DimBrand.csv'))
assert set(r['VehicleTypeKey'] for r in fact)<=set(r['VehicleTypeKey'] for r in read('DimVehicleType.csv'))
assert set(r['Date'] for r in fact)<=set(r['Date'] for r in read('DimDate.csv'))
comparison=read('ModelComparison.csv');forecast=read('FactForecast.csv');errors=read('TestErrors.csv')
assert len(comparison)==35 and len(forecast)==182 and len(errors)==35
for series in {r['SeriesKey'] for r in forecast}:
    methods=[r for r in comparison if r['SeriesKey']==series]
    winner=[r for r in methods if r['SelectedModel']=='True']
    assert len(winner)==1
    winner=winner[0]
    assert float(winner['ValidationMAE'])==min(float(r['ValidationMAE']) for r in methods)
    rows=[r for r in forecast if r['SeriesKey']==series]
    assert Counter(r['DatasetSegment'] for r in rows)=={'History':15,'Validation':5,'Test':5,'Future':1}
    assert all(r['Model']==winner['Model'] for r in rows)
    future=[r for r in rows if r['DatasetSegment']=='Future'][0]
    assert future['Date']=='2026-02-01' and future['ActualRegistrations']==''
    assert float(future['ForecastRegistrations'])>=0
    assert all(r['ForecastRegistrations']=='' for r in rows if r['DatasetSegment']=='History')
    cases=[r for r in errors if r['SeriesKey']==series]
    abs_errors=[abs(float(r['ActualRegistrations'])-float(r['PredictedRegistrations'])) for r in cases]
    mae=sum(abs_errors)/len(abs_errors)
    rmse=math.sqrt(sum(e*e for e in abs_errors)/len(abs_errors))
    actual=[float(r['ActualRegistrations']) for r in cases]
    mean=sum(actual)/len(actual)
    r2=1-sum(e*e for e in abs_errors)/sum((x-mean)**2 for x in actual)
    assert math.isclose(mae,float(winner['TestMAE']),abs_tol=1e-8)
    assert math.isclose(rmse,float(winner['TestRMSE']),abs_tol=1e-8)
    assert math.isclose(r2,float(winner['TestR2']),abs_tol=1e-10)
    exported_test={r['Date']:float(r['ForecastRegistrations']) for r in rows if r['DatasetSegment']=='Test'}
    assert all(math.isclose(exported_test[r['Date']],float(r['PredictedRegistrations']),abs_tol=1e-8) for r in cases)

# Falsify a test-data selection leak: change the last test target dramatically.
data=pd.read_csv(folder/project.RAW_NAME)
fact_original,_,_=project.prepare_fact(data)
original_series=project.segment_series(fact_original,'Total','All')
original_result,_,original_features,_=project.train_evaluate_series(original_series)
data.loc[(data.Source_Year_BE==2569)&(data.Source_Month==1),'จำนวน']*=10
fact_changed,_,_=project.prepare_fact(data)
changed_result,_,changed_features,_=project.train_evaluate_series(project.segment_series(fact_changed,'Total','All'))
assert project.select_model(original_result)==project.select_model(changed_result)
np.testing.assert_allclose(original_result.ValidationMAE,changed_result.ValidationMAE,rtol=0,atol=0)
pd.testing.assert_frame_equal(original_features.iloc[:17],changed_features.iloc[:17])
notebook=json.loads((folder/'DLT_Brand_Type_Term_Project.ipynb').read_text(encoding='utf-8'))
code_cells=[r for r in notebook['cells'] if r['cell_type']=='code']
assert all(r['execution_count'] is not None for r in code_cells)
assert not any(o['output_type']=='error' for r in code_cells for o in r['outputs'])
json.loads((folder/'verification.json').read_text(encoding='utf-8'),parse_constant=lambda value:(_ for _ in ()).throw(ValueError(value)))
report={'source_reconciliation':True,'fact_dimension_integrity':True,'forecast_null_and_segment_contract':True,
        'validation_only_selection':True,'independent_test_metric_recalculation':True,
        'test_target_mutation_does_not_change_selection':True,'executed_notebook_code_cells':len(code_cells)}
(folder/'output_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
