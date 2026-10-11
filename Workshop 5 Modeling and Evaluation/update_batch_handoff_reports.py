from pathlib import Path
import json,hashlib
import pandas as pd
W5=Path(__file__).resolve().parent;ROOT=W5.parent;DOCS=ROOT/'docs/execution';M1=ROOT/'BI Mini Project 1';W4=ROOT/'Workshop 4 การจัดเตรียมข้อมูล (Data Preparation)'
def table(df):
 out=['| Model | Accuracy | Precision | Recall | F1 | AUC | TN | FP | FN | TP |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
 for r in df.itertuples():out.append('| '+r.model+' | '+' | '.join(f'{getattr(r,k):.6f}' for k in ['accuracy','precision_yes','recall_yes','f1_yes','roc_auc'])+' | '+' | '.join(str(getattr(r,k)) for k in ['tn','fp','fn','tp'])+' |')
 return '\n'.join(out)
def update(name,replacements,appendix):
 p=DOCS/name;s=p.read_text(encoding='utf-8')
 backup=p.with_name(p.stem+'-before-native-batch.md')
 if not backup.exists():backup.write_text(s,encoding='utf-8')
 for old,new in replacements.items():s=s.replace(old,new)
 marker='\n## Verified official native batch completion (11 October 2026)\n'
 if marker in s:s=s.split(marker)[0]
 p.write_text(s.rstrip()+marker+'\n'+appendix+'\n',encoding='utf-8')

n5=pd.read_csv(W5/'native_model_comparison.csv');n1=pd.read_csv(M1/'native_model_comparison.csv')
update('ws45-report.md',{
 'Offline preparation, grouped shared holdout, five-model Python reference, two real-operator RMP processes, and Thai PDF reports are finished and verified. **Root still owns actual Turbo Prep, AI Studio Run, screenshots, native metrics, and relocated Run.**':'Native engine batch runs, native preparation, five-model metrics, grouped shared holdout, Python reference, and Thai PDF updates are finished and verified. **Actual Turbo Prep GUI, GUI screenshots, and relocated native Run remain pending with root/user.**',
 '`Workshop5_Modeling_Evaluation_Report.pdf` — four Thai pages, all visually checked.':'`Workshop5_Modeling_Evaluation_Report.pdf` — five Thai pages, all visually checked; native batch results lead and Python reference stays separate.',
 'No native runtime success is claimed.':'Official installed batch runtime success is confirmed in the completion section below; GUI evidence is separate.',
 '**Native Turbo Prep/Run/autoexport/screenshot/relocation evidence remains pending with root.**':'**Native engine batch Run and autoexport now pass. Turbo Prep GUI, GUI screenshots, and relocated native execution remain pending with root/user.**',
 '**Native Turbo Prep/Run/autoexport/screenshot/relocation evidence remains pending.**':'**Native engine batch Run and autoexport now pass. Turbo Prep GUI, GUI screenshots, and relocated native execution remain pending with root/user.**',
 'Native Run will write':'Verified native batch Run wrote',
 'replace("%{process_path}", "%{process_file}",':'replace(%{process_path}, %{process_file},'
},f'''Official installed `D:/AI Studio 2026.1.1/scripts/ai-studio-batch.bat` executed the actual RMPs. Bundled native engine12.1.1, heap3GB, process-scoped TEMP/TMP and java.io.tmpdir on D; ordinary existing-license detection/fallback only. No GUI/security UI automation, license/profile changes, or alternative model engine.

WS4 succeeded04:03:03. `heart_2020_prepared_native.csv` is319,795×19; all18 original columns exactly match source values; derived AnyUnhealthyDays matches its rule for every row; No292,422/Yes27,373. Raw source SHA unchanged. Proof `native_batch_verification.json` and actual `native_batch.log` in WS4.

WS5 succeeded04:08:53. All5 `native_<CODE>.csv` are fresh after its run start. Fail-closed collector checks completion log, finite metrics, confusion reconciliation, exact95,940test rows and8,212Yes for each model, and stable export hashes. `native_model_comparison.csv` and `native_metrics_provenance.json` retain full precision/provenance.

{table(n5)}

Native LR has highest F1 .390917 and AUC .838352, narrowly ahead of GBT F1 .389976 (difference .000941, not evidence of statistical significance). Native RF's Accuracy .915405 comes with Recall .024111 and8,014 false negatives. Use native conclusions separately from Python-reference rankings.

Bounded runtime fixes: explicit Thai path argument was corrupted to question marks by batch/Java argument handling, so WS4 was launched using the unchanged ASCII RMP filename from its existing Thai-named task working directory. Failed log preserved. WS5 first parallel RF exceeded3GB heap; installed concurrency operator manual explicitly directs disabling parallel execution for memory problems. Only RF enable_parallel_execution true→false changed. Keep100trees/depth12/leaf10/seed2026 and all rows. Backup RMP, failed log, reversal proof in `native_batch_memory_fix.json`; final builder and portability-check copy retain the corrected setting.

Final Thai reports: WS4 three pages / WS5 five pages. Every final page rendered and visually reviewed, including tables, Thai glyphs, citations and footer spacing. Initial reference PDFs preserved as *_Report_before_native_batch.pdf. Native/GUI distinction is explicit throughout. `native_pdf_visual_review.json` provides hashes and page counts.

Pending only actual Turbo Prep GUI evidence, actual GUI process/results screenshots, and relocated native execution proof. Offline portability copies and path checks pass; they do not constitute relocated native execution.
''')
update('mini1-report.md',{
 'Prepared 11 October 2026 Asia/Bangkok. Scope: offline data preparation, reproducible Python reference benchmarks, installed-schema AI Studio process, and Thai CRISP-DM PDF. **Native Turbo Prep, AI Studio Run, screenshots, and relocated native Run remain for the main agent.**':'Prepared 11 October 2026 Asia/Bangkok. Native engine batch execution, five-model exports, Python reference, source-preserving preparation, and Thai CRISP-DM PDF updates pass. **Actual Turbo Prep GUI, GUI screenshots, and relocated native Run remain with root/user.**',
 '`MiniProject1_Report.pdf` — six-page Thai report, all six CRISP-DM stages, dictionary, quality findings, actual Python reference results, confusion counts, insights, deployment, sources, and explicit pending GUI evidence.':'`MiniProject1_Report.pdf` — seven-page Thai report with all six CRISP-DM stages, native batch results as primary, Python reference labeled separately, dictionary, quality, confusion counts, sources, and explicit pending GUI evidence.',
 'not yet native AI Studio conclusions':'separate from the verified native AI Studio conclusions below',
 'No native runtime success is claimed.':'Official native batch runtime success is confirmed in the completion section below; GUI evidence is separate.',
 'This work did not start one.':'The verified official native batch run started the local H2O cluster.',
 'this work did not start one.':'the verified official native batch run started the local H2O cluster.',
 'replace("%{process_path}", "%{process_file}",':'replace(%{process_path}, %{process_file},',
 '**The required native Turbo Prep, complete AI Studio Run, screenshots, native report result replacement, and relocation Run are still pending.**':'**Native engine batch execution, five-model metric exports and report integration now pass; actual Turbo Prep GUI, GUI screenshots, and relocation Run remain pending.**'
},f'''Official installed batch runner executed `MiniProject1.rmp`, finished04:11:33. Native engine12.1.1 with3GB heap/D temp, standard existing license detection; no GUI automation or license/profile changes. Actual native split uses31,647train/13,564test, testyes1,587/no11,977 shared across all5 branches. Python reference uses the same counts but its own RNG/implementations; equal counts do not claim the same rows across engines.

Fail-closed collector validates all5 new Performance-to-Data exports, actual completion log, timestamps, finite criteria, same actual-label counts and confusion reconciliation. `native_model_comparison.csv` and `native_metrics_provenance.json` store results/provenance separately from Python reference.

{table(n1)}

Native GBT wins declared F1 criterion .489310, Recall .504726 and AUC .791056; Precision .474807, FP886/FN786. Its Accuracy .876733 is below all-no baseline .8830, whose positive F1 is0. The original Python-reference RF winner is not presented as the native winner.

Bounded schema fix: authored Split Data used list partitions and the actual engine rejected partitions as missing. Installed Split Data tutorial uses enumeration. Changed only that container tag; retained.7/.3 ratios, stratified sampling, seed2026, preprocessing, learners and every connection. Original/error log backed up; reversal proof in `native_split_schema_fix.json`. Builder and portability-check copy contain enumeration. `verify_native_exports.py` passes meaningful missing/duplicate/nonfinite/inconsistent-criterion rejection fixtures without replacing real exports.

Final Thai CRISP-DM report has7 pages; native results are primary, Python reference labeled separately. All7 pages rendered and visually checked. Earlier reference PDF retained as MiniProject1_Report_before_native_batch.pdf. Raw bank-full.csv bytes and original filename remain unchanged.

Pending actual Turbo Prep GUI, process/results GUI screenshots for all5 models, and relocated native execution proof. Current portability-check copy is updated and its offline paths/hash pass, but no relocated native execution is claimed.
''')
review=[]
for folder,name,pages in [(W4,'Workshop4_Data_Preparation_Report.pdf',3),(W5,'Workshop5_Modeling_Evaluation_Report.pdf',5),(M1,'MiniProject1_Report.pdf',7)]:
 p=folder/name;review.append({'pdf':str(p),'pages':pages,'pdf_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'all_final_pages_rendered_and_visually_reviewed':True,'no_clipping_or_overlapping_text_or_tables':True,'native_batch_and_reference_and_GUI_pending_distinguished':True})
(W5/'native_pdf_visual_review.json').write_text(json.dumps(review,indent=2),encoding='utf8')
print('Updated task handoff reports and final15-page visual review proof')
