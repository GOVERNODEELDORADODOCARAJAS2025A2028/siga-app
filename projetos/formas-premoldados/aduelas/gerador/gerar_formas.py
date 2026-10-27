#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador paramétrico das fôrmas metálicas das aduelas (galerias celulares) de concreto armado
pré-moldado de seção quadrada interna de 1,00 × 1,00 m, 2,00 × 2,00 m e 2,50 × 2,50 m.

A aduela é moldada na posição vertical, com o eixo da galeria na vertical: o macho (ponta) fica
embaixo, moldado pela base, e a bolsa (fêmea) fica em cima, moldada pelo anel superior. Cada
jogo de fôrma tem fôrma externa (painéis e cantos), núcleo (painéis e cantos com mísula), base
e anel superior.

Gera, por tamanho de aduela, em saida/<tamanho>/:
  dxf/<marca>_CORTE.dxf, dxf/<marca>_CORTE_E_GRAVACAO.dxf e dxf/<marca>_DESENHO.dxf
  svg/<marca>.svg e tabelas/*.csv

O motor de chapas (dobra, planificação, verificações e arquivos) fica em ../../comum/chapas.py.

ATENÇÃO
  1. Raio interno de dobra e fator K (tabela DOBRA, em comum/chapas.py) são PROVISÓRIOS.
  2. Espessura das paredes, mísulas e encaixe são de pré-dimensionamento. O engenheiro
     responsável (ART) confirma ou corrige antes da fabricação.

Uso:  python3 gerar_formas.py            (requer: pip install ezdxf)
"""

import math
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(AQUI, "..", "..", "comum")))
from chapas import (CONCRETO_T_M3, DOBRA, FURO_M16, Peca, dados_dobra,  # noqa: E402,F401
                    fmt, fmt_t, forca_dobra_tf, grava_saidas)

SAIDA = os.path.normpath(os.path.join(AQUI, "..", "saida"))

IDENTIFICACAO = dict(
    obra="ADUELAS DE CONCRETO ARMADO PRÉ-MOLDADO, SEÇÕES QUADRADAS DE 1,00 m, 2,00 m E 2,50 m",
    local="A DEFINIR",
    situacao="ANTEPROJETO PARA ANÁLISE TÉCNICA – NÃO LIBERADO PARA FABRICAÇÃO",
    data="27/10/2026",
    revisoes=[("0", "27/10/2026", "EMISSÃO INICIAL PARA ANÁLISE TÉCNICA")],
)

# --------------------------------------------------------------------------
# ADUELAS (pré-dimensionamento; ver README.md e memorial MD-02)
#   B: vão e altura internos; t: espessura das lajes e paredes; m: mísula interna (m × m);
#   r: trecho reto do canto do núcleo junto a cada face; sinapi: composição de referência
# --------------------------------------------------------------------------
ADUELAS = {
    "A100": dict(B=1000, t=150, m=150, r=80, sinapi="–",
                 nome="1,00 × 1,00 m", titulo="1,00 × 1,00"),
    "A200": dict(B=2000, t=200, m=200, r=100, sinapi="104493",
                 nome="2,00 × 2,00 m", titulo="2,00 × 2,00"),
    "A250": dict(B=2500, t=200, m=200, r=100, sinapi="104495",
                 nome="2,50 × 2,50 m", titulo="2,50 × 2,50"),
}

# Encaixe macho e fêmea (todas as aduelas)
L_UTIL = 1000          # comprimento útil da aduela (passo na galeria)
P_MACHO = 65           # comprimento do macho
P_BOLSA = 75           # profundidade da bolsa; folga axial de 10 mm no fundo da bolsa
FOLGA = 6              # diferença entre a largura da bolsa e a do macho, sem a inclinação
DECLIVE = 0.10         # inclinação de referência das faces do encaixe; recuos arredondados
H_EXT = L_UTIL + P_MACHO                  # 1065: altura da fôrma externa (z = 0 na base)
H_NUC = L_UTIL - P_BOLSA + P_MACHO        # 990: altura do núcleo
FORMAS_POR_TAMANHO = 1                    # jogos de fôrma por tamanho (1 aduela por dia)

E_PELE = 4.75          # chapa das faces, cantos, nervuras e cintas
E_PERFIL = 6.30        # chapa das cantoneiras
E_PLACA = 6.30         # chapa da base, do anel superior, das barras e travamentos
ESP_NERV = 340         # espaçamento máximo das nervuras verticais
H_BARRA_MACHO = P_MACHO - E_PLACA          # barras sob a chapa do ressalto
H_BARRA_BOLSA = P_BOLSA - E_PLACA          # barras sobre a chapa do anel superior
RECUO_MACHO = round(DECLIVE * H_BARRA_MACHO)   # 6 mm: macho mais estreito na ponta
RECUO_BOLSA = round(DECLIVE * H_BARRA_BOLSA)   # 7 mm: bolsa mais larga na boca

BASE_EXT, BASE_INT = 105, 105   # quanto a chapa da base passa da face externa e da interna
ANEL_INT = 80                   # quanto o anel superior avança sobre o núcleo
FURO_FACE = 45                  # furos das cantoneiras a 45 mm da face de concreto
CINTA = (60, 150, 60)           # cinta superior: aba soldada, alma, aba
CANT = (63, 75)                 # cantoneira: aba soldada, aba aparafusada
NERV = (63, 40, 63)             # nervura vertical em U


def geometria(cod):
    """Dimensões derivadas de uma aduela (mm)."""
    a = dict(ADUELAS[cod], codigo=cod)
    B, t, m, r = a["B"], a["t"], a["m"], a["r"]
    a["Be"] = B + 2 * t                         # lado externo
    a["Bn"] = B - 2 * (m + r)                   # painel do núcleo
    a["wm"] = (t - FOLGA) / 2                   # largura do macho junto ao ombro
    a["s0"] = (t + FOLGA) / 2                   # face da bolsa no fundo, a partir da face interna
    # faces inclinadas do encaixe: a inclinação fica nas barras; as bordas das chapas do
    # ressalto e do anel são verticais (6,3 mm)
    a["wm_ponta"] = a["wm"] - RECUO_MACHO       # macho na ponta (z = 0)
    a["wm_ombro"] = a["wm"]                     # macho junto à chapa do ressalto
    a["s_fundo"] = a["s0"]                      # bolsa junto à chapa do anel
    a["s_boca"] = a["s0"] + RECUO_BOLSA         # bolsa na boca (z = 1065)
    a["folga_radial"] = a["s_boca"] - a["wm"]
    a["n_ext"] = _nervuras(B)
    a["n_nuc"] = _nervuras(a["Bn"])
    return a


def _nervuras(comprimento):
    """Número par de nervuras (o meio do painel fica livre para o tubo-fôrma)."""
    n = math.ceil(comprimento / ESP_NERV) - 1
    return n + (n % 2)


def eixos_nervuras(comprimento, n):
    passo = comprimento / (n + 1)
    return [passo * (k + 1) for k in range(n)]


def furos_base(comprimento, n):
    """Parafusos de base no meio do primeiro vão, do vão central e do último vão entre
    nervuras (o número de vãos é ímpar), a pelo menos 30 mm da ponta da cantoneira."""
    passo = comprimento / (n + 1)
    meio = n // 2
    minimo = CANT[0] + 2 + 30
    return [max(passo / 2, minimo), passo * meio + passo / 2,
            min(comprimento - passo / 2, comprimento - minimo)]


def furos_cantoneira(altura):
    """Quatro furos espaçados igualmente em torno do meio da altura."""
    s = round(altura / 4)
    return [altura / 2 + (k - 1.5) * s for k in range(4)]


# --------------------------------------------------------------------------
# CONCRETO DA ADUELA
# --------------------------------------------------------------------------
def anel(lado_ext, lado_int, m):
    """Área entre dois quadrados, com mísulas m × m nos cantos internos."""
    return lado_ext ** 2 - lado_int ** 2 + 2 * m ** 2


def concreto(a):
    """Volume (m³), massa (t) e altura do centro de gravidade (mm, a partir da ponta do macho).
    Integração por trechos ao longo do eixo, com as faces inclinadas do encaixe."""
    B, t, m = a["B"], a["t"], a["m"]

    def integra(z0, z1, area, n=40):
        h = (z1 - z0) / n
        v = zv = 0.0
        for k in range(n):
            z = z0 + (k + 0.5) * h
            s = area(z) * h
            v += s
            zv += s * z
        return v, zv

    def macho(z):
        if z < H_BARRA_MACHO:
            r = a["wm_ponta"] + z / H_BARRA_MACHO * RECUO_MACHO
        else:
            r = a["wm_ombro"]
        return anel(B + 2 * r, B, m)

    def bolsa(z):
        if z < H_NUC + E_PLACA:
            s = a["s_fundo"]
        else:
            s = a["s0"] + (z - H_NUC - E_PLACA) / H_BARRA_BOLSA * RECUO_BOLSA
        return (B + 2 * t) ** 2 - (B + 2 * s) ** 2

    partes = [integra(0, P_MACHO, macho),
              integra(P_MACHO, H_NUC, lambda z: anel(B + 2 * t, B, m), 1),
              integra(H_NUC, H_EXT, bolsa)]
    v = sum(p[0] for p in partes)
    zc = sum(p[1] for p in partes) / v
    furo = math.pi * 55 ** 2 * t                 # furo de içamento de 110 mm na laje superior
    v_m3 = (v - furo) / 1e9
    return v_m3, v_m3 * CONCRETO_T_M3, zc


def altura_icamento(a):
    """Altura do furo de içamento (centro de gravidade, arredondado a 5 mm)."""
    return 5 * round(concreto(a)[2] / 5)


# --------------------------------------------------------------------------
# PEÇAS DA FÔRMA
# --------------------------------------------------------------------------
def pecas_aduela(cod):
    a = geometria(cod)
    B, t, m, r, Be, Bn = a["B"], a["t"], a["m"], a["r"], a["Be"], a["Bn"]
    F = lambda n: f"F-{cod}-{n:02d}"
    z_ic = altura_icamento(a)
    n_e, n_n = a["n_ext"], a["n_nuc"]
    pecas = []

    def furo_flange(p):
        """y, na planificação da cantoneira, do furo a FURO_FACE da face de concreto."""
        return p.largura - (CANT[1] - (FURO_FACE - E_PELE))

    # ---------------- FÔRMA EXTERNA ----------------
    ext = "Fôrma externa"
    for k, com_furo in ((1, False), (2, True)):
        nome = "Painel da fôrma externa" + (", com furo do tubo-fôrma (laje superior)"
                                            if com_furo else "")
        p = Peca(F(k), nome, ext, E_PELE, 1 if com_furo else 3, B, [H_EXT], ["chapa plana"],
                 obs="Face de concreto pela face inferior no corte. Nervuras, cintas e "
                     "cantoneiras soldadas pela face superior, sem solda na face de concreto.")
        for x in eixos_nervuras(B, n_e):
            p.marcas.append((x, CANT[0] + 4, x, H_EXT - CINTA[0] - 4))
        p.lado_marca = "face superior (face posterior do painel)"
        p.face_concreto = "inferior"
        if com_furo:
            p.furos.append((B / 2, z_ic, FURO_M16))
            p.obs = ("Painel da laje superior da aduela: furo para a barra roscada do "
                     "tubo-fôrma do furo de içamento. " + p.obs)
        pecas.append(p)

    canto = Peca(F(3), "Canto da fôrma externa", ext, E_PELE, 4, H_EXT,
                 [t + E_PELE, t + E_PELE], ["face de concreto", "face de concreto"],
                 sentido="dobra única de 90 graus, face de concreto no lado interno",
                 face_concreto="superior",
                 obs=f"Abas internas de {fmt(t)} mm, iguais à espessura da parede: o canto é a "
                     f"única peça da fôrma externa que depende da espessura. Cantoneiras "
                     f"{F(4)} soldadas nas duas extremidades, pelo lado externo.")
    pecas.append(canto)

    ce = Peca(F(4), "Cantoneira de extremidade da fôrma externa", ext, E_PERFIL, 16, H_EXT,
              list(CANT), ["aba soldada", "aba aparafusada"], sentido="dobra única de 90 graus",
              obs=f"Duas em cada painel e duas em cada canto, com a aba soldada rente à borda "
                  f"da chapa. Ligação painel-canto com 4 parafusos M16.")
    for z in furos_cantoneira(H_EXT):
        ce.furos.append((z, furo_flange(ce), FURO_M16))
    pecas.append(ce)

    comp_int = B - 2 * CANT[0] - 4           # entre as cantoneiras de extremidade
    cb = Peca(F(5), "Cantoneira de base do painel da fôrma externa", ext, E_PERFIL, 4,
              comp_int, list(CANT), ["aba soldada", "aba de base"],
              sentido="dobra única de 90 graus",
              obs="Soldada rente à borda inferior do painel; a aba de base é aparafusada na "
                  "chapa da base com 3 parafusos M16.")
    for x in furos_base(B, n_e):
        cb.furos.append((x - CANT[0] - 2, furo_flange(cb), FURO_M16))
    pecas.append(cb)

    ci = Peca(F(6), "Cinta superior do painel da fôrma externa, perfil U", ext, E_PELE, 4,
              comp_int, list(CINTA), ["aba soldada", "alma", "aba"],
              sentido="perfil U, abas para o mesmo lado",
              obs="Soldada no topo do painel, com a alma rente à borda superior. O furo central "
                  "recebe a régua porta-inserto ou o olhal de içamento do painel.")
    ci.furos.append((B / 2 - CANT[0] - 2, ci.y_na_face(1, 60), FURO_M16))
    pecas.append(ci)

    ne = Peca(F(7), "Nervura vertical do painel da fôrma externa, perfil U", ext, E_PELE,
              4 * n_e, H_EXT - CANT[0] - 2 - CINTA[0] - 2, list(NERV), ["aba", "alma", "aba"],
              sentido="perfil U, abas para o mesmo lado",
              obs=f"{n_e} por painel, nos eixos gravados, soldadas pelas bordas das abas.")
    pecas.append(ne)

    # ---------------- NÚCLEO ----------------
    nuc = "Núcleo"
    for k, com_furo in ((8, False), (9, True)):
        nome = "Painel do núcleo" + (", com furo do tubo-fôrma (laje superior)"
                                     if com_furo else "")
        p = Peca(F(k), nome, nuc, E_PELE, 1 if com_furo else 3, Bn, [H_NUC], ["chapa plana"],
                 obs="Face de concreto pela face inferior no corte. Nervuras, cinta e "
                     "cantoneiras soldadas pela face superior.")
        for x in eixos_nervuras(Bn, n_n):
            p.marcas.append((x, CANT[0] + 4, x, H_NUC - CINTA[0] - 4))
        p.lado_marca = "face superior (face interna do núcleo)"
        p.face_concreto = "inferior"
        if com_furo:
            p.furos.append((Bn / 2, z_ic, FURO_M16))
            p.obs = ("Painel da laje superior da aduela, oposto ao painel externo com furo. "
                     + p.obs)
        pecas.append(p)

    cn = Peca(F(10), "Canto do núcleo com mísula", nuc, E_PELE, 4, H_NUC,
              [r, m * math.sqrt(2), r], ["face de concreto", "mísula", "face de concreto"],
              angulos=[45.0, 45.0], giros=[-1, -1],
              sentido="duas dobras de 45 graus, face de concreto no lado externo",
              face_concreto="superior",
              obs=f"Mísula de {fmt(m)} × {fmt(m)} mm. Cantoneiras {F(11)} soldadas nas duas "
                  f"extremidades e chapa de travamento {F(15)} soldada no topo, pelo lado "
                  f"interno.")
    pecas.append(cn)

    cen = Peca(F(11), "Cantoneira de extremidade do núcleo", nuc, E_PERFIL, 16, H_NUC,
               list(CANT), ["aba soldada", "aba aparafusada"], sentido="dobra única de 90 graus",
               obs="Duas em cada painel e duas em cada canto do núcleo, com a aba soldada rente "
                   "à borda. Ligação painel-canto com 4 parafusos M16, pelo lado interno.")
    for z in furos_cantoneira(H_NUC):
        cen.furos.append((z, furo_flange(cen), FURO_M16))
    pecas.append(cen)

    comp_n = Bn - 2 * CANT[0] - 4
    cbn = Peca(F(12), "Cantoneira de base do painel do núcleo", nuc, E_PERFIL, 4, comp_n,
               list(CANT), ["aba soldada", "aba de base"], sentido="dobra única de 90 graus",
               obs="Soldada rente à borda inferior do painel; aparafusada na chapa da base com "
                   "3 parafusos M16, pelo lado interno.")
    for x in furos_base(Bn, n_n):
        cbn.furos.append((x - CANT[0] - 2, furo_flange(cbn), FURO_M16))
    pecas.append(cbn)

    cin = Peca(F(13), "Cinta superior do painel do núcleo, perfil U", nuc, E_PELE, 4, comp_n,
               list(CINTA), ["aba soldada", "alma", "aba"], sentido="perfil U, abas para o mesmo lado",
               obs="Soldada no topo do painel, com a alma rente à borda superior; a alma apoia o "
                   "anel superior, fixado com 3 parafusos M16.")
    for x in furos_base(Bn, n_n):
        cin.furos.append((x - CANT[0] - 2, cin.y_na_face(1, FURO_FACE - E_PELE), FURO_M16))
    pecas.append(cin)

    nn = Peca(F(14), "Nervura vertical do painel do núcleo, perfil U", nuc, E_PELE, 4 * n_n,
              H_NUC - CANT[0] - 2 - CINTA[0] - 2, list(NERV), ["aba", "alma", "aba"],
              sentido="perfil U, abas para o mesmo lado",
              obs=f"{n_n} por painel, nos eixos gravados, soldadas pelas bordas das abas.")
    pecas.append(nn)

    tv = travamento_canto(a)
    pecas.append(Peca(F(15), "Chapa de travamento do canto do núcleo", nuc, E_PLACA, 4,
                      max(x for x, _ in tv), [max(y for _, y in tv)], ["chapa plana"],
                      contorno=tv,
                      obs=f"Soldada no topo do canto {F(10)}, rente à borda superior, entre as "
                          f"cantoneiras; apoia o anel superior no canto."))

    # ---------------- BASE ----------------
    base = "Base"
    pecas.append(chapa_base(a, F(16)))
    pecas.extend(ressalto(a, F))

    # ---------------- ANEL SUPERIOR ----------------
    pecas.extend(anel_superior(a, F))

    # ---------------- ACESSÓRIO ----------------
    pecas.append(regua_inserto(a, F(22)))
    for p in pecas:
        p.tamanho = cod
    assert {p.forma for p in pecas} <= {ext, nuc, base, "Anel superior", "Acessório"}
    return pecas


def travamento_canto(a):
    """Hexágono da chapa de travamento, no canto superior direito do núcleo (coordenadas
    locais). Folga de 2 mm para as faces internas do canto e para as cantoneiras."""
    B, m, r = a["B"], a["m"], a["r"]
    xa = B / 2 - m - r + CANT[0] + 2
    yb = B / 2 - E_PELE - 2
    c1 = B - m - (E_PELE + 2) * math.sqrt(2)
    c2 = B - m - 110 * math.sqrt(2)
    pts = [(xa, yb), (c1 - yb, yb), (yb, c1 - yb), (yb, xa), (c2 - xa, xa), (xa, c2 - xa)]
    x0 = min(x for x, _ in pts)
    y0 = min(y for _, y in pts)
    return [(round(x - x0, 2), round(y - y0, 2)) for x, y in pts]


def _gira(pts, k):
    """Gira pontos (x, y) de k × 90 graus em torno da origem."""
    for _ in range(k % 4):
        pts = [(-y, x) for x, y in pts]
    return pts


def chapa_base(a, marca):
    """Chapa da base: quatro retângulos iguais em catavento formando o anel quadrado. O
    retângulo 1 fica no lado inferior (y negativo), com o canto inferior esquerdo."""
    B, t, Be, Bn = a["B"], a["t"], a["Be"], a["Bn"]
    So = Be + 2 * BASE_EXT
    w = t + BASE_EXT + BASE_INT
    x0, y0 = -So / 2, -So / 2                    # origem local do retângulo 1
    comp = So - w
    furos = []
    for x in furos_base(B, a["n_ext"]):          # cantoneira de base da fôrma externa
        furos.append((-B / 2 + x, -B / 2 - t - FURO_FACE))
    for x in furos_base(Bn, a["n_nuc"]):         # cantoneira de base do núcleo
        furos.append((-Bn / 2 + x, -B / 2 + FURO_FACE))
    furos.append((-Be / 2 - 55, -Be / 2 - 55))   # chumbador no canto
    p = Peca(marca, "Chapa da base", "Base", E_PLACA, 4, comp, [w], ["chapa plana"],
             obs="Quatro peças iguais em catavento, unidas por solda de penetração total "
                 "esmerilhada na face superior; assentar sobre piso de concreto nivelado, com "
                 "tolerância de 2 mm, e fixar com 4 chumbadores M16.")
    for x, y in furos:
        p.furos.append((round(x - x0, 2), round(y - y0, 2), FURO_M16))
    # linhas gravadas: barras do ressalto (lados inferior e esquerdo, recortadas no retângulo)
    r_macho = a["wm_ponta"] + barra(H_BARRA_MACHO, RECUO_MACHO)[1]   # face posterior, na base
    r_ext = t - 1.5 - E_PLACA                    # face interna da barra externa
    for rr in (r_macho, r_ext):
        h = B / 2 + rr
        segs = [((-h, -h), (h, -h)), ((-h, -h), (-h, h))]     # lados inferior e esquerdo
        for (xa, ya), (xb, yb) in segs:
            dentro = x0 <= xa <= x0 + comp if xa == xb else y0 <= ya <= y0 + w
            xa, xb = max(xa, x0), min(xb, x0 + comp)
            ya, yb = max(ya, y0), min(yb, y0 + w)
            if dentro and (xa < xb or ya < yb):
                p.marcas.append((round(xa - x0, 2), round(ya - y0, 2), round(xb - x0, 2),
                                 round(yb - y0, 2)))
    p.lado_marca = "face superior"
    p.face_concreto = "superior"
    p.catavento = dict(So=So, w=w)
    return p


def barra(h, recuo):
    """Barra inclinada de altura vertical h e recuo horizontal 'recuo' no topo: altura
    medida na própria barra e espessura horizontal."""
    return math.hypot(h, recuo), E_PLACA * math.hypot(h, recuo) / h


def ressalto(a, F):
    """Ressalto que molda o ombro do macho: chapa em catavento sobre a barra da face do macho
    (inclinada 1:10) e a barra externa."""
    B, t = a["B"], a["t"]
    h = H_BARRA_MACHO
    r_in, r_out = a["wm_ombro"], t - 1
    lado_o = B + 2 * r_out
    ws = r_out - r_in
    pecas = [Peca(F(17), "Chapa do ressalto da base", "Base", E_PLACA, 4, round(lado_o - ws, 2),
                  [round(ws, 2)], ["chapa plana"],
                  obs=f"Quatro peças iguais em catavento, soldadas sobre as barras {F(18)} e "
                      f"{F(19)}. A face superior molda o ombro do macho; a borda interna, o topo "
                      f"da face do macho. Juntas esmerilhadas.",
                  face_concreto="superior")]
    # barra da face do macho: trapézio, mais largo em cima; face de concreto voltada para dentro
    lado0 = B + 2 * a["wm_ponta"]
    lado1 = B + 2 * a["wm_ombro"]
    hs, eb = barra(h, RECUO_MACHO)
    l0, l1 = lado0 + eb, lado1 + eb
    d = (l1 - l0) / 2
    pecas.append(Peca(F(18), "Barra da face do macho", "Base", E_PLACA, 4, round(l1, 2),
                      [round(hs, 2)], ["chapa plana"],
                      contorno=[(round(d, 2), 0), (round(d + l0, 2), 0), (round(l1, 2), round(hs, 2)),
                                (0, round(hs, 2))],
                      obs=f"Base menor apoiada na chapa da base, na linha gravada; topo "
                          f"{RECUO_MACHO} mm para fora da base. Face de concreto voltada para o "
                          f"centro: molda a face externa do macho. Cantos em catavento, soldados "
                          f"e esmerilhados."))
    lado_e = B + 2 * (t - 1.5)
    pecas.append(Peca(F(19), "Barra externa do ressalto", "Base", E_PLACA, 4,
                      round(lado_e - E_PLACA, 2), [round(h, 2)], ["chapa plana"],
                      obs="Vertical, sob a borda externa da chapa do ressalto, encostada na fôrma "
                          "externa. Não tem contato com o concreto."))
    return pecas


def anel_superior(a, F):
    """Anel superior: chapa em quatro trapézios com juntas a 45 graus e barras da saia
    (inclinadas 1:10) que moldam a face interna da bolsa."""
    B, m, Bn = a["B"], a["m"], a["Bn"]
    sp = a["s_fundo"]                          # borda externa da chapa = face da bolsa
    S = B + 2 * sp
    c = (B - m) - ANEL_INT * math.sqrt(2)      # chanfro interno, paralelo à mísula
    yi = -(B / 2 - ANEL_INT)                   # borda interna reta
    xi = B / 2 - m - (ANEL_INT * math.sqrt(2) - ANEL_INT)
    xd = c / 2                                 # vértice do chanfro na junta a 45 graus
    pts = [(-S / 2, -S / 2), (S / 2, -S / 2), (xd, -xd), (xi, yi), (-xi, yi), (-xd, -xd)]
    loc = [(round(x + S / 2, 2), round(y + S / 2, 2)) for x, y in pts]
    p = Peca(F(20), "Chapa do anel superior", "Anel superior", E_PLACA, 4, round(S, 2),
             [max(y for _, y in loc)], ["chapa plana"], contorno=loc,
             obs=f"Quatro peças iguais com juntas a 45 graus, soldadas e esmerilhadas na face "
                 f"inferior. A face inferior molda o fundo da bolsa e a borda externa, o início "
                 f"da face da bolsa. Apoiada nas cintas {F(13)} e fixada com 12 parafusos M16.",
             face_concreto="inferior")
    for x in furos_base(Bn, a["n_nuc"]):
        p.furos.append((round(-Bn / 2 + x + S / 2, 2), round(sp + FURO_FACE, 2), FURO_M16))
    # linha gravada: face interna da barra da saia (barras em catavento)
    eb = barra(H_BARRA_BOLSA, RECUO_BOLSA)[1]
    p.marcas.append((round(eb, 2), round(eb, 2), round(S - eb, 2), round(eb, 2)))
    p.lado_marca = "face superior"
    pecas = [p]
    # barra da saia: trapézio mais largo em cima; face de concreto voltada para fora
    hs, eb = barra(H_BARRA_BOLSA, RECUO_BOLSA)
    lado0, lado1 = B + 2 * sp, B + 2 * a["s_boca"]
    l0, l1 = lado0 - eb, lado1 - eb
    d = (l1 - l0) / 2
    pecas.append(Peca(F(21), "Barra da saia do anel superior", "Anel superior", E_PLACA, 4,
                      round(l1, 2), [round(hs, 2)], ["chapa plana"],
                      contorno=[(round(d, 2), 0), (round(d + l0, 2), 0), (round(l1, 2), round(hs, 2)),
                                (0, round(hs, 2))],
                      obs=f"Base menor soldada sobre a chapa do anel, rente à borda externa; "
                          f"topo {RECUO_BOLSA} mm para fora da base. Face de concreto voltada para "
                          f"fora: molda a face interna da bolsa. Cantos em catavento, soldados e "
                          f"esmerilhados."))
    return pecas


def regua_inserto(a, marca):
    """Régua que posiciona o inserto de içamento no topo da bolsa, apoiada na cinta da fôrma
    externa."""
    t = a["t"]
    r_ins = (a["s_boca"] + t) / 2               # meio da aba da bolsa, no topo
    r_cinta = t + E_PELE + 60                    # furo da alma da cinta
    x0 = r_ins - 40
    comp = r_cinta + 40 - x0
    p = Peca(marca, "Régua porta-inserto de içamento", "Acessório", E_PLACA, 2,
             round(comp, 2), [60], ["chapa plana"],
             obs="Apoiada na alma da cinta da fôrma externa, no meio dos painéis da laje superior "
                 "e da laje inferior. O furo interno posiciona o inserto de içamento no topo da "
                 "bolsa; adequar o furo ao inserto especificado no projeto estrutural.")
    p.furos.append((round(r_ins - x0, 2), 30, FURO_M16))
    p.furos.append((round(r_cinta - x0, 2), 30, FURO_M16))
    return p


# --------------------------------------------------------------------------
# ELEMENTOS DE CONCRETO E ITENS COMERCIAIS
# --------------------------------------------------------------------------
def kit(cod):
    a = geometria(cod)
    v, _, _ = concreto(a)
    B, t = a["B"] / 1000, a["t"] / 1000
    dim = (f"{B:.2f} × {B:.2f} interno, parede {t:.2f}, comprimento útil 1,00"
           .replace(".", ","))
    return [(cod, f"Aduela fechada {a['nome']}", dim, v, 1, f"F-{cod}")]


def lista_de_compras(cod):
    """Itens comerciais e materiais de consumo de um jogo de fôrma (quantidades com reserva)."""
    a = geometria(cod)
    n_paraf = 8 * 4 + 4 * 3 + 8 * 4 + 4 * 3 + 12 + 2
    return [
        (f"Parafuso sextavado M16 x 50, classe 8.8, com porca e duas arruelas, zincado "
         f"({n_paraf} por jogo e reserva)", n_paraf + 8, "jogo"),
        ("Chumbador mecânico M16 para fixação da base no piso de concreto", 4, "un"),
        ("Olhal giratório M16 para içamento dos painéis e do anel superior", 2, "un"),
        (f"Barra roscada M16 x {int(a['t'] + 200)} mm, com duas porcas e duas arruelas "
         f"(tubo-fôrma do furo de içamento)", 1, "jogo"),
        ("Tubo de PVC rígido DE 110 mm, cortado na espessura da parede, com dois tampões "
         "centralizadores (tubo-fôrma do furo de içamento, um por aduela)", 1, "conforme consumo"),
        ("Inserto de içamento conforme projeto estrutural (dois por aduela, no topo da bolsa)",
         1, "conforme consumo"),
        ("Espaçador plástico para cobrimento de 40 mm", 1, "conforme consumo"),
        ("Desmoldante para fôrma metálica", 1, "conforme consumo"),
        ("Fita ou cordão de vedação para juntas da fôrma", 1, "conforme consumo"),
    ]


def todas_as_pecas(cod):
    return pecas_aduela(cod)


def main():
    for cod in ADUELAS:
        a = geometria(cod)
        v, massa, zc = concreto(a)
        saida = os.path.join(SAIDA, cod)
        resumo = grava_saidas(todas_as_pecas(cod), saida, lista_de_compras(cod), kit(cod))
        aco = sum(kg for _, kg, _ in resumo)
        print(f"{cod}: concreto {v:.3f} m³, {massa:.2f} t, centro a {zc:.0f} mm; "
              f"fôrma {sum(n for *_, n in resumo)} peças, {aco:.0f} kg")
        for forma, kg, n in resumo:
            print(f"   {forma}: {n} peças, {kg:.0f} kg")
    print("Arquivos em", SAIDA)


if __name__ == "__main__":
    main()
