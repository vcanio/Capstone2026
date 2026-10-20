"""Genera el PDF de Trabajo_en_equipo.md. Requiere reportlab; no usa datos/modelos.

Ejecutar desde cualquier carpeta con un Python que tenga reportlab instalado.
Los saltos <!-- page --> del Markdown determinan las secciones imprimibles.
"""
from html import escape
from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Preformatted,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'Documentacion/Trabajo_en_equipo.md'
TARGET = SOURCE.with_suffix('.pdf')
WIDTH = A4[0] - 36 * mm
INK = colors.HexColor('#142639')
BLUE = colors.HexColor('#145A88')


def fonts():
    choices = [
        (Path('C:/Windows/Fonts'), ('arial.ttf', 'arialbd.ttf', 'consola.ttf')),
        (Path('/usr/share/fonts/truetype/dejavu'),
         ('DejaVuSans.ttf', 'DejaVuSans-Bold.ttf', 'DejaVuSansMono.ttf')),
    ]
    for directory, files in choices:
        if all((directory / f).exists() for f in files):
            for name, filename in zip(('Body', 'BodyBold', 'Code'), files):
                pdfmetrics.registerFont(TTFont(name, str(directory / filename)))
            pdfmetrics.registerFontFamily('Body', normal='Body', bold='BodyBold',
                                          italic='Body', boldItalic='BodyBold')
            return
    raise RuntimeError('Instalar Arial o DejaVu Sans para generar el PDF con Unicode.')


def inline(text):
    text = escape(text)
    text = re.sub(r'\[([^]]+)\]\(([^)]+)\)', r'<link href="\2" color="#145A88">\1</link>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'`([^`]+)`', r'<font name="Code" size="8.3">\1</font>', text)
    return text


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#CEDAE3'))
    canvas.line(18 * mm, 16 * mm, A4[0] - 18 * mm, 16 * mm)
    canvas.setFont('Body', 8)
    canvas.setFillColor(INK)
    canvas.drawString(18 * mm, 11 * mm, 'Walmart Computer Vision | Trabajo en equipo')
    canvas.drawRightString(A4[0] - 18 * mm, 11 * mm, str(doc.page))
    canvas.restoreState()


def build():
    fonts()
    body = ParagraphStyle('body', fontName='Body', fontSize=9.6, leading=13.3,
                          textColor=INK, spaceAfter=7, alignment=TA_LEFT)
    h1 = ParagraphStyle('title', parent=body, fontName='BodyBold', fontSize=24,
                        leading=28, spaceAfter=15)
    h2 = ParagraphStyle('h2', parent=body, fontName='BodyBold', fontSize=17,
                        leading=21, spaceBefore=3, spaceAfter=12, keepWithNext=True)
    h3 = ParagraphStyle('h3', parent=body, fontName='BodyBold', fontSize=11.4,
                        leading=15, spaceBefore=6, spaceAfter=6, keepWithNext=True)
    cell = ParagraphStyle('cell', parent=body, fontSize=8.3, leading=11.1,
                          wordWrap='CJK', spaceAfter=0)
    code = ParagraphStyle('code', fontName='Code', fontSize=7.6, leading=10.4,
                          backColor=colors.HexColor('#EFF4F7'), borderPadding=6,
                          spaceBefore=3, spaceAfter=10, textColor=INK)
    story = []
    lines = SOURCE.read_text(encoding='utf-8').splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line == '<!-- page -->':
            story.append(PageBreak()); i += 1; continue
        if line.startswith('```'):
            block = []; i += 1
            while i < len(lines) and not lines[i].startswith('```'):
                block.append(lines[i]); i += 1
            story.append(Preformatted('\n'.join(block), code, maxLineLength=105))
            i += 1; continue
        if line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                values = [v.strip() for v in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?', v) for v in values):
                    rows.append(values)
                i += 1
            count = len(rows[0])
            weights = [0.25, 0.40, 0.35] if count == 3 else [0.25, 0.75]
            table = Table([[Paragraph(inline(v), cell) for v in row] for row in rows],
                          colWidths=[WIDTH * v for v in weights], repeatRows=1, hAlign='LEFT')
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#DDEAF2')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F8FA')]),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 7),
                ('RIGHTPADDING', (0, 0), (-1, -1), 7),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LINEBELOW', (0, 0), (-1, 0), .6, colors.HexColor('#A9C6D9')),
            ]))
            story.extend((table, Spacer(1, 9)))
            continue
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            story.append(Paragraph(inline(line[level:].strip()), {1: h1, 2: h2}.get(level, h3)))
            i += 1; continue
        paragraph = [line]; i += 1
        while i < len(lines) and lines[i].strip() and not lines[i].startswith(('#', '|', '```', '<!--', '- ')) and not re.match(r'^\d+\. ', lines[i]):
            paragraph.append(lines[i].strip()); i += 1
        text = ' '.join(paragraph)
        if text.startswith('- '):
            story.append(Paragraph(inline(text[2:]), body, bulletText='•'))
        else:
            story.append(Paragraph(inline(text), body))
    doc = SimpleDocTemplate(str(TARGET), pagesize=A4, rightMargin=18 * mm,
                            leftMargin=18 * mm, topMargin=18 * mm, bottomMargin=23 * mm,
                            title='Cómo trabajar juntos en Walmart Computer Vision',
                            author='Equipo Walmart Computer Vision')
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(TARGET)


if __name__ == '__main__':
    build()
