import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {Presentation, PresentationFile, FileBlob} from '@oai/artifact-tool';

const build = path.dirname(fileURLToPath(import.meta.url));
const workspaceDir = path.resolve(build, '..');
const repo = path.resolve(workspaceDir, '../../..');
const skill = 'C:/Users/abhir/.codex/plugins/cache/openai-primary-runtime/presentations/26.904.11930/skills/presentations';
const python = 'C:/Users/abhir/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe';
process.env.RUNTIME_NODE_MODULES = 'C:/Users/abhir/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const {resolvePresentationFont, applyPresentationChartFont, finalizePresentation} = await import(pathToFileURL(path.join(skill, 'container_tools/artifact_tool_utils.mjs')).href);
const family = resolvePresentationFont();
const sourceCommit = '7db77bd8d38aa5f23dc4180e341de415d6b99296';
const github = 'https://github.com/dlmastery/simple-coding-harness/blob/' + sourceCommit + '/';
const storyboard = await fs.readFile(path.join(build, 'STORYBOARD-SOURCE.md'), 'utf8');
const assets = [];
const usedSources = new Map();
async function bytes(relative) {
  const raw = await fs.readFile(path.join(repo, relative));
  usedSources.set(relative, {path: relative, bytes: raw.length, sha256: createHash('sha256').update(raw).digest('hex')});
  return raw;
}
function csv(raw) {
  const rows = [], row = []; let value = '', quoted = false;
  for (let i=0; i<raw.length; i++) {
    const c=raw[i];
    if(c==='"') {if(quoted && raw[i+1]==='"'){value+='"';i++;}else quoted=!quoted;}
    else if(c===','&&!quoted){row.push(value);value='';}
    else if(c==='\n'&&!quoted){row.push(value.replace(/\r$/, ''));rows.push(row.splice(0));value='';}
    else value+=c;
  }
  if(value||row.length){row.push(value.replace(/\r$/, ''));rows.push(row);}
  const header=rows.shift();return rows.map(r=>Object.fromEntries(header.map((h,i)=>[h,r[i]])));
}
const sources = [
 ['rsi/README.md','rsi/09_recursive_self_improvement/step_01_three_objects/README.md'],
 ['rsi/START-HERE.md','rsi/COURSE-MAP.md','rsi/TEACHING-ROADMAP.md'],
 ['rsi/00_start_here/README.md','how-did-i-generate-it/rsi/validation/BENCHMARK-REPAIR-PROTOCOL.md'],
 ['rsi/00_start_here/step_01_meet_the_task/README.md'],
 ['rsi/08_measuring_improvement/README.md','rsi/evidence/2026-09-22/discovery-final/README.md'],
 ['rsi/00_start_here/step_03_one_attempt/README.md'],
 ['rsi/02_loop_engineering/step_01_why_repeat/README.md','rsi/skills/run-ml-experiment/SKILL.md'],
 ['rsi/01_process_without_loops/README.md','rsi/skills/README.md'],
 ['rsi/02_loop_engineering/README.md'],
 ['rsi/03_graph_engineering/README.md','rsi/evidence/2026-09-22/graph-reconciliation/README.md'],
 ['rsi/04_ontology_engineering/README.md'],
 ['rsi/05_system_intelligence/README.md'],
 ['rsi/06_meta_harness_engineering/README.md','rsi/evidence/2026-09-21/capstone-harness/README.md'],
 ['rsi/07_understanding_self_star/README.md','rsi/GLOSSARY.md'],
 ['rsi/07_understanding_self_star/step_02_reflection/README.md'],
 ['rsi/07_understanding_self_star/step_05_organization/README.md','rsi/07_understanding_self_star/step_06_emergence/README.md'],
 ['rsi/09_recursive_self_improvement/step_01_three_objects/README.md','rsi/skills/improve-research-skill/SKILL.md'],
 ['rsi/09_recursive_self_improvement/step_04_inherit/README.md'],
 ['how-did-i-generate-it/rsi/validation/RSI-RESULTS-DIAGNOSIS-2026-09-22.md','rsi/RESULTS-GUIDE.md'],
 ['rsi/evidence/2026-09-22/discovery-final/README.md','rsi/08_measuring_improvement/step_03_cost/README.md'],
 ['how-did-i-generate-it/rsi/research/2026-09-22-BENCHMARK-SCALE.md'],
 ['rsi/10_research_studio/README.md','rsi/research/README.md'],
 ['rsi/10_research_studio/02_dream_rsi/step_08_replay/README.md','rsi/evidence/2026-09-22/online-discovery/README.md'],
 ['rsi/evidence/2026-09-22/online-discovery/README.md'],
 ['rsi/10_research_studio/01_memory_and_exploration/step_04_actor_memory/README.md'],
 ['rsi/10_research_studio/01_memory_and_exploration/step_06_working_and_experience/README.md'],
 ['rsi/10_research_studio/04_aide2/step_14_outer_research/README.md','rsi/evidence/2026-09-22/nested-research-evaluation/README.md'],
 ['rsi/10_research_studio/04_aide2/step_15_ignition/README.md'],
 ['rsi/10_research_studio/05_meta_skill_evolution/step_17_meta_skills/README.md'],
 ['rsi/10_research_studio/06_scientist_two/README.md','rsi/evidence/2026-09-21/scientist-labs/README.md'],
 ['rsi/10_research_studio/07_sciencebuddy/README.md'],
 ['rsi/evidence/2026-09-22/discovery-final/README.md','rsi/evidence/2026-09-22/discovery-final/RESULTS.csv','rsi/evidence/2026-09-22/discovery-final/PAIRED.csv'],
 ['rsi/evidence/2026-09-22/nested-research-evaluation/README.md','rsi/evidence/2026-09-22/nested-research-evaluation/CONTRASTS.csv'],
 ['how-did-i-generate-it/rsi/validation/REPAIRED-METHOD-REQUIREMENTS.md','rsi/RESULTS-GUIDE.md'],
 ['rsi/11_capstones/README.md'],
 ['rsi/compute/README.md','rsi/skills/scale-experiment/SKILL.md'],
 ['rsi/GLOSSARY.md','rsi/11_capstones/step_05_teach_back/README.md','rsi/TEACHING-ROADMAP.md']
];
const matches = [...storyboard.matchAll(/^## (\d{2}) · (.+)$/gm)];
if(matches.length!==37)throw new Error('Expected the maintained 37-slide route');
const slideSpecs=[];
for(let i=0;i<matches.length;i++){
  const start=matches[i], end=matches[i+1]?.index ?? storyboard.indexOf('## Production checks');
  const section=storyboard.slice(start.index,end);
  const visual=section.match(/Visual: \x60([^\x60]+\.png)\x60/);
  const point=section.match(/On slide: ([\s\S]*?)(?:\n\n|$)/)?.[1].replace(/\s+/g,' ').trim();
  const noteAt=section.indexOf('Speaker notes:');
  if(noteAt<0 || !point)throw new Error('Missing content on slide '+(i+1));
  let notes=section.slice(noteAt+'Speaker notes:'.length).trim();
  notes=notes.replace(/\[([^\]]+)\]\(([^)]+)\)/g,(all,label,target)=>{
    if(/^https?:/.test(target))return label+': '+target;
    const resolved=path.resolve(workspaceDir,target);
    const relative=path.relative(repo,resolved).replaceAll('\\','/');
    if(relative.startsWith('..'))throw new Error('Outside citation: '+target);
    return label+': '+github+relative;
  });
  for(const source of sources[i])await bytes(source);
  notes='Teaching point: '+point+'\n\n'+notes+'\n\nCourse evidence and reading:\n'+sources[i].map(p=>github+p).join('\n');
  if(visual)notes+='\n\nIllustration: '+github+'rsi/assets/illustrations/'+visual[1]+'\nThe figure explains a mechanism. Its illustrative cards do not establish an empirical result.';
  if(i===20)notes+='\n\nPrimary benchmark documentation, inspected 22 September 2026:\nhttps://github.com/aiming-lab/RSI-Exam/blob/main/README.md\nhttps://github.com/openai/mle-bench/blob/main/README.md\nThe table reports dated maintainer specifications, not our benchmark execution.';
  slideSpecs.push({number:i+1,title:start[2],point,image:visual?.[1],notes});
}

const p=Presentation.create({slideSize:{width:1280,height:720}});
const ink='#112840', teal='#087F83';
function text(slide,name,content,box,size=28,bold=false,color=ink){
 const s=slide.shapes.add({name,geometry:'textbox',position:box,fill:'none',line:{fill:'none',width:0}});
 s.text=content;s.text.style={typeface:family,fontSize:size,bold,color,autoFit:'none'};return s;
}
function heading(slide,title,point){
 text(slide,'Slide title',title,{left:64,top:40,width:1152,height:64},44,true);
 text(slide,'Teaching point',point,{left:64,top:115,width:1152,height:84},27,false);
}
function table(slide,values,widths,top=225,height=330,font=25){
 const t=slide.tables.add({rows:values.length,columns:values[0].length,left:64,top,width:1152,height,values,columnWidths:widths});
 t.borders.assign({fill:'#DCE4E8',width:0.7,style:'solid'});
 for(let r=0;r<values.length;r++){
   t.rows[r].height=height/values.length;
   for(let c=0;c<values[0].length;c++){
     const cell=t.getCell(r,c);cell.fill=r===0?'#E8F4F3':'#FFFFFF';
     cell.text.style={typeface:family,fontSize:font,bold:r===0,color:ink};
   }
 }
 return t;
}
const discovery = csv((await bytes('rsi/evidence/2026-09-22/discovery-final/RESULTS.csv')).toString('utf8'));
const contrasts = csv((await bytes('rsi/evidence/2026-09-22/nested-research-evaluation/CONTRASTS.csv')).toString('utf8'));
const counts = ['broad','greedy','lineage','evolved','broad-stop'].map(arm=>({arm,records:discovery.filter(r=>r.arm===arm)}));
// Validate the actual archive labels before exporting any chart.
console.log('Discovery arms:',[...new Set(discovery.map(r=>r.arm))].join(', '));
const chartCounts=counts.map(({arm,records})=>{
 if(records.length!==16)throw new Error('Expected sixteen tasks for '+arm);
 return records.reduce((s,r)=>s+Number(r.attempts),0);
});
if(chartCounts.join(',')!=='192,192,192,55,84')throw new Error('Search-cost evidence changed');
for(const spec of slideSpecs){
 const slide=p.slides.add();slide.background.fill='#FFFFFF';
 if(spec.image){
   const asset='rsi/assets/illustrations/'+spec.image;
   const raw=await bytes(asset);
   slide.images.add({blob:raw,contentType:'image/png',alt:spec.title+'. '+spec.point,fit:'contain',position:{left:16,top:8,width:1248,height:704}});
   assets.push({slide:spec.number,path:asset,...usedSources.get(asset)});
 }else if(spec.number===19){
   heading(slide,'Why the original results were mostly zero','Similar candidate sets can produce the same winner.');
   table(slide,[['Observed issue','What it hides','Repair to check'],['Repeated candidate sets','Different policy names can reach the same model','Inspect executed constructors and retained predictions'],['Fits called “wasted” afterward','A bookkeeping label does not save computation','Count attempts the program actually avoids'],['Fragile selection rankings','A selection gain can reverse on final rows','Freeze choices and retain all final outcomes']], [310,410,432],220,360,25);
   text(slide,'Scope','A code repair can restore the intended experiment without guaranteeing a quality gain.',{left:64,top:610,width:1152,height:70},27);
 }else if(spec.number===21){
   heading(slide,'Research benchmark scale','The laptop exercise and larger benchmarks test different capabilities.');
   table(slide,[['Setting','Task scope','Resource and grading boundary'],['Local nested study','6 reserved public tabular tasks','12 fits per procedure per task\nPublic files, procedural boundary'],['RSI-Exam','88 tasks in 6 domains\n35 public, 53 withheld','Up to 12 hours per task\nSeparate hidden grading'],['MLE-bench','75 competitions\n22 in the smaller subset','Recommended: 24 hours, 36 vCPUs,\n440 GB RAM, 24 GB A10 GPU']], [235,355,562],210,375,25);
   text(slide,'Dated scope','Maintainer specifications checked 22 September 2026. Resources vary by task.',{left:64,top:618,width:1152,height:65},25);
 }else if(spec.number===32){
   heading(slide,'Fewer executed fits on sixteen tasks','55 search fits versus 192. Overall predictive change remains uncertain.');
   const chart=slide.charts.add('bar',{position:{left:72,top:210,width:1120,height:385},categories:['Broad search','Greedy search','Lineage, no stop','Evolved policy','Broad + stop'],series:[{name:'Executed search fits',values:chartCounts,fill:teal,points:chartCounts.map((v,idx)=>({idx,fill:idx===3?teal:'#7890A5'}))}],barOptions:{direction:'bar',grouping:'clustered',gapWidth:65},hasLegend:false,xAxis:{min:0,max:220,numberFormatCode:'0',textStyle:{fontSize:24,typeface:family,fill:ink},majorGridlines:{fill:'#E8ECEF',width:0.5}},yAxis:{textStyle:{fontSize:26,typeface:family,fill:ink},majorGridlines:null},dataLabels:{showValue:true,position:'outEnd',textStyle:{fontSize:28,bold:true,typeface:family,fill:ink}},chartFill:'#FFFFFF',plotAreaFill:'#FFFFFF'});
   applyPresentationChartFont(chart,{fontFamily:family});
   text(slide,'Quality and cost boundary','Final quality: 3 better, 12 tied, 1 worse versus broad.\nBars exclude development, scoring and unmetered agent inference.',{left:64,top:620,width:1152,height:75},25);
 }else if(spec.number===33){
   heading(slide,'Later researchers have mixed results','I1 versus I0: two gains, three ties and one regression.');
   const names={i0:'I0 (primary)',parent:'Parent researcher',fixed:'Fixed portfolio',random:'Random search'};
   const fmt=v=>(Number(v)>=0?'+':'')+Number(v).toFixed(6);
   const values=[['Control','Mean loss change','Exploratory 95% interval'],...contrasts.map(r=>[names[r.parent],fmt(r.mean_loss_change),'['+fmt(r.interval_low)+', '+fmt(r.interval_high)+']'])];
   table(slide,values,[355,310,487],220,355,28);
   text(slide,'Interpretation','Lower is better. Every interval includes zero.\nSix public tasks, one model seed. Full study: 624 model attempts.',{left:64,top:615,width:1152,height:80},27);
 }else throw new Error('No layout for slide '+spec.number);
 slide.speakerNotes.textFrame.setText(spec.notes);
}
await fs.writeFile(path.join(build,'SLIDE-CONTENT.json'),JSON.stringify(slideSpecs,null,2)+'\n');
await fs.writeFile(path.join(build,'SPEAKER-NOTES.md'),slideSpecs.map(s=>'# '+String(s.number).padStart(2,'0')+' · '+s.title+'\n\n'+s.notes).join('\n\n')+'\n');
await fs.writeFile(path.join(build,'SOURCE-MANIFEST.json'),JSON.stringify({sourceCommit,font:family,canvas:{width:1280,height:720},sources:[...usedSources.values()],assets},null,2)+'\n');
const candidatePath=path.join(build,'candidate.pptx');
await (await PresentationFile.exportPptx(p)).save(candidatePath);
console.log('Exported 37-slide candidate with font '+family);
const finalPath=path.join(workspaceDir,'output/rsi-masterclass-review-v1.pptx');
const final=await finalizePresentation({workspaceDir,candidatePath,finalPath,pythonExecutable:python,integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit','--require-native-table-slide','19','--require-native-table-slide','21','--require-native-table-slide','33'],requiredNativeTableOwnerSlides:[19,21,33],requiredNativeChartOwnerSlides:[32],materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'design',families:[family]},verifyArtifactToolImport:true,receiptPath:path.join(build,'FINALIZATION.json')});
console.log('Finalizer:',JSON.stringify(final));
const renderDir=path.join(build,'renders');await fs.mkdir(renderDir,{recursive:true});
const reviewed = await PresentationFile.importPptx(await FileBlob.load(finalPath));
for(let i=0;i<reviewed.slides.items.length;i++){
 const slide=reviewed.slides.items[i];
 const png=await reviewed.export({slide,format:'png',scale:1});
 const stem=String(i+1).padStart(2,'0');
 await fs.writeFile(path.join(renderDir,'slide-'+stem+'.png'),new Uint8Array(await png.arrayBuffer()));
 const layout=await slide.export({format:'layout'});
 await fs.writeFile(path.join(renderDir,'slide-'+stem+'.layout.json'),await layout.text());
 console.log('Rendered slide '+(i+1));
}
