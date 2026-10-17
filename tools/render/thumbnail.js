// Thumbnail renderer: node thumbnail.js <photo> <out.png> <w> <h> <crop x0,y0,x1,y1 (fractions)> <layout h|v>
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const path = require('path');
const [photo, out, W, H, crop, layout] = process.argv.slice(2);
const ROOT = path.resolve(__dirname, '../..');
const [x0, y0, x1, y1] = crop.split(',').map(Number);
(async () => {
  const b = await chromium.launch({ args: ['--allow-file-access-from-files', '--font-render-hinting=none'] });
  const p = await b.newPage({ viewport: { width: +W, height: +H } });
  const horiz = layout === 'h';
  const html = (`<html><head><style>
    @font-face{font-family:R;src:url(file://${ROOT}/brand/fonts/ReadexPro[HEXP,wght].ttf);unicode-range:U+0000-065F,U+066A-10FFFF}
    @font-face{font-family:R;src:url(file://${ROOT}/brand/fonts/IBMPlexSansArabic-Bold.ttf);unicode-range:U+0660-0669}
    html,body{margin:0;direction:ltr;width:${W}px;height:${H}px;overflow:hidden;background:#0B0E13}
    .ph{position:absolute;inset:0;background:url(file://${photo});background-size:${100 / (x1 - x0)}% ${100 / (y1 - y0)}%;
        background-position:${x0 / (1 - (x1 - x0)) * 100}% ${y0 / (1 - (y1 - y0)) * 100}%;filter:contrast(1.08) saturate(1.05)}
    .sh{position:absolute;inset:0;background:${horiz
      ? 'linear-gradient(270deg, rgba(11,14,19,.92) 0%, rgba(11,14,19,.75) 30%, rgba(11,14,19,0) 58%)'
      : 'linear-gradient(0deg, rgba(11,14,19,.95) 0%, rgba(11,14,19,.7) 30%, rgba(11,14,19,0) 55%)'}}
    .t{position:absolute;direction:rtl;color:#F2EFE9;font:700 ${horiz ? 150 : 190}px/1.08 R;font-variation-settings:'wght' 800;
       text-shadow:0 6px 30px rgba(0,0,0,.6); ${horiz ? 'right:56px;top:170px;text-align:right' : 'left:0;right:0;bottom:240px;text-align:center'}}
    .t b{color:#E9A13B;font-weight:inherit}
    .bar{position:absolute;left:0;right:0;bottom:0;height:10px;background:#E9A13B}
  </style></head><body><div class=ph></div><div class=sh></div>
  <div class=t><b>٦٩</b> يومًا<br>تحت الأرض</div><div class=bar></div></body></html>`);
  const tmp = out.replace(/\.png$/, '.html'); require('fs').writeFileSync(tmp, html);
  await p.goto('file://' + tmp);
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(300);
  await p.screenshot({ path: out });
  await b.close(); require('fs').unlinkSync(tmp);
})();
