#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Desenhos em escala das aduelas e das fôrmas (SVG, milímetros).

Cortes verticais: x é a distância radial a partir da face interna da parede (positiva para
fora) e z a altura a partir da base de moldagem (ponta do macho). Plantas: x e y no plano
horizontal, com origem no eixo da aduela; o lado da laje superior fica em cima (y positivo).
O desenho base (Dwg), a planificação e a seção dobrada ficam em ../../comum/desenho.py.
"""
import math

import gerar_formas as gf                     # noqa: F401  (inclui comum/ no caminho)
from desenho import Dwg, c, n                 # noqa: F401
from desenho import extensao_dobrada, planificacao, secao_dobrada  # noqa: F401,E501

E = gf.E_PLACA          # chapas planas da base e do anel
EP = gf.E_PELE          # faces, cantos, nervuras e cintas
EF = gf.E_PERFIL        # cantoneiras
CA, CB = gf.CANT        # abas da cantoneira (soldada, aparafusada)
CI = gf.CINTA[1]        # alma da cinta
ND, NW = gf.NERV[0], gf.NERV[1]   # nervura: profundidade e largura


# --------------------------------------------------------------------------
# GEOMETRIA
# --------------------------------------------------------------------------
def perfil_parede(a):
    """Perfil da parede no corte vertical: (r, z), r a partir da face interna."""
    t = a["t"]
    return [(0, 0), (0, gf.H_NUC), (a["s_fundo"], gf.H_NUC), (a["s_fundo"], gf.H_NUC + E),
            (a["s_boca"], gf.H_EXT), (t, gf.H_EXT), (t, gf.P_MACHO), (a["wm_ombro"], gf.P_MACHO),
            (a["wm_ombro"], gf.P_MACHO - E), (a["wm_ponta"], 0)]


def quadrado(h):
    return [(-h, -h), (h, -h), (h, h), (-h, h)]


def contorno_interno(B, m):
    h = B / 2
    return [(-h + m, -h), (h - m, -h), (h, -h + m), (h, h - m), (h - m, h), (-h + m, h),
            (-h, h - m), (-h, -h + m)]


def gira(pts, k):
    """Gira pontos de k × 90 graus em torno da origem (sentido anti-horário)."""
    for _ in range(k % 4):
        pts = [(-y, x) for x, y in pts]
    return pts


def desloca(pts, dist):
    """Desloca uma poligonal aberta de 'dist' para a esquerda do sentido de percurso."""
    linhas = []
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        L = math.hypot(x2 - x1, y2 - y1)
        nx, ny = -(y2 - y1) / L, (x2 - x1) / L
        linhas.append(((x1 + nx * dist, y1 + ny * dist), (x2 - x1, y2 - y1)))
    out = [linhas[0][0]]
    for (p1, d1), (p2, d2) in zip(linhas, linhas[1:]):
        det = d1[0] * (-d2[1]) - d1[1] * (-d2[0])
        rx, ry = p2[0] - p1[0], p2[1] - p1[1]
        s = (rx * (-d2[1]) - ry * (-d2[0])) / det
        out.append((p1[0] + s * d1[0], p1[1] + s * d1[1]))
    (p, d) = linhas[-1]
    out.append((p[0] + d[0], p[1] + d[1]))
    return out


def chapa_dobrada(linha, esp):
    """Polígono de uma chapa ao longo de uma poligonal (face de referência à direita)."""
    return linha + desloca(linha, esp)[::-1]


def recorta(svg):
    """SVG de vista parcial: o desenho fica limitado ao retângulo da vista."""
    return svg.replace('style="width:', 'style="overflow:hidden;width:', 1)


def ruptura_v(d, x, z1, z2):
    a = d.mm(1.4)
    pts, k = [(x, z1)], 7
    for i in range(1, k):
        pts.append((x + (a if i % 2 else -a), z1 + (z2 - z1) * i / k))
    pts.append((x, z2))
    d.pline(pts, "rupt")


def ruptura_h(d, z, x1, x2):
    a = d.mm(1.4)
    pts, k = [(x1, z)], 7
    for i in range(1, k):
        pts.append((x1 + (x2 - x1) * i / k, z + (a if i % 2 else -a)))
    pts.append((x2, z))
    d.pline(pts, "rupt")


# --------------------------------------------------------------------------
# ADUELA (ELEMENTO DE CONCRETO)
# --------------------------------------------------------------------------
def secao_aduela(a, escala):
    """Seção transversal da aduela na posição de assentamento."""
    B, t, m, Be = a["B"], a["t"], a["m"], a["Be"]
    h, H = B / 2, Be / 2
    k = escala
    d = Dwg(-H - 22 * k, H + 26 * k, -H - 26 * k, H + 14 * k, 0, escala, "traco")
    d.line(-H - 6 * k, 0, H + 6 * k, 0, "beamline")
    d.line(0, -H - 6 * k, 0, H + 6 * k, "beamline")
    d.poly_vazado([quadrado(H), contorno_interno(B, m)], "conc")
    d.rect(-55, h, 55, H, "hfundo")
    d.line(-55, h, -55, H, "vis")
    d.line(55, h, 55, H, "vis")
    d.text(-B / 4, h + t / 2 - d.fs * 0.35, "LAJE SUPERIOR", cls="tag", k=0.9)
    d.text(0, -h - t / 2 - d.fs * 0.35, "LAJE INFERIOR", cls="tag", k=0.9)
    for s in (-1, 1):
        d.text(s * (h + t / 2) + d.fs * 0.35, 0, "PAREDE", cls="tag", k=0.9, rot=-90)
    d.cadeia([-H, -h, h, H], -H - 8 * k, "h", -H)
    d.dim_h(-H, H, -H - 17 * k, c(Be), ext=-H)
    d.cadeia([-H, -h, h, H], H + 8 * k, "v", H)
    d.dim_v(-H, H, H + 17 * k, c(Be), ext=H)
    d.dim_h(-h, -h + m, -h + m + 6 * k, c(m), ext=-h)
    d.dim_v(-h, -h + m, -h + m + 6 * k, c(m), ext=-h)
    d.rotulo(["FURO DE IÇAMENTO", "DIÂMETRO 110"], 55 + 14 * k, H + 7 * k, 30, H - t / 3)
    d.rotulo(f"MÍSULA {c(m)} × {c(m)}", -h + m + 14 * k, -h + m + 14 * k, -h + m / 2,
             -h + m / 2)
    return d.svg(f"Seção transversal da aduela {a['nome']}", 400, f"sa-{a['codigo']}")


def corte_longitudinal(a, escala):
    """Corte longitudinal pelo eixo vertical da aduela assentada: laje superior e laje
    inferior em corte, encaixe nas extremidades e furo de içamento."""
    B, t, m, Be = a["B"], a["t"], a["m"], a["Be"]
    h, H = B / 2, Be / 2
    k = escala
    z_ic = gf.altura_icamento(a)
    d = Dwg(-12 * k, gf.H_EXT + 22 * k, -H - 22 * k, H + 22 * k, 0, escala, "traco")
    d.line(-6 * k, 0, gf.H_EXT + 6 * k, 0, "beamline")
    for s in (1, -1):
        d.poly([(z, s * (h + r)) for r, z in perfil_parede(a)], "conc")
        d.line(0, s * (h - m), gf.H_NUC, s * (h - m), "rupt")
    d.line(0, -h, 0, h, "rupt")
    d.line(gf.H_NUC, -h, gf.H_NUC, h, "rupt")
    d.rect(z_ic - 55, h, z_ic + 55, H + 0.5, "hfundo")
    d.line(z_ic - 55, h, z_ic - 55, H, "vis")
    d.line(z_ic + 55, h, z_ic + 55, H, "vis")
    d.cadeia([0, gf.P_MACHO, gf.H_NUC, gf.H_EXT], -H - 8 * k, "h", -H)
    d.dim_h(gf.P_MACHO, gf.H_EXT, -H - 17 * k, f"{gf.L_UTIL} ÚTIL", ext=-H)
    d.cadeia([0, z_ic], H + 8 * k, "h", H)
    d.dim_h(0, gf.H_EXT, H + 17 * k, c(gf.H_EXT), ext=H)
    d.cadeia([-H, -h, h, H], gf.H_EXT + 9 * k, "v", gf.H_EXT)
    d.text(gf.H_EXT / 2, 0 + d.fs * 0.35 + d.mm(1), "INTERIOR DA GALERIA", cls="note", k=0.85)
    d.text(gf.P_MACHO / 2, -h + d.mm(4), "MACHO", cls="note", k=0.8)
    d.text(gf.H_EXT - 40, -h + d.mm(4), "BOLSA", cls="note", k=0.8)
    return d.svg(f"Corte longitudinal da aduela {a['nome']}", 300, f"cl-{a['codigo']}")


def detalhe_encaixe(a, escala):
    """Encaixe entre duas aduelas assentadas, na laje superior: bolsa da aduela N e macho
    da aduela N + 1, com a argamassa de rejuntamento."""
    t = a["t"]
    k = escala
    x0, x1 = gf.H_EXT - 150, gf.H_EXT + 120
    L = gf.L_UTIL
    d = Dwg(x0 - 6 * k, x1 + 30 * k, -24 * k, t + 26 * k, 0, escala, "seta")
    sf, sb, wp, wo = a["s_fundo"], a["s_boca"], a["wm_ponta"], a["wm_ombro"]
    d.poly([(x0, 0), (gf.H_NUC, 0), (gf.H_NUC, sf), (gf.H_NUC + E, sf), (gf.H_EXT, sb),
            (gf.H_EXT, t), (x0, t)], "conc")
    d.poly([(L, 0), (x1, 0), (x1, t), (L + gf.P_MACHO, t), (L + gf.P_MACHO, wo),
            (L + gf.P_MACHO - E, wo), (L, wp)], "conc")
    d.poly([(gf.H_NUC, 0), (L, 0), (L, wp), (L + gf.P_MACHO - E, wo), (L + gf.P_MACHO, wo),
            (gf.H_EXT, sb), (gf.H_NUC + E, sf), (gf.H_NUC, sf)], "grout")
    ruptura_v(d, x0, -4 * k, t + 4 * k)
    ruptura_v(d, x1, -4 * k, t + 4 * k)
    d.dim_h(gf.H_NUC, L, -7 * k, c(L - gf.H_NUC), ext=0)
    d.cadeia([L, L + gf.P_MACHO], -16 * k, "h", 0, rotulos=[f"MACHO {gf.P_MACHO}"])
    d.cadeia([gf.H_NUC, gf.H_EXT], t + 8 * k, "h", t, rotulos=[f"BOLSA {gf.P_BOLSA}"])
    d.dim_v(0, t, x1 + 10 * k, c(t), ext=x1)
    d.dim_v(0, wp, L + 6 * k, c(wp))
    d.dim_v(0, wo, L + gf.P_MACHO + 6 * k, c(wo))
    d.dim_v(sf, t, gf.H_NUC - 6 * k, c(t - sf))
    d.dim_v(sb, t, gf.H_EXT - 6 * k, c(t - sb))
    d.rotulo("ADUELA N", x0 + 10 * k, t + 16 * k, x0 + 40, t - 30, lado=1)
    d.rotulo("ADUELA N + 1", x1 - 4 * k, t + 16 * k, x1 - 40, t - 30, lado=1)
    d.rotulo("ARGAMASSA DE REJUNTAMENTO", L + 30 * k, -9 * k, gf.H_NUC + 5, 6)
    d.rotulo(f"FOLGA RADIAL {c(a['folga_radial'])} NA BOCA", gf.H_EXT + 14 * k, sb + 10 * k,
             gf.H_EXT - 3, (wo + sb) / 2)
    d.text(x0 + 60, t + d.mm(1.2), "FACE EXTERNA", cls="note", k=0.8, anchor="start")
    d.text(x0 + 60, -d.mm(1.2) - d.fs * 0.6, "FACE INTERNA", cls="note", k=0.8, anchor="start")
    return d.svg(f"Encaixe macho e fêmea da aduela {a['nome']}", 300, f"ec-{a['codigo']}")


# --------------------------------------------------------------------------
# FÔRMA MONTADA: PLANTA (CORTE HORIZONTAL NA ALTURA DO FURO DE IÇAMENTO)
# --------------------------------------------------------------------------
def _lado_planta(a):
    """Peças de um lado (o inferior, y negativo) e do canto inferior direito, na planta.
    Devolve listas (pontos, classe) de polígonos e (x1, y1, x2, y2, classe) de linhas."""
    B, t, m, r, Be, Bn = a["B"], a["t"], a["m"], a["r"], a["Be"], a["Bn"]
    h, H, hn = B / 2, Be / 2, Bn / 2
    pol, lin = [], []
    # ---- fôrma externa: painel, cantoneiras, nervuras e cinta (oculta)
    pol.append(([(-h, -H - EP), (h, -H - EP), (h, -H), (-h, -H)], "steel"))
    yb = -H - EP

    def cant_ext(x, s):           # s = +1: aba aparafusada à direita do ponto x
        return [(x, yb), (x - s * CA, yb), (x - s * CA, yb - EF), (x - s * EF, yb - EF),
                (x - s * EF, yb - CB), (x, yb - CB)]
    pol.append((cant_ext(h, 1), "steel"))
    pol.append((cant_ext(-h, -1), "steel"))
    for xk in gf.eixos_nervuras(B, a["n_ext"]):
        x1, x2 = -h + xk - NW / 2, -h + xk + NW / 2
        pol.append(([(x1, yb), (x1 + EP, yb), (x1 + EP, yb - ND + EP), (x2 - EP, yb - ND + EP),
                     (x2 - EP, yb), (x2, yb), (x2, yb - ND), (x1, yb - ND)], "steel"))
    lin.append((-h + CA + 2, yb - CI, h - CA - 2, yb - CI, "hidden"))
    # ---- canto externo e suas cantoneiras
    pol.append(([(h, -H), (H, -H), (H, -h), (H + EP, -h), (H + EP, -H - EP), (h, -H - EP)],
                "steel"))
    pol.append(([(h, yb), (h + CA, yb), (h + CA, yb - EF), (h + EF, yb - EF), (h + EF, yb - CB),
                 (h, yb - CB)], "steel"))
    xb = H + EP
    pol.append(([(xb, -h), (xb, -h - CA), (xb + EF, -h - CA), (xb + EF, -h - EF),
                 (xb + CB, -h - EF), (xb + CB, -h)], "steel"))
    lin.append((h - 22, -H - FURO, h + 22, -H - FURO, "bolt"))
    # ---- núcleo: painel, cantoneiras, nervuras e cinta (oculta)
    yn = -h + EP
    pol.append(([(-hn, -h), (hn, -h), (hn, yn), (-hn, yn)], "steel"))

    def cant_nuc(x, s):
        return [(x, yn), (x - s * CA, yn), (x - s * CA, yn + EF), (x - s * EF, yn + EF),
                (x - s * EF, yn + CB), (x, yn + CB)]
    pol.append((cant_nuc(hn, 1), "steel"))
    pol.append((cant_nuc(-hn, -1), "steel"))
    for xk in gf.eixos_nervuras(Bn, a["n_nuc"]):
        x1, x2 = -hn + xk - NW / 2, -hn + xk + NW / 2
        pol.append(([(x1, yn), (x1 + EP, yn), (x1 + EP, yn + ND - EP), (x2 - EP, yn + ND - EP),
                     (x2 - EP, yn), (x2, yn), (x2, yn + ND), (x1, yn + ND)], "steel"))
    lin.append((-hn + CA + 2, yn + CI, hn - CA - 2, yn + CI, "hidden"))
    # ---- canto do núcleo com mísula e suas cantoneiras
    face = [(hn, -h), (h - m, -h), (h, -h + m), (h, -hn)]
    pol.append((chapa_dobrada(face, EP), "steel"))
    pol.append(([(hn, yn), (hn + CA, yn), (hn + CA, yn + EF), (hn + EF, yn + EF),
                 (hn + EF, yn + CB), (hn, yn + CB)], "steel"))
    xn = h - EP
    pol.append(([(xn, -hn), (xn, -hn - CA), (xn - EF, -hn - CA), (xn - EF, -hn - EF),
                 (xn - CB, -hn - EF), (xn - CB, -hn)], "steel"))
    lin.append((hn - 22, -h + FURO, hn + 22, -h + FURO, "bolt"))
    return pol, lin


FURO = gf.FURO_FACE


def planta_forma(a, escala, janela=None, ident=None):
    """Planta da fôrma montada, em corte horizontal na altura do furo de içamento, vista de
    cima. 'janela' = (x1, y1, x2, y2) para vista parcial."""
    B, t, m, Be, Bn = a["B"], a["t"], a["m"], a["Be"], a["Bn"]
    h, H = B / 2, Be / 2
    k = escala
    ext = H + EP + CB
    if janela:
        x1, y1, x2, y2 = janela
        d = Dwg(x1, x2, y1, y2, 0, escala, "seta")
    else:
        d = Dwg(-ext - 19 * k, ext + 19 * k, -ext - 24 * k, ext + 14 * k, 0, escala, "seta")
    d.poly_vazado([quadrado(H), contorno_interno(B, m)], "conc")
    pol, lin = _lado_planta(a)
    for q in range(4):
        for pts, cls in pol:
            d.poly(gira(pts, q), cls)
        for xa, ya, xb, yb, cls in lin:
            (xa, ya), (xb, yb) = gira([(xa, ya), (xb, yb)], q)
            d.line(xa, ya, xb, yb, cls)
    # tubo-fôrma do furo de içamento, na laje superior (lado de cima)
    d.rect(-55, h, 55, H, "ins")
    d.line(0, h - EP - 40, 0, H + EP + 40, "rod")
    for yy in (h - EP - 12, H + EP):
        d.rect(-14, yy, 14, yy + 12, "nut")
    if janela:
        return recorta(d.svg(f"Detalhe da planta da fôrma {a['nome']}", 300,
                             ident or f"dp-{a['codigo']}"))
    F = lambda n_: f"F-{a['codigo']}-{n_:02d}"
    xs = [-h + x for x in gf.eixos_nervuras(B, a["n_ext"])]
    d.text(-B / 4, h + t / 2 - d.fs * 0.35, "LAJE SUPERIOR", cls="tag", k=0.85)
    d.text(B / 4, -h - t / 2 - d.fs * 0.35, "LAJE INFERIOR", cls="tag", k=0.85)
    yb = -H - EP
    d.rotulo(F(1), -h + 60, -ext - 12 * k, -h + 60, -H - EP / 2, lado=-1)
    d.rotulo(F(2), -h + 140, ext + 8 * k, -h + 140, H + EP / 2, lado=-1)
    d.rotulo(F(7), xs[0], -ext - 19 * k, xs[0], yb - ND + 2, lado=1)
    d.rotulo(F(3), H + 8 * k, -ext - 12 * k, H + EP / 2, -H - 40)
    d.rotulo(F(4), h + 20 * k, -ext - 19 * k, h + EF / 2, yb - CB + 8)
    d.rotulo(F(6), -h - 10 * k, -ext - 19 * k, -h + CA + 40, yb - CI, lado=-1)
    d.rotulo([F(8), F(14)], -B / 4, -h + 32 * k, -B / 4, -h + EP / 2, lado=1)
    d.rotulo(F(9), B / 4, h - 18 * k, B / 4, h - EP / 2, lado=1)
    d.rotulo([F(10), F(11)], h - 55 * k, -h + 26 * k, h - m / 2 - 2, -h + m / 2 + 2, lado=-1)
    d.rotulo(F(13), -h + CA + 40, -h + 14 * k, -h + CA + 40, -h + EP + CI, lado=1)
    d.rotulo(["TUBO-FÔRMA DE 110", "E BARRA M16"], 70 + 14 * k, ext + 10 * k, 40, H - t / 3)
    d.cadeia([-H, -h, h, H], -ext - 5 * k, "h", -H - EP)
    d.dim_h(-H, H, ext + 5 * k, c(Be), ext=H + EP)
    d.cadeia([-H, -h, h, H], ext + 6 * k, "v", H + EP)
    return d.svg(f"Planta da fôrma montada da aduela {a['nome']}", 400, f"pf-{a['codigo']}")


def detalhe_canto(a, escala):
    """Vista parcial ampliada da planta no canto inferior direito."""
    B, t, m, r = a["B"], a["t"], a["m"], a["r"]
    h, H = B / 2, a["Be"] / 2
    hn = a["Bn"] / 2
    x1, x2 = hn - 70, H + EP + CB + 60
    y1, y2 = -(H + EP + CB + 60), -(hn - 70)
    svg = planta_forma(a, escala, janela=(x1, y1, x2, y2), ident=f"dc-{a['codigo']}")
    return svg


# --------------------------------------------------------------------------
# FÔRMA MONTADA: CORTE VERTICAL PELO MEIO DA LAJE SUPERIOR
# --------------------------------------------------------------------------
def corte_forma(a, escala, janela=None, ident=None):
    """Corte vertical da fôrma montada pelo meio do painel da laje superior. x radial a
    partir da face interna (positivo para fora), z a partir da face superior da base.
    'janela' = (x1, z1, x2, z2) para os detalhes da base e do anel superior."""
    t, Be = a["t"], a["Be"]
    k = escala
    z_ic = gf.altura_icamento(a)
    hb, hk = gf.H_BARRA_MACHO, gf.H_BARRA_BOLSA
    _, ebm = gf.barra(hb, gf.RECUO_MACHO)
    _, ebs = gf.barra(hk, gf.RECUO_BOLSA)
    wp, wm, s0, sb = a["wm_ponta"], a["wm"], a["s0"], a["s_boca"]
    re_ = t + EP                                   # face posterior da pele externa
    rn = -EP                                       # face posterior da pele do núcleo
    r_ins = (sb + t) / 2
    r_cinta = t + EP + 60
    if janela:
        x1, z1, x2, z2 = janela
        d = Dwg(x1, x2, z1, z2, 0, escala, "seta")
    else:
        d = Dwg(-gf.BASE_INT - 44 * k, t + gf.BASE_EXT + 52 * k, -E - 16 * k,
                gf.H_EXT + 12 * k, 0, escala, "seta")
    d.poly(perfil_parede(a), "conc")
    d.rect(0, z_ic - 55, t, z_ic + 55, "ins")
    d.line(rn - 40, z_ic, re_ + 40, z_ic, "rod")
    for x0 in (rn - 12, re_):
        d.rect(x0, z_ic - 14, x0 + 12, z_ic + 14, "nut")
    # base: chapa, ressalto e barras
    d.rect(-gf.BASE_INT, -E, t + gf.BASE_EXT, 0, "steel")
    d.rect(wm, hb, t - 1, gf.P_MACHO, "steel")
    d.poly([(wp, 0), (wm, hb), (wm + ebm, hb), (wp + ebm, 0)], "steel")
    d.rect(t - 1.5 - E, 0, t - 1.5, hb, "steel")
    # fôrma externa: pele, cantoneira de base, nervura (vista), cinta e parafuso
    d.rect(t, 0, re_, gf.H_EXT, "steel")
    d.rect(re_, CA + 2, re_ + ND, gf.H_EXT - gf.CINTA[0] - 2, "steel2")
    d.poly([(re_, 0), (re_ + CB, 0), (re_ + CB, EF), (re_ + EF, EF), (re_ + EF, CA), (re_, CA)],
           "steel")
    hc = gf.CINTA[0]
    d.poly([(re_, gf.H_EXT), (re_ + CI, gf.H_EXT), (re_ + CI, gf.H_EXT - hc),
            (re_ + CI - EP, gf.H_EXT - hc), (re_ + CI - EP, gf.H_EXT - EP),
            (re_ + EP, gf.H_EXT - EP), (re_ + EP, gf.H_EXT - hc), (re_, gf.H_EXT - hc)], "steel")
    d.line(t + FURO, -E - 14, t + FURO, EF + 14, "bolt")
    d.rect(t + FURO - 12, EF, t + FURO + 12, EF + 12, "nut")
    # núcleo: pele, cantoneira de base, nervura (vista), cinta e parafuso
    d.rect(rn, 0, 0, gf.H_NUC, "steel")
    d.rect(rn - ND, CA + 2, rn, gf.H_NUC - hc - 2, "steel2")
    d.poly([(rn, 0), (rn - CB, 0), (rn - CB, EF), (rn - EF, EF), (rn - EF, CA), (rn, CA)],
           "steel")
    d.poly([(rn, gf.H_NUC), (rn - CI, gf.H_NUC), (rn - CI, gf.H_NUC - hc),
            (rn - CI + EP, gf.H_NUC - hc), (rn - CI + EP, gf.H_NUC - EP),
            (rn - EP, gf.H_NUC - EP), (rn - EP, gf.H_NUC - hc), (rn, gf.H_NUC - hc)], "steel")
    d.line(-FURO, -E - 14, -FURO, EF + 14, "bolt")
    d.rect(-FURO - 12, EF, -FURO + 12, EF + 12, "nut")
    # anel superior: chapa, barra da saia e parafuso na cinta do núcleo
    d.rect(-gf.ANEL_INT, gf.H_NUC, s0, gf.H_NUC + E, "steel")
    d.poly([(s0 - ebs, gf.H_NUC + E), (s0, gf.H_NUC + E), (sb, gf.H_EXT),
            (sb - ebs, gf.H_EXT)], "steel")
    d.line(-FURO, gf.H_NUC - EP - 14, -FURO, gf.H_NUC + E + 14, "bolt")
    d.rect(-FURO - 12, gf.H_NUC + E, -FURO + 12, gf.H_NUC + E + 12, "nut")
    # régua porta-inserto e inserto de içamento no topo da bolsa
    d.rect(r_ins - 40, gf.H_EXT, r_cinta + 40, gf.H_EXT + E, "steel")
    d.line(r_cinta, gf.H_EXT - EP - 14, r_cinta, gf.H_EXT + E + 14, "bolt")
    d.rect(r_ins - 12, gf.H_EXT - 90, r_ins + 12, gf.H_EXT, "ins")
    d.line(r_ins, gf.H_EXT - 60, r_ins, gf.H_EXT + E + 14, "rod")
    F = lambda n_: f"F-{a['codigo']}-{n_:02d}"
    if janela:
        x1, z1, x2, z2 = janela
        if z1 < 0:                           # detalhe da base
            d.cadeia([0, wp], -E - 6 * k, "h", 0)
            d.dim_h(0, wm, -E - 12 * k, c(wm), ext=gf.P_MACHO)
            d.dim_h(0, t, -E - 18 * k, c(t), ext=0)
            d.dim_v(0, gf.P_MACHO, wp - 5 * k, c(gf.P_MACHO), ext=wp)
            d.dim_h(t, t + FURO, EF + 10 * k, c(FURO), ext=EF + 12)
            d.dim_h(-FURO, 0, EF + 10 * k, c(FURO), ext=EF + 12)
            xd, xe = re_ + CB + 4 * k, rn - CB - 4 * k
            d.rotulo(F(16), xd, -E - 9 * k, t + gf.BASE_EXT - 20, -E / 2)
            d.rotulo(F(17), xd, gf.P_MACHO + 22 * k, (wm + t) / 2, gf.P_MACHO - 2)
            d.rotulo(F(18), xe, gf.P_MACHO + 22 * k, wm + ebm / 2, hb * 0.6, lado=-1)
            d.rotulo(F(19), xd, gf.P_MACHO + 14 * k, t - 4.5, hb * 0.5)
            d.rotulo(F(5), xd, CA + 4 * k, re_ + EF / 2, CA - 8)
            d.rotulo(F(12), xe, CA + 4 * k, rn - EF / 2, CA - 8, lado=-1)
            d.rotulo("PARAFUSO M16", xd, -E - 16 * k, t + FURO, -E - 8)
            d.rotulo("PARAFUSO M16", xe, -E - 9 * k, -FURO, -E - 8, lado=-1)
        else:                                # detalhe do anel superior
            d.dim_h(0, s0, gf.H_NUC - 8 * k, c(s0), ext=gf.H_NUC)
            d.dim_h(0, sb, gf.H_EXT + 7 * k, c(sb), ext=gf.H_EXT)
            d.dim_v(gf.H_NUC, gf.H_EXT, t + EP + CI + 8 * k, c(gf.P_BOLSA), ext=re_ + CI)
            xd, xe = re_ + CI + 4 * k, rn - CI - 4 * k
            d.rotulo(F(20), xe, gf.H_NUC + 12 * k, -gf.ANEL_INT + 20, gf.H_NUC + E / 2,
                     lado=-1)
            d.rotulo(F(21), xe, gf.H_EXT + 6 * k, (s0 + sb) / 2 - ebs / 2, gf.H_EXT - 30,
                     lado=-1)
            d.rotulo(F(13), xe, gf.H_NUC - 24 * k, rn - CI + EP / 2, gf.H_NUC - 30, lado=-1)
            d.rotulo(F(6), xd, gf.H_EXT - 24 * k, re_ + CI - EP / 2, gf.H_EXT - 30)
            d.rotulo(F(22), xd, gf.H_EXT + 14 * k, r_cinta + 30, gf.H_EXT + E / 2)
            d.rotulo("INSERTO DE IÇAMENTO", xd, gf.H_EXT - 12 * k, r_ins + 12, gf.H_EXT - 70)
        return recorta(d.svg(f"Detalhe do corte da fôrma da aduela {a['nome']}", 300,
                             ident or f"dcf-{a['codigo']}"))
    xr = t + gf.BASE_EXT                           # cotas à direita, rótulos além delas
    d.cadeia([0, gf.P_MACHO, z_ic, gf.H_NUC, gf.H_EXT], xr + 7 * k, "v", re_ + CI)
    d.dim_v(0, gf.H_EXT, xr + 15 * k, c(gf.H_EXT), ext=re_ + CI)
    d.dim_v(0, gf.H_NUC, -gf.BASE_INT - 8 * k, c(gf.H_NUC), ext=rn - CI)
    d.dim_h(0, t, -E - 9 * k, c(t), ext=0)
    xl = xr + 22 * k
    d.rotulo([F(1), F(2)], xl, gf.H_EXT * 0.40, re_ - EP / 2, gf.H_EXT * 0.40)
    d.rotulo(F(7), xl, gf.H_EXT * 0.64, re_ + ND / 2, gf.H_EXT * 0.64)
    d.rotulo(["TUBO-FÔRMA DE 110", "E BARRA M16"], xl, z_ic + 22 * k, t - 30, z_ic + 30)
    d.rotulo("CONCRETO DA ADUELA", xl, gf.H_EXT * 0.22, t / 2, gf.H_EXT * 0.22)
    d.rotulo(F(6), xl, gf.H_EXT + 4 * k, re_ + CI - EP / 2, gf.H_EXT - 25)
    xe = -gf.BASE_INT - 16 * k
    d.rotulo([F(8), F(9)], xe, gf.H_NUC * 0.40, rn + EP / 2, gf.H_NUC * 0.40, lado=-1)
    d.rotulo(F(14), xe, gf.H_NUC * 0.64, rn - ND / 2, gf.H_NUC * 0.64, lado=-1)
    d.rotulo(F(13), xe, gf.H_NUC - 4 * k, rn - CI + EP / 2, gf.H_NUC - 25, lado=-1)
    d.rotulo(F(16), xe, -E - 8 * k, -gf.BASE_INT + 20, -E / 2, lado=-1)
    return d.svg(f"Corte vertical da fôrma montada da aduela {a['nome']}", 300,
                 f"cf-{a['codigo']}")


def detalhe_base(a, escala):
    t, k = a["t"], escala
    return corte_forma(a, escala, janela=(-EP - CB - 30 * k, -E - 22 * k,
                                          t + EP + CB + 30 * k, gf.P_MACHO + 30 * k),
                       ident=f"db-{a['codigo']}")


def detalhe_anel(a, escala):
    t, k = a["t"], escala
    return corte_forma(a, escala, janela=(-EP - CI - 28 * k, gf.H_NUC - 40 * k,
                                          t + EP + CI + 40 * k, gf.H_EXT + 22 * k),
                       ident=f"da-{a['codigo']}")


# --------------------------------------------------------------------------
# PLANTAS DA BASE E DO ANEL SUPERIOR
# --------------------------------------------------------------------------
def _catavento(lado, larg):
    """Quatro retângulos em catavento: o primeiro no lado inferior, com o canto esquerdo."""
    So = lado
    r1 = [(-So / 2, -So / 2), (So / 2 - larg, -So / 2), (So / 2 - larg, -So / 2 + larg),
          (-So / 2, -So / 2 + larg)]
    return [gira(r1, q) for q in range(4)]


def planta_base(a, escala, pecas):
    """Planta da base: chapas em catavento, ressalto, furos e contornos de referência."""
    B, t, m, Be = a["B"], a["t"], a["m"], a["Be"]
    k = escala
    pb = pecas[f"F-{a['codigo']}-16"]
    So, w = pb.catavento["So"], pb.catavento["w"]
    d = Dwg(-So / 2 - 8 * k, So / 2 + 36 * k, -So / 2 - 20 * k, So / 2 + 8 * k, 0, escala,
            "seta")
    for ret in _catavento(So, w):
        d.poly(ret, "vis")
    ri, ro = a["wm"], t - 1
    for ret in _catavento(B + 2 * ro, ro - ri):
        d.poly(ret, "rupt")
    d.poly(quadrado(B / 2 + a["wm_ponta"]), "ghost")
    d.poly(contorno_interno(B, m), "ghost")
    d.poly(quadrado(Be / 2 + EP), "ghost")
    x0 = -So / 2
    for q in range(4):
        for x, y, dd in pb.furos:
            (gx, gy), = gira([(x + x0, y + x0)], q)
            d.circle(gx, gy, dd / 2, "furo")
    F = lambda n_: f"F-{a['codigo']}-{n_:02d}"
    xd = So / 2 + 6 * k
    d.rotulo(F(16), xd, So / 2 - w / 2, So / 2 - w / 2, So / 2 - w / 3)
    d.rotulo(F(17), xd, So / 2 - w - 14 * k, B / 2 + (ri + ro) / 2, B / 4)
    d.rotulo(["CHUMBADOR M16", "4 NOS CANTOS"], xd, -So / 2 + 2 * k, Be / 2 + 55, -Be / 2 - 55)
    d.cadeia([-So / 2, So / 2 - w, So / 2], -So / 2 - 6 * k, "h", -So / 2)
    d.dim_h(-So / 2, So / 2, -So / 2 - 14 * k, c(So), ext=-So / 2)
    return d.svg(f"Planta da base da aduela {a['nome']}", 400, f"pb-{a['codigo']}")


def planta_anel(a, escala, pecas):
    """Planta do anel superior: quatro chapas com juntas a 45 graus, barras da saia e furos."""
    B, m = a["B"], a["m"]
    k = escala
    pa = pecas[f"F-{a['codigo']}-20"]
    S = pa.comprimento
    loc = pa.contorno
    d = Dwg(-S / 2 - 18 * k, S / 2 + 30 * k, -S / 2 - 20 * k, S / 2 + 11 * k, 0, escala, "seta")
    _, ebs = gf.barra(gf.H_BARRA_BOLSA, gf.RECUO_BOLSA)
    for q in range(4):
        d.poly(gira([(x - S / 2, y - S / 2) for x, y in loc], q), "vis")
        d.poly(gira([(-S / 2 + ebs, -S / 2), (S / 2, -S / 2), (S / 2, -S / 2 + ebs),
                     (-S / 2 + ebs, -S / 2 + ebs)], q), "steel")
        for x, y, dd in pa.furos:
            (gx, gy), = gira([(x - S / 2, y - S / 2)], q)
            d.circle(gx, gy, dd / 2, "furo")
    d.poly(contorno_interno(B, m), "ghost")
    F = lambda n_: f"F-{a['codigo']}-{n_:02d}"
    d.rotulo(F(20), -S / 4, -S / 2 - 12 * k, -S / 4, -S / 2 + 80, lado=-1)
    d.rotulo(F(21), S / 4, -S / 2 - 12 * k, S / 4, -S / 2 + ebs / 2, lado=1)
    d.dim_h(-S / 2, S / 2, S / 2 + 6 * k, c(S), ext=S / 2)
    d.cadeia([-S / 2, -B / 2, -B / 2 + gf.ANEL_INT], -S / 2 - 5 * k, "h", -S / 2)
    return d.svg(f"Planta do anel superior da aduela {a['nome']}", 400, f"pa-{a['codigo']}")
