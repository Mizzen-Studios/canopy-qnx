#!/usr/bin/env python3
"""Deterministic one-file offline desk; only two already-public packs. No network."""
import argparse,base64,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PACKS={'canopy-2026-11-08-original.json':'docs/acceptance/control-fix-20261108/incident.json','canopy-2026-11-15-original.json':'docs/acceptance/recording-20261115/incident.json'}
def digest(data):return hashlib.sha256(data).hexdigest()
def build():
    source=ROOT/'web/incident-pack/index.html';body=source.read_text();assets=[]
    css=(source.parent/'style.css').read_text()
    body=body.replace('<link rel="stylesheet" href="style.css">','<style>'+css+'</style>')
    def inline(m):
        p=(source.parent/m[1]).resolve();raw=p.read_text()
        if p.name=='recorded-example.js':
            rel=next(iter(PACKS.values()));data=(ROOT/rel).read_bytes()
            raw='globalThis.CANopyRecordedExample={raw:new TextDecoder().decode(Uint8Array.from(atob('+json.dumps(base64.b64encode(data).decode())+'),c=>c.charCodeAt(0))),sha256:'+json.dumps(digest(data))+',source:'+json.dumps(rel)+'};'
        if '</script' in raw.lower():raise ValueError('unsafe inline script terminator')
        assets.append({'path':str(p.relative_to(ROOT)),'sha256':digest(p.read_bytes())})
        return '<script>'+raw+'</script>'
    body=re.sub(r'<script src="([^"]+)"></script>',inline,body)
    packs=[{'name':name,'source':rel,'sha256':digest((ROOT/rel).read_bytes()),'base64':base64.b64encode((ROOT/rel).read_bytes()).decode()} for name,rel in PACKS.items()]
    downloads='''<section id="portable-downloads"><h2>Two public originals — save without renaming collisions</h2><p>This one-file offline bundle needs no clone, installation or server. Save each original below, then import them in Compare two captures. Original public evidence bytes may retain historical lab paths; they are not reusable instructions. Only the public 8 and 15 November packs are included; later private video evidence is NOT included or authorized for access. Select historical analysis explicitly for expired saved observations. Integrity checks are unchanged.</p><div id="public-download-buttons"></div></section>'''
    body=body.replace('<section aria-labelledby="import-title">',downloads+'<section aria-labelledby="import-title">')
    helper='globalThis.CANopyPublicDownloads='+json.dumps(packs,separators=(',',':'))+''';for(const pack of CANopyPublicDownloads){const button=document.createElement('button');button.textContent='Save '+pack.name;button.addEventListener('click',()=>{const bytes=Uint8Array.from(atob(pack.base64),c=>c.charCodeAt(0));const url=URL.createObjectURL(new Blob([bytes],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=pack.name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});document.getElementById('public-download-buttons').append(button);}'''
    body=body.replace('</body>','<script>'+helper+'</script></body>')
    body=re.sub(r'<a href="../../docs/[^"]+">([^<]+)</a>',r'<span>\1 (see repository documentation separately)</span>',body)
    scripts=re.findall(r'<script>(.*?)</script>',body,re.S)
    hashes=lambda raws:' '.join("'sha256-"+base64.b64encode(hashlib.sha256(raw.encode()).digest()).decode()+"'" for raw in raws)
    policy="default-src 'none'; script-src "+hashes(scripts)+"; style-src "+hashes([css])+"; connect-src 'none'; img-src 'none'; base-uri 'none'; form-action 'none'"
    body=re.sub(r'content="default-src [^"]+"','content="'+policy+'"',body,count=1)
    raw=body.encode();manifest={'kind':'canopy-offline-desk-v1','scope':'HOST offline viewer; no SDK, native execution, private pack, upload or live connection','bundle':'canopy-incident-desk.html','sha256':digest(raw),'pack_files':[{k:v for k,v in p.items() if k!='base64'} for p in packs],'script_sources':assets}
    return {ROOT/'docs/downloads/canopy-incident-desk.html':raw,ROOT/'docs/downloads/manifest.json':(json.dumps(manifest,indent=2)+chr(10)).encode()}
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    for path,raw in build().items():
        if args.check:
            if not path.exists() or path.read_bytes()!=raw:raise SystemExit('FAIL: stale portable desk '+str(path.relative_to(ROOT)))
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    print('PASS: deterministic one-file offline desk; two public originals only')
if __name__=='__main__':main()
