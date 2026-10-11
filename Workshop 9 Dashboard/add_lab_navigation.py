from pathlib import Path
import json,uuid
base=Path(r'D:\Github\BI 2026\Workshop 9 Dashboard\offline\Workshop9_Foreign_Tourists.Report\definition\pages')
for page in base.iterdir():
    if not page.is_dir():continue
    id='labpagenavigator'
    def prop(x):return {'expr':{'Literal':{'Value':('true' if x else 'false') if isinstance(x,bool) else str(x)+'L'}}}
    def obj(**ps):return [{'properties':{k:prop(v) for k,v in ps.items()}}]
    visual={'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.7.0/schema.json','name':id,'position':{'x':24,'y':1032,'z':99,'width':1548,'height':40,'tabOrder':99},'visual':{'visualType':'pageNavigator','objects':{'pages':obj(showHiddenPages=False,showTooltipPages=False,showByDefault=True),'layout':obj(orientation=0,cellPadding=4),'text':obj(fontSize=11)}}}
    out=page/'visuals'/id/'visual.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(visual,indent=2),encoding='utf-8')
print('Added native page navigation to six existing pages')
