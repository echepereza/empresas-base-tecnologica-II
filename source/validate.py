#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validaciones del build de ebt-2 (criterios de éxito del prompt)."""
import os
import re
import sys
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PAGES = ['index.html', 'repaso-final.html']
VOID = {'br', 'hr', 'img', 'input', 'link', 'meta', 'area', 'base', 'col',
        'embed', 'param', 'source', 'track', 'wbr'}

# Patrones de datos personales que NUNCA deben aparecer en el build.
PII_PATTERNS = [
    (r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', 'email'),
    (r'\bpadr[oó]n\b', 'padrón'),
    (r'\blegajo\b', 'legajo'),
    (r'ezeperezadamo', 'usuario'),
    (r'\bEzequiel\b', 'nombre'),
    (r'\bPerez Adamo\b', 'apellido'),
]

ok = True


def fail(msg):
    global ok
    ok = False
    print('  ✗ ' + msg)


def read(p):
    with open(p, encoding='utf-8') as fh:
        return fh.read()


class Balancer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.errors = 0

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if tag in self.stack:
            while self.stack and self.stack.pop() != tag:
                pass
        else:
            self.errors += 1


def check_wellformed(name, html):
    b = Balancer()
    b.feed(html)
    if b.errors or b.stack:
        fail(f'{name}: HTML no balanceado (errores={b.errors}, sin cerrar={b.stack[-5:]})')
    else:
        print(f'  ✓ {name}: HTML balanceado')


def check_mermaid(name, html):
    blocks = re.findall(r'<div class="mermaid">(.*?)</div>', html, re.DOTALL)
    bad = [b for b in blocks if '<' in b]
    if bad:
        fail(f'{name}: {len(bad)} diagrama(s) Mermaid con "<"')
    else:
        print(f'  ✓ {name}: {len(blocks)} diagramas Mermaid, 0 con "<"')


def check_toc(name, html):
    anchors = set(re.findall(r'href="#([^"]+)"', html))
    ids = set(re.findall(r'<section class="chapter" id="([^"]+)"', html))
    missing = [a for a in anchors if a and a not in ids]
    if missing:
        fail(f'{name}: anclas del índice sin sección destino: {missing}')
    else:
        print(f'  ✓ {name}: {len(anchors)} anclas del índice resuelven a secciones')
    # cada sección con id + data-title (para buscador y navegación)
    secs = re.findall(r'<section class="chapter"([^>]*)>', html)
    no_dt = [s for s in secs if 'data-title=' not in s]
    if no_dt:
        fail(f'{name}: {len(no_dt)} sección(es) sin data-title')
    else:
        print(f'  ✓ {name}: {len(secs)} secciones, todas con data-title (buscador OK)')


def check_images(name, html):
    refs = re.findall(r'<img[^>]+src="(img/[^"]+)"', html)
    missing = [r for r in refs if not os.path.exists(os.path.join(ROOT, r))]
    if missing:
        fail(f'{name}: {len(missing)} imagen(es) referenciada(s) sin archivo: {missing[:5]}')
    else:
        print(f'  ✓ {name}: {len(refs)} imágenes referenciadas, todas presentes en img/')
    # ningún <img> sin alt (accesibilidad)
    no_alt = re.findall(r'<img(?![^>]*\balt=)[^>]*>', html)
    if no_alt:
        fail(f'{name}: {len(no_alt)} <img> sin alt')


def check_brand(name, html):
    leftovers = html.count('Aprendizaje Autom')
    if leftovers:
        fail(f'{name}: quedaron {leftovers} referencias a "Aprendizaje Automático"')
    if 'href="resumen.html"' in html:
        fail(f'{name}: quedó un enlace roto a resumen.html')
    if not leftovers and 'href="resumen.html"' not in html:
        print(f'  ✓ {name}: marca EBT II, sin restos del template')
    for needle in ('serviceWorker', 'manifest.webmanifest', 'cdn.jsdelivr.net/npm/mermaid'):
        if needle not in html:
            fail(f'{name}: falta "{needle}"')


def check_pii():
    files = ['index.html', 'repaso-final.html', 'repaso-final.md']
    found = False
    for f in files:
        txt = read(os.path.join(ROOT, f))
        for pat, label in PII_PATTERNS:
            for m in re.findall(pat, txt, re.IGNORECASE):
                # ignorar "@media", "@import" y similares del CSS/JS del shell
                if label == 'email' and (m.startswith('@') or 'media' in m or 'import' in m):
                    continue
                fail(f'PII ({label}) en {f}: {m!r}')
                found = True
    if not found:
        print('  ✓ 0 filtraciones de datos personales (email/padrón/legajo/nombre)')


def main():
    for page in PAGES:
        path = os.path.join(ROOT, page)
        if not os.path.exists(path):
            fail(f'falta {page}')
            continue
        html = read(path)
        print(f'== {page} ({len(html)} bytes) ==')
        check_wellformed(page, html)
        check_mermaid(page, html)
        check_toc(page, html)
        check_images(page, html)
        check_brand(page, html)
    print('== privacidad ==')
    check_pii()
    print()
    print('RESULTADO:', 'TODO OK' if ok else 'HAY FALLAS')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
