// Prueba de navegador aislada. Requiere Playwright y un Chromium instalado.
const { chromium } = require(process.env.WALMART_PLAYWRIGHT || 'playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '../..');
const work = path.join(root, '.tmp/cliente_memoria_20261111');
fs.mkdirSync(work, { recursive: true });
let fixture;
let expectedHash;
const current = fs.readFileSync(path.join(root, 'Aplicacion_Cliente/interfaz_cliente.html'), 'utf8');
const beforePath = path.join(work, 'interfaz_antes.html');
const base = 'http://127.0.0.1:19098';

(async () => {
  const browser = await chromium.launch({
    executablePath: process.env.WALMART_CHROMIUM || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    headless: true,
  });
  const report = {};
  const generator = await browser.newPage();
  fixture = Buffer.from(await generator.evaluate(() => {
    const canvas = document.createElement('canvas');
    canvas.width = 2048; canvas.height = 1536;
    const ctx = canvas.getContext('2d');
    const pixels = ctx.createImageData(canvas.width, canvas.height);
    let seed = 11;
    for (let i = 0; i < pixels.data.length; i += 4) {
      seed ^= seed << 13; seed ^= seed >>> 17; seed ^= seed << 5;
      pixels.data[i] = seed & 255;
      pixels.data[i + 1] = (seed >>> 8) & 255;
      pixels.data[i + 2] = (seed >>> 16) & 255;
      pixels.data[i + 3] = 255;
    }
    ctx.putImageData(pixels, 0, 0);
    return canvas.toDataURL('image/jpeg', .88).split(',')[1];
  }), 'base64');
  expectedHash = crypto.createHash('sha256').update(fixture).digest('hex');
  await generator.close();
  async function setup(html, count, undoCount = 0, failMigration = false) {
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => { errors.push(error.message); console.error('Error de página:', error.message); });
    await page.addInitScript(({ failMigration }) => {
      window.testWrites = [];
      window.testClones = 0;
      window.failWrite = failMigration;
      const put = IDBObjectStore.prototype.put;
      IDBObjectStore.prototype.put = function(value, ...args) {
        window.testWrites.push({ store: this.name, id: value?.id, photos: value?.items?.length || 0 });
        return put.call(this, value, ...args);
      };
      const clone = structuredClone;
      window.structuredClone = function(value, ...args) {
        if (value?.items) window.testClones++;
        return clone(value, ...args);
      };
      const transaction = IDBDatabase.prototype.transaction;
      IDBDatabase.prototype.transaction = function(stores, mode, ...args) {
        const tx = transaction.call(this, stores, mode, ...args);
        if (window.failWrite && mode === 'readwrite' && Array.from(stores).includes('photos')) {
          queueMicrotask(() => tx.abort());
        }
        return tx;
      };
    }, { failMigration });
    await page.route(`${base}/**`, async route => {
      const pathname = new URL(route.request().url()).pathname;
      if (pathname === '/seed') return route.fulfill({ contentType: 'text/html', body: '<title>Datos de prueba aislados</title>' });
      if (pathname === '/fixture.jpg') return route.fulfill({ contentType: 'image/jpeg', body: fixture });
      if (pathname === '/logo.svg') return route.fulfill({ contentType: 'image/svg+xml', body: fs.readFileSync(path.join(root, 'Aplicacion_Cliente/logo.svg')) });
      if (pathname === '/api/health') return route.fulfill({ json: { status: 'ok', analysis_ready: true } });
      if (pathname === '/api/predict') return route.fulfill({ status: 500, json: { error: 'No se debe inferir una foto ya analizada.' } });
      return route.fulfill({ contentType: 'text/html', body: html });
    });
    await page.goto(`${base}/seed`);
    console.log(`Preparando ${count} fotos de prueba…`);
    await page.evaluate(async ({ count, undoCount }) => {
      const blob = await (await fetch('/fixture.jpg')).blob();
      // Una anotación de prueba más pequeña evita exceder el tamaño máximo de un
      // registro IndexedDB del formato antiguo al sembrar las 68 fotos.
      const bitmap = await createImageBitmap(blob);
      const canvas = document.createElement('canvas'); canvas.width = 800; canvas.height = 600;
      canvas.getContext('2d').drawImage(bitmap, 0, 0, 800, 600); bitmap.close();
      const imageUrl = canvas.toDataURL('image/jpeg', .8);
      canvas.width = 1; canvas.height = 1;
      const records = Array.from({ length: count }, (_, i) => ({
        id: `photo-${i}`, order: i + 1, name: `foto-${i}.jpg`,
        file: new File([blob], `foto-${i}.jpg`, { type: 'image/jpeg' }),
        replenished: { 3: '12:00' }, reviews: { 2: { value: 'confirmado', at: '2026-11-11T15:00:00Z' } },
        error: null, result: {
          model: 'fixture', width: 2048, height: 1536, image_url: imageUrl,
          detections: [1, 2, 3].map(id => ({ id,
            display_polygon: [[10, 10 + id * 200], [1900, 10 + id * 200], [1900, 100 + id * 200], [10, 100 + id * 200]],
            occupancy_estimate: { pct: 25, state: 'reponer' },
            store_diagnosis: { operational_state: 'reponer', operational_label: 'Reponer', headline: 'Dato conservado', action: 'Reponer' },
          })),
        },
      }));
      const db = await new Promise((resolve, reject) => {
        const req = indexedDB.open('walmart-cliente-sesion', 1);
        req.onupgradeneeded = () => req.result.createObjectStore('session');
        req.onerror = () => reject(req.error); req.onsuccess = () => resolve(req.result);
      });
      await new Promise((resolve, reject) => {
        const tx = db.transaction('session', 'readwrite');
        tx.objectStore('session').put({ items: records.slice(0, count - undoCount), undo: undoCount ? records.slice(-undoCount) : null, selectedId: 'photo-0' }, 'current');
        tx.oncomplete = resolve; tx.onerror = () => reject(tx.error); tx.onabort = () => reject(tx.error || new Error('No se pudieron sembrar los datos de prueba'));
      });
      db.close();
    }, { count, undoCount });
    await page.goto(`${base}/`);
    console.log(`Recuperando ${count} fotos…`);
    await page.evaluate(() => Promise.race([storageReady, new Promise((_, reject) => setTimeout(() => reject(new Error('La recuperación excedió 45 segundos')), 45000))]));
    console.log(`Recorrido de ${count} fotos recuperado.`);
    return { context, page, errors };
  }
  async function settle(page) {
    await page.waitForTimeout(250);
    await page.waitForFunction(() => typeof thumbnailRunning === 'undefined' || (!thumbnailRunning && !saveRunning));
    await page.evaluate(() => saveChain);
  }
  async function metrics(page) {
    return page.evaluate(() => ({
      writes: testWrites.length,
      photoWrites: testWrites.filter(w => w.store === 'photos').length,
      fullSessionPhotoCopies: testWrites.reduce((sum, w) => sum + w.photos, 0),
      fullSessionClones: testClones,
      thumbnailPixels: [...document.querySelectorAll('.queue-thumb')].reduce((sum, img) => sum + img.naturalWidth * img.naturalHeight, 0),
      maxThumbnailSide: Math.max(0, ...[...document.querySelectorAll('.queue-thumb')].flatMap(img => [img.naturalWidth, img.naturalHeight])),
    }));
  }
  try {
    // Comparación limitada a ocho fotos para no forzar otro cierre por memoria.
    for (const [name, html] of [['before', fs.existsSync(beforePath) ? fs.readFileSync(beforePath, 'utf8') : null], ['after', current]]) {
      if (!html) continue;
      const { context, page, errors } = await setup(html, 8);
      await settle(page);
      await page.evaluate(async () => {
        testWrites.length = 0; testClones = 0;
        for (let i = 0; i < 12; i++) selectItem(state.items[i % state.items.length].id);
        await saveChain;
      });
      await settle(page);
      report[name] = await metrics(page);
      console.log(name, report[name]);
      assert.deepEqual(errors, []);
      await context.close();
    }
    assert.equal(report.after.fullSessionClones, 0);
    assert.equal(report.after.fullSessionPhotoCopies, 0);
    assert.equal(report.after.photoWrites, 0);
    assert(report.after.maxThumbnailSide <= 160);

    const { context, page, errors } = await setup(current, 68, 2);
    await settle(page);
    const preserved = await page.evaluate(async () => {
      const record = await readStored('photos', 'photo-0');
      const digest = await crypto.subtle.digest('SHA-256', await record.file.arrayBuffer());
      return {
        count: state.items.length, version: db.version,
        discardedUndo: await readStored('photos', 'photo-67'),
        manifestHasUndo: 'undoIds' in await readStored('session', 'current-v2'),
        hash: [...new Uint8Array(digest)].map(v => v.toString(16).padStart(2, '0')).join(''),
        imageStoredAsBlob: record.resultImage instanceof Blob,
        temporaryUrlStored: 'image_url' in record.result,
        previousReview: record.reviews[2].value,
        previousReplenishment: record.replenished[3],
        polygon: record.result.detections[0].display_polygon,
        legacy: await readStored('session', 'current'),
      };
    });
    assert.equal(preserved.count, 66);
    assert.equal(preserved.discardedUndo, undefined); assert.equal(preserved.manifestHasUndo, false);
    assert.equal(preserved.version, 2); assert.equal(preserved.hash, expectedHash);
    assert.equal(preserved.imageStoredAsBlob, true); assert.equal(preserved.temporaryUrlStored, false);
    assert.equal(preserved.previousReview, 'confirmado'); assert.equal(preserved.previousReplenishment, '12:00');
    assert.deepEqual(preserved.polygon, [[10, 210], [1900, 210], [1900, 300], [10, 300]]);
    assert.equal(preserved.legacy, undefined);
    await page.evaluate(async () => {
      testWrites.length = 0;
      for (let i = 0; i < 100; i++) selectItem(state.items[i % state.items.length].id);
      await saveChain;
    });
    await settle(page);
    report.stress68 = await metrics(page);
    assert.equal(report.stress68.photoWrites, 0);
    assert.equal(report.stress68.fullSessionClones, 0);
    assert(report.stress68.writes <= 2);
    assert(report.stress68.maxThumbnailSide <= 160);
    await page.evaluate(() => { testWrites.length = 0; selectItem('photo-0'); });
    await page.locator('[data-quick-level="3"][data-action="revisado"]').click();
    await page.evaluate(() => saveChain);
    assert.equal(await page.evaluate(() => testWrites.filter(w => w.store === 'photos').length), 1);
    await page.reload(); await page.evaluate(() => storageReady); await settle(page);
    assert.equal(await page.evaluate(() => state.items.find(i => i.id === 'photo-0').reviews[3].value), 'revisado');
    assert.equal(await page.evaluate(() => visualAlertCount(state.items.find(i => i.id === 'photo-0'))), 3);

    // Un guardado abortado conserva el registro anterior y puede reintentarse.
    await page.evaluate(async () => {
      failWrite = true;
      state.items[0].reviews[1] = { value: 'necesita', at: 'prueba' };
      saveSession(state.items[0].id); await saveChain;
    });
    assert.equal(await page.locator('#saveStatus').innerText(), 'No se pudo guardar');
    assert.equal(await page.evaluate(async () => Boolean((await readStored('photos', state.items[0].id)).reviews[1])), false);
    await page.evaluate(async () => { failWrite = false; saveSession(); await saveChain; });
    assert.equal(await page.evaluate(async () => (await readStored('photos', state.items[0].id)).reviews[1].value), 'necesita');

    await page.evaluate(() => { state.viewMode = 'compare'; renderStageAndLevels(); });
    assert.equal(await page.locator('#compareResImg').getAttribute('src').then(v => v.startsWith('blob:')), true);
    await page.evaluate(() => { state.viewMode = 'original'; renderStageAndLevels(); });
    assert.equal(await page.locator('#compareResImg').getAttribute('src'), null);
    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({ path: path.join(work, 'movil.png'), fullPage: true });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.screenshot({ path: path.join(work, 'escritorio.png') });
    // Limpiar borra los registros y no conserva una reserva para deshacer.
    await page.evaluate(() => $('clearSessionBtn').click()); await settle(page);
    await page.reload(); await page.evaluate(() => storageReady); await settle(page);
    assert.equal(await page.evaluate(() => state.items.length), 0);
    assert.equal(await page.locator('#undoClearBtn').count(), 0);
    assert.equal(await page.evaluate(() => new Promise(resolve => {
      const request = db.transaction('photos').objectStore('photos').count();
      request.onsuccess = () => resolve(request.result);
    })), 0);
    assert.deepEqual(await page.evaluate(async () => (await readStored('session', 'current-v2')).itemIds), []);
    assert.deepEqual(errors, []);
    await context.close();

    // Si la migración falla, la sesión v1 permanece completa hasta un reintento correcto.
    const failed = await setup(current, 3, 1, true);
    const retained = await failed.page.evaluate(async () => ({
      legacyCount: (await readStored('session', 'current')).items.length,
      manifest: await readStored('session', 'current-v2'),
    }));
    assert.equal(retained.legacyCount, 2); assert.equal(retained.manifest, undefined);
    await failed.page.evaluate(async () => { failWrite = false; saveSession(); await saveChain; });
    assert.equal(await failed.page.evaluate(async () => (await readStored('session', 'current-v2')).itemIds.length), 2);
    assert.deepEqual(failed.errors, []);
    await failed.context.close();

    report.validation = 'OK: 68 fotos simuladas; migración atómica, SHA original, contornos y marcas activos intactos; antiguas reservas de deshacer descartadas; navegación, guardado fallido y reintento, recarga, limpieza definitiva y móvil. Sin inferencia ni datos reales.';
    fs.writeFileSync(path.join(work, 'resultado.json'), JSON.stringify(report, null, 2));
    console.log(JSON.stringify(report, null, 2));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
