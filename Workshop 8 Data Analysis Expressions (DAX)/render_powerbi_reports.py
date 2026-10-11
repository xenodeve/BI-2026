import pypdfium2 as pdfium
from pathlib import Path
from PIL import Image,ImageDraw
root=Path(r'D:\Github\BI 2026')
for folder,name in [('Workshop 8 Data Analysis Expressions (DAX)','Workshop8_Report.pdf'),('Workshop 9 Dashboard','Workshop9_Report.pdf')]:
    p=root/folder;out=p/'analysis'/'report_previews';out.mkdir(parents=True,exist_ok=True)
    pdf=pdfium.PdfDocument(p/name);thumbs=[]
    for i in range(len(pdf)):
        im=pdf[i].render(scale=1.4).to_pil();im.save(out/f'page_{i+1:02d}.png')
        im.thumbnail((238,337));tile=Image.new('RGB',(250,360),'white');tile.paste(im,((250-im.width)//2,18));ImageDraw.Draw(tile).text((6,2),str(i+1),fill='black');thumbs.append(tile)
    sheet=Image.new('RGB',(1000,360*((len(thumbs)+3)//4)),'#e5e7eb')
    for i,im in enumerate(thumbs):sheet.paste(im,((i%4)*250,(i//4)*360))
    sheet.save(out/'contact.png');print(name,len(pdf),'pages')
