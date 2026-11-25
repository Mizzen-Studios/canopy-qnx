/* HOST-only recorded-byte projection. No built-in vehicle/DBC semantics. */
(function(root){'use strict';
const node=typeof module!=='undefined'&&module.exports,c=node?require('./core'):root.IncidentPack,compare=node?require('./compare'):root.IncidentCompare;
const LIMIT=8192,fields='byteLength byteOffset direction endian id label max min offset scale signed unit';
function need(ok,msg){if(!ok)throw Error(msg);}
function mapping(raw){
 need(typeof raw==='string'&&raw.length<=LIMIT,'mapping must be JSON text up to 8192 characters');
 const m=JSON.parse(raw);need(m&&Object.keys(m).sort().join(' ')==='schema signals'&&m.schema==='canopy.signals/1','mapping schema canopy.signals/1 required');
 need(Array.isArray(m.signals)&&m.signals.length>0&&m.signals.length<=8,'one to eight mappings required');
 for(const s of m.signals){need(s&&Object.keys(s).sort().join(' ')===fields,'closed signal fields required');
 for(const k of ['label','unit'])need(typeof s[k]==='string'&&s[k].trim().length>0&&s[k].length<=80,'bounded label/unit required');
 need(['RX','TX'].includes(s.direction)&&Number.isSafeInteger(s.id)&&s.id>=0&&s.id<=2047,'direction / standard CAN ID required');
 need(Number.isSafeInteger(s.byteOffset)&&s.byteOffset>=0&&Number.isSafeInteger(s.byteLength)&&s.byteLength>=1&&s.byteLength<=4&&s.byteOffset+s.byteLength<=8,'byte bounds: offset 0..7, length 1..4, within eight bytes');
 need(['little','big'].includes(s.endian)&&typeof s.signed==='boolean','explicit endian and signed required');
 for(const k of ['scale','offset','min','max'])need(typeof s[k]==='number'&&Number.isFinite(s[k]),'finite numeric '+k+' required');
 need(s.scale!==0&&s.min<=s.max,'nonzero scale and ordered physical bounds required');
 }return m;
}
function decode(hex,s){
 need(typeof hex==='string'&&/^[0-9a-f]{16}$/.test(hex),'eight lowercase-hex bytes required');
 const bytes=hex.match(/../g).slice(s.byteOffset,s.byteOffset+s.byteLength).map(x=>parseInt(x,16));if(s.endian==='little')bytes.reverse();
 let raw=bytes.reduce((n,b)=>n*256+b,0);if(s.signed&&raw>=2**(s.byteLength*8-1))raw-=2**(s.byteLength*8);
 const value=raw*s.scale+s.offset;return {raw,value:Number.isFinite(value)&&value>=s.min&&value<=s.max?value:null};
}
async function analyze(raw,mapRaw,options={}){
 try{
 const m=mapping(mapRaw),v=await c.validate(raw,options);need(v.status==='VALID',(v.issues||['pack not accepted']).join('; '));
 const traffic={};for(const d of ['RX','TX'])traffic[d]=await compare.inspect(v.pack,d);
 const signals=m.signals.map(s=>{
 const a=v.pack.artifacts.find(a=>a.path===s.direction+'.txt'),lists=compare.parseLists(a.text,s.direction,v.pack.schema==='canopy.incident/3');
 const points=lists.observed.flatMap((frame,index)=>{const [id,hex]=frame.split(':');if(Number(id)!==s.id)return [];return [{index,frame,...decode(hex,s),citation:{path:a.path,line:lists.split+2+index,sha256:a.sha256,event:traffic[s.direction].citations[0].event}}];});
 return {mapping:s,status:points.some(p=>p.value!==null)?'DECODED_USER_MAPPING':'UNKNOWN',points,totalObserved:lists.observed.length};
 });return {status:'ACCEPTED_RECORDED_BYTES',scope:v.scope,current:false,signals,traffic:Object.values(traffic),axis:'Observed frame ordinal within each direction (zero-based); NOT elapsed time. No per-frame aligned clock is supplied by the canonical lists. RX/TX are separate axes. No interpolation, carry-forward or outside-capture values.',meaning:'USER-SUPPLIED INTERPRETATION — not verified vehicle meaning, OEM DBC, native RPM or speed proof. Public bytes are recorder test patterns.',outside:'Missing samples, invalid physical values and outside capture UNKNOWN. List differences do not identify missing signal values or exact loss times.'};
 }catch(e){return {status:'UNKNOWN',current:false,signals:[],issues:[e.message]};}
}
function example(){return JSON.stringify({schema:'canopy.signals/1',signals:[{label:'Recorder byte zero (illustrative, not vehicle speed)',unit:'raw count',direction:'RX',id:1,byteOffset:0,byteLength:1,endian:'little',signed:false,scale:1,offset:0,min:0,max:255}]},null,2);}
const api={mapping,decode,analyze,example,LIMIT};if(node)module.exports=api;else root.IncidentSignals=api;
})(globalThis);
