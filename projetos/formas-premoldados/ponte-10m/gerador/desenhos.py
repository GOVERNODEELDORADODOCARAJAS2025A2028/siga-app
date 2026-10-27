#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Desenhos em escala do kit "Ponte pré-moldada de 10 m" (SVG, milímetros, z para cima).

Cada função devolve um <svg class="dwg">; o desenho base (Dwg), as hachuras, a planificação
e a seção dobrada das peças de chapa ficam em ../../comum/desenho.py.
"""
import gerar_formas as gf                                                  # noqa: F401
from desenho import (HACHURAS, TEXTO_MM, Dwg, _intersecao, _soma, c,  # noqa: F401
                     espalha, extensao_dobrada, geometria_dobrada, n, planificacao,
                     secao_dobrada)


# --------------------------------------------------------------------------
# B1: corte longitudinal pelo eixo da ponte
# --------------------------------------------------------------------------
def corte_longitudinal(escala=None, term="traco"):
    """Corte longitudinal da ponte de vão único: longarinas de 10,00 m entre cabeceiras."""
    L = 10100                         # entre faces internas das cortinas
    d = Dwg(-5200, L + 5200, -3100, 7200, 380, escala, term)

    def gx(u, lado):
        return u if lado == 0 else L - u

    def r_local(u1, z1, u2, z2, cls, lado):
        d.rect(gx(u1, lado), z1, gx(u2, lado), z2, cls)

    perfil = [(-3400, 4760), (-250, 4760), (-250, 3000), (125, 3000), (125, 0), (1200, 0),
              (4200, -1800), (L - 4200, -1800), (L - 1200, 0), (L - 125, 0), (L - 125, 3000),
              (L + 250, 3000), (L + 250, 4760), (L + 3400, 4760), (L + 3400, -3000),
              (-3400, -3000)]
    d.poly(perfil, "soil")
    zw = -700
    xw = 1200 + 3000 * (-zw / 1800)
    d.poly([(xw, zw), (L - xw, zw), (L - 4200, -1800), (4200, -1800)], "water")
    d.line(xw - 600, 2600, L - xw + 600, 2600, "na")
    d.text(L / 2, 2700, "NA MÁX. A DEFINIR (ESTUDO HIDROLÓGICO)", cls="note", k=0.8)
    for lado in (0, 1):
        for i in range(9):
            u = 1350 + i * 330
            z = -(u - 1200) * 0.6 - 90
            d.circle(gx(u, lado), z, 120, "rock")

    for lado in (0, 1):
        sapata = [(-2000, -1300), (1200, -1300), (1200, -800), (800, -800), (800, 0),
                  (-400, 0), (-400, -800), (-2000, -800)]
        d.poly([(gx(u, lado), z) for u, z in sapata], "pm")
        r_local(-200, -1100, 600, 0, "cip", lado)
        r_local(-150, -1100, 550, 3000, "pm2", lado)
        r_local(125, 0, 275, 3000, "ghost", lado)
        for k in range(1, 6):
            d.line(gx(125, lado), 500 * k, gx(275, lado), 500 * k, "ghostl")
        r_local(-250, 3000, 650, 3600, "pm", lado)
        r_local(-250, 3600, 0, 4760, "pm", lado)
        r_local(-400, 4360, -250, 4510, "pm", lado)
        r_local(-3250, 4510, -250, 4760, "pm", lado)
        r_local(125, 3600, 375, 3660, "brg", lado)

    d.rect(50, 3660, L - 50, 4560, "pm2")
    d.rect(50, 4560, L - 50, 4760, "pm")
    for k in range(1, 8):
        d.line(50 + 1250 * k, 4560, 50 + 1250 * k, 4760, "joint")
    d.rect(50, 4760, L - 50, 5560, "pm")
    for k in range(1, 4):
        d.line(50 + 2500 * k, 4760, 50 + 2500 * k, 5560, "joint")

    d.text(-2400, 1600, "ATERRO", cls="tag", k=0.8)
    d.text(L + 2400, 1600, "ATERRO", cls="tag", k=0.8)
    d.text(L / 2, -1350, "RIO", cls="tag", k=0.8)

    d.dim_h(50, L - 50, 6200, "10,00 (LONGARINA)")
    d.dim_h(0, L, 6850, "10,10 (ENTRE FACES DAS CORTINAS)")
    d.dim_h(550, L - 550, 700, "9,00 (ABERTURA LIVRE ENTRE PILARES)", k=0.85)
    d.dim_v(0, 3000, -3900, "3,00")
    d.dim_v(3000, 3600, -3900, "0,60", k=0.75)
    d.dim_v(3600, 4760, -3900, "1,16", k=0.8)
    d.dim_v(0, 4760, -4600, "4,76")

    d.callout(1, 3000, 5870, 3000, 5560)
    d.callout(2, 4400, 5870, 4400, 4700)
    d.callout(3, 7000, 3000, 7000, 3660)
    d.callout(4, 1500, 3300, 650, 3300)
    d.callout(5, 1500, 1500, 550, 1500)
    d.callout(6, 1500, 2400, 275, 2400)
    d.callout(7, -1300, 5400, -150, 4300)
    d.callout(8, -2400, 3600, -1800, 4600)
    d.callout(9, -900, -2000, -900, -1100)
    d.callout(10, 2700, 3250, 375, 3630)
    d.callout(11, 3300, -300, 2300, -650)
    return d.svg("Corte longitudinal da ponte de vão único de 10 m, em escala", 640, "b1")


# --------------------------------------------------------------------------
# B2: seção transversal do tabuleiro sobre a travessa
# --------------------------------------------------------------------------
def guarda_rodas(d, y0, sinal, z0):
    pts = [(0, 0), (400, 0), (400, 75), (230, 250), (170, 800), (0, 800)]
    d.poly([(y0 + sinal * y, z0 + z) for y, z in pts], "pm")


def secao_transversal(escala=None, term="traco"):
    d = Dwg(-900, 5400, 2500, 6450, 135, escala, term)
    vigas = (450, 1650, 2850, 4050)
    d.rect(-70, 3000, 4570, 3600, "pm")
    for c in (80, 2250, 4420):
        d.rect(c - 150, 2500, c + 150, 3000, "pm2")
    for c in vigas:
        d.rect(c - 150, 3600, c + 150, 3660, "brg")
        d.rect(c - 150, 3660, c + 150, 4560, "pm2")
    d.rect(0, 4560, 4500, 4760, "pm")
    for c in vigas:
        d.rect(c - 100, 4560, c + 100, 4760, "cip")
    guarda_rodas(d, 0, 1, 4760)
    guarda_rodas(d, 4500, -1, 4760)
    d.dim_h(0, 4500, 6050, "4,50")
    d.dim_h(400, 4100, 5250, "PISTA 3,70")
    d.dim_h(1650, 2850, 4950, "1,20", k=0.8)
    d.dim_h(2850, 4050, 4950, "1,20", k=0.8)
    d.dim_v(3660, 4560, 4950, "0,90", k=0.8)
    d.dim_v(4560, 4760, 5250, "0,20", k=0.7)
    d.dim_v(3000, 3600, 4950, "0,60", k=0.8)
    d.callout(1, -500, 5400, 120, 5300)
    d.callout(2, 1050, 4950, 1050, 4700)
    d.callout(3, 1650, 4100)
    d.callout(4, -500, 3300, -70, 3300)
    d.callout(5, 2250, 2750)
    d.callout(6, 4750, 4640, 4050, 4700)
    d.callout(7, -500, 3800, 300, 3630)
    return d.svg("Seção transversal do tabuleiro de 4,50 m, em escala", 520, "b2")


# --------------------------------------------------------------------------
# B3: cabeceira vista do rio
# --------------------------------------------------------------------------
def cabeceira_frontal(escala=None, term="traco"):
    d = Dwg(-1300, 5600, -2800, 6000, 165, escala, term)
    pil = (80, 2250, 4420)
    for y1, y2 in ((-270, 1410), (1410, 3090), (3090, 4770)):
        d.rect(y1, -1300, y2, -800, "pm")
        d.rect(y1, -800, y2, 0, "pm")
    for y1 in (165, 2335):
        for k in range(6):
            d.rect(y1, 500 * k, y1 + 2000, 500 * (k + 1), "pm")
        for zc in (250, 1250):
            d.circle(y1 + 1000, zc, 28, "void")
    for c in pil:
        d.rect(c - 150, 0, c + 150, 3000, "pm2")
    for yg in (150, 2180, 2320, 4350):
        d.line(yg, 0, yg, 3000, "hidden")
    for c in pil:
        d.rect(c - 200, -1100, c + 200, 0, "hiddenr")
    d.rect(-70, 3000, 4570, 3600, "pm")
    d.rect(-70, 3600, 4570, 4760, "pm")
    for c in (450, 1650, 2850, 4050):
        d.rect(c - 150, 3600, c + 150, 3660, "brg")
        d.rect(c - 150, 3660, c + 150, 4560, "pm2")
    d.rect(0, 4560, 4500, 4760, "pm")
    guarda_rodas(d, 0, 1, 4760)
    guarda_rodas(d, 4500, -1, 4760)
    d.dim_h(165, 2165, -1650, "2,00", k=0.85)
    d.dim_h(2335, 4335, -1650, "2,00", k=0.85)
    d.dim_h(80, 2250, -2050, "2,17", k=0.85)
    d.dim_h(2250, 4420, -2050, "2,17", k=0.85)
    d.dim_h(-70, 4570, -2500, "4,64")
    d.dim_v(0, 3000, 5000, "6 × 0,50", k=0.85)
    d.dim_v(3000, 3600, 5000, "0,60", k=0.75)
    d.dim_v(3600, 4760, 5000, "1,16", k=0.8)
    d.dim_v(0, 4760, 5450, "4,76")
    d.dim_v(-1300, 0, 5000, "1,30", k=0.8)
    d.callout(1, -800, 1500, -70, 1500)
    d.callout(2, 1165, 2250)
    d.callout(3, 1650, 1250, 1195, 1250)
    d.callout(4, -800, 3300, -70, 3300)
    d.callout(5, -800, 4200, -70, 4200)
    d.callout(6, 3335, 4100, 2850, 4100)
    d.callout(7, -800, -1050, -270, -1050)
    d.callout(8, 2950, -550, 2450, -550)
    return d.svg("Cabeceira vista do rio, em escala", 520, "b3")


# --------------------------------------------------------------------------
# B4: planta do pilar intermediário da cabeceira, com ranhuras e placas
# --------------------------------------------------------------------------
def planta_pilar(escala=None, term="traco"):
    d = Dwg(-760, 760, -820, 760, 34, escala, term)
    d.rect(-760, -700, -75, 700, "soil")
    d.text(-470, -560, "ATERRO", cls="tag", k=0.8)
    d.text(470, -560, "RIO", cls="tag", k=0.8)
    for s in (1, -1):
        d.rect(-75, s * 85, 75, s * 700, "pm")
    d.poly([(-350, -150), (-90, -150), (-90, -70), (90, -70), (90, -150), (350, -150),
            (350, 150), (90, 150), (90, 70), (-90, 70), (-90, 150), (-350, 150)], "pm2")
    d.dim_h(-350, 350, 300, "0,70", tx=230)
    d.dim_v(-150, 150, -420, "0,30")
    d.dim_h(-90, 90, -110, "0,18", k=0.75, tx=175)
    d.dim_v(70, 150, 125, "0,08", k=0.7)
    d.dim_v(-70, 70, 230, "0,14", k=0.7)
    d.dim_h(-75, 75, 620, "0,15", k=0.75, tx=215)
    d.text(0, -760, "FOLGA DE 15 mm EM CADA FACE DA PLACA", cls="note", k=0.85)
    return d.svg("Planta do pilar intermediário da cabeceira com as duas ranhuras e as placas "
                 "encaixadas", 380, "b4")


# --------------------------------------------------------------------------
# F1: seção da forma da longarina
# --------------------------------------------------------------------------
def secao_forma_longarina(escala=None, term="seta"):
    """Seção da fôrma da longarina: fundo, painéis laterais com nervuras, tirante e chanfros."""
    d = Dwg(-560, 840, -230, 1190, 24, escala, term)
    ch = 20
    d.poly([(-150 + ch, 0), (150 - ch, 0), (150, ch), (150, 900), (-150, 900), (-150, ch)],
           "conc")
    d.poly([(-320, 0), (320, 0), (320, -75), (313.7, -75), (313.7, -6.3), (-313.7, -6.3),
            (-313.7, -75), (-320, -75)], "steel")
    for s in (1, -1):
        pts = [(150, 0), (250, 0), (250, 4.75), (154.75, 4.75), (154.75, 995.25),
               (225, 995.25), (225, 1000), (150, 1000)]
        d.poly([(s * y, z) for y, z in pts], "steel")
        y1, y2 = sorted((s * 154.75, s * 217.75))
        d.rect(y1, 12.75, y2, 986.75, "steel2")
        y1, y2 = sorted((s * 190, s * 196.3))
        d.rect(y1, 1000, y2, 1080, "steel")
        d.line(s * 210, -30, s * 210, 30, "bolt")
        y1, y2 = sorted((s * 196.3, s * 226.3))
        d.rect(y1, 1028, y2, 1052, "nut")
        d.poly([(s * 150, 0), (s * (150 - ch), 0), (s * 150, ch)], "chanf")
    d.line(-250, 1040, 250, 1040, "rod")
    d.text(0, 560, "LONGARINA", cls="tag", k=0.9)
    d.text(0, 500, "300 × 900", cls="tag", k=0.9)
    d.dim_h(-150, 150, 950, "300", ext=900)
    d.dim_v(0, 900, -100, "900")
    d.dim_v(0, 1000, -400, "1000", ext=-250)
    d.dim_h(-320, 320, -150, "640", ext=-75)
    d.rotulo("F-LON-02", 380, 700, 186, 700)
    d.rotulo("F-LON-01", 380, 400, 152.4, 400)
    d.rotulo(["F-LON-04", "TIRANTE 5/8\""], 380, 1120, 193.2, 1065)
    d.rotulo("F-LON-05", 380, -40, 317, -40)
    d.rotulo("PARAFUSO M16", 380, -120, 210, -22)
    d.rotulo("CHANFRO 20 × 20", -125, 130, -141, 7)
    return d.svg("Seção da fôrma da longarina com fundo, painéis, nervuras e tirante", 380, "f1")


def secao_forma_placa(escala=None, term="seta"):
    """Seção da fôrma da placa de saia: fundo, trilhos, tubo do dreno e chanfros."""
    d = Dwg(-400, 620, -165, 245, 16, escala, term)
    ch = 20
    d.poly([(-250 + ch, 0), (250 - ch, 0), (250, ch), (250, 150), (-250, 150), (-250, ch)],
           "conc")
    d.poly([(-350, 0), (350, 0), (350, -63), (345.25, -63), (345.25, -4.75), (-345.25, -4.75),
            (-345.25, -63), (-350, -63)], "steel")
    for s in (1, -1):
        pts = [(250, 0), (325, 0), (325, 6.3), (256.3, 6.3), (256.3, 150), (250, 150)]
        d.poly([(s * y, z) for y, z in pts], "steel")
        d.line(s * 295, -20, s * 295, 25, "bolt")
        d.poly([(s * 250, 0), (s * (250 - ch), 0), (s * 250, ch)], "chanf")
    d.line(-25, 0, -25, 150, "hidden")
    d.line(25, 0, 25, 150, "hidden")
    d.text(-110, 95, "PLACA DE SAIA", cls="tag", k=0.9)
    d.dim_h(-250, 250, 200, "500", ext=150)
    d.dim_v(0, 150, -300, "150", k=0.9)
    d.dim_h(-350, 350, -125, "700", ext=-63)
    d.rotulo("F-PLA-03 E F-PLA-04", 380, 110, 253, 110)
    d.rotulo("F-PLA-01", 380, -40, 347.6, -40)
    d.rotulo("PARAFUSO M16", 380, -95, 295, -18)
    d.rotulo(["TUBO-FÔRMA", "DIÂMETRO 50"], 120, 60, 25, 40)
    d.rotulo("CHANFRO 20 × 20", -195, 40, -242, 6)
    return d.svg("Seção da fôrma da placa de saia", 360, "f2")


def modulos_longarina(escala=None, term="seta"):
    d = Dwg(-600, 10600, -900, 900, 230, escala, term)
    for k in range(4):
        x1 = 2500 * k
        for s in (1, -1):
            d.rect(x1, s * 150, x1 + 2500, s * 250, "steel2")
    d.rect(-6.3, -250, 0, 250, "steel")
    d.rect(10000, -250, 10006.3, 250, "steel")
    d.rect(0, -150, 10000, 150, "conc")
    d.line(0, -320, 10000, -320, "hidden")
    d.line(0, 320, 10000, 320, "hidden")
    for k in range(1, 4):
        d.line(2500 * k, -330, 2500 * k, 330, "jointb")
    for k in range(4):
        d.text(2500 * k + 1250, -60, f"MÓDULO {k + 1}", cls="note", k=0.85)
    d.dim_h(0, 10000, 650, "4 × 2500 = 10000")
    d.text(-300, -700, "TESTEIRA", cls="note", k=0.8, anchor="start")
    d.text(10300, -700, "TESTEIRA", cls="note", k=0.8, anchor="end")
    return d.svg("Planta da forma da longarina em 4 módulos de 2,50 m", 520, "f3")


# --------------------------------------------------------------------------
# FORMA DO PAINEL DE LAJE (F-LAJ)
# --------------------------------------------------------------------------
def _perfil_concreto_painel(L, e, rb, ch=15):
    """Borda do painel com chave fêmea (rebaixo rb entre z = 50 e 150, rampas de 45°) e
    chanfros de ch nas arestas inferiores e superiores."""
    return [(ch, 0), (L - ch, 0), (L, ch), (L, 50), (L - rb, 50 + rb), (L - rb, 150 - rb),
            (L, 150), (L, e - ch), (L - ch, e), (ch, e), (0, e - ch), (0, 150), (rb, 150 - rb),
            (rb, 50 + rb), (0, 50), (0, ch)]


def secao_forma_painel(P, escala=None, term="seta"):
    """Corte da fôrma do painel na linha dos nichos (atravessa os 1230 mm)."""
    B, e, rb = P["largura"], P["espessura"], P["chave"]["rebaixo"]
    (bx, by), (tx, ty) = P["nicho_base"], P["nicho_topo"]
    ch = 15
    d = Dwg(-330, B + 330, -160, e + 150, 24, escala, term)
    d.rect(-100, -6.3, B + 100, 0, "steel")
    for s, y0 in ((1, 0), (-1, B)):
        d.poly([(y0 - s * 100, -6.3), (y0, -6.3), (y0, -11.05), (y0 - s * 95.25, -11.05),
                (y0 - s * 95.25, -69.3), (y0 - s * 100, -69.3)], "steel")
        d.poly([(y0, 0), (y0 - s * 75, 0), (y0 - s * 75, 4.75), (y0 - s * 4.75, 4.75),
                (y0 - s * 4.75, e - 4.75), (y0 - s * 75, e - 4.75), (y0 - s * 75, e),
                (y0, e)], "steel")
    d.poly(_perfil_concreto_painel(B, e, rb, ch), "conc")
    for s, y0 in ((1, 0), (-1, B)):
        d.pline([(y0, 30), (y0, 50), (y0 + s * rb, 50 + rb), (y0 + s * rb, 150 - rb),
                 (y0, 150), (y0, 170)], "hat")
        d.poly([(y0, 0), (y0 + s * ch, 0), (y0, ch)], "chanf")
        d.poly([(y0, e), (y0 + s * ch, e), (y0, e - ch)], "chanf")
    for yc in P["nichos_y"]:
        d.poly([(yc - by / 2, 0), (yc + by / 2, 0), (yc + ty / 2, e), (yc - ty / 2, e)], "void")
        d.line(yc - by / 2, 0, yc - ty / 2, e, "hat")
        d.line(yc + by / 2, 0, yc + ty / 2, e, "hat")
        d.rect(yc - 130, e - 6.3, yc + 130, e, "steel")
        d.line(yc, e + 14, yc, -20, "bolt")
        d.rect(yc - 10, -18.3, yc + 10, -6.3, "nut")
        d.rect(yc - 12, e, yc + 12, e + 10, "nut")
    y1, y2 = P["nichos_y"]
    d.text(B / 2, 80, "PAINEL DE LAJE", cls="tag", k=0.9)
    d.dim_h(0, B, -110, f"{B}", ext=-70)
    d.dim_v(0, e, B + 110, f"{e}", ext=B + 75)
    d.dim_h(0, y1, e + 55, c(y1), k=0.9, ext=e)
    d.dim_h(y1, y2, e + 55, c(y2 - y1), k=0.9)
    d.dim_h(y2, B, e + 55, c(B - y2), k=0.9, ext=e)
    d.dim_h(y2 - ty / 2, y2 + ty / 2, e + 105, f"{ty} NO TOPO", k=0.9, ext=e + 12)
    d.dim_h(y2 - by / 2, y2 + by / 2, -45, f"{by} NA BASE", k=0.9)
    d.rotulo("F-LAJ-01", B + 170, -25, B + 60, -3)
    d.rotulo("F-LAJ-02", B + 170, -85, B + 97.6, -60)
    d.rotulo("F-LAJ-05", -170, 185, -40, e - 2.4)
    d.rotulo("F-LAJ-06", -170, 100, 12, 100)
    d.rotulo("F-LAJ-08 E F-LAJ-09", y1 + 210, e + 105, y1 + 116, e - 25)
    d.rotulo("F-LAJ-10 E BARRA M12", y1 - 60, e + 105, y1 - 40, e - 3, lado=-1)
    d.rotulo("PORCA M12 SOLDADA", y2 + 120, -140, y2 + 8, -14)
    return d.svg("Corte da fôrma do painel de laje na linha dos nichos", 560, "f4")


def planta_painel(P, escala=None, term="seta"):
    """Planta do painel com nichos, insertos, eixos das vigas e chaves."""
    L, B = P["comprimento"], P["largura"]
    (bx, by), (tx, ty) = P["nicho_base"], P["nicho_topo"]
    d = Dwg(-520, L + 500, -560, B + 470, 88, escala, term)
    d.rect(0, 0, L, B, "pm")
    d.rect(0, 0, 400, B, "zone")
    d.rect(L - 400, 0, L, B, "zone")
    for c in P["vigas_x"]:
        d.rect(c - 150, 0, c + 150, B, "beamline")
    d.line(L / 2, -80, L / 2, B + 80, "modj")
    d.line(0, 0, L, 0, "key")
    d.line(0, B, L, B, "key")
    for c in P["vigas_x"]:
        for y in P["nichos_y"]:
            d.rect(c - bx / 2, y - by / 2, c + bx / 2, y + by / 2, "void")
            d.rect(c - tx / 2, y - ty / 2, c + tx / 2, y + ty / 2, "hiddenr")
        for y in P["nivelamento_y"]:
            d.rect(c - 25, y - 25, c + 25, y + 25, "lev")
    for x in P["icamento_x"]:
        for y in P["nichos_y"]:
            d.circle(x, y, 45, "ins")
    for x, y in P["esperas_guarda_rodas"]:
        d.circle(x, y, 22, "esp")
    v = P["vigas_x"]
    d.dim_h(0, L, B + 250, f"{L}")
    marcos = [0, *v, L]
    for a, b in zip(marcos, marcos[1:]):
        d.dim_h(a, b, -300, n(b - a), k=0.8)
    d.dim_h(0, L / 2, -480, f"MÓDULO DO FUNDO {n(L / 2)}", k=0.75)
    d.dim_h(L / 2, L, -480, f"MÓDULO DO FUNDO {n(L / 2)}", k=0.75)
    y1, y2 = P["nichos_y"]
    d.dim_v(0, y1, L + 250, n(y1).replace(".", ","), k=0.75)
    d.dim_v(y1, y2, L + 250, n(y2 - y1), k=0.75)
    d.dim_v(y2, B, L + 250, n(B - y2).replace(".", ","), k=0.75)
    d.dim_v(0, B, L + 420, f"{B}")
    d.callout(1, v[1], B + 130, v[1], y2 + ty / 2)
    d.callout(2, P["icamento_x"][0], B + 130, P["icamento_x"][0], y2 + 45)
    d.callout(3, v[2], B + 130, v[2], P["nivelamento_y"][1] + 25)
    d.callout(4, 3300, B + 130, 3300, B)
    d.callout(5, 200, B + 130, 200, B - 60)
    d.callout(6, -300, 600, v[0] - 150, 600)
    d.callout(7, L / 2 + 220, -120, L / 2, -40)
    d.callout(8, L - 200, B + 130, P["esperas_guarda_rodas"][3][0], P["esperas_guarda_rodas"][3][1] + 22)
    return d.svg("Planta do painel de laje com nichos, insertos e eixos das longarinas", 620, "f5")


def detalhe_junta(P, escala=None, term="seta"):
    """Junta fêmea-fêmea entre dois painéis, com chanfros, graute, tarugo e revestimento."""
    e, rb = P["espessura"], P["chave"]["rebaixo"]
    g = P["modulo"] - P["largura"]        # abertura da junta: 20 mm
    ch = 15
    d = Dwg(-470, g + 470, -110, e + 150, 16, escala, term)
    esq = [(-300, 0), (-ch, 0), (0, ch), (0, 50), (-rb, 50 + rb), (-rb, 150 - rb), (0, 150),
           (0, e - ch), (-ch, e), (-300, e)]
    d.poly(esq, "conc")
    d.poly([(g - x, z) if x != -300 else (g + 300, z) for x, z in esq], "conc")
    zt = ch + g                            # topo do tarugo comprimido na garganta
    d.poly([(0, zt), (g, zt), (g, 50), (g + rb, 50 + rb), (g + rb, 150 - rb), (g, 150),
            (g, e - ch), (g + ch, e), (-ch, e), (0, e - ch), (0, 150), (-rb, 150 - rb),
            (-rb, 50 + rb), (0, 50)], "grout")
    d.circle(g / 2, ch + g / 2, g / 2 - 0.5, "rod2")
    d.rect(-300, e, g + 300, e + 5, "memb")
    d.rect(-300, e + 5, g + 300, e + 55, "asph")
    d.dim_h(0, g, -40, f"{n(g)}", k=0.9, ext=ch)
    d.dim_h(-rb, 0, -80, f"{rb}", k=0.9, ext=50)
    d.cadeia([0, 50, 50 + rb, 150 - rb, 150, e], g + 330, "v", g + 300, k=0.9)
    d.rotulo("GRAUTE SEM RETRAÇÃO", 150, 120, g / 2, 120)
    d.rotulo("TARUGO DE ESPUMA DIÂMETRO 25", 120, -60, g / 2, ch + 4)
    d.rotulo("MANTA IMPERMEABILIZANTE", -60, e + 95, -60, e + 3, lado=-1)
    d.rotulo("REVESTIMENTO ASFÁLTICO 50", 140, e + 95, 140, e + 40)
    d.rotulo("REBAIXO DE 25 (RÉGUA F-LAJ-06)", -150, 100, -rb + 1, 100, lado=-1)
    d.rotulo("CHANFRO 15 × 15", -150, -60, -6, 5, lado=-1)
    return d.svg("Junta fêmea-fêmea entre painéis, com graute e revestimento", 380, "f6")
