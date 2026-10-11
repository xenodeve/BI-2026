"""Five-model Python reference on the fixed, group-safe holdout. Not native UI evidence."""
from pathlib import Path
import json,time,sys
import numpy as np,pandas as pd,sklearn
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.naive_bayes import GaussianNB
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier,GradientBoostingClassifier
from sklearn.metrics import accuracy_score,precision_score,recall_score,f1_score,roc_auc_score,average_precision_score,confusion_matrix
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent
NUM=['BMI','PhysicalHealth','MentalHealth','SleepTime']
def main():
 d=pd.read_csv(R/'heart_2020_modeling.csv');features=[c for c in d if c not in ['HeartDisease','SplitSet']];cat=[c for c in features if c not in NUM]
 train=d.SplitSet.eq('train');test=d.SplitSet.eq('test');Xtr=d.loc[train,features];Xte=d.loc[test,features];ytr=d.loc[train,'HeartDisease'].eq('Yes').astype(int);yte=d.loc[test,'HeartDisease'].eq('Yes').astype(int)
 split=json.loads((R/'split_verification.json').read_text());assert len(Xtr)==split['train_rows'] and len(Xte)==split['test_rows']
 assert set(d.HeartDisease)=={'No','Yes'} and set(d.SplitSet)=={'train','test'}
 assert 'HeartDisease' not in features and 'SplitSet' not in features
 def pre():return ColumnTransformer([('numeric',StandardScaler(),NUM),('categorical',OneHotEncoder(handle_unknown='ignore',sparse_output=False),cat)],remainder='drop')
 # Verify a synthetic held-out-only extreme/category cannot enter learned training parameters.
 trial=pre();trial.fit(Xtr);z=Xte.head(2).copy();z.iloc[0,z.columns.get_loc('BMI')]=99999;z.iloc[0,z.columns.get_loc('GenHealth')]='held-out-only'
 assert np.allclose(trial.named_transformers_['numeric'].mean_,Xtr[NUM].mean().to_numpy())
 assert 'held-out-only' not in trial.named_transformers_['categorical'].categories_[cat.index('GenHealth')]
 assert np.isfinite(trial.transform(z)).all()
 checks={'positive_class':'Yes','training_only_scaler_means_verified':True,'held_out_only_category_not_learned':True,'unseen_category_transforms_safely':True,'target_and_SplitSet_excluded':True,'group_holdout_verified':True}
 (R/'pretraining_verification.json').write_text(json.dumps(checks,indent=2),encoding='utf8');print('PRECHECK',json.dumps(checks),flush=True)
 models={'Naive Bayes':GaussianNB(var_smoothing=1e-9),'Logistic Regression':LogisticRegression(C=1,max_iter=1500,solver='lbfgs',class_weight='balanced',random_state=2026),'Decision Tree':DecisionTreeClassifier(max_depth=8,min_samples_leaf=30,class_weight='balanced',random_state=2026),'Random Forest':RandomForestClassifier(n_estimators=100,max_depth=12,min_samples_leaf=10,class_weight='balanced',n_jobs=4,random_state=2026),'Gradient Boosted Trees':GradientBoostingClassifier(n_estimators=60,max_depth=3,min_samples_leaf=20,learning_rate=.1,random_state=2026)}
 rows=[];parameters={};predictions=pd.DataFrame({'source_row':np.flatnonzero(test)+1,'HeartDisease':d.loc[test,'HeartDisease'].to_numpy()})
 for name,model in models.items():
  pipe=Pipeline([('preprocessing',pre()),('model',model)]);start=time.monotonic();pipe.fit(Xtr,ytr);prediction=pipe.predict(Xte);prob=pipe.predict_proba(Xte)[:,list(pipe.classes_).index(1)];tn,fp,fn,tp=confusion_matrix(yte,prediction,labels=[0,1]).ravel()
  r={'model':name,'engine':'Python scikit-learn reference','positive_class':'Yes','threshold':.5,'accuracy':accuracy_score(yte,prediction),'precision_yes':precision_score(yte,prediction,zero_division=0),'recall_yes':recall_score(yte,prediction),'f1_yes':f1_score(yte,prediction),'roc_auc':roc_auc_score(yte,prob),'average_precision':average_precision_score(yte,prob),'tn':int(tn),'fp':int(fp),'fn':int(fn),'tp':int(tp),'train_rows':len(Xtr),'test_rows':len(Xte),'elapsed_seconds':time.monotonic()-start};rows.append(r);parameters[name]=model.get_params();slug=name.lower().replace(' ','_');predictions[slug+'_prediction']=np.where(prediction,'Yes','No');predictions[slug+'_prob_yes']=prob
  assert tn+fp+fn+tp==len(Xte);assert np.allclose(pipe.named_steps['preprocessing'].named_transformers_['numeric'].mean_,Xtr[NUM].mean().to_numpy())
  print('MODEL',json.dumps(r),flush=True)
 result=pd.DataFrame(rows);result.to_csv(R/'model_comparison.csv',index=False,float_format='%.9f');predictions.to_csv(R/'reference_predictions.csv',index=False,float_format='%.9f')
 info={'split':split,'features':features,'numeric_features':NUM,'categorical_features':cat,'seed':2026,'sklearn_version':sklearn.__version__,'python_version':sys.version,'parameters':parameters,'preprocessing':'Fit numeric StandardScaler and category OneHotEncoder only on train; preserve Yes/No target; fixed group split','threshold':.5,'majority_no_accuracy':float((yte==0).mean()),'random_ranking_average_precision_baseline':float(yte.mean()),'native_run':False}
 (R/'reference_run.json').write_text(json.dumps(info,indent=2),encoding='utf8')
 fig,ax=plt.subplots(figsize=(10,4.8));result.set_index('model')[['precision_yes','recall_yes','f1_yes','average_precision']].plot.bar(ax=ax,color=['#4778ae','#ee7733','#227766','#7c64a4']);ax.set_ylim(0,1);ax.set_title('Python reference: group-safe holdout, positive HeartDisease=Yes');ax.set_ylabel('Score');ax.tick_params(axis='x',rotation=15);ax.legend(['Precision','Recall','F1','Average precision'],loc='upper left',bbox_to_anchor=(1,1));fig.tight_layout();fig.savefig(R/'reference_model_comparison.png',dpi=160);plt.close(fig)
 print('REFERENCE COMPLETE; native GUI verification pending',flush=True)
if __name__=='__main__':main()
