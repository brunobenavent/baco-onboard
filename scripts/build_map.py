#!/usr/bin/env python3
"""Generate the self-contained interactive factory map from map.json."""
from __future__ import annotations

import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "diagrams" / "factory-map.json"
OUTPUT_PATH = ROOT / "diagrams" / "factory-map.html"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def build_svg(data: dict) -> str:
    nodes = {node["id"]: node for node in data["nodes"]}
    width = max(node["x"] for node in data["nodes"]) + 260
    edges = []
    for edge in data["edges"]:
        source = nodes[edge["from"]]
        target = nodes[edge["to"]]
        sx, sy = source["x"] + 210, source["y"] + 48
        tx, ty = target["x"], target["y"] + 48
        mx = (sx + tx) / 2
        css = "edge planned" if edge.get("planned") else "edge"
        edges.append(f'<path class="{css}" d="M {sx} {sy} H {mx} V {ty} H {tx}" marker-end="url(#arrow)"/>')

    cards = []
    for node in data["nodes"]:
        kind = node["kind"].lower().replace(" ", "-").replace("/", "-")
        cards.append(
            f'<g class="node kind-{esc(kind)}" data-id="{esc(node["id"])}" tabindex="0" role="button">'
            f'<rect x="{node["x"]}" y="{node["y"]}" width="210" height="96" rx="12"/>'
            f'<text class="kind" x="{node["x"] + 14}" y="{node["y"] + 21}">{esc(node["kind"])}</text>'
            f'<text class="label" x="{node["x"] + 14}" y="{node["y"] + 49}">{esc(node["label"])}</text>'
            f'<text class="hint" x="{node["x"] + 14}" y="{node["y"] + 73}">Seleccionar</text>'
            "</g>"
        )
    return f"""<svg viewBox="0 0 {width} 520" aria-label="Mapa de BACO Onboard">
      <defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z"/></marker></defs>
      <g class="edges">%s</g><g class="nodes">%s</g>
    </svg>""" % ("".join(edges), "".join(cards))


def build(data: dict) -> str:
    nodes_json = json.dumps(data["nodes"], ensure_ascii=False).replace("</", "<\\/")
    svg = build_svg(data)
    node_links = "".join(
        f'<button class="node-link" data-id="{esc(node["id"])}">{esc(node["label"])}</button>'
        for node in data["nodes"]
    )
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(data['title'])}</title>
<style>
:root {{ color-scheme: light dark; --bg:#0d1117; --panel:#151b23; --panel2:#1f2937; --text:#f0f6fc; --muted:#9da7b3; --line:#3d444d; --accent:#60a5fa; --planned:#fbbf24; --green:#34d399; }}
* {{ box-sizing:border-box }} body {{ margin:0; min-height:100vh; background:var(--bg); color:var(--text); font:14px/1.5 Inter,system-ui,sans-serif }}
header {{ padding:24px 28px 18px; border-bottom:1px solid var(--line) }} h1 {{ margin:0 0 4px; font-size:25px }} header p {{ margin:0;color:var(--muted) }}
.layout {{ display:grid; grid-template-columns:250px 1fr; min-height:calc(100vh - 91px) }} aside {{ border-right:1px solid var(--line); padding:18px 12px; background:var(--panel) }}
.search {{ width:100%; padding:9px 10px; border:1px solid var(--line); border-radius:8px; background:var(--bg); color:var(--text); margin-bottom:12px }}
.node-link {{ display:block; width:100%; text-align:left; padding:8px 10px; margin:2px 0; border:0; border-radius:7px; background:none; color:var(--muted); cursor:pointer }} .node-link:hover,.node-link.active {{ background:var(--panel2); color:var(--text) }}
main {{ padding:22px; overflow:auto }} .toolbar {{ display:flex; gap:8px; margin-bottom:12px; align-items:center }} .toolbar button {{ padding:7px 11px; border:1px solid var(--line); border-radius:7px; background:var(--panel); color:var(--text); cursor:pointer }}
.canvas {{ min-width:1000px; border:1px solid var(--line); border-radius:12px; background:radial-gradient(#253041 1px,transparent 1px); background-size:18px 18px; overflow:auto }} svg {{ display:block; width:2020px; height:520px }}
.node {{ cursor:pointer }} .node rect {{ fill:var(--panel); stroke:var(--line); stroke-width:2 }} .node:hover rect,.node.selected rect {{ stroke:var(--accent); stroke-width:3 }} .node.kind-planned-adapter rect {{ stroke:var(--planned); stroke-dasharray:7 5 }}
.node .kind {{ fill:var(--accent); font-size:12px; font-weight:600 }} .node.kind-planned-adapter .kind {{ fill:var(--planned) }} .node .label {{ fill:var(--text); font-size:15px; font-weight:700 }} .node .hint {{ fill:var(--muted); font-size:11px }}
.edge {{ fill:none; stroke:#718096; stroke-width:2 }} .edge.planned {{ stroke:var(--planned); stroke-dasharray:7 5 }} marker path {{ fill:#718096 }}
.details {{ margin-top:14px; padding:16px; border:1px solid var(--line); border-radius:10px; background:var(--panel); max-width:860px }} .details h2 {{ margin:0 0 4px }} .details p {{ color:var(--muted) }} .source {{ color:var(--accent); font-family:monospace }}
@media(max-width:720px) {{ .layout {{ grid-template-columns:1fr }} aside {{ border-right:0; border-bottom:1px solid var(--line) }} .node-link {{ display:inline-block; width:auto }} }}
</style></head><body>
<header><h1>{esc(data['title'])}</h1><p>{esc(data['subtitle'])}</p></header>
<div class="layout"><aside><input id="search" class="search" placeholder="Buscar un nodo…" aria-label="Buscar un nodo"><nav id="node-list">{node_links}</nav></aside>
<main><div class="toolbar"><button id="reset">Vista general</button><span id="status" aria-live="polite"></span></div><div class="canvas">{svg}</div><section id="details" class="details" aria-live="polite"><h2>Selecciona una parte</h2><p>Elige un nodo en el mapa o en la lista lateral.</p></section></main></div>
<script>const NODES={nodes_json};const byId=Object.fromEntries(NODES.map(n=>[n.id,n]));const nodes=[...document.querySelectorAll('.node')];const links=[...document.querySelectorAll('.node-link')];const details=document.getElementById('details');
function select(id,update=true){{const n=byId[id];if(!n)return;nodes.forEach(x=>x.classList.toggle('selected',x.dataset.id===id));links.forEach(x=>x.classList.toggle('active',x.dataset.id===id));details.innerHTML=`<h2>${{n.label}}</h2><p><strong>${{n.kind}}</strong></p><p>${{n.description}}</p><div class="source">Fuente: ${{n.source}}</div>`;if(update)history.replaceState(null,'','#view='+encodeURIComponent(id));}}
nodes.forEach(n=>n.addEventListener('click',()=>select(n.dataset.id)));nodes.forEach(n=>n.addEventListener('keydown',e=>{{if(e.key==='Enter'||e.key===' ')select(n.dataset.id)}}));links.forEach(n=>n.addEventListener('click',()=>select(n.dataset.id)));
document.getElementById('search').addEventListener('input',e=>{{const q=e.target.value.toLowerCase();links.forEach(x=>x.hidden=!x.textContent.toLowerCase().includes(q));}});document.getElementById('reset').addEventListener('click',()=>{{history.replaceState(null,'',location.pathname);nodes.forEach(x=>x.classList.remove('selected'));links.forEach(x=>x.classList.remove('active'));details.innerHTML='<h2>Vista general</h2><p>La fábrica recibe una petición, ejecuta un workflow, guarda evidencia y detiene los efectos externos hasta la aprobación.</p>';}});const initial=decodeURIComponent(location.hash.replace('#view=',''));if(initial)select(initial,false);</script></body></html>"""


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    OUTPUT_PATH.write_text(build(data), encoding="utf-8")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
