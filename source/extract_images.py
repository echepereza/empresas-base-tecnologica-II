#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Recolecta los bloques de imagen de la pagina publica de Notion, con su contexto
(pagina / h2 / h3 / h4), y los descarga a ebt-2/img/ via el proxy publico notion.site.
Emite source/images.json con el mapeo para insertarlos en el contenido."""
import json
import os
import re
import time
import urllib.request
import urllib.parse

API = "https://www.notion.so/api/v3/loadPageChunk"
SITE = "https://brick-softball-9f9.notion.site"
ROOT_ID = "1f4ca24f-3fd3-80b5-a3ac-ecbb1e60ce28"
SPACE_ID = "d03c929c-a9e6-457a-a240-38cafd044ea6"

HERE = os.path.dirname(os.path.abspath(__file__))
IMGDIR = os.path.join(os.path.dirname(HERE), 'img')

blocks = {}
spaceids = {}
_fetched = set()


def dashify(pid):
    p = pid.replace("-", "")
    return f"{p[0:8]}-{p[8:12]}-{p[12:16]}-{p[16:20]}-{p[20:32]}" if len(p) == 32 else pid


def post(payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(API, data=data, headers={
        "Content-Type": "application/json", "User-Agent": "Mozilla/5.0 notion"})
    for i in range(4):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read().decode())
        except Exception:
            if i == 3:
                raise
            time.sleep(1.5 * (i + 1))


def load_page(pid):
    pid = dashify(pid)
    if pid in _fetched:
        return
    _fetched.add(pid)
    cursor = {"stack": []}
    while True:
        res = post({"pageId": pid, "limit": 100, "cursor": cursor,
                    "chunkNumber": 0, "verticalColumns": False})
        rm = res.get("recordMap", {}).get("block", {})
        for bid, wrap in rm.items():
            sid = wrap.get("spaceId") or SPACE_ID
            val = wrap.get("value", {})
            if "value" in val and "id" in val.get("value", {}):
                val = val["value"]
            blocks[bid] = val
            spaceids[bid] = sid
        cursor = res.get("cursor", {}) or {}
        if not cursor.get("stack"):
            break


def rt(arr):
    return "".join(s[0] for s in (arr or []) if s)


def title_of(b):
    return rt(b.get("properties", {}).get("title", []))


images = []


def walk(block_id, ctx):
    b = blocks.get(dashify(block_id))
    if not b:
        return
    t = b.get("type")
    props = b.get("properties", {})
    if t in ("header",):
        ctx = dict(ctx, h2=title_of(b), h3="", h4="")
    elif t == "sub_header":
        ctx = dict(ctx, h3=title_of(b), h4="")
    elif t == "sub_sub_header":
        ctx = dict(ctx, h4=title_of(b))
    elif t == "image":
        src = props.get("source", [[""]])[0][0]
        cap = title_of(b)
        images.append({"idx": len(images), "block_id": dashify(block_id),
                       "source": src, "caption": cap, **ctx})
    for cid in b.get("content", []) or []:
        walk(cid, ctx)


def main():
    load_page(ROOT_ID)
    # BFS de paginas (raiz + subpaginas)
    queue = [(ROOT_ID, title_of(blocks[dashify(ROOT_ID)]))]
    processed = set()
    while queue:
        pid, ptitle = queue.pop(0)
        pid = dashify(pid)
        if pid in processed:
            continue
        processed.add(pid)
        load_page(pid)
        pb = blocks.get(pid)
        if not pb:
            continue
        ctx = {"page": ptitle, "h2": "", "h3": "", "h4": ""}
        for cid in pb.get("content", []) or []:
            walk(cid, ctx)
        # encolar subpaginas
        for cid in pb.get("content", []) or []:
            cb = blocks.get(dashify(cid))
            if cb and cb.get("type") == "page":
                queue.append((cid, title_of(cb)))

    os.makedirs(IMGDIR, exist_ok=True)
    print(f"Imagenes encontradas: {len(images)}")
    ok = 0
    for im in images:
        src = im["source"]
        bid = im["block_id"]
        # nombre de archivo estable
        m = re.search(r'attachment:([0-9a-f-]+):([^:?]+)', src)
        if m:
            uuid, fname = m.group(1), m.group(2)
        else:
            uuid, fname = bid, os.path.basename(urllib.parse.urlparse(src).path) or "image.png"
        ext = os.path.splitext(fname)[1] or ".png"
        out_name = f"{im['idx']:02d}-{uuid[:8]}{ext}"
        im["file"] = out_name
        url = (f"{SITE}/image/{urllib.parse.quote(src, safe='')}"
               f"?table=block&id={bid}&spaceId={spaceids.get(bid, SPACE_ID)}&width=1200&cache=v2")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
                ct = r.headers.get("Content-Type", "")
            with open(os.path.join(IMGDIR, out_name), "wb") as f:
                f.write(data)
            im["bytes"] = len(data)
            im["content_type"] = ct
            ok += 1
            print(f"  OK  {out_name}  {len(data)}B  {ct}  [{im['page']} > {im['h3'] or im['h2']}]")
        except Exception as e:
            im["error"] = str(e)
            print(f"  ERR {out_name}  {e}")
    with open(os.path.join(HERE, "images.json"), "w", encoding="utf-8") as f:
        json.dump(images, f, ensure_ascii=False, indent=2)
    print(f"Descargadas OK: {ok}/{len(images)} -> {IMGDIR}")


if __name__ == "__main__":
    main()
