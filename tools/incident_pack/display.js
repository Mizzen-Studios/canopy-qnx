'use strict';
// Presentation only. Validation/comparison APIs and verdicts remain unchanged.
function table(result) {
  const clean=v=>String(v??'UNKNOWN').split(String.fromCharCode(10)).join(' ').split(String.fromCharCode(13)).join(' ').replaceAll('|',' ').slice(0,240);
  const lines=['CANopy capture comparison — '+clean(result.status),'HISTORICAL / NOT CURRENT: saved observations, not live health.',clean(result.relationship||'No accepted comparison.'),'','| Capture | Mode / expiry | Direction | Expected | Observed | Missing | Duplicate | Unexpected | Reordered | Verdict |','|---|---|---|---:|---:|---:|---:|---:|---|---|'];
  const notes=[];
  for(const [i,run] of (result.runs||[]).entries()) {
    const scope=run.scope||{}, name=(i?'Right: ':'Left: ')+(scope.runId||'not accepted');
    const age=(scope.mode||'unknown')+' / '+(scope.expired?'EXPIRED':'expires '+(scope.expiresAt||'unknown'));
    if(!run.traffic?.length)lines.push('| '+[name,age,'—',null,null,null,null,null,null,run.status].map(clean).join(' | ')+' |');
    for(const t of run.traffic||[]) {
      const observed=t.status==='OBSERVED',count=a=>observed?a.reduce((n,x)=>n+x.count,0):null;
      lines.push('| '+[name,age,t.direction,observed?t.expected:null,observed?t.observed:null,count(t.missing||[]),count(t.duplicate||[]),count(t.unexpected||[]),observed?t.reordered:null,t.status].map(clean).join(' | ')+' |');
    }
    notes.push((i?'Right':'Left')+' origin: '+clean(scope.originalEnvironment)+'; seal: '+clean(scope.seal));
    for(const issue of run.issues||[])notes.push('Issue: '+clean(issue));
  }
  lines.push('',...notes,'',clean(result.outside||'Outside recorded evidence UNKNOWN.'));
  for(const issue of result.issues||[])lines.push('Issue: '+clean(issue));
  lines.push('Use --json for the unchanged machine-readable comparison result.');
  return lines.join(String.fromCharCode(10));
}
module.exports={table};
