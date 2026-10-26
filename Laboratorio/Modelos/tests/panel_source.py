"""Cargar los recursos reales del panel para las pruebas de comportamiento JS."""
from pathlib import Path
import re

HERE = Path(__file__).resolve().parents[1]


def read_panel():
    html = (HERE / 'panel.html').read_text(encoding='utf-8')

    def script(match):
        attrs, filename = match.groups()
        body = (HERE / 'static' / filename).read_text(encoding='utf-8')
        return f'<script{attrs}>\n{body}</script>'

    html = re.sub(r'<script([^>]*?) src="/static/([^"/]+)"></script>', script, html)
    css = (HERE / 'static/panel.css').read_text(encoding='utf-8')
    return html.replace('<link rel="stylesheet" href="/static/panel.css">', f'<style>\n{css}</style>')
