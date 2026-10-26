#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Folhas de desenho (ABNT NBR 16752:2020) para as pranchas da ponte pré-moldada de 10 m.

Formato da série A, margem esquerda de 20 mm e demais de 10 mm, linha de margem de 0,7 mm
(A2 a A4) ou 1,0 mm (A0 e A1), legenda de 180 mm no canto inferior direito, com quadro de
revisões acima dela. Linhas e escrita conforme ABNT NBR 16861:2020; escalas conforme
ABNT NBR 8196. Os blocos de cada folha são posicionados em milímetros, a partir do canto
superior esquerdo do quadro.
"""

import html
import os
import shutil
import subprocess

FORMATOS = {"A1": (841, 594), "A3": (420, 297), "A4": (210, 297)}
MARGEM = dict(esq=20, dir=10, sup=10, inf=10)

PROPRIETARIO = "PREFEITURA MUNICIPAL DE ELDORADO DO CARAJÁS – PA"
OBRA = "PONTE EM CONCRETO PRÉ-MOLDADO, VÃO ÚNICO DE 10,00 m, LARGURA DE 4,50 m"
LOCAL = "A DEFINIR"
SITUACAO = "ANTEPROJETO – NÃO LIBERADO PARA FABRICAÇÃO"
DATA = "26/10/2026"
REVISOES = [("0", DATA, "EMISSÃO INICIAL PARA ANÁLISE")]

LEG_W, LEG_H, REV_H = 180, 50, 13      # legenda e quadro de revisões (mm)

CSS = """
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:#fff;color:#000}
body{font-family:"Liberation Sans",Arial,Helvetica,sans-serif;font-size:2.5mm;line-height:1.28}
.folha{position:relative;overflow:hidden;page-break-after:always;break-after:page;background:#fff}
.quadro{position:absolute}
.borda{position:absolute;left:0;top:0;right:0;bottom:0;border:.7mm solid #000;pointer-events:none}
.A1 .borda{border-width:1mm}
.A1 th,.A1 td,.A1 .notas{font-size:3mm}
.A1 caption,.A1 .notas h3,.A1 .bloco-tit{font-size:3.5mm}
.A1 .vista .tit b{font-size:5mm}
.A1 .vista .tit span{font-size:3mm}
.bl{position:absolute;overflow:hidden}
.bl.solto{overflow:visible}
.vista{display:flex;flex-direction:column;align-items:center;gap:1.2mm}
.vista .tit{text-align:center;line-height:1.15}
.vista .tit b{display:block;font-size:3.5mm;letter-spacing:.02em;text-decoration:underline;
  text-underline-offset:.6mm;text-decoration-thickness:.25mm}
.vista .tit span{display:block;font-size:2.5mm;margin-top:.5mm}
.cab{font-size:3.5mm;font-weight:700;letter-spacing:.02em;border-bottom:.35mm solid #000;
  padding-bottom:.6mm;margin-bottom:1.2mm}
.cab small{font-size:2.5mm;font-weight:400;margin-left:2mm}
table{border-collapse:collapse;width:100%}
th,td{border:.25mm solid #000;padding:.45mm .9mm;vertical-align:top;font-size:2.5mm;
  line-height:1.2;text-align:left}
th{font-weight:700;text-align:center;vertical-align:middle}
td.n{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}
td.c{text-align:center;white-space:nowrap}
caption{caption-side:top;text-align:left;font-weight:700;font-size:3mm;padding:0 0 1mm;
  letter-spacing:.02em}
.notas{font-size:2.5mm}
.notas h3,.bloco-tit{font-size:3mm;font-weight:700;margin:0 0 1mm;letter-spacing:.02em}
.notas ol{margin:0;padding-left:4.6mm}
.notas li{margin:0 0 .7mm;text-align:justify}
.notas p{margin:0 0 .9mm;text-align:justify}
.pilha{display:flex;flex-direction:column;gap:3mm}
.linha{display:flex;gap:4mm;align-items:flex-start}
.tabs{display:flex;flex-wrap:wrap;gap:3mm 4mm;align-items:flex-start}
.tabs>div{flex:0 1 auto}
.tabs>div.dados{width:125mm;flex:0 0 125mm}
.tabs>div.dobras{max-width:142mm}
.nw{white-space:nowrap}
.tabs>div.notas-m{flex:1 1 55mm}
.tabs table{width:auto}
.tabs .dados table{width:100%}
.leg{position:absolute;border-top:.5mm solid #000;border-left:.5mm solid #000;
  display:grid;grid-template-columns:1fr 1fr 1fr 1fr;
  grid-template-rows:7mm 9.5mm 10.5mm 7mm 9mm minmax(0,1fr);font-size:2.2mm}
.leg>div{border-right:.25mm solid #000;border-bottom:.25mm solid #000;padding:.6mm 1.2mm;
  overflow:hidden}
.leg .r{font-size:1.8mm;letter-spacing:.04em;display:block;line-height:1.1;margin-bottom:.3mm}
.leg .v{font-size:2.5mm;font-weight:700;line-height:1.15;display:block}
.leg .grande{font-size:3.5mm}
.leg .num{font-size:6mm;font-weight:700;text-align:center;line-height:1}
.leg .sit{font-weight:700;font-size:2.8mm;text-align:center;display:flex;align-items:center;
  justify-content:center}
.rev{position:absolute;border-top:.5mm solid #000;border-left:.5mm solid #000;font-size:2.2mm}
.rev table td,.rev table th{font-size:2.2mm;padding:.25mm .8mm;border-width:.25mm}
.rev table{border-left:0;border-top:0}
.selo{position:absolute;font-weight:700;font-size:3.5mm;letter-spacing:.06em;
  border:.5mm solid #000;padding:1mm 2.5mm}

/* desenhos impressos: espessuras em mm de papel (NBR 16861) */
svg.dwg{display:block;overflow:visible}
svg.imp *{vector-effect:non-scaling-stroke}
svg.imp .hfundo{fill:#fff;stroke:none}
svg.imp .hl{fill:none;stroke:#6b6b6b;stroke-width:.13mm}
svg.imp .hd circle{fill:#5a5a5a;stroke:none}
svg.imp text{font-family:"Liberation Sans",Arial,sans-serif;fill:#000;stroke:none}
svg.imp text.note,svg.imp text.tag,svg.imp text.dimt,svg.imp text.nfuro{paint-order:stroke;
  stroke:#fff;stroke-width:.7mm;stroke-linejoin:round}
svg.imp text.tag{font-weight:700}
svg.imp .co circle{fill:#fff;stroke:#000;stroke-width:.25mm}
svg.imp .co text{font-weight:700;text-anchor:middle;dominant-baseline:central;paint-order:normal;
  stroke:none}
svg.imp .vis{fill:none;stroke:#000;stroke-width:.5mm;stroke-linejoin:round}
svg.imp .rupt{fill:none;stroke:#000;stroke-width:.25mm}
svg.imp .furo{fill:#fff;stroke:#000;stroke-width:.35mm}
svg.imp .cm{stroke:#000;stroke-width:.18mm}
svg.imp .dobra{stroke:#000;stroke-width:.25mm;stroke-dasharray:6mm 1mm .6mm 1mm}
svg.imp .grav{stroke:#000;stroke-width:.25mm;stroke-dasharray:4mm 1mm .6mm 1mm .6mm 1mm}
svg.imp .dim,svg.imp .dimo{fill:none;stroke:#000;stroke-width:.18mm}
svg.imp .tick{stroke:#000;stroke-width:.35mm}
svg.imp .arrow{fill:#000;stroke:none}
svg.imp .dot{fill:#000;stroke:none}
svg.imp .lead{stroke:#000;stroke-width:.18mm;fill:none}
svg.imp .pm{fill:#fff;stroke:#000;stroke-width:.5mm}
svg.imp .pm2{fill:#e6e6e6;stroke:#000;stroke-width:.5mm}
svg.imp .cip{stroke:#000;stroke-width:.35mm}
svg.imp .cipd{stroke:#000;stroke-width:.25mm;stroke-dasharray:2.5mm 1mm}
svg.imp .soil{stroke:none}
svg.imp .water{stroke:none}
svg.imp .rock{fill:#fff;stroke:#000;stroke-width:.25mm}
svg.imp .na{stroke:#000;stroke-width:.25mm;stroke-dasharray:6mm 1mm .6mm 1mm}
svg.imp .ghost{fill:none;stroke:#000;stroke-width:.25mm;stroke-dasharray:2.5mm 1mm}
svg.imp .ghostl{stroke:#000;stroke-width:.18mm;stroke-dasharray:2.5mm 1mm}
svg.imp .brg{fill:#000;stroke:none}
svg.imp .joint{stroke:#000;stroke-width:.25mm}
svg.imp .steel{fill:#000;stroke:#000;stroke-width:.13mm}
svg.imp .steel2{fill:#d0d0d0;stroke:#000;stroke-width:.25mm}
svg.imp .conc{stroke:#000;stroke-width:.25mm}
svg.imp .void{fill:#fff;stroke:#000;stroke-width:.35mm}
svg.imp .hat{fill:none;stroke:#000;stroke-width:.7mm;stroke-linejoin:round}
svg.imp .bolt{stroke:#000;stroke-width:.5mm}
svg.imp .nut{fill:#000;stroke:none}
svg.imp .rod{stroke:#000;stroke-width:.5mm}
svg.imp .hidden,svg.imp .hiddenr{fill:none;stroke:#000;stroke-width:.25mm;stroke-dasharray:2mm 1mm}
svg.imp .jointb{stroke:#000;stroke-width:.35mm}
svg.imp .zone{fill:#ececec;stroke:none}
svg.imp .beamline{fill:none;stroke:#000;stroke-width:.18mm;stroke-dasharray:6mm 1mm .6mm 1mm}
svg.imp .modj{stroke:#000;stroke-width:.35mm;stroke-dasharray:6mm 1mm .6mm 1mm .6mm 1mm}
svg.imp .key{stroke:#000;stroke-width:.7mm}
svg.imp .ins{fill:#fff;stroke:#000;stroke-width:.35mm}
svg.imp .lev{fill:#000;stroke:none}
svg.imp .esp{fill:#7a7a7a;stroke:#000;stroke-width:.18mm}
svg.imp .grout{stroke:#000;stroke-width:.25mm}
svg.imp .rod2{fill:#9a9a9a;stroke:#000;stroke-width:.18mm}
svg.imp .memb{fill:#000;stroke:none}
svg.imp .asph{fill:#c8c8c8;stroke:#000;stroke-width:.18mm}
svg.imp .chanf{fill:#a8a8a8;stroke:#000;stroke-width:.18mm}
"""


class Bruto(str):
    """Texto já em HTML, que a tabela não deve escapar."""


def esc(s):
    return s if isinstance(s, Bruto) else html.escape(str(s))


def bloco(x, y, w, h, conteudo, solto=False):
    cls = "bl solto" if solto else "bl"
    return (f'<div class="{cls}" style="left:{x}mm;top:{y}mm;width:{w}mm;height:{h}mm">'
            f'{conteudo}</div>')


def vista(svg, titulo, escala=None, sub=None):
    partes = []
    if sub:
        partes.append(esc(sub))
    if escala:
        partes.append(f"ESCALA {esc(escala)}")
    sp = f"<span>{' – '.join(partes)}</span>" if partes else ""
    return f'<div class="vista">{svg}<div class="tit"><b>{esc(titulo)}</b>{sp}</div></div>'


def tabela(cabecalho, linhas, titulo=None, larguras=None, classes=None, estilo=""):
    """linhas: listas de células; classes: classe de cada coluna ('n' numérica, 'c'
    centralizada, '' texto)."""
    col = ""
    if larguras:
        col = "<colgroup>" + "".join(f'<col style="width:{w}">' for w in larguras) + "</colgroup>"
    cab = ""
    if cabecalho:
        if isinstance(cabecalho[0], (list, tuple)):
            cab = "".join("<tr>" + "".join(_th(c) for c in linha) + "</tr>" for linha in cabecalho)
        else:
            cab = "<tr>" + "".join(_th(c) for c in cabecalho) + "</tr>"
    corpo = []
    for linha in linhas:
        cels = []
        for i, v in enumerate(linha):
            if isinstance(v, tuple):          # (valor, colspan, classe)
                val, span, cl = v
                cels.append(f'<td colspan="{span}" class="{cl}">{val}</td>')
                continue
            cl = classes[i] if classes and i < len(classes) else ""
            cels.append(f'<td class="{cl}">{esc(v)}</td>')
        corpo.append("<tr>" + "".join(cels) + "</tr>")
    cap = f"<caption>{esc(titulo)}</caption>" if titulo else ""
    return (f'<table style="{estilo}">{cap}{col}<thead>{cab}</thead><tbody>{"".join(corpo)}'
            f'</tbody></table>')


def _th(c):
    if isinstance(c, tuple):
        texto, colspan, rowspan = c
        return f'<th colspan="{colspan}" rowspan="{rowspan}">{esc(texto)}</th>'
    return f"<th>{esc(c)}</th>"


def notas(titulo, itens, numerar=True):
    if numerar:
        corpo = "<ol>" + "".join(f"<li>{esc(t)}</li>" for t in itens) + "</ol>"
    else:
        corpo = "".join(f"<p>{esc(t)}</p>" for t in itens)
    tit = f"<h3>{esc(titulo)}</h3>" if titulo else ""
    return f'<div class="notas">{tit}{corpo}</div>'


class Documento:
    """Conjunto de folhas de um mesmo formato, com legenda e quadro de revisões."""

    def __init__(self, formato, assunto, prefixo, titulo_html, unidade="mm, SALVO INDICAÇÃO"):
        self.formato, self.assunto, self.prefixo = formato, assunto, prefixo
        self.titulo_html, self.unidade = titulo_html, unidade
        self.folhas = []

    def folha(self, titulo, escalas, conteudo):
        self.folhas.append((titulo, escalas, conteudo))
        return len(self.folhas)

    def numero(self, i):
        return f"{self.prefixo}-{i:02d}"

    def area(self):
        W, H = FORMATOS[self.formato]
        return W - MARGEM["esq"] - MARGEM["dir"], H - MARGEM["sup"] - MARGEM["inf"]

    def _legenda(self, i, titulo, escalas):
        total = len(self.folhas)
        qw, qh = self.area()
        x, y = qw - LEG_W, qh - LEG_H
        c = (f'<div style="grid-column:span 3"><span class="r">PROPRIETÁRIO</span>'
             f'<span class="v">{esc(PROPRIETARIO)}</span></div>'
             f'<div style="grid-row:span 2"><span class="r">PRANCHA</span>'
             f'<div class="num">{esc(self.numero(i))}</div>'
             f'<span class="r" style="text-align:center;margin-top:.8mm">FOLHA {i:02d}/'
             f'{total:02d}</span></div>'
             f'<div style="grid-column:span 3"><span class="r">OBRA</span>'
             f'<span class="v">{esc(OBRA)}</span><span class="r" style="margin-top:.4mm">'
             f'LOCAL: {esc(LOCAL)}</span></div>'
             f'<div style="grid-column:span 4"><span class="r">{esc(self.assunto)}</span>'
             f'<span class="v grande">{esc(titulo)}</span></div>'
             f'<div><span class="r">ESCALA</span><span class="v">{esc(escalas)}</span></div>'
             f'<div><span class="r">UNIDADE</span><span class="v">{esc(self.unidade)}</span>'
             f'</div>'
             f'<div><span class="r">DATA</span><span class="v">{esc(DATA)}</span></div>'
             f'<div><span class="r">FORMATO</span><span class="v">{self.formato}</span></div>'
             f'<div style="grid-column:span 2"><span class="r">RESPONSÁVEL TÉCNICO</span>'
             f'<span class="v">&nbsp;</span></div>'
             f'<div><span class="r">CREA</span><span class="v">&nbsp;</span></div>'
             f'<div><span class="r">ART</span><span class="v">&nbsp;</span></div>'
             f'<div class="sit" style="grid-column:span 4">{esc(SITUACAO)}</div>')
        leg = (f'<div class="leg" style="left:{x}mm;top:{y}mm;width:{LEG_W}mm;height:{LEG_H}mm">'
               f'{c}</div>')
        linhas = "".join(f"<tr><td class='c'>{esc(r)}</td><td class='c'>{esc(d)}</td>"
                         f"<td>{esc(t)}</td></tr>" for r, d, t in REVISOES)
        vazias = max(0, 2 - len(REVISOES))
        linhas = "<tr><td>&nbsp;</td><td></td><td></td></tr>" * vazias + linhas
        rev = (f'<div class="rev" style="left:{x}mm;top:{y - REV_H}mm;width:{LEG_W}mm;'
               f'height:{REV_H}mm"><table><colgroup><col style="width:9%"><col style="width:17%">'
               f'<col></colgroup><tbody>{linhas}<tr><th>REV.</th><th>DATA</th>'
               f'<th>DESCRIÇÃO</th></tr></tbody></table></div>')
        return rev + leg

    def html(self):
        W, H = FORMATOS[self.formato]
        qw, qh = self.area()
        css = CSS + f"@page{{size:{W}mm {H}mm;margin:0}}"
        out = []
        for i, (titulo, escalas, conteudo) in enumerate(self.folhas, 1):
            out.append(f'<section class="folha {self.formato}" style="width:{W}mm;height:{H}mm">'
                       f'<div class="quadro" style="left:{MARGEM["esq"]}mm;top:{MARGEM["sup"]}mm;'
                       f'width:{qw}mm;height:{qh}mm">{conteudo}'
                       f'{self._legenda(i, titulo, escalas)}<div class="borda"></div></div>'
                       f'</section>')
        return (f"<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'>"
                f"<title>{esc(self.titulo_html)}</title><style>{css}</style></head><body>"
                + "".join(out) + "</body></html>")


def grava_e_imprime(doc, html_path, pdf_path, cabecalho=None):
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(doc if isinstance(doc, str) else doc.html())
    js = os.path.join(os.path.dirname(os.path.abspath(__file__)), "imprimir_pdf.js")
    if not shutil.which("node"):
        print("Node não encontrado: abrir o HTML no navegador e imprimir no formato da folha.")
        return False
    args = ["node", js, html_path, pdf_path] + ([cabecalho] if cabecalho else [])
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        print("Falha ao imprimir o PDF:", r.stderr.strip()[:500])
        return False
    return True
