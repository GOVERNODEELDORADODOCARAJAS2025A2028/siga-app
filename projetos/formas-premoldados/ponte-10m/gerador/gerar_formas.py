#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador paramétrico das formas metálicas do kit "Ponte pré-moldada de 10 m".

Gera, para cada peça de chapa das formas:
  saida/dxf/<código>_CORTE.dxf    contorno e furos, sem mais nada (arquivo do plasma)
  saida/dxf/<código>_DESENHO.dxf  contorno, furos, linhas de dobra, marcas e textos
  saida/svg/<código>.svg          pré-visualização da planificação
  saida/tabelas/*.csv             lista de corte, tabela de dobras, compras, kit e resumo

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
import unicodedata
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

# Painel de laje de espessura total. Eixo X ao longo dos 4500 mm (atravessa a ponte),
# eixo Y ao longo da ponte (1230 mm), Z = 0 na face de baixo (a que apoia nas vigas).
PAINEL = dict(
    comprimento=4_500,
    largura=1_230,           # módulo de 1250 mm com junta de 20 mm entre painéis
    modulo=1_250,
    espessura=200,
    vigas_x=(450, 1650, 2850, 4050),   # eixos das longarinas
    nichos_y=(302.5, 927.5),           # centros dos nichos: 312,5 + 625 n ao longo da viga
    nicho_base=(200, 250),             # medidas do nicho na face de baixo (X x Y)
    nicho_topo=(220, 270),             # medidas do nicho na face de cima (X x Y)
    icamento_x=(900, 3600),            # insertos de içamento, nas linhas dos nichos
    nivelamento_y=(120, 1110),         # insertos de nivelamento, sobre cada viga
    chave=dict(rebaixo=25, aba=20, topo=50, z0=30),  # chave fêmea nas bordas de 4500 mm
    # esperas do guarda-rodas (amarradas na armadura; não são peça de forma)
    esperas_guarda_rodas=((200, 307.5), (200, 922.5), (4300, 307.5), (4300, 922.5)),
)
BASE_LAJ = dict(margem_x=90, margem_y=100)   # quanto o fundo passa do concreto

# --------------------------------------------------------------------------
# CHAPA E DOBRA  (PROVISÓRIO: trocar pela tabela do fornecedor)
#   ri = raio interno resultante (mm)   k = fator K   v = abertura do V da matriz (mm)
# --------------------------------------------------------------------------
DOBRA = {
    3.00: dict(ri=3.5, k=0.42, v=20),
    4.75: dict(ri=6.0, k=0.42, v=40),
    6.30: dict(ri=8.0, k=0.42, v=50),
}
ABA_MINIMA_FATOR = 0.7    # aba mínima ~ 0,7 x abertura do V
DENSIDADE_ACO = 7.85e-6   # kg/mm3
FURO_M16 = 18.0           # furo para parafuso M16
FURO_FIXADOR = 14.0       # furo para parafuso M12
RESISTENCIA_ACO = 450     # MPa, resistência à tração de referência (chapa A36/1020)

CONCRETO_T_M3 = 2.5      # massa específica do concreto armado (NBR 6118)


def _volume_painel():
    P = PAINEL
    a1 = P["nicho_base"][0] * P["nicho_base"][1] / 1e6
    a2 = P["nicho_topo"][0] * P["nicho_topo"][1] / 1e6
    h = P["espessura"] / 1000
    nicho = h / 3 * (a1 + a2 + math.sqrt(a1 * a2))
    c = P["chave"]
    rebaixo = (c["rebaixo"] ** 2 + c["topo"] * c["rebaixo"]) / 1e6   # dois chanfros + topo
    bruto = P["comprimento"] * P["largura"] * P["espessura"] / 1e9
    return bruto - 8 * nicho - 2 * (P["comprimento"] / 1000) * rebaixo


# Peças de concreto da ponte (2 vãos de 10 m, largura 4,50 m, cabeceiras de 4,76 m).
# (código, peça, dimensões em m, volume unitário em m3, quantidade, forma)
KIT = [
    ("P-01", "Longarina", "0,30 x 0,90 x 10,00", 0.30 * 0.90 * 10.00, 8, "F-LON"),
    ("P-02", "Painel de laje de espessura total, 8 nichos", "4,50 x 1,23 x 0,20",
     _volume_painel(), 16, "F-LAJ"),
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
def dados_dobra(t, ang=90.0):
    """Recuo externo (OSSB) e comprimento desenvolvido (BA) de uma dobra de 'ang' graus."""
    p = DOBRA[t]
    a = math.radians(ang)
    ossb = (p["ri"] + t) * math.tan(a / 2)
    ba = a * (p["ri"] + p["k"] * t)
    return ossb, ba


def planifica(abas, t, angulos):
    """abas: medidas EXTERNAS dos trechos, em ordem; angulos: ângulo de cada dobra.
    Retorna (largura planificada, centros das linhas de dobra, trechos retos)."""
    n = len(abas)
    dd = [dados_dobra(t, a) for a in angulos]
    retos = []
    for i, a in enumerate(abas):
        r = a
        if i > 0:
            r -= dd[i - 1][0]
        if i < n - 1:
            r -= dd[i][0]
        retos.append(r)
    largura = sum(retos) + sum(ba for _, ba in dd)
    linhas, y = [], 0.0
    for i in range(n - 1):
        y += retos[i]
        linhas.append(y + dd[i][1] / 2)
        y += dd[i][1]
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
    angulos: list = None        # ângulo de cada dobra (padrão 90 graus)
    giros: list = None          # sentido de cada dobra no perfil: +1 ou -1 (padrão +1)
    furos: list = field(default_factory=list)   # (x, y, diâmetro)
    rasgos: list = field(default_factory=list)  # (x, y1, y2, largura): rasgo alinhado em y
    contorno: list = None       # contorno próprio (x, y); se vazio, retângulo
    marcas: list = field(default_factory=list)  # (y, texto): linha de referência, não é corte
    sentido: str = ""
    obs: str = ""

    def __post_init__(self):
        if self.contorno:
            self.largura = max(y for _, y in self.contorno)
            self.linhas, self.retos, self.angulos, self.giros = [], [self.largura], [], []
        elif len(self.abas) > 1:
            self.angulos = self.angulos or [90.0] * (len(self.abas) - 1)
            self.giros = self.giros or [1] * (len(self.abas) - 1)
            self.largura, self.linhas, self.retos = planifica(self.abas, self.t, self.angulos)
        else:
            self.largura, self.linhas, self.retos = self.abas[0], [], [self.abas[0]]
            self.angulos, self.giros = [], []

    def y_na_face(self, i, z):
        """Posição y, na chapa planificada, do ponto que fica a 'z' mm do lado
        externo da aba i-1 medido ao longo da aba i (para marcar soldas)."""
        y = sum(self.retos[:i])
        for k in range(i):
            y += dados_dobra(self.t, self.angulos[k])[1]
        return y + (z - dados_dobra(self.t, self.angulos[i - 1])[0])

    @property
    def area_bruta(self):
        if not self.contorno:
            return self.comprimento * self.largura
        pts = self.contorno
        return abs(sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0]
                       * pts[i][1] for i in range(len(pts)))) / 2

    @property
    def peso(self):
        area = self.area_bruta
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
    meios = [passo_nerv / 2 + passo_nerv * k for k in range(8)]
    x_fix = [meios[0], meios[3], meios[4], meios[7]]   # 156,25 1093,75 1406,25 2343,75

    pecas = []

    # F-LON-01 painel lateral: aba superior 75, face 1000, aba inferior 100
    lat = Peca("F-LON-01", "Painel lateral da longarina", "Longarina", 4.75, 2 * n_mod,
               mod, [75, 1000, 100], ["aba superior", "face (concreto)", "aba inferior (base)"],
               sentido="as duas abas para trás, lado oposto à face de concreto",
               obs="Solda de nervuras, cantoneiras e orelhas pelo lado de trás. "
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
    cant = Peca("F-LON-03", "Cantoneira de ligação do painel", "Longarina", 6.30, 2 * 2 * n_mod,
                math.floor(comp_nerv), [63, 75], ["aba soldada", "aba aparafusada"],
                sentido="uma dobra de 90 graus",
                obs="Uma em cada ponta do painel, aba soldada rente à borda; liga módulos "
                    "entre si e recebe a testeira.")
    furo_cant_z = [87 + 200 * i for i in range(5)]
    for z in furo_cant_z:                # furo a 45 mm da face de concreto
        cant.furos.append((z, cant.largura - (75 - (45 - 4.75)), FURO_M16))
    pecas.append(cant)

    # F-LON-04 orelha do tirante (chapa plana)
    ore = Peca("F-LON-04", "Orelha do tirante superior", "Longarina", 6.30, 4 * 2 * n_mod,
               80, [80], ["chapa plana"],
               obs="Soldar em pé sobre a aba superior, a 40 mm da face de concreto, "
                   "nas posições 156,25 / 1093,75 / 1406,25 / 2343,75 mm.")
    ore.furos.append((40, 40, FURO_M16))
    pecas.append(ore)

    # F-LON-05 fundo: U invertido, alma 640, abas 75 para baixo
    fun = Peca("F-LON-05", "Fundo da longarina (U invertido)", "Longarina", 6.30, n_mod,
               mod, [75, 640, 75], ["aba", "alma (concreto)", "aba"],
               sentido="as duas abas para baixo, lado oposto à face de concreto",
               obs="Rasgos permitem larguras de viga de 250 a 360 mm.")
    yc = fun.largura / 2
    r1, r2 = VIGA_B_MIN / 2 + 60, VIGA_B_MAX / 2 + 60   # 185 a 240 mm do eixo
    for x in x_fix:
        fun.rasgos.append((x, yc + r1, yc + r2, FURO_M16))
        fun.rasgos.append((x, yc - r2, yc - r1, FURO_M16))
    pecas.append(fun)

    # F-LON-06 cantoneira do fundo
    comp_cf = 640 - 2 * 6.30 - 2 * DOBRA[6.30]["ri"] - 2 * 2
    cf = Peca("F-LON-06", "Cantoneira de ligação do fundo", "Longarina", 6.30, 2 * n_mod,
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
                obs="Peça própria de cada largura de viga. Aparafusada nas cantoneiras "
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
               sentido="as duas abas para baixo, lado oposto à face de concreto",
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
              round(comp_tl, 1), [e, 75], ["face (concreto)", "pé"],
              sentido="pé para fora, lado oposto ao concreto",
              obs="Espessura da placa até 150 mm (altura da face).")
    for dx in (-900, -450, 0, 450, 900):
        tl.furos.append((comp_tl / 2 + dx, tl.largura - 30, FURO_M16))
    pecas.append(tl)

    comp_tc = H - 2
    tc = Peca("F-PLA-04", "Trilho curto da placa", "Placa de saia", 6.30, 2 * n_formas,
              comp_tc, [e, 75], ["face (concreto)", "pé"],
              sentido="pé para fora, lado oposto ao concreto",
              obs="Entra entre os trilhos longos.")
    for dy in (-175, 0, 175):
        tc.furos.append((comp_tc / 2 + dy, tc.largura - 30, FURO_M16))
    pecas.append(tc)
    return pecas


def pecas_forma_laje():
    """Forma do painel de laje P-02. O fundo tem 2 módulos iguais: o segundo é o
    primeiro girado 180 graus, por isso todos os furos são simétricos em relação ao
    centro do painel."""
    P = PAINEL
    L, B, e = P["comprimento"], P["largura"], P["espessura"]
    mx, my = BASE_LAJ["margem_x"], BASE_LAJ["margem_y"]
    jx = L / 2                        # junta entre os dois módulos do fundo
    comp_base, larg_base = jx + mx, B + 2 * my            # 2340 x 1430
    t_tr = 4.75                       # chapa dos trilhos
    furos_trilho_x = (150, 600, 1050, 1500, 1950, 2150)   # metade 1 (espelhados na 2)
    furos_ponta_y = (150, 615, 1080)
    furos_junta = (163, 488, 738, 1063)                   # ligação entre módulos
    n_formas = 2
    pecas = []

    def local(X, Y):
        return (round(X + mx, 2), round(Y + my, 2))

    # ---- F-LAJ-01 fundo (chapa plana com furos)
    fun = Peca("F-LAJ-01", "Fundo do painel (módulo)", "Painel de laje", 6.30, 2 * n_formas,
               comp_base, [larg_base], ["chapa plana"],
               obs="Dois módulos iguais por forma; o segundo gira 180 graus. Assentar sobre "
                   "base de concreto nivelada (±2 mm). Soldar porca M12 por baixo dos 4 furos "
                   "de 14 mm.")
    for X in furos_trilho_x:
        for Y in (-45, B + 45):
            fun.furos.append((*local(X, Y), FURO_M16))
    for Y in furos_ponta_y:
        fun.furos.append((*local(-45, Y), FURO_M16))
    for X in P["vigas_x"][:2]:
        for Y in P["nichos_y"]:
            fun.furos.append((*local(X, Y), FURO_FIXADOR))
        for Y in P["nivelamento_y"]:
            fun.furos.append((*local(X, Y), FURO_M16))
    # o módulo 2, girado, precisa cair exatamente nos mesmos furos
    mod2 = []
    for X in furos_trilho_x:
        for Y in (-45, B + 45):
            mod2.append((L - X, Y, FURO_M16))
    for Y in furos_ponta_y:
        mod2.append((L + 45, Y, FURO_M16))
    for X in P["vigas_x"][2:]:
        for Y in P["nichos_y"]:
            mod2.append((X, Y, FURO_FIXADOR))
        for Y in P["nivelamento_y"]:
            mod2.append((X, Y, FURO_M16))
    girado = sorted((round(L + mx - X, 2), round(B + my - Y, 2), d) for X, Y, d in mod2)
    assert girado == sorted(fun.furos), "módulos do fundo do painel não são intercambiáveis"
    pecas.append(fun)

    # ---- F-LAJ-02 cantoneira longitudinal do fundo (sob as bordas de 2340 mm)
    cl = Peca("F-LAJ-02", "Cantoneira longitudinal do fundo", "Painel de laje", 4.75,
              4 * n_formas, comp_base, [63, 100], ["aba vertical (para baixo)",
                                                   "aba sob o fundo"],
              sentido="uma dobra de 90 graus",
              obs="Soldada sob a borda do fundo, aba vertical rente à borda. Os furos "
                  "coincidem com os do fundo: o parafuso do trilho atravessa as duas chapas.")
    for X in furos_trilho_x:
        cl.furos.append((X + mx, cl.largura - (100 - 55), FURO_M16))
    pecas.append(cl)

    # ---- F-LAJ-03 cantoneira de topo do fundo (sob as bordas de 1430 mm)
    comp_ct = larg_base - 2 * my - 4
    ct = Peca("F-LAJ-03", "Cantoneira de topo do fundo", "Painel de laje", 6.30, 4 * n_formas,
              comp_ct, [75, 75], ["aba vertical (ligação entre módulos)", "aba sob o fundo"],
              sentido="uma dobra de 90 graus",
              obs="Uma em cada ponta do módulo, entre as cantoneiras longitudinais. A da junta "
                  "aparafusa na do outro módulo; a da ponta recebe o trilho de ponta.")
    for Y in furos_ponta_y:
        ct.furos.append((Y - 2, ct.largura - (75 - 45), FURO_M16))
    for s in furos_junta:
        ct.furos.append((s, 75 - 45, FURO_M16))
    pecas.append(ct)

    # ---- F-LAJ-04 nervura transversal do fundo
    pecas.append(Peca("F-LAJ-04", "Nervura transversal do fundo (U)", "Painel de laje", 4.75,
                      4 * 2 * n_formas, comp_ct, [63, 40, 63], ["aba", "alma", "aba"],
                      sentido="U: as duas abas para o mesmo lado",
                      obs="4 por módulo, a 468 / 936 / 1404 / 1872 mm da ponta do módulo."))

    # ---- F-LAJ-05 trilho longo (pé 75, face 200, aba superior 75), 2 segmentos por lado
    comp_tl = jx + t_tr
    tl = Peca("F-LAJ-05", "Trilho longo do painel", "Painel de laje", t_tr, 4 * n_formas,
              comp_tl, [75, e, 75], ["pé", "face (concreto)", "aba superior"],
              sentido="pé e aba superior para fora, lado oposto ao concreto",
              obs="4 segmentos iguais por forma (2 por borda). Recebe a régua de chave "
                  "F-LAJ-06 soldada entre as marcas.")
    for X in furos_trilho_x:
        tl.furos.append((X + t_tr, 75 - 45, FURO_M16))
    tl.furos.append((P["icamento_x"][0] + t_tr, tl.largura - (75 - 45), FURO_M16))
    c = P["chave"]
    alt_chave = 2 * c["aba"] + 2 * c["rebaixo"] + c["topo"]          # 140 mm
    tl.marcas.append((tl.y_na_face(1, c["z0"]), "SOLDAR CHAVE A PARTIR DAQUI"))
    tl.marcas.append((tl.y_na_face(1, c["z0"] + alt_chave), "LIMITE DA CHAVE"))
    pecas.append(tl)

    # ---- F-LAJ-06 régua de chave (perfil chapéu, 4 dobras de 45 graus)
    inc = c["rebaixo"] * math.sqrt(2)
    pecas.append(Peca("F-LAJ-06", "Régua de chave fêmea (chapéu)", "Painel de laje", 3.00,
                      4 * n_formas, jx - 1, [c["aba"], inc, c["topo"], inc, c["aba"]],
                      ["aba soldada", "rampa 45°", "topo (25 mm da face)", "rampa 45°",
                       "aba soldada"], angulos=[45.0] * 4, giros=[1, -1, -1, 1],
                      sentido="perfil chapéu: dobras 1 e 4 num sentido, 2 e 3 no sentido "
                              "contrário",
                      obs="Forma o rebaixo de 25 mm na borda do painel (junta fêmea-fêmea). "
                          "Medidas admitem ±2 mm."))

    # ---- F-LAJ-07 trilho de ponta (borda da ponte)
    tp = Peca("F-LAJ-07", "Trilho de ponta do painel", "Painel de laje", t_tr, 2 * n_formas,
              B - 2, [75, e, 75], ["pé", "face (concreto)", "aba superior"],
              sentido="pé e aba superior para fora, lado oposto ao concreto",
              obs="Entra entre os trilhos longos; a régua de chave encosta na face dele.")
    for Y in furos_ponta_y:
        tp.furos.append((Y - 1, 75 - 45, FURO_M16))
    pecas.append(tp)

    # ---- F-LAJ-08/09/10 fôrma de nicho (caixa tronco-piramidal) e travessa
    (bx, by), (tx_, ty) = P["nicho_base"], P["nicho_topo"]
    h = math.hypot(e, (tx_ - bx) / 2)
    def trapezio(b1, b2):
        d = (b2 - b1) / 2
        return [(d, 0), (d + b1, 0), (b2, h), (0, h)]
    pecas.append(Peca("F-LAJ-08", f"Lado de {bx} mm da forma de nicho", "Painel de laje", 4.75,
                      2 * 8 * n_formas, tx_, [h], ["trapézio"], contorno=trapezio(bx, tx_),
                      obs="Base menor apoia no fundo. Os lados de 200 mm cobrem as quinas."))
    b1, b2 = by - 2 * 4.75, ty - 2 * 4.75
    pecas.append(Peca("F-LAJ-09", f"Lado de {by} mm da forma de nicho", "Painel de laje", 4.75,
                      2 * 8 * n_formas, b2, [h], ["trapézio"], contorno=trapezio(b1, b2),
                      obs="Entra entre os lados de 200 mm. Soldar as quinas por dentro e "
                          "esmerilhar por fora."))
    trv = Peca("F-LAJ-10", "Travessa da forma de nicho", "Painel de laje", 6.30, 8 * n_formas,
               260, [50], ["chapa plana"],
               obs="Soldada no topo, por dentro, entre os lados de 200 mm. A barra roscada M12 "
                   "passa no furo e prende a forma na porca soldada sob o fundo.")
    trv.furos.append((130, 25, FURO_FIXADOR))
    pecas.append(trv)

    # ---- F-LAJ-11 régua porta-insertos (gabarito dos insertos de içamento)
    comp_r = round(B + 2 * (t_tr + 75), 1)
    reg = Peca("F-LAJ-11", "Régua porta-insertos de içamento", "Painel de laje", 4.75,
               2 * n_formas, comp_r, [40, 63, 40], ["aba", "alma (apoia nos trilhos)", "aba"],
               sentido="U: as duas abas para cima",
               obs="Atravessa o painel sobre as abas superiores dos trilhos, a 900 e 3600 mm "
                   "da borda da ponte; segura os insertos de içamento na posição.")
    y_alma = reg.largura / 2
    for Y in (-45, P["nichos_y"][0], P["nichos_y"][1], B + 45):
        reg.furos.append((round(Y + t_tr + 75, 2), y_alma, FURO_M16))
    pecas.append(reg)
    return pecas


def todas_as_pecas():
    return pecas_forma_longarina() + pecas_forma_placa() + pecas_forma_laje()


# --------------------------------------------------------------------------
# VERIFICAÇÕES AUTOMÁTICAS
# --------------------------------------------------------------------------
def verifica(p):
    """Regras: centro do furo a pelo menos 1,5 diâmetro da borda; borda do furo a pelo
    menos (meia zona de dobra + 2 espessuras) do centro da dobra; aba de pelo menos
    0,7 vez o V da matriz; dobra de até 3 m."""
    problemas = []
    bas = [dados_dobra(p.t, a)[1] for a in p.angulos]

    def checa(x, y, d, nome):
        dist_borda = min(x, p.comprimento - x, y, p.largura - y)
        if dist_borda < 1.5 * d:
            problemas.append(f"{nome} a {dist_borda:.1f} mm da borda (mínimo {1.5 * d:.1f})")
        for yl, ba in zip(p.linhas, bas):
            folga = abs(y - yl) - d / 2
            if folga < ba / 2 + 2 * p.t:
                problemas.append(f"{nome} a {folga:.1f} mm da dobra em y = {yl:.1f}")

    for x, y, d in p.furos:
        checa(x, y, d, "furo")
    for x, y1, y2, wdt in p.rasgos:
        checa(x, y1, wdt, "rasgo")
        checa(x, y2, wdt, "rasgo")
    if p.linhas:
        if p.comprimento > 3000:
            problemas.append(f"dobra de {p.comprimento} mm excede a dobradeira de 3 m")
        minimo = ABA_MINIMA_FATOR * DOBRA[p.t]["v"]
        for a in p.abas:
            if a < minimo:
                problemas.append(f"aba de {a:.1f} mm menor que o mínimo de {minimo:.1f} mm "
                                 f"para V{DOBRA[p.t]['v']}")
    return problemas


def roteiro_de_dobra(p):
    """Para cada dobra: distâncias às bordas A (y = 0) e B (y = largura), borda de
    encosto sugerida (a mais próxima) e a aba que resulta do lado do encosto."""
    passos = []
    n = len(p.linhas)
    for i, yl in enumerate(p.linhas):
        da, db = yl, p.largura - yl
        borda = "A" if da <= db else "B"
        aba = ""
        if borda == "A" and i == 0:
            aba = p.abas[0]
        if borda == "B" and i == n - 1:
            aba = p.abas[-1]
        passos.append(dict(n=i + 1, ang=p.angulos[i], da=da, db=db, borda=borda, aba=aba))
    return passos


# --------------------------------------------------------------------------
# SAÍDAS
# --------------------------------------------------------------------------
def novo_doc():
    doc = ezdxf.new("R2000", setup=True)
    doc.units = units.MM
    doc.header["$INSUNITS"] = 4
    doc.header["$MEASUREMENT"] = 1
    for nome, cor, tipo in (("CORTE", 7, "CONTINUOUS"), ("DOBRA", 2, "DASHED"),
                            ("MARCA", 4, "DASHED"), ("TEXTO", 3, "CONTINUOUS")):
        if nome not in doc.layers:
            doc.layers.add(nome, color=cor, linetype=tipo)
    return doc


def contorno_de(p):
    if p.contorno:
        return p.contorno
    return [(0, 0), (p.comprimento, 0), (p.comprimento, p.largura), (0, p.largura)]


def desenha_geometria(msp, p):
    msp.add_lwpolyline(contorno_de(p), close=True, dxfattribs={"layer": "CORTE"})
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
    for i, (yl, ang) in enumerate(zip(p.linhas, p.angulos), 1):
        msp.add_line((0, yl), (p.comprimento, yl), dxfattribs={"layer": "DOBRA"})
        msp.add_text(f"DOBRA {i} - {fmt(ang)} GRAUS", height=max(4.0, min(8.0, p.largura / 20)),
                     dxfattribs={"layer": "TEXTO"}).set_placement((10, yl + 2))
    for ym, texto in p.marcas:
        msp.add_line((0, ym), (p.comprimento, ym), dxfattribs={"layer": "MARCA"})
        msp.add_text(texto, height=6, dxfattribs={"layer": "TEXTO"}).set_placement(
            (p.comprimento * 0.6, ym + 2))
    h = max(6.0, min(30.0, max(p.comprimento, p.largura) / 40))
    linhas_txt = [
        f"{p.codigo}  {sem_acento(p.nome).upper()}",
        f"CHAPA {fmt_t(p.t)} MM   QTD {p.qtd}   PLANIFICADA "
        f"{fmt(p.comprimento)} x {fmt(p.largura)} MM",
        f"ABAS EXTERNAS: {' / '.join(fmt(a) for a in p.abas)} MM",
        "CAMADAS DOBRA, MARCA E TEXTO NAO SAO CORTE",
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
    pts = " ".join(f"{x:.1f},{Y(y):.1f}" for x, y in contorno_de(p))
    out.append(f'<polygon class="cut" points="{pts}"/>')
    for yl in p.linhas:
        out.append(f'<line class="bend" x1="0" y1="{Y(yl):.1f}" x2="{p.comprimento:.1f}" '
                   f'y2="{Y(yl):.1f}"/>')
    for ym, _ in p.marcas:
        out.append(f'<line class="mark" x1="0" y1="{Y(ym):.1f}" x2="{p.comprimento:.1f}" '
                   f'y2="{Y(ym):.1f}"/>')
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


def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def lista_de_compras():
    n_lon_mod = VIGA["comprimento"] // VIGA["modulo"]
    return [
        ("Parafuso sextavado M16 x 50 com porca e 2 arruelas (forma da longarina)", 100, "jogo"),
        ("Barra roscada 5/8\" (16 mm) x 600 mm, com 2 porcas e 2 arruelas (tirante superior "
         "da longarina)", 4 * n_lon_mod, "jogo"),
        ("Parafuso sextavado M16 x 40 com porca e arruela (forma da placa)", 16 * 3, "jogo"),
        ("Tubo-forma de aço ou PVC rígido, D 50 x 150 mm, com tampa e parafuso M12 "
         "(furo de içamento e dreno da placa)", 3 * 3, "un"),
        ("Parafuso sextavado M16 x 40 com porca e arruela (forma do painel)", 40 * 2, "jogo"),
        ("Barra roscada M12 x 250 mm com porca e arruela (prende a fôrma de nicho)", 8 * 2, "jogo"),
        ("Porca M12 para soldar sob o fundo do painel", 8 * 2, "un"),
        ("Inserto roscado M16 de nivelamento, deixado no painel (8 por painel, 16 painéis)",
         8 * 16, "un"),
        ("Inserto de içamento especificado pelo engenheiro (4 por painel, 16 painéis)",
         4 * 16, "un"),
        ("Gaxeta de espuma para a base da fôrma de nicho", 1, "conforme consumo"),
        ("Desmoldante para forma metálica", 1, "conforme consumo"),
        ("Fita ou cordão de vedação para juntas da forma", 1, "conforme consumo"),
    ]


def main():
    pastas = {k: os.path.join(SAIDA, k) for k in ("dxf", "svg", "tabelas")}
    for pasta in pastas.values():
        os.makedirs(pasta, exist_ok=True)

    pecas = todas_as_pecas()

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
        wr.writerow(["codigo", "dobra", "angulo_graus", "distancia_da_borda_A_mm",
                     "distancia_da_borda_B_mm", "encosto_sugerido", "aba_do_lado_do_encosto_mm",
                     "comprimento_da_dobra_mm", "chapa_mm", "raio_interno_mm", "fator_K",
                     "V_matriz_mm", "forca_estimada_tf", "sentido"])
        for p in pecas:
            d = DOBRA[p.t]
            for r in roteiro_de_dobra(p):
                wr.writerow([p.codigo, r["n"], fmt(r["ang"]), fmt(r["da"]), fmt(r["db"]),
                             r["borda"], fmt(r["aba"]) if r["aba"] != "" else "",
                             fmt(p.comprimento), fmt_t(p.t), fmt(d["ri"]), d["k"], d["v"],
                             fmt(forca_dobra_tf(p.t, p.comprimento)), p.sentido])

    with open(os.path.join(pastas["tabelas"], "lista_de_compras.csv"), "w", newline="",
              encoding="utf-8") as f:
        wr = csv.writer(f, delimiter=";")
        wr.writerow(["item", "quantidade", "unidade"])
        for linha in lista_de_compras():
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

    resumo = []
    for forma in dict.fromkeys(p.forma for p in pecas):
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
