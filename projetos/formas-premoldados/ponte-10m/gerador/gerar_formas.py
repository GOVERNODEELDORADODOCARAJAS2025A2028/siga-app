#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador paramétrico das formas metálicas do kit "Ponte pré-moldada de 10 m".

Gera, para cada peça de chapa das formas:
  saida/dxf/<código>_CORTE.dxf            contorno e furos, sem mais nada (arquivo do laser)
  saida/dxf/<código>_CORTE_E_GRAVACAO.dxf corte e linhas de gravação a laser (posição de
                                          soldas), em camadas separadas; só nas peças gravadas
  saida/dxf/<código>_DESENHO.dxf          contorno, furos, linhas de dobra, gravação e textos
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

# Ponte de vão único de 10 m: quantidades de elementos e de fôrmas
N_LONGARINAS = 4          # 4 linhas de longarina a cada 1,20 m
N_PAINEIS = 8             # 10,00 m de tabuleiro em módulos de 1,25 m
FORMAS_PLACA = 3          # 24 placas de saia em 8 ciclos de concretagem
FORMAS_PAINEL = 1         # 8 painéis em 8 ciclos de concretagem

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
# Dobradeira do fornecedor (3 m). Preencher a capacidade quando chegar a plaqueta; o
# gerador passa a recusar dobra que exija mais que 'uso_maximo' da capacidade.
DOBRADEIRA = dict(capacidade_tf=None, uso_maximo=0.85, comprimento_util=3000)
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


# Peças de concreto da ponte (vão único de 10 m, largura 4,50 m, cabeceiras de 4,76 m).
# (código, peça, dimensões em m, volume unitário em m3, quantidade, forma)
KIT = [
    ("P-01", "Longarina", "0,30 x 0,90 x 10,00", 0.30 * 0.90 * 10.00, N_LONGARINAS, "F-LON"),
    ("P-02", "Painel de laje de espessura total, com 8 nichos", "4,50 x 1,23 x 0,20",
     _volume_painel(), N_PAINEIS, "F-LAJ"),
    ("P-03", "Guarda-rodas, módulo de 2,50 m (seção a definir; área de referência 0,20 m²)",
     "2,50 de comprimento", 0.20 * 2.50, 8, "F-GUA"),
    ("P-04", "Travessa das cabeceiras", "4,64 x 0,90 x 0,60", 4.64 * 0.90 * 0.60, 2, "F-TRA"),
    ("P-05", "Pilar de cabeceira com ranhura", "0,30 x 0,70 x 4,10",
     0.30 * 0.70 * 4.10 - 1.5 * 0.18 * 0.08 * 3.00, 6, "F-PIL"),
    ("P-07", "Placa de saia", "2,00 x 0,50 x 0,15", 2.00 * 0.50 * 0.15, 24, "F-PLA"),
    ("P-08", "Cortina, 2 painéis por cabeceira", "2,32 x 1,16 x 0,25",
     2.32 * 1.16 * 0.25, 4, "F-COR"),
    # segmento de 1,68 m: calcanhar 1,60 x 0,50 + bloco do cálice 1,20 x 1,30 + ponta
    # 0,40 x 0,50 (seção no sentido do eixo), menos o cálice de 0,40 x 0,80 x 1,10
    ("P-09", "Sapata em segmento, com cálice (dimensões após sondagem)",
     "1,68 x 3,20 x 1,30 (referência)",
     1.68 * (1.60 * 0.50 + 1.20 * 1.30 + 0.40 * 0.50) - 0.40 * 0.80 * 1.10, 6, "F-SAP"),
    ("P-10", "Laje de transição", "1,55 x 3,00 x 0,25", 1.55 * 3.00 * 0.25, 6, "F-LTR"),
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


def forca_dobra_tf(t, comprimento, v=None):
    """Estimativa de força de dobra no ar: F = 1,42 x Rm x t² x L / V (Rm = 450 MPa dá o
    coeficiente usual de 650 kN, com t e V em mm e L em m)."""
    v = v or DOBRA[t]["v"]
    kn = 650 * t ** 2 * (comprimento / 1000) / v * (RESISTENCIA_ACO / 450)
    return kn / 9.81


MATRIZES_V = (16, 20, 25, 32, 40, 50, 63, 80, 100)   # série usual de aberturas de matriz


def matriz_para_capacidade(p, capacidade_tf):
    """Menor abertura de V da série, a partir da adotada, que mantém a força de dobra dentro
    do uso admitido da dobradeira e respeita a aba mínima. None se nenhuma atende."""
    limite = capacidade_tf * DOBRADEIRA["uso_maximo"]
    for v in MATRIZES_V:
        if v < DOBRA[p.t]["v"]:
            continue
        if min(p.abas) < ABA_MINIMA_FATOR * v:
            return None
        if forca_dobra_tf(p.t, p.comprimento, v) <= limite:
            return v
    return None


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
    marcas: list = field(default_factory=list)  # (x1, y1, x2, y2): linha só para gravar
    lado_marca: str = ""        # em que face da chapa a marca é gravada
    face_concreto: str = ""     # face em contato com o concreto, referida à face superior
                                # no corte: "superior", "inferior" ou "" (sem contato)
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
    lat = Peca("F-LON-01", "Painel lateral da fôrma da longarina", "Longarina", 4.75, 2 * n_mod,
               mod, [75, 1000, 100], ["aba superior", "face de concreto", "aba de base"],
               sentido="abas superior e de base voltadas para a face posterior",
               obs="Nervuras, cantoneiras e orelhas soldadas somente na face posterior. Face de "
                   "concreto isenta de solda e de respingo.")
    w = lat.largura
    for x in x_fix:                      # furos da base: 60 mm da face de concreto
        lat.furos.append((x, w - (100 - 60), FURO_M16))
    y1, y2 = lat.linhas[0] + 15, lat.linhas[1] - 15
    for i in range(1, 8):                # eixo das 7 nervuras
        lat.marcas.append((passo_nerv * i, y1, passo_nerv * i, y2))
    lat.lado_marca = "face posterior (lado interno das dobras)"
    lat.face_concreto = "inferior"
    pecas.append(lat)

    # F-LON-02 nervura vertical do painel: U 63-40-63, entre as abas
    comp_nerv = 1000 - 2 * 4.75 - 2 * DOBRA[4.75]["ri"] - 2 * 2
    pecas.append(Peca("F-LON-02", "Nervura vertical do painel lateral, perfil U", "Longarina",
                      4.75, 7 * 2 * n_mod, math.floor(comp_nerv), [63, 40, 63],
                      ["aba", "alma", "aba"],
                      sentido="perfil U, abas para o mesmo lado",
                      obs="Sete por painel, com eixos a cada 312,5 mm, soldadas pelas bordas das "
                          "abas na face posterior do painel."))

    # F-LON-03 cantoneira de ligação do painel: 63 (soldada) x 75 (aparafusada)
    cant = Peca("F-LON-03", "Cantoneira de ligação do painel lateral", "Longarina", 6.30,
                2 * 2 * n_mod, math.floor(comp_nerv), [63, 75], ["aba soldada", "aba aparafusada"],
                sentido="dobra única de 90 graus",
                obs="Uma em cada extremidade do painel, com a aba soldada rente à borda. Faz a "
                    "ligação entre módulos e recebe a testeira.")
    furo_cant_z = [87 + 200 * i for i in range(5)]
    for z in furo_cant_z:                # furo a 45 mm da face de concreto
        cant.furos.append((z, cant.largura - (75 - (45 - 4.75)), FURO_M16))
    pecas.append(cant)

    # F-LON-04 orelha do tirante (chapa plana)
    ore = Peca("F-LON-04", "Orelha de fixação do tirante superior", "Longarina", 6.30,
               4 * 2 * n_mod, 80, [80], ["chapa plana"],
               obs="Soldada perpendicularmente à aba superior do painel, a 40 mm da face de "
                   "concreto, nas posições 156,25, 1093,75, 1406,25 e 2343,75 mm.")
    ore.furos.append((40, 40, FURO_M16))
    pecas.append(ore)

    # F-LON-05 fundo: U invertido, alma 640, abas 75 para baixo
    fun = Peca("F-LON-05", "Fundo da fôrma da longarina, perfil U invertido", "Longarina",
               6.30, n_mod, mod, [75, 640, 75], ["aba", "alma (face de concreto)", "aba"],
               sentido="abas voltadas para baixo, lado oposto à face de concreto",
               obs="Os rasgos admitem larguras de viga de 250 mm a 360 mm.")
    yc = fun.largura / 2
    r1, r2 = VIGA_B_MIN / 2 + 60, VIGA_B_MAX / 2 + 60   # 185 a 240 mm do eixo
    for x in x_fix:
        fun.rasgos.append((x, yc + r1, yc + r2, FURO_M16))
        fun.rasgos.append((x, yc - r2, yc - r1, FURO_M16))
    for x in (500, 1000, 1500, 2000):    # eixo das nervuras transversais
        fun.marcas.append((x, fun.linhas[0] + 15, x, fun.linhas[1] - 15))
    fun.lado_marca = "face inferior (lado interno das dobras)"
    fun.face_concreto = "inferior"
    pecas.append(fun)

    # F-LON-06 cantoneira do fundo
    comp_cf = 640 - 2 * 6.30 - 2 * DOBRA[6.30]["ri"] - 2 * 2
    cf = Peca("F-LON-06", "Cantoneira de ligação do fundo", "Longarina", 6.30, 2 * n_mod,
              math.floor(comp_cf), [63, 75], ["aba soldada", "aba aparafusada"],
              sentido="dobra única de 90 graus",
              obs="Uma em cada extremidade do fundo, soldada sob a alma.")
    meio = math.floor(comp_cf) / 2
    for dx in (-200, 0, 200):
        cf.furos.append((meio + dx, cf.largura - (75 - 40), FURO_M16))
    pecas.append(cf)

    # F-LON-07 nervura transversal do fundo
    pecas.append(Peca("F-LON-07", "Nervura transversal do fundo, perfil U", "Longarina", 4.75,
                      4 * n_mod, math.floor(comp_cf), [63, 40, 63], ["aba", "alma", "aba"],
                      sentido="perfil U, abas para o mesmo lado",
                      obs="Quatro por fundo, com eixos a 500, 1000, 1500 e 2000 mm."))

    # F-LON-08 testeira: face 1000 + aba superior 63; largura = b + 2 x 79,75
    larg_test = b + 2 * (4.75 + 75)
    test = Peca("F-LON-08", f"Testeira da fôrma da longarina, viga de {b} mm", "Longarina",
                6.30, 2, larg_test, [1000, 63], ["face de concreto", "aba superior"],
                sentido="aba superior voltada para fora, lado oposto ao concreto",
                obs="Peça específica de cada largura de viga, aparafusada nas cantoneiras "
                    "F-LON-03 dos dois painéis laterais.")
    test.face_concreto = "inferior"
    z0 = 4.75 + DOBRA[4.75]["ri"] + 2          # inicio da cantoneira acima do fundo
    for z in furo_cant_z:
        for x in (larg_test / 2 - (b / 2 + 45), larg_test / 2 + (b / 2 + 45)):
            test.furos.append((x, z0 + z, FURO_M16))
    pecas.append(test)
    return pecas


def pecas_forma_placa():
    L, H, e = PLACA["comprimento"], PLACA["altura"], PLACA["espessura"]
    n_formas = FORMAS_PLACA
    pecas = []

    # F-PLA-01 bandeja de fundo: alma 2200 x 700, abas 63 para baixo
    comp = L + 200
    fun = Peca("F-PLA-01", "Fundo da fôrma da placa de saia", "Placa de saia", 4.75, n_formas,
               comp, [63, H + 200, 63], ["aba", "alma (face de concreto)", "aba"],
               sentido="abas voltadas para baixo, lado oposto à face de concreto",
               obs="A face de concreto molda a face aparente da placa, voltada para o curso "
                   "d'água.")
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
    for x in (275, 825, 1375, 1925):                 # eixo das nervuras
        fun.marcas.append((x, fun.linhas[0] + 15, x, fun.linhas[1] - 15))
    fun.lado_marca = "face inferior (lado interno das dobras)"
    fun.face_concreto = "inferior"
    pecas.append(fun)

    comp_n = (H + 200) - 2 * 4.75 - 2 * DOBRA[4.75]["ri"] - 2 * 2
    pecas.append(Peca("F-PLA-02", "Nervura do fundo da fôrma da placa, perfil U",
                      "Placa de saia", 4.75, 4 * n_formas, math.floor(comp_n), [63, 40, 63],
                      ["aba", "alma", "aba"], sentido="perfil U, abas para o mesmo lado",
                      obs="Quatro por fundo, com eixos a 275, 825, 1375 e 1925 mm."))

    comp_tl = L + 2 * 6.30
    tl = Peca("F-PLA-03", "Trilho longitudinal da fôrma da placa", "Placa de saia", 6.30,
              2 * n_formas, round(comp_tl, 1), [e, 75], ["face de concreto", "aba de apoio"],
              sentido="aba de apoio voltada para fora, lado oposto ao concreto",
              obs="Altura da face igual à espessura da placa, 150 mm.")
    for dx in (-900, -450, 0, 450, 900):
        tl.furos.append((comp_tl / 2 + dx, tl.largura - 30, FURO_M16))
    tl.face_concreto = "inferior"
    pecas.append(tl)

    comp_tc = H - 2
    tc = Peca("F-PLA-04", "Trilho transversal da fôrma da placa", "Placa de saia", 6.30,
              2 * n_formas, comp_tc, [e, 75], ["face de concreto", "aba de apoio"],
              sentido="aba de apoio voltada para fora, lado oposto ao concreto",
              obs="Montado entre os trilhos longitudinais.")
    for dy in (-175, 0, 175):
        tc.furos.append((comp_tc / 2 + dy, tc.largura - 30, FURO_M16))
    tc.face_concreto = "inferior"
    pecas.append(tc)
    return pecas


def pecas_forma_laje():
    """Forma do painel de laje P-02. O fundo tem 2 módulos iguais: o segundo é o
    primeiro girado 180 graus, por isso todos os furos são simétricos em relação ao
    centro do painel. A furação dos trilhos longos é simétrica em relação ao meio do
    módulo, para que trilhos e cantoneiras sirvam em qualquer posição sem peça espelhada."""
    P = PAINEL
    L, B, e = P["comprimento"], P["largura"], P["espessura"]
    mx, my = BASE_LAJ["margem_x"], BASE_LAJ["margem_y"]
    jx = L / 2                        # junta entre os dois módulos do fundo
    comp_base, larg_base = jx + mx, B + 2 * my            # 2340 x 1430
    t_tr = 4.75                       # chapa dos trilhos
    furos_trilho_x = (60, 480, 900, 1260, 1680, 2100)     # metade 1 (girados na 2)
    centro = (jx - mx) / 2                                # meio do módulo, X = 1080
    assert all(round(2 * centro - X, 6) in furos_trilho_x for X in furos_trilho_x), \
        "furação do trilho longo deve ser simétrica em relação ao meio do módulo"
    assert P["icamento_x"][0] in furos_trilho_x and L - P["icamento_x"][1] in furos_trilho_x, \
        "a régua porta-insertos precisa de furo no trilho longo"
    furos_ponta_y = (150, 615, 1080)
    furos_junta = (163, 488, 738, 1063)                   # ligação entre módulos
    n_formas = FORMAS_PAINEL
    pecas = []

    def local(X, Y):
        return (round(X + mx, 2), round(Y + my, 2))

    # ---- F-LAJ-01 fundo (chapa plana com furos)
    fun = Peca("F-LAJ-01", "Módulo do fundo da fôrma do painel", "Painel de laje", 6.30,
               2 * n_formas, comp_base, [larg_base], ["chapa plana"],
               obs="Dois módulos iguais por fôrma; o segundo é montado girado 180 graus. "
                   "Assentar sobre base de concreto nivelada, com tolerância de 2 mm. Soldar "
                   "porca M12 sob cada um dos 4 furos de 14 mm.")
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
    for x in (468, 936, 1404, 1872):                 # eixo das nervuras, entre as cantoneiras
        fun.marcas.append((x, my + 2, x, larg_base - my - 2))
    fun.lado_marca = "face inferior, oposta ao concreto (chapa simétrica)"
    pecas.append(fun)

    # ---- F-LAJ-02 cantoneira longitudinal do fundo (sob as bordas de 2340 mm)
    cl = Peca("F-LAJ-02", "Cantoneira longitudinal do fundo", "Painel de laje", 4.75,
              4 * n_formas, comp_base, [63, 100], ["aba vertical", "aba sob o fundo"],
              sentido="dobra única de 90 graus",
              obs="Soldada sob a borda longitudinal do fundo, com a aba vertical rente à borda. "
                  "Furos coincidentes com os do fundo e com os do trilho longitudinal.")
    for X in furos_trilho_x:
        cl.furos.append((X + mx, cl.largura - (100 - 55), FURO_M16))
    pecas.append(cl)

    # ---- F-LAJ-03 cantoneira de topo do fundo (sob as bordas de 1430 mm)
    comp_ct = larg_base - 2 * my - 4
    ct = Peca("F-LAJ-03", "Cantoneira de extremidade do fundo", "Painel de laje", 6.30,
              4 * n_formas, comp_ct, [75, 75], ["aba vertical", "aba sob o fundo"],
              sentido="dobra única de 90 graus",
              obs="Uma em cada extremidade do módulo, entre as cantoneiras longitudinais. A da "
                  "junta é aparafusada na do módulo adjacente; a da extremidade recebe o trilho "
                  "de extremidade.")
    for Y in furos_ponta_y:
        ct.furos.append((Y - 2, ct.largura - (75 - 45), FURO_M16))
    for s in furos_junta:
        ct.furos.append((s, 75 - 45, FURO_M16))
    pecas.append(ct)

    # ---- F-LAJ-04 nervura transversal do fundo
    pecas.append(Peca("F-LAJ-04", "Nervura transversal do fundo, perfil U", "Painel de laje",
                      4.75, 4 * 2 * n_formas, comp_ct, [63, 40, 63], ["aba", "alma", "aba"],
                      sentido="perfil U, abas para o mesmo lado",
                      obs="Quatro por módulo, com eixos a 468, 936, 1404 e 1872 mm da extremidade "
                          "do módulo."))

    # ---- F-LAJ-05 trilho longo (pé 75, face 200, aba superior 75), 2 segmentos por borda.
    # Vai da borda do fundo (X = -90) até a junta dos módulos; furos iguais no pé e na aba
    # superior, simétricos no comprimento: a mesma peça serve nas 4 posições, virada ou girada.
    comp_tl = jx + mx
    tl = Peca("F-LAJ-05", "Trilho longitudinal da fôrma do painel", "Painel de laje", t_tr,
              4 * n_formas, comp_tl, [75, e, 75], ["aba de apoio", "face de concreto",
                                                  "aba superior"],
              giros=[-1, -1],
              sentido="abas voltadas para fora, lado oposto ao concreto; face gravada no lado "
                      "externo das dobras",
              obs="Quatro por fôrma, todos iguais: a furação simétrica permite usar a peça nas "
                  "quatro posições. A régua F-LAJ-06 é soldada na face de concreto, entre as "
                  "linhas gravadas.")
    for X in furos_trilho_x:
        tl.furos.append((X + mx, 75 - 45, FURO_M16))
        tl.furos.append((X + mx, tl.largura - (75 - 45), FURO_M16))
    c = P["chave"]
    alt_chave = 2 * c["aba"] + 2 * c["rebaixo"] + c["topo"]          # 140 mm
    assert c["z0"] * 2 + alt_chave == e, "régua de chave deve ficar centrada na face"
    for z in (c["z0"], c["z0"] + alt_chave):         # faixa onde a régua de chave é soldada
        ym = tl.y_na_face(1, z)
        tl.marcas.append((mx, ym, mx + jx - 1, ym))
    tl.lado_marca = "face de concreto (lado externo das dobras)"
    tl.face_concreto = "superior"
    pecas.append(tl)

    # ---- F-LAJ-06 régua de chave (perfil chapéu, 4 dobras de 45 graus)
    inc = c["rebaixo"] * math.sqrt(2)
    pecas.append(Peca("F-LAJ-06", "Régua da chave de cisalhamento, perfil cartola",
                      "Painel de laje", 3.00, 4 * n_formas, jx - 1,
                      [c["aba"], inc, c["topo"], inc, c["aba"]],
                      ["aba soldada", "rampa", "topo", "rampa", "aba soldada"],
                      angulos=[45.0] * 4, giros=[1, -1, -1, 1],
                      sentido="perfil cartola: dobras 1 e 4 em um sentido, 2 e 3 no sentido "
                              "oposto",
                      obs="Molda o rebaixo de 25 mm da borda do painel (junta fêmea-fêmea). "
                          "Tolerância de 2 mm nas medidas do perfil.",
                      face_concreto="superior"))

    # ---- F-LAJ-07 trilho de ponta (borda da ponte)
    tp = Peca("F-LAJ-07", "Trilho de extremidade da fôrma do painel", "Painel de laje", t_tr,
              2 * n_formas, B - 2, [75, e, 75], ["aba de apoio", "face de concreto",
                                                 "aba superior"],
              sentido="abas voltadas para fora, lado oposto ao concreto",
              obs="Montado entre os trilhos longitudinais; as réguas de chave terminam na "
                  "face deste trilho.")
    for Y in furos_ponta_y:
        tp.furos.append((Y - 1, 75 - 45, FURO_M16))
    tp.face_concreto = "inferior"
    pecas.append(tp)

    # ---- F-LAJ-08/09/10 fôrma de nicho (caixa tronco-piramidal) e travessa
    (bx, by), (tx_, ty) = P["nicho_base"], P["nicho_topo"]
    h = math.hypot(e, (tx_ - bx) / 2)
    def trapezio(b1, b2):
        d = (b2 - b1) / 2
        return [(d, 0), (d + b1, 0), (b2, h), (0, h)]
    pecas.append(Peca("F-LAJ-08", f"Face de {bx} mm da fôrma do nicho", "Painel de laje",
                      4.75, 2 * 8 * n_formas, tx_, [h], ["trapézio"], contorno=trapezio(bx, tx_),
                      obs=f"Base menor apoiada no fundo. As faces de {bx} mm cobrem as arestas "
                          f"da fôrma."))
    b1, b2 = by - 2 * 4.75, ty - 2 * 4.75
    pecas.append(Peca("F-LAJ-09", f"Face de {by} mm da fôrma do nicho", "Painel de laje",
                      4.75, 2 * 8 * n_formas, b2, [h], ["trapézio"], contorno=trapezio(b1, b2),
                      obs=f"Montada entre as faces de {bx} mm. Arestas soldadas pelo lado interno "
                          f"e esmerilhadas pelo lado externo."))
    trv = Peca("F-LAJ-10", "Travessa de fixação da fôrma do nicho", "Painel de laje", 6.30,
               8 * n_formas, 260, [50], ["chapa plana"],
               obs=f"Soldada no topo, pelo lado interno, entre as faces de {bx} mm. A barra "
                   f"roscada M12 passa pelo furo e fixa a fôrma na porca soldada sob o fundo.")
    trv.furos.append((130, 25, FURO_FIXADOR))
    pecas.append(trv)

    # ---- F-LAJ-11 régua porta-insertos (gabarito dos insertos de içamento)
    comp_r = round(B + 2 * (t_tr + 75), 1)
    reg = Peca("F-LAJ-11", "Régua de posicionamento dos insertos de içamento",
               "Painel de laje", 4.75, 2 * n_formas, comp_r, [40, 63, 40],
               ["aba", "alma", "aba"], sentido="perfil U, abas voltadas para cima",
               obs="Apoiada sobre as abas superiores dos trilhos longitudinais, a 900 mm e a "
                   "3600 mm da borda da ponte; mantém os insertos de içamento na posição de "
                   "projeto.")
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
        if p.comprimento > DOBRADEIRA["comprimento_util"]:
            problemas.append(f"dobra de {p.comprimento} mm excede a dobradeira de 3 m")
        cap = DOBRADEIRA["capacidade_tf"]
        if cap:
            f = forca_dobra_tf(p.t, p.comprimento)
            if f > cap * DOBRADEIRA["uso_maximo"]:
                problemas.append(f"dobra pede {f:.0f} tf; a dobradeira de {cap} t admite "
                                 f"{cap * DOBRADEIRA['uso_maximo']:.0f} tf: aumentar o V")
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
                            ("GRAVACAO", 4, "DASHED"), ("TEXTO", 3, "CONTINUOUS")):
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

    if p.marcas:
        # corte e gravação no mesmo arquivo, em camadas separadas (o operador atribui a
        # camada GRAVACAO ao processo de marcação no software do laser)
        doc = ezdxf.new("R2000", setup=True)
        doc.units = units.MM
        doc.header["$INSUNITS"] = 4
        doc.header["$MEASUREMENT"] = 1
        doc.layers.add("CORTE", color=7)
        doc.layers.add("GRAVACAO", color=3)
        msp = doc.modelspace()
        msp.add_lwpolyline(contorno_de(p), close=True, dxfattribs={"layer": "CORTE"})
        for x, y, d in p.furos:
            msp.add_circle((x, y), d / 2, dxfattribs={"layer": "CORTE"})
        for x, y1, y2, wdt in p.rasgos:
            ya, yb, r = min(y1, y2), max(y1, y2), wdt / 2
            msp.add_lwpolyline([(x + r, ya, 0), (x + r, yb, 1), (x - r, yb, 0), (x - r, ya, 1)],
                               format="xyb", close=True, dxfattribs={"layer": "CORTE"})
        for x1, y1, x2, y2 in p.marcas:
            msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": "GRAVACAO"})
        doc.saveas(os.path.join(pasta, f"{p.codigo}_CORTE_E_GRAVACAO.dxf"))

    doc = novo_doc()
    msp = doc.modelspace()
    desenha_geometria(msp, p)
    for i, (yl, ang) in enumerate(zip(p.linhas, p.angulos), 1):
        msp.add_line((0, yl), (p.comprimento, yl), dxfattribs={"layer": "DOBRA"})
        msp.add_text(f"DOBRA {i} - {fmt(ang)} GRAUS", height=max(4.0, min(8.0, p.largura / 20)),
                     dxfattribs={"layer": "TEXTO"}).set_placement((10, yl + 2))
    for x1, y1, x2, y2 in p.marcas:
        msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": "GRAVACAO"})
    h = max(6.0, min(30.0, max(p.comprimento, p.largura) / 40))
    linhas_txt = [
        f"{p.codigo}  {sem_acento(p.nome).upper()}",
        f"CHAPA {fmt_t(p.t)} MM   QTD {p.qtd}   PLANIFICADA "
        f"{fmt(p.comprimento)} x {fmt(p.largura)} MM",
        f"ABAS EXTERNAS: {' / '.join(fmt(a) for a in p.abas)} MM",
        "CAMADAS DOBRA, GRAVACAO E TEXTO NAO SAO DE CORTE",
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
    for x1, y1, x2, y2 in p.marcas:
        out.append(f'<line class="mark" x1="{x1:.1f}" y1="{Y(y1):.1f}" x2="{x2:.1f}" '
                   f'y2="{Y(y2):.1f}"/>')
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
    """Materiais de consumo e itens comerciais do jogo de fôrmas (quantidades com reserva)."""
    n_lon_mod = VIGA["comprimento"] // VIGA["modulo"]
    n_paraf_painel = 4 * 6 + 2 * 3 + 4 + 2 * 2 + 8   # trilhos, junta, réguas, nivelamento
    return [
        ("Parafuso sextavado M16 x 50, classe 8.8, com porca e duas arruelas, zincado "
         "(fôrma da longarina; 91 por jogo e reserva)", 100, "jogo"),
        ("Barra roscada 5/8\" (16 mm) x 600 mm, com duas porcas e duas arruelas (tirante "
         "superior da fôrma da longarina)", 4 * n_lon_mod, "jogo"),
        ("Parafuso sextavado M16 x 40, classe 8.8, com porca e arruela, zincado (fôrma da "
         "placa de saia, 16 por fôrma)", 16 * FORMAS_PLACA, "jogo"),
        ("Tubo-fôrma de aço ou PVC rígido, diâmetro 50 mm x 150 mm, com tampa e parafuso M12 "
         "(furos de içamento e dreno da placa)", 3 * FORMAS_PLACA, "un"),
        ("Parafuso sextavado M16 x 40, classe 8.8, com porca e arruela, zincado (fôrma do "
         f"painel, {n_paraf_painel} por fôrma)", n_paraf_painel * FORMAS_PAINEL, "jogo"),
        ("Barra roscada M12 x 250 mm com porca e arruela (fixação da fôrma do nicho)",
         8 * FORMAS_PAINEL, "jogo"),
        ("Porca M12 para solda sob o fundo da fôrma do painel", 8 * FORMAS_PAINEL, "un"),
        ("Inserto roscado M16 de nivelamento, incorporado ao painel (8 por painel, "
         f"{N_PAINEIS} painéis)", 8 * N_PAINEIS, "un"),
        ("Inserto de içamento conforme especificação do projeto estrutural (4 por painel, "
         f"{N_PAINEIS} painéis)", 4 * N_PAINEIS, "un"),
        ("Perfil triangular de PVC rígido para chanfro, 20 x 20 mm (arestas inferiores da "
         "longarina)", 2 * VIGA["comprimento"] / 1000, "m"),
        ("Perfil triangular de PVC rígido para chanfro, 20 x 20 mm (arestas da face aparente da "
         f"placa, {FORMAS_PLACA} fôrmas)",
         FORMAS_PLACA * 2 * (PLACA["comprimento"] + PLACA["altura"]) / 1000, "m"),
        ("Perfil triangular de PVC rígido para chanfro, 15 x 15 mm (arestas inferiores e "
         "superiores das bordas do painel)", round(FORMAS_PAINEL * 2 * 2 * (PAINEL["comprimento"]
                                                         + PAINEL["largura"]) / 1000, 1), "m"),
        ("Gaxeta de espuma para a base da fôrma do nicho", 1, "conforme consumo"),
        ("Desmoldante para fôrma metálica", 1, "conforme consumo"),
        ("Fita ou cordão de vedação para juntas da fôrma", 1, "conforme consumo"),
    ]


def main():
    pastas = {k: os.path.join(SAIDA, k) for k in ("dxf", "svg", "tabelas")}
    for pasta in pastas.values():
        os.makedirs(pasta, exist_ok=True)
    for k, ext in (("dxf", ".dxf"), ("svg", ".svg")):    # remove arquivos de versões antigas
        for nome in os.listdir(pastas[k]):
            if nome.endswith(ext):
                os.remove(os.path.join(pastas[k], nome))

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
