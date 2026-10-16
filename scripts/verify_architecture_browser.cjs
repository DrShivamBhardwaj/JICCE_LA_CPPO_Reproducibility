// Real-browser layout and interaction checks; executable supplied by environment.
const fs=require('fs'),path=require('path'),assert=require('assert');
const {chromium}=require((process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES?process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES+'/':'')+'playwright');
(async()=>{const root=path.resolve(__dirname,'..'),out=path.join(root,'outputs/browser_validation');fs.mkdirSync(out,{recursive:true});const browser=await chromium.launch({executablePath:process.env.BROWSER_EXECUTABLE||undefined,args:['--no-sandbox','--disable-dev-shm-usage','--disable-gpu','--no-zygote'],headless:true});const report={browser:await browser.version(),checks:[],errors:[]};
for(const width of [320,736,1024])for(const theme of ['light','dark']){
 const page=await browser.newPage({viewport:{width,height:700},colorScheme:theme});page.on('pageerror',e=>report.errors.push(e.message));await page.goto('file://'+path.join(root,'publication/redesigned/interactive_architecture.html'));const frame=page.frameLocator('iframe');await frame.locator('#routing-stage').waitFor();for(const mode of ['prototype','frozen']){await frame.locator('#routing-mode').selectOption(mode);const details=[];
 for(let i=0;i<6;i++){
  await frame.locator('#routing-stage').selectOption(String(i));const bounds=await frame.locator('#routing-feedback-architecture').evaluate(root=>{const svg=root.querySelector('svg'),nodes=[...svg.querySelectorAll('rect.node')],texts=[...svg.querySelectorAll('text')];return {scroll:document.documentElement.scrollWidth,viewport:innerWidth,active:nodes.filter(x=>x.classList.contains('active')).length,overflow:texts.map((t,j)=>{const a=t.getBBox(),b=nodes[Math.floor(j/2)].getBBox();return a.x<b.x-1||a.x+a.width>b.x+b.width+1?t.textContent:null;}).filter(Boolean)};});
  assert.equal(bounds.active,1);assert(bounds.scroll<=bounds.viewport,'horizontal overflow');assert.equal(bounds.overflow.length,0,'node text overflow at '+width+': '+bounds.overflow.join(', '));details.push(await frame.locator('#routing-detail').innerText());
 }
 assert.equal(new Set(details).size,6);await page.screenshot({path:path.join(out,`architecture_${mode}_${width}_${theme}.png`),fullPage:true});report.checks.push({mode,width,theme,selections:6,overflow:false});}await page.close();
}
assert.equal(report.errors.length,0);report.status='passed';fs.writeFileSync(path.join(out,'verification.json'),JSON.stringify(report,null,2));await browser.close();console.log(JSON.stringify(report));})().catch(e=>{console.error(e);process.exit(1)});
