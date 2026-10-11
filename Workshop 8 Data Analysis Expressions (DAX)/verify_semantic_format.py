from pathlib import Path
import json,datetime,shutil,sys
ROOT=Path(r'D:\Github\BI 2026')
projects=[('Workshop 8 Data Analysis Expressions (DAX)','Workshop8_DAX'),('Workshop 9 Dashboard','Workshop9_Foreign_Tourists')]
for folder,name in projects:
    p=ROOT/folder/'offline'/(name+'.SemanticModel');metadata=p/'definition.pbism';data=json.loads(metadata.read_text(encoding='utf-8'));version=data['version'];hasbim=(p/'model.bim').is_file();hastmdl=(p/'definition/model.tmdl').is_file()
    passed=(hasbim or hastmdl) if float(version)>=4 else hasbim
    result={'passed':passed,'version':version,'has_model_bim':hasbim,'has_TMDL_definition':hastmdl,'rule':'definition.pbism version1.0 requires TMSL model.bim; version4.0+ permits TMDL definition folder','source':'https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset#definitionpbism','timestamp':datetime.datetime.now().isoformat()}
    out=ROOT/folder/'analysis'/'semantic_format_validation.json'
    if '--fix' in sys.argv:
        backup=ROOT/folder/'analysis'/'backups';backup.mkdir(parents=True,exist_ok=True)
        shutil.copy2(metadata,backup/'definition.pbism.before-format-fix.json')
        (backup/'semantic_format_failed_check.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        assert hastmdl and not hasbim and version=='1.0',result
        data['version']='4.0';metadata.write_text(json.dumps(data,indent=2),encoding='utf-8')
        result.update({'passed':True,'version':'4.0','fix':'Only artifactformat version changed; schemaURI, TMDL model, report and data unchanged'})
    out.write_text(json.dumps(result,indent=2),encoding='utf-8');print(name, 'PASS' if result['passed'] else 'FAIL',result['version'])
    if not result['passed'] and '--expect-failure' not in sys.argv:sys.exit(1)
