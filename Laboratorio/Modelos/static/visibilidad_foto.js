/* Sección independiente del prototipo de visibilidad; no inicia trabajos sola. */
(() => {
  const node = id => document.getElementById(id);
  let activeJob = null;
  let timer = null;
  async function request(path, body) {
    const options = body ? {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)} : {};
    const response = await fetch(path, options);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'No se pudo completar la consulta.');
    return data;
  }
  function write(id, text) { node(id).textContent = text; }
  function renderProposals(items, target = 'visibility-proposals-grid') {
    const root = node(target);
    root.textContent = '';
    if (!items?.length) return;
    const intro = document.createElement('p');
    intro.textContent = 'Revisa las imágenes y, si necesitas corregir una, abre su trabajo en CVAT y ve al número de fotograma indicado. Guarda en CVAT y vuelve a consultar la revisión.';
    root.append(intro);
    for (const split of ['train', 'val']) {
      const rows = items.filter(x => x.split === split);
      const details = document.createElement('details');
      const summary = document.createElement('summary');
      summary.textContent = `${split === 'train' ? 'Entrenamiento' : 'Validación'} · ${rows.length} propuestas`;
      details.append(summary);
      const grid = document.createElement('div');
      grid.style.display = 'grid'; grid.style.gridTemplateColumns = 'repeat(auto-fill,minmax(180px,1fr))'; grid.style.gap = '16px';
      for (const row of rows) {
        const figure = document.createElement('figure'); figure.style.margin = '16px 0';
        const image = document.createElement('img'); image.loading = 'lazy'; image.style.width = '100%';
        image.src = `/api/visibilidad/propuesta-imagen?task=${row.revision_task_id}&frame=${row.revision_frame}&preview=thumb`;
        image.alt = `Foto ${row.name}`;
        const caption = document.createElement('figcaption');
        caption.textContent = `${row.name} · ${row.propuesta.decision} · ${row.propuesta.motivo || 'sin motivo'}`;
        const link = document.createElement('a');
        const job = row.revision_task_id === 37 ? 84 : 85;
        link.href = `http://localhost:8082/tasks/${row.revision_task_id}/jobs/${job}?frame=${row.revision_frame}`;
        link.target = '_blank'; link.rel = 'noopener'; link.textContent = `Abrir CVAT · fotograma ${row.revision_frame}`;
        figure.append(image, caption, link); grid.append(figure);
      }
      details.append(grid); root.append(details);
    }
  }
  async function review() {
    write('visibility-review-status', 'Consultando CVAT…');
    try {
      const data = await request('/api/visibilidad/revision');
      const lines = data.counts.map(x => `${x.split} · ${x.origen} · ${x.etiqueta}: ${x.total}`);
      write('visibility-review-status', lines.join(' | ') + (data.issues.length ? ` · ${data.issues.length} decisiones por corregir: ${data.issues.map(x => x.name + ' (' + x.reason + ')').join(', ')}` : ' · Sin decisiones incompatibles'));
      const status = node('visibility-proposal-status');
      status.hidden = !data.proposal_count;
      status.textContent = data.proposal_count ? `${data.proposal_count} propuestas de la tarea 33 · ${data.proposals_confirmed ? 'confirmadas' : 'pendientes de tu revisión'}` : '';
      renderProposals(data.proposals.filter(x => x.propuesta.lote === 'tarea33'));
      const second = data.proposal_batches.revision_visual;
      write('visibility-second-status', second.count ? `${second.count} fotos del segundo lote · ${second.confirmed ? 'confirmadas' : 'pendientes de tu revisión'}` : 'El segundo lote todavía no está disponible.');
      renderProposals(data.proposals.filter(x => x.propuesta.lote === 'revision_visual'), 'visibility-second-grid');
    } catch (error) { write('visibility-review-status', error.message); }
  }
  async function poll() {
    try {
      const jobs = await request('/api/jobs');
      const job = activeJob ? jobs.find(j => j.id === activeJob) : jobs.find(j => j.config?.pipeline === 'visibilidad_foto_v1');
      if (!job) return;
      activeJob = job.id;
      const progress = job.progress || {};
      write('visibility-job-status', `Trabajo ${job.state} · ${progress.completed_epochs || 0}/${progress.total_epochs || 40} épocas${job.state === 'error' ? ' · Revisa el registro del trabajo.' : ''}`);
      node('visibility-train').disabled = job.state === 'running';
      if (job.state === 'running') timer = setTimeout(poll, 5000);
      else if (job.state === 'done') await results(job.config.run);
    } catch (error) { write('visibility-job-status', error.message); }
  }
  async function results(run) {
    const output = node('visibility-result-output');
    output.textContent = 'Consultando resultados…';
    try {
      if (!run) {
        const jobs = await request('/api/jobs');
        const last = jobs.find(j => j.config?.pipeline === 'visibilidad_foto_v1' && j.state === 'done');
        if (!last) { output.textContent = 'Todavía no hay ensayos terminados.'; return; }
        run = last.config.run;
      }
      const data = await request('/api/visibilidad/resultado?run=' + encodeURIComponent(run));
      output.textContent = '';
      const intro = document.createElement('p');
      intro.textContent = `Ensayo ${run}. Mejor época: ${data.best_epoch}. Umbral: ${data.threshold ?? 'no disponible'}. Activación automática: deshabilitada.`;
      output.append(intro);
      const eligibility = document.createElement('p');
      eligibility.textContent = data.acceptance?.candidate_for_testing
        ? 'Cumple los criterios del prototipo. Prepara el visor experimental desde el proyecto; no sustituye la aplicación estable.'
        : 'No cumple los criterios para preparar el visor experimental. Revisa la calibración y los resultados.';
      output.append(eligibility);
      if (!data.validation.length) {
        const note = document.createElement('p');
        note.textContent = 'Las 69 fotos de validación no se evaluaron porque la calibración no produjo un umbral aceptable. La galería siguiente muestra solo calibración interna.';
        output.append(note);
      }
      if (data.calibration?.length) {
        const section = document.createElement('section');
        const title = document.createElement('h3'); title.textContent = 'Fotos de calibración'; section.append(title);
        const note = document.createElement('p');
        note.textContent = 'Compara la etiqueta revisada con la puntuación de aptitud del modelo. El corte 0,50 se muestra solo para diagnosticar el ensayo; no es un umbral aprobado ni una medida de ocupación.';
        section.append(note);
        for (const [label, heading] of [['no_apta', 'Fotos marcadas como no aptas'], ['apta', 'Fotos marcadas como aptas']]) {
          const rows = data.calibration.filter(x => x.etiqueta === label);
          const details = document.createElement('details'); details.open = label === 'no_apta';
          const summary = document.createElement('summary'); summary.textContent = `${heading} · ${rows.length}`; details.append(summary);
          const grid = document.createElement('div'); grid.className = 'visibility-calibration-grid';
          for (const item of rows) {
            const figure = document.createElement('figure');
            const url = '/api/visibilidad/calibracion-imagen?run=' + encodeURIComponent(run) + '&photo=' + encodeURIComponent(item.name);
            const link = document.createElement('a'); link.href = url; link.target = '_blank'; link.rel = 'noopener';
            const image = document.createElement('img'); image.src = url + '&preview=thumb'; image.alt = `Foto ${item.name}`; image.loading = 'lazy'; link.append(image);
            const caption = document.createElement('figcaption');
            const prediction = item.score_apta >= .5 ? 'apta' : 'no apta';
            caption.textContent = `${item.name} · Etiqueta: ${label === 'apta' ? 'apta' : 'no apta'} · Puntuación de aptitud: ${item.score_apta.toFixed(3)} · Con corte 0,50: ${prediction}`;
            figure.append(link, caption); grid.append(figure);
          }
          details.append(grid); section.append(details);
        }
        output.append(section);
      }
      if (data.acceptance?.candidate_for_testing) {
        const command = document.createElement('pre');
        command.textContent = `.\\.venv-modelo\\Scripts\\python.exe Laboratorio\\Modelos\\preparar_visibilidad_app.py ${run}`;
        output.append(command);
      }
      for (const group of data.validation_summary.filter(x => x.group_by === 'origen')) {
        const p = document.createElement('p');
        p.textContent = `${group.group}: ${group.photos} fotos; ${group.aptas_aceptadas}/${group.aptas} aptas aceptadas; ${group.no_aptas_aceptadas}/${group.no_aptas} no aptas aceptadas indebidamente.`;
        output.append(p);
      }
      const grouped = document.createElement('details');
      const groupedTitle = document.createElement('summary'); groupedTitle.textContent = 'Resultados por escena y motivo'; grouped.append(groupedTitle);
      for (const group of data.validation_summary.filter(x => x.group_by !== 'origen')) {
        const row = document.createElement('p');
        row.textContent = `${group.group_by} ${group.group}: ${group.photos} fotos; ${group.aptas_aceptadas}/${group.aptas} aptas aceptadas; ${group.no_aptas_aceptadas}/${group.no_aptas} no aptas aceptadas indebidamente.`;
        grouped.append(row);
      }
      output.append(grouped);
      if (data.history.length) {
        const chart = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        chart.setAttribute('viewBox', '0 0 400 120'); chart.setAttribute('role', 'img');
        chart.setAttribute('aria-label', 'Exactitud equilibrada de calibración por época');
        chart.style.maxWidth = '400px'; chart.style.width = '100%';
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
        line.setAttribute('fill', 'none'); line.setAttribute('stroke', '#2563eb'); line.setAttribute('stroke-width', '3');
        line.setAttribute('points', data.history.map((x, i) => `${10 + i * 380 / Math.max(1, data.history.length - 1)},${110 - x.balanced_accuracy * 100}`).join(' '));
        chart.append(line); output.append(chart);
      }
      const history = document.createElement('details');
      const summary = document.createElement('summary'); summary.textContent = 'Valores por época'; history.append(summary);
      const lines = document.createElement('pre');
      lines.textContent = data.history.map(x => `Época ${x.epoch}: pérdida ${x.loss.toFixed(3)}, exactitud equilibrada ${x.balanced_accuracy.toFixed(3)}`).join('\n');
      history.append(lines); output.append(history);
      const errors = data.validation.filter(x => (x.etiqueta === 'no_apta' && x.decision === 'apta') || (x.etiqueta === 'apta' && x.decision !== 'apta'));
      const title = document.createElement('p'); title.textContent = `Errores de validación para revisar: ${errors.length}`; if (data.validation.length) output.append(title);
      for (const item of errors) {
        const figure = document.createElement('figure');
        const image = document.createElement('img');
        image.src = '/api/visibilidad/imagen?run=' + encodeURIComponent(run) + '&photo=' + encodeURIComponent(item.name);
        image.alt = `Foto de validación ${item.name}`; image.loading = 'lazy'; image.style.maxWidth = '240px';
        const caption = document.createElement('figcaption');
        caption.textContent = `${item.name} · ${item.origen} · etiqueta ${item.etiqueta} · resultado ${item.decision}`;
        figure.append(image, caption); output.append(figure);
      }
      const comparisons = document.createElement('details');
      const comparisonsTitle = document.createElement('summary'); comparisonsTitle.textContent = 'Comparar V3 y anotaciones por foto'; comparisons.append(comparisonsTitle);
      const explanation = document.createElement('p');
      explanation.textContent = 'Izquierda: anotaciones de referencia. Derecha: contornos V3 sin filtro. La comparación aplica solo los controles de visibilidad y geometría; no calcula ocupación. Revisa también los contornos con igual número de niveles.';
      comparisons.append(explanation);
      for (const item of data.validation.filter(x => x.comparison_image)) {
        const figure = document.createElement('figure');
        const image = document.createElement('img');
        image.src = '/api/visibilidad/comparacion?run=' + encodeURIComponent(run) + '&photo=' + encodeURIComponent(item.name);
        image.alt = `Anotaciones y contornos de ${item.name}`; image.loading = 'lazy'; image.style.maxWidth = '100%';
        const caption = document.createElement('figcaption');
        caption.textContent = `${item.name} · referencia ${item.reference_levels} · V3 ${item.baseline_levels} · con filtro: ${item.filtered_outcome}`;
        figure.append(image, caption); comparisons.append(figure);
      }
      if (data.validation.length) output.append(comparisons);
    } catch (error) { output.textContent = error.message; }
  }
  node('visibility-refresh').addEventListener('click', review);
  node('visibility-confirm-proposals').addEventListener('click', async () => {
    if (!node('visibility-proposals-reviewed').checked) {
      write('visibility-proposal-status', 'Marca la casilla después de revisar y guardar las propuestas.');
      node('visibility-proposal-status').hidden = false;
      return;
    }
    node('visibility-confirm-proposals').disabled = true;
    try {
      await request('/api/visibilidad/confirmar', {reviewed: true});
      node('visibility-proposals-reviewed').checked = false;
      await review();
    } catch (error) { node('visibility-proposal-status').hidden = false; write('visibility-proposal-status', error.message); }
    finally { node('visibility-confirm-proposals').disabled = false; }
  });
  node('visibility-results').addEventListener('click', () => results());
  node('visibility-confirm-second').addEventListener('click', async () => {
    if (!node('visibility-second-reviewed').checked) {
      write('visibility-second-status', 'Marca la casilla después de revisar y guardar el segundo lote.'); return;
    }
    node('visibility-confirm-second').disabled = true;
    try {
      await request('/api/visibilidad/confirmar', {reviewed: true, batch: 'revision_visual'});
      node('visibility-second-reviewed').checked = false;
      await review();
    } catch (error) { write('visibility-second-status', error.message); }
    finally { node('visibility-confirm-second').disabled = false; }
  });
  node('visibility-train').addEventListener('click', async () => {
    node('visibility-train').disabled = true;
    write('visibility-job-status', 'Comprobando revisión y particiones…');
    try {
      const job = await request('/api/jobs', {action: 'train', pipeline: 'visibilidad_foto_v1'});
      activeJob = job.id; await poll();
    } catch (error) { write('visibility-job-status', error.message); node('visibility-train').disabled = false; }
  });
  document.querySelectorAll('[data-tab="visibilidad-foto"]').forEach(button => button.addEventListener('click', () => { if (!timer) poll(); }));
})();
