"""Author Word/PDF report from measured outputs using bundled document libraries."""
from pathlib import Path
import csv,json,html,math,hashlib
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter

folder=Path(__file__).resolve().parent
m=json.loads((folder/'verification.json').read_text(encoding='utf-8'))
def read(name):
    with (folder/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def label(value):
    return {'All':'Total','รถจักรยานยนต์':'Motorcycles',
        'รถยนต์นั่งส่วนบุคคลไม่เกิน 7 คน':'Passenger cars up to 7 seats',
        'รถยนต์บรรทุกส่วนบุคคล':'Private trucks'}.get(value,value)
selected=m['selected_models'];future=m['future_forecasts'];hypotheses=m['hypotheses']
total=selected[0];etl=read('ETL_Counts.csv')
evidence_dir=folder/'native_evidence'
def native_result(name):
    envelope=json.loads((evidence_dir/name).read_text(encoding='utf-8'))
    assert not envelope.get('isError'),name
    return json.loads(envelope['content'][0]['text'])['data']
refresh=json.loads((evidence_dir/'pbi-term-refresh-result.json').read_text(encoding='utf-8'))
assert not refresh.get('isError')
native_totals=native_result('pbi-term-dax-totals-result.json')['rows'][0]
native_series=native_result('pbi-term-dax-forecast-result.json')['rows']
expected_totals={'[Registrations]':5007659,'[SourceRecords]':35805,'[FactRows]':5712,'[Brands]':421,'[Types]':16,'[RawRows]':68398,'[Months]':25}
for key,value in expected_totals.items():assert native_totals[key]==value,(key,native_totals[key])
assert native_totals['[UnsafeAggregatedForecast]'] is None
assert len(native_series)==7
for row in native_series:
    expected=next(item for item in selected if item['SeriesKey']==row['DimSeries[SeriesKey]'])
    future_expected=next(item for item in future if item['SeriesKey']==row['DimSeries[SeriesKey]'])
    assert row['[SelectedModel]']==expected['Model']
    for native_key,computed_key in [('[ValidationMAE]','ValidationMAE'),('[TestMAE]','TestMAE'),('[RMSE]','TestRMSE'),('[R2]','TestR2')]:
        assert math.isclose(row[native_key],expected[computed_key],rel_tol=0,abs_tol=1e-8)
    assert math.isclose(row['[Future]'],future_expected['ForecastRegistrations'],rel_tol=0,abs_tol=1e-8)
main_pages=['Executive Summary','Data Quality','Diagnostic Insight','Predictive Results','Decision Recommendation']
for name in main_pages:assert (folder/'screenshots'/f'{name}.png').is_file()
native_progress={'full_refresh_reported_pass':True,'native_dax_totals_verified':True,'native_dax_seven_series_verified':True,
    'unsafe_multi_series_forecast_blank':True,'desktop_process':68744,'engine_port':50620,
    'source_receipts':[str((evidence_dir/name).resolve()) for name in ['pbi-term-refresh-result.json','pbi-term-dax-totals-result.json','pbi-term-dax-forecast-result.json']],
    'screenshot_sha256':{name:hashlib.sha256((folder/'screenshots'/f'{name}.png').read_bytes()).hexdigest() for name in main_pages},
    'native_field_parameter_authored_selections_verified':True,
    'native_field_parameter_proof':'docs/execution/term-parameter-native-verification.md',
    'native_field_parameter_cases':{'canonical_default':{'metric':'Registrations','HONDA':2938308},
        'source_records_clone':{'metric':'Source records','HONDA':1950},
        'registrations_per_record_clone':{'metric':'Registrations/source record','HONDA':1506.8246153846153}},
    'canonical_parameter_patch_scope':{'checked_files':96,'changed_files':1,
        'changed_component':'Metric slicer saved field-identity selection','semantic_model_and_csv_data_unchanged':True},
    'pending':['Final PBIX save and close/reopen','Actual Metric dropdown clicks','Brand hover tooltip context','Drillthrough with retained filters and Ctrl-click Back','Native Word pagination','Real group members and topic/dataset approval'],
    'scope':'Native operations controlled by root; compute worker checks saved receipts/screenshots. Visible Back label is configuration evidence only.'}
(folder/'native_progress_verification.json').write_text(json.dumps(native_progress,ensure_ascii=False,indent=2),encoding='utf-8')
errors=sorted(read('TestErrors.csv'),key=lambda r:float(r['AbsoluteError']),reverse=True)
brand_counts={}
for row in read('BrandMonthly.csv'):
    if row['Date']<'2026-01-01':brand_counts[row['Brand']]=brand_counts.get(row['Brand'],0)+int(row['Registrations'])
presentation_data={'verification':m,'native_progress':native_progress,'top_brands':sorted(brand_counts.items(),key=lambda item:item[1],reverse=True)[:6],
    'etl':etl,'total_models':[row for row in read('ModelComparison.csv') if row['SeriesKey']=='S01'],
    'total_forecast':[row for row in read('FactForecast.csv') if row['SeriesKey']=='S01' and row['Date']>='2025-03-01'],
    'worst_errors':errors[:4]}
(folder/'presentation-build'/'presentation_data.json').write_text(json.dumps(presentation_data,ensure_ascii=False,indent=2),encoding='utf-8')
blocks=[
    [
        ('title','DLT Brand and Vehicle Type Demand Analysis'),
        ('text','Business Intelligence Term Project proposal with computed results and native Desktop evidence'),
        ('text','Prepared 11 October 2026. Group members and student IDs have not been supplied. A group of 2–5 actual members, confirmation that the proposed topic and dataset do not duplicate another group, and instructor approval are pending. This report does not claim those requirements are complete.'),
        ('head','Business problem and intended users'),
        ('text','A vehicle distributor or market analyst needs to see which vehicle types and brands account for registrations, how the mix changes, and which segments can be forecast with acceptable error. National totals alone can hide a strong motorcycle share and different trends within passenger cars and trucks. The proposed decision support system therefore separates brand and vehicle type analysis and evaluates seven forecast series.'),
        ('head','Computed conclusion'),
        ('text',f'Motorcycles represent {hypotheses[0]["ObservedValue"]:.2%} of registrations in the complete 2024–2025 calendar years. Honda is the largest brand overall at {hypotheses[1]["ObservedValue"]:.2%}, but its overall position must not be confused with leadership within passenger cars. The hypothesis that private passenger car registrations declined in 2025 is not supported: this category grew {hypotheses[2]["ObservedValue"]:.2%}.'),
        ('text',f'For the total series, validation selects {total["Model"]}; its independent five-month test MAE is {total["TestMAE"]:,.2f} vehicles and the February 2026 forecast is {future[0]["ForecastRegistrations"]:,.2f} vehicles. Different segments select different methods, so a single model is not imposed on every category.'),
        ('head','Scope and success criteria'),
        ('text','The supplied snapshot contains 68,398 source records. Analysis uses 25 consecutive complete months from January 2024 to January 2026. Source totals, six hypotheses and five methods have been computed and checked. The five main Power BI pages have actual Desktop captures, and native DAX agrees with all seven series. Final PBIX save/reopen, genuine feature interactions, Word pagination and group identities remain pending.'),
        ('text','Registrations are a proxy for market activity. This dataset contains registration counts, not transaction prices, inventory, customer intent, profitability, regional demand, or vehicle fuel type. A brand name alone is not evidence of electric vehicle status.'),
    ],
    [
        ('head','Data source and quality'),
        ('text','Source organization: Department of Land Transport, Thailand. The DLT Data Catalog identifies the first-registration dataset by vehicle type, brand and model. The computational source is the raw CSV supplied with the course, preserved without modification. The catalog establishes a traceable public source; this report does not claim every supplied byte was redownloaded and checked against the current online resource.'),
        ('text',m['source_url']),
        ('table',['Quality check','Measured outcome'],[
            ['Raw rows and columns','68,398 rows and 9 columns'],
            ['Observed source months','49 months; December 2023 is absent'],
            ['Incomplete February 2026','6 records representing 18 registrations; excluded'],
            ['Missing vehicle model names','623 source rows retained as Unknown model'],
            ['Missing required counts and period fields','0'],
            ['Exact duplicate rows','0'],
            ['Duplicate period type brand model keys','0'],
            ['High counts flagged by 1.5 IQR rule',f'{m["raw_count_iqr_high_outliers"]:,} source rows; retained'],
            ['Complete analysis period','January 2024 through January 2026; 25 months'],
        ],[2.7,3.9]),
        ('text','The IQR rule is a diagnostic flag, not a deletion rule. Source records represent aggregated counts for heterogeneous brands and models; a high-volume category can be valid. Removing those counts would bias total registrations and composition. Missing model names do not prevent brand/type analysis, so their registrations remain in the sums.'),
        ('head','Snapshot provenance'),
        ('text','File: DLT_First_Registration_Monthly_Original_Combined.csv. SHA256: '+m['source_sha256']),
        ('text','Each raw record includes Source_Year_BE, Source_Month and Source_File. Source year minus 543 gives the Gregorian year. The original Thai period labels remain in the raw file; aggregation uses the numeric source period fields. An absent category in a verified complete month has a zero category count. An absent or incomplete source month is never filled as zero actual.'),
    ],
    [
        ('head','ETL and data model'),
        ('table',['Transformation','Input rows','Output rows'],[[r['Stage'],r['InputRows'],r['OutputRows']] for r in etl],[3.6,1.5,1.5]),
        ('text','The monthly fact grain is one date, one brand and one vehicle type. Aggregation preserves both the sum of registrations and the number of original source rows. The complete period contains 35,805 source records and 5,007,659 registrations. All fact aggregates reconcile to these original records.'),
        ('table',['Table','Grain or role'],[
            ['FactRegistrations','5,712 monthly Date × BrandKey × VehicleTypeKey aggregates'],
            ['DimDate','One calendar day; continuous date table for time intelligence'],
            ['DimBrand','421 unique brand keys and names'],
            ['DimVehicleType','16 unique vehicle type keys and Thai labels'],
            ['DimSeries','7 forecast series with type and display name'],
            ['FactForecast','182 rows; one date per series including Future'],
            ['ModelComparison','35 rows; one model per series'],
            ['TestErrors','35 selected-model held-out test predictions'],
            ['DataQuality and ETL_Counts','Original month coverage and transformation audit'],
        ],[2.1,4.5]),
        ('text','Use one-to-many, single-direction relationships from DimDate, DimBrand and DimVehicleType to FactRegistrations. DimDate also filters FactForecast. DimSeries filters FactForecast, ModelComparison and TestErrors. Keep model-selection tables separate from historical fact sums. Do not join forecast series to brand/type dimensions using overlapping text labels.'),
        ('text','Total, brand and vehicle-type forecasts overlap: the total already contains the brands and types. They are not additive and must never be summed across all seven series. A forecast card requires exactly one series. FactRegistrations is the authoritative source for historical totals and shares.'),
        ('text','DataDictionary.csv documents exported fields and table grain. ModelFeatures.csv preserves every lag/calendar input. BrandMonthly.csv and VehicleTypeMonthly.csv provide reconciled views for review. The raw CSV, preparation code, executed notebook and count audit allow the ETL to be repeated.'),
    ],
    [
        ('head','Hypotheses and measured evidence'),
        ('text','These six proposed questions are assessed descriptively on the supplied registration snapshot. The results are not statistical significance claims and do not establish causal mechanisms.'),
        ('head','H1 Motorcycles exceed half of registrations'),
        ('text',f'In the complete calendar years 2024–2025, motorcycles account for {hypotheses[0]["ObservedValue"]:.4%}. This exceeds the prespecified 50% threshold. Supported descriptively. The business implication is to avoid presenting the national series as passenger-car demand.'),
        ('head','H2 Honda is the largest brand overall'),
        ('text',f'Honda accounts for {hypotheses[1]["ObservedValue"]:.4%} of all registrations in 2024–2025 and has the highest brand count. Supported descriptively. Product-level decisions still need the vehicle-type filter because overall brand composition includes motorcycles.'),
        ('head','H3 Private passenger car registrations decline'),
        ('text',f'Private passenger cars with up to 7 seats increased {hypotheses[2]["ObservedValue"]:.4%} in 2025 relative to the full year 2024. The decline hypothesis is not supported. The report preserves this contradiction rather than changing the hypothesis to fit the result.'),
        ('head','H4 Three brands account for over seventy percent'),
        ('text',f'The three largest brands account for {hypotheses[3]["ObservedValue"]:.4%} in 2024–2025, exceeding 70%. Supported descriptively. This descriptive full-period concentration does not determine predictive segment selection; forecast brands are selected using past training-period volume only.'),
        ('head','H5 January 2026 exceeds January 2025'),
        ('text',f'January registrations increased {hypotheses[4]["ObservedValue"]:.4%}, from 227,900 in 2025 to 250,212 in 2026. Supported descriptively. One strong month cannot prove continuing growth for the rest of 2026.'),
        ('head','H6 The selected total model improves on Naive'),
        ('text',f'The validation-selected total method reduces held-out test MAE by {hypotheses[5]["ObservedValue"]:.4%} against Naive on the same five months. Supported descriptively. Test is reporting-only; if a test result were worse, that would not authorize switching to another model after seeing test.'),
    ],
    [
        ('head','Predictive methodology'),
        ('text','Seven independent series are modeled: national total; Honda, Toyota and Yamaha; motorcycles, private passenger cars up to 7 seats, and private trucks. The top three brands and types are selected using January 2024–March 2025 volume only, so later validation/test composition cannot influence which segments enter the modeling comparison.'),
        ('table',['Partition','Target period','Observations'],[
            ['Train','April 2024–March 2025','12'],
            ['Validation','April–August 2025','5'],
            ['Held-out test','September 2025–January 2026','5'],
            ['Final fit','All 22 lag observations','22'],
        ],[1.5,3.6,1.5]),
        ('text','The source has 25 complete months. Lag1, Lag2 and Lag3 use prior observed counts; the first three months have no full lag history. MonthSin and MonthCos encode the known calendar cycle, and TimeIndex counts months since January 2024. This yields 22 target observations per series. No row shuffling is used.'),
        ('table',['Method','Fixed specification'],[
            ['Naive Forecast','Use Lag1; no model fit'],
            ['Linear Regression','StandardScaler fitted inside the training pipeline'],
            ['Ridge Regression','StandardScaler pipeline; alpha 10.0'],
            ['Random Forest','200 trees; depth 3; min_samples_leaf 2; seed 42'],
            ['Gradient Boosting','200 rounds; learning rate 0.03; depth 2; seed 42'],
        ],[2.1,4.5]),
        ('text','Lowest validation MAE selects the method before test evaluation. Each method is refit on the 17 train-plus-validation observations for a fair independent test comparison. The selected method is then refit on all 22 complete observations to forecast February 2026. Every model prediction is constrained to be nonnegative before evaluation. Naive needs no fit when it wins.'),
        ('text','Validation and test are rolling one-month-ahead predictions with the fitted model held fixed within each partition. An observed previous validation/test month may provide a lag for the next month. This does not forecast all five months simultaneously from a single cutoff. Scaling learns only from the data passed to fit.'),
    ],
    [
        ('head','Model results and future forecasts'),
        ('text','The table reports only the method chosen on validation for each series. ModelComparison.csv retains validation and test metrics for all five methods. Test MAE, RMSE and R² are independent reporting measures and do not control the selected flag.'),
        ('table',['Series','Selected method','Validation MAE','Test MAE','Test R²'],[
            [label(r['SegmentName']),r['Model'],f'{r["ValidationMAE"]:,.2f}',f'{r["TestMAE"]:,.2f}',f'{r["TestR2"]:.4f}'] for r in selected
        ],[1.8,1.6,1.1,1.1,1.0]),
        ('text',f'Total-series test RMSE is {total["TestRMSE"]:,.2f} vehicles. MAE is the average absolute count error; RMSE gives greater weight to large errors. R² compares squared error with the test-mean reference, so a negative R² is possible and is not a negative accuracy percentage.'),
        ('table',['February 2026 series','Forecast vehicles'],[[label(r['SegmentName']),f'{r["ForecastRegistrations"]:,.2f}'] for r in future],[4.3,2.3]),
        ('text','February actual values are blank in every series. Forecast values retain model precision in the CSV; whole-vehicle displays may round for readability. These seven overlapping forecasts are independent and are not reconciled into a hierarchical total. A selected private-truck Naive model is retained because its validation MAE won.'),
    ],
    [
        ('head','Error analysis and interpretation'),
        ('image','validation_test_errors.png',6.6,3.05),
        ('text',f'The total series has a January 2026 actual of 250,212 compared with a selected-model test prediction of 213,296.68, an absolute error of 36,915.32. Passenger cars show a much larger January peak than typical preceding months. Lag/calendar inputs alone do not explain the external cause of this increase.'),
        ('table',['Series','Date','Actual','Prediction','Absolute error'],[
            [label(r['SegmentName']),r['Date'],f'{float(r["ActualRegistrations"]):,.0f}',f'{float(r["PredictedRegistrations"]):,.2f}',f'{float(r["AbsoluteError"]):,.2f}'] for r in errors[:5]
        ],[1.8,1.0,1.1,1.35,1.35]),
        ('text','Forecast quality differs by series and by period. A lower validation error is not a guarantee of a lower future error. Several selected segments have negative held-out R² despite being the best validation method. Relative error and the business scale of a series should accompany absolute MAE when prioritizing investigation.'),
        ('text','Only five validation and five test months are available. The project has one time split, fixed algorithms, no external drivers and no calibrated prediction intervals. More complete history, rolling-origin validation and explanatory data would be needed before making inventory commitments.'),
    ],
    [
        ('head','Power BI Desktop evidence and remaining checks'),
        ('text','The report has five visible pages and two hidden contextual pages, with 36 measure definitions and eight relationships. It passed an actual Desktop Full refresh and native DAX queries. The saved receipts match the computed data and all seven selected models, metrics and forecasts. The five actual main-page captures appear in the appendix.'),
        ('table',['Report page','Question and interaction'],[
            ['Executive Summary','Total registrations, growth, motorcycle share and one selected-series future forecast'],
            ['Data Quality','Before/after ETL counts, missing month, partial month and null/model-name audit'],
            ['Diagnostic Insight','Which brands lead within a vehicle type; Year, Brand, Type and Metric controls'],
            ['Predictive Results','Validation versus test metrics; selected method; actual/prediction line by one series'],
            ['Decision Recommendation','Hypothesis evidence, forecast limitations and error-driven review priorities'],
        ],[2.1,4.5]),
        ('table',['Native DAX acceptance','Observed result'],[
            ['Registrations and represented source records','5,007,659 and 35,805'],
            ['Fact rows and original raw records','5,712 and 68,398'],
            ['Brands types and complete months','421 brands, 16 types and 25 months'],
            ['January 2026 year on year','9.7903%'],
            ['Seven series','Selected method, validation/test metrics and future values match CSV'],
            ['Unfiltered overlapping future forecast','Blank; the one-series guard prevents unsafe summation'],
        ],[2.4,4.2]),
        ('text','The genuine field parameter uses NAMEOF bindings for Registrations, Source records and Registrations/source record. Brand hover tooltip and drillthrough pages are authored. These bindings and direct-page captures do not prove user-triggered switching, hovering or drillthrough. The visible Back label above the unchanged button proves its label configuration only.'),
        ('text','Final PBIX save/close/reopen and the three real feature interactions remain pending. The native security prompt requires user handling. Word content is updated but native pagination remains unverified. Full ETL reasons and hypothesis interpretations remain available in the report/CSVs when native table text requires horizontal scrolling.'),
    ],
    [
        ('head','Deployment decisions and limitations'),
        ('text','Use the report to compare category composition and investigate forecast errors before changing planning assumptions. Motorcycle dominance means that national totals should not stand in for passenger-car planning. The passenger-car decline hypothesis was rejected, so a recommendation to cut that category solely because of a presumed decline would contradict the observed data.'),
        ('text','Honda and motorcycle forecasts have better held-out explanatory fit than some other selected segments. Passenger-car and private-truck forecasts need closer review. A distributor should add its own stock, sales, prices and supplier lead times before converting registration forecasts into purchase quantities. The forecast supplies a measured demand proxy, not an order recommendation.'),
        ('head','Refresh procedure'),
        ('text','Preserve a new raw snapshot and its hash. Recheck monthly completeness, nulls, duplicates and definitions before extending the approved complete window. Recompute the source fact and features, reserve a chronological validation/test split, freeze model selection before examining test, rerun the notebook and output checks, then refresh Power BI. The current code deliberately asserts the supplied 25-month snapshot; a production refresh must change the explicit period configuration and revalidate it rather than silently treating partial data as complete.'),
        ('head','Reproducibility and responsibilities'),
        ('text','Use Python 3.11 with requirements.txt in a dedicated environment. Run term_project.py to compute exports, build_notebook.py to execute and save notebook outputs, verify_outputs.py for independent reconciliation/metric checks, and python -m pytest for six behavior tests. Python 3.11.9, pandas 2.3.3, NumPy 2.3.4 and scikit-learn 1.7.2 produced these results.'),
        ('text','Assign actual group responsibilities after members are known: business understanding and hypotheses, data preparation and audit, predictive modeling and validation, Power BI report and measures, and report/presentation demonstration. These are proposed work areas, not fabricated assignments to unnamed people.'),
        ('head','Required work before final submission'),
        ('text','Provide 2–5 real member names and student IDs, confirm topic/dataset uniqueness and receive instructor approval. Complete final PBIX save/reopen and user-triggered field-parameter switching, contextual tooltip, drillthrough and Back checks. Verify Word pagination in a native renderer and demonstrate the pipeline/report. Actual page captures and native baseline DAX checks are already included; they do not replace these remaining steps.'),
        ('head','References'),
        ('text','Department of Land Transport. First vehicle registrations by vehicle type, brand and model. DLT Data Catalog. '+m['source_url']),
        ('text','Course source: BI_Term_Project_2569.pdf, pages 1–2, including CRISP-DM, data, modeling, report and presentation requirements. Computational snapshot: DLT_First_Registration_Monthly_Original_Combined.csv, preserved SHA256 as recorded in verification.json.'),
    ],
]

appendix=[
    ('Executive Summary','The complete-period overview shows 5,007,659 registrations, 35,805 represented source records and 421 brands. This period includes January 2026, unlike the 2024–2025 composition hypotheses. The actual count values and suffixes fit in the latest capture.'),
    ('Data Quality','The original observed-source total is 10,276,823 registrations from 68,398 raw rows. The analysis window has 25 months; February 2026 contributes only 18 incomplete registrations and is excluded. ETL source/output counts are readable. Full long reasons are recorded in ETL_Counts.csv and the ETL section.'),
    ('Diagnostic Insight','The updated native capture visibly selects Registrations and shows Registrations by Brand, with HONDA 2,938,308 in 2024–2025. Motorcycles show 72.38%; passenger-car counts are 486,963 and 506,439. Isolated native copies with authored saved filters resolved Source records to HONDA 1,950 and Registrations/source record to 1,506.82, with matching changed captions and dropdown labels. These checks prove genuine parameter resolution under saved selections, not dropdown clicks. The canonical regression checks 96 files and allows only the Metric-slicer selection file to change; semantic model and CSV data remain unchanged.'),
    ('Predictive Results','The All/S01 series selects Gradient Boosting from validation. Native cards show test MAE 16,207.59 and February 2026 forecast 227,934. All five model rows are visible. Random Forest has lower test MAE but remains unselected. Native DAX matches every selected series method, metric and future forecast in the computed files.'),
    ('Decision Recommendation','All six hypothesis rows and their measured percentages are visible. H3 is Not supported descriptively. Improvement over the Naive total method is 11.00%. Full interpretation text is provided in the hypotheses section and HypothesisEvidence.csv when the native table needs horizontal scrolling.'),
]
for name,caption in appendix:
    blocks.append([
        ('head','Native Desktop page '+name),
        ('image','screenshots/'+name+'.png',6.6,6.6*1210/2602),
        ('text',caption),
        ('head','Evidence scope'),
        ('text','Actual native report-page capture from 11 October 2026, after the latest source formatting changes. This records a rendered page and visible values. It does not claim a user clicked a slicer, hovered a brand, entered drillthrough or used Back. Final PBIX save/reopen and advanced interaction acceptance remain pending.'),
        ('text','Native receipts: pbi-term-refresh-result.json, pbi-term-dax-totals-result.json and pbi-term-dax-forecast-result.json. Screenshot: '+name+'.png.'),
    ])

doc=Document();section=doc.sections[0]
section.page_width=Inches(8.5);section.page_height=Inches(11)
section.left_margin=section.right_margin=Inches(.75)
section.top_margin=section.bottom_margin=Inches(.65)
for name in ['Normal','Title','Heading 1','Heading 2']:
    style=doc.styles[name];style.font.name='Arial';style.font.color.rgb=RGBColor(0,0,0)
    style._element.get_or_add_rPr().rFonts.set(qn('w:ascii'),'Arial')
    style._element.get_or_add_rPr().rFonts.set(qn('w:hAnsi'),'Arial')
doc.styles['Normal'].font.size=Pt(11)
doc.styles['Normal'].paragraph_format.space_after=Pt(7)
doc.styles['Normal'].paragraph_format.line_spacing=1.1
doc.styles['Title'].font.size=Pt(23);doc.styles['Title'].paragraph_format.space_after=Pt(14)
doc.styles['Heading 1'].font.size=Pt(15);doc.styles['Heading 1'].paragraph_format.space_before=Pt(10)
doc.styles['Heading 1'].paragraph_format.space_after=Pt(7)
footer=section.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
run=footer.add_run('Page ');run.font.size=Pt(9)
field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)

font_path=Path('C:/Windows/Fonts/arial.ttf');bold_path=Path('C:/Windows/Fonts/arialbd.ttf')
pdfmetrics.registerFont(TTFont('ReportArial',str(font_path)))
pdfmetrics.registerFont(TTFont('ReportArialBold',str(bold_path)))
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='ReportBody',fontName='ReportArial',fontSize=10.5,leading=14.1,spaceAfter=8,wordWrap='CJK'))
styles.add(ParagraphStyle(name='ReportTitle',fontName='ReportArialBold',fontSize=23,leading=27,spaceAfter=16))
styles.add(ParagraphStyle(name='ReportHead',fontName='ReportArialBold',fontSize=14,leading=17,spaceBefore=10,spaceAfter=8))
styles.add(ParagraphStyle(name='ReportCell',fontName='ReportArial',fontSize=9.3,leading=12,spaceAfter=0,wordWrap='CJK'))
styles.add(ParagraphStyle(name='ReportCellHead',fontName='ReportArialBold',fontSize=9.3,leading=12,spaceAfter=0))
story=[]
def clean(value):return str(value).replace('\u2013','-').replace('\u2014','-').replace('\u2011','-')
def paragraph(value,style):return Paragraph(html.escape(clean(value)).replace('\n','<br/>'),styles[style])
for page_index,page in enumerate(blocks):
    if page_index:doc.add_page_break();story.append(PageBreak())
    for block in page:
        kind=block[0]
        if kind in ['title','head','text']:
            value=clean(block[1])
            doc.add_paragraph(value,style={'title':'Title','head':'Heading 1','text':'Normal'}[kind])
            story.append(paragraph(value,{'title':'ReportTitle','head':'ReportHead','text':'ReportBody'}[kind]))
        elif kind=='image':
            path=folder/block[1];doc.add_picture(str(path),width=Inches(block[2]))
            story.append(Image(str(path),width=block[2]*72,height=block[3]*72));story.append(Spacer(1,8))
        else:
            headers,rows,widths=block[1:]
            table=doc.add_table(rows=1,cols=len(headers));table.alignment=WD_TABLE_ALIGNMENT.CENTER
            table.autofit=False
            for cell,value,width in zip(table.rows[0].cells,headers,widths):cell.text=clean(value);cell.width=Inches(width)
            for row in rows:
                for cell,value,width in zip(table.add_row().cells,row,widths):cell.text=clean(value);cell.width=Inches(width)
            for i,row in enumerate(table.rows):
                row.height=None
                for j,cell in enumerate(row.cells):
                    cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
                    props=cell._tc.get_or_add_tcPr()
                    borders=OxmlElement('w:tcBorders')
                    for edge in ['top','left','bottom','right']:
                        element=OxmlElement('w:'+edge);element.set(qn('w:val'),'single');element.set(qn('w:sz'),'4');element.set(qn('w:color'),'D9D9D9');borders.append(element)
                    props.append(borders)
                    shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'E9EEF2' if i==0 else ('FFFFFF' if i%2 else 'F7F9FA'));props.append(shade)
                    margin=OxmlElement('w:tcMar')
                    for edge in ['top','left','bottom','right']:
                        element=OxmlElement('w:'+edge);element.set(qn('w:w'),'80');element.set(qn('w:type'),'dxa');margin.append(element)
                    props.append(margin)
                    for p in cell.paragraphs:
                        p.paragraph_format.space_after=Pt(4);p.paragraph_format.space_before=Pt(4)
                        p.paragraph_format.line_spacing=1.0
                        if j>0 and len(headers)>2:p.alignment=WD_ALIGN_PARAGRAPH.CENTER
                        for r in p.runs:r.font.size=Pt(9.5);r.bold=i==0
                if i==0:
                    repeat=OxmlElement('w:tblHeader');row._tr.get_or_add_trPr().append(repeat)
            doc.add_paragraph().paragraph_format.space_after=Pt(3)
            pdf_rows=[[paragraph(value,'ReportCellHead') for value in headers]]+[[paragraph(value,'ReportCell') for value in row] for row in rows]
            pdf_table=Table(pdf_rows,colWidths=[value*72 for value in widths],repeatRows=1,hAlign='LEFT')
            pdf_table.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.4,colors.HexColor('#D9D9D9')),
                ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E9EEF2')),
                ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F7F9FA')]),
                ('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),6),
                ('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
            story.append(pdf_table);story.append(Spacer(1,9))

docx_path=folder/'DLT_Brand_Type_Project_Report_Draft.docx'
pdf_path=folder/'DLT_Brand_Type_Project_Report_Draft.pdf'
doc.save(docx_path)
def footer_pdf(canvas,document):
    canvas.setFont('ReportArial',9);canvas.setFillColor(colors.HexColor('#606C76'))
    canvas.drawRightString(558,25,f'Page {document.page}')
    canvas.drawString(54,25,'DLT brand and vehicle type project proposal')
pdf=SimpleDocTemplate(str(pdf_path),pagesize=letter,leftMargin=54,rightMargin=54,topMargin=42,bottomMargin=42)
pdf.build(story,onFirstPage=footer_pdf,onLaterPages=footer_pdf)
print(docx_path);print(pdf_path)
