// Navegador aislado, imágenes generadas y respuestas simuladas. Sin inferencia.
const { chromium } = require(process.env.WALMART_PLAYWRIGHT || 'playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../..');
const work = path.join(root, '.tmp/cliente_alertas_20261111');
fs.mkdirSync(work, { recursive: true });
const html = fs.readFileSync(path.join(root, 'Aplicacion_Cliente/interfaz_cliente.html'), 'utf8');

(async () => {
  const browser = await chromium.launch({
    executablePath: process.env.WALMART_CHROMIUM || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    headless: true,
  });
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    const fixture = await page.evaluate(() => {
      const canvas = document.createElement('canvas');
      canvas.width = 800; canvas.height = 600;
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = '#c3c9cd'; ctx.fillRect(0, 0, 800, 600);
      for (let row = 0; row < 3; row++) {
        ctx.fillStyle = '#717b84'; ctx.fillRect(30, 35 + row * 180, 740, 150);
        for (let col = 0; col < (row === 2 ? 3 : 9); col++) {
          ctx.fillStyle = ['#cba75d', '#7a9c7e', '#8eabc0'][row];
          ctx.fillRect(45 + col * 76, 80 + row * 180, 54, 100);
        }
        ctx.fillStyle = '#e1e6ea'; ctx.fillRect(30, 185 + row * 180, 740, 12);
      }
      return canvas.toDataURL('image/png');
    });
    const det = (id, state, pct) => ({
      id, display_polygon: [[30, 365 - (id - 1) * 180], [770, 365 - (id - 1) * 180],
        [770, 545 - (id - 1) * 180], [30, 545 - (id - 1) * 180]],
      occupancy_estimate: { pct, state }, occupancy: { max_gap_pct: state === 'reponer' ? 65 : 10 },
      // Texto antiguo deliberado: tampoco debe reaparecer en sesiones recuperadas.
      store_diagnosis: { operational_state: state, operational_label: 'Reponer',
        headline: 'Reponer frente completo', action: 'Registrar reposición' },
    });
    const predictions = [
      [det(1, 'reponer', 25), det(2, 'revisar', null), det(3, 'suficiente', 80)],
      [det(1, 'suficiente', 90)], [det(1, 'revisar', null)], [],
    ];
    let predictionsSent = 0;
    await page.route('http://127.0.0.1:19099/**', route => {
      const pathname = new URL(route.request().url()).pathname;
      if (pathname === '/api/health') return route.fulfill({ json: { status: 'ok', analysis_ready: true } });
      if (pathname === '/logo.svg' || pathname === '/favicon.svg') return route.fulfill({
        contentType: 'image/svg+xml', body: fs.readFileSync(path.join(root, 'Aplicacion_Cliente/logo.svg')),
      });
      if (pathname === '/api/predict') return route.fulfill({ json: {
        width: 800, height: 600, image_url: fixture, detections: predictions[predictionsSent++],
      } });
      return route.fulfill({ contentType: 'text/html', body: html });
    });
    await page.goto('http://127.0.0.1:19099/');
    await page.evaluate(() => storageReady);
    await page.screenshot({ path: path.join(work, 'vacio.png'), animations: 'disabled' });
    const png = Buffer.from(fixture.split(',')[1], 'base64');
    await page.locator('#fileInput').setInputFiles(['mixta', 'sin_alertas', 'ambigua', 'sin_niveles'].map(name => ({
      name: `${name}.png`, mimeType: 'image/png', buffer: png,
    })));
    await page.waitForFunction(() => state.items.length === 4 && state.items.every(item => item.result));
    await page.evaluate(() => saveChain);
    const initial = await page.evaluate(() => ({
      results: JSON.stringify(state.items.map(item => { const { image_url, ...result } = item.result; return result; })),
      order: visibleItems().map(item => item.id),
      selected: state.selectedId,
    }));
    async function selected() { return page.evaluate(() => state.selectedId); }
    await page.evaluate(() => document.activeElement.blur());
    await page.keyboard.press('ArrowLeft');
    assert.equal(await selected(), initial.order[0]);
    for (const id of initial.order.slice(1)) {
      await page.keyboard.press('ArrowRight'); assert.equal(await selected(), id);
    }
    await page.keyboard.press('ArrowRight'); assert.equal(await selected(), initial.order.at(-1));
    await page.keyboard.press('ArrowLeft'); assert.equal(await selected(), initial.order.at(-2));
    await page.locator('#prevGondolaBtn').click(); assert.equal(await selected(), initial.order[1]);
    await page.locator('#nextGondolaBtn').click(); assert.equal(await selected(), initial.order[2]);
    await page.evaluate(() => {
      const sel = document.createElement('select'); sel.id = 'keyboardSelectTest';
      sel.add(new Option('a', 'a')); document.body.append(sel); sel.focus();
    });
    await page.keyboard.press('ArrowLeft'); assert.equal(await selected(), initial.order[2]);
    await page.evaluate(() => $('keyboardSelectTest').remove());
    await page.evaluate(() => {
      const field = document.createElement('input'); field.id = 'keyboardTest';
      field.value = 'texto'; document.body.append(field); field.focus();
    });
    await page.keyboard.press('ArrowRight'); assert.equal(await selected(), initial.order[2]);
    await page.evaluate(() => {
      const field = document.createElement('div'); field.id = 'keyboardTest';
      field.contentEditable = 'true'; field.textContent = 'texto';
      $('keyboardTest').replaceWith(field); field.focus();
    });
    await page.keyboard.press('ArrowLeft'); assert.equal(await selected(), initial.order[2]);
    await page.evaluate(() => $('keyboardTest').remove());
    await page.locator('[data-view="original"]').focus();
    await page.keyboard.press('ArrowRight'); assert.equal(await selected(), initial.order[2]);
    await page.evaluate(() => { document.activeElement.blur(); $('cameraModal').hidden = false; });
    await page.keyboard.press('ArrowRight'); assert.equal(await selected(), initial.order[2]);
    await page.evaluate(() => { $('cameraModal').hidden = true; $('moreActions').open = true; });
    await page.keyboard.press('ArrowRight'); assert.equal(await selected(), initial.order[2]);
    await page.evaluate(() => $('moreActions').open = false);
    await page.keyboard.press('Control+ArrowRight'); assert.equal(await selected(), initial.order[2]);
    await page.locator('[data-filter="verificar"]').click();
    const filtered = await page.evaluate(() => visibleItems().map(item => item.id));
    await page.keyboard.press('ArrowRight'); assert.equal(await selected(), filtered[1]);
    await page.keyboard.press('ArrowRight'); assert.equal(await selected(), filtered[1]);
    await page.keyboard.press('ArrowLeft'); assert.equal(await selected(), filtered[0]);
    await page.locator('[data-filter="all"]').click();
    assert.deepEqual(await page.evaluate(() => visibleItems().map(item => effectiveGondolaState(item))),
      ['reponer', 'verificar', 'verificar', 'suficiente']);
    await page.evaluate(id => selectItem(id), initial.selected);
    async function unchanged() {
      assert.deepEqual(await page.evaluate(() => [
        ...['countAll', 'countReponer', 'countVerificar', 'countSuficiente'].map(id => $(id).textContent),
      ]), ['4', '1', '2', '1']);
      assert.equal(await page.evaluate(() => JSON.stringify(state.items.map(item => {
        const { image_url, ...result } = item.result; return result;
      }))), initial.results);
      assert.equal(await page.locator('#stagePill').innerText(), '1 nivel con alerta');
      assert.equal(await page.locator('[data-level="1"] .status-pill').innerText(), 'Alerta por baja disponibilidad');
    }
    await unchanged();
    assert.equal(await page.locator('[data-level="2"] .status-pill').innerText(), 'No evaluable');
    assert.equal(await page.locator('[data-level="2"] .front-coverage').innerText(), 'Frente cubierto sin lectura');
    await page.locator('[data-filter="reponer"]').click();
    for (const action of ['revisado', 'no_evaluable', 'pendiente']) {
      await page.locator(`[data-quick-level="1"][data-action="${action}"]`).click();
      await unchanged();
      assert.equal(await page.locator('.queue-item').count(), 1);
    }
    await page.locator('[data-level="1"] summary').click();
    await page.locator('[data-review-level="1"]').selectOption('sin_alerta');
    await unchanged();
    await page.evaluate(() => saveChain);
    await page.reload(); await page.evaluate(() => storageReady);
    await unchanged();
    assert.equal(await page.evaluate(() => state.items[0].reviews[1].value), 'sin_alerta');
    // Marcas de sesiones anteriores se conservan pero no ocultan alertas.
    await page.evaluate(async () => {
      const item = state.items[0];
      item.replenished = { 1: '12:00', 2: '12:01', 3: '12:02' };
      item.reviews = { 1: { value: 'confirmado', at: 'anterior' }, 2: { value: 'necesita', at: 'anterior' } };
      saveSession(item.id); await saveChain;
    });
    await page.reload(); await page.evaluate(() => storageReady);
    await unchanged();
    assert.deepEqual(await page.evaluate(() => state.items[0].replenished), { 1: '12:00', 2: '12:01', 3: '12:02' });
    assert.deepEqual(await page.evaluate(() => visibleItems().map(item => item.id)), initial.order);
    const downloadPending = page.waitForEvent('download');
    await page.locator('#exportCsvBtn').click();
    const download = await downloadPending;
    const chunks = []; for await (const chunk of await download.createReadStream()) chunks.push(chunk);
    const csv = Buffer.concat(chunks).toString('utf8');
    assert.match(download.suggestedFilename(), /^alertas_pasillo_/);
    assert.match(csv, /Resultado del análisis/); assert.match(csv, /Revisión humana/);
    assert.match(csv, /Con alertas/); assert.match(csv, /Confirmación visual anterior/);
    assert.match(csv, /No se detectaron niveles/);
    assert.doesNotMatch(csv, /Reposición|Repuesto|Reponer|Estado Reposición/);
    assert.equal(csv.trim().split('\r\n').length, 7);
    await page.locator('[data-filter="suficiente"]').click();
    assert.equal(await page.locator('.queue-item').count(), 1);
    assert.equal(await page.locator('#stagePill').innerText(), 'Sin alertas');
    await page.locator('[data-filter="verificar"]').click();
    assert.equal(await page.locator('.queue-item').count(), 2);
    await page.locator('.queue-item').last().click();
    assert.match(await page.locator('#levelsList').innerText(), /No se detectaron niveles/);
    assert.equal(await page.locator('#stagePill').innerText(), 'Requiere revisión');
    await page.locator('[data-filter="all"]').click();
    await page.evaluate(id => selectItem(id), initial.selected);
    assert.doesNotMatch(await page.locator('body').innerText(), /Repuesto|Reposición|Por reponer|Sin pendientes/);
    assert.deepEqual(await page.evaluate(() => [
      analysisState({ occupancy_estimate: { state: 'suficiente', pct: null } }),
      analysisState({ occupancy_estimate: { state: 'reponer', pct: NaN } }),
      analysisState({ occupancy_estimate: { state: 'desconocido', pct: 90 } }),
    ]), ['revisar', 'revisar', 'revisar']);
    // Comprobar las cinco vistas y los 3 pasos en móvil (Góndolas, Foto, Plan).
    for (const [name, width, height, theme] of [
      ['escritorio', 1440, 900, 'dark'], ['escritorio_claro', 1440, 900, 'light'],
      ['tablet', 1024, 768, 'dark'], ['movil', 390, 844, 'dark'], ['movil_estrecho', 320, 740, 'dark'],
    ]) {
      await page.setViewportSize({ width, height });
      await page.evaluate(theme => setTheme(theme), theme);
      const navVisible = await page.locator('#mobileSteps').isVisible();
      if (width <= 700) {
        assert.equal(navVisible, true, `Navegación móvil visible en ${name}`);
        assert.equal(await page.locator('#cameraBtn').isVisible(), true, `Tomar foto visible en ${name}`);
        assert.equal(await page.locator('#exportCsvBtn').isVisible(), false, `Exportar CSV fuera de barra en ${name}`);
        assert.equal(await page.locator('.top-actions > label[for="fileInput"]').isVisible(), false, `Subir fotos fuera de barra en ${name}`);
        for (const [step, activeSelector, hiddenSelectors] of [
          ['queue', '.queue-panel', ['.stage-panel', '.plan-panel']],
          ['stage', '.stage-panel', ['.queue-panel', '.plan-panel']],
          ['plan', '.plan-panel', ['.queue-panel', '.stage-panel']],
        ]) {
          await page.locator(`#mobileSteps [data-mobile-step="${step}"]`).click();
          assert.equal(await page.locator(activeSelector).isVisible(), true, `${activeSelector} visible en ${name}/${step}`);
          for (const hiddenSel of hiddenSelectors) {
            assert.equal(await page.locator(hiddenSel).isVisible(), false, `${hiddenSel} oculto en ${name}/${step}`);
          }
          assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, `${name}/${step}`);
          if (step === 'stage') {
            assert.equal(await page.locator('#stageToolbar').isVisible(), false, `Toolbar oculta en ${name}/${step}`);
          }
          if (step === 'plan') {
            const overflow = await page.locator('.level-top').evaluateAll(nodes => nodes.some(node => node.scrollWidth > node.clientWidth));
            assert.equal(overflow, false, `Las etiquetas deben caber: ${name}/${step}`);
          }
          await page.screenshot({ path: path.join(work, `${name}_${step}.png`), fullPage: true, animations: 'disabled' });
        }
        await page.locator('#mobileSteps [data-mobile-step="queue"]').click();
        await page.locator('.queue-item').first().click();
        assert.equal(await page.locator('.stage-panel').isVisible(), true, `Tocar góndola avanza a Foto en ${name}`);
        await page.locator('#mobileSteps [data-mobile-step="queue"]').click();
      } else {
        assert.equal(navVisible, false, `Navegación móvil oculta en ${name}`);
        await page.screenshot({ path: path.join(work, `${name}.png`), fullPage: true, animations: 'disabled' });
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, name);
        const overflow = await page.locator('.level-top').evaluateAll(nodes => nodes.some(node => node.scrollWidth > node.clientWidth));
        assert.equal(overflow, false, `Las etiquetas deben caber: ${name}`);
      }
    }
    assert.equal(predictionsSent, 4, 'Las revisiones y recargas no deben volver a inferir');
    // Borrado atómico, revocación de URLs y reintento cuando IndexedDB falla.
    const photoCount = () => page.evaluate(() => new Promise((resolve, reject) => {
      const request = db.transaction('photos').objectStore('photos').count();
      request.onsuccess = () => resolve(request.result); request.onerror = () => reject(request.error);
    }));
    // Una sesión v2 antigua puede conservar fotos solo para deshacer: descartarlas sin cargarlas.
    await page.evaluate(async () => {
      const record = await readStored('photos', state.items[0].id);
      const manifest = await readStored('session', 'current-v2');
      await new Promise((resolve, reject) => {
        const tx = db.transaction(['photos', 'session'], 'readwrite');
        tx.objectStore('photos').put({ ...record, id: 'old-undo' });
        tx.objectStore('session').put({ ...manifest, undoIds: ['old-undo'] }, 'current-v2');
        tx.oncomplete = resolve; tx.onabort = () => reject(tx.error);
      });
    });
    await page.reload(); await page.evaluate(() => storageReady);
    assert.equal(await photoCount(), 4);
    assert.equal(await page.evaluate(async () => 'undoIds' in await readStored('session', 'current-v2')), false);
    await unchanged();
    await page.waitForFunction(() => !thumbnailRunning && !saveRunning);
    const urls = await page.evaluate(async () => {
      const record = await readStored('photos', state.items[0].id);
      await new Promise((resolve, reject) => {
        const tx = db.transaction('photos', 'readwrite');
        tx.objectStore('photos').put({ ...record, id: 'orphan-photo' });
        tx.oncomplete = resolve; tx.onabort = () => reject(tx.error);
      });
      window.revokedUrls = [];
      const revoke = URL.revokeObjectURL;
      URL.revokeObjectURL = function(url) { revokedUrls.push(url); return revoke.call(this, url); };
      const transaction = IDBDatabase.prototype.transaction;
      IDBDatabase.prototype.transaction = function(stores, mode, ...args) {
        const tx = transaction.call(this, stores, mode, ...args);
        if (window.failClear && mode === 'readwrite') queueMicrotask(() => tx.abort());
        return tx;
      };
      window.failClear = true;
      return state.items.flatMap(item => [item.origUrl, item.thumbUrl, item.result?.image_url])
        .filter(url => url?.startsWith('blob:'));
    });
    assert.equal(await photoCount(), 5);
    await page.evaluate(() => $('clearSessionBtn').click());
    await page.evaluate(() => saveChain);
    assert.equal(await page.locator('#saveStatus').innerText(), 'No se pudo borrar');
    assert.equal(await photoCount(), 5, 'Un borrado fallido no debe quedar a medias');
    assert.equal(await page.locator('#clearSessionBtn').evaluate(button => button.hidden), false);
    await page.evaluate(() => { window.failClear = false; $('clearSessionBtn').click(); });
    await page.evaluate(() => saveChain);
    assert.equal(await photoCount(), 0);
    assert.equal(await page.locator('#undoClearBtn').count(), 0);
    assert.equal(await page.locator('#mainPhoto').getAttribute('src'), null);
    assert.equal(await page.locator('#downloadAnnotatedBtn').getAttribute('href'), null);
    assert.equal(await page.evaluate(() => thumbnailQueue.length + thumbnailPending.size), 0);
    assert.equal(await page.evaluate(urls => urls.every(url => revokedUrls.includes(url)), urls), true);
    await page.reload(); await page.evaluate(() => storageReady);
    assert.equal(await page.evaluate(() => state.items.length), 0);
    assert.equal(await photoCount(), 0);
    await page.keyboard.press('ArrowRight');
    assert.equal(await selected(), null);
    // Una respuesta tardía no debe recuperar las fotos limpiadas ni analizar el resto del lote.
    let releasePrediction;
    let lateRequests = 0;
    await page.route('**/api/predict', async route => {
      lateRequests++;
      await new Promise(resolve => { releasePrediction = resolve; });
      await route.fulfill({ json: { width: 800, height: 600, image_url: fixture, detections: predictions[0] } }).catch(() => {});
    });
    const lateRequest = page.waitForRequest('**/api/predict');
    await page.locator('#fileInput').setInputFiles(['tardia', 'pendiente'].map(name => ({
      name: `${name}.png`, mimeType: 'image/png', buffer: png,
    })));
    await page.waitForFunction(() => state.items.some(item => item.analyzing));
    await lateRequest;
    await page.evaluate(() => $('clearSessionBtn').click());
    await page.waitForFunction(() => !queueRunning && !saveRunning && !thumbnailRunning);
    releasePrediction();
    await page.evaluate(() => saveChain);
    assert.equal(lateRequests, 1);
    assert.equal(await photoCount(), 0);
    assert.equal(await page.evaluate(() => state.items.length), 0);
    await page.reload(); await page.evaluate(() => storageReady);
    assert.equal(await photoCount(), 0);
    await page.route('**/api/predict', route => route.fulfill({ json: {
      width: 800, height: 600, image_url: fixture, detections: predictions[0],
    } }));
    await page.locator('#fileInput').setInputFiles({ name: 'nuevo.png', mimeType: 'image/png', buffer: png });
    await page.waitForFunction(() => state.items.length === 1 && state.items[0].result);
    await page.evaluate(() => saveChain);
    assert.equal(await photoCount(), 1);
    assert.equal(await page.evaluate(() => state.items[0].order), 1);
    await page.evaluate(() => $('clearSessionBtn').click());
    await page.evaluate(() => saveChain);
    assert.equal(await photoCount(), 0);
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(work, 'resultado_alertas.json'), JSON.stringify({
      status: 'OK', mobileThreeSteps: true, predictionsSimulated: predictionsSent,
      checks: ['filtros', 'alertas independientes de revisión', 'recarga', 'marcas anteriores conservadas',
        'flechas: limites/filtro/orden/controles', 'limpieza definitiva', 'borrado fallido y reintento', 'respuesta tardia cancelada',
        'CSV', 'sin niveles', 'no evaluable', 'escritorio claro/oscuro', 'tablet', 'móvil 3 pasos 390/320'],
    }, null, 2));
    console.log('OK: alertas, revisión independiente, persistencia, CSV y móvil en 3 pasos.');
    await context.close();
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
