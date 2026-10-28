#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vistas em perspectiva de cada marca das fôrmas das aduelas: a chapa como sai do corte (face
superior da mesa para cima, com furos, rasgos, linhas de dobra e linhas gravadas) e a peça
depois de dobrada, com a sequência de dobras.

Gera saida/<tamanho>/vistas_3d/<marca>.jpg.

Uso:  python3 gerar_vistas_3d.py      (rodar depois de gerar_formas.py; requer Node.js com
                                        Playwright e Pillow)
"""

import html
import math
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gerar_formas as gf                 # noqa: E402
import chapas as ch                       # noqa: E402
from desenho import geometria_dobrada     # noqa: E402

W, H = 1800, 1050
AZ, EL = math.radians(-32), math.radians(28)
LUZ = (-0.35, -0.55, 0.75)
SHOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "comum",
                    "imprimir_jpg.js")


def num(v, casas=1):
    s = f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s[:-2] if s.endswith(",0") else s


def projeta(p):
    """Ponto (x ao longo das dobras, u na largura, v na espessura) para a tela e a
    profundidade."""
    x, u, v = p
    x1 = x * math.cos(AZ) - u * math.sin(AZ)
    y1 = x * math.sin(AZ) + u * math.cos(AZ)
    z1 = v
    y2 = y1 * math.cos(EL) - z1 * math.sin(EL)
    z2 = y1 * math.sin(EL) + z1 * math.cos(EL)
    return (x1, -z2), y2


def normal(pts):
    (ax, ay, az), (bx, by, bz), (cx, cy, cz) = pts[0], pts[1], pts[2]
    u = (bx - ax, by - ay, bz - az)
    w = (cx - ax, cy - ay, cz - az)
    n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])
    m = math.sqrt(sum(c * c for c in n)) or 1
    return tuple(c / m for c in n)


def prisma(secao, L):
    """Faces do sólido extrudado: seção (u, v) ao longo de x de 0 a L."""
    faces = [[(0, u, v) for u, v in secao], [(L, u, v) for u, v in reversed(secao)]]
    n = len(secao)
    for i in range(n):
        (u1, v1), (u2, v2) = secao[i], secao[(i + 1) % n]
        faces.append([(0, u1, v1), (L, u1, v1), (L, u2, v2), (0, u2, v2)])
    return faces


def placa(contorno, t):
    """Faces de uma chapa plana com contorno (x, u) e espessura t."""
    faces = [[(x, u, 0) for x, u in reversed(contorno)], [(x, u, t) for x, u in contorno]]
    n = len(contorno)
    for i in range(n):
        (x1, u1), (x2, u2) = contorno[i], contorno[(i + 1) % n]
        faces.append([(x1, u1, 0), (x2, u2, 0), (x2, u2, t), (x1, u1, t)])
    return faces


class Cena:
    """Faces e detalhes em 3D, desenhados num retângulo da imagem com escala única."""

    def __init__(self):
        self.faces, self.linhas, self.manchas = [], [], []

    def caixa(self):
        pts = [projeta(p)[0] for f in self.faces for p in f]
        xs, ys = [x for x, _ in pts], [y for _, y in pts]
        return min(xs), max(xs), min(ys), max(ys)

    def svg(self, ox, oy, esc):
        x0, _, y0, _ = self.caixa()
        tela = lambda p: (ox + (projeta(p)[0][0] - x0) * esc, oy + (projeta(p)[0][1] - y0) * esc)
        out = []
        ordem = []
        for f in self.faces:
            n = normal(f)
            prof = sum(projeta(p)[1] for p in f) / len(f)
            luz = abs(sum(a * b for a, b in zip(n, LUZ)))
            ordem.append((prof, f, luz))
        ordem.sort(key=lambda o: -o[0])
        for _, f, luz in ordem:
            g = int(150 + 95 * luz)
            pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in map(tela, f))
            out.append(f'<polygon points="{pts}" fill="rgb({g},{g + 3},{g + 8})" '
                       f'stroke="#30343a" stroke-width="0.9" stroke-linejoin="round"/>')
        for pts, cor in self.manchas:
            q = " ".join(f"{x:.1f},{y:.1f}" for x, y in map(tela, pts))
            out.append(f'<polygon points="{q}" fill="{cor}" stroke="#222" stroke-width="0.6"/>')
        for a, b, cor, tr, larg in self.linhas:
            (x1, y1), (x2, y2) = tela(a), tela(b)
            d = f' stroke-dasharray="{tr}"' if tr else ""
            out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                       f'stroke="{cor}" stroke-width="{larg}"{d}/>')
        return "".join(out)


def cena_plana(p):
    c = Cena()
    L, Wd, t = p.comprimento, p.largura, p.t
    contorno = p.contorno or [(0, 0), (L, 0), (L, Wd), (0, Wd)]
    c.faces = placa(contorno, t)
    for x, y, d in p.furos:
        c.manchas.append(([(x + d / 2 * math.cos(a), y + d / 2 * math.sin(a), t + 0.1)
                           for a in [k * math.pi / 12 for k in range(24)]], "#20242a"))
    for x, y1, y2, w in p.rasgos:
        a, b = min(y1, y2), max(y1, y2)
        pts = [(x + w / 2 * math.cos(q), b + w / 2 * math.sin(q), t + 0.1)
               for q in [k * math.pi / 8 for k in range(9)]]
        pts += [(x + w / 2 * math.cos(q), a + w / 2 * math.sin(q), t + 0.1)
                for q in [math.pi + k * math.pi / 8 for k in range(9)]]
        c.manchas.append((pts, "#20242a"))
    for yl in p.linhas:
        c.linhas.append(((0, yl, t + 0.2), (L, yl, t + 0.2), "#c0392b", "10 6", 2.0))
    for x1, y1, x2, y2 in p.marcas:
        c.linhas.append(((x1, y1, t + 0.2), (x2, y2, t + 0.2), "#d35400", "4 4", 2.0))
    return c


def cena_dobrada(p):
    poly, _, _ = geometria_dobrada(p)
    c = Cena()
    c.faces = prisma(poly, p.comprimento)
    return c


def legenda_dobras(p):
    linhas = []
    for r, g in zip(ch.roteiro_de_dobra(p), p.giros):
        borda = "INFERIOR" if r["borda"] == "A" else "SUPERIOR"
        dist = r["da"] if r["borda"] == "A" else r["db"]
        linhas.append(f"DOBRA {r['n']}: {num(r['ang'])}° {'PARA CIMA' if g > 0 else 'PARA BAIXO'}"
                      f" – BORDA {borda} NO BATENTE, LINHA DE DOBRA A {num(dist)} mm DA BORDA")
    return linhas


def texto(x, y, s, tam=18, peso="400", cor="#1a1a1a", ancora="start"):
    return (f'<text x="{x}" y="{y}" font-size="{tam}" font-weight="{peso}" fill="{cor}" '
            f'text-anchor="{ancora}">{html.escape(s)}</text>')


def imagem(p, a):
    d = ch.DOBRA[p.t]
    s = [f'<rect width="{W}" height="{H}" fill="#fff"/>',
         f'<rect x="20" y="20" width="{W - 40}" height="{H - 40}" fill="none" '
         f'stroke="#000" stroke-width="2"/>',
         texto(50, 72, f"MARCA {p.codigo} – {p.nome.upper()}", 28, "700"),
         texto(50, 108, f"FÔRMA DA ADUELA {a['titulo']} m – CHAPA {ch.fmt_t(p.t)} mm – "
                        f"{p.qtd} PEÇAS – ARQUIVO DE CORTE {p.codigo}_CORTE"
                        f"{'_E_GRAVACAO' if p.marcas else ''}.dxf", 18, cor="#333")]
    plana, dobrada = cena_plana(p), (cena_dobrada(p) if p.linhas else None)
    paineis = [(plana, "1 – CHAPA COMO SAI DO CORTE (FACE SUPERIOR DA MESA PARA CIMA)")]
    if dobrada:
        paineis.append((dobrada, "2 – PEÇA DEPOIS DE DOBRADA"))
    larg = (W - 140) / len(paineis)
    for k, (cena, titulo) in enumerate(paineis):
        x0, x1, y0, y1 = cena.caixa()
        esc = min((larg - 60) / (x1 - x0), 560 / (y1 - y0))
        px = 70 + k * (larg + 40)
        ox = px + (larg - (x1 - x0) * esc) / 2
        oy = 200 + (580 - (y1 - y0) * esc) / 2
        s.append(texto(px, 170, titulo, 19, "700", "#1f4e8c"))
        s.append(cena.svg(ox, oy, esc))
        if k == 1:
            s.append(f'<path d="M{px - 34},{490} l24,0 m-10,-10 l10,10 l-10,10" '
                     f'stroke="#1f4e8c" stroke-width="4" fill="none"/>')
    y = 830
    plan = (f"PLANIFICAÇÃO {num(p.comprimento)} × {num(p.largura)} mm"
            if not p.contorno else f"CONTORNO RECORTADO, {num(p.comprimento)} × "
                                   f"{num(p.largura)} mm")
    det = [f"{len(p.furos)} FURO(S)" if p.furos else "SEM FUROS"]
    det += [f"{len(p.rasgos)} RASGO(S)"] if p.rasgos else []
    det += [f"{len(p.marcas)} LINHA(S) GRAVADA(S) A LASER"] if p.marcas else []
    info = [plan, ", ".join(det)]
    if p.linhas:
        info.append(f"ABAS EXTERNAS {' / '.join(num(x) for x in p.abas)} mm – RAIO INTERNO "
                    f"{num(d['ri'])} mm – MATRIZ V {d['v']} – FORÇA ESTIMADA "
                    f"{num(ch.forca_dobra_tf(p.t, p.comprimento))} tf")
        info += legenda_dobras(p)
    else:
        info.append("PEÇA PLANA: NÃO HÁ DOBRA")
    for k, linha in enumerate(info):
        s.append(texto(50, y + k * 30, linha, 19, "700" if k == 0 else "400"))
    s.append(texto(W - 50, H - 45, "LINHA VERMELHA TRACEJADA: LINHA DE DOBRA – LINHA LARANJA: "
                                   "GRAVAÇÃO A LASER (POSIÇÃO DE SOLDA) – CINZA ESCURO: FURO",
                   15, cor="#555", ancora="end"))
    s.append(texto(W - 50, H - 70, "PERSPECTIVA SEM ESCALA. COTAS E FUROS NAS PRANCHAS FA. "
                                   "ANTEPROJETO – NÃO LIBERADO PARA FABRICAÇÃO", 15, cor="#555",
                   ancora="end"))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'font-family="Liberation Sans, Arial, sans-serif">' + "".join(s) + "</svg>")


def main():
    for cod in gf.ADUELAS:
        a = gf.geometria(cod)
        pasta = os.path.join(gf.SAIDA, cod, "vistas_3d")
        os.makedirs(pasta, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            pares = []
            for p in gf.todas_as_pecas(cod):
                h = os.path.join(tmp, p.codigo + ".html")
                with open(h, "w", encoding="utf-8") as f:
                    f.write("<html><body style='margin:0'>" + imagem(p, a) + "</body></html>")
                pares += [h, os.path.join(pasta, p.codigo + ".jpg")]
            subprocess.run(["node", SHOT, str(W), str(H)] + pares, check=True)
        print(cod, len(pares) // 2, "vistas em", pasta)


if __name__ == "__main__":
    main()
