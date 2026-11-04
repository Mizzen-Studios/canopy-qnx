const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const path=require('node:path');
const fs=require('node:fs');
const evidence=process.env.REPLAY_EVIDENCE_DIR;
if(!evidence)throw Error('Set REPLAY_EVIDENCE_DIR outside the repository (binary-free SDK guard)');
fs.mkdirSync(evidence,{recursive:true});
const {pathToFileURL}=require('node:url');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH||undefined,args:['--no-sandbox']});
 try {
  const page=await browser.newPage({viewport:{width:1920,height:1080},reducedMotion:'reduce'});
  const errors=[],requests=[];page.on('pageerror',e=>errors.push(String(e)));page.on('request',r=>{if(/^https?:/.test(r.url()))requests.push(r.url());});
  await page.goto(pathToFileURL(path.resolve('docs/replay/index.html')).href);
  await page.waitForFunction(()=>document.querySelector('#speed').textContent!=='—');
  assert.equal(await page.locator('#clock').textContent(),'0 ms');
  await page.locator('body').click({position:{x:5,y:5}});
  await page.keyboard.press('ArrowRight');assert.equal(await page.locator('#clock').textContent(),'10 ms');
  await page.keyboard.press('End');assert.equal(await page.locator('#clock').textContent(),'6000 ms');
  await page.keyboard.press('Home');await page.keyboard.press('i');assert.equal(await page.locator('#record').isVisible(),false);
  await page.keyboard.press('i');assert.equal(await page.locator('#record').isVisible(),true);
  await page.keyboard.press('Space');await page.waitForTimeout(150);await page.keyboard.press('Space');assert.notEqual(await page.locator('#clock').textContent(),'0 ms');
  await page.locator('#rate').selectOption('0.25');
  await page.locator('#seek').fill('250');assert.equal(await page.locator('#clock').textContent(),'2500 ms');
  await page.locator('#events button').filter({hasText:'4000 ms obstacle-start'}).click();assert.equal(await page.locator('#inputs').textContent(),'1 m / 10 m/s');
  await page.locator('#file').setInputFiles(path.resolve('docs/replay/run.jsonl'));await page.waitForFunction(()=>document.querySelector('#message').textContent.startsWith('Local host'));
  await page.locator('#seek').fill('100');
  await page.locator('#file').setInputFiles({name:'invalid.jsonl',mimeType:'text/plain',buffer:Buffer.from('{}')});
  await page.waitForFunction(()=>document.querySelector('#message').textContent.includes('Previous replay retained'));
  assert.equal(await page.locator('#clock').textContent(),'1000 ms');
  if(process.env.REPLAY_LIVE_FILE){
   const live=process.env.REPLAY_LIVE_FILE;
   await page.locator('#file').setInputFiles(live);
   await page.waitForFunction(()=>document.querySelector('#message').textContent.includes('HOST VCAN live SocketCAN'));
   assert.match(await page.locator('.truth').textContent(),/HOST VCAN/);
   assert.match(await page.locator('.strip').first().textContent(),/Recorded Linux SocketCAN/);
   const bad=fs.readFileSync(live,'utf8').trim().split('\n').map(x=>JSON.parse(x));bad[0].clock='logical-ms';
   await page.locator('#file').setInputFiles({name:'bad-live.jsonl',mimeType:'text/plain',buffer:Buffer.from(bad.map(x=>JSON.stringify(x)).join('\n'))});
   await page.waitForFunction(()=>document.querySelector('#message').textContent.includes('Previous replay retained'));
   assert.match(await page.locator('.truth').textContent(),/HOST VCAN/);
  }
  await page.locator('#sample').click();assert.equal(await page.locator('#clock').textContent(),'0 ms');
  await page.locator('#events button').filter({hasText:'590 ms watchdog-held'}).click();
  assert.equal(await page.locator('#watchdog').textContent(),'Held');
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollHeight<=innerHeight),true);
  await page.screenshot({path:path.join(evidence,'host-hero-1920.png'),fullPage:true});
  await page.setViewportSize({width:390,height:844});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await page.screenshot({path:path.join(evidence,'host-hero-mobile.png'),fullPage:true});
  assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);
  console.log('PASS: Chromium offline load, keyboard, playback, rate, scrub, event jump, file picker, invalid retention, reset, desktop/mobile, no network or JS errors');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
