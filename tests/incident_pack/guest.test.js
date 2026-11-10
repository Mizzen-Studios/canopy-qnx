'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),c=require('../../tools/incident_pack/core');
// Artificial derivatives used only for validator regression, not target evidence.
async function fixture(){
 const p=JSON.parse(fs.readFileSync('docs/acceptance/control-fix-20261108/incident.json','utf8'));
 p.collector={id:'canopy-native-query',version:'2',mechanism:'slog2-libcan-query'};
 const kill=p.events.find(e=>e.kind==='kill'&&e.process.name==='dev-can-linux'),recovery=p.events.find(e=>e.kind==='recovery'),main=p.events.find(e=>e.kind==='process'&&e.process.name==='io-sock');
 const raw=p.artifacts.find(a=>a.path==='serial.txt'),slog='canopy_incident.999 SLOG2_INFO ARTIFICIAL TEST ONLY';
 const rows=['publish','killed','recovery','survivors','isolation'].map(query=>'CANOPY_GUEST_QUERY '+JSON.stringify({schema:'canopy-query-1',query,server:999,target:kill.process.pid,replacement:recovery.process.pid,main:main.process.pid,killed:1,recovery:1,survivor:1}));
 raw.text='CANOPY_QUERY_READY pid=999 chid=1 ARTIFICIAL TEST'+String.fromCharCode(10)+raw.text+String.fromCharCode(10)+rows.join(String.fromCharCode(10))+String.fromCharCode(10)+slog;
 raw.sha256=await c.sha(raw.text);raw.subjectSha256=raw.sha256;
 for(const [path,text]of [['guest-query.txt',rows.join(String.fromCharCode(10))],['slog2.txt',slog]])p.artifacts.push({path,role:'observation',runId:p.run.id,text,sha256:await c.sha(text),subjectSha256:await c.sha(text)});
 return p;
}
test('artificial same-pack guest results exposed in four hero answers',async()=>{const p=await fixture(),v=await c.validate(JSON.stringify(await c.seal(p)));assert.equal(v.status,'VALID',v.issues.join());for(const q of ['killed','recovery','survivors','isolation'])assert.match(v.answers[q].guestQuery.text,new RegExp('"query":"'+q+'"'));});
for(const variant of ['missing','mixed','wrongIdentity','corrupt','missingSlog','wrongOrigin'])test('guest proof '+variant+' fails closed',async()=>{
 const p=await fixture(),a=p.artifacts.find(a=>a.path==='guest-query.txt');
 if(variant==='missing')p.artifacts=p.artifacts.filter(a=>a.path!=='guest-query.txt');
 if(variant==='missingSlog')p.artifacts=p.artifacts.filter(a=>a.path!=='slog2.txt');
 if(variant==='mixed')a.runId='different-run';
 if(variant==='wrongOrigin')p.run.environment='HOST_SIMULATION';
 if(variant==='wrongIdentity'){a.text=a.text.replaceAll('"server":999','"server":998');a.sha256=await c.sha(a.text);a.subjectSha256=a.sha256;}
 if(variant==='corrupt')a.text+='x';
 const v=await c.validate(JSON.stringify(await c.seal(p)));assert.equal(v.status,'UNKNOWN');for(const a of Object.values(v.answers))assert.equal(a.status,'UNKNOWN');
});
