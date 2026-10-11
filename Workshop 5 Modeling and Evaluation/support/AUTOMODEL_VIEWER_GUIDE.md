# WS5 native Auto Model input handoff

Open `Workshop5_AutoModel_Data_Viewer.rmp` as a local process, keeping `WS5_AutoModel_Heart_Native_Prepared.csv` beside it. Import/Run is performed by root in the real app; this preparation task did not operate the UI or claim a native viewer run.

The data copy is byte-identical to the actual WS4 native output (SHA256 `fafcc2ff71daf147d0ab3968887dd74330c645e3f6a2341c5a217e52b99658af`): 319,795 rows, 19 attributes. HeartDisease No 292,422 / Yes 27,373. All 19 roles are regular attributes in Result 1; no label is assigned, no attribute selected out, and no preparation, sampling, training or writing operator is present.

Actual numeric columns are **four**, not six: BMI, PhysicalHealth, MentalHealth, SleepTime. They remain real. HeartDisease is binominal No/Yes; AnyUnhealthyDays is polynominal Yes/No. AgeCategory stays categorical with its original text categories. Typed metadata preserves the existing native-validated reader schema and original column order; it does not invent numerical conversions.

Root's intended real-app sequence:

1. Run the viewer and confirm Result 1 has 319,795 rows and 19 regular attributes, with no SplitSet or SourceRow.
2. Start **Auto Model** from the resulting dataset. Select **Predict**, target **HeartDisease**, and positive class **Yes**.
3. Check all **18 remaining attributes** are inputs, including AnyUnhealthyDays; target HeartDisease must be excluded from inputs. Retain the original categorical meanings.
4. Choose **Naive Bayes, Logistic Regression, Decision Tree, Random Forest, Gradient Boosted Trees**. Five is the user's approved working scope, not a teacher-confirmed WS5 count.
5. Record the real Auto Model setup, run and export/save the actual generated process and model results separately from the existing direct-learner baseline. Do not overwrite existing `native_<CODE>.csv`, `native_model_comparison.csv`, baseline RMP or report.

BI07 PDF 10 / slide 38 teaches the six-step Auto Model workflow; PDF 6 / slide 24 describes its default 60/40 split and seven testing parts. Actual native Auto Model results/validation behavior must be reported as observed. The prior grouped 70/30 direct-learner benchmark remains a separate experiment; it must not be relabeled Auto Model. The preserved anonymous identical response profiles may cross Auto Model's default random split, so do not carry over the prior group-disjointness claim to this new run.

The installed Auto Model templates previously audited for Mini2 contain model-dependent initial sampling caps (RF/GBT 125,000 versus higher caps for NB/LR/DT). Therefore full input row count does not establish equal per-model training/test counts in this new default run. Inspect the actual exported WS5 processes and native counts; do not copy the prior 95,940-row test count or claim a common test from the viewer alone.

File checks and types: `automodel_viewer_verification.json`. Source WS4 output and all pre-existing WS5 files were hash-checked unchanged.
