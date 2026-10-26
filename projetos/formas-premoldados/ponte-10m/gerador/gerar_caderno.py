#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Caderno de fabricação em PDF (A4 deitado) das formas do kit "Ponte pré-moldada de 10 m".

Monta saida/caderno/caderno_formas_ponte_10m.html com: capa, folhas de montagem de cada
forma, uma folha por peça de chapa (planificação cotada, dobras e furos) e as tabelas.
Depois imprime o PDF com o Chromium (Node + Playwright), pelo script imprimir_pdf.js.

Uso:  python3 gerar_caderno.py      (rodar depois de gerar_formas.py)
"""

import html
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import desenhos as dz                     # noqa: E402
import gerar_formas as gf                 # noqa: E402

DATA = "26/10/2026"
PROJETO = "Kit ponte pré-moldada 2 × 10 m · formas metálicas"
PASTA = os.path.join(gf.SAIDA, "caderno")
HTML_OUT = os.path.join(PASTA, "caderno_formas_ponte_10m.html")
PDF_OUT = os.path.join(PASTA, "caderno_formas_ponte_10m.pdf")

FORMAS = [
    ("Longarina", "F-LON", "Forma da longarina", "1 jogo: 4 módulos de 2,50 m (viga de 10 m)"),
    ("Placa de saia", "F-PLA", "Forma da placa de saia", "3 formas"),
    ("Painel de laje", "F-LAJ", "Forma do painel de laje", "2 formas"),
]

PASSOS = {
    "F-LON": [
        "Assentar os 4 fundos F-LON-05 sobre base de concreto nivelada (±2 mm) e aparafusar as "
        "cantoneiras F-LON-06 entre eles (3 parafusos M16 por junta).",
        "Posicionar os painéis F-LON-01 na largura da viga e prender a base com 4 parafusos M16 "
        "por painel, pelos rasgos do fundo.",
        "Aparafusar os painéis entre si pelas cantoneiras F-LON-03 (5 parafusos por junta).",
        "Fechar as pontas com as testeiras F-LON-08 (10 parafusos cada) e travar o topo com "
        "4 tirantes de 5/8\" por módulo, pelas orelhas F-LON-04.",
        "Solda só pelo lado de trás: nervuras com filete de 4 mm intermitente (50 a cada 150), "
        "cantoneiras com filete contínuo de 4 mm, orelhas com filete de 5 mm em volta.",
    ],
    "F-PLA": [
        "Soldar as 4 nervuras F-PLA-02 sob o fundo F-PLA-01, a 275, 825, 1375 e 1925 mm.",
        "Aparafusar os trilhos longos F-PLA-03 de ponta a ponta e os curtos F-PLA-04 entre eles "
        "(16 parafusos M16 por forma).",
        "Fixar os tubos-forma de 50 mm nos furos de 14 mm: 2 para içamento e 1 opcional para "
        "dreno.",
        "A face de baixo é a face do rio e também a face tracionada: armadura principal embaixo.",
    ],
    "F-LAJ": [
        "Soldar sob cada fundo F-LAJ-01 as 2 cantoneiras longitudinais F-LAJ-02, as 2 de topo "
        "F-LAJ-03 e as 4 nervuras F-LAJ-04, e soldar as 4 porcas M12 sob os furos de 14 mm.",
        "Assentar os 2 fundos sobre base de concreto nivelada (±2 mm), o segundo girado 180°, e "
        "aparafusar as cantoneiras de topo da junta (4 parafusos M16).",
        "Soldar a régua de chave F-LAJ-06 em cada trilho longo F-LAJ-05, entre as marcas do "
        "desenho, com o topo do chapéu a 25 mm da face.",
        "Aparafusar os 4 trilhos longos e os 2 trilhos de ponta F-LAJ-07 no fundo.",
        "Montar as 8 fôrmas de nicho (F-LAJ-08, 09 e 10), com gaxeta de espuma na base, e "
        "prender cada uma com barra roscada M12 na porca sob o fundo.",
        "Posicionar as réguas porta-insertos F-LAJ-11 a 900 e 3600 mm, com os insertos de "
        "içamento pendurados; fixar os 8 insertos de nivelamento pelos furos do fundo.",
        "Concretar, sarrafear pelas abas superiores dos trilhos e dar acabamento áspero no topo. "
        "Retirar as fôrmas de nicho no início da pega.",
    ],
}

CSS = """
@page { size: A4 landscape; margin: 0 }
:root{ --ink:#1C2A33; --muted:#5A6A74; --rule:#C7D2D9; --accent:#1F5C99; --paper:#F3F6F8;
  --pm:#D5E4F2; --pm2:#B9D2EA; --cip:#ECD9B2; --soil:#E3DCCF; --water:#C9E0EC;
  --steel:#8FA1AE; --steel2:#C3CED6; --conc:#E4E3DD; --warn:#874200; --warn-bg:#FCEFDF;
  --sheet:#FFFFFF; --good:#2E6B3F; }
*{ box-sizing:border-box }
body{ margin:0; color:var(--ink); background:#fff;
  font: 9pt/1.38 "Liberation Sans","DejaVu Sans",Arial,sans-serif }
.folha{ width:297mm; height:210mm; padding:8mm 10mm 7mm; display:grid;
  grid-template-rows:auto minmax(0,1fr) auto; gap:4mm; page-break-after:always;
  overflow:hidden }
.cab{ display:flex; justify-content:space-between; align-items:baseline; gap:6mm;
  border-bottom:0.45mm solid var(--ink); padding-bottom:2mm }
.cab h1{ font-size:15pt; margin:0; letter-spacing:.01em }
.cab .sub{ color:var(--muted); font-size:8.5pt }
.cod{ font: 700 15pt "DejaVu Sans Mono","Liberation Mono",monospace; color:var(--accent) }
.carimbo{ display:grid; grid-template-columns: 2.1fr 1.5fr 1.25fr 0.75fr;
  border:0.35mm solid var(--ink); font-size:7.2pt; line-height:1.3 }
.carimbo > div{ padding:1.4mm 2.4mm; border-right:0.25mm solid var(--rule) }
.carimbo > div:last-child{ border-right:0 }
.carimbo b{ display:block; font-size:6.2pt; letter-spacing:.12em; text-transform:uppercase;
  color:var(--muted); font-weight:700 }
.carimbo .alerta{ color:var(--warn); font-weight:700 }
.grade{ display:grid; grid-template-columns: minmax(0,1.6fr) minmax(0,1fr); gap:5mm;
  min-height:0 }
.desenho{ border:0.25mm solid var(--rule); padding:3mm; display:flex; align-items:center;
  justify-content:center; min-height:0; overflow:hidden }
.desenho svg{ width:100%; height:100%; max-height:150mm }
.pilha .desenho svg{ max-height:100% }
.info{ display:flex; flex-direction:column; gap:2.6mm; min-height:0; overflow:hidden }
.info h2{ font-size:11.5pt; margin:0 }
.info h3{ font-size:7pt; letter-spacing:.12em; text-transform:uppercase; color:var(--muted);
  margin:0 0 .8mm }
table{ border-collapse:collapse; width:100% }
th,td{ text-align:left; padding:.7mm 1.6mm; border-bottom:0.2mm solid var(--rule);
  vertical-align:top }
th{ font-size:6.6pt; letter-spacing:.08em; text-transform:uppercase; color:var(--muted);
  background:var(--paper) }
td.n, .mono{ font-family:"DejaVu Sans Mono","Liberation Mono",monospace; font-size:7.6pt;
  white-space:nowrap }
.kv{ display:grid; grid-template-columns:auto 1fr; gap:.6mm 3mm; font-size:8.4pt }
.kv span:nth-child(odd){ color:var(--muted) }
.furos{ columns:3; column-gap:4mm; font-size:7.2pt }
.furos div{ break-inside:avoid; font-family:"DejaVu Sans Mono",monospace;
  border-bottom:0.15mm solid var(--rule); padding:.25mm 0 }
.obs{ font-size:8pt; background:var(--paper); padding:1.6mm 2.4mm; border-left:0.8mm solid var(--accent) }
.aviso{ background:var(--warn-bg); border:0.3mm solid var(--warn); color:var(--ink);
  padding:2.5mm 3.5mm; font-size:8.6pt }
.aviso b{ color:var(--warn) }
.capa{ display:grid; grid-template-columns: minmax(0,1.15fr) minmax(0,1fr); gap:8mm; min-height:0 }
.capa h1{ font-size:26pt; margin:0 0 2mm; line-height:1.05 }
.capa .lead{ font-size:10.5pt; color:var(--ink) }
.capa ol, .passos{ margin:0; padding-left:5mm; display:grid; gap:1.4mm; font-size:8.8pt }
.monta{ display:grid; grid-template-columns: minmax(0,1.7fr) minmax(0,1fr); gap:5mm; min-height:0 }
.monta .desenhos{ display:grid; gap:3mm; min-height:0; grid-auto-rows:minmax(0,1fr) }
.monta .desenhos > div{ border:0.25mm solid var(--rule); padding:2mm; display:flex;
  align-items:center; justify-content:center; min-height:0; overflow:hidden }
.monta svg{ width:100%; height:100%; max-height:100%; min-width:0 !important }
.legenda{ font-size:7.6pt; color:var(--muted) }
.tab{ font-size:7.6pt }
.tab td{ padding:.55mm 1.4mm }

/* classes dos desenhos */
svg *{ vector-effect:non-scaling-stroke }
.dwg .pm{fill:var(--pm);stroke:var(--ink);stroke-width:.8}
.dwg .pm2{fill:var(--pm2);stroke:var(--ink);stroke-width:.8}
.dwg .cip{fill:var(--cip);stroke:var(--ink);stroke-width:.8}
.dwg .steel{fill:var(--steel);stroke:var(--ink);stroke-width:.8}
.dwg .steel2{fill:var(--steel2);stroke:var(--ink);stroke-width:.6}
.dwg .conc{fill:var(--conc);stroke:var(--muted);stroke-width:.6;stroke-dasharray:2 2}
.dwg .void{fill:#fff;stroke:var(--ink);stroke-width:.7}
.dwg .hat{fill:none;stroke:var(--ink);stroke-width:2.2}
.dwg .bolt{stroke:var(--warn);stroke-width:1.8}
.dwg .nut{fill:var(--warn)}
.dwg .rod{stroke:var(--warn);stroke-width:1.6}
.dwg .dim,.dwg .tick{stroke:var(--muted);stroke-width:.7;fill:none}
.dwg .lead{stroke:var(--accent);stroke-width:.8}
.dwg .co circle{fill:#fff;stroke:var(--accent);stroke-width:1.1}
.dwg .co text{fill:var(--accent);font-family:"DejaVu Sans Mono",monospace;font-weight:700;
  text-anchor:middle;dominant-baseline:central}
.dwg text.dimt{fill:var(--ink);font-family:"DejaVu Sans Mono",monospace}
.dwg text.note{fill:var(--ink);font-family:"Liberation Sans",sans-serif;font-weight:700}
.dwg text.tag{fill:var(--muted);font-family:"Liberation Sans",sans-serif;font-weight:700}
.dwg .hidden,.dwg .hiddenr{fill:none;stroke:var(--ink);stroke-width:.6;stroke-dasharray:4 3}
.dwg .jointb{stroke:var(--accent);stroke-width:1.4}
.dwg .zone{fill:var(--steel2);opacity:.55;stroke:none}
.dwg .beamline{fill:none;stroke:var(--accent);stroke-width:.8;stroke-dasharray:6 4}
.dwg .modj{stroke:var(--warn);stroke-width:1;stroke-dasharray:8 4}
.dwg .key{stroke:var(--accent);stroke-width:2.6}
.dwg .ins{fill:#fff;stroke:var(--warn);stroke-width:1.4}
.dwg .lev{fill:var(--ink)}
.dwg .esp{fill:var(--good)}
.dwg .grout{fill:var(--cip);stroke:var(--ink);stroke-width:.7}
.dwg .rod2{fill:var(--muted)}
.dwg .memb{fill:var(--ink)}
.dwg .asph{fill:#9AA3A8;stroke:none}
.pilha{ display:grid; grid-template-rows: minmax(0,1.35fr) minmax(0,1fr); gap:3mm; min-height:0 }
.perfilbox{ position:relative; padding-top:6mm }
.perfilbox .rot{ position:absolute; top:1.6mm; left:2.4mm; font-size:6.6pt; letter-spacing:.08em;
  text-transform:uppercase; color:var(--muted); font-weight:700 }
.tfuros td, .tfuros th{ padding:.35mm 1.1mm; font-size:6.8pt }
.cot .prof{fill:none;stroke:var(--ink);stroke-width:3.2;stroke-linejoin:miter}
.cot .vx{fill:var(--accent)}
.cot .cut{fill:var(--steel2);stroke:var(--ink);stroke-width:1.1}
.cot .hole{fill:#fff;stroke:var(--warn);stroke-width:1}
.cot .bend{stroke:var(--accent);stroke-width:1.1;stroke-dasharray:9 5}
.cot .mark{stroke:var(--good);stroke-width:1;stroke-dasharray:3 3}
.cot .dim,.cot .tick{stroke:var(--muted);stroke-width:.7;fill:none}
.cot text{fill:var(--ink);font-family:"DejaVu Sans Mono",monospace}
.cot text.lb{fill:var(--accent);font-weight:700}
.cot text.hn{fill:var(--warn)}
.cot text.ed{fill:var(--muted);font-family:"Liberation Sans",sans-serif;font-weight:700}
"""


def esc(s):
    return html.escape(str(s))


def f1(v):
    return gf.fmt(v)


# --------------------------------------------------------------------------
# planificação cotada
# --------------------------------------------------------------------------
def svg_cotado(p):
    L, W = p.comprimento, p.largura
    s = max(L, W)
    fs = s / 36
    mL, mR, mT, mB = 7.2 * fs, 5.2 * fs, 2.6 * fs, 5.0 * fs
    vbw, vbh = L + mL + mR, W + mT + mB

    def X(x):
        return mL + x

    def Y(y):
        return mT + (W - y)

    o = [f'<svg class="cot" viewBox="0 0 {vbw:.1f} {vbh:.1f}" role="img" '
         f'aria-label="Planificação cotada {p.codigo}">']
    pts = " ".join(f"{X(x):.1f},{Y(y):.1f}" for x, y in gf.contorno_de(p))
    o.append(f'<polygon class="cut" points="{pts}"/>')

    def linha(x1, y1, x2, y2, cls):
        o.append(f'<line class="{cls}" x1="{X(x1):.1f}" y1="{Y(y1):.1f}" x2="{X(x2):.1f}" '
                 f'y2="{Y(y2):.1f}"/>')

    def texto(x, y, t, cls="", k=1.0, anchor="middle", rot=None):
        tr = f' transform="rotate({rot} {X(x):.1f} {Y(y):.1f})"' if rot is not None else ""
        c = f' class="{cls}"' if cls else ""
        o.append(f'<text{c} x="{X(x):.1f}" y="{Y(y):.1f}" font-size="{fs * k:.1f}" '
                 f'text-anchor="{anchor}"{tr}>{esc(t)}</text>')

    def tick(x, y):
        t = fs * 0.3
        linha(x - t, y - t, x + t, y + t, "tick")

    # dobras (etiquetas espaçadas para não encavalar) e marcas
    alvo = espalha(list(p.linhas), 1.15 * fs)
    for i, (yl, ang, ye) in enumerate(zip(p.linhas, p.angulos, alvo), 1):
        linha(0, yl, L, yl, "bend")
        linha(L, yl, L + 0.3 * fs, ye, "tick")
        texto(L + 0.4 * fs, ye - 0.32 * fs, f"D{i} {f1(ang)}°", "lb", 0.82, "start")
    for ym, _ in p.marcas:
        linha(0, ym, L, ym, "mark")

    # furos e rasgos numerados
    k = 0
    for x, y, d in p.furos:
        k += 1
        o.append(f'<circle class="hole" cx="{X(x):.1f}" cy="{Y(y):.1f}" r="{d / 2:.1f}"/>')
        texto(x + d / 2 + 0.12 * fs, y + d / 2 + 0.12 * fs, str(k), "hn", 0.62, "start")
    for x, y1, y2, wdt in p.rasgos:
        k += 1
        ya, yb = sorted((y1, y2))
        o.append(f'<rect class="hole" x="{X(x - wdt / 2):.1f}" y="{Y(yb + wdt / 2):.1f}" '
                 f'width="{wdt:.1f}" height="{yb - ya + wdt:.1f}" rx="{wdt / 2:.1f}"/>')
        texto(x + wdt / 2 + 0.12 * fs, yb + 0.1 * fs, str(k), "hn", 0.62, "start")

    # cota do comprimento (embaixo)
    yb_ = -2.6 * fs
    linha(0, yb_, L, yb_, "dim")
    tick(0, yb_)
    tick(L, yb_)
    texto(L / 2, yb_ + 0.35 * fs, f"{f1(L)}", "", 0.95)
    # cotas de bordas reais em peças com contorno próprio
    if p.contorno:
        base = sorted(x for x, y in p.contorno if y == 0)
        topo = sorted(x for x, y in p.contorno if y == W)
        yb2 = -1.2 * fs
        linha(base[0], yb2, base[-1], yb2, "dim")
        tick(base[0], yb2)
        tick(base[-1], yb2)
        texto((base[0] + base[-1]) / 2, yb2 + 0.3 * fs, f"base {f1(base[-1] - base[0])}", "", 0.8)
        texto((topo[0] + topo[-1]) / 2, W + 0.6 * fs, f"topo {f1(topo[-1] - topo[0])}", "", 0.8)
    # cota total da largura (esquerda) e corrente das dobras
    xt = -5.6 * fs
    linha(xt, 0, xt, W, "dim")
    tick(xt, 0)
    tick(xt, W)
    texto(xt - 0.35 * fs, W / 2, f"{f1(W)}", "", 0.95, rot=-90)
    if p.linhas:
        xc = -2.7 * fs
        marcos = [0.0] + list(p.linhas) + [W]
        linha(xc, 0, xc, W, "dim")
        for a, b in zip(marcos, marcos[1:]):
            tick(xc, a)
            if b - a >= 2.6 * fs:
                texto(xc - 0.3 * fs, (a + b) / 2, f1(b - a), "", 0.78, rot=-90)
        tick(xc, W)
    texto(0, -0.95 * fs, "borda A", "ed", 0.7, "start")
    if not p.contorno:
        texto(0, W + 0.45 * fs, "borda B", "ed", 0.7, "start")
    o.append("</svg>")
    return "".join(o)


def espalha(pos, gap):
    """Distribui etiquetas em 1D mantendo a ordem e uma distância mínima entre elas."""
    if not pos:
        return []
    ordem = sorted(range(len(pos)), key=lambda i: pos[i])
    v = [pos[i] for i in ordem]
    for _ in range(50):
        mexeu = False
        for i in range(1, len(v)):
            falta = gap - (v[i] - v[i - 1])
            if falta > 1e-6:
                v[i - 1] -= falta / 2
                v[i] += falta / 2
                mexeu = True
        if not mexeu:
            break
    out = [0.0] * len(pos)
    for k, i in enumerate(ordem):
        out[i] = v[k]
    return out


def svg_perfil(p):
    """Perfil dobrado (seção da peça pronta), com as medidas externas e os ângulos.
    Medidas ficam do lado de fora de cada aba; ângulos, do lado convexo de cada dobra."""
    import math
    pts, rumo = [(0.0, 0.0)], 0.0
    for i, a in enumerate(p.abas):
        x, y = pts[-1]
        pts.append((x + a * math.cos(math.radians(rumo)), y + a * math.sin(math.radians(rumo))))
        if i < len(p.angulos):
            rumo += p.giros[i] * p.angulos[i]
    xs, ys = [x for x, _ in pts], [y for _, y in pts]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    s = max(w, h, 1)
    fs = s / 13
    m = 3.6 * fs
    x0, y0 = min(xs) - m, max(ys) + m
    vbw, vbh = w + 2 * m, h + 2 * m
    cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)

    def P(x, y):
        return f"{x - x0:.1f},{y0 - y:.1f}"

    def rotulo(x, y, dx, dy, txt, cls, k):
        ancora = "start" if dx > 0.35 else ("end" if dx < -0.35 else "middle")
        yy = y0 - y + (0.35 * fs * k if abs(dy) < 0.35 else (0.9 * fs * k if dy < 0 else 0))
        c = f' class="{cls}"' if cls else ""
        return (f'<text{c} x="{x - x0:.1f}" y="{yy:.1f}" font-size="{fs * k:.1f}" '
                f'text-anchor="{ancora}">{esc(txt)}</text>')

    o = [f'<svg class="cot perfil" viewBox="0 0 {vbw:.1f} {vbh:.1f}" role="img" '
         f'aria-label="Perfil dobrado {p.codigo}">']
    o.append(f'<polyline class="prof" points="{" ".join(P(x, y) for x, y in pts)}"/>')
    for i, a in enumerate(p.abas):
        (xa, ya), (xb, yb) = pts[i], pts[i + 1]
        mx, my = (xa + xb) / 2, (ya + yb) / 2
        dx, dy = xb - xa, yb - ya
        comp = math.hypot(dx, dy) or 1
        nx, ny = -dy / comp, dx / comp
        if (mx + nx - cx) ** 2 + (my + ny - cy) ** 2 < (mx - nx - cx) ** 2 + (my - ny - cy) ** 2:
            nx, ny = -nx, -ny
        nome = p.nomes_abas[i] if i < len(p.nomes_abas) else ""
        marca = " FC" if "concreto" in nome else ""
        o.append(rotulo(mx + nx * 0.55 * fs, my + ny * 0.55 * fs, nx, ny, f"{f1(a)}{marca}", "", 1.0))
    for i, ang in enumerate(p.angulos):
        (xa, ya), (xv, yv), (xb, yb) = pts[i], pts[i + 1], pts[i + 2]
        ua = ((xv - xa), (yv - ya))
        ub = ((xb - xv), (yb - yv))
        la, lb = math.hypot(*ua) or 1, math.hypot(*ub) or 1
        bx, by = ua[0] / la - ub[0] / lb, ua[1] / la - ub[1] / lb   # lado convexo
        lbis = math.hypot(bx, by) or 1
        bx, by = bx / lbis, by / lbis
        o.append(f'<circle class="vx" cx="{xv - x0:.1f}" cy="{y0 - yv:.1f}" r="{fs * 0.16:.1f}"/>')
        o.append(rotulo(xv + bx * 0.5 * fs, yv + by * 0.5 * fs, bx, by, f"D{i + 1} {f1(ang)}°",
                        "lb", 0.78))
    o.append("</svg>")
    return "".join(o)


# --------------------------------------------------------------------------
# folhas
# --------------------------------------------------------------------------
class Caderno:
    def __init__(self):
        self.folhas = []

    def add(self, titulo, corpo, cod=""):
        self.folhas.append((titulo, corpo, cod))

    def render(self):
        total = len(self.folhas)
        out = []
        for i, (titulo, corpo, cod) in enumerate(self.folhas, 1):
            out.append(f"""<section class="folha">
<div class="cab"><div><h1>{esc(titulo)}</h1><div class="sub">{esc(PROJETO)}</div></div>
<div class="cod">{esc(cod)}</div></div>
{corpo}
<div class="carimbo">
<div><b>Projeto</b>{esc(PROJETO)}<br>Planificações em mm · origem no canto da borda A</div>
<div><b>Situação</b><span class="alerta">Anteprojeto. Não cortar sem ART do engenheiro e sem a
tabela de dobra do fornecedor.</span></div>
<div><b>Dados de dobra (provisórios)</b>3,00: ri 3,5 · 4,75: ri 6 · 6,30: ri 8 · K 0,42</div>
<div><b>Data · Folha</b>{DATA}<br>{i} / {total}</div>
</div></section>""")
        return ("<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'>"
                f"<title>Caderno de fabricação · formas da ponte de 10 m</title><style>{CSS}"
                "</style></head><body>" + "".join(out) + "</body></html>")


def folha_capa(cad, pecas):
    linhas = []
    for forma, cod, nome, jogo in FORMAS:
        ps = [p for p in pecas if p.forma == forma]
        kg = sum(p.peso * p.qtd for p in ps)
        linhas.append(f"<tr><td class='n'>{cod}</td><td>{esc(nome)}</td><td>{esc(jogo)}</td>"
                      f"<td class='n'>{len(ps)}</td><td class='n'>{sum(p.qtd for p in ps)}</td>"
                      f"<td class='n'>{kg:,.0f} kg</td></tr>".replace(",", "."))
    total = sum(p.peso * p.qtd for p in pecas)
    corpo = f"""<div class="capa">
<div style="display:grid;gap:4mm;align-content:start">
<div><h1>Caderno de fabricação</h1><p class="lead">Formas metálicas de chapa cortada no plasma e
dobrada, para as peças pré-moldadas da ponte de dois vãos de 10 m e 4,50 m de largura. Cada peça
tem uma folha com a planificação cotada, a sequência de dobras e as coordenadas dos furos.</p></div>
<table class="tab"><thead><tr><th>Forma</th><th>Faz</th><th>Jogo</th><th>Tipos</th><th>Peças</th>
<th>Aço</th></tr></thead><tbody>{''.join(linhas)}
<tr><td></td><td><b>Total</b></td><td></td><td></td><td></td><td class='n'><b>{total:,.0f} kg</b>
</td></tr></tbody></table>
<div class="aviso"><b>Antes de cortar:</b> (1) engenheiro com ART aprova as peças de concreto;
(2) o fornecedor informa a tabela de dobra (raio interno e fator K) e a força da dobradeira; (3) os
arquivos são gerados de novo com esses dados; (4) corta-se e monta-se um módulo de teste.</div>
</div>
<div style="display:grid;gap:3mm;align-content:start">
<h2 style="margin:0;font-size:12pt">Como ler os arquivos</h2>
<ol>
<li><b>_CORTE.dxf</b> vai para o plasma: só contorno e furos, em mm, DXF R2000.</li>
<li><b>_DESENHO.dxf</b> é para conferência: tem linhas de dobra (camada DOBRA), marcas de solda
(MARCA) e textos (TEXTO). Não mandar para corte.</li>
<li>Nas folhas, a origem (0; 0) é o canto esquerdo da <b>borda A</b>. As dobras estão medidas das
duas bordas; o encosto sugerido é a borda mais próxima.</li>
<li>Furos numerados no desenho, com x, y e diâmetro na tabela da folha. Ø18 = parafuso M16;
Ø14 = M12.</li>
<li>Forças de dobra estimadas pela fórmula usual de dobra no ar. As maiores: fundo da longarina
(6,30 × 2500 mm) ≈ 131 tf; trilho da placa (6,30 × 2013) ≈ 106 tf. Se a máquina tiver menos,
avisar para trocar a chapa.</li>
<li>Tolerâncias recomendadas: face de concreto ±2 mm de planeza em 2,5 m; altura das faces ±1 mm;
furos ±1 mm. Nenhuma solda ou respingo na face de concreto.</li>
</ol></div></div>"""
    cad.add("Caderno de fabricação", corpo)


def folha_montagem(cad, cod, titulo, svgs, legendas, passos):
    blocos = "".join(f"<div>{s}</div>" for s in svgs)
    leg = "".join(f"<p class='legenda'>{esc(t)}</p>" for t in legendas)
    corpo = f"""<div class="monta"><div class="desenhos">{blocos}</div>
<div style="display:grid;gap:3mm;align-content:start"><h2 style="margin:0;font-size:12pt">Montagem
</h2><ol class="passos">{''.join(f'<li>{esc(t)}</li>' for t in passos)}</ol>{leg}</div></div>"""
    cad.add(titulo, corpo, cod)


def folha_peca(cad, p):
    dobras = ""
    if p.linhas:
        linhas = "".join(
            f"<tr><td class='n'>D{r['n']}</td><td class='n'>{f1(r['ang'])}°</td>"
            f"<td class='n'>{f1(r['da'])}</td><td class='n'>{f1(r['db'])}</td>"
            f"<td class='n'>{r['borda']}</td><td class='n'>{f1(r['aba']) if r['aba'] != '' else '-'}"
            f"</td></tr>" for r in gf.roteiro_de_dobra(p))
        dobras = (f"<div><h3>Dobras</h3><table><thead><tr><th>Dobra</th><th>Ângulo</th>"
                  f"<th>Da borda A</th><th>Da borda B</th><th>Encosto</th><th>Aba</th></tr></thead>"
                  f"<tbody>{linhas}</tbody></table><div class='legenda'>{esc(p.sentido)}"
                  f"</div></div>")
    furos = ""
    itens = []
    for x, y, d in p.furos:
        itens.append((f1(x), f1(y), f"Ø{f1(d)}"))
    for x, y1, y2, wdt in p.rasgos:
        itens.append((f1(x), f"{f1(min(y1, y2))}–{f1(max(y1, y2))}", f"rasgo {f1(wdt)}"))
    if itens:
        grupos = 3 if len(itens) > 16 else (2 if len(itens) > 6 else 1)
        por = -(-len(itens) // grupos)
        cab = "".join("<th>Nº</th><th>x</th><th>y</th><th>Ø</th>" for _ in range(grupos))
        corpo_f = ""
        for r in range(por):
            celulas = ""
            for g in range(grupos):
                k = g * por + r
                if k < len(itens):
                    x_, y_, d_ = itens[k]
                    celulas += (f"<td class='n'>{k + 1}</td><td class='n'>{x_}</td>"
                                f"<td class='n'>{y_}</td><td class='n'>{d_}</td>")
                else:
                    celulas += "<td></td><td></td><td></td><td></td>"
            corpo_f += f"<tr>{celulas}</tr>"
        furos = (f"<div><h3>Furos ({len(itens)}) · coordenadas em mm a partir do canto da borda A"
                 f"</h3><table class='tfuros'><thead><tr>{cab}</tr></thead><tbody>{corpo_f}"
                 f"</tbody></table></div>")
    abas = " / ".join(f"{f1(a)} ({n})" for a, n in zip(p.abas, p.nomes_abas)) if p.nomes_abas \
        else " / ".join(f1(a) for a in p.abas)
    marcas = ""
    if p.marcas:
        marcas = "<div class='legenda'>Marcas (verde tracejado): " + "; ".join(
            f"y = {f1(y)} mm, {esc(t.lower())}" for y, t in p.marcas) + "</div>"
    if p.linhas:
        esquerda = (f"<div class='pilha'><div class='desenho'>{svg_cotado(p)}</div>"
                    f"<div class='desenho perfilbox'><div class='rot'>Perfil dobrado · medidas "
                    f"externas · FC = face de concreto</div>{svg_perfil(p)}</div></div>")
    else:
        esquerda = f"<div class='desenho'>{svg_cotado(p)}</div>"
    corpo = f"""<div class="grade">{esquerda}
<div class="info"><h2>{esc(p.nome)}</h2>
<div class="kv"><span>Forma</span><span>{esc(p.forma)}</span>
<span>Chapa</span><span class="mono">{gf.fmt_t(p.t)} mm</span>
<span>Quantidade</span><span class="mono">{p.qtd}</span>
<span>Planificada</span><span class="mono">{f1(p.comprimento)} × {f1(p.largura)} mm</span>
<span>Abas externas</span><span>{esc(abas)}</span>
<span>Peso</span><span class="mono">{f1(p.peso)} kg/peça · {f1(p.peso * p.qtd)} kg no total</span>
<span>Arquivo de corte</span><span class="mono">{p.codigo}_CORTE.dxf</span></div>
{dobras}{furos}{marcas}<div class="obs">{esc(p.obs)}</div></div></div>"""
    cad.add(p.nome if len(p.nome) < 48 else p.nome[:46] + "…", corpo, p.codigo)


def folhas_tabela(cad, titulo, cabecalho, linhas, por_folha=27):
    for i in range(0, len(linhas), por_folha):
        corpo_l = "".join("<tr>" + "".join(f"<td class='{c}'>{esc(v)}</td>" for v, c in linha)
                          + "</tr>" for linha in linhas[i:i + por_folha])
        th = "".join(f"<th>{esc(h)}</th>" for h in cabecalho)
        sufixo = f" ({i // por_folha + 1})" if len(linhas) > por_folha else ""
        cad.add(titulo + sufixo, f"<div style='min-height:0;overflow:hidden'><table class='tab'>"
                                 f"<thead><tr>{th}</tr></thead><tbody>{corpo_l}</tbody></table></div>")


def main():
    pecas = gf.todas_as_pecas()
    os.makedirs(PASTA, exist_ok=True)
    cad = Caderno()
    folha_capa(cad, pecas)
    P = gf.PAINEL
    montagens = {
        "F-LON": ("Forma da longarina · montagem", [dz.secao_forma_longarina(), dz.modulos_longarina()],
                  ["1 nervura F-LON-02 · 2 painel F-LON-01 · 3 fundo F-LON-05 · 4 orelha F-LON-04 e "
                   "tirante · 5 parafuso M16 no rasgo · 6 concreto da viga 300 × 900"]),
        "F-PLA": ("Forma da placa de saia · montagem", [dz.secao_forma_placa()],
                  ["1 trilho F-PLA-03/04 · 2 fundo F-PLA-01 · 3 concreto da placa · 4 tubo-forma "
                   "do dreno"]),
        "F-LAJ": ("Forma do painel de laje · montagem", [dz.planta_painel(P), dz.secao_forma_painel(P)],
                  ["Planta: 1 nicho · 2 inserto de içamento · 3 inserto de nivelamento · 4 chave "
                   "fêmea · 5 zona do guarda-rodas · 6 eixo da longarina · 7 junta dos módulos do "
                   "fundo · 8 espera do guarda-rodas",
                   "Corte: 1 fundo F-LAJ-01 · 2 cantoneira F-LAJ-02 · 3 trilho F-LAJ-05 · 4 régua "
                   "de chave F-LAJ-06 · 5 fôrma de nicho F-LAJ-08/09 · 6 travessa F-LAJ-10 e barra "
                   "M12 · 7 concreto · 8 porca soldada sob o fundo"]),
    }
    for forma, cod, nome, _ in FORMAS:
        titulo, svgs, leg = montagens[cod]
        folha_montagem(cad, cod, titulo, svgs, leg, PASSOS[cod])
        if cod == "F-LAJ":
            folha_montagem(cad, cod, "Junta entre painéis", [dz.detalhe_junta(P)],
                           ["1 graute sem retração · 2 tarugo de espuma no fundo da junta · "
                            "3 manta impermeabilizante · 4 revestimento asfáltico de 5 cm · "
                            "5 rebaixo de 25 mm formado pela régua F-LAJ-06"],
                           ["A junta tem 20 mm de abertura e rebaixo de 25 mm em cada painel, "
                            "formando um losango que trava os painéis entre si.",
                            "Fechar o fundo com tarugo de espuma, encher com graute sem retração "
                            "e vedar as pontas da junta na borda da ponte.",
                            "Sobre o tabuleiro: manta impermeabilizante e revestimento. A junta é "
                            "o ponto crítico de durabilidade."])
        for p in pecas:
            if p.forma == forma:
                folha_peca(cad, p)

    linhas = [[(p.codigo, "n"), (p.nome, ""), (gf.fmt_t(p.t), "n"), (p.qtd, "n"),
               (f"{f1(p.comprimento)} × {f1(p.largura)}", "n"),
               (" / ".join(f1(a) for a in p.abas), "n"), (len(p.furos) + len(p.rasgos), "n"),
               (f1(p.peso * p.qtd), "n")] for p in pecas]
    folhas_tabela(cad, "Lista de corte", ["Código", "Peça", "Chapa", "Qtd.", "Planificada (mm)",
                                          "Abas externas (mm)", "Furos", "Aço total (kg)"], linhas)
    linhas = []
    for p in pecas:
        for r in gf.roteiro_de_dobra(p):
            linhas.append([(p.codigo, "n"), (f"D{r['n']}", "n"), (f"{f1(r['ang'])}°", "n"),
                           (f1(r["da"]), "n"), (f1(r["db"]), "n"), (r["borda"], "n"),
                           (f1(p.comprimento), "n"), (gf.fmt_t(p.t), "n"),
                           (f1(gf.forca_dobra_tf(p.t, p.comprimento)), "n")])
    folhas_tabela(cad, "Tabela de dobras", ["Código", "Dobra", "Ângulo", "Da borda A (mm)",
                                            "Da borda B (mm)", "Encosto", "Comprimento (mm)",
                                            "Chapa", "Força (tf)"], linhas, por_folha=28)
    folhas_tabela(cad, "Lista de compras", ["Item", "Quantidade", "Unidade"],
                  [[(a, ""), (b, "n"), (c, "")] for a, b, c in gf.lista_de_compras()])

    with open(HTML_OUT, "w", encoding="utf-8") as f:
        f.write(cad.render())
    print("HTML:", HTML_OUT, f"({len(cad.folhas)} folhas)")

    js = os.path.join(os.path.dirname(os.path.abspath(__file__)), "imprimir_pdf.js")
    if shutil.which("node"):
        r = subprocess.run(["node", js, HTML_OUT, PDF_OUT], capture_output=True, text=True)
        if r.returncode == 0:
            print("PDF:", PDF_OUT)
        else:
            print("Não consegui imprimir o PDF:", r.stderr.strip()[:400])
    else:
        print("Node não encontrado: abra o HTML no navegador e imprima em A4 deitado.")


if __name__ == "__main__":
    main()
