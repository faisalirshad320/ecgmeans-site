// Renders 1200x630 social images for every page listed in og_pages.json
const { chromium } = require('playwright'); const fs=require('fs'); const path=require('path');
(async()=>{
 const root=__dirname, out=path.join(root,'site','assets','og'); fs.mkdirSync(out,{recursive:true});
 const pages=JSON.parse(fs.readFileSync(path.join(root,'og_pages.json')));
 const b=await chromium.launch(); const p=await b.newPage({viewport:{width:1200,height:630}});
 for(const [slug,title] of pages){
  const svg=path.join(root,'site','assets','ecg',slug+'.svg');
  const strip=fs.existsSync(svg)?`<img src="data:image/svg+xml;base64,${fs.readFileSync(svg).toString('base64')}" style="width:100%;max-height:250px;object-fit:contain;object-position:left;border-radius:10px;border:1px solid #f1d4d6">`:'';
  const esc=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;');
  const html=`<html><body style="margin:0;width:1200px;height:630px;font-family:Arial,Helvetica,sans-serif;background:#fff;display:flex;flex-direction:column">
  <div style="height:14px;background:#b91c1c"></div>
  <div style="padding:40px 60px 0;display:flex;align-items:center;gap:16px"><svg width="56" height="56" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#b91c1c"/><path d="M6 36h12l6-16 8 30 8-22 4 8h14" fill="none" stroke="#fff" stroke-width="5" stroke-linejoin="round" stroke-linecap="round"/></svg><span style="font-size:32px;font-weight:800;color:#1a1a1a">ECG Means</span></div>
  <div style="padding:22px 60px 0;font-size:${title.length>48?50:60}px;font-weight:800;line-height:1.12;color:#111827">${esc(title)}</div>
  <div style="padding:22px 60px 0;flex:1;display:flex;align-items:flex-start">${strip}</div>
  <div style="padding:0 60px 30px;font-size:24px;color:#595f6b">Plain-English ECG explanations · Reviewed by Dr. Faisal Irshad, MBBS</div></body></html>`;
  await p.setContent(html,{waitUntil:'load'}); await p.screenshot({path:path.join(out,slug+'.png'),type:'png'});
 }
 await b.close(); console.log('og images:',pages.length);
})();
