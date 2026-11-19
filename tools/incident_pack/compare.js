/* Bounded comparative analysis; each run is independently validated. No pooled verdict. */
(function(root){'use strict';
const c=typeof module!=='undefined'&&module.exports?require('./core'):root.IncidentPack;
const MAX_FRAMES=512, outside='Outside these finite recorded lists UNKNOWN. CAN IDs are not sequence counters; silence and snapshots do not prove loss.';
function need(ok,msg){if(!ok)throw Error(msg);}
function parseLists(text,direction,allowEmpty=false){
 need(typeof text==='string'&&text.length<=32768,'bounded traffic artifact required');
 const lines=text.split('\n');need(lines.pop()==='','traffic requires final newline');
 need(lines[0]===direction+' expected','expected list header');const split=lines.indexOf(direction+' actual');
 need(split>=(allowEmpty?1:2)&&lines.lastIndexOf(direction+' actual')===split,'ambiguous actual list');
 function frames(rows){need(rows.length<=MAX_FRAMES,'frame resource limit');return rows.map(row=>{const m=/^(0|[1-9][0-9]{0,3}):([a-f0-9]{16})$/.exec(row);need(m&&Number(m[1])<=2047,'unsupported frame encoding: SFF / eight bytes only');return row;});}
 const expected=frames(lines.slice(1,split)),observed=frames(lines.slice(split+1));need(allowEmpty||expected.length>0,'explicit expected list required');return {expected,observed,split};
}
function diff(expected,observed){
 const counts=rows=>{const m=new Map();for(const f of rows)m.set(f,(m.get(f)||0)+1);return m;},a=counts(expected),b=counts(observed),missing=[],duplicate=[],unexpected=[];
 for(const [frame,n] of a)if((b.get(frame)||0)<n)missing.push({frame,count:n-(b.get(frame)||0)});
 for(const [frame,n] of b)if(!a.has(frame))unexpected.push({frame,count:n});else if(n>a.get(frame))duplicate.push({frame,count:n-a.get(frame)});
 // Compare relative order of shared occurrences, ignoring unmatched extras/missing.
 const shared=rows=>{const used=new Map();return rows.filter(f=>{const n=(used.get(f)||0)+1;used.set(f,n);return n<=Math.min(a.get(f)||0,b.get(f)||0);});};
 const x=shared(expected),y=shared(observed),reordered=x.some((f,i)=>f!==y[i]);
 return {expected:expected.length,observed:observed.length,missing,duplicate,unexpected,reordered,orderedExact:c.canonical(expected)===c.canonical(observed)};
}
async function inspect(p,direction){
 const es=p.events.filter(e=>e.kind==='traffic'&&e.data.direction===direction);need(es.length===1,'missing/ambiguous '+direction+' event');const e=es[0],a=p.artifacts.find(a=>a.path===direction+'.txt');
 need(a&&a.role==='observation'&&a.subjectSha256===a.sha256,'missing/raw traffic subject mismatch');need(e.evidence.length===1&&e.evidence[0].path===a.path&&e.evidence[0].line===1,'traffic citation mismatch');
 const {expected,observed,split}=parseLists(a.text,direction,p.schema==='canopy.incident/3'),encode=rows=>rows.join('\n')+(rows.length?'\n':'');
 need(await c.sha(encode(expected))===e.data.expectedSha256&&await c.sha(encode(observed))===e.data.observedSha256,'raw/summary digest mismatch');
 need(e.data.count===observed.length&&e.data.bytes===observed.length*8,'raw/summary count mismatch');
 if(p.schema==='canopy.incident/3'){
 need(e.data.expectedCount===expected.length&&e.data.expectedBytes===expected.length*8,'raw/expected count mismatch');
 const end=p.artifacts.find(a=>a.path===e.data.captureEnd.path);
 need(end?.role==='observation'&&end.subjectSha256===end.sha256,'capture completion artifact required');
 const completionLines=end.text.replace(/\r/g,'').split('\n'),prefix='CANOPY_CAPTURE_COMPLETE '+p.run.id+' '+direction+' ';
 need(completionLines.filter(line=>line.startsWith(prefix)).length===1&&completionLines[e.data.captureEnd.line-1]===['CANOPY_CAPTURE_COMPLETE',p.run.id,direction,e.observer.generation,expected.length,observed.length,e.data.expectedSha256,e.data.observedSha256].join(' '),'finite capture completion mismatch/ambiguity');
 }
 const outcome=diff(expected,observed);need(e.data.ordered===outcome.orderedExact,'raw/summary ordered mismatch');
 const recoveries=p.events.filter(r=>r.kind==='recovery'&&c.canonical(r.process)===c.canonical(e.process)&&r.at<e.at&&r.data.state==='observed');need(recoveries.length===1&&e.observer.independent,'ambiguous traffic process provenance');
 const citations=[{event:e.id,path:a.path,sha256:a.sha256,expectedLines:expected.length?[2,split]:[],observedLines:observed.length?[split+2,split+1+observed.length]:[]}];
 if(p.schema==='canopy.incident/3')citations.push({captureCompletion:e.data.captureEnd,expectedCount:e.data.expectedCount,observedCount:e.data.count});
 if(p.run.environment!=='HOST_SIMULATION'){
 need(['slog2-serial-libcan','slog2-libcan-query'].includes(p.collector.mechanism),'unsupported native traffic provenance');
 const serial=p.artifacts.find(a=>a.path==='serial.txt');need(serial?.role==='observation'&&serial.subjectSha256===serial.sha256,'missing serial binding');
 const lines=serial.text.replace(/\r/g,'').split('\n'),r=recoveries[0];need(r.evidence.length===1&&r.evidence[0].path==='serial.txt','recovery citation mismatch');const line=r.evidence[0].line;
 need(new RegExp('^\\s*'+e.process.pid+'\\s+.*dev-can-linux').test(lines[line-1]),'raw recovery PID mismatch');
 const rows=[];for(let i=line;i<lines.length;i++){let m;if(direction==='RX'){m=/^  \/dev\/can0\/rx0 TS: [0-9]+ms \[SFF\] ([A-Fa-f0-9]+) \[8\] ((?:[A-Fa-f0-9]{2} ){7}[A-Fa-f0-9]{2})$/.exec(lines[i]);if(m)rows.push({frame:parseInt(m[1],16)+':'+m[2].replace(/ /g,'').toLowerCase(),line:i+1});}else{m=/^> \/proc\/boot\/cansend -u0,tx0 -m0x([a-f0-9]+),0,0x([a-f0-9]{16}) \|\| exit 1$/.exec(lines[i]);if(m)rows.push({frame:parseInt(m[1],16)+':'+m[2],line:i+1});}}
 need(rows.length<=MAX_FRAMES&&c.canonical(rows.map(x=>x.frame))===c.canonical(direction==='RX'?observed:expected),'serial traffic mismatch/ambiguity');
 if(p.schema==='canopy.incident/3')need(e.data.captureEnd.path==='serial.txt'&&e.data.captureEnd.line>line&&rows.every(x=>x.line<e.data.captureEnd.line),'native capture completion must follow actual serial frames');
 need(rows.length>0||p.schema==='canopy.incident/3','missing serial traffic');citations.push({path:'serial.txt',sha256:serial.sha256,processLine:line,frameLines:rows.map(x=>x.line),scope:direction==='RX'?'QNX RX observed bytes':'QNX TX command expected bytes; host observed list separately bound, not serial reception proof'});
 }
return {direction,status:'OBSERVED',origin:p.run.environment==='HOST_SIMULATION'?'HOST / SYNTHETIC — NOT QNX':'RECORDED collector-declared QNX',process:e.process,...outcome,citations,text:outcome.orderedExact?'No missing frames observed in these finite recorded lists.':'Recorded list differences observed; not a continuous-loss rate.'};
}
async function diagnose(raw,options={}){
 const v=await c.validate(raw,options);if(v.status!=='VALID')return {status:'UNKNOWN',scope:v.scope,issues:v.issues,traffic:[],outside};
 const p=v.pack,scope={...v.scope,collector:p.collector,bindings:Object.fromEntries(Object.entries(p.bindings).map(([role,path])=>{const a=p.artifacts.find(a=>a.path===path);return [role,{path,sha256:a.sha256,subjectSha256:a.subjectSha256}];}))},traffic=[];
 for(const direction of ['RX','TX']){try{
 traffic.push(await inspect(p,direction));
 }catch(err){traffic.push({direction,status:'UNKNOWN',issues:[err.message]});}}
 return {status:traffic.every(t=>t.status==='OBSERVED')?'OBSERVED':'UNKNOWN',scope,traffic,outside,issues:traffic.flatMap(t=>t.issues||[])};
}
async function compare(left,right,options={}){
 const validOptions=options&&typeof options==='object'&&!Array.isArray(options)&&Object.keys(options).every(k=>['mode','now','left','right'].includes(k)),shared=validOptions?Object.fromEntries(Object.entries(options).filter(([k])=>['mode','now'].includes(k))):{invalid:true};
 const runs=await Promise.all([diagnose(left,validOptions&&Object.hasOwn(options,'left')?options.left:shared),diagnose(right,validOptions&&Object.hasOwn(options,'right')?options.right:shared)]),[a,b]=runs;
 const valid=r=>!!r.scope?.runId, same=valid(a)&&valid(b)&&a.scope.seal===b.scope.seal,sharedId=valid(a)&&valid(b)&&a.scope.runId===b.scope.runId&&!same,mixed=valid(a)&&valid(b)&&(a.scope.originalEnvironment==='HOST_SIMULATION')!==(b.scope.originalEnvironment==='HOST_SIMULATION');
 const issues=[];if(sharedId)issues.push('Ambiguous shared run ID with different seals: not independent incidents.');if(mixed)issues.push('Mixed HOST/native origins: no shared native conclusion.');
 const differences=['RX','TX'].map(direction=>{const x=a.traffic.find(t=>t.direction===direction),y=b.traffic.find(t=>t.direction===direction);if(x?.status!=='OBSERVED'||y?.status!=='OBSERVED'||sharedId||mixed)return {direction,status:'UNKNOWN'};const metrics=t=>({expected:t.expected,observed:t.observed,missing:t.missing.reduce((n,x)=>n+x.count,0),duplicate:t.duplicate.reduce((n,x)=>n+x.count,0),unexpected:t.unexpected.reduce((n,x)=>n+x.count,0),reordered:t.reordered});return {direction,status:'OBSERVED',left:metrics(x),right:metrics(y),changed:c.canonical(metrics(x))!==c.canonical(metrics(y))};});
 return {status:!sharedId&&!mixed&&runs.every(r=>r.status==='OBSERVED')?'OBSERVED':'UNKNOWN',relationship:same?'SAME PACK — not independent incidents':sharedId?'AMBIGUOUS RUN ID':mixed?'MIXED ORIGINS — no shared native conclusion':'SEPARATELY VALIDATED RUNS — no pooled events or cross-run PID verdict',runs,differences,issues,outside,current:false};
}
const api={compare,diagnose,inspect,parseLists,diff,MAX_FRAMES};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.IncidentCompare=api;
})(globalThis);
