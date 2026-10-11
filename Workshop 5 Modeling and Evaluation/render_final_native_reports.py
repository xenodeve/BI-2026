from pathlib import Path
import json,hashlib
import pypdfium2 as pdfium
from pypdf import PdfReader
W5=Path(__file__).resolve().parent;ROOT=W5.parent
jobs=[(ROOT/'Workshop 4 การจัดเตรียมข้อมูล (Data Preparation)','Workshop4_Data_Preparation_Report.pdf'),(W5,'Workshop5_Modeling_Evaluation_Report.pdf'),(ROOT/'BI Mini Project 1','MiniProject1_Report.pdf')]
result=[]
for folder,name in jobs:
 p=folder/name;qa=folder/'report-qa'/'native-batch';qa.mkdir(parents=True,exist_ok=True)
 doc=pdfium.PdfDocument(str(p));reader=PdfReader(p);pages=[]
 for i in range(len(doc)):
  out=qa/f'page-{i+1:02d}.png';page=doc[i];page.render(scale=1.55).to_pil().save(out)
  text=reader.pages[i].extract_text();assert len(text.strip())>50,(name,i)
  pages.append({'page':i+1,'png':str(out),'text_characters':len(text),'png_sha256':hashlib.sha256(out.read_bytes()).hexdigest()})
 result.append({'pdf':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'page_count':len(doc),'all_pages_rendered':True,'pages':pages})
(W5/'native_pdf_render_verification.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps([{'pdf':v['pdf'],'page_count':v['page_count']} for v in result],indent=2))
