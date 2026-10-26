#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Desenhos em escala do kit "Ponte pré-moldada de 10 m" (SVG, milímetros, z para cima).

Usado pela página de apresentação e pelo caderno de fabricação em PDF. Cada função
devolve um <svg class="dwg"> pronto para ser inserido numa página HTML; as cores
vêm das classes CSS (pm, pm2, cip, soil, steel, conc etc.) definidas pela página.
"""
import html

def n(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


class Dwg:
    """Desenho em milímetros, com z para cima."""

    def __init__(self, xmin, xmax, zmin, zmax, fs):
        self.xmin, self.xmax, self.zmin, self.zmax, self.fs = xmin, xmax, zmin, zmax, fs
        self.items = []
        self.callouts = []

    def X(self, x):
        return x - self.xmin

    def Z(self, z):
        return self.zmax - z

    def rect(self, x1, z1, x2, z2, cls):
        xa, xb = sorted((x1, x2))
        za, zb = sorted((z1, z2))
        self.items.append(f'<rect class="{cls}" x="{n(self.X(xa))}" y="{n(self.Z(zb))}" '
                          f'width="{n(xb - xa)}" height="{n(zb - za)}"/>')

    def poly(self, pts, cls):
        p = " ".join(f"{n(self.X(x))},{n(self.Z(z))}" for x, z in pts)
        self.items.append(f'<polygon class="{cls}" points="{p}"/>')

    def pline(self, pts, cls):
        p = " ".join(f"{n(self.X(x))},{n(self.Z(z))}" for x, z in pts)
        self.items.append(f'<polyline class="{cls}" points="{p}"/>')

    def line(self, x1, z1, x2, z2, cls):
        self.items.append(f'<line class="{cls}" x1="{n(self.X(x1))}" y1="{n(self.Z(z1))}" '
                          f'x2="{n(self.X(x2))}" y2="{n(self.Z(z2))}"/>')

    def circle(self, x, z, r, cls):
        self.items.append(f'<circle class="{cls}" cx="{n(self.X(x))}" cy="{n(self.Z(z))}" '
                          f'r="{n(r)}"/>')

    def text(self, x, z, s, anchor="middle", cls="lbl", k=1.0, rot=None):
        tr = ""
        if rot is not None:
            tr = f' transform="rotate({rot} {n(self.X(x))} {n(self.Z(z))})"'
        self.items.append(f'<text class="{cls}" x="{n(self.X(x))}" y="{n(self.Z(z))}" '
                          f'text-anchor="{anchor}" font-size="{n(self.fs * k)}"{tr}>'
                          f'{html.escape(s)}</text>')

    def _tick(self, x, z):
        t = self.fs * 0.35
        self.line(x - t, z - t, x + t, z + t, "tick")

    def dim_h(self, x1, x2, z, label, k=0.9, tx=None):
        self.line(x1, z, x2, z, "dim")
        self._tick(x1, z)
        self._tick(x2, z)
        xt = (x1 + x2) / 2 if tx is None else tx
        self.text(xt, z + self.fs * 0.35, label, k=k, cls="dimt")

    def dim_v(self, z1, z2, x, label, k=0.9):
        self.line(x, z1, x, z2, "dim")
        self._tick(x, z1)
        self._tick(x, z2)
        self.text(x - self.fs * 0.35, (z1 + z2) / 2, label, k=k, cls="dimt", rot=-90)

    def callout(self, num, x, z, tx=None, tz=None):
        r = self.fs * 0.62
        if tx is not None:
            self.items.append(f'<line class="lead" x1="{n(self.X(x))}" y1="{n(self.Z(z))}" '
                              f'x2="{n(self.X(tx))}" y2="{n(self.Z(tz))}"/>')
        self.items.append(f'<g class="co"><circle cx="{n(self.X(x))}" cy="{n(self.Z(z))}" '
                          f'r="{n(r)}"/><text x="{n(self.X(x))}" y="{n(self.Z(z))}" '
                          f'font-size="{n(self.fs * 0.78)}">{num}</text></g>')

    def svg(self, title, minw, ident):
        w, h = self.xmax - self.xmin, self.zmax - self.zmin
        return (f'<svg class="dwg" viewBox="0 0 {n(w)} {n(h)}" style="--minw:{minw}px" '
                f'role="img" aria-labelledby="{ident}"><title id="{ident}">{html.escape(title)}'
                f'</title>' + "".join(self.items) + "</svg>")


# --------------------------------------------------------------------------
# B1: corte longitudinal pelo eixo da ponte
# --------------------------------------------------------------------------
def corte_longitudinal():
    d = Dwg(-5200, 25350, -4600, 7200, 380)
    L = 20150

    def gx(u, lado):
        return u if lado == 0 else L - u

    def r_local(u1, z1, u2, z2, cls, lado):
        d.rect(gx(u1, lado), z1, gx(u2, lado), z2, cls)

    perfil = [(-5200, 4760), (-250, 4760), (-250, 3000), (125, 3000), (125, 0), (1200, 0),
              (4200, -1800), (L - 4200, -1800), (L - 1200, 0), (L - 125, 0), (L - 125, 3000),
              (L + 250, 3000), (L + 250, 4760), (25350, 4760), (25350, -4600), (-5200, -4600)]
    d.poly(perfil, "soil")
    zw = -700
    xw = 1200 + 3000 * (-zw / 1800)
    d.poly([(xw, zw), (L - xw, zw), (L - 4200, -1800), (4200, -1800)], "water")
    d.line(xw - 600, 2600, L - xw + 600, 2600, "na")
    d.text(11000, 2700, "NA de cheia máxima (posição ilustrativa)", anchor="start", cls="note", k=0.8)
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

    xc = L / 2
    d.rect(xc - 750, -3000, xc + 750, -1900, "cip")
    for dx in (-550, 250):
        d.rect(xc + dx, -4500, xc + dx + 300, -3000, "cipd")
    d.rect(xc - 150, -1900, xc + 150, 3000, "pm2")
    d.rect(xc - 450, 3000, xc + 450, 3600, "pm")
    for c in (xc - 225, xc + 225):
        d.rect(c - 125, 3600, c + 125, 3660, "brg")

    for x1, x2 in ((50, 10050), (10100, 20100)):
        d.rect(x1, 3660, x2, 4560, "pm2")
        d.rect(x1, 4560, x2, 4760, "pm")
        for k in range(1, 8):
            d.line(x1 + 1250 * k, 4560, x1 + 1250 * k, 4760, "joint")
    d.rect(50, 4760, 20100, 5560, "pm")
    for k in range(1, 8):
        d.line(50 + 2500 * k, 4760, 50 + 2500 * k, 5560, "joint")

    d.text(-2400, 1600, "ATERRO", cls="tag", k=0.8)
    d.text(L + 2400, 1600, "ATERRO", cls="tag", k=0.8)
    d.text(7000, -1350, "RIO", cls="tag", k=0.8)

    d.dim_h(50, 10050, 6200, "10,00 m")
    d.dim_h(10100, 20100, 6200, "10,00 m")
    d.dim_h(0, L, 6850, "20,15 m entre cortinas")
    d.dim_v(0, 3000, -3700, "3,00")
    d.dim_v(3000, 3600, -3700, "0,60", k=0.75)
    d.dim_v(3600, 4760, -3700, "1,16", k=0.8)
    d.dim_v(0, 4760, -4300, "4,76 m")

    d.callout(1, 3000, 5870, 3000, 5560)
    d.callout(2, 4400, 5870, 4400, 4700)
    d.callout(3, 6000, 3000, 6000, 3660)
    d.callout(4, 1500, 3300, 650, 3300)
    d.callout(5, 1500, 1500, 550, 1500)
    d.callout(6, 1500, 2400, 275, 2400)
    d.callout(7, -1300, 5400, -150, 4300)
    d.callout(8, -2400, 3600, -1800, 4600)
    d.callout(9, -900, -2000, -900, -1100)
    d.callout(10, 2700, 3250, 375, 3630)
    d.callout(11, xc + 1300, 1000, xc + 150, 1000)
    d.callout(12, xc + 1500, -2500, xc + 750, -2500)
    d.callout(13, 3300, -300, 2300, -650)
    return d.svg("Corte longitudinal da ponte de dois vãos de 10 m, em escala", 820, "b1")


# --------------------------------------------------------------------------
# B2: seção transversal do tabuleiro sobre a travessa
# --------------------------------------------------------------------------
def guarda_rodas(d, y0, sinal, z0):
    pts = [(0, 0), (400, 0), (400, 75), (230, 250), (170, 800), (0, 800)]
    d.poly([(y0 + sinal * y, z0 + z) for y, z in pts], "pm")


def secao_transversal():
    d = Dwg(-900, 5400, 2500, 6450, 135)
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
    d.dim_h(0, 4500, 6050, "4,50 m")
    d.dim_h(400, 4100, 5250, "pista livre 3,70 m")
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
def cabeceira_frontal():
    d = Dwg(-1300, 5600, -2800, 6000, 165)
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
    d.dim_h(-70, 4570, -2500, "4,64 m (saia)")
    d.dim_v(0, 3000, 5000, "6 × 0,50", k=0.85)
    d.dim_v(3000, 3600, 5000, "0,60", k=0.75)
    d.dim_v(3600, 4760, 5000, "1,16", k=0.8)
    d.dim_v(0, 4760, 5450, "4,76 m")
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
# B4: planta do pilar central com ranhuras e placas
# --------------------------------------------------------------------------
def planta_pilar():
    d = Dwg(-760, 760, -820, 760, 34)
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
    d.dim_v(-70, 70, 230, "alma 0,14", k=0.7)
    d.dim_h(-75, 75, 620, "placa 0,15", k=0.75, tx=215)
    d.text(0, -760, "folga de 15 mm de cada lado da placa", cls="note", k=0.85)
    return d.svg("Planta do pilar central com as duas ranhuras e as placas encaixadas", 380, "b4")


# --------------------------------------------------------------------------
# F1: seção da forma da longarina
# --------------------------------------------------------------------------
def secao_forma_longarina():
    d = Dwg(-560, 560, -150, 1180, 24)
    d.rect(-150, 0, 150, 900, "conc")
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
    d.line(-250, 1040, 250, 1040, "rod")
    d.dim_h(-150, 150, 450, "viga 300")
    d.dim_v(0, 900, -90, "900")
    d.dim_v(0, 1000, -400, "painel 1000")
    d.dim_h(-320, 320, -125, "fundo 640", k=0.9)
    d.callout(1, 420, 600, 217, 600)
    d.callout(2, 420, 300, 186, 300)
    d.callout(3, 420, -50, 320, -40)
    d.callout(4, 420, 1110, 226, 1040)
    d.callout(5, 420, 100, 250, 15)
    d.callout(6, -420, 600, -150, 600)
    return d.svg("Seção da forma da longarina com fundo, painéis, nervuras e tirante", 380, "f1")


def secao_forma_placa():
    d = Dwg(-420, 420, -120, 260, 16)
    d.rect(-250, 0, 250, 150, "conc")
    d.poly([(-350, 0), (350, 0), (350, -63), (345.25, -63), (345.25, -4.75), (-345.25, -4.75),
            (-345.25, -63), (-350, -63)], "steel")
    for s in (1, -1):
        pts = [(250, 0), (325, 0), (325, 6.3), (256.3, 6.3), (256.3, 150), (250, 150)]
        d.poly([(s * y, z) for y, z in pts], "steel")
        d.line(s * 295, -20, s * 295, 25, "bolt")
    d.line(0, 0, 0, 150, "hidden")
    d.dim_h(-250, 250, 190, "placa 500")
    d.dim_v(0, 150, -300, "150", k=0.9)
    d.dim_h(-350, 350, -95, "fundo 700", k=0.9)
    d.callout(1, 380, 100, 256, 100)
    d.callout(2, 380, -40, 345, -30)
    d.callout(3, -380, 80, -250, 80)
    d.callout(4, 120, 225, 0, 150)
    return d.svg("Seção da forma da placa de saia", 360, "f2")


def modulos_longarina():
    d = Dwg(-600, 10600, -900, 900, 230)
    for k in range(4):
        x1 = 2500 * k
        for s in (1, -1):
            d.rect(x1, s * 150, x1 + 2500, s * 250, "steel")
    d.rect(-6.3, -250, 0, 250, "steel")
    d.rect(10000, -250, 10006.3, 250, "steel")
    d.rect(0, -150, 10000, 150, "conc")
    d.line(0, -320, 10000, -320, "hidden")
    d.line(0, 320, 10000, 320, "hidden")
    for k in range(1, 4):
        d.line(2500 * k, -330, 2500 * k, 330, "jointb")
    for k in range(4):
        d.text(2500 * k + 1250, -60, f"módulo {k + 1}", cls="note", k=0.85)
    d.dim_h(0, 10000, 650, "4 módulos × 2,50 = 10,00 m")
    d.text(-300, -700, "testeira", cls="note", k=0.8, anchor="start")
    d.text(10300, -700, "testeira", cls="note", k=0.8, anchor="end")
    return d.svg("Planta da forma da longarina em 4 módulos de 2,50 m", 520, "f3")


# --------------------------------------------------------------------------
# FORMA DO PAINEL DE LAJE (F-LAJ)
# --------------------------------------------------------------------------
def _perfil_concreto_painel(L, e, rb):
    """Borda do painel com chave fêmea: rebaixo rb entre z = 50 e 150 (rampas de 45°)."""
    return [(0, 0), (L, 0), (L, 50), (L - rb, 50 + rb), (L - rb, 150 - rb), (L, 150),
            (L, e), (0, e), (0, 150), (rb, 150 - rb), (rb, 50 + rb), (0, 50)]


def secao_forma_painel(P):
    """Corte da forma do painel na linha dos nichos (atravessa os 1230 mm)."""
    B, e, rb = P["largura"], P["espessura"], P["chave"]["rebaixo"]
    (bx, by), (tx, ty) = P["nicho_base"], P["nicho_topo"]
    d = Dwg(-230, B + 250, -125, e + 130, 24)
    d.rect(-100, -6.3, B + 100, 0, "steel")
    for s, y0 in ((1, 0), (-1, B)):
        d.poly([(y0 - s * 100, -6.3), (y0, -6.3), (y0, -11.05), (y0 - s * 95.25, -11.05),
                (y0 - s * 95.25, -69.3), (y0 - s * 100, -69.3)], "steel")
        d.poly([(y0, 0), (y0 - s * 75, 0), (y0 - s * 75, 4.75), (y0 - s * 4.75, 4.75),
                (y0 - s * 4.75, e - 4.75), (y0 - s * 75, e - 4.75), (y0 - s * 75, e),
                (y0, e)], "steel")
    d.poly(_perfil_concreto_painel(B, e, rb), "conc")
    for s, y0 in ((1, 0), (-1, B)):
        d.pline([(y0, 30), (y0, 50), (y0 + s * rb, 50 + rb), (y0 + s * rb, 150 - rb),
                 (y0, 150), (y0, 170)], "hat")
    for yc in P["nichos_y"]:
        d.poly([(yc - by / 2, 0), (yc + by / 2, 0), (yc + ty / 2, e), (yc - ty / 2, e)], "void")
        d.line(yc - by / 2, 0, yc - ty / 2, e, "hat")
        d.line(yc + by / 2, 0, yc + ty / 2, e, "hat")
        d.rect(yc - 130, e - 6.3, yc + 130, e, "steel")
        d.line(yc, e + 14, yc, -20, "bolt")
        d.rect(yc - 10, -18.3, yc + 10, -6.3, "nut")
        d.rect(yc - 12, e, yc + 12, e + 10, "nut")
    y1, y2 = P["nichos_y"]
    d.dim_h(0, B, -105, f"{B}")
    d.dim_v(0, e, B + 105, f"{e}")
    d.dim_h(0, y1, e + 55, n(y1).replace(".", ","), k=0.85)
    d.dim_h(y1, y2, e + 55, n(y2 - y1), k=0.85)
    d.dim_h(y2, B, e + 55, n(B - y2).replace(".", ","), k=0.85)
    d.dim_h(y2 - ty / 2, y2 + ty / 2, e + 100, f"{ty} no topo", k=0.8)
    d.dim_h(y2 - by / 2, y2 + by / 2, -40, f"{by} na base", k=0.8)
    d.callout(1, B + 210, -30, B + 100, -3)
    d.callout(2, B + 210, -82, B + 98, -55)
    d.callout(3, -190, 150, -4, 150)
    d.callout(4, -190, 70, 12, 62)
    d.callout(5, y1 + 230, e + 110, y1 + 134, e - 20)
    d.callout(6, y1 - 110, e + 110, y1 - 20, e)
    d.callout(7, B / 2, 100)
    d.callout(8, y2 - 90, -70, y2 - 10, -14)
    return d.svg("Corte da forma do painel de laje na linha dos nichos", 560, "f4")


def planta_painel(P):
    """Planta do painel com nichos, insertos, eixos das vigas e chaves."""
    L, B = P["comprimento"], P["largura"]
    (bx, by), (tx, ty) = P["nicho_base"], P["nicho_topo"]
    d = Dwg(-520, L + 500, -560, B + 470, 88)
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
    d.dim_h(0, L / 2, -480, f"módulo do fundo {n(L / 2)}", k=0.75)
    d.dim_h(L / 2, L, -480, f"módulo do fundo {n(L / 2)}", k=0.75)
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


def detalhe_junta(P):
    """Junta fêmea-fêmea entre dois painéis, com graute, tarugo e revestimento."""
    e, rb = P["espessura"], P["chave"]["rebaixo"]
    g = P["modulo"] - P["largura"]        # abertura da junta: 20 mm
    d = Dwg(-330, 380, -95, e + 135, 16)
    esq = [(-300, 0), (0, 0), (0, 50), (-rb, 50 + rb), (-rb, 150 - rb), (0, 150), (0, e),
           (-300, e)]
    d.poly(esq, "pm")
    d.poly([(g - x, z) if x != -300 else (g + 300, z) for x, z in esq], "pm")
    d.poly([(0, 20), (g, 20), (g, 50), (g + rb, 50 + rb), (g + rb, 150 - rb), (g, 150), (g, e),
            (0, e), (0, 150), (-rb, 150 - rb), (-rb, 50 + rb), (0, 50)], "grout")
    d.circle(g / 2, 10, g / 2 - 0.5, "rod2")
    d.rect(-300, e, g + 300, e + 5, "memb")
    d.rect(-300, e + 5, g + 300, e + 55, "asph")
    d.dim_h(0, g, -45, f"{n(g)}", k=0.85)
    d.dim_h(-rb, 0, -75, f"{rb}", k=0.85)
    for a, b in ((0, 50), (50, 50 + rb), (50 + rb, 150 - rb), (150 - rb, 150), (150, e)):
        d.dim_v(a, b, g + 340, n(b - a), k=0.6)
    d.callout(1, 140, 100, g + rb - 2, 100)
    d.callout(2, -110, -55, g / 2 - 6, 6)
    d.callout(3, -170, e + 95, -170, e + 3)
    d.callout(4, 120, e + 95, 120, e + 40)
    d.callout(5, -170, 100, -rb + 1, 100)
    return d.svg("Junta fêmea-fêmea entre painéis, com graute e revestimento", 380, "f6")
