#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ensambla la PWA de EBT II (Empresas de Base Tecnológica) reutilizando el shell
probado de aprendizaje-automatico/index.html (todo su CSS/JS: buscador, notas,
resaltador, modo oscuro, service worker) y reemplazando SOLO el contenido, el
índice y la marca.

Genera:
  - index.html          (apunte completo, app PWA)
  - repaso-final.html   (repaso compacto: el mínimo para el final)
  - repaso-final.md     (mirror en Markdown, fuente portable)

Fuente única de contenido: la página de Notion "EBT II | Empresas de Base
Tecnológica" (ver source/notion-ebt2.md). El contenido se escribe UNA sola vez en
content/part-*.html. Los diagramas van como <div class="mermaid">...</div>
(evitar '<' literal adentro).
"""
import os
import re
import glob
import html as htmllib

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, '..', 'aprendizaje-automatico', 'index.html')

ACCENT = '#0d9488'

ROOT_LIGHT = """:root {
      color-scheme: light;
      --bg: #f5f7f6;
      --surface: #ffffff;
      --surface-2: #eaf1ef;
      --ink: #14201d;
      --muted: #5d6b66;
      --line: #dbe6e2;
      --accent: #0d9488;
      --accent-2: #d2efe9;
      --accent-ink: #0f766e;
      --warm: #9b5f1d;
      --warm-bg: #fbe4c9;
      --danger: #a23b3b;
      --danger-bg: #fbe3e0;
      --blue: #3f5bb2;
      --blue-bg: #e7ecfb;
      --hl-yellow: #ffe08a;
      --hl-mint: #b7ecc6;
      --hl-pink: #ffc1d2;
      --hl-blue: #bcd7ff;
      --shadow: 0 18px 55px rgba(15, 60, 50, .10);
      --radius: 18px;
      --sidebar: 300px;
    }"""

ROOT_DARK = """html[data-theme="dark"] {
      color-scheme: dark;
      --bg: #0e1614;
      --surface: #14201d;
      --surface-2: #1c2a27;
      --ink: #eef4f1;
      --muted: #9fb1ab;
      --line: #26332f;
      --accent: #2dd4bf;
      --accent-2: #123029;
      --accent-ink: #99f6e4;
      --warm: #f0b766;
      --warm-bg: #3b2c19;
      --danger: #f3a29a;
      --danger-bg: #3e2422;
      --blue: #9bb0f7;
      --blue-bg: #1e2440;
      --hl-yellow: #725d19;
      --hl-mint: #1f5a37;
      --hl-pink: #71384b;
      --hl-blue: #294f78;
      --shadow: 0 18px 55px rgba(0, 0, 0, .30);
    }"""

INJECTED_STYLE = """  <style>
    pre.code { margin: 16px 0; padding: 15px 18px; overflow-x: auto; border: 1px solid var(--line); border-radius: 12px; background: var(--surface-2); color: var(--ink); font-size: 13.5px; line-height: 1.55; -webkit-overflow-scrolling: touch; }
    pre.code code { padding: 0; background: transparent; font-size: inherit; }
    .diagram { margin: 22px 0; padding: 16px 14px 12px; overflow-x: auto; border: 1px solid var(--line); border-radius: 16px; background: #f6faf9; }
    .diagram .mermaid { display: flex; justify-content: center; min-width: 0; text-align: center; }
    .diagram img { display: block; max-width: 100%; height: auto; margin: 0 auto; }
    .diagram figcaption { margin-top: 10px; color: #4a5a55; font-size: 12.5px; line-height: 1.45; text-align: center; }
    html[data-theme="dark"] .diagram { background: #eef4f1; border-color: #b9c8c3; }
    html[data-theme="dark"] .diagram figcaption { color: #4a5a55; }
    .exam-answer { margin: 18px 0; padding: 15px 18px; border-left: 4px solid var(--accent); border-radius: 0 12px 12px 0; background: var(--accent-2); color: var(--accent-ink); }
    .exam-answer strong { color: inherit; }
    .cmp { display: grid; gap: 12px; margin: 18px 0; }
    @media (min-width: 720px) { .cmp.two { grid-template-columns: 1fr 1fr; } }
    .formula { margin: 14px 0; padding: 12px 16px; border: 1px dashed var(--accent); border-radius: 12px; background: var(--surface-2); font-size: 15px; text-align: center; }
    .example-box { margin: 18px 0; padding: 14px 18px; border-left: 4px solid var(--warm); border-radius: 0 12px 12px 0; background: var(--warm-bg); color: var(--ink); }
    .example-box strong { color: inherit; }
    .cmp.two > figure.diagram { margin: 0; }
    /* Circulos concentricos TAM/SAM/SOM */
    .circles { margin: 22px 0; padding: 16px; border: 1px solid var(--line); border-radius: 16px; background: #f6faf9; display: grid; gap: 16px; align-items: center; }
    html[data-theme="dark"] .circles { background: #eef4f1; border-color: #b9c8c3; color: #14201d; }
    @media (min-width: 720px) { .circles { grid-template-columns: 260px 1fr; } }
    .circles svg { width: 100%; height: auto; max-width: 260px; margin: 0 auto; display: block; }
    .circles ul { margin: 0; }
    /* Grafico de linea (oferta/demanda) */
    .chart { margin: 22px 0; padding: 16px; border: 1px solid var(--line); border-radius: 16px; background: #f6faf9; }
    html[data-theme="dark"] .chart { background: #eef4f1; border-color: #b9c8c3; color: #14201d; }
    .chart svg { width: 100%; height: auto; max-width: 460px; display: block; margin: 0 auto; }
    /* Piramide inline con hover */
    .pyramid-block { margin: 22px 0; padding: 16px; border: 1px solid var(--line); border-radius: 16px; background: #f6faf9; display: grid; gap: 18px; align-items: center; overflow: visible; }
    html[data-theme="dark"] .pyramid-block { background: #eef4f1; border-color: #b9c8c3; color: #14201d; }
    @media (min-width: 720px) { .pyramid-block { grid-template-columns: 1fr 1fr; } }
    .pyr { display: flex; flex-direction: column; align-items: center; gap: 6px; }
    .pyr-band { position: relative; padding: 12px 10px; text-align: center; color: #fff; font-weight: 600; border-radius: 6px; cursor: help; transition: transform .15s; }
    .pyr-band:hover { transform: scale(1.03); }
    .pyr-tip { display: none; position: absolute; left: calc(100% + 8px); top: 50%; transform: translateY(-50%); width: 160px; background: #fff; color: #14201d; border: 1px solid #cbd5d1; border-radius: 8px; padding: 8px 10px; font-size: 12px; font-weight: 400; text-align: left; box-shadow: 0 8px 24px rgba(0,0,0,.15); z-index: 6; }
    .pyr-band:hover .pyr-tip { display: block; }
    .pyr-desc p { margin: .35em 0; }
    @media (max-width: 719px) { .pyr-tip { display: none !important; } }
    /* Taza de cafe (estructura de costos) */
    .cup-block { margin: 22px 0; padding: 16px; border: 1px solid var(--line); border-radius: 16px; background: #f6faf9; overflow: visible; }
    html[data-theme="dark"] .cup-block { background: #eef4f1; border-color: #b9c8c3; color: #14201d; }
    .cup-top { text-align: center; font-weight: 700; color: var(--accent-ink); border: 2px dashed #7fbdb3; border-radius: 10px; padding: 8px; margin: 0 auto 8px; max-width: 340px; }
    .cup { max-width: 360px; margin: 0 auto; display: flex; flex-direction: column; align-items: center; gap: 3px; }
    .cup-lid { width: 100%; height: 14px; background: #dfece9; border: 1px solid #b9c8c3; border-radius: 8px 8px 3px 3px; }
    .cup-band { position: relative; text-align: center; color: #fff; font-weight: 600; font-size: 13px; padding: 12px 8px; cursor: help; border-radius: 3px; }
    .cup-band:hover { filter: brightness(1.08); }
    .cup-tip { display: none; position: absolute; left: calc(100% + 8px); top: 50%; transform: translateY(-50%); width: 190px; background: #fff; color: #14201d; border: 1px solid #cbd5d1; border-radius: 8px; padding: 8px 10px; font-size: 12px; font-weight: 400; text-align: left; box-shadow: 0 8px 24px rgba(0,0,0,.15); z-index: 6; }
    .cup-band:hover .cup-tip { display: block; }
    @media (max-width: 719px) { .cup-tip { left: auto; right: 4px; top: 108%; transform: none; width: auto; max-width: 78vw; } }
    /* Tarjetas TRL */
    .trl-row { display: flex; gap: 10px; overflow-x: auto; padding: 6px 2px 12px; -webkit-overflow-scrolling: touch; }
    .trl-card { flex: 0 0 150px; border: 1px solid var(--line); border-radius: 12px; padding: 12px; background: var(--surface-2); }
    .trl-card .trl-n { display: inline-block; font-weight: 700; color: #fff; background: var(--accent); border-radius: 6px; padding: 2px 10px; margin-bottom: 8px; font-size: 13px; }
    .trl-card p { margin: 0; font-size: 12.5px; line-height: 1.4; }
    /* Matriz ERIC 2x2 */
    .eric { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 18px 0; }
    .eric .q { border: 1px solid var(--line); border-radius: 12px; padding: 14px; background: var(--surface-2); }
    .eric .q h4 { margin: 0 0 .3em; }
    body.hide-code pre.code { display: none; }
    body.hide-code pre.code + p { margin-top: 0; }
  </style>
"""

MERMAID_SCRIPT = """  <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
    mermaid.initialize({
      startOnLoad: true,
      securityLevel: 'loose',
      theme: 'base',
      themeVariables: {
        background: '#f6faf9',
        primaryColor: '#d2efe9',
        primaryBorderColor: '#0d9488',
        primaryTextColor: '#0f2a25',
        secondaryColor: '#e7ecfb',
        tertiaryColor: '#eaf1ef',
        lineColor: '#5f7a73',
        fontFamily: 'Inter, system-ui, sans-serif',
        fontSize: '15px'
      },
      flowchart: { htmlLabels: true, curve: 'basis' },
      sequence: { useMaxWidth: true }
    });
  </script>
  <script>
    (function () {
      var KEY = 'ebt2-hide-code';
      var btn = document.getElementById('code-toggle');
      var lbl = document.getElementById('code-toggle-label');
      function apply(hidden) {
        document.body.classList.toggle('hide-code', hidden);
        if (btn) { btn.classList.toggle('active', hidden); btn.setAttribute('aria-pressed', hidden ? 'true' : 'false'); }
        if (lbl) { lbl.textContent = hidden ? 'Fórmulas ocultas' : 'Fórmulas'; }
      }
      var hidden = localStorage.getItem(KEY) === '1';
      apply(hidden);
      if (btn) btn.addEventListener('click', function () {
        hidden = !hidden;
        localStorage.setItem(KEY, hidden ? '1' : '0');
        apply(hidden);
      });
    })();
  </script>
</body>"""

# Botón que se inyecta en la barra lateral (side-actions)
CODE_TOGGLE_BUTTON = """<button class="icon-button wide" id="code-toggle" type="button" aria-pressed="false" title="Mostrar u ocultar los bloques de fórmulas">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="m8 6-6 6 6 6"></path><path d="m16 6 6 6-6 6"></path></svg>
        <span id="code-toggle-label">Fórmulas</span>
      </button>"""

# Enlaces de navegación entre las dos vistas (mismo shell, distinto <main>),
# igual que aprendizaje-automatico alterna entre Apunte y Resumen.
NAV_TO_REPASO = ('<a class="icon-button wide" href="repaso-final.html" '
                 'title="Repaso compacto: el mínimo para el final">Repaso final</a>')
NAV_TO_APUNTE = ('<a class="icon-button wide" href="index.html" '
                 'title="Volver al apunte completo">Apunte</a>')

BRAND = 'EBT II'
DESC_APUNTE = ('Guía de estudio para los parciales y el final de EBT II (Empresas de '
               'Base Tecnológica), FIUBA: teoría, diagramas y machete.')
DESC_REPASO = ('Repaso final de EBT II (Empresas de Base Tecnológica), FIUBA: el mínimo '
               'para aprobar los parciales y el final.')


def read(path):
    with open(path, encoding='utf-8') as fh:
        return fh.read()


def write(path, data):
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(data)


def load_content():
    parts = sorted(glob.glob(os.path.join(HERE, 'content', 'part-*.html')))
    if not parts:
        raise SystemExit('No hay archivos content/part-*.html')
    chunks = [read(p).strip() for p in parts]
    return '\n\n'.join(chunks) + '\n'


def escape_code_blocks(markup):
    """<pre data-code="lang">raw</pre> -> <pre class=code><code>escaped</code></pre>"""
    def repl(m):
        lang = m.group(1) or 'text'
        inner = m.group(2)
        inner = inner.strip('\n')
        esc = inner.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        return ('<pre class="code" data-lang="%s"><code>%s</code></pre>'
                % (lang, esc))
    return re.sub(r'<pre data-code="([^"]*)">(.*?)</pre>', repl, markup,
                  flags=re.DOTALL)


# ---------------------------------------------------------------------------
# Shell compartido: mismo armazón (índice, notas, buscador, resaltador, tema)
# para el apunte (index.html) y para el repaso final (repaso-final.html). Solo
# cambian el contenido del <main> y el enlace de navegación de la barra lateral.
# ---------------------------------------------------------------------------
def build_shell(template, content_html, toc_html, nav_link, page_title=None,
                description=None):
    doc = template

    # palette
    doc = re.sub(r':root \{[^}]*\}', ROOT_LIGHT, doc, count=1)
    doc = re.sub(r'html\[data-theme="dark"\] \{[^}]*\}', ROOT_DARK, doc, count=1)

    # head branding
    doc = doc.replace('content="#167e9e"', 'content="%s"' % ACCENT)
    desc = description or DESC_APUNTE
    doc = re.sub(r'<meta name="description"[^>]*>',
                 '<meta name="description" content="%s">' % desc,
                 doc, count=1)
    doc = re.sub(r'<link rel="icon"[^>]*>',
                 '<link rel="icon" href="pwa-icon.svg" type="image/svg+xml">',
                 doc, count=1)
    doc = doc.replace('href="apple-touch-icon.png"', 'href="pwa-icon.svg"')

    # sidebar nav (índice)
    i = doc.index('<div class="nav-title">')
    j = doc.index('<div class="side-actions">')
    doc = doc[:i] + toc_html.strip() + '\n\n    ' + doc[j:]

    # main content
    a = doc.index('<main class="content" id="content">') + len('<main class="content" id="content">')
    b = doc.index('</main>', a)
    doc = doc[:a] + '\n' + content_html + '\n    ' + doc[b:]

    # inject styles + mermaid
    doc = doc.replace('</head>', INJECTED_STYLE + '</head>', 1)
    head, sep, tail = doc.rpartition('</body>')
    doc = head + MERMAID_SCRIPT[:-len('</body>')] + '</body>' + tail

    # barra lateral: el link "Resumen" del template se reemplaza por el toggle de
    # fórmulas + el enlace a la otra vista (apunte <-> repaso final).
    doc = doc.replace(
        '<a class="icon-button wide" href="resumen.html">Resumen</a>',
        CODE_TOGGLE_BUTTON + '\n      ' + nav_link,
        1)

    # marca en todos lados
    doc = doc.replace('Aprendizaje Automático', BRAND)

    if page_title:
        doc = re.sub(r'<title>[^<]*</title>', '<title>%s</title>' % page_title, doc, count=1)
    return doc


# ---------------------------------------------------------------------------
# Exportador HTML -> Markdown, con placeholders para code/mermaid
# (genera repaso-final.md, mirror portable del repaso).
# ---------------------------------------------------------------------------
class El:
    __slots__ = ('tag', 'attrs', 'children')

    def __init__(self, tag, attrs=None):
        self.tag = tag
        self.attrs = attrs or {}
        self.children = []


VOID = {'br', 'hr', 'img', 'input', 'link', 'meta'}


def parse_html(markup):
    root = El('root')
    stack = [root]
    tokens = re.findall(r'<!--[\s\S]*?-->|<![^>]*>|<[^>]+>|[^<]+', markup)
    for tok in tokens:
        if tok.startswith('<!--') or tok.startswith('<!'):
            continue
        if not tok.startswith('<'):
            stack[-1].children.append(tok)
            continue
        if tok.startswith('</'):
            m = re.match(r'</\s*([\w-]+)', tok)
            tag = m.group(1).lower() if m else ''
            while len(stack) > 1:
                node = stack.pop()
                if node.tag == tag:
                    break
            continue
        m = re.match(r'<\s*([\w-]+)', tok)
        if not m:
            continue
        name = m.group(1).lower()
        attrs = {}
        for a in re.finditer(r'([:\w-]+)(?:\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s"\'=<>`]+)))?', tok[1 + len(name):]):
            attrs[a.group(1).lower()] = htmllib.unescape(a.group(2) or a.group(3) or a.group(4) or '')
        node = El(name, attrs)
        stack[-1].children.append(node)
        if name not in VOID and not tok.endswith('/>'):
            stack.append(node)
    return root


def has_class(node, cls):
    return cls in (node.attrs.get('class', '') or '').split()


def clean(s):
    return re.sub(r'[ \t\r\n]+', ' ', s).strip()


def inline(node):
    if isinstance(node, str):
        return re.sub(r'[ \t\r\n]+', ' ', node)
    content = ''.join(inline(c) for c in node.children)
    t = node.tag
    if t in ('strong', 'b'):
        return '**%s**' % clean(content)
    if t in ('em', 'i'):
        return '*%s*' % clean(content)
    if t == 'code':
        return '`%s`' % clean(content)
    if t == 'a':
        return '[%s](%s)' % (clean(content), node.attrs.get('href', ''))
    if t == 'br':
        return '  \n'
    return content


def plain(node):
    if isinstance(node, str):
        return re.sub(r'[ \t\r\n]+', ' ', node)
    return ''.join(plain(c) for c in node.children)


def render_list(node, depth=0):
    ordered = node.tag == 'ol'
    lines = []
    n = 1
    for item in [c for c in node.children if isinstance(c, El) and c.tag == 'li']:
        nested = [c for c in item.children if isinstance(c, El) and c.tag in ('ul', 'ol')]
        primary = ''.join(inline(c) for c in item.children if c not in nested)
        marker = ('%d.' % n) if ordered else '-'
        lines.append('%s%s %s' % ('  ' * depth, marker, clean(primary)))
        for lst in nested:
            lines.append(render_list(lst, depth + 1).rstrip())
        n += 1
    return '\n'.join(lines) + '\n\n'


def render_table(node):
    rows = []
    for tr in _collect(node, 'tr'):
        cells = [clean(''.join(inline(c) for c in cell.children)).replace('|', '\\|')
                 for cell in tr.children if isinstance(cell, El) and cell.tag in ('th', 'td')]
        if cells:
            rows.append(cells)
    if not rows:
        return ''
    width = max(len(r) for r in rows)
    rows = [r + [''] * (width - len(r)) for r in rows]
    line = lambda r: '| ' + ' | '.join(r) + ' |'
    out = [line(rows[0]), line(['---'] * width)] + [line(r) for r in rows[1:]]
    return '\n'.join(out) + '\n\n'


def _collect(node, tag):
    found = []
    def rec(n):
        if isinstance(n, El):
            if n.tag == tag:
                found.append(n)
            else:
                for c in n.children:
                    rec(c)
    rec(node)
    return found


def render_children(node):
    return ''.join(render_block(c) for c in node.children)


def render_block(node):
    if isinstance(node, str):
        return (clean(node) + '\n\n') if node.strip() else ''
    t = node.tag
    if t == 'section':
        return render_section(node)
    if t == 'h1':
        return '# %s\n\n' % clean(plain(node))
    if t == 'h2':
        return '## %s\n\n' % clean(plain(node))
    if t == 'h3':
        return '### %s\n\n' % clean(plain(node))
    if t == 'h4':
        return '#### %s\n\n' % clean(plain(node))
    if t == 'p':
        return '%s\n\n' % clean(''.join(inline(c) for c in node.children))
    if t in ('ul', 'ol'):
        return render_list(node)
    if t == 'table':
        return render_table(node)
    if t == 'pre':
        ph = node.attrs.get('data-ph')
        if ph is not None:
            lang, code = PLACEHOLDERS[int(ph)]
            return '```%s\n%s\n```\n\n' % (lang, code)
        return '```\n%s\n```\n\n' % plain(node)
    if t == 'summary':
        return '**%s**\n\n' % clean(plain(node))
    if t in ('header', 'main', 'div', 'figure', 'details'):
        if t == 'div' and node.attrs.get('data-ph') is not None:
            code = PLACEHOLDERS[int(node.attrs['data-ph'])][1]
            return '```mermaid\n%s\n```\n\n' % code
        if t == 'figure' and has_class(node, 'diagram'):
            body = render_children(node)
            cap = _collect(node, 'figcaption')
            caption = ('*%s*\n\n' % clean(plain(cap[0]))) if cap else ''
            return body + caption
        if has_class(node, 'chapter-number') or has_class(node, 'chapter-head'):
            if has_class(node, 'chapter-number'):
                return ''
        return render_children(node)
    if t == 'figcaption':
        return ''
    return render_children(node)


def render_section(node):
    md = ('<a id="%s"></a>\n\n' % node.attrs['id']) if node.attrs.get('id') else ''
    for child in node.children:
        if isinstance(child, El) and has_class(child, 'chapter-head'):
            number_node = _first(child, lambda n: has_class(n, 'chapter-number'))
            heading = _first(child, lambda n: n.tag == 'h2')
            number = clean(plain(number_node)) if number_node else ''
            title = clean(plain(heading)) if heading else ''
            md += '## %s. %s\n\n' % (number, title)
        else:
            md += render_block(child)
    return md


def _first(node, pred):
    if isinstance(node, El) and pred(node):
        return node
    if isinstance(node, El):
        for c in node.children:
            r = _first(c, pred)
            if r:
                return r
    return None


PLACEHOLDERS = []


def build_markdown(raw_content):
    """raw_content tiene <pre data-code> y <div class=mermaid>. Se cambian por
    placeholders para que el parser naive nunca vea '<' adentro de código/diagramas."""
    global PLACEHOLDERS
    PLACEHOLDERS = []

    def stash_pre(m):
        lang = m.group(1) or 'text'
        PLACEHOLDERS.append((lang, m.group(2).strip('\n')))
        return '<pre data-ph="%d"></pre>' % (len(PLACEHOLDERS) - 1)

    def stash_mermaid(m):
        PLACEHOLDERS.append(('mermaid', m.group(1).strip('\n')))
        return '<div data-ph="%d"></div>' % (len(PLACEHOLDERS) - 1)

    tmp = re.sub(r'<pre data-code="([^"]*)">(.*?)</pre>', stash_pre, raw_content, flags=re.DOTALL)
    tmp = re.sub(r'<div class="mermaid">(.*?)</div>', stash_mermaid, tmp, flags=re.DOTALL)

    root = parse_html(tmp)
    main = El('main')
    main.children = root.children
    md = render_block(main)
    md = re.sub(r'\n{3,}', '\n\n', md).strip() + '\n'
    first_nl = md.find('\n')
    if md.startswith('# ') and first_nl != -1:
        md = md[:first_nl] + '\n\n[Abrir apunte](index.html)\n' + md[first_nl:]
    return md


# ---------------------------------------------------------------------------
def main():
    template = read(TEMPLATE)
    raw_content = load_content()
    toc_html = read(os.path.join(HERE, 'toc.html'))
    toc_repaso = read(os.path.join(HERE, 'toc-repaso.html'))

    content_html = escape_code_blocks(raw_content)
    raw_repaso = read(os.path.join(HERE, 'content', 'repaso-final.html'))
    repaso_content = escape_code_blocks(raw_repaso)

    # Apunte completo (index.html): índice del apunte, barra lateral -> Repaso final.
    index = build_shell(template, content_html, toc_html, NAV_TO_REPASO,
                        page_title='%s | Empresas de Base Tecnológica' % BRAND,
                        description=DESC_APUNTE)
    write(os.path.join(HERE, 'index.html'), index)

    # Repaso final (repaso-final.html): MISMO shell, con su PROPIO índice (anclas
    # in-page a las secciones del repaso) y barra lateral -> Apunte.
    repaso = build_shell(template, repaso_content, toc_repaso, NAV_TO_APUNTE,
                         page_title='Repaso final | %s' % BRAND,
                         description=DESC_REPASO)
    write(os.path.join(HERE, 'repaso-final.html'), repaso)

    # Mirror portable en Markdown del repaso.
    write(os.path.join(HERE, 'repaso-final.md'), build_markdown(raw_repaso))

    words = len(re.sub(r'<[^>]+>', ' ', content_html).split())
    rwords = len(re.sub(r'<[^>]+>', ' ', raw_repaso).split())
    print('OK  index.html + repaso-final.html + repaso-final.md')
    print('    ~%d palabras de apunte, ~%d palabras de repaso final' % (words, rwords))


if __name__ == '__main__':
    main()
