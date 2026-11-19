/* HOST/SYNTHETIC ONLY — never native capture evidence. */
'use strict';
const core=require('../../tools/incident_pack/core'),fixture=require('../../tools/incident_pack/fixture');
module.exports=async function diagnostic(expectedCount=100,observedCount=99,change){
const p=await fixture();p.schema='canopy.incident/3';p.collector.version='3';
for(const direction of ['RX','TX']){
const expected=Array.from({length:expectedCount},(_,i)=>i+':'+i.toString(16).padStart(16,'0')),observed=expected.slice(0,observedCount);while(observed.length<observedCount)observed.push('2000:ffffffffffffffff');if(change&&direction==='RX')change(expected,observed);
const encode=rows=>rows.map(x=>x+'\n').join(''),text=direction+' expected\n'+encode(expected)+direction+' actual\n'+encode(observed),path=direction+'.txt';
const artifact=async(path,text)=>p.artifacts.push({path,text,role:'observation',runId:p.run.id,sha256:await core.sha(text),subjectSha256:await core.sha(text)});await artifact(path,text);
const e=p.events.find(e=>e.kind==='traffic'&&e.data.direction===direction);e.evidence=[{path,line:1}];e.data={direction,count:observed.length,bytes:observed.length*8,expectedCount:expected.length,expectedBytes:expected.length*8,expectedSha256:await core.sha(encode(expected)),observedSha256:await core.sha(encode(observed)),ordered:core.canonical(expected)===core.canonical(observed),captureEnd:{path:direction+'-complete.txt',line:1}};
await artifact(e.data.captureEnd.path,['CANOPY_CAPTURE_COMPLETE',p.run.id,direction,e.observer.generation,expected.length,observed.length,e.data.expectedSha256,e.data.observedSha256].join(' ')+'\n');
}return core.seal(p);
};
