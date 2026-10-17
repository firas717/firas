const { chromium } = require('/opt/node-tools/node_modules/playwright');
(async () => {
  const browser = await chromium.launch({ args: ['--font-render-hinting=none', '--disable-gpu'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.setContent(`<html><head><style>
   @font-face{font-family:Readex;src:url(file:///home/user/firas/brand/fonts/ReadexPro[HEXP,wght].ttf)}
   @font-face{font-family:Plex;src:url(file:///home/user/firas/brand/fonts/IBMPlexSansArabic-Medium.ttf)}
   html,body{margin:0;background:#0B0E13;direction:ltr} body *{direction:rtl}
   .big{position:absolute;top:500px;width:100%;text-align:center;font:800 330px Readex;color:#E9A13B}
   .cap{position:absolute;top:1250px;left:120px;width:840px;text-align:center;font:500 67px/1.35 Plex;color:#fff;text-shadow:0 2px 10px rgba(0,0,0,.75)}
  </style></head><body><div class=big id=b>٣٣</div><div class=cap id=c>في عام ٢٠١٠، اختفى ٣٣ عاملًا داخل منجم في تشيلي</div></body></html>`);
  await page.evaluate(() => document.fonts.ready);
  const cdp = await page.context().newCDPSession(page);
  const t0 = Date.now(); let n = 30;
  for (let i = 0; i < n; i++) {
    await page.evaluate((i) => { document.getElementById('b').style.transform = `translateY(${i}px)`; }, i);
    const r = await cdp.send('Page.captureScreenshot', { format: 'jpeg', quality: 92 });
    if (i == 0) require('fs').writeFileSync('bench.jpg', Buffer.from(r.data, 'base64'));
  }
  console.log('ms/frame', (Date.now() - t0) / n);
  await browser.close();
})();
