#!/usr/bin/env node
'use strict';
const fs=require('node:fs'),path=require('node:path'),core=require('./core');
function readLocal(name){const absolute=path.resolve(name);let current=path.parse(absolute).root;for(const part of absolute.slice(current.length).split(path.sep)){current=path.join(current,part);if(fs.lstatSync(current).isSymbolicLink())throw Error('symlink path refused');}const fd=fs.openSync(absolute,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW|fs.constants.O_NONBLOCK);try{const s=fs.fstatSync(fd);if(!s.isFile()||s.size>core.LIMIT)throw Error('regular file <= 2 MiB required');const b=Buffer.alloc(core.LIMIT+1),n=fs.readSync(fd,b,0,b.length,0);if(n>core.LIMIT)throw Error('file grew beyond limit');return new TextDecoder('utf-8',{fatal:true}).decode(b.subarray(0,n));}finally{fs.closeSync(fd);}}
(async()=>{
  let result;const args=process.argv.slice(2),command=args[0],json=args.includes('--json');
  try {
    if(json){if(command!=='compare'||args.filter(x=>x==='--json').length!==1)throw Error('--json is only accepted once for compare');args.splice(args.indexOf('--json'),1);}
    const historical=args.includes('--historical');if(historical)args.splice(args.indexOf('--historical'),1);
    const [cmd,file,question]=args;
    if(cmd==='compare'){
      if(args.length!==3)throw Error('usage: compare LEFT.json RIGHT.json [--historical] [--json]');
      result=await require('./compare').compare(readLocal(file),readLocal(question),{mode:historical?'historical':'strict'});
      process.exitCode=result.status==='OBSERVED'?0:2;
    } else {
      if(!['validate','query'].includes(cmd)||!file||args.length>(cmd==='query'?3:2))throw Error('usage: node tools/incident_pack/cli.js validate PACK.json [--historical] | query PACK.json [killed|recovery|survivors|isolation] [--historical] | compare LEFT.json RIGHT.json [--historical] [--json]');
      result=await core.validate(readLocal(file),{mode:historical?'historical':'strict'});
      if(cmd==='query'&&question){if(!Object.hasOwn(result.answers,question))throw Error('unknown question');result={status:result.status,scope:result.scope,issues:result.issues,answer:result.answers[question]};}
      process.exitCode=result.status==='VALID'?0:2;
    }
  }catch(e){result={status:'UNKNOWN',issues:[e.message]};process.exitCode=2;}
  delete result.pack;
  console.log(command==='compare'&&!json?require('./display').table(result):JSON.stringify(result,null,2));
})();
