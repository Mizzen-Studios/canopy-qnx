'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),{spawnSync}=require('node:child_process'),compare=require('../../tools/incident_pack/compare');
const files=['docs/acceptance/control-fix-20261108/incident.json','docs/acceptance/recording-20261115/incident.json'];
async function clocked(fn){const dir=fs.mkdtempSync(path.join(os.tmpdir(),'canopy-display-'));try{const clock=path.join(dir,'clock.cjs');fs.writeFileSync(clock,"Date.now=()=>Date.parse('2027-01-15T00:00:00Z');");const run=args=>spawnSync(process.execPath,['--require',clock,'tools/incident_pack/cli.js',...args],{encoding:'utf8'});await fn(run,dir);}finally{fs.rmSync(dir,{recursive:true});}}
test('expired compare table default, JSON opt-in identical API, strict remains closed',()=>clocked(async run=>{
 const table=run(['compare',...files,'--historical']);assert.equal(table.status,0,table.stderr);assert.match(table.stdout,/Capture.*Expected.*Observed.*Missing/);assert.match(table.stdout,/EXPIRED/);assert.match(table.stdout,/NOT CURRENT/);assert.match(table.stdout,/100.*100.*0/);
 const json=run(['compare',...files,'--historical','--json']);assert.equal(json.status,0);assert.deepEqual(JSON.parse(json.stdout),await compare.compare(...files.map(f=>fs.readFileSync(f,'utf8')),{mode:'historical',now:Date.parse('2027-01-15T00:00:00Z')}));
 const strict=run(['compare',...files]);assert.equal(strict.status,2);assert.match(strict.stdout,/UNKNOWN/);assert.doesNotMatch(strict.stdout,/100 [|] 100/);
}));
test('missing corrupt and invalid format options fail with explicit UNKNOWN',()=>clocked(async(run,dir)=>{
 const bad=path.join(dir,'bad.json');fs.writeFileSync(bad,'{}');for(const args of [['compare',files[0],bad,'--historical'],['compare',files[0],'missing.json','--historical'],['compare',...files,'--json','--json'],['compare',...files,'--csv']]){const r=run(args);assert.equal(r.status,2);assert.match(r.stdout,/UNKNOWN/);}
 const r=run(['query',files[0],'recovery','--historical']);assert.equal(r.status,0);assert.equal(JSON.parse(r.stdout).answer.status,'OBSERVED');
}));
