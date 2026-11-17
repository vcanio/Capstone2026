"""Walmart Visión · Visor de alertas (aplicación cliente).

Comparte el motor oficial (`Aplicacion/inferencia.py`, `ocupacion_linea_a.py` y `best.pt`)
sin modificar la aplicación de auditoría técnica en `Aplicacion/`.
"""
import argparse
import base64
from contextlib import closing
from datetime import datetime, timezone
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
import json
import math
from pathlib import Path
import socket
import sqlite3
import sys
import threading
from urllib.parse import parse_qs, urlparse
import webbrowser
from xml.sax.saxutils import escape as xml_escape
import zipfile

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
APP_DIR = PROJECT_ROOT / 'Aplicacion'
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from inferencia import BusyError, MAX_BYTES, ModelRunner, read_photo  # noqa: E402
from ocupacion_linea_a import CALIBRATED_THRESHOLD_PCT, REVISION_LINEA_A  # noqa: E402

DEFAULT_CONFIDENCE = 0.60
DEFAULT_METHOD = 'yolo_paulo_v2'
DEFAULT_HISTORY_DB = HERE / '.runtime/historial_cliente.sqlite3'
EXPORT_HEADERS = [
    'Góndola / Archivo',
    'Resultado Góndola',
    'Nivel (1=Inferior)',
    'Resultado del análisis',
    'Severidad Operativa',
    'Índice Visual (0-100)',
    'Índice Bruto (0-100)',
    'Hueco Horizontal (%)',
    'Detalle del análisis',
]


class HistoryStore:
    """Persistencia compartida en SQLite para sesiones y revisiones de la app cliente."""

    def __init__(self, db_path: Path | str = DEFAULT_HISTORY_DB):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        with closing(self._connect()) as conn:
            conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS aisle_items (
                    id TEXT PRIMARY KEY,
                    item_order INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    aisle_state TEXT NOT NULL,
                    summary_json TEXT NOT NULL,
                    detections_json TEXT NOT NULL,
                    reviews_json TEXT NOT NULL,
                    preview_url TEXT NOT NULL DEFAULT ''
                )
                '''
            )
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def list_items(self) -> list[dict]:
        with self._lock, closing(self._connect()) as conn:
            rows = conn.execute(
                'SELECT id, item_order, name, updated_at, aisle_state, '
                'summary_json, detections_json, reviews_json, preview_url '
                'FROM aisle_items ORDER BY item_order ASC, updated_at ASC'
            ).fetchall()
        items = []
        for row in rows:
            summary = json.loads(row['summary_json'])
            detections = json.loads(row['detections_json'])
            reviews = json.loads(row['reviews_json'])
            result = {
                'store_summary': summary,
                'detections': detections,
            }
            if row['preview_url']:
                result['image_url'] = row['preview_url']
            items.append({
                'id': row['id'],
                'order': row['item_order'],
                'name': row['name'],
                'updated_at': row['updated_at'],
                'aisle_state': row['aisle_state'],
                'result': result,
                'reviews': reviews,
            })
        return items

    def upsert_items(self, items: list[dict]) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, closing(self._connect()) as conn:
            for idx, item in enumerate(items or (), 1):
                item_id = str(item.get('id') or '').strip()
                if not item_id or len(item_id) > 128:
                    continue
                result = item.get('result') or {}
                summary = result.get('store_summary') or item.get('store_summary') or {}
                detections = result.get('detections') or item.get('detections') or []
                reviews = item.get('reviews') or {}
                aisle_state = str(
                    item.get('aisle_state')
                    or summary.get('aisle_state')
                    or 'verificar'
                )
                preview_url = str(result.get('image_url') or '')
                if preview_url.startswith('blob:'):
                    preview_url = ''
                conn.execute(
                    '''
                    INSERT INTO aisle_items (
                        id, item_order, name, updated_at, aisle_state,
                        summary_json, detections_json, reviews_json, preview_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        item_order = excluded.item_order,
                        name = excluded.name,
                        updated_at = excluded.updated_at,
                        aisle_state = excluded.aisle_state,
                        summary_json = excluded.summary_json,
                        detections_json = excluded.detections_json,
                        reviews_json = excluded.reviews_json,
                        preview_url = CASE
                            WHEN excluded.preview_url != '' THEN excluded.preview_url
                            ELSE aisle_items.preview_url
                        END
                    ''',
                    (
                        item_id,
                        int(item.get('order') or idx),
                        str(item.get('name') or item_id),
                        str(item.get('updated_at') or now),
                        aisle_state,
                        json.dumps(summary, ensure_ascii=False),
                        json.dumps(detections, ensure_ascii=False),
                        json.dumps(reviews, ensure_ascii=False),
                        preview_url,
                    ),
                )
            conn.commit()
            return int(conn.execute('SELECT COUNT(*) FROM aisle_items').fetchone()[0])

    def delete_item(self, item_id: str) -> int:
        with self._lock, closing(self._connect()) as conn:
            conn.execute('DELETE FROM aisle_items WHERE id = ?', (str(item_id),))
            conn.commit()
            return int(conn.execute('SELECT COUNT(*) FROM aisle_items').fetchone()[0])

    def clear(self) -> int:
        with self._lock, closing(self._connect()) as conn:
            conn.execute('DELETE FROM aisle_items')
            conn.commit()
        return 0


def rows_from_history(items: list[dict]) -> list[list]:
    """Construir matriz tabular uniforme para exportaciones CSV/XLSX/PDF desde SQLite."""
    rows = [list(EXPORT_HEADERS)]
    sev_labels = {'critica': 'Crítica', 'alta': 'Alta', 'normal': 'Normal', 'verificar': 'Verificar'}
    for item in items:
        res = item.get('result') or {}
        summary = res.get('store_summary') or {}
        eff = summary.get('aisle_state') or item.get('aisle_state') or 'verificar'
        g_label = 'Con alertas' if eff == 'reponer' else 'Requiere revisión' if eff == 'verificar' else 'Sin alertas'
        dets = sorted(res.get('detections') or [], key=lambda d: int(d.get('id') or 0), reverse=True)
        if not dets:
            is_ne = res.get('photo_status') == 'no_evaluable'
            rows.append([
                item.get('name', ''),
                g_label,
                '',
                summary.get('aisle_label') or ('Foto no evaluable' if is_ne else 'No se detectaron niveles'),
                'Verificar',
                '',
                '',
                '',
                res.get('message') or summary.get('aisle_summary') or 'Sin lectura evaluable.',
            ])
        for det in dets:
            est = det.get('occupancy_estimate') or {}
            occ = det.get('occupancy') or {}
            diag = det.get('store_diagnosis') or {}
            pct = round(est['pct']) if isinstance(est.get('pct'), (int, float)) else ''
            raw = round(diag['raw_pct']) if isinstance(diag.get('raw_pct'), (int, float)) else (
                round(occ['raw_pct']) if isinstance(occ.get('raw_pct'), (int, float)) else ''
            )
            gap = round(occ['max_gap_pct']) if pct != '' and isinstance(occ.get('max_gap_pct'), (int, float)) else ''
            sev = sev_labels.get(diag.get('operational_severity') or occ.get('operational_severity'), 'Verificar')
            rows.append([
                item.get('name', ''),
                g_label,
                f"Nivel {det.get('id', '')}",
                diag.get('operational_label') or est.get('label') or 'Requiere revisión',
                sev,
                pct,
                raw,
                gap,
                f"{diag.get('headline', '')} - {diag.get('action', '')}".strip(' -'),
            ])
    return rows


def _col_letter(idx: int) -> str:
    chars = []
    n = idx + 1
    while n > 0:
        n, rem = divmod(n - 1, 26)
        chars.append(chr(65 + rem))
    return ''.join(reversed(chars))


def build_xlsx_bytes(rows: list[list], sheet_name: str = 'Alertas') -> bytes:
    """Generar archivo OpenXML `.xlsx` válido sin dependencias externas."""
    clean_rows = rows or [list(EXPORT_HEADERS)]
    max_cols = max((len(r) for r in clean_rows), default=len(EXPORT_HEADERS))
    col_widths = [14] * max_cols
    sheet_rows = []
    for r_idx, row in enumerate(clean_rows, 1):
        cells = []
        style = '1' if r_idx == 1 else '0'
        for c_idx, raw_val in enumerate(row):
            ref = f'{_col_letter(c_idx)}{r_idx}'
            val = '' if raw_val is None else raw_val
            col_widths[c_idx] = min(48, max(col_widths[c_idx], len(str(val)) + 3))
            if r_idx > 1 and isinstance(val, (int, float)) and not isinstance(val, bool) and math.isfinite(val):
                cells.append(f'<c r="{ref}" s="{style}"><v>{val}</v></c>')
            else:
                text = xml_escape(str(val))
                cells.append(f'<c r="{ref}" t="inlineStr" s="{style}"><is><t>{text}</t></is></c>')
        sheet_rows.append(f'<row r="{r_idx}">{"".join(cells)}</row>')

    cols_xml = ''.join(
        f'<col min="{i}" max="{i}" width="{w}" customWidth="1"/>'
        for i, w in enumerate(col_widths, 1)
    )
    safe_sheet = xml_escape(sheet_name[:31] or 'Alertas')
    worksheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<cols>{cols_xml}</cols>'
        f'<sheetData>{"".join(sheet_rows)}</sheetData>'
        '</worksheet>'
    )
    styles_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="2">'
        '<font><sz val="10"/><name val="Calibri"/></font>'
        '<font><b/><sz val="10"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font>'
        '</fonts>'
        '<fills count="3">'
        '<fill><patternFill patternType="none"/></fill>'
        '<fill><patternFill patternType="gray125"/></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FF0064CC"/></patternFill></fill>'
        '</fills>'
        '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="2">'
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
        '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/>'
        '</cellXfs>'
        '</styleSheet>'
    )
    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<sheets><sheet name="{safe_sheet}" sheetId="1" r:id="rId1"/></sheets>'
        '</workbook>'
    )
    content_types_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        '</Types>'
    )
    root_rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '</Relationships>'
    )
    wb_rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        '</Relationships>'
    )
    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', content_types_xml)
        zf.writestr('_rels/.rels', root_rels_xml)
        zf.writestr('xl/workbook.xml', workbook_xml)
        zf.writestr('xl/_rels/workbook.xml.rels', wb_rels_xml)
        zf.writestr('xl/styles.xml', styles_xml)
        zf.writestr('xl/worksheets/sheet1.xml', worksheet_xml)
    return buf.getvalue()


def _pdf_escape(text: str) -> str:
    normalized = (
        str(text or '')
        .replace('—', '-')
        .replace('–', '-')
        .replace('·', '|')
        .replace('…', '...')
    )
    safe = normalized.encode('latin-1', 'replace').decode('latin-1')
    return safe.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')


def build_pdf_bytes(rows: list[list], title: str = 'Walmart Vision - Reporte Ejecutivo') -> bytes:
    """Generar reporte PDF `%PDF-1.4` multipágina sin dependencias externas."""
    data_rows = rows[1:] if len(rows) > 1 else []
    gondolas = {str(r[0]) for r in data_rows if r}
    n_alert = sum(1 for r in data_rows if len(r) > 3 and 'Alerta' in str(r[3]))
    n_rev = sum(1 for r in data_rows if len(r) > 3 and ('revisión' in str(r[3]).lower() or 'evaluable' in str(r[3]).lower()))
    n_ok = sum(1 for r in data_rows if len(r) > 3 and 'Sin alerta' in str(r[3]))
    stamp = datetime.now().strftime('%Y-%m-%d %H:%M')

    pages_ops: list[list[str]] = []

    def new_page(page_num: int) -> list[str]:
        ops = [
            '0.00 0.39 0.80 rg',
            '36 730 540 36 re f',
            '1 1 1 rg',
            'BT /F2 13 Tf 48 744 Td (' + _pdf_escape(title) + ') Tj ET',
            '0.25 0.35 0.46 rg',
            f'BT /F1 9 Tf 36 712 Td ({_pdf_escape(f"Generado: {stamp} | Gondolas: {len(gondolas)} | Niveles: {len(data_rows)} | Alertas: {n_alert} | Revision: {n_rev} | Sin alertas: {n_ok} | Pag. {page_num}")}) Tj ET',
            '0.88 0.92 0.96 rg',
            '36 686 540 18 re f',
            '0.07 0.14 0.23 rg',
            'BT /F2 8.5 Tf 42 692 Td (' + _pdf_escape('Gondola') + ') Tj ET',
            'BT /F2 8.5 Tf 194 692 Td (' + _pdf_escape('Nivel') + ') Tj ET',
            'BT /F2 8.5 Tf 250 692 Td (' + _pdf_escape('Estado') + ') Tj ET',
            'BT /F2 8.5 Tf 410 692 Td (' + _pdf_escape('Sev.') + ') Tj ET',
            'BT /F2 8.5 Tf 466 692 Td (' + _pdf_escape('Ind.') + ') Tj ET',
            'BT /F2 8.5 Tf 512 692 Td (' + _pdf_escape('Hueco%') + ') Tj ET',
        ]
        return ops

    ops = new_page(1)
    y = 670
    if not data_rows:
        ops.append('0.2 0.25 0.32 rg')
        ops.append('BT /F1 10 Tf 42 666 Td (' + _pdf_escape('Sin analisis registrados para exportar.') + ') Tj ET')
        pages_ops.append(ops)
    else:
        for idx, r in enumerate(data_rows):
            if y < 56:
                pages_ops.append(ops)
                ops = new_page(len(pages_ops) + 1)
                y = 670
            if idx % 2 == 1:
                ops.append('0.96 0.98 1.00 rg')
                ops.append(f'36 {y - 4} 540 16 re f')
            gond = str(r[0] if len(r) > 0 else '')[:28]
            lvl = str(r[2] if len(r) > 2 else '')[:10]
            est = str(r[3] if len(r) > 3 else '')[:28]
            sev = str(r[4] if len(r) > 4 else '')[:9]
            pct = str(r[5] if len(r) > 5 and r[5] != '' else '-')[:5]
            gap = str(r[7] if len(r) > 7 and r[7] != '' else '-')[:5]
            ops.append('0.07 0.14 0.23 rg')
            ops.append(f'BT /F1 8 Tf 42 {y} Td ({_pdf_escape(gond)}) Tj ET')
            ops.append(f'BT /F1 8 Tf 194 {y} Td ({_pdf_escape(lvl)}) Tj ET')
            ops.append(f'BT /F1 8 Tf 250 {y} Td ({_pdf_escape(est)}) Tj ET')
            ops.append(f'BT /F1 8 Tf 410 {y} Td ({_pdf_escape(sev)}) Tj ET')
            ops.append(f'BT /F1 8 Tf 466 {y} Td ({_pdf_escape(pct)}) Tj ET')
            ops.append(f'BT /F1 8 Tf 512 {y} Td ({_pdf_escape(gap)}) Tj ET')
            y -= 16
        pages_ops.append(ops)

    objects: list[bytes] = []
    # 1: Catalog, 2: Pages, 3: F1 Helvetica, 4: F2 Helvetica-Bold, then (Page, Stream) pairs
    page_ids = []
    next_id = 5
    page_objs = []
    for ops_list in pages_ops:
        page_id = next_id
        stream_id = next_id + 1
        next_id += 2
        page_ids.append(page_id)
        stream_bytes = '\n'.join(ops_list).encode('latin-1', 'replace')
        page_objs.append((page_id, stream_id, stream_bytes))

    kids = ' '.join(f'{pid} 0 R' for pid in page_ids)
    objects.append(b'1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n')
    objects.append(f'2 0 obj\n<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>\nendobj\n'.encode('ascii'))
    objects.append(b'3 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>\nendobj\n')
    objects.append(b'4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>\nendobj\n')
    for page_id, stream_id, stream_bytes in page_objs:
        objects.append(
            f'{page_id} 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] '
            f'/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents {stream_id} 0 R >>\nendobj\n'.encode('ascii')
        )
        objects.append(
            f'{stream_id} 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n'.encode('ascii')
            + stream_bytes
            + b'\nendstream\nendobj\n'
        )

    out = bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n')
    offsets = [0]
    for obj in objects:
        offsets.append(len(out))
        out.extend(obj)
    xref_pos = len(out)
    out.extend(f'xref\n0 {len(objects) + 1}\n0000000000 65535 f \n'.encode('ascii'))
    for off in offsets[1:]:
        out.extend(f'{off:010d} 00000 n \n'.encode('ascii'))
    out.extend(
        f'trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n'.encode('ascii')
    )
    return bytes(out)


def _order_quadrilateral(points):
    pts = [(float(p[0]), float(p[1])) for p in points]
    by_y = sorted(pts, key=lambda p: p[1])
    top = sorted(by_y[:2], key=lambda p: p[0])
    bot = sorted(by_y[2:], key=lambda p: p[0])
    return top[0], top[1], bot[1], bot[0]


def _gap_polygon_for_span(display_polygon, x_gap_0: float, x_gap_1: float):
    if len(display_polygon) == 4:
        tl, tr, br, bl = _order_quadrilateral(display_polygon)
        top_dx = tr[0] - tl[0]
        bot_dx = br[0] - bl[0]
        if top_dx <= 1 or bot_dx <= 1:
            return None
        t0_top = max(0.0, min(1.0, (x_gap_0 - tl[0]) / top_dx))
        t1_top = max(0.0, min(1.0, (x_gap_1 - tl[0]) / top_dx))
        t0_bot = max(0.0, min(1.0, (x_gap_0 - bl[0]) / bot_dx))
        t1_bot = max(0.0, min(1.0, (x_gap_1 - bl[0]) / bot_dx))
        if t1_top <= t0_top and t1_bot <= t0_bot:
            return None
        p_tl = [round(tl[0] + t0_top * top_dx, 1), round(tl[1] + t0_top * (tr[1] - tl[1]), 1)]
        p_tr = [round(tl[0] + t1_top * top_dx, 1), round(tl[1] + t1_top * (tr[1] - tl[1]), 1)]
        p_br = [round(bl[0] + t1_bot * bot_dx, 1), round(bl[1] + t1_bot * (br[1] - bl[1]), 1)]
        p_bl = [round(bl[0] + t0_bot * bot_dx, 1), round(bl[1] + t0_bot * (br[1] - bl[1]), 1)]
        return [p_tl, p_tr, p_br, p_bl]
    xs = [float(p[0]) for p in display_polygon]
    ys = [float(p[1]) for p in display_polygon]
    x0 = max(min(xs), min(max(xs), x_gap_0))
    x1 = max(min(xs), min(max(xs), x_gap_1))
    if x1 - x0 <= 1:
        return None
    y0, y1 = round(min(ys), 1), round(max(ys), 1)
    return [[round(x0, 1), y0], [round(x1, 1), y0], [round(x1, 1), y1], [round(x0, 1), y1]]


def _attach_gap_spans(image_body: bytes, detections: list[dict], min_gap_pct: float = 10.0) -> None:
    """Calcular tramos horizontales de hueco por nivel para el visor visual."""
    if not detections:
        return
    try:
        import cv2
        import numpy as np
        from ocupacion_linea_a import compute_cell_maps, extract_cell_features, gondola_feature_bounds
        from ocupacion_paulo import Analyzer

        image = read_photo(image_body)
        rgb = np.asarray(image)
        analyzer = Analyzer(rgb, version='v2', front_mode=True)
        scale_x = analyzer.rgb.shape[1] / max(1, image.width)
        features = []
        for det in detections:
            poly = det.get('display_polygon') or []
            if len(poly) < 3:
                features.append(None)
                continue
            mask = np.zeros((image.height, image.width), dtype='uint8')
            pts = np.rint(np.asarray(poly, dtype=np.float32)).astype('int32')
            cv2.fillPoly(mask, [pts], 1)
            features.append(extract_cell_features(analyzer, mask))
        bounds = gondola_feature_bounds([f for f in features if f is not None])
        for det, feat in zip(detections, features):
            det['gap_spans'] = []
            poly = det.get('display_polygon') or []
            if feat is None or len(poly) < 3:
                continue
            maps = compute_cell_maps(feat, bounds)
            valid_cols = maps['valid_cols']
            col_covered_full = maps['col_covered_full']
            idxs = np.flatnonzero(valid_cols)
            if len(idxs) == 0:
                continue
            arr = np.asarray(col_covered_full[idxs], dtype=bool).copy()
            if len(arr) >= 3:
                for idx in range(1, len(arr) - 1):
                    if arr[idx] and (not arr[idx - 1]) and (not arr[idx + 1]):
                        arr[idx] = False
            n_total = max(1, col_covered_full.shape[0])
            n_valid = len(arr)
            bx, _, bw, _ = feat['bounds']
            i = 0
            while i < n_valid:
                if not arr[i]:
                    j = i
                    while j < n_valid and not arr[j]:
                        j += 1
                    pct = 100.0 * (j - i) / n_valid
                    if pct >= min_gap_pct:
                        c0, c1 = int(idxs[i]), int(idxs[j - 1]) + 1
                        x0 = (bx + (c0 / n_total) * bw) / scale_x
                        x1 = (bx + (c1 / n_total) * bw) / scale_x
                        gap_poly = _gap_polygon_for_span(poly, x0, x1)
                        if gap_poly is not None:
                            det['gap_spans'].append({
                                'start': round(i / n_valid, 4),
                                'end': round(j / n_valid, 4),
                                'pct': round(pct, 1),
                                'polygon': gap_poly,
                            })
                    i = j
                else:
                    i += 1
    except Exception:
        for det in detections:
            det.setdefault('gap_spans', [])


def store_diagnosis(detection: dict) -> dict:
    """Describir alertas visuales sin prescribir acciones de reposición."""
    est = detection.get('occupancy_estimate') or {}
    occ = detection.get('occupancy') or {}
    pct = est.get('pct')
    evaluable = isinstance(pct, (int, float)) and math.isfinite(pct)
    state = (est.get('state') or 'revisar') if evaluable else 'revisar'
    max_gap = occ.get('max_gap_pct')
    hyb_body = occ.get('hyb_body_pct')
    fill_pct = occ.get('fill_pct')
    pattern = occ.get('signal_pattern')
    near_frame = bool(detection.get('near_frame'))
    raw_pct = occ.get('raw_pct', pct if evaluable else None)

    if state == 'reponer':
        sev_occ = occ.get('operational_severity')
        if sev_occ in ('critica', 'alta'):
            severity = sev_occ
        elif (isinstance(raw_pct, (int, float)) and raw_pct <= 15.0) or (
            isinstance(max_gap, (int, float)) and max_gap >= 60.0
        ):
            severity = 'critica'
        else:
            severity = 'alta'
        if (pct is not None and pct <= 12.0) or (hyb_body is not None and hyb_body < 15.0):
            headline = 'Posible ausencia de producto visible'
        elif (
            max_gap is not None and max_gap >= 45.0 and
            (fill_pct is None or (100.0 - max_gap) <= fill_pct + 5.0)
        ):
            headline = f'Hueco visual estimado en el {round(max_gap)} % del frente'
        elif max_gap is not None and max_gap >= 30.0:
            headline = f'Posible baja disponibilidad (hueco de {round(max_gap)} % del ancho)'
        else:
            headline = 'Índice visual bajo el umbral de alerta'
        return {
            'operational_state': 'reponer',
            'operational_label': 'Alerta por baja disponibilidad',
            'operational_severity': severity,
            'raw_pct': raw_pct,
            'headline': headline,
            'action': 'Revisa la foto y los contornos para confirmar la alerta.',
        }

    if state == 'suficiente':
        gap_note = (
            f'Frente continuo cubierto ({round(100.0 - max_gap)} % del ancho con producto).'
            if isinstance(max_gap, (int, float)) else 'El análisis de esta foto no generó una alerta en este nivel.'
        )
        return {
            'operational_state': 'suficiente',
            'operational_label': 'Sin alerta visual',
            'operational_severity': 'normal',
            'raw_pct': raw_pct,
            'headline': 'Sin alerta visual detectada',
            'action': gap_note,
        }

    if near_frame:
        headline = 'Estante en el borde de la foto'
        action = 'Revisa el encuadre y toma otra foto que muestre el nivel completo.'
    elif pattern == 'foreground_occlusion':
        headline = 'Zona obstruida frente al estante'
        action = 'Una persona o carro tapa parte del nivel; toma otra foto despejada.'
    elif pattern in ('hollow_banner', 'upper_band_only'):
        headline = 'Patrón visual ambiguo en el nivel'
        action = 'Revisa la visibilidad del nivel y toma otra foto si hace falta.'
    else:
        headline = 'Lectura visual ambigua'
        action = 'Revisa la foto; si no hay evidencia suficiente, registra el nivel como no evaluable.'
    return {
        'operational_state': 'revisar',
        'operational_label': 'Requiere revisión' if evaluable else 'No evaluable',
        'operational_severity': 'verificar',
        'raw_pct': raw_pct,
        'headline': headline,
        'action': action,
    }


def enrich_for_store(prediction: dict) -> dict:
    """Añadir resumen de alertas por nivel; conservar los códigos internos del motor."""
    detections = prediction.get('detections') or []
    reponer_ids = []
    revisar_ids = []
    suficiente_ids = []

    for det in detections:
        diag = store_diagnosis(det)
        det['store_diagnosis'] = diag
        st = diag['operational_state']
        if st == 'reponer':
            reponer_ids.append(det['id'])
        elif st == 'revisar':
            revisar_ids.append(det['id'])
        else:
            suficiente_ids.append(det['id'])

    if prediction.get('photo_status') == 'no_evaluable':
        aisle_state = 'verificar'
        aisle_label = 'Foto no evaluable'
        aisle_summary = prediction.get('message') or 'La calidad o visibilidad de la foto impide evaluar la góndola.'
    elif not detections:
        aisle_state = 'verificar'
        aisle_label = 'Sin niveles detectados'
        aisle_summary = 'Toma la foto de frente incluyendo toda la góndola.'
    elif reponer_ids:
        aisle_state = 'reponer'
        n_rep = len(reponer_ids)
        lv_str = f'nivel {reponer_ids[0]}' if n_rep == 1 else f'niveles {", ".join(map(str, reponer_ids))}'
        aisle_label = f'{n_rep} {"nivel con alerta" if n_rep == 1 else "niveles con alerta"}'
        aisle_summary = f'Posible baja disponibilidad en {lv_str}. Revisa la foto y los contornos.'
    elif revisar_ids:
        aisle_state = 'verificar'
        n_rev = len(revisar_ids)
        aisle_label = f'{n_rev} {"nivel por verificar" if n_rev == 1 else "niveles por verificar"}'
        aisle_summary = 'Verifica los niveles con lectura ambigua.'
    else:
        aisle_state = 'suficiente'
        aisle_label = 'Sin alertas visuales detectadas'
        aisle_summary = f'El análisis no generó alertas en los {len(detections)} niveles detectados.'

    prediction['store_summary'] = {
        'aisle_state': aisle_state,
        'aisle_label': aisle_label,
        'aisle_summary': aisle_summary,
        'total_levels': len(detections),
        'reponer_count': len(reponer_ids),
        'revisar_count': len(revisar_ids),
        'suficiente_count': len(suficiente_ids),
        'reponer_levels': reponer_ids,
        'revisar_levels': revisar_ids,
        'threshold_pct': CALIBRATED_THRESHOLD_PCT,
        'revision': REVISION_LINEA_A,
    }
    return prediction


@lru_cache(maxsize=1)
def demo_catalog() -> dict:
    """Catálogo pequeño de fotos de ejemplo de desarrollo (nunca de test) para demostración en 1 clic."""
    export_dir = PROJECT_ROOT / 'Datos/Preparados/V3/v3_20261105_012333_53df4a59/exportacion_71b4668d/images'
    candidates = [
        ('gondola_pasillo_01', 'Pasillo Snacks · Góndola 1', 'lider_express_020_A_vacios.png'),
        ('gondola_pasillo_02', 'Pasillo Despensa · Góndola 2', 'R238__2710_ma_110.jpg'),
        ('gondola_pasillo_03', 'Pasillo Bebidas · Góndola 3', 'lider_express_046_D_superior_vacio.png'),
        ('gondola_pasillo_04', 'Pasillo Abarrotes · Góndola 4', 'lider_2_122_0_original.jpg'),
    ]
    items = []
    by_id = {}
    if export_dir.is_dir():
        dev_dirs = [export_dir / sub for sub in ('train', 'val_real', 'val_sintetica', 'val')
                    if (export_dir / sub).is_dir()]
        for demo_id, label, filename in candidates:
            for d in dev_dirs:
                target = d / filename
                if target.is_file():
                    rec = {'id': demo_id, 'label': label, 'filename': filename, 'path': str(target)}
                    items.append({'id': demo_id, 'label': label, 'filename': filename})
                    by_id[demo_id] = rec
                    break
    return {'items': items, 'by_id': by_id}


class ClientHandler(BaseHTTPRequestHandler):
    def local_request(self):
        host = self.headers.get('Host', '')
        allowed = {f'localhost:{self.server.server_port}', f'127.0.0.1:{self.server.server_port}'}
        if host in allowed:
            return self.headers.get('Origin', f'http://{host}') == f'http://{host}'
        normalized = host.strip().lower()
        tunnel_hosts = getattr(self.server, 'allow_hosts', set())
        if normalized in tunnel_hosts:
            return self.headers.get('Origin', f'https://{normalized}') == f'https://{normalized}'
        return False

    def send(self, body, status=200, content_type='application/json; charset=utf-8', extra_headers=None):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False, allow_nan=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        for k, v in (extra_headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _history_store(self) -> HistoryStore:
        store = getattr(self.server, 'history_store', None)
        if store is None:
            store = HistoryStore(getattr(self.server, 'history_db_path', DEFAULT_HISTORY_DB))
            self.server.history_store = store
        return store

    def _read_json_body(self) -> dict:
        length = int(self.headers.get('Content-Length', '0'))
        if length == 0:
            return {}
        if not 0 < length <= MAX_BYTES:
            raise ValueError('El cuerpo supera el límite permitido de 10 MB.')
        raw = self.rfile.read(length)
        if len(raw) != length:
            raise ValueError('Carga JSON incompleta.')
        return json.loads(raw.decode('utf-8'))

    def do_GET(self):
        if not self.local_request():
            return self.send({'error': 'Solo se permite el acceso local.'}, 403)
        route = urlparse(self.path)
        path = route.path
        if path == '/':
            return self.send((HERE / 'interfaz_cliente.html').read_bytes(), content_type='text/html; charset=utf-8')
        if path in ('/favicon.ico', '/favicon.svg', '/logo.svg'):
            return self.send((HERE / 'logo.svg').read_bytes(), content_type='image/svg+xml')
        if path == '/api/health':
            return self.send({
                'status': 'ok',
                'app': 'Walmart Visión · Visor de alertas',
                'revision': REVISION_LINEA_A,
                'threshold_pct': CALIBRATED_THRESHOLD_PCT,
                'analysis_ready': getattr(self.server, 'analysis_ready', False),
                'persistence': 'sqlite3',
            })
        if path == '/api/history':
            return self.send({'items': self._history_store().list_items(), 'persistence': 'sqlite3'})
        if path == '/api/export/xlsx':
            rows = rows_from_history(self._history_store().list_items())
            return self.send(
                build_xlsx_bytes(rows),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                extra_headers={'Content-Disposition': 'attachment; filename="alertas_disponibilidad.xlsx"'},
            )
        if path == '/api/export/pdf':
            rows = rows_from_history(self._history_store().list_items())
            return self.send(
                build_pdf_bytes(rows),
                content_type='application/pdf',
                extra_headers={'Content-Disposition': 'attachment; filename="reporte_ejecutivo.pdf"'},
            )
        if path == '/api/demo-photos':
            return self.send({'demos': demo_catalog()['items']})
        if path.startswith('/api/demo-photo/'):
            demo_id = path.rsplit('/', 1)[-1]
            entry = demo_catalog()['by_id'].get(demo_id)
            if not entry:
                return self.send({'error': 'Ejemplo no disponible.'}, 404)
            file_path = Path(entry['path'])
            mime = 'image/png' if file_path.suffix.lower() == '.png' else 'image/jpeg'
            return self.send(file_path.read_bytes(), content_type=mime)
        return self.send({'error': 'Ruta no disponible.'}, 404)

    def do_DELETE(self):
        if not self.local_request():
            return self.send({'error': 'Origen no autorizado.'}, 403)
        route = urlparse(self.path)
        if route.path != '/api/history':
            return self.send({'error': 'Ruta no disponible.'}, 404)
        params = parse_qs(route.query)
        item_id = (params.get('id') or [''])[0].strip()
        store = self._history_store()
        count = store.delete_item(item_id) if item_id else store.clear()
        return self.send({'status': 'ok', 'count': count})

    def do_POST(self):
        if not self.local_request():
            return self.send({'error': 'Origen no autorizado.'}, 403)
        route = urlparse(self.path)
        if route.path == '/api/history':
            try:
                payload = self._read_json_body()
                store = self._history_store()
                action = payload.get('action')
                if action == 'clear':
                    count = store.clear()
                elif action == 'delete' and payload.get('id'):
                    count = store.delete_item(str(payload['id']))
                else:
                    count = store.upsert_items(payload.get('items') or [])
                return self.send({'status': 'ok', 'count': count})
            except (ValueError, TypeError, json.JSONDecodeError) as error:
                return self.send({'error': str(error)}, 400)
        if route.path in ('/api/export/xlsx', '/api/export/pdf'):
            try:
                payload = self._read_json_body()
                rows = payload.get('rows')
                if not isinstance(rows, list) or not rows:
                    rows = rows_from_history(self._history_store().list_items())
                if route.path.endswith('/xlsx'):
                    return self.send(
                        build_xlsx_bytes(rows),
                        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        extra_headers={'Content-Disposition': 'attachment; filename="alertas_disponibilidad.xlsx"'},
                    )
                return self.send(
                    build_pdf_bytes(rows),
                    content_type='application/pdf',
                    extra_headers={'Content-Disposition': 'attachment; filename="reporte_ejecutivo.pdf"'},
                )
            except (ValueError, TypeError, json.JSONDecodeError) as error:
                return self.send({'error': str(error)}, 400)
        if route.path != '/api/predict':
            return self.send({'error': 'Ruta no disponible.'}, 404)
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= MAX_BYTES:
                self.close_connection = True
                return self.send({'error': 'Elige una foto de hasta 10 MB.'}, 413)
            if self.headers.get_content_type() not in ('image/jpeg', 'image/png', 'image/webp', 'application/octet-stream'):
                self.close_connection = True
                return self.send({'error': 'Usa una foto JPG, PNG o WebP.'}, 415)
            body = self.rfile.read(length)
            if len(body) != length:
                raise ValueError('La carga quedó incompleta. Vuelve a seleccionar la foto.')

            default_model = getattr(self.server.runner, 'manifest', {}).get('default_model')
            prediction = self.server.runner.analyze(
                body,
                model_id=default_model,
                confidence=DEFAULT_CONFIDENCE,
                method=DEFAULT_METHOD,
            )
            self.server.analysis_ready = True
            buffer = BytesIO()
            prediction.pop('image').save(buffer, format='JPEG', quality=90)
            prediction['image_url'] = 'data:image/jpeg;base64,' + base64.b64encode(buffer.getvalue()).decode('ascii')
            for extra_img in ('occupancy_image', 'edges_image', 'filtered_edges_image'):
                prediction.pop(extra_img, None)
            if prediction.get('detections'):
                _attach_gap_spans(body, prediction['detections'])
            enrich_for_store(prediction)
            item_id = (self.headers.get('X-Item-Id') or '').strip()
            if item_id:
                item_name = (self.headers.get('X-Item-Name') or item_id).strip()
                self._history_store().upsert_items([{'id': item_id, 'name': item_name, 'result': prediction}])
            self.send(prediction)
        except BusyError as error:
            self.send({'error': str(error)}, 409)
        except (ValueError, TypeError) as error:
            self.send({'error': str(error)}, 400)
        except Exception as error:
            print(f'Error al analizar en app cliente: {error}', file=sys.stderr, flush=True)
            self.send({'error': 'No se pudo analizar la foto. Intenta nuevamente con una toma despejada.'}, 500)

    def log_message(self, *_):
        pass


def pick_free_port(preferred: int = 8098) -> int:
    for candidate in range(preferred, preferred + 15):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex(('127.0.0.1', candidate)) != 0:
                return candidate
    return preferred


def _normalize_allowed_hosts(allow_hosts):
    normalized = set()
    for item in allow_hosts or ():
        host = str(item).strip().lower()
        for prefix in ('https://', 'http://'):
            if host.startswith(prefix):
                host = host[len(prefix):]
                break
        host = host.rstrip('/')
        if host:
            normalized.add(host)
    return normalized


def create_server(port=8098, directory=None, device='auto', host='127.0.0.1', allow_hosts=None, db_path=None):
    runner = ModelRunner(directory or APP_DIR, device=device)
    server = ThreadingHTTPServer((host, port), ClientHandler)
    server.runner = runner
    server.allow_hosts = _normalize_allowed_hosts(allow_hosts)
    server.history_store = HistoryStore(db_path or DEFAULT_HISTORY_DB)
    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8098)
    parser.add_argument('--host', choices=('127.0.0.1', '0.0.0.0'), default='127.0.0.1')
    parser.add_argument('--allow-host', action='append', default=[],
                        help='Hostname HTTPS público adicional autorizado (p. ej. túnel Cloudflare)')
    parser.add_argument('--open', action='store_true', help='Abrir navegador automáticamente')
    parser.add_argument('--check', action='store_true', help='Verificar configuración y pesos sin abrir servidor')
    parser.add_argument('--device', choices=('auto', 'cpu'), default='auto')
    parser.add_argument('--app-dir', type=Path, default=APP_DIR,
                        help='Carpeta del motor compartido y modelos (para Docker)')
    args = parser.parse_args()

    if args.check:
        runner = ModelRunner(args.app_dir, device=args.device)
        print(json.dumps({
            'status': 'ok',
            'app': 'Walmart Visión · Cliente Final',
            'models': len(runner.available()),
            'revision': REVISION_LINEA_A,
            'threshold_pct': CALIBRATED_THRESHOLD_PCT,
            'demo_photos': len(demo_catalog()['items']),
        }, ensure_ascii=False, indent=2))
        return

    port = pick_free_port(args.port)
    server = create_server(
        port=port,
        directory=args.app_dir,
        device=args.device,
        host=args.host,
        allow_hosts=args.allow_host,
    )
    url = f'http://127.0.0.1:{server.server_port}'
    print(f'Walmart Visión (Cliente Final) activo en: {url}', flush=True)
    if args.open:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
