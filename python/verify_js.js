/* Cross-check the JavaScript model in web/ballistics.html against the Python
   reference implementation. Renders the page, sweeps barrel length, and dumps
   JSON to stdout for compare_js_py.py. Also screenshots each tab. */
const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await browser.newPage({ viewport: { width: 1600, height: 1100 }, deviceScaleFactor: 2 });
  const errors = [];
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()); });

  const file = 'file://' + path.resolve(__dirname, '../web/ballistics.html');
  await page.goto(file, { waitUntil: 'load' });
  await page.waitForTimeout(1200);

  const out = await page.evaluate(() => {
    const Ls = [5, 7, 7.5, 8, 9, 10.3, 10.5, 11.5, 12.5, 14.5, 16, 18, 20, 22, 24, 26];
    const rows = Ls.map(L => {
      const c = build(Object.assign({}, P, { L_bbl: L, dt: 0.1 }));
      const r = simulate(c, { keep: false });
      const E = energyBudget(c, r);
      return {
        L, v: r.v, pBase: r.pBase, pMean: r.pMean, pBreech: r.pBreech,
        peak: r.peak, tExit: r.tExit, psi: r.psi, T: r.T, closure: E.closure
      };
    });
    const c = build(Object.assign({}, P, { dt: 0.1 }));
    return { rows, meta: { phi: c.phi, zeta: c.zeta, A: c.A, L0: c.L0,
                           chi: c.chi, lam: c.lam, dens: c.dens, pack: c.pack } };
  });

  // screenshots
  const shots = [];
  for (const tab of ['shot', 'sweep', 'energy']) {
    await page.click(`[data-tab="${tab}"]`);
    await page.waitForTimeout(700);
    const f = path.resolve(__dirname, `../doc/screen_${tab}.png`);
    await page.screenshot({ path: f, fullPage: tab !== 'shot' });
    shots.push(f);
  }
  // a dark-mode shot of the sweep tab
  await page.click('#theme');
  await page.waitForTimeout(600);
  await page.click('[data-tab="shot"]');
  await page.waitForTimeout(700);
  await page.screenshot({ path: path.resolve(__dirname, '../doc/screen_dark.png') });

  console.log(JSON.stringify({ errors, shots, ...out }, null, 1));
  await browser.close();
})();
