/* Datos de revisión humana. No modifica la inferencia ni las anotaciones CVAT. */
'use strict';
const ReviewDesk = (() => {
  const VERSION = 'revision_equipo_20261109_v1';
  const LEVEL_LABELS = ['suficiente', 'baja_disponibilidad', 'vacio', 'no_evaluable'];
  const LEVEL_LABEL_META = {
    suficiente: {short: 'Suficiente', alert: 0},
    baja_disponibilidad: {short: 'Baja', alert: 1},
    vacio: {short: 'Vacío', alert: 1},
    no_evaluable: {short: 'No eval.', alert: null},
  };
  const reasons = ['Falso nivel detectado', 'Nivel omitido', 'Contorno incorrecto',
    'Pidió reponer y era suficiente', 'Indicó suficiente y faltaba producto',
    'Debía pedir revisión', 'Otro'];
  const uid = () => globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  const clone = value => JSON.parse(JSON.stringify(value));
  function analysisId(data) {
    if (!data) return null;
    return data.analysis_context?.id || JSON.stringify([data.model, data.occupancy?.revision,
      data.detections?.map(d => [d.id, d.display_polygon, d.occupancy_estimate])]);
  }
  function ensure(item) {
    item.issues ||= [];
    item.reviewEvents ||= [];
    if (!item.levelLabels || typeof item.levelLabels !== 'object' || Array.isArray(item.levelLabels)) item.levelLabels = {};
    if (item.marked && !item.issues.length && item.reason) {
      item.issues.push({id: uid(), reason: item.reason, note: item.note || '',
        level_id: null, zone: null, expected: '', analysis_id: analysisId(item.result), legacy: true});
    }
    return item;
  }
  function setLevelLabel(item, levelId, label, reviewer) {
    ensure(item);
    const key = String(levelId);
    if (!label || item.levelLabels[key]?.label === label) {
      delete item.levelLabels[key];
      event(item, 'etiqueta_nivel_retirada', reviewer);
      return null;
    }
    if (!LEVEL_LABELS.includes(label)) throw Error('Etiqueta de nivel no válida.');
    const detection = item.result?.detections?.find(d => d.id === Number(levelId));
    const entry = {level_id: Number(levelId), label, reviewer, at: new Date().toISOString(),
      analysis_id: analysisId(item.result), confidence: detection?.confidence ?? null};
    item.levelLabels[key] = entry;
    event(item, 'etiqueta_nivel', reviewer);
    return entry;
  }
  function levelLabelCount(item) {
    return Object.keys(item?.levelLabels || {}).length;
  }
  function variantResultFor(item, algo, modelId, activeAlgo) {
    if (!item) return null;
    if (algo === activeAlgo) return item.result || null;
    if (!modelId) return null;
    return item.variantResults?.[JSON.stringify([modelId, algo])]?.result || null;
  }
  function emptyMetricBucket() {
    return {evaluable: 0, tp: 0, fp: 0, tn: 0, fn: 0, revisar: 0, omitidos: 0};
  }
  function finalizeMetricBucket(b) {
    const decided = b.tp + b.fp + b.tn + b.fn;
    const total = decided + b.revisar + b.omitidos;
    const precision = (b.tp + b.fp) ? 100 * b.tp / (b.tp + b.fp) : null;
    const recall = (b.tp + b.fn + b.revisar) ? 100 * b.tp / (b.tp + b.fn + b.revisar) : null;
    const f1 = (precision != null && recall != null && (precision + recall) > 0) ? 2 * precision * recall / (precision + recall) : null;
    const reviewRate = total ? 100 * b.revisar / total : null;
    return {...b, precision, recall, f1, reviewRate};
  }
  function computeComparisonMetrics(items, modelId, activeAlgo) {
    let comparedPhotos = 0, comparedLevels = 0, agreements = 0, discrepancies = 0;
    let lineaAReview = 0, basalReview = 0, labeledPhotos = 0, labeledLevels = 0;
    const labelCounts = {suficiente: 0, baja_disponibilidad: 0, vacio: 0, no_evaluable: 0};
    const discrepancyIndices = new Set();
    const evalBuckets = {linea_a: emptyMetricBucket(), basal: emptyMetricBucket()};
    for (const [idx, item] of (items || []).entries()) {
      const resA = variantResultFor(item, 'linea_a', modelId, activeAlgo);
      const resB = variantResultFor(item, 'basal', modelId, activeAlgo);
      if (resA && resB && Array.isArray(resA.detections) && Array.isArray(resB.detections)) {
        comparedPhotos++;
        const byIdB = new Map(resB.detections.map(d => [d.id, d]));
        for (const detA of resA.detections) {
          const detB = byIdB.get(detA.id);
          if (!detB) continue;
          comparedLevels++;
          const stA = detA.occupancy_estimate?.state || 'sin_medicion';
          const stB = detB.occupancy_estimate?.state || 'sin_medicion';
          if (stA === 'revisar') lineaAReview++;
          if (stB === 'revisar') basalReview++;
          if (stA === stB) agreements++;
          else {discrepancies++; discrepancyIndices.add(idx);}
        }
      }
      const labels = item?.levelLabels || {};
      const entries = Object.values(labels);
      if (entries.length) {
        labeledPhotos++;
        for (const entry of entries) {
          if (!Object.hasOwn(labelCounts, entry.label)) continue;
          labeledLevels++;
          labelCounts[entry.label]++;
          const alert = LEVEL_LABEL_META[entry.label]?.alert;
          if (alert === null) continue;
          for (const [algo, res] of [['linea_a', resA], ['basal', resB]]) {
            if (!res) continue;
            const det = res.detections?.find(d => d.id === Number(entry.level_id));
            const bucket = evalBuckets[algo];
            bucket.evaluable++;
            if (!det) {bucket.omitidos++; continue;}
            const st = det.occupancy_estimate?.state;
            if (st === 'revisar' || st === 'sin_medicion' || !st) bucket.revisar++;
            else if (st === 'reponer') {if (alert === 1) bucket.tp++; else bucket.fp++;}
            else if (st === 'suficiente') {if (alert === 0) bucket.tn++; else bucket.fn++;}
          }
        }
      }
    }
    return {
      comparedPhotos, comparedLevels, agreements, discrepancies, discrepancyIndices,
      lineaAReviewRate: comparedLevels ? 100 * lineaAReview / comparedLevels : null,
      basalReviewRate: comparedLevels ? 100 * basalReview / comparedLevels : null,
      labeledPhotos, labeledLevels, labelCounts,
      metrics: {linea_a: finalizeMetricBucket(evalBuckets.linea_a), basal: finalizeMetricBucket(evalBuckets.basal)},
    };
  }
  function status(item) {
    if (item.reviewStale || !item.result) return 'sin_revisar';
    return item.marked ? 'para_revision' : item.correct ? 'correcta' : 'sin_revisar';
  }
  function summary(data) {
    const counts = {reponer: 0, suficiente: 0, revisar: 0};
    for (const d of data?.detections || []) {
      const state = d.occupancy_estimate?.state || (d.state === 'reponer' || d.state === 'suficiente' ? d.state : 'revisar');
      counts[Object.hasOwn(counts, state) ? state : 'revisar']++;
    }
    return counts;
  }
  function snapshot(item) {
    return clone(Object.fromEntries(['marked', 'correct', 'reason', 'note', 'issues', 'reviewStale',
      'reviewedAt', 'reviewer', 'reviewAnalysisId', 'comparison', 'reviewEvents'].map(k => [k, item[k] ?? null])));
  }
  function event(item, action, reviewer) {
    ensure(item).reviewEvents.push({action, reviewer, at: new Date().toISOString(), analysis_id: analysisId(item.result)});
  }
  function accept(item, data, confidence) {
    ensure(item);
    if (item.result) {
      item.previousAnalysis = {result: item.result, confidence: item.analyzedConfidence,
        review: snapshot(item), analysis_id: analysisId(item.result)};
    }
    item.result = data;
    item.analyzedConfidence = confidence;
    item.failure = '';
    item.reanalysisPending = false;
    item.reviewStale = Boolean(item.marked || item.correct || item.issues.length);
    if (item.previousAnalysis) item.comparison = {status: 'pendiente',
      before: item.previousAnalysis.analysis_id, after: analysisId(data)};
  }
  function addIssue(item, issue, reviewer) {
    ensure(item);
    const record = {...issue, id: uid(), reviewer, at: new Date().toISOString(), analysis_id: analysisId(item.result)};
    item.issues.push(record);
    item.marked = true; item.correct = false; item.reviewStale = false;
    item.reason = issue.reason; item.note = issue.note;
    item.reviewedAt = record.at; item.reviewer = reviewer; item.reviewAnalysisId = record.analysis_id;
    event(item, 'fallo_registrado', reviewer);
    return record;
  }
  function correct(item, reviewer) {
    ensure(item); item.correct = true; item.marked = false; item.reviewStale = false;
    item.reviewedAt = new Date().toISOString(); item.reviewer = reviewer;
    item.reviewAnalysisId = analysisId(item.result);
    event(item, 'foto_correcta', reviewer);
  }
  function inPolygon(p, points) {
    let inside = false;
    for (let i = 0, j = points.length - 1; i < points.length; j = i++) {
      const a = points[i], b = points[j];
      if ((a[1] > p[1]) !== (b[1] > p[1]) && p[0] < (b[0] - a[0]) * (p[1] - a[1]) / (b[1] - a[1]) + a[0]) inside = !inside;
    }
    return inside;
  }
  function zone(a, b) {
    const x = Math.max(0, Math.min(1, Math.min(a.x, b.x))), y = Math.max(0, Math.min(1, Math.min(a.y, b.y)));
    return {x, y, width: Math.max(0, Math.min(1 - x, Math.abs(a.x - b.x))),
      height: Math.max(0, Math.min(1 - y, Math.abs(a.y - b.y))), coordinates: 'normalized_oriented_image'};
  }
  function exportRecord(item, paths) {
    ensure(item);
    return {...paths, original: item.file.name, estado: status(item), motivo: item.marked ? item.reason || '' : '',
      nota: item.marked ? item.note || '' : '', modelo: item.result?.model || null,
      confianza: item.analyzedConfidence ?? null, contexto: item.result?.analysis_context || null,
      revision_estimador: item.result?.occupancy?.revision || null, revision_pendiente: Boolean(item.reviewStale),
      revisor: item.reviewer || '', revisado_en: item.reviewedAt || null,
      revision_analysis_id: item.reviewAnalysisId || null, incidencias: item.issues,
      etiquetas_ocupacion: item.levelLabels || {},
      comparacion: item.comparison || null, historial: item.reviewEvents};
  }
  function csv(rows) {
    // Evita interpretar nombres/notas como fórmulas al abrirlos en Excel.
    const cell = value => {let s = String(value ?? ''); if (/^[\s]*[=+@-]/.test(s)) s = "'" + s; return '"' + s.replace(/"/g, '""') + '"';};
    return '\uFEFF' + rows.map(row => row.map(cell).join(';')).join('\r\n');
  }
  const crcTable = Array.from({length: 256}, (_, n) => {for (let k = 0; k < 8; k++) n = n & 1 ? 0xedb88320 ^ (n >>> 1) : n >>> 1; return n >>> 0;});
  function crc32(bytes) {let crc = 0xffffffff; for (const n of bytes) crc = crcTable[(crc ^ n) & 255] ^ (crc >>> 8); return (crc ^ 0xffffffff) >>> 0;}
  function readZip(buffer) {
    const bytes = new Uint8Array(buffer), view = new DataView(buffer), files = new Map();
    let offset = 0;
    while (offset + 4 <= bytes.length && view.getUint32(offset, true) === 0x04034b50) {
      if (offset + 30 > bytes.length) throw Error('ZIP incompleto.');
      const flags = view.getUint16(offset + 6, true), method = view.getUint16(offset + 8, true);
      const size = view.getUint32(offset + 18, true), originalSize = view.getUint32(offset + 22, true);
      const nameLength = view.getUint16(offset + 26, true), extra = view.getUint16(offset + 28, true);
      const start = offset + 30 + nameLength + extra, end = start + size;
      if (flags & 9 || method !== 0 || size !== originalSize) throw Error('Importa un lote ZIP exportado por esta mesa de revisión (sin recomprimir).');
      if (end > bytes.length || files.size > 500) throw Error('ZIP incompleto o demasiado grande.');
      const name = new TextDecoder('utf-8', {fatal: true}).decode(bytes.subarray(offset + 30, offset + 30 + nameLength));
      if (!name || name.startsWith('/') || name.includes('\\') || name.split('/').includes('..') || files.has(name)) throw Error('Rutas inválidas o duplicadas en el ZIP.');
      const body = bytes.subarray(start, end);
      if (crc32(body) !== view.getUint32(offset + 14, true)) throw Error('El ZIP tiene un archivo dañado.');
      files.set(name, body); offset = end;
    }
    if (!files.has('revision.json') || offset + 4 > bytes.length || view.getUint32(offset, true) !== 0x02014b50) throw Error('No es un lote de revisión válido.');
    return files;
  }
  function importRecords(files, model) {
    const json = path => {if (!files.has(path)) throw Error(`Falta ${path} en el lote.`); return JSON.parse(new TextDecoder().decode(files.get(path)));};
    const manifest = json('revision.json');
    if (manifest.schema_version !== 2 || !Array.isArray(manifest.fotos) || !manifest.fotos.length || manifest.fotos.length > 50) throw Error('Versión o tamaño de lote no compatible.');
    const originals = new Set(); let total = 0;
    return manifest.fotos.map(rec => {
      const body = files.get(rec.archivo);
      if (!body || !rec.archivo.startsWith('originales/') || originals.has(rec.archivo) || body.length > 10 * 1024 * 1024 || !body.length) throw Error('Original ausente, repetido o demasiado grande.');
      originals.add(rec.archivo); total += body.length;
      if (total > 500 * 1024 * 1024) throw Error('El lote supera 500 MB de originales.');
      const name = String(rec.original || '').replace(/[\\/]/g, '_');
      const ext = name.split('.').pop().toLowerCase(), type = {jpg: 'image/jpeg', jpeg: 'image/jpeg', png: 'image/png', webp: 'image/webp'}[ext];
      if (!type) throw Error('El lote contiene un original que no es JPG, PNG o WebP.');
      const validateResult = result => {
        if (!result) return;
        if (!Array.isArray(result.detections) || result.detections.length > 1000 || !Number.isFinite(result.width) || !Number.isFinite(result.height)
          || result.width <= 0 || result.height <= 0 || result.width * result.height > 24000000) throw Error('Resultado guardado no válido.');
        for (const key of ['image_url', 'occupancy_image_url', 'edges_image_url', 'filtered_edges_image_url']) {
          if ((key === 'image_url' || result[key] != null) && (typeof result[key] !== 'string' || !/^data:image\/(jpeg|png|webp);base64,/.test(result[key]))) throw Error('Imagen guardada no válida.');
        }
      };
      const saved = rec.resultado ? json(rec.resultado) : null; validateResult(saved);
      const variants = rec.variantes ? json(rec.variantes) : {};
      if (!variants || typeof variants !== 'object' || Array.isArray(variants) || Object.keys(variants).length > 20) throw Error('Variantes no válidas.');
      for (const [key, entry] of Object.entries(variants)) {
        const identity = JSON.parse(key);
        if (!Array.isArray(identity) || identity.length !== 2 || typeof identity[0] !== 'string' || !['linea_a', 'basal'].includes(identity[1]) || !entry || typeof entry !== 'object') throw Error('Variante no válida.');
        validateResult(entry.result); validateResult(entry.previousAnalysis?.result);
        if (entry.result && entry.result.model !== identity[0]) throw Error('Modelo de variante incoherente.');
      }
      const compatible = saved && saved.model === model?.id && (!model.occupancy_revision || saved.occupancy?.revision === model.occupancy_revision)
        && (!model.occupancy_method || saved.occupancy?.method === model.occupancy_method)
        && (!model.occupancy_source_sha256 || saved.occupancy?.source_sha256 === model.occupancy_source_sha256)
        && (!model.model_sha256 || saved.analysis_context?.model_sha256 === model.model_sha256)
        && (!model.inference_sha256 || saved.analysis_context?.source_sha256?.['inferencia.py'] === model.inference_sha256);
      const previous = rec.anterior ? json(rec.anterior) : null;
      if (previous && (typeof previous !== 'object' || !previous.result)) throw Error('Referencia anterior no válida.');
      validateResult(previous?.result);
      const validIssue = issue => {
        if (!issue || typeof issue.reason !== 'string') return false;
        if (issue.zone && !['x', 'y', 'width', 'height'].every(key => Number.isFinite(issue.zone[key]) && issue.zone[key] >= 0 && issue.zone[key] <= 1)) return false;
        if (issue.polygon && (!Array.isArray(issue.polygon) || issue.polygon.some(p => !Array.isArray(p) || p.length !== 2 || !p.every(Number.isFinite)))) return false;
        return true;
      };
      if (rec.incidencias != null && (!Array.isArray(rec.incidencias) || rec.incidencias.length > 1000 || !rec.incidencias.every(validIssue))) throw Error('Incidencias guardadas no válidas.');
      if (rec.etiquetas_ocupacion != null) {
        if (!rec.etiquetas_ocupacion || typeof rec.etiquetas_ocupacion !== 'object' || Array.isArray(rec.etiquetas_ocupacion)) throw Error('Etiquetas de ocupación no válidas.');
        for (const entry of Object.values(rec.etiquetas_ocupacion)) {
          if (!entry || typeof entry !== 'object' || !LEVEL_LABELS.includes(entry.label)) throw Error('Etiqueta de ocupación no válida.');
        }
      }
      for (const entry of Object.values(variants)) {
        if (entry.review?.issues != null && (!Array.isArray(entry.review.issues) || entry.review.issues.length > 1000 || !entry.review.issues.every(validIssue))) throw Error('Incidencias de variante no válidas.');
        if (entry.review?.reviewEvents != null && !Array.isArray(entry.review.reviewEvents)) throw Error('Historial de variante no válido.');
      }
      return {file: new File([body], name, {type}), thumb: null, result: compatible ? saved : null,
        variantResults: variants,
        previousAnalysis: compatible ? previous : saved ? {result: saved, confidence: rec.confianza, analysis_id: analysisId(saved)} : previous,
        analyzedConfidence: compatible ? rec.confianza : null, marked: rec.estado === 'para_revision', correct: rec.estado === 'correcta',
        reason: rec.motivo || '', note: rec.nota || '', failure: '', issues: Array.isArray(rec.incidencias) ? rec.incidencias : [],
        levelLabels: rec.etiquetas_ocupacion || {},
        reviewEvents: Array.isArray(rec.historial) ? rec.historial : [], reviewer: rec.revisor || '', reviewedAt: rec.revisado_en,
        reviewAnalysisId: rec.revision_analysis_id, reviewStale: !compatible || Boolean(rec.revision_pendiente), comparison: rec.comparacion || null};
    });
  }
  return {VERSION, LEVEL_LABELS, LEVEL_LABEL_META, reasons, uid, clone, analysisId, ensure, status, summary, snapshot, event, accept,
    addIssue, correct, setLevelLabel, levelLabelCount, variantResultFor, computeComparisonMetrics,
    inPolygon, zone, exportRecord, csv, readZip, importRecords};
})();

let reviewUndoStack = [], reviewBitmap = null, reviewCanvasToken = 0, reviewZone = null, reviewDrag = null, reviewOpenedAnalysis = null;
function reviewerName() {return $('reviewer-name').value.trim() || 'Sin identificar';}
function reviewMessage(message) {$('review-feedback').textContent = message;}
function rememberReview(item) {
  reviewUndoStack.push({item, analysis: ReviewDesk.analysisId(item.result), before: ReviewDesk.snapshot(item), levelLabels: ReviewDesk.clone(item.levelLabels || {})});
  if (reviewUndoStack.length > 50) reviewUndoStack.shift();
}
function nextUnreviewed() {
  const candidates = filteredBatchIndices().filter(i => ReviewDesk.status(batch[i]) === 'sin_revisar' && batch[i].result && !batch[i].analyzing);
  const next = candidates.find(i => i > batchIndex) ?? candidates.find(i => i !== batchIndex);
  if (next !== undefined) selectBatch(next);
  else reviewMessage(batch.some(item => !item.result && !item.failure) ? 'No quedan fotos analizadas por revisar. Puedes seguir cuando termine la cola.' : 'Revisión terminada en este filtro. Descarga el lote para compartirlo.');
}
function reviewCorrect() {
  const item = batch[batchIndex]; if (!item?.result || item.analyzing || running) return;
  rememberReview(item); ReviewDesk.correct(item, reviewerName()); markDirty();
  renderBatch(); saveSession(); reviewMessage(`${item.file.name}: marcada correcta.`);
  if ($('review-auto-next').checked) nextUnreviewed();
}
function undoReview() {
  const entry = reviewUndoStack.at(-1); if (!entry) return;
  if (!batch.includes(entry.item) || entry.item.analyzing || ReviewDesk.analysisId(entry.item.result) !== entry.analysis) {
    reviewUndoStack.pop(); renderBatch(); reviewMessage('Esa marca pertenece a un resultado anterior; se conserva en el historial.'); return;
  }
  reviewUndoStack.pop(); Object.assign(entry.item, entry.before); if (entry.levelLabels) entry.item.levelLabels = entry.levelLabels; markDirty();
  selectBatch(batch.indexOf(entry.item)); renderBatch(); saveSession(); reviewMessage('Última marca deshecha.');
}
function renderReviewDesk() {
  const reviewed = batch.filter(item => ReviewDesk.status(item) !== 'sin_revisar').length;
  for (const item of batch) ReviewDesk.ensure(item);
  $('review-progress').textContent = batch.length ? `Foto ${batchIndex + 1} / ${batch.length} · ${reviewed} revisadas · ${batch.length - reviewed} pendientes` : 'Carga un lote para empezar';
  $('review-undo').disabled = !reviewUndoStack.length || running;
  $('review-replay').disabled = !ready || running || batchRunning || !batch.some(item => item.result || item.previousAnalysis);
  $('review-import').disabled = running || batchRunning;
  const item = batch[batchIndex];
  $('review-history').hidden = !item;
  if (!item) return;
  const list = item.issues || [], previous = item.previousAnalysis;
  $('review-history-title').textContent = `Incidencias (${list.length}) e historial${item.reviewStale ? ' · resultado nuevo pendiente de revisión' : ''}`;
  $('review-issues').innerHTML = list.length ? list.map(issue => `<li><strong>${esc(issue.reason)}</strong> · ${issue.level_id == null ? issue.zone ? 'Zona señalada' : 'Foto completa' : 'Nivel ' + esc(issue.level_id)}${issue.analysis_id !== ReviewDesk.analysisId(item.result) ? ' · ejecución anterior' : ''}<br>${esc(issue.note || '')}${issue.expected ? ' · Esperado: ' + esc(issue.expected) : ''} · ${esc(issue.reviewer || 'Sin identificar')}<button type="button" data-remove-issue="${esc(issue.id)}" aria-label="Retirar incidencia: ${esc(issue.reason)}">Retirar</button></li>`).join('') : '<li>Sin incidencias registradas.</li>';
  $('review-comparison-note').textContent = item.lastAnalysisError ? `No se pudo reanalizar: ${item.lastAnalysisError}. Se conserva el resultado anterior.` : previous ? 'Compara ambas ejecuciones y registra si el ajuste corrigió el problema. La aplicación no lo da por resuelto automáticamente.' : 'Las incidencias y sus marcas se conservan al reanalizar. El siguiente resultado podrá compararse aquí.';
  $('review-comparison-controls').hidden = !previous || !item.result || item.analyzing;
  $('review-comparison').value = item.comparison?.status || 'pendiente';
  $('review-history-pair').hidden = !previous?.result?.image_url;
  if (previous?.result?.image_url) {
    $('review-before-image').src = previous.result.image_url;
    $('review-before-caption').textContent = `Anterior · ${previous.result.model} · confianza ${Math.round((previous.confidence || 0) * 100)} %`;
    $('review-after-image').src = item.result?.image_url || '';
    $('review-after-caption').textContent = item.result ? `Actual · ${item.result.model} · confianza ${Math.round((item.analyzedConfidence || 0) * 100)} %` : 'Pendiente de analizar con la versión actual';
  }
}
function resetReviewFields(item, level = null) {
  reviewZone = null; reviewDrag = null;
  $('batch-reason').value = ''; $('batch-note').value = ''; $('review-expected').value = '';
  $('review-level').innerHTML = '<option value="photo">Foto completa</option><option value="zone">Señalar zona / nivel omitido</option>' + item.result.detections.map(d => `<option value="${esc(d.id)}">Nivel ${esc(d.id)}</option>`).join('');
  $('review-level').value = level == null ? 'photo' : String(level);
  $('review-zone-status').textContent = '';
}
async function openReview(level = null) {
  const item = batch[batchIndex]; if (!item?.result || item.analyzing || running) return;
  reviewTarget = item; reviewOpenedAnalysis = ReviewDesk.analysisId(item.result);
  $('review-filename').textContent = item.file.name;
  resetReviewFields(item, level);
  $('review-dialog').showModal(); $('batch-reason').focus();
  const token = ++reviewCanvasToken;
  reviewBitmap?.close(); reviewBitmap = null;
  const canvas = $('review-canvas'), context = canvas.getContext?.('2d');
  context?.clearRect(0, 0, canvas.width, canvas.height);
  try {
    if (typeof createImageBitmap !== 'function') return;
    const bitmap = await createImageBitmap(item.file);
    if (token !== reviewCanvasToken || reviewTarget !== item) {bitmap.close(); return;}
    reviewBitmap = bitmap;
    const scale = Math.min(1, 1400 / Math.max(bitmap.width, bitmap.height));
    canvas.width = Math.round(bitmap.width * scale); canvas.height = Math.round(bitmap.height * scale);
    drawReviewCanvas();
  } catch { $('review-zone-status').textContent = 'No se pudo cargar la vista de marcado. Puedes elegir el nivel en la lista.'; }
}
function drawReviewCanvas() {
  if (!reviewBitmap || !reviewTarget) return;
  const canvas = $('review-canvas'), ctx = canvas.getContext('2d'), data = reviewTarget.result;
  ctx.clearRect(0, 0, canvas.width, canvas.height); ctx.drawImage(reviewBitmap, 0, 0, canvas.width, canvas.height);
  const sx = canvas.width / data.width, sy = canvas.height / data.height;
  for (const d of data.detections) {
    const points = d.display_polygon; if (!Array.isArray(points) || points.length < 3) continue;
    ctx.strokeStyle = String(d.id) === $('review-level').value ? '#ffc220' : '#00b7ff'; ctx.lineWidth = String(d.id) === $('review-level').value ? 5 : 2;
    ctx.beginPath(); ctx.moveTo(points[0][0] * sx, points[0][1] * sy);
    for (const p of points.slice(1)) ctx.lineTo(p[0] * sx, p[1] * sy);
    ctx.closePath(); ctx.stroke(); ctx.fillStyle = '#001529'; ctx.fillRect(points[0][0] * sx, points[0][1] * sy, 54, 23);
    ctx.fillStyle = '#ffffff'; ctx.font = 'bold 16px Segoe UI, sans-serif'; ctx.fillText(`N${d.id}`, points[0][0] * sx + 4, points[0][1] * sy + 17);
  }
  if (reviewZone) {ctx.strokeStyle = '#ffc220'; ctx.lineWidth = 4; ctx.strokeRect(reviewZone.x * canvas.width, reviewZone.y * canvas.height, reviewZone.width * canvas.width, reviewZone.height * canvas.height);}
}
function canvasPoint(event) {
  const canvas = $('review-canvas'), bounds = canvas.getBoundingClientRect();
  // El canvas conserva su relación de aspecto: las coordenadas pertenecen a la imagen orientada.
  return {x: Math.max(0, Math.min(1, (event.clientX - bounds.left) / bounds.width)), y: Math.max(0, Math.min(1, (event.clientY - bounds.top) / bounds.height))};
}
function saveReviewIssue(event) {
  event.preventDefault();
  const item = reviewTarget, reason = $('batch-reason').value;
  if (!item || !reason) return;
  if (item.analyzing || reviewOpenedAnalysis !== ReviewDesk.analysisId(item.result)) { $('review-zone-status').textContent = 'El resultado cambió. Cierra y abre el marcado para revisar la ejecución actual.'; return; }
  if ($('review-level').value === 'zone' && (!reviewZone || reviewZone.width < .005 || reviewZone.height < .005)) { $('review-zone-status').textContent = 'Arrastra sobre la foto para señalar la zona que falta.'; return; }
  const level = ['photo', 'zone', ''].includes($('review-level').value) ? null : Number($('review-level').value);
  const detection = item.result.detections.find(d => d.id === level);
  rememberReview(item);
  ReviewDesk.addIssue(item, {reason, category: ['Falso nivel detectado', 'Nivel omitido', 'Nivel superior omitido', 'Contorno incorrecto'].includes(reason) ? 'deteccion' : reason === 'Otro' ? 'otro' : 'disponibilidad_visual',
    level_id: level, zone: $('review-level').value === 'zone' ? reviewZone : null,
    expected: $('review-expected').value, actual: detection?.occupancy_estimate || null,
    polygon: detection?.display_polygon || null, polygon_reference: detection?.display_polygon ? {width: item.result.width, height: item.result.height} : null, note: $('batch-note').value.trim()}, reviewerName());
  markDirty(); const more = event.submitter?.id === 'review-save-more';
  // Mantener abierto evita que un evento close pendiente borre la imagen del siguiente fallo.
  if (more) {resetReviewFields(item); drawReviewCanvas(); $('batch-reason').focus();}
  else $('review-dialog').close();
  renderBatch(); saveSession(); reviewMessage(`${item.file.name}: fallo guardado.`);
  if (!more && $('review-auto-next').checked) nextUnreviewed();
}
async function importReviewLot(selected) {
  if (!selected || running || batchRunning) return;
  try {
    if (selected.size > 750 * 1024 * 1024) throw Error('El ZIP supera 750 MB. Divide la revisión en lotes menores.');
    const imported = ReviewDesk.importRecords(ReviewDesk.readZip(await selected.arrayBuffer()), algorithmModel());
    for (const item of imported) {
      const expected = (item.result || item.previousAnalysis?.result)?.analysis_context?.input_sha256;
      if (expected && globalThis.crypto?.subtle) {
        const hash = [...new Uint8Array(await crypto.subtle.digest('SHA-256', await item.file.arrayBuffer()))].map(n => n.toString(16).padStart(2, '0')).join('');
        if (hash !== expected) throw Error(`El original ${item.file.name} no coincide con su resultado guardado.`);
        for (const entry of Object.values(item.variantResults || {})) {
          if (entry.result?.analysis_context?.input_sha256 && entry.result.analysis_context.input_sha256 !== hash) throw Error('Una variante no corresponde a la foto original.');
        }
      }
      if (item.variantResults?.[variantKey()]) activateVariant(item,currentModel,occupancyAlgorithm,true);
    }
    if (dirtySelection && !confirm('Hay cambios sin descargar. ¿Reemplazar el lote actual?')) return;
    clearBatch(); batch = imported; dirtySelection = false; reviewUndoStack = []; batchFilter = 'all'; $('batch-filter').value = 'all';
    await selectBatch(0); buildThumbnails(batch); saveSession(); reviewMessage('Lote recuperado. Los resultados de otra versión quedan pendientes de reanalizar; sus incidencias se conservan.');
  } catch (err) {error(`No se pudo abrir el lote: ${err.message}`);}
}
function reviewKeydown(event) {
  if (event.defaultPrevented || event.repeat || event.altKey || event.ctrlKey || event.metaKey || !$('camera-dialog').hidden) return;
  const key = event.key.toLowerCase(), typing = /^(INPUT|TEXTAREA|SELECT)$/.test(event.target?.tagName) || event.target?.isContentEditable;
  if ($('review-dialog').open) {
    if (event.target?.tagName !== 'TEXTAREA' && /^[1-7]$/.test(key)) {event.preventDefault(); $('batch-reason').value = ReviewDesk.reasons[Number(key) - 1]; suggestExpected();}
    else if (key === 'enter' && event.target?.tagName !== 'TEXTAREA' && event.target?.id !== 'review-cancel') {event.preventDefault(); saveReviewIssue({preventDefault(){}, submitter: event.target?.id === 'review-save-more' ? $('review-save-more') : $('review-save-next')});}
    return;
  }
  if (typing || batchIndex < 0 || running) return;
  if (['arrowleft', 'arrowright', 'a', 'f', 'm', 'z', 'c'].includes(key)) event.preventDefault();
  if (key === 'arrowleft' || key === 'arrowright') moveBatch(key === 'arrowleft' ? -1 : 1);
  else if (key === 'a') reviewCorrect(); else if (key === 'f' || key === 'm') openReview();
  else if (key === 'z') undoReview(); else if (key === 'c' && result) view('compare');
}
function suggestExpected() {
  $('review-expected').value = {'Falso nivel detectado': 'sin_nivel', 'Nivel omitido': 'nivel', 'Contorno incorrecto': 'contorno',
    'Pidió reponer y era suficiente': 'suficiente', 'Indicó suficiente y faltaba producto': 'reponer', 'Debía pedir revisión': 'revisar'}[$('batch-reason').value] || '';
}
function setupReviewDesk() {
  try {$('reviewer-name').value = localStorage.getItem('walmart-vision-reviewer') || '';} catch {}
  $('reviewer-name').addEventListener('change', () => {try {localStorage.setItem('walmart-vision-reviewer', $('reviewer-name').value.trim());} catch {} saveSession();});
  $('review-auto-next').addEventListener('change', saveSession);
  $('review-undo').addEventListener('click', undoReview);
  $('review-import').addEventListener('click', () => $('review-import-file').click());
  $('review-import-file').addEventListener('change', async () => {await importReviewLot($('review-import-file').files?.[0]); $('review-import-file').value = '';});
  $('review-replay').addEventListener('click', () => {
    if (batchRunning || running || !confirm('¿Reanalizar el lote con la configuración actual? Se conservarán el resultado anterior y las incidencias; tendrás que revisar el nuevo resultado.')) return;
    analyzeBatch(true);
  });
  $('review-level').addEventListener('change', () => {reviewZone = null; drawReviewCanvas(); $('review-zone-status').textContent = $('review-level').value === 'zone' ? 'Arrastra para dibujar la zona.' : '';});
  $('batch-reason').addEventListener('change', suggestExpected);
  const canvas = $('review-canvas');
  canvas.addEventListener('pointerdown', event => {
    if (!reviewTarget || !reviewBitmap || event.button !== 0) return;
    event.preventDefault(); const point = canvasPoint(event);
    if ($('review-level').value === 'zone') {reviewDrag = point; reviewZone = null; canvas.setPointerCapture(event.pointerId);}
    else {
      const data = reviewTarget.result, hit = data.detections.find(d => Array.isArray(d.display_polygon) && ReviewDesk.inPolygon([point.x * data.width, point.y * data.height], d.display_polygon));
      if (hit) {$('review-level').value = String(hit.id); drawReviewCanvas();}
    }
  });
  canvas.addEventListener('pointermove', event => {if (reviewDrag) {reviewZone = ReviewDesk.zone(reviewDrag, canvasPoint(event)); drawReviewCanvas();}});
  canvas.addEventListener('pointerup', event => {if (reviewDrag) {reviewZone = ReviewDesk.zone(reviewDrag, canvasPoint(event)); reviewDrag = null; drawReviewCanvas(); $('review-zone-status').textContent = 'Zona señalada. Elige el motivo y guarda.';}});
  canvas.addEventListener('pointercancel', () => {reviewDrag = null; reviewZone = null; drawReviewCanvas();});
  $('occupancy-rows').addEventListener('click', event => {
    const occBtn = event.target.closest?.('[data-occ-level]');
    if (occBtn) {
      const item = batch[batchIndex];
      if (!item?.result || item.analyzing || running) return;
      rememberReview(item);
      const saved = ReviewDesk.setLevelLabel(item, Number(occBtn.dataset.occLevel), occBtn.dataset.occLabel, reviewerName());
      markDirty();
      show(item.result);
      renderBatch();
      saveSession();
      reviewMessage(`${item.file.name} · Nivel ${occBtn.dataset.occLevel}: ${saved ? ReviewDesk.LEVEL_LABEL_META[saved.label].short : 'etiqueta retirada'}.`);
      return;
    }
    const button = event.target.closest?.('[data-review-level]');
    if (button) openReview(Number(button.dataset.reviewLevel));
  });
  $('review-issues').addEventListener('click', event => {
    const button = event.target.closest('[data-remove-issue]'), item = batch[batchIndex]; if (!button || !item || item.analyzing) return;
    rememberReview(item); item.issues = item.issues.filter(issue => issue.id !== button.dataset.removeIssue);
    item.marked = item.issues.some(issue => issue.analysis_id === ReviewDesk.analysisId(item.result)); item.correct = false;
    ReviewDesk.event(item, 'incidencia_retirada', reviewerName()); markDirty(); renderBatch(); saveSession();
  });
  $('review-comparison').addEventListener('change', () => {
    const item = batch[batchIndex]; if (!item?.previousAnalysis || !item.result || item.analyzing) return;
    rememberReview(item); item.comparison = {status: $('review-comparison').value, before: item.previousAnalysis.analysis_id,
      after: ReviewDesk.analysisId(item.result), reviewer: reviewerName(), at: new Date().toISOString()};
    ReviewDesk.event(item, 'comparacion_' + item.comparison.status, reviewerName()); markDirty(); renderBatch(); saveSession();
  });
  document.addEventListener('keydown', reviewKeydown);
}

async function markedEvidence(item, warnings = []) {
  if (!item.issues?.some(issue => issue.zone || issue.polygon)) return null;
  const bitmap = await createImageBitmap(item.file);
  try {
    const canvas = document.createElement('canvas'); canvas.width = bitmap.width; canvas.height = bitmap.height;
    const ctx = canvas.getContext('2d'); ctx.drawImage(bitmap, 0, 0);
    ctx.strokeStyle = '#ffc220'; ctx.lineWidth = Math.max(3, bitmap.width / 400);
    ctx.font = `bold ${Math.max(18, bitmap.width / 55)}px Segoe UI, sans-serif`;
    for (const [index, issue] of item.issues.entries()) {
      let x, y;
      if (issue.zone) {
        const z = issue.zone; x = z.x * bitmap.width; y = z.y * bitmap.height;
        ctx.strokeRect(x, y, z.width * bitmap.width, z.height * bitmap.height);
      } else if (issue.polygon?.length) {
        const source = [item.result, item.previousAnalysis?.result].find(result => result && ReviewDesk.analysisId(result) === issue.analysis_id);
        const reference = issue.polygon_reference || source;
        if (!(reference?.width > 0 && reference?.height > 0)) {warnings.push(`${item.file.name}: incidencia F${index + 1} sin dimensiones de referencia`); continue;}
        const points = issue.polygon.map(p => [p[0] * bitmap.width / reference.width, p[1] * bitmap.height / reference.height]);
        [x, y] = points[0]; ctx.beginPath(); ctx.moveTo(x, y);
        for (const p of points.slice(1)) ctx.lineTo(p[0], p[1]); ctx.closePath(); ctx.stroke();
      } else continue;
      ctx.fillStyle = '#001529'; ctx.fillRect(x, y, 75, 30); ctx.fillStyle = '#ffffff'; ctx.fillText(`F${index + 1}`, x + 5, y + 24);
    }
    const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', .92));
    if (!blob) throw Error('No se pudo generar la evidencia de las zonas señaladas.');
    return new Uint8Array(await blob.arrayBuffer());
  } finally {bitmap.close();}
}
let exportingReviewLot = false;
async function exportReviewLot() {
  if (exportingReviewLot || !batch.length || running || batchRunning) return;
  for (const item of batch) stashVariant(item);
  const sourceBatch = batch, version = changeVersion;
  const selected = batch.map(({file, thumb, ...item}) => ({...ReviewDesk.clone(item), file}));
  const pending = selected.filter(item => ReviewDesk.status(item) === 'sin_revisar').length;
  if (pending && !confirm(`Hay ${pending} ${pending === 1 ? 'foto sin revisar' : 'fotos sin revisar'}. Se incluirán como pendientes. ¿Descargar el lote de todos modos?`)) return;
  const noResult = selected.filter(item => !item.result).length;
  if (noResult && !confirm(`${noResult} fotos no tienen resultado y se incluirán sin contornos actuales. ¿Continuar?`)) return;
  exportingReviewLot = true; $('batch-download').disabled = true;
  try {
    const entries = [], records = [], warnings = [], reasons = new Map(), comparisons = {pendiente: 0, corregido: 0, persiste: 0, empeoro: 0};
    const csvRows = [['Archivo', 'Estado de revisión', 'Motivo', 'Nivel', 'Resultado esperado', 'Obtenido', 'Revisor', 'Fecha UTC', 'Comparación', 'Nota']];
    const labelRows = [['Archivo', 'SHA256_original', 'Nivel', 'Etiqueta_humana', 'Alerta_humana', 'LineaA_pct', 'LineaA_estado', 'Basal_pct', 'Basal_estado', 'Basal_ancho_obs', 'Confianza_YOLO', 'Revisor', 'Fecha_UTC']];
    const labelJson = [];
    const addJSON = (name, value) => entries.push({name, bytes: new TextEncoder().encode(JSON.stringify(value, null, 2))});
    const activeModelId = currentModel?.id || null;
    for (const [i, item] of selected.entries()) {
      ReviewDesk.ensure(item);
      const prefix = String(i + 1).padStart(3, '0'), safe = item.file.name.replace(/[\\/\x00-\x1f]/g, '_');
      const original = `originales/${prefix}_${safe}`, contour = `contornos/${prefix}_contornos.jpg`;
      const resultPath = `resultados/${prefix}.json`, previousPath = `anteriores/${prefix}.json`, marks = `marcas/${prefix}_fallos.jpg`;
      const originalBytes = new Uint8Array(await item.file.arrayBuffer());
      entries.push({name: original, bytes: originalBytes});
      let inputSha = item.result?.analysis_context?.input_sha256 || null;
      if (!inputSha && globalThis.crypto?.subtle) {
        inputSha = [...new Uint8Array(await crypto.subtle.digest('SHA-256', originalBytes))].map(n => n.toString(16).padStart(2, '0')).join('');
      }
      if (item.result) {entries.push({name: contour, bytes: await contourEvidence(item)}); addJSON(resultPath, item.result);}
      if (item.previousAnalysis) addJSON(previousPath, item.previousAnalysis);
      const variantsPath = `variantes/${prefix}.json`;
      addJSON(variantsPath, item.variantResults || {});
      const marked = await markedEvidence(item, warnings); if (marked) entries.push({name: marks, bytes: marked});
      records.push(ReviewDesk.exportRecord(item, {archivo: original, contornos: item.result ? contour : null,
        resultado: item.result ? resultPath : null, anterior: item.previousAnalysis ? previousPath : null, marcas: marked ? marks : null,
        variantes: variantsPath,
        ultimo_error_analisis: item.lastAnalysisError || null}));
      if (item.comparison && Object.hasOwn(comparisons, item.comparison.status)) comparisons[item.comparison.status]++;
      const resA = ReviewDesk.variantResultFor(item, 'linea_a', activeModelId, occupancyAlgorithm);
      const resB = ReviewDesk.variantResultFor(item, 'basal', activeModelId, occupancyAlgorithm);
      for (const entry of Object.values(item.levelLabels || {})) {
        const lvl = Number(entry.level_id);
        const detA = resA?.detections?.find(d => d.id === lvl);
        const detB = resB?.detections?.find(d => d.id === lvl);
        const alertVal = ReviewDesk.LEVEL_LABEL_META[entry.label]?.alert;
        const pctA = detA?.occupancy_estimate?.pct ?? '', stA = detA?.occupancy_estimate?.state ?? '';
        const pctB = detB?.occupancy_estimate?.pct ?? '', stB = detB?.occupancy_estimate?.state ?? '';
        const obsB = detB?.occupancy?.observed_width_pct ?? '';
        const conf = detA?.confidence ?? detB?.confidence ?? entry.confidence ?? '';
        labelRows.push([item.file.name, inputSha || '', lvl, entry.label, alertVal === null ? '' : alertVal,
          pctA, stA, pctB, stB, obsB, conf, entry.reviewer || '', entry.at || '']);
        labelJson.push({archivo: item.file.name, input_sha256: inputSha, level_id: lvl, label: entry.label,
          alerta_humana: alertVal, linea_a: detA ? {pct: detA.occupancy_estimate?.pct ?? null, state: detA.occupancy_estimate?.state ?? null} : null,
          basal: detB ? {pct: detB.occupancy_estimate?.pct ?? null, state: detB.occupancy_estimate?.state ?? null, observed_width_pct: detB.occupancy?.observed_width_pct ?? null} : null,
          confidence: conf === '' ? null : conf, reviewer: entry.reviewer || '', at: entry.at || null});
      }
      for (const issue of item.issues) {
        reasons.set(issue.reason, (reasons.get(issue.reason) || 0) + 1);
        csvRows.push([item.file.name, ReviewDesk.status(item), issue.reason, issue.level_id ?? (issue.zone ? 'Zona' : 'Foto'),
          issue.expected, issue.actual?.state, issue.reviewer, issue.at, item.comparison?.status, issue.note]);
      }
      if (!item.issues.length) csvRows.push([item.file.name, ReviewDesk.status(item), '', '', '', '', item.reviewer, item.reviewedAt, item.comparison?.status, '']);
    }
    const compareSummary = ReviewDesk.computeComparisonMetrics(selected, activeModelId, occupancyAlgorithm);
    addJSON('revision.json', {schema_version: 2, app_version: ReviewDesk.VERSION, exported_at_utc: new Date().toISOString(), fotos: records});
    addJSON('resumen.json', {fotos: records.length, revisadas: records.length - pending, pendientes: pending, advertencias: warnings,
      incidencias_por_motivo: Object.fromEntries([...reasons].sort((a, b) => b[1] - a[1])), comparaciones: comparisons,
      etiquetas_ocupacion_totales: compareSummary.labeledLevels, etiquetas_por_clase: compareSummary.labelCounts});
    entries.push({name: 'resumen.csv', bytes: new TextEncoder().encode(ReviewDesk.csv(csvRows))});
    if (labelJson.length) {
      addJSON('etiquetas_ocupacion.json', labelJson);
      entries.push({name: 'etiquetas_ocupacion.csv', bytes: new TextEncoder().encode(ReviewDesk.csv(labelRows))});
    }
    entries.push({name: 'LEEME.txt', bytes: new TextEncoder().encode('Lote de revisión humana de desarrollo. Abrir este ZIP sin recomprimir desde «Abrir lote de revisión». Los originales conservan sus bytes. marcas/ identifica las incidencias F1, F2… en el orden de revision.json; puede incluir ejecuciones anteriores. resultados/ y anteriores/ conservan los resultados para comparar. variantes/ conserva cada algoritmo y sus revisiones por separado; revision_estimador identifica cuál estaba activo al exportar. Una marca no modifica CVAT, no inicia entrenamiento ni certifica exactitud. El índice visual 0–100 no es porcentaje físico de stock. Las comparaciones son confirmaciones humanas. resumen.json incluye motivos históricos; consultar analysis_id para su ejecución de origen.')} );
    const totalBytes = entries.reduce((total, entry) => total + entry.bytes.length, 0);
    if (totalBytes > 740 * 1024 * 1024) throw Error('El lote con evidencias supera 740 MB. Descarga lotes menores.');
    const blob = zipSelected(entries), url = URL.createObjectURL(blob), link = document.createElement('a');
    link.href = url; link.download = `revision_equipo_${new Date().toISOString().replace(/[:.]/g, '-')}.zip`; link.click();
    if (batch === sourceBatch && changeVersion === version) {dirtySelection = false; saveSession();}
    reviewMessage('ZIP preparado; descarga iniciada.' + (warnings.length ? ` ${warnings.length} incidencias no pudieron dibujarse; consulta resumen.json.` : '')); setTimeout(() => URL.revokeObjectURL(url), 60000);
  } catch (err) {error(`No se pudo preparar el lote: ${err.message}`);} finally {exportingReviewLot = false; availability();}
}
