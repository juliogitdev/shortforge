// shortforge 3D renderer: node render3d.js PLAN.json OUT_DIR [START_FRAME END_FRAME] | --still t1,t2,...
// Renders the "shots" of a plan with three.js in headless Chromium (SwiftShader) and writes JPEG frames.
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
const args = process.argv.slice(2);
const planPath = path.resolve(args[0]); const out = path.resolve(args[1]);
const plan = JSON.parse(fs.readFileSync(planPath, 'utf8')); const base = 'file://' + path.dirname(planPath) + '/';
const FPS = 30, total = Math.round(plan.duration * FPS);
let list;
if (args[2] === '--still') list = args[3].split(',').map(Number);
else { const a = +(args[2] || 0), b = +(args[3] || total); list = [...Array(b - a).keys()].map(i => (a + i) / FPS); }
(async () => {
  const br = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--allow-file-access-from-files'] });
  const p = await br.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('pageerror', e => console.log('PAGEERR', e.message)); p.on('console', m => { if (m.type() === 'error') console.log('ERR', m.text()); });
  await p.addInitScript(([pl, b]) => { window.PLAN = pl; window.PLAN_BASE = b; }, [plan, base]);
  await p.goto('file://' + path.join(__dirname, 'scene.html'));
  await p.waitForFunction('window.ready === true && window.assetsLoaded === true', null, { timeout: 60000 });
  fs.mkdirSync(out, { recursive: true });
  for (const T of list) {
    await p.evaluate(T => window.renderAt(T), T);
    const data = await p.evaluate(() => document.querySelector('canvas').toDataURL('image/jpeg', 0.92));
    const name = args[2] === '--still' ? `s_${T.toFixed(2)}.jpg` : `f_${String(Math.round(T * FPS)).padStart(5, '0')}.jpg`;
    fs.writeFileSync(path.join(out, name), Buffer.from(data.split(',')[1], 'base64'));
  }
  await br.close();
})().catch(e => { console.error(e); process.exit(1); });
