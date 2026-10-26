#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador paramétrico das formas metálicas do kit "Ponte pré-moldada de 10 m".

Gera, para cada peça de chapa das formas:
  saida/dxf/<código>_CORTE.dxf    contorno e furos, sem mais nada (arquivo do plasma)
  saida/dxf/<código>_DESENHO.dxf  contorno, furos, linhas de dobra e textos (conferência)
  saida/svg/<código>.svg          pré-visualização da planificação
  saida/tabelas/*.csv             lista de corte, tabela de dobras, compras e resumo

ATENÇÃO
  1. Raio interno de dobra e fator K (tabela DOBRA) são PROVISÓRIOS. Antes de cortar,
     substituir pelos valores da tabela de dobra do fornecedor, com o ferramental real.
  2. As dimensões das peças de concreto são de pré-dimensionamento. O engenheiro
     responsável (ART) confirma ou corrige antes da fabricação.

Uso:  python3 gerar_formas.py            (requer: pip install ezdxf)
"""

import csv
import math
import os
from dataclasses import dataclass, field

import ezdxf
from ezdxf import units

# --------------------------------------------------------------------------
# PEÇAS DE CONCRETO (pré-dimensionamento; ver README.md)
# --------------------------------------------------------------------------
VIGA = dict(
    largura=300,        # b da longarina; a forma aceita de 250 a 360 mm
    altura=900,         # h da longarina; o painel lateral tem 1000 mm e aceita até 1000
    comprimento=10_000,  # 4 módulos de 2500 mm
    modulo=2_500,
)
VIGA_B_MIN, VIGA_B_MAX = 250, 360

PLACA = dict(
    comprimento=2_000,  # placa de saia, encaixa nas ranhuras dos pilares
    altura=500,
    espessura=150,
)

# --------------------------------------------------------------------------
# CHAPA E DOBRA  (PROVISÓRIO: trocar pela tabela do fornecedor)
#   ri = raio interno resultante (mm)   k = fator K   v = abertura do V da matriz (mm)
# --------------------------------------------------------------------------
DOBRA = {
    4.75: dict(ri=6.0, k=0.42, v=40),
    6.30: dict(ri=8.0, k=0.42, v=50),
}
DENSIDADE_ACO = 7.85e-6   # kg/mm3
FURO_M16 = 18.0           # furo para parafuso M16
FURO_FIXADOR = 14.0       # furo para fixar tubo-forma (parafuso M12)
RESISTENCIA_ACO = 450     # MPa, resistência à tração de referência (chapa A36/1020)

CONCRETO_T_M3 = 2.5      # massa específica do concreto armado (NBR 6118)

# Peças de concreto da ponte (2 vãos de 10 m, largura 4,50 m, cabeceiras de 4,76 m).
# (código, peça, dimensões em m, volume unitário em m3, quantidade, forma)
KIT = [
    ("P-01", "Longarina", "0,30 x 0,90 x 10,00", 0.30 * 0.90 * 10.00, 8, "F-LON"),
    ("P-02", "Painel de laje de espessura total, 8 nichos", "4,50 x 1,25 x 0,20",
     4.50 * 1.25 * 0.20 - 8 * 0.25 * 0.20 * 0.20, 16, "F-LAJ"),
    ("P-03", "Guarda-rodas, módulo (seção a definir, ~0,20 m2)", "2,50 de comprimento",
     0.20 * 2.50, 16, "F-GUA"),
    ("P-04", "Travessa (cabeceiras e apoio central)", "4,64 x 0,90 x 0,60",
     4.64 * 0.90 * 0.60, 3, "F-TRA"),
    ("P-05", "Pilar de cabeceira com ranhura", "0,30 x 0,70 x 4,10",
     0.30 * 0.70 * 4.10 - 1.5 * 0.18 * 0.08 * 3.00, 6, "F-PIL"),
    ("P-06", "Pilar do apoio central (comprimento a definir; valor por metro)",
     "0,30 x 0,70 x 1,00", 0.30 * 0.70 * 1.00, 3, "F-PIL"),
    ("P-07", "Placa de saia", "2,00 x 0,50 x 0,15", 2.00 * 0.50 * 0.15, 24, "F-PLA"),
    ("P-08", "Cortina (2 painéis por cabeceira)", "2,32 x 1,16 x 0,25",
     2.32 * 1.16 * 0.25, 4, "F-COR"),
    # segmento de 1,68 m: calcanhar 1,60 x 0,50 + bloco do cálice 1,20 x 1,30 + ponta
    # 0,40 x 0,50 (seção no sentido do eixo), menos o cálice de 0,40 x 0,80 x 1,10
    ("P-09", "Sapata em segmento com cálice (dimensões após sondagem)",
     "~1,68 x 3,20 x 1,30 (indicativo)",
     1.68 * (1.60 * 0.50 + 1.20 * 1.30 + 0.40 * 0.50) - 0.40 * 0.80 * 1.10, 6, "F-SAP"),
    ("P-10", "Laje de transição (recomendada)", "1,55 x 3,00 x 0,25",
     1.55 * 3.00 * 0.25, 6, "F-LTR"),
]

AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.normpath(os.path.join(AQUI, "..", "saida"))


# --------------------------------------------------------------------------
# GEOMETRIA DE DOBRA
# --------------------------------------------------------------------------
def dados_dobra(t):
    p = DOBRA[t]
    ossb = p["ri"] + t                                # recuo externo (90 graus)
    ba = math.pi / 2 * (p["ri"] + p["k"] * t)          # comprimento desenvolvido da dobra
    return ossb, ba


def planifica(abas, t):
    """abas: medidas EXTERNAS dos trechos, em ordem, com dobra de 90 graus entre eles.
    Retorna (largura planificada, centros das linhas de dobra, trechos retos)."""
    ossb, ba = dados_dobra(t)
    n = len(abas)
    retos = []
    for i, a in enumerate(abas):
        n_dobras = (1 if i > 0 else 0) + (1 if i < n - 1 else 0)
        retos.append(a - n_dobras * ossb)
    largura = sum(retos) + (n - 1) * ba
    linhas, y = [], 0.0
    for i in range(n - 1):
        y += retos[i]
        linhas.append(y + ba / 2)
        y += ba
    return largura, linhas, retos


def forca_dobra_tf(t, comprimento):
    """Estimativa de força de dobra no ar (fórmula usual P = 650 t² L / V, kN, L em m)."""
    v = DOBRA[t]["v"]
    kn = 650 * t ** 2 * (comprimento / 1000) / v * (RESISTENCIA_ACO / 450)
    return kn / 9.81


@dataclass
class Peca:
    codigo: str
    nome: str
    forma: str
    t: float
    qtd: int
    comprimento: float          # medida paralela às linhas de dobra (eixo x)
    abas: list                  # medidas externas dos trechos ao longo de y
    nomes_abas: list = field(default_factory=list)
    furos: list = field(default_factory=list)   # (x, y, diâmetro)
    rasgos: list = field(default_factory=list)  # (x, y1, y2, largura): rasgo alinhado em y
    sentido: str = ""
    obs: str = ""

    def __post_init__(self):
        if len(self.abas) > 1:
            self.largura, self.linhas, self.retos = planifica(self.abas, self.t)
        else:
            self.largura, self.linhas, self.retos = self.abas[0], [], [self.abas[0]]

    @property
    def peso(self):
        area = self.comprimento * self.largura
        area -= sum(math.pi * d ** 2 / 4 for _, _, d in self.furos)
        area -= sum((abs(y2 - y1) * w + math.pi * w ** 2 / 4) for _, y1, y2, w in self.rasgos)
        return area * self.t * DENSIDADE_ACO


# --------------------------------------------------------------------------
# PEÇAS DAS FORMAS
# --------------------------------------------------------------------------
def pecas_forma_longarina():
    b, mod = VIGA["largura"], VIGA["modulo"]
    n_mod = VIGA["comprimento"] // mod
    assert VIGA["comprimento"] % mod == 0, "comprimento da viga deve ser múltiplo do módulo"
    assert VIGA_B_MIN <= b <= VIGA_B_MAX, "largura fora da faixa da forma"
    assert VIGA["altura"] <= 1000, "altura acima do painel lateral (1000 mm)"

    # posições (ao longo do módulo) dos parafusos de base e dos tirantes:
    # no meio dos vãos entre nervuras, longe das nervuras
    passo_nerv = mod / 8                       # 312,5 mm
    nervuras_x = [passo_nerv * i for i in range(1, 8)]
    meios = [passo_nerv / 2 + passo_nerv * k for k in range(8)]
    x_fix = [meios[0], meios[3], meios[4], meios[7]]   # 156,25 1093,75 1406,25 2343,75

    pecas = []

    # F-LON-01 painel lateral: aba superior 75, face 1000, aba inferior 100
    abas = [75, 1000, 100]
    lat = Peca("F-LON-01", "Painel lateral da longarina", "Longarina", 4.75, 2 * n_mod,
               mod, abas, ["aba superior", "face (concreto)", "aba inferior (base)"],
               sentido="as duas abas para tras, lado oposto a face de concreto",
               obs="Solda de nervuras, cantoneiras e orelhas pelo lado de tras. "
                   "Face de concreto sem solda e sem respingo.")
    w = lat.largura
    for x in x_fix:                      # furos da base: 60 mm da face de concreto
        lat.furos.append((x, w - (100 - 60), FURO_M16))
    pecas.append(lat)

    # F-LON-02 nervura vertical do painel: U 63-40-63, entre as abas
    comp_nerv = 1000 - 2 * 4.75 - 2 * DOBRA[4.75]["ri"] - 2 * 2
    pecas.append(Peca("F-LON-02", "Nervura vertical do painel (U)", "Longarina", 4.75,
                      7 * 2 * n_mod, math.floor(comp_nerv), [63, 40, 63],
                      ["aba", "alma", "aba"],
                      sentido="U: as duas abas para o mesmo lado",
                      obs="7 por painel, eixos a cada 312,5 mm; soldar pelas pontas das abas "
                          "na face de tras do painel."))

    # F-LON-03 cantoneira de ligação do painel: 63 (soldada) x 75 (aparafusada)
    cant = Peca("F-LON-03", "Cantoneira de ligacao do painel", "Longarina", 6.30, 2 * 2 * n_mod,
                math.floor(comp_nerv), [63, 75], ["aba soldada", "aba aparafusada"],
                sentido="uma dobra de 90 graus",
                obs="Uma em cada ponta do painel, aba soldada rente a borda; liga modulos "
                    "entre si e recebe a testeira.")
    furo_cant_z = [87 + 200 * i for i in range(5)]
    for z in furo_cant_z:                # furo a 45 mm da face de concreto
        cant.furos.append((z, cant.largura - (75 - (45 - 4.75)), FURO_M16))
    pecas.append(cant)

    # F-LON-04 orelha do tirante (chapa plana)
    ore = Peca("F-LON-04", "Orelha do tirante superior", "Longarina", 6.30, 4 * 2 * n_mod,
               80, [80], ["chapa plana"],
               obs="Soldar em pe sobre a aba superior, a 40 mm da face de concreto, "
                   "nas posicoes 156,25 / 1093,75 / 1406,25 / 2343,75 mm.")
    ore.furos.append((40, 40, FURO_M16))
    pecas.append(ore)

    # F-LON-05 fundo: U invertido, alma 640, abas 75 para baixo
    fun = Peca("F-LON-05", "Fundo da longarina (U invertido)", "Longarina", 6.30, n_mod,
               mod, [75, 640, 75], ["aba", "alma (concreto)", "aba"],
               sentido="as duas abas para baixo, lado oposto a face de concreto",
               obs="Rasgos permitem larguras de viga de 250 a 360 mm.")
    yc = fun.largura / 2
    r1, r2 = VIGA_B_MIN / 2 + 60, VIGA_B_MAX / 2 + 60   # 185 a 240 mm do eixo
    for x in x_fix:
        fun.rasgos.append((x, yc + r1, yc + r2, FURO_M16))
        fun.rasgos.append((x, yc - r2, yc - r1, FURO_M16))
    pecas.append(fun)

    # F-LON-06 cantoneira do fundo
    comp_cf = 640 - 2 * 6.30 - 2 * DOBRA[6.30]["ri"] - 2 * 2
    cf = Peca("F-LON-06", "Cantoneira de ligacao do fundo", "Longarina", 6.30, 2 * n_mod,
              math.floor(comp_cf), [63, 75], ["aba soldada", "aba aparafusada"],
              sentido="uma dobra de 90 graus",
              obs="Uma em cada ponta do fundo, soldada por baixo da alma.")
    meio = math.floor(comp_cf) / 2
    for dx in (-200, 0, 200):
        cf.furos.append((meio + dx, cf.largura - (75 - 40), FURO_M16))
    pecas.append(cf)

    # F-LON-07 nervura transversal do fundo
    pecas.append(Peca("F-LON-07", "Nervura transversal do fundo (U)", "Longarina", 4.75,
                      4 * n_mod, math.floor(comp_cf), [63, 40, 63], ["aba", "alma", "aba"],
                      sentido="U: as duas abas para o mesmo lado",
                      obs="4 por fundo, a 500 / 1000 / 1500 / 2000 mm."))

    # F-LON-08 testeira: face 1000 + aba superior 63; largura = b + 2 x 79,75
    larg_test = b + 2 * (4.75 + 75)
    test = Peca("F-LON-08", f"Testeira da longarina (b = {b} mm)", "Longarina", 6.30, 2,
                larg_test, [1000, 63], ["face (concreto)", "aba superior"],
                sentido="aba superior para fora, lado oposto ao concreto",
                obs="Peca propria de cada largura de viga. Aparafusada nas cantoneiras "
                    "F-LON-03 das duas laterais.")
    z0 = 4.75 + DOBRA[4.75]["ri"] + 2          # inicio da cantoneira acima do fundo
    for z in furo_cant_z:
        for x in (larg_test / 2 - (b / 2 + 45), larg_test / 2 + (b / 2 + 45)):
            test.furos.append((x, z0 + z, FURO_M16))
    pecas.append(test)
    return pecas


def pecas_forma_placa():
    L, H, e = PLACA["comprimento"], PLACA["altura"], PLACA["espessura"]
    n_formas = 3
    pecas = []

    # F-PLA-01 bandeja de fundo: alma 2200 x 700, abas 63 para baixo
    comp = L + 200
    fun = Peca("F-PLA-01", "Fundo da forma da placa", "Placa de saia", 4.75, n_formas,
               comp, [63, H + 200, 63], ["aba", "alma (concreto)", "aba"],
               sentido="as duas abas para baixo, lado oposto a face de concreto",
               obs="Face de concreto = face aparente da placa (lado do rio).")
    yc = fun.largura / 2
    xc = comp / 2
    for dx in (-900, -450, 0, 450, 900):            # trilhos longos
        for s in (-1, 1):
            fun.furos.append((xc + dx, yc + s * (H / 2 + 45), FURO_M16))
    for s in (-1, 1):                                # trilhos curtos
        for dy in (-175, 0, 175):
            fun.furos.append((xc + s * (L / 2 + 45), yc + dy, FURO_M16))
    for s in (-1, 1):                                # tubos-forma dos furos de içamento
        fun.furos.append((xc + s * 600, yc + H / 2 - 100, FURO_FIXADOR))
    fun.furos.append((xc, yc, FURO_FIXADOR))         # tubo-forma do dreno (opcional)
    pecas.append(fun)

    comp_n = (H + 200) - 2 * 4.75 - 2 * DOBRA[4.75]["ri"] - 2 * 2
    pecas.append(Peca("F-PLA-02", "Nervura do fundo da placa (U)", "Placa de saia", 4.75,
                      4 * n_formas, math.floor(comp_n), [63, 40, 63], ["aba", "alma", "aba"],
                      sentido="U: as duas abas para o mesmo lado",
                      obs="4 por fundo, a 275 / 825 / 1375 / 1925 mm."))

    comp_tl = L + 2 * 6.30
    tl = Peca("F-PLA-03", "Trilho longo da placa", "Placa de saia", 6.30, 2 * n_formas,
              round(comp_tl, 1), [e, 75], ["face (concreto)", "pe"],
              sentido="pe para fora, lado oposto ao concreto",
              obs="Espessura da placa ate 150 mm (altura da face).")
    for dx in (-900, -450, 0, 450, 900):
        tl.furos.append((comp_tl / 2 + dx, tl.largura - 30, FURO_M16))
    pecas.append(tl)

    comp_tc = H - 2
    tc = Peca("F-PLA-04", "Trilho curto da placa", "Placa de saia", 6.30, 2 * n_formas,
              comp_tc, [e, 75], ["face (concreto)", "pe"],
              sentido="pe para fora, lado oposto ao concreto",
              obs="Entra entre os trilhos longos.")
    for dy in (-175, 0, 175):
        tc.furos.append((comp_tc / 2 + dy, tc.largura - 30, FURO_M16))
    pecas.append(tc)
    return pecas


# --------------------------------------------------------------------------
# VERIFICAÇÕES AUTOMÁTICAS
# --------------------------------------------------------------------------
def verifica(p):
    """Regras: centro do furo a pelo menos 1,5 diâmetro da borda; borda do furo a pelo
    menos (meia zona de dobra + 2 espessuras) do centro da dobra; dobra de até 3 m."""
    problemas = []
    ba = dados_dobra(p.t)[1] if p.linhas else 0.0

    def checa(x, y, d, nome):
        dist_borda = min(x, p.comprimento - x, y, p.largura - y)
        if dist_borda < 1.5 * d:
            problemas.append(f"{nome} a {dist_borda:.1f} mm da borda (mínimo {1.5 * d:.1f})")
        for yl in p.linhas:
            folga = abs(y - yl) - d / 2
            if folga < ba / 2 + 2 * p.t:
                problemas.append(f"{nome} a {folga:.1f} mm da dobra em y = {yl:.1f}")

    for x, y, d in p.furos:
        checa(x, y, d, "furo")
    for x, y1, y2, wdt in p.rasgos:
        checa(x, y1, wdt, "rasgo")
        checa(x, y2, wdt, "rasgo")
    if p.linhas and p.comprimento > 3000:
        problemas.append(f"dobra de {p.comprimento} mm excede a dobradeira de 3 m")
    return problemas


# --------------------------------------------------------------------------
# SAÍDAS
# --------------------------------------------------------------------------
def novo_doc():
    doc = ezdxf.new("R2000", setup=True)
    doc.units = units.MM
    doc.header["$INSUNITS"] = 4
    doc.header["$MEASUREMENT"] = 1
    for nome, cor, tipo in (("CORTE", 7, "CONTINUOUS"), ("DOBRA", 2, "DASHED"),
                            ("TEXTO", 3, "CONTINUOUS")):
        if nome not in doc.layers:
            doc.layers.add(nome, color=cor, linetype=tipo)
    return doc


def desenha_geometria(msp, p):
    msp.add_lwpolyline([(0, 0), (p.comprimento, 0), (p.comprimento, p.largura),
                        (0, p.largura)], close=True, dxfattribs={"layer": "CORTE"})
    for x, y, d in p.furos:
        msp.add_circle((x, y), d / 2, dxfattribs={"layer": "CORTE"})
    for x, y1, y2, wdt in p.rasgos:
        ya, yb = min(y1, y2), max(y1, y2)
        r = wdt / 2
        msp.add_lwpolyline([(x + r, ya, 0), (x + r, yb, 1), (x - r, yb, 0), (x - r, ya, 1)],
                           format="xyb", close=True, dxfattribs={"layer": "CORTE"})


def grava_dxf(p, pasta):
    doc = novo_doc()
    desenha_geometria(doc.modelspace(), p)
    doc.saveas(os.path.join(pasta, f"{p.codigo}_CORTE.dxf"))

    doc = novo_doc()
    msp = doc.modelspace()
    desenha_geometria(msp, p)
    for i, yl in enumerate(p.linhas, 1):
        msp.add_line((0, yl), (p.comprimento, yl), dxfattribs={"layer": "DOBRA"})
        msp.add_text(f"DOBRA {i} - 90 GRAUS", height=8,
                     dxfattribs={"layer": "TEXTO"}).set_placement((10, yl + 3))
    h = max(10.0, min(30.0, p.largura / 18))
    linhas_txt = [
        f"{p.codigo}  {sem_acento(p.nome).upper()}",
        f"CHAPA {fmt_t(p.t)} MM   QTD {p.qtd}   PLANIFICADA "
        f"{fmt(p.comprimento)} x {fmt(p.largura)} MM",
        f"ABAS EXTERNAS: {' / '.join(fmt(a) for a in p.abas)} MM",
        "CAMADAS DOBRA E TEXTO NAO SAO CORTE",
    ]
    for k, s in enumerate(linhas_txt):
        msp.add_text(s, height=h, dxfattribs={"layer": "TEXTO"}).set_placement(
            (0, -h * 1.8 * (k + 1)))
    doc.saveas(os.path.join(pasta, f"{p.codigo}_DESENHO.dxf"))


def grava_svg(p, pasta):
    m = 20
    vb_w, vb_h = p.comprimento + 2 * m, p.largura + 2 * m
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-m} {-m} {vb_w:.1f} {vb_h:.1f}" '
           f'class="flat" data-codigo="{p.codigo}">']
    # y do DXF cresce para cima; no SVG invertemos para manter a mesma leitura
    def Y(y):
        return p.largura - y
    out.append(f'<rect class="cut" x="0" y="0" width="{p.comprimento:.1f}" '
               f'height="{p.largura:.1f}"/>')
    for yl in p.linhas:
        out.append(f'<line class="bend" x1="0" y1="{Y(yl):.1f}" x2="{p.comprimento:.1f}" '
                   f'y2="{Y(yl):.1f}"/>')
    for x, y, d in p.furos:
        out.append(f'<circle class="hole" cx="{x:.1f}" cy="{Y(y):.1f}" r="{d / 2:.1f}"/>')
    for x, y1, y2, wdt in p.rasgos:
        ya, yb = sorted((Y(y1), Y(y2)))
        out.append(f'<rect class="hole" x="{x - wdt / 2:.1f}" y="{ya - wdt / 2:.1f}" '
                   f'width="{wdt:.1f}" height="{yb - ya + wdt:.1f}" rx="{wdt / 2:.1f}"/>')
    out.append("</svg>")
    with open(os.path.join(pasta, f"{p.codigo}.svg"), "w", encoding="utf-8") as f:
        f.write("\n".join(out))


def fmt(v):
    s = f"{v:.1f}".replace(".", ",")
    return s[:-2] if s.endswith(",0") else s


def fmt_t(t):
    return f"{t:.2f}".replace(".", ",")


def roteiro_de_dobra(p):
    """Para cada dobra: borda de encosto no batente, medida até o centro da dobra e aba
    que resulta do lado do batente. Com uma dobra, encosta a borda mais próxima dela.
    Com duas, a dobra 1 encosta na borda A (y = 0) e a dobra 2 na borda B (y = largura)."""
    if len(p.linhas) == 1:
        yl = p.linhas[0]
        if yl <= p.largura - yl:
            return [(1, "A", yl, p.abas[0])]
        return [(1, "B", p.largura - yl, p.abas[-1])]
    passos = []
    for i, yl in enumerate(p.linhas, 1):
        if i == 1:
            passos.append((i, "A", yl, p.abas[0]))
        else:
            passos.append((i, "B", p.largura - yl, p.abas[-1]))
    return passos


def sem_acento(s):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def main():
    pastas = {k: os.path.join(SAIDA, k) for k in ("dxf", "svg", "tabelas")}
    for pasta in pastas.values():
        os.makedirs(pasta, exist_ok=True)

    pecas = pecas_forma_longarina() + pecas_forma_placa()

    erros = {p.codigo: verifica(p) for p in pecas}
    erros = {k: v for k, v in erros.items() if v}
    if erros:
        for k, v in erros.items():
            print(k, "->", "; ".join(v))
        raise SystemExit("Verificação falhou: corrija os parâmetros antes de gerar.")

    for p in pecas:
        grava_dxf(p, pastas["dxf"])
        grava_svg(p, pastas["svg"])

    with open(os.path.join(pastas["tabelas"], "lista_de_corte.csv"), "w", newline="",
              encoding="utf-8") as f:
        wr = csv.writer(f, delimiter=";")
        wr.writerow(["codigo", "peca", "forma", "chapa_mm", "qtd", "planificada_comprimento_mm",
                     "planificada_largura_mm", "abas_externas_mm", "furos", "rasgos",
                     "peso_unit_kg", "peso_total_kg", "observacao"])
        for p in pecas:
            wr.writerow([p.codigo, p.nome, p.forma, fmt_t(p.t), p.qtd, fmt(p.comprimento),
                         fmt(p.largura), " / ".join(fmt(a) for a in p.abas), len(p.furos),
                         len(p.rasgos), fmt(p.peso), fmt(p.peso * p.qtd), p.obs])

    with open(os.path.join(pastas["tabelas"], "tabela_de_dobras.csv"), "w", newline="",
              encoding="utf-8") as f:
        wr = csv.writer(f, delimiter=";")
        wr.writerow(["codigo", "dobra", "angulo_graus", "borda_de_encosto",
                     "medida_ate_centro_da_dobra_mm", "aba_externa_resultante_mm",
                     "comprimento_da_dobra_mm", "chapa_mm", "raio_interno_mm", "fator_K",
                     "V_matriz_mm", "forca_estimada_tf", "sentido"])
        for p in pecas:
            d = DOBRA[p.t]
            for i, borda, medida, aba in roteiro_de_dobra(p):
                wr.writerow([p.codigo, i, 90, borda, fmt(medida), fmt(aba), fmt(p.comprimento),
                             fmt_t(p.t), fmt(d["ri"]), d["k"], d["v"],
                             fmt(forca_dobra_tf(p.t, p.comprimento)), p.sentido])

    compras = [
        ("Parafuso sextavado M16 x 50 com porca e 2 arruelas (forma da longarina)", 100, "jogo"),
        ("Barra roscada 5/8\" (16 mm) x 600 mm, com 2 porcas e 2 arruelas (tirante superior)",
         4 * VIGA["comprimento"] // VIGA["modulo"], "jogo"),
        ("Parafuso sextavado M16 x 40 com porca e arruela (forma da placa)", 16 * 3, "jogo"),
        ("Tubo-forma de aço ou PVC rígido, D 50 x 150 mm, com tampa e parafuso M12 "
         "(furo de içamento e dreno da placa)", 3 * 3, "un"),
        ("Desmoldante para forma metálica", 1, "conforme consumo"),
        ("Fita ou cordão de vedação para juntas da forma", 1, "conforme consumo"),
    ]
    with open(os.path.join(pastas["tabelas"], "lista_de_compras.csv"), "w", newline="",
              encoding="utf-8") as f:
        wr = csv.writer(f, delimiter=";")
        wr.writerow(["item", "quantidade", "unidade"])
        for linha in compras:
            wr.writerow(linha)

    with open(os.path.join(pastas["tabelas"], "kit_pecas_de_concreto.csv"), "w", newline="",
              encoding="utf-8") as f:
        wr = csv.writer(f, delimiter=";")
        wr.writerow(["codigo", "peca", "dimensoes_m", "volume_unit_m3", "peso_unit_t", "qtd",
                     "volume_total_m3", "forma"])
        for cod, nome, dim, vol, qtd, forma in KIT:
            wr.writerow([cod, nome, dim, f"{vol:.3f}".replace(".", ","),
                         f"{vol * CONCRETO_T_M3:.2f}".replace(".", ","), qtd,
                         f"{vol * qtd:.2f}".replace(".", ","), forma])
            print(f"{cod} {nome[:48]:48s} {vol:6.3f} m3  {vol * CONCRETO_T_M3:5.2f} t  x{qtd}")

    resumo = []
    for forma in sorted({p.forma for p in pecas}):
        ps = [p for p in pecas if p.forma == forma]
        resumo.append((forma, sum(p.peso * p.qtd for p in ps), sum(p.qtd for p in ps)))
    with open(os.path.join(pastas["tabelas"], "resumo.txt"), "w", encoding="utf-8") as f:
        for forma, kg, n in resumo:
            f.write(f"{forma}: {n} peças de chapa, {kg:.0f} kg de aço\n")
        f.write(f"Total: {sum(r[1] for r in resumo):.0f} kg\n")
    for forma, kg, n in resumo:
        print(f"{forma}: {n} peças, {kg:.0f} kg")
    print("Arquivos em", SAIDA)


if __name__ == "__main__":
    main()
