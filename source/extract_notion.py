#!/usr/bin/env python3
"""
Extractor de una pagina publica de Notion -> Markdown.
Unica fuente: la pagina publicada EBT II. Pagina recursivamente por subpaginas.
Sin dependencias externas (urllib).
"""
import json
import sys
import time
import urllib.request

API = "https://www.notion.so/api/v3/loadPageChunk"
ROOT_ID = "1f4ca24f-3fd3-80b5-a3ac-ecbb1e60ce28"

blocks = {}          # id -> value(dict)  (acumulado global)
_fetched_pages = set()


def dashify(pid):
    p = pid.replace("-", "")
    if len(p) != 32:
        return pid
    return f"{p[0:8]}-{p[8:12]}-{p[12:16]}-{p[16:20]}-{p[20:32]}"


def post(payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API, data=data,
        headers={"Content-Type": "application/json",
                 "User-Agent": "Mozilla/5.0 notion-md-extractor"},
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa
            if attempt == 3:
                raise
            time.sleep(1.5 * (attempt + 1))


def load_page(page_id):
    """Carga (paginando) el arbol de un page_id y lo mergea en `blocks`."""
    page_id = dashify(page_id)
    if page_id in _fetched_pages:
        return
    _fetched_pages.add(page_id)
    cursor = {"stack": []}
    while True:
        res = post({
            "pageId": page_id,
            "limit": 100,
            "cursor": cursor,
            "chunkNumber": 0,
            "verticalColumns": False,
        })
        rm = res.get("recordMap", {}).get("block", {})
        for bid, wrap in rm.items():
            val = wrap.get("value", {})
            # notion.so devuelve value directamente; notion.site anida value.value
            if "value" in val and "id" in val.get("value", {}):
                val = val["value"]
            blocks[bid] = val
        cursor = res.get("cursor", {}) or {}
        if not cursor.get("stack"):
            break


# ---------- rich text ----------
def rt(arr):
    if not arr:
        return ""
    out = []
    for seg in arr:
        if not seg:
            continue
        text = seg[0]
        fmts = seg[1] if len(seg) > 1 else []
        pre, post_ = "", ""
        link = None
        for f in fmts or []:
            tag = f[0]
            if tag == "b":
                pre, post_ = "**" + pre, post_ + "**"
            elif tag == "i":
                pre, post_ = "*" + pre, post_ + "*"
            elif tag == "c":
                pre, post_ = "`" + pre, post_ + "`"
            elif tag == "s":
                pre, post_ = "~~" + pre, post_ + "~~"
            elif tag == "a":
                link = f[1] if len(f) > 1 else None
        piece = pre + text + post_
        if link:
            piece = f"[{piece}]({link})"
        out.append(piece)
    return "".join(out)


def title_of(b):
    return rt(b.get("properties", {}).get("title", []))


# ---------- render ----------
LANG = {}


def render(block_id, depth, lines, subpages):
    b = blocks.get(dashify(block_id))
    if not b:
        return
    t = b.get("type")
    props = b.get("properties", {})
    ind = "  " * depth

    if t == "page":
        # subpagina: la registramos para procesar como seccion aparte
        subpages.append(dashify(block_id))
        lines.append(f"{ind}- [[SUBPAGINA]] {title_of(b)}")
        return
    if t in ("header",):
        lines.append(f"\n## {title_of(b)}\n")
    elif t == "sub_header":
        lines.append(f"\n### {title_of(b)}\n")
    elif t == "sub_sub_header":
        lines.append(f"\n#### {title_of(b)}\n")
    elif t == "text":
        txt = title_of(b)
        lines.append(f"{ind}{txt}" if txt else "")
    elif t == "bulleted_list":
        lines.append(f"{ind}- {title_of(b)}")
    elif t == "numbered_list":
        lines.append(f"{ind}1. {title_of(b)}")
    elif t == "to_do":
        checked = props.get("checked", [["No"]])[0][0] == "Yes"
        lines.append(f"{ind}- [{'x' if checked else ' '}] {title_of(b)}")
    elif t == "toggle":
        lines.append(f"{ind}- **{title_of(b)}**")
    elif t == "quote":
        lines.append(f"{ind}> {title_of(b)}")
    elif t == "callout":
        lines.append(f"{ind}> {title_of(b)}")
    elif t == "code":
        lang = ""
        lp = props.get("language")
        if lp:
            lang = lp[0][0].lower()
        lines.append(f"```{lang}")
        lines.append(props.get("title", [[""]])[0][0] if props.get("title") else "")
        lines.append("```")
    elif t == "divider":
        lines.append("\n---\n")
    elif t == "image":
        src = ""
        if props.get("source"):
            src = props["source"][0][0]
        cap = title_of(b)
        lines.append(f"{ind}![{cap}]({src})")
    elif t == "bookmark":
        link = props.get("link", [[""]])[0][0]
        lines.append(f"{ind}[bookmark]({link}) {title_of(b)}")
    elif t == "table":
        render_table(b, ind, lines)
        return  # table maneja sus filas
    elif t in ("column_list", "column"):
        pass  # solo contenedor
    elif t == "collection_view" or t == "collection_view_page":
        lines.append(f"{ind}[BASE DE DATOS / collection_view: contenido no volcado]")
    else:
        txt = title_of(b)
        if txt:
            lines.append(f"{ind}{txt}")

    # hijos (excepto tablas ya manejadas)
    for cid in b.get("content", []) or []:
        render(cid, depth + 1, lines, subpages)


def render_table(b, ind, lines):
    rows = b.get("content", []) or []
    fmt = b.get("format", {}) or {}
    order = fmt.get("table_block_column_order", [])
    grid = []
    for rid in rows:
        rb = blocks.get(dashify(rid))
        if not rb or rb.get("type") != "table_row":
            continue
        cells = rb.get("properties", {})
        grid.append([rt(cells.get(col, [])) for col in order])
    if not grid:
        return
    header = grid[0]
    lines.append(f"\n{ind}| " + " | ".join(header) + " |")
    lines.append(f"{ind}| " + " | ".join(["---"] * len(header)) + " |")
    for row in grid[1:]:
        row = row + [""] * (len(header) - len(row))
        lines.append(f"{ind}| " + " | ".join(row) + " |")
    lines.append("")


def main():
    load_page(ROOT_ID)
    root = blocks[dashify(ROOT_ID)]
    all_lines = [f"# {title_of(root)}\n",
                 "> Fuente unica: pagina Notion publicada (EBT II). Extraido automaticamente.\n"]

    # BFS de paginas: raiz + subpaginas descubiertas
    queue = [(ROOT_ID, title_of(root), 1)]
    processed = set()
    while queue:
        pid, ptitle, level = queue.pop(0)
        pid = dashify(pid)
        if pid in processed:
            continue
        processed.add(pid)
        load_page(pid)
        pb = blocks.get(pid)
        if not pb:
            continue
        if pid != dashify(ROOT_ID):
            all_lines.append(f"\n{'#' * min(level, 6)} {ptitle}\n")
        subpages = []
        for cid in pb.get("content", []) or []:
            render(cid, 0, all_lines, subpages)
        for sp in subpages:
            spb = blocks.get(dashify(sp))
            queue.append((sp, title_of(spb) if spb else "(subpagina)", level + 1))

    out = "\n".join(all_lines)
    # colapsar lineas en blanco multiples
    while "\n\n\n" in out:
        out = out.replace("\n\n\n", "\n\n")
    with open("notion-ebt2.md", "w", encoding="utf-8") as f:
        f.write(out)

    # resumen de estructura para inspeccion
    headings = [l for l in all_lines if l.strip().startswith("#")]
    print(f"Paginas procesadas: {len(processed)}")
    print(f"Bloques totales:    {len(blocks)}")
    print(f"Caracteres MD:      {len(out)}")
    print("=== ESTRUCTURA (headings) ===")
    for h in headings:
        print(h.strip())


if __name__ == "__main__":
    main()
