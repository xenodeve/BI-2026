"""Reproducible Python reference; not an AI Studio Run or TurboPrep artifact."""
from pathlib import Path
import csv, hashlib, json, shutil, time, sys
import numpy as np
import pandas as pd
import sklearn
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.naive_bayes import GaussianNB
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, average_precision_score, confusion_matrix
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent
SEED=2026
NUMERIC=['age','balance','day','campaign','pdays','previous']
CATEGORICAL=['job','marital','education','default','housing','loan','contact','month','poutcome','previously_contacted']
FEATURES=NUMERIC+CATEGORICAL
def prepare_features(raw):
    out=raw.drop(columns=['duration']).copy()
    out['previously_contacted']=np.where(out['pdays']==-1,'no','yes')
    return out
def make_preprocessor():
    return ColumnTransformer([
        ('numeric',StandardScaler(),NUMERIC),
        ('categorical',OneHotEncoder(handle_unknown='ignore',sparse_output=False),CATEGORICAL)
    ],remainder='drop')
def verify_before_training(raw,prepared,train_ids,test_ids):
    assert len(raw)==45211 and raw.shape[1]==17
    assert set(raw.y)=={'yes','no'} and not raw.isna().any().any()
    assert 'duration' not in FEATURES and 'y' not in FEATURES
    assert set(train_ids).isdisjoint(test_ids) and len(train_ids)+len(test_ids)==len(raw)
    assert abs((raw.iloc[train_ids].y=='yes').mean()-(raw.iloc[test_ids].y=='yes').mean())<.001
    # Synthetic separation check: a held-out extreme must not alter training means/categories.
    train=prepared.iloc[train_ids].copy();test=prepared.iloc[test_ids[:2]].copy()
    test.loc[test.index[0],'age']=99999;test.loc[test.index[0],'job']='unseen-test-only'
    pre=make_preprocessor();pre.fit(train[FEATURES]);expected=train[NUMERIC].mean().to_numpy()
    assert np.allclose(pre.named_transformers_['numeric'].mean_,expected)
    assert 'unseen-test-only' not in pre.named_transformers_['categorical'].categories_[0]
    transformed=pre.transform(test[FEATURES]);assert np.isfinite(transformed).all()
    assert all(not x.startswith(('duration','y')) for x in pre.get_feature_names_out())
    return {'label_values':['no','yes'],'positive_class':'yes','source_rows':len(raw),'train_rows':len(train_ids),'test_rows':len(test_ids),'train_test_disjoint':True,'duration_excluded':True,'target_excluded_from_features':True,'training_only_preprocessing_test':True,'unseen_category_test':True}
def quality(raw,prepared):
    q={'source_rows':len(raw),'source_columns':len(raw.columns),'positive':int((raw.y=='yes').sum()),'negative':int((raw.y=='no').sum()),'positive_rate':float((raw.y=='yes').mean()),'empty_cells':int(raw.isna().sum().sum()),'exact_duplicate_rows':int(raw.duplicated().sum()),'duplicate_predictor_rows_after_duration_removal':int(prepared[FEATURES].duplicated().sum()),'unknown_counts':{c:int((raw[c]=='unknown').sum()) for c in raw.select_dtypes('object').columns if (raw[c]=='unknown').any()},'negative_balance_rows':int((raw.balance<0).sum()),'pdays_minus_one':int((raw.pdays==-1).sum()),'previous_zero':int((raw.previous==0).sum()),'numeric':{}}
    for c in raw.select_dtypes('number').columns:
        s=raw[c];q1,q3=s.quantile([.25,.75]);lo=q1-1.5*(q3-q1);hi=q3+1.5*(q3-q1)
        q['numeric'][c]={'min':int(s.min()),'max':int(s.max()),'mean':float(s.mean()),'median':float(s.median()),'q1':float(q1),'q3':float(q3),'iqr_low':float(lo),'iqr_high':float(hi),'iqr_flag_count':int(((s<lo)|(s>hi)).sum())}
    return q
def main():
    raw_path=ROOT/'data/bank-full.csv';raw=pd.read_csv(raw_path,sep=';')
    original_hash=hashlib.sha256(raw_path.read_bytes()).hexdigest()
    shutil.copy2(raw_path,ROOT/'bank-full.csv')
    prepared=prepare_features(raw)
    prepared.to_csv(ROOT/'bank-clean.csv',sep=';',index=False,quoting=csv.QUOTE_MINIMAL)
    ids=np.arange(len(raw));train_ids,test_ids=train_test_split(ids,test_size=.30,stratify=raw.y,random_state=SEED)
    checks=verify_before_training(raw,prepared,train_ids,test_ids)
    (ROOT/'verification.json').write_text(json.dumps(checks,indent=2),encoding='utf8')
    print('PRECHECK',json.dumps(checks),flush=True)
    assign=pd.DataFrame({'source_row':ids+1,'split':np.where(np.isin(ids,train_ids),'train','test')})
    assign.to_csv(ROOT/'split_assignment.csv',index=False)
    q=quality(raw,prepared);q['raw_sha256']=original_hash
    (ROOT/'data_quality.json').write_text(json.dumps(q,indent=2),encoding='utf8')
    pd.DataFrame(q['numeric']).T.to_csv(ROOT/'numeric_quality.csv',index_label='attribute')
    raw.y.value_counts().rename_axis('label').reset_index(name='count').to_csv(ROOT/'target_distribution.csv',index=False)
    models={
        'Naive Bayes':GaussianNB(var_smoothing=1e-9),
        'Logistic Regression':LogisticRegression(C=1.0,max_iter=2000,solver='lbfgs',class_weight='balanced',random_state=SEED),
        'Decision Tree':DecisionTreeClassifier(max_depth=8,min_samples_leaf=20,class_weight='balanced',random_state=SEED),
        'Random Forest':RandomForestClassifier(n_estimators=200,max_depth=12,min_samples_leaf=5,class_weight='balanced',n_jobs=4,random_state=SEED),
        'Gradient Boosted Trees':GradientBoostingClassifier(n_estimators=150,learning_rate=.1,max_depth=3,min_samples_leaf=10,random_state=SEED),
    }
    Xtr=prepared.iloc[train_ids][FEATURES];Xte=prepared.iloc[test_ids][FEATURES]
    ytr=(raw.iloc[train_ids].y=='yes').astype(int);yte=(raw.iloc[test_ids].y=='yes').astype(int)
    rows=[];predictions=pd.DataFrame({'source_row':test_ids+1,'actual_y':raw.iloc[test_ids].y.to_numpy()})
    model_details={}
    for name,model in models.items():
        pipe=Pipeline([('preprocessing',make_preprocessor()),('model',model)])
        started=time.monotonic();pipe.fit(Xtr,ytr);pred=pipe.predict(Xte);prob=pipe.predict_proba(Xte)[:,list(pipe.classes_).index(1)]
        tn,fp,fn,tp=confusion_matrix(yte,pred,labels=[0,1]).ravel()
        r={'model':name,'engine':'Python scikit-learn reference','positive_class':'yes','threshold':.5,'accuracy':accuracy_score(yte,pred),'precision_yes':precision_score(yte,pred,zero_division=0),'recall_yes':recall_score(yte,pred),'f1_yes':f1_score(yte,pred),'roc_auc':roc_auc_score(yte,prob),'average_precision':average_precision_score(yte,prob),'tn':int(tn),'fp':int(fp),'fn':int(fn),'tp':int(tp),'train_rows':len(train_ids),'test_rows':len(test_ids),'elapsed_seconds':time.monotonic()-started}
        rows.append(r);slug=name.lower().replace(' ','_');predictions[slug+'_pred']=np.where(pred==1,'yes','no');predictions[slug+'_prob_yes']=prob
        assert sum([tn,fp,fn,tp])==len(test_ids)
        assert np.allclose(pipe.named_steps['preprocessing'].named_transformers_['numeric'].mean_,Xtr[NUMERIC].mean().to_numpy())
        model_details[name]=model.get_params()
        print('MODEL',json.dumps(r),flush=True)
    result=pd.DataFrame(rows);result.to_csv(ROOT/'model_comparison.csv',index=False,float_format='%.9f');predictions.to_csv(ROOT/'reference_predictions.csv',index=False,float_format='%.9f')
    meta={'seed':SEED,'split':'shared stratified random 70/30 by source row, scikit-learn train_test_split','sklearn_version':sklearn.__version__,'python_version':sys.version,'features':FEATURES,'numeric_features':NUMERIC,'categorical_features':CATEGORICAL,'excluded':['duration'],'preprocessing':'Training-only StandardScaler and OneHotEncoder; explicit unknown category retained; new test categories encoded as all zeros','parameters':model_details,'test_positive':int(yte.sum()),'test_negative':int((yte==0).sum()),'majority_no_accuracy':float((yte==0).mean()),'random_rank_average_precision_baseline':float(yte.mean()),'raw_sha256':original_hash,'native_ai_studio_run':False}
    (ROOT/'reference_run.json').write_text(json.dumps(meta,indent=2),encoding='utf8')
    fig,ax=plt.subplots(figsize=(10,4.8));plot=result.set_index('model')[['precision_yes','recall_yes','f1_yes','average_precision']];plot.plot.bar(ax=ax,color=['#4778ae','#ee7733','#227766','#7c64a4']);ax.set_ylim(0,1);ax.set_ylabel('Positive class: yes');ax.set_title('Python reference: shared 70/30 holdout, duration excluded');ax.tick_params(axis='x',rotation=15);ax.legend(['Precision','Recall','F1','Average precision'],loc='upper left',bbox_to_anchor=(1,1));fig.tight_layout();fig.savefig(ROOT/'reference_model_comparison.png',dpi=160);plt.close(fig)
    assert hashlib.sha256(raw_path.read_bytes()).hexdigest()==original_hash
    assert hashlib.sha256((ROOT/'bank-full.csv').read_bytes()).hexdigest()==original_hash
    assert len(pd.read_csv(ROOT/'bank-clean.csv',sep=';'))==45211
    print('COMPLETE raw preserved; reference results are not native AI Studio evidence',flush=True)
if __name__=='__main__':main()
