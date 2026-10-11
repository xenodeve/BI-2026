from pathlib import Path
import xml.etree.ElementTree as E,json
R=Path(__file__).resolve().parent
SOURCE=R.parents[1]/'Native_AI_Repository/MiniProject2_AutoModel_9Models'
MODELS=['Naive Bayes','Generalized Linear Model','Logistic Regression','Fast Large Margin','Deep Learning','Decision Tree','Random Forest','Gradient Boosted Trees','Support Vector Machine']
all_data={}
def walk(node,path='',result=None):
 result=[] if result is None else result
 for child in node:
  if child.tag=='operator':
   cur=path+'/'+child.attrib.get('name','');pars={p.attrib['key']:p.attrib['value'] for p in child.findall('parameter')}
   result.append({'path':cur,'class':child.attrib.get('class'),'activated':child.attrib.get('activated'),'params':pars})
   walk(child,cur,result)
  elif child.tag=='process':walk(child,path,result)
 return result
for name in MODELS:
 p=SOURCE/name/'process.rmp';tree=E.parse(p);nodes=walk(tree.getroot());all_data[name]=nodes
 top=tree.find('.//operator/process')
 print('\nMODEL',name,'TOP',[{'name':o.attrib['name'],'class':o.attrib['class'],'inputs':[(c.attrib.get('from_op'),c.attrib.get('from_port'),c.attrib.get('to_port')) for c in top.findall('connect') if c.attrib.get('to_op')==o.attrib['name']]} for o in top.findall('operator')])
 for n in nodes:
  if n['class'] in ['sample','sample_stratified','split_data','blending:split_data','store','retrieve','remember','recall','model_simulator:robust_performance_average','model_simulator:generate_batch','model_simulator:automodel_performance','performance_binominal_classification']:
   print(json.dumps(n))
(R/'native_template_audit.json').write_text(json.dumps(all_data,indent=2),encoding='utf8')
