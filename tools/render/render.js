// Render a timeline page to video with headless Chromium.
// usage: node render.js <timeline.js> <out.mp4> [--workers 3] [--from s] [--to s] [--fps 30] [--stills t1,t2,...] [--gfx a,b]
const fs = require('fs'), path = require('path'), { spawn } = require('child_process');
const { chromium } = require('/opt/node-tools/node_modules/playwright');

const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf('--' + k); return i >= 0 ? args[i + 1] : d; };
const tlPath = path.resolve(args[0]), out = path.resolve(args[1]);
const FPS = +opt('fps', 30), WORKERS = +opt('workers', 3);
const HERE = __dirname, ROOT = path.resolve(HERE, '../..');

function buildPage() {
  let html = fs.readFileSync(path.join(HERE, 'engine.html'), 'utf8');
  html = html.split('../../brand/').join('file://' + ROOT + '/brand/');
  html = html.replace('TIMELINE_JS', 'file://' + tlPath);
  const gdir = path.join(HERE, 'graphics');
  const only = opt('gfx', null);   // --gfx a,b : include only these modules (isolated testing)
  const files = fs.readdirSync(gdir).filter(f => f.endsWith('.js') && f !== 'common.js')
    .filter(f => !only || only.split(',').includes(f.replace(/\.js$/, ''))).sort();
  html = html.replace('GRAPHICS_SCRIPTS', files.map(f => `<script src="file://${gdir}/${f}"></script>`).join('\n'));
  html = html.replace('src="graphics/common.js"', `src="file://${gdir}/common.js"`);
  html = html.replace('src="engine.js"', `src="file://${HERE}/engine.js"`);
  const page = path.join(path.dirname(tlPath), '_page.html');
  fs.writeFileSync(page, html);
  return page;
}

async function openPage(browser, pageFile) {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('pageerror', e => console.error('PAGE ERROR', e.message));
  page.on('console', m => { if (m.type() === 'error') console.error('console:', m.text()); });
  await page.goto('file://' + pageFile);
  await page.waitForFunction(() => window.ENGINE_READY !== undefined);
  await page.evaluate(() => window.ENGINE_READY);
  const cdp = await page.context().newCDPSession(page);
  return { page, cdp };
}

async function shot(p, t, fmt = 'jpeg') {
  await p.page.evaluate(t => window.renderFrame(t), t);
  const r = await p.cdp.send('Page.captureScreenshot', fmt === 'png' ? { format: 'png' } : { format: 'jpeg', quality: 95 });
  return Buffer.from(r.data, 'base64');
}

async function renderChunk(browser, pageFile, f0, f1, file) {
  const p = await openPage(browser, pageFile);
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '12', '-pix_fmt', 'yuv420p', '-r', String(FPS), file], { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  for (let f = f0; f < f1; f++) {
    const buf = await shot(p, f / FPS);
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if ((f - f0) % 150 === 0) console.log(`  [${path.basename(file)}] frame ${f}/${f1} (${((Date.now() - t0) / Math.max(1, f - f0 + 1)).toFixed(0)} ms/f)`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await p.page.close();
}

(async () => {
  const pageFile = buildPage();
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files', '--disable-web-security', '--font-render-hinting=none', '--disable-gpu', '--force-color-profile=srgb'] });
  const stills = opt('stills', null);
  if (stills) {   // contact frames for review
    const p = await openPage(browser, pageFile);
    fs.mkdirSync(out, { recursive: true });
    for (const t of stills.split(',').map(Number)) {
      fs.writeFileSync(path.join(out, `t${t.toFixed(2).padStart(7, '0')}.png`), await shot(p, t, 'png'));
    }
    await browser.close(); return;
  }
  const TLsrc = fs.readFileSync(tlPath, 'utf8');
  const dur = +(/"duration":\s*([\d.]+)/.exec(TLsrc)[1]);
  const fromS = +opt('from', 0), toS = +opt('to', dur);
  const F0 = Math.round(fromS * FPS), F1 = Math.round(toS * FPS);
  const n = Math.max(1, Math.min(WORKERS, Math.ceil((F1 - F0) / 60)));
  const step = Math.ceil((F1 - F0) / n);
  const parts = [];
  const jobs = [];
  for (let i = 0; i < n; i++) {
    const a = F0 + i * step, b = Math.min(F1, a + step);
    if (a >= b) break;
    const file = out.replace(/\.mp4$/, `.part${i}.mp4`); parts.push(file);
    jobs.push(renderChunk(browser, pageFile, a, b, file));
  }
  await Promise.all(jobs);
  await browser.close();
  const list = out.replace(/\.mp4$/, '.parts.txt');
  fs.writeFileSync(list, parts.map(p => `file '${p}'`).join('\n'));
  await new Promise(r => spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', out], { stdio: 'inherit' }).on('close', r));
  parts.forEach(p => fs.unlinkSync(p)); fs.unlinkSync(list);
  console.log('wrote', out);
})();
