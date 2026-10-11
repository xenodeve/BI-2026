"""Proposed DLT brand/type decision support project; approvals and members pending."""
from pathlib import Path
import hashlib, json, platform, sys
import numpy as np
import pandas as pd
import sklearn
from sklearn.base import clone
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

RAW_NAME='DLT_First_Registration_Monthly_Original_Combined.csv'
SOURCE_URL='https://gdcatalog.dlt.go.th/en/dataset/stat_1_1_01_first_regis_vehicles_car'
FEATURES=['Lag1','Lag2','Lag3','MonthSin','MonthCos','TimeIndex']
DATES=pd.date_range('2024-01-01','2026-01-01',freq='MS')
TYPE_LABELS={
    'รถจักรยานยนต์':'Motorcycles',
    'รถยนต์นั่งส่วนบุคคลไม่เกิน 7 คน':'Private passenger cars up to 7 seats',
    'รถยนต์บรรทุกส่วนบุคคล':'Private trucks',
    'รถแทร็กเตอร์':'Tractors',
    'รถยนต์นั่งส่วนบุคคลเกิน 7 คน':'Private passenger cars over 7 seats',
}


def prepare_fact(raw):
    data=raw.copy()
    for col in ['Source_Year_BE','Source_Month','จำนวน']:
        data[col]=pd.to_numeric(data[col],errors='raise')
    required=['Source_Year_BE','Source_Month','จำนวน','ยี่ห้อ','ประเภทรถ']
    if data[required].isna().any().any() or (data['จำนวน']<0).any():
        raise ValueError('Required source fields missing or negative count')
    data['Date']=pd.to_datetime(dict(year=data.Source_Year_BE-543,month=data.Source_Month,day=1))
    data['Brand']=data['ยี่ห้อ'].astype(str).str.strip().str.upper()
    data['VehicleType']=data['ประเภทรถ'].astype(str).str.strip()
    data['VehicleModel']=data['รุ่น'].fillna('Unknown model').astype(str).str.strip()
    quality=data.groupby('Date',as_index=False).agg(SourceRegistrations=('จำนวน','sum'),SourceRecords=('จำนวน','size'))
    quality['IsComplete']=quality.Date!=pd.Timestamp('2026-02-01')
    quality['UsedForModeling']=quality.Date.isin(DATES)
    selected=data[data.Date.isin(DATES)].copy()
    if sorted(selected.Date.unique().tolist())!=DATES.tolist():
        raise ValueError('Need 25 continuous complete source months')
    fact=selected.groupby(['Date','Brand','VehicleType'],as_index=False).agg(
        Registrations=('จำนวน','sum'),SourceRecords=('จำนวน','size'))
    stages=[
        {'Stage':'Raw read','InputRows':len(raw),'OutputRows':len(raw),'Reason':'Original retained without modification'},
        {'Stage':'Type validation and normalize labels','InputRows':len(raw),'OutputRows':len(data),'Reason':'Validate counts/period and trim labels; missing model mapped to Unknown model'},
        {'Stage':'Complete consecutive period','InputRows':len(data),'OutputRows':len(selected),'Reason':'Jan 2024-Jan 2026; exclude earlier discontinuous period and incomplete Feb 2026'},
        {'Stage':'Monthly brand vehicle type fact','InputRows':len(selected),'OutputRows':len(fact),'Reason':'Sum registrations at Date Brand VehicleType grain; preserve SourceRecords'},
    ]
    assert fact.Registrations.sum()==selected['จำนวน'].sum()
    assert fact.SourceRecords.sum()==len(selected)
    return fact,quality,pd.DataFrame(stages)


def segment_series(fact, kind, name):
    if kind=='Total':
        selected=fact
    else:
        selected=fact[fact[kind]==name]
    values=selected.groupby('Date').Registrations.sum().reindex(DATES,fill_value=0)
    # Zero means no records for this category inside a verified complete source month.
    return values.rename('Registrations').reset_index().rename(columns={'index':'Date'})


def choose_series(fact):
    past=fact[fact.Date<='2025-03-01']
    series=[('Total','All')]
    for kind in ['Brand','VehicleType']:
        names=past.groupby(kind).Registrations.sum().sort_values(ascending=False).head(3).index
        series.extend((kind,name) for name in names)
    return series


def prepare_modeling(series):
    if series.Date.tolist()!=DATES.tolist():
        raise ValueError('Need 25 continuous complete source months')
    data=series.copy()
    for lag in range(1,4):
        data[f'Lag{lag}']=data.Registrations.shift(lag)
    data['MonthSin']=np.sin(2*np.pi*data.Date.dt.month/12)
    data['MonthCos']=np.cos(2*np.pi*data.Date.dt.month/12)
    data['TimeIndex']=np.arange(len(data))
    data=data.dropna().reset_index(drop=True)
    return data,data.iloc[:12].copy(),data.iloc[12:17].copy(),data.iloc[17:].copy()


def make_models():
    return {
        'Linear Regression':make_pipeline(StandardScaler(),LinearRegression()),
        'Ridge Regression':make_pipeline(StandardScaler(),Ridge(alpha=10.0)),
        'Random Forest':RandomForestRegressor(n_estimators=200,max_depth=3,min_samples_leaf=2,random_state=42),
        'Gradient Boosting':GradientBoostingRegressor(n_estimators=200,learning_rate=.03,max_depth=2,random_state=42),
    }


def metrics(actual,prediction):
    return {'MAE':float(mean_absolute_error(actual,prediction)),
            'RMSE':float(np.sqrt(mean_squared_error(actual,prediction))),
            'R2':float(r2_score(actual,prediction))}


def select_model(results):
    return results.sort_values('ValidationMAE',kind='stable').iloc[0].Model


def train_evaluate_series(series):
    data,train,validation,test=prepare_modeling(series)
    models=make_models()
    val_predictions={'Naive Forecast':validation.Lag1.to_numpy()}
    for name,model in models.items():
        model.fit(train[FEATURES],train.Registrations)
        val_predictions[name]=np.maximum(model.predict(validation[FEATURES]),0)
    val_results=pd.DataFrame([{'Model':name,**{f'Validation{k}':v for k,v in metrics(validation.Registrations,pred).items()}}
                              for name,pred in val_predictions.items()])
    best=select_model(val_results)  # Frozen before inspecting test metrics.
    fit_data=pd.concat([train,validation],ignore_index=True)
    test_predictions={'Naive Forecast':test.Lag1.to_numpy()}
    for name,model in models.items():
        model=clone(model).fit(fit_data[FEATURES],fit_data.Registrations)
        test_predictions[name]=np.maximum(model.predict(test[FEATURES]),0)
    test_results=pd.DataFrame([{'Model':name,**{f'Test{k}':v for k,v in metrics(test.Registrations,pred).items()}}
                               for name,pred in test_predictions.items()])
    results=val_results.merge(test_results,on='Model').sort_values('ValidationMAE',kind='stable').reset_index(drop=True)
    results['SelectedModel']=results.Model.eq(best)
    future_date=series.Date.max()+pd.DateOffset(months=1)
    future_input=pd.DataFrame({**{f'Lag{i}':[series.Registrations.iloc[-i]] for i in range(1,4)},
        'MonthSin':[np.sin(2*np.pi*future_date.month/12)],
        'MonthCos':[np.cos(2*np.pi*future_date.month/12)],'TimeIndex':[len(series)]})
    if best=='Naive Forecast':
        future_prediction=float(series.Registrations.iloc[-1])
    else:
        final=clone(models[best]).fit(data[FEATURES],data.Registrations)
        future_prediction=float(max(0,final.predict(future_input)[0]))
    forecast=series.rename(columns={'Registrations':'ActualRegistrations'}).copy()
    forecast['ForecastRegistrations']=np.nan
    forecast['DatasetSegment']='History'
    forecast.loc[forecast.Date.isin(validation.Date),'ForecastRegistrations']=val_predictions[best]
    forecast.loc[forecast.Date.isin(validation.Date),'DatasetSegment']='Validation'
    forecast.loc[forecast.Date.isin(test.Date),'ForecastRegistrations']=test_predictions[best]
    forecast.loc[forecast.Date.isin(test.Date),'DatasetSegment']='Test'
    forecast=pd.concat([forecast,pd.DataFrame({'Date':[future_date],'ActualRegistrations':[np.nan],
        'ForecastRegistrations':[future_prediction],'DatasetSegment':['Future']})],ignore_index=True)
    forecast['Model']=best
    errors=pd.DataFrame({'Date':test.Date,'ActualRegistrations':test.Registrations,
                        'PredictedRegistrations':test_predictions[best]})
    errors['AbsoluteError']=(errors.ActualRegistrations-errors.PredictedRegistrations).abs()
    errors['Model']=best
    return results,forecast,data,errors


def evaluate_hypotheses(fact, comparisons):
    full=fact[fact.Date.dt.year.isin([2024,2025])]
    total=float(full.Registrations.sum())
    motorcycles=float(full.loc[full.VehicleType=='รถจักรยานยนต์','Registrations'].sum())
    brand_totals=full.groupby('Brand').Registrations.sum().sort_values(ascending=False)
    passenger=full[full.VehicleType=='รถยนต์นั่งส่วนบุคคลไม่เกิน 7 คน'].groupby(full.Date.dt.year).Registrations.sum()
    jan=fact[fact.Date.dt.month==1].groupby(fact.Date.dt.year).Registrations.sum()
    selected_total=comparisons[(comparisons.SegmentType=='Total')&comparisons.SelectedModel].iloc[0]
    naive_total=comparisons[(comparisons.SegmentType=='Total')&(comparisons.Model=='Naive Forecast')].iloc[0]
    def row(id,question,value,threshold,supported,interpretation):
        return {'Hypothesis':id,'Question':question,'ObservedValue':value,'Threshold':threshold,
                'Result':'Supported descriptively' if supported else 'Not supported descriptively','Interpretation':interpretation}
    return pd.DataFrame([
        row('H1','Motorcycles exceed 50 percent of registrations in 2024-2025',motorcycles/total,.5,motorcycles/total>.5,'Registration composition, not sales or causal demand'),
        row('H2','Honda is the largest brand overall in 2024-2025',float(brand_totals.get('HONDA',0))/total,0,brand_totals.index[0]=='HONDA','Overall brand composition mixes motorcycles and passenger cars; compare brands within type for a product decision'),
        row('H3','Private passenger car registrations declined in 2025 against 2024',float(passenger.loc[2025]/passenger.loc[2024]-1),0,passenger.loc[2025]<passenger.loc[2024],'Like-for-like full calendar years within passenger cars up to 7 seats'),
        row('H4','The largest 3 brands account for over 70 percent in 2024-2025',float(brand_totals.head(3).sum())/total,.7,brand_totals.head(3).sum()/total>.7,'Full-period concentration is descriptive; predictive segment selection uses training period only'),
        row('H5','January 2026 registrations exceed January 2025',float(jan.loc[2026]/jan.loc[2025]-1),0,jan.loc[2026]>jan.loc[2025],'A one-month year-on-year change does not prove sustained growth'),
        row('H6','The validation-selected total model beats Naive on held-out test MAE',float(1-selected_total.TestMAE/naive_total.TestMAE),0,selected_total.TestMAE<naive_total.TestMAE,'Test is reporting-only; a negative improvement does not permit switching the selected model'),
    ])


def make_charts(folder,fact,comparisons,forecasts):
    import matplotlib.pyplot as plt
    from matplotlib.ticker import StrMethodFormatter
    plt.rcParams.update({'font.family':'Tahoma','font.size':11})
    full=fact[fact.Date.dt.year.isin([2024,2025])]
    fig,axes=plt.subplots(1,2,figsize=(15,6))
    brands=full.groupby('Brand').Registrations.sum().sort_values(ascending=False).head(8)
    axes[0].barh(brands.index[::-1],brands.iloc[::-1],color='#197369')
    axes[0].set_title('Largest brands 2024–2025'); axes[0].set_xlabel('Registrations')
    types=full.groupby('VehicleType').Registrations.sum().sort_values(ascending=False).head(5)
    labels=[TYPE_LABELS.get(x,x) for x in types.index[::-1]]
    axes[1].barh(labels,types.iloc[::-1],color='#294e74')
    axes[1].set_title('Largest vehicle types 2024–2025');axes[1].set_xlabel('Registrations')
    for ax in axes:
        ax.xaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))
        ax.spines[['top','right']].set_visible(False)
    fig.tight_layout();fig.savefig(folder/'brand_type_composition.png',dpi=180);plt.close(fig)
    selected=comparisons[comparisons.SelectedModel].copy()
    fig,ax=plt.subplots(figsize=(13,6))
    positions=np.arange(len(selected))
    ax.bar(positions-.2,selected.ValidationMAE,.4,label='Validation MAE (selection)',color='#197369')
    ax.bar(positions+.2,selected.TestMAE,.4,label='Held-out test MAE (reporting)',color='#c3732b')
    labels=[TYPE_LABELS.get(x,x) for x in selected.SegmentName]
    labels=[x.replace('Private passenger cars up to 7 seats','Passenger cars ≤7 seats') for x in labels]
    ax.set_xticks(positions,labels,rotation=20,ha='right')
    ax.set_ylabel('Vehicles per month');ax.set_title('Selected model errors by series')
    ax.legend();ax.yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))
    fig.tight_layout();fig.savefig(folder/'validation_test_errors.png',dpi=180);plt.close(fig)
    fig,axes=plt.subplots(4,2,figsize=(15,15));axes=axes.ravel()
    for ax,(series_key,series) in zip(axes,forecasts.groupby('SeriesKey',sort=False)):
        label=TYPE_LABELS.get(series.SegmentName.iloc[0],series.SegmentName.iloc[0])
        ax.plot(series.Date,series.ActualRegistrations,label='Actual',color='#294e74')
        for segment,color in [('Validation','#8395a7'),('Test','#197369'),('Future','#c3732b')]:
            part=series[series.DatasetSegment==segment]
            ax.plot(part.Date,part.ForecastRegistrations,marker='o',linestyle='--',color=color,label=segment)
        ax.set_title(f'{label}\n{series.Model.iloc[0]}',fontsize=11)
        ax.tick_params(axis='x',rotation=25)
        ax.yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))
        ax.legend(fontsize=8,loc='best')
    axes[-1].axis('off')
    fig.suptitle('Independent segment forecasts — model selected on validation only',fontsize=18)
    fig.tight_layout(rect=(0,0,1,.97));fig.savefig(folder/'segment_forecasts.png',dpi=170);plt.close(fig)


def main():
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    folder=Path(__file__).resolve().parent
    raw=pd.read_csv(folder/RAW_NAME,encoding='utf-8-sig')
    fact,quality,etl=prepare_fact(raw)
    series_list=choose_series(fact)
    comparisons=[];forecasts=[];modeling=[];errors=[]
    for index,(kind,name) in enumerate(series_list,1):
        key=f'S{index:02d}'
        result,forecast,features,error=train_evaluate_series(segment_series(fact,kind,name))
        for frame in [result,forecast,features,error]:
            frame.insert(0,'SeriesKey',key);frame.insert(1,'SegmentType',kind);frame.insert(2,'SegmentName',name)
        comparisons.append(result);forecasts.append(forecast);modeling.append(features);errors.append(error)
    comparisons=pd.concat(comparisons,ignore_index=True)
    forecasts=pd.concat(forecasts,ignore_index=True)
    modeling=pd.concat(modeling,ignore_index=True)
    errors=pd.concat(errors,ignore_index=True)
    hypotheses=evaluate_hypotheses(fact,comparisons)
    brand_names=sorted(fact.Brand.unique())
    type_names=sorted(fact.VehicleType.unique())
    dim_brand=pd.DataFrame({'BrandKey':range(1,len(brand_names)+1),'Brand':brand_names})
    dim_type=pd.DataFrame({'VehicleTypeKey':range(1,len(type_names)+1),'VehicleType':type_names})
    dim_type['VehicleTypeEnglish']=dim_type.VehicleType.map(TYPE_LABELS).fillna(dim_type.VehicleType)
    fact=fact.merge(dim_brand,on='Brand',validate='many_to_one').merge(dim_type[['VehicleTypeKey','VehicleType']],on='VehicleType',validate='many_to_one')
    fact_export=fact[['Date','BrandKey','VehicleTypeKey','Registrations','SourceRecords']]
    brand_month=fact.groupby(['Date','BrandKey','Brand'],as_index=False).agg(Registrations=('Registrations','sum'),SourceRecords=('SourceRecords','sum'))
    type_month=fact.groupby(['Date','VehicleTypeKey','VehicleType'],as_index=False).agg(Registrations=('Registrations','sum'),SourceRecords=('SourceRecords','sum'))
    monthly_totals=fact.groupby('Date').Registrations.sum()
    for frame in [brand_month,type_month]:
        frame['RegistrationShare']=frame.Registrations/frame.Date.map(monthly_totals)
    dim_date=pd.DataFrame({'Date':pd.date_range('2024-01-01','2026-02-28',freq='D')})
    dim_date['Year']=dim_date.Date.dt.year;dim_date['YearBE']=dim_date.Year+543
    dim_date['Month']=dim_date.Date.dt.month;dim_date['YearMonth']=dim_date.Date.dt.strftime('%Y-%m')
    dim_date['YearMonthSort']=dim_date.Year*100+dim_date.Month
    dim_date['IsCompleteMonth']=dim_date.Date<'2026-02-01'
    dim_series=forecasts[['SeriesKey','SegmentType','SegmentName']].drop_duplicates()
    dim_series['DisplayName']=dim_series.SegmentName.map(TYPE_LABELS).fillna(dim_series.SegmentName)
    files={'FactRegistrations.csv':fact_export,'DimBrand.csv':dim_brand,'DimVehicleType.csv':dim_type,'DimDate.csv':dim_date,
        'DimSeries.csv':dim_series,'BrandMonthly.csv':brand_month,'VehicleTypeMonthly.csv':type_month,
        'FactForecast.csv':forecasts,'ModelComparison.csv':comparisons,'ModelFeatures.csv':modeling,
        'TestErrors.csv':errors,'DataQuality.csv':quality,'ETL_Counts.csv':etl,'HypothesisEvidence.csv':hypotheses}
    for name,frame in files.items():
        frame.to_csv(folder/name,index=False,encoding='utf-8-sig',date_format='%Y-%m-%d')
    raw_definitions={
        'ปี พ.ศ.':'Original Buddhist-era year label; use numeric Source_Year_BE for grouping',
        'เดือน':'Original Thai month name; use numeric Source_Month for grouping',
        'ประเภทรถ':'DLT vehicle type label',
        'ยี่ห้อ':'Vehicle brand label',
        'รุ่น':'Vehicle model label; 623 raw nulls retained for brand/type aggregation',
        'จำนวน':'Registrations represented by this source row (vehicles)',
        'Source_Year_BE':'Numeric source Buddhist-era year; subtract543 for Gregorian year',
        'Source_Month':'Numeric source month1-12',
        'Source_File':'Original monthly source filename for lineage',
    }
    dictionary=[{'Table':'RawData','Column':column,'Type':str(raw[column].dtype),
                 'Definition':raw_definitions[column],'Grain':'One original source period type brand model record'} for column in raw.columns]
    for name,frame in files.items():
        for column in frame.columns:
            dictionary.append({'Table':name.removesuffix('.csv'),'Column':column,'Type':str(frame[column].dtype),
                'Definition':column_definition(column),'Grain':table_grain(name)})
    pd.DataFrame(dictionary).to_csv(folder/'DataDictionary.csv',index=False,encoding='utf-8-sig')
    make_charts(folder,fact,comparisons,forecasts)
    original_months=pd.DatetimeIndex(quality.Date)
    missing=pd.date_range(original_months.min(),original_months.max(),freq='MS').difference(original_months)
    q1,q3=raw['จำนวน'].quantile([.25,.75]);outliers=int((raw['จำนวน']>q3+1.5*(q3-q1)).sum())
    manifest={'status':'Proposal and computed analysis; group identities, uniqueness and instructor topic approval pending',
        'source_url':SOURCE_URL,'source_sha256':hashlib.sha256((folder/RAW_NAME).read_bytes()).hexdigest(),
        'raw_rows':len(raw),'raw_columns':len(raw.columns),'null_counts':{k:int(v) for k,v in raw.isna().sum().items()},
        'exact_duplicate_rows':int(raw.duplicated().sum()),'natural_key_duplicate_rows':int(raw.duplicated(['Source_Year_BE','Source_Month','ประเภทรถ','ยี่ห้อ','รุ่น']).sum()),
        'raw_count_iqr_high_outliers':outliers,'outlier_action':'Retain valid aggregated counts; category volumes are heterogeneous and high volume is not proof of error',
        'missing_months':[x.strftime('%Y-%m-%d') for x in missing],'complete_months':25,
        'raw_total_registrations':int(raw['จำนวน'].sum()),'complete_period_registrations':int(fact.Registrations.sum()),
        'complete_period_source_records':int(fact.SourceRecords.sum()),'fact_rows':len(fact),'brands':len(dim_brand),'vehicle_types':len(dim_type),
        'train_period':['2024-04-01','2025-03-01'],'validation_period':['2025-04-01','2025-08-01'],'test_period':['2025-09-01','2026-01-01'],
        'observations_per_series':{'source':25,'modeling':22,'train':12,'validation':5,'test':5},
        'selection':'Lowest validation MAE, frozen before test; models refit on train+validation for test and all complete modeling data for future',
        'feature_definition':FEATURES,'prediction_constraint':'Negative model predictions clipped to zero before every evaluation and future forecast',
        'series_selection':'Total + top3 brands + top3 vehicle types ranked only with source months Jan2024-Mar2025',
        'versions':{'python':platform.python_version(),'pandas':pd.__version__,'numpy':np.__version__,'scikit-learn':sklearn.__version__},
        'selected_models':comparisons[comparisons.SelectedModel].to_dict('records'),
        'future_forecasts':forecasts[forecasts.DatasetSegment=='Future'].drop(columns='Date').astype(object).where(pd.notnull(forecasts[forecasts.DatasetSegment=='Future'].drop(columns='Date')),None).to_dict('records'),
        'hypotheses':hypotheses.to_dict('records'),'output_schemas':{name:{'rows':len(frame),'columns':frame.columns.tolist()} for name,frame in files.items()}}
    (folder/'verification.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    print(comparisons[comparisons.SelectedModel][['SegmentType','SegmentName','Model','ValidationMAE','TestMAE','TestRMSE','TestR2']].to_string(index=False))
    print(forecasts[forecasts.DatasetSegment=='Future'][['SegmentType','SegmentName','ForecastRegistrations','Model']].to_string(index=False))
    print(hypotheses[['Hypothesis','ObservedValue','Result']].to_string(index=False))
    return manifest


def column_definition(column):
    definitions={'Date':'Period date (monthly facts use first day; DimDate is daily)',
        'Registrations':'Sum of source vehicle registration counts; vehicles not source rows',
        'SourceRecords':'Number of original source rows represented by this aggregate',
        'ActualRegistrations':'Observed complete-month registration count; blank for Future',
        'ForecastRegistrations':'Model prediction in vehicles; blank for History; nonnegative',
        'SelectedModel':'True for the lowest-validation-MAE method for its series; never selected using test',
        'RegistrationShare':'Category registrations divided by all registrations in same month',
        'DatasetSegment':'History, Validation, Test or Future; periods and fit boundaries fixed chronologically',
        'SeriesKey':'Unique forecast series identity; total/brand/type forecasts overlap and must not be summed together',
        'IsComplete':'Observed source month treated as complete except known partial Feb2026; a missing month has no row',
        'UsedForModeling':'True for Jan2024-Jan2026 source months',
        'VehicleTypeEnglish':'English display label for major types; original Thai preserved',
        'Result':'Descriptive assessment on supplied records; no causal or population inference',
        'TimeIndex':'Months since Jan2024 (0-based); known calendar feature',
        'MonthSin':'sin(2*pi*month/12), known calendar seasonal feature',
        'MonthCos':'cos(2*pi*month/12), known calendar seasonal feature'}
    if column.startswith('Lag'):return f'Registrations observed {column[-1]} month(s) before target month'
    if column.startswith('Validation'):return 'Validation '+column.removeprefix('Validation')+'; Apr-Aug2025 using model fit on training only'
    if column.startswith('Test'):return 'Held-out test '+column.removeprefix('Test')+'; Sep2025-Jan2026 using refit on train+validation'
    return definitions.get(column,column+'; see table grain and notebook context')


def table_grain(name):
    grains={'FactRegistrations.csv':'One Date BrandKey VehicleTypeKey combination',
        'BrandMonthly.csv':'One Date BrandKey combination','VehicleTypeMonthly.csv':'One Date VehicleTypeKey combination',
        'FactForecast.csv':'One SeriesKey Date combination','ModelComparison.csv':'One SeriesKey Model combination',
        'ModelFeatures.csv':'One SeriesKey Date target observation','TestErrors.csv':'One selected SeriesKey Date held-out prediction',
        'DataQuality.csv':'One original observed source month','ETL_Counts.csv':'One transformation stage',
        'HypothesisEvidence.csv':'One proposed descriptive hypothesis','DimDate.csv':'One calendar day'}
    return grains.get(name,'One unique dimension key')


if __name__=='__main__':main()
