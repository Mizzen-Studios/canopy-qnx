/* Native capture ingestion; never runs commands or manufactures absent evidence. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),c=require('./core');
async function adapt(dir,receiptFile){
 const read=n=>fs.readFileSync(path.join(dir,n),'utf8');
 const r=JSON.parse(read('receipt.json')), build=JSON.parse(fs.readFileSync(receiptFile,'utf8'));
 if(!r.guest_stopped_reaped)throw Error('unreaped capture');
 const runId=r.run_id,artifacts=[],bindings={};
 async function artifact(p,role,text,subject){artifacts.push({path:p,role,runId,text,sha256:await c.sha(text),subjectSha256:subject});}
 for(const role of ['source','binary','image','disk']){
  const b=build[role];if(!b||!b.sha256||!b.text)throw Error('missing '+role+' lineage');
  if(role==='image'&&b.sha256!==r.image_sha256||role==='disk'&&b.sha256!==r.disk_sha256)throw Error('mixed build/run');
  bindings[role]=role+'.txt';await artifact(bindings[role],role,b.text,b.sha256);
 }
 const raw=read('serial.txt');if(r.raw_sha256&&r.raw_sha256!==await c.sha(raw)||build.captureSha256&&build.captureSha256!==await c.sha(raw))throw Error('mixed raw capture');await artifact('serial.txt','observation',raw,await c.sha(raw));
 const lines=raw.replace(/\r/g,'').split('\n'),events=[];
 const add=(kind,process,data,line,observer={name:'host-controller',generation:runId+'-host',independent:true})=>events.push({id:'e'+events.length,seq:events.length,at:events.length,runId,kind,process,observer,evidence:[{path:'serial.txt',line:line+1}],data});
 const proc=(name,pid,generation,domain)=>({name,pid,generation,domain});
 const native=[];lines.forEach((l,i)=>{if(l.startsWith('{"schema":"canopy-native-1"')){try{native.push({v:JSON.parse(l),i});}catch{throw Error('truncated native JSON');}}});
 if(native.length){
  if(native.length!==5||native.some((x,i)=>x.v.seq!==i)||native.map(x=>x.v.phase).join()!=='before,kill,waitpid,interruption,after')throw Error('native sequence incomplete');
  const pid=native[0].v.pid,recorder=native[0].v.recorder;
  const slog=lines.filter(l=>l.includes('canopy_incident.')&&l.includes('SLOG2_INFO')).map(l=>{try{return JSON.parse(l.slice(l.indexOf('{')));}catch{throw Error('slog2 truncation');}});
  if(slog.length!==5||slog.some((v,i)=>JSON.stringify(v)!==JSON.stringify(native[i].v)))throw Error('slog2/serial mismatch');
  if(native.some(x=>x.v.pid!==pid||x.v.recorder!==recorder)||native[0].v.result!==0||native[1].v.result!==0)throw Error('target/kill failed');
  const row=r.restarts.find(x=>x.killed_pid===pid),driver=proc('dev-can-linux',pid,runId+'-driver1','can');
  const survivor=proc('io-sock',r.main_io_sock_pid,runId+'-iosock','network');
  const snapshots=lines.map((l,i)=>({l,i})).filter(x=>new RegExp('^\\s*'+r.main_io_sock_pid+'\\s+.*io-sock').test(x.l));
  if(snapshots.length>1)add('process',survivor,{state:'observed'},snapshots[0].i);
  add('kill',driver,{signal:'SIGKILL'},native[1].i);
  if(native[3].v.result===1)add('interruption',driver,{state:'observed'},native[3].i);
  if(row&&row.new_pid!==pid){
   const replacement=proc('dev-can-linux',row.new_pid,runId+'-driver2','can');
   const line=lines.findIndex((l,i)=>i>native[3].i&&new RegExp('^\\s*'+row.new_pid+'\\s+.*dev-can-linux').test(l));
   if(line>=0){add('recovery',replacement,{state:'observed'},line);
    if(fs.existsSync(path.join(dir,'traffic1.json'))){
     const t=JSON.parse(read('traffic1.json'));
     for(const [direction,expected,actual] of [['RX',t.host_rx,t.qnx_rx],['TX',t.native_tx_expected,t.host_tx]]){
      const valid=x=>Array.isArray(x)&&x.length===100&&x.every(f=>Array.isArray(f)&&f.length===2&&Number.isInteger(f[0])&&f[0]>=0&&f[0]<=2047&&/^[a-f0-9]{16}$/.test(f[1]));
      if(!valid(expected)||!valid(actual))continue;
      // Canonical encoding: decimal CAN-ID ':' lowercase 8-byte hex '\n', preserving order.
      const encode=x=>x.map(f=>f[0]+':'+f[1]+'\n').join('');
      const text=direction+' expected\n'+encode(expected)+direction+' actual\n'+encode(actual);
      const p=direction+'.txt';await artifact(p,'observation',text,await c.sha(text));
      const e={id:'e'+events.length,seq:events.length,at:events.length,runId,kind:'traffic',process:replacement,observer:{name:'host-controller',generation:runId+'-host',independent:true},evidence:[{path:p,line:1}],data:{direction,count:100,bytes:800,expectedSha256:await c.sha(encode(expected)),observedSha256:await c.sha(encode(actual)),ordered:true}};events.push(e);
     }
    }
   }
  }
  if(snapshots.length>1)add('process',survivor,{state:'observed'},snapshots.at(-1).i);
  // Known collector topology: worker main joins its observer thread; no TID invented.
  const before=lines.map((l,i)=>({i,m:/^SEPARATE_RECORDER before_kill pid=(\d+) target=(\d+)$/.exec(l)})).filter(x=>x.m);
  if(before.length===1){
   const b=before[0],target=Number(b.m[2]),parent=Number(b.m[1]);
   const samples=[0,1,2].map(n=>lines.findIndex(l=>l==='RECORDER captured=COLOCATED sample='+n+' pid='+target));
   const ready=lines.indexOf('RECORDER captured=COLOCATED_READY');
   const ctl=lines.findIndex((l,i)=>i>b.i&&/^NEGATIVE_CONTROL signal=9 eof=[1-9][0-9]* colocated_post_kill=0$/.test(l));
   const after=[0,1,2].map(n=>lines.findIndex((l,i)=>i>ctl&&l==='SEPARATE_RECORDER after_kill='+n+' pid='+parent));
   if(target!==parent&&samples.every((v,i)=>v>=0&&(i===0||v>samples[i-1]))&&ready>samples[2]&&b.i>ready&&ctl>b.i&&after.every((v,i)=>v>ctl&&(i===0||v>after[i-1]))){
    const combined=proc('prereq-worker',target,runId+'-control-child','control-child'),separate=proc('prereq-recorder',parent,runId+'-control-parent','control-parent');
    const emit=(kind,p,data,line)=>{add(kind,p,data,line);return events.at(-1).id;};
    const mainBefore=emit('process',combined,{state:'observed'},ready);
    const memberBefore=emit('process',combined,{state:'observed'},samples[2]);
    const survivorBefore=emit('process',separate,{state:'observed'},b.i);
    const trigger=emit('kill',combined,{signal:'SIGKILL'},ctl);
    const termination=emit('interruption',combined,{state:'observed'},ctl);
    const mainAfter=emit('process',combined,{state:'absent'},ctl);
    const memberAfter=emit('process',combined,{state:'absent'},ctl);
    const survivorAfter=emit('process',separate,{state:'observed'},after[2]);
    add('control',combined,{mode:'in_process',outcome:'cofailure_observed',members:[{name:'worker-main',process:combined,before:mainBefore,after:mainAfter},{name:'observer-thread',process:combined,before:memberBefore,after:memberAfter}],trigger,termination,survivor:{before:survivorBefore,after:survivorAfter}},ctl);
   }
  }
 }
 if(!events.length)throw Error('no actual incident events');
 const capturedAt=new Date(r.captured_at*1000).toISOString(),expiresAt=new Date(r.captured_at*1000+30*86400000).toISOString();
 const p=await c.seal({schema:'canopy.incident/2',collector:{id:'canopy-native',version:'2',mechanism:'slog2-serial-libcan'},run:{id:runId,environment:'FRESH_QNX',capturedAt,expiresAt},bindings,artifacts,events});
 const check=await c.validate(JSON.stringify(p));if(check.status!=='VALID')throw Error(check.issues.join(';'));return p;
}
module.exports=adapt;
if(require.main===module)adapt(process.argv[2],process.argv[3]).then(p=>console.log(JSON.stringify(p,null,2))).catch(e=>{console.error('UNKNOWN: '+e.message);process.exitCode=2;});
