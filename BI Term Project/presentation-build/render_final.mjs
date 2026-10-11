import fs from 'node:fs/promises';
import path from 'node:path';
import {FileBlob,PresentationFile} from '@oai/artifact-tool';
const file=path.resolve(import.meta.dirname,'../presentation/DLT_Brand_Type_Project_Proposal.pptx');
const presentation=await PresentationFile.importPptx(await FileBlob.load(file));
const previews=path.join(import.meta.dirname,'final-previews');await fs.mkdir(previews,{recursive:true});
for(const [index,slide] of presentation.slides.items.entries()){
  const png=await presentation.export({slide,format:'png',scale:1});
  await fs.writeFile(path.join(previews,`slide-${String(index+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));
}
console.log(`Final PPTX imported and rendered ${presentation.slides.items.length} slides`);
