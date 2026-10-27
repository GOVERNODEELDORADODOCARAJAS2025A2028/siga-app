#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Motor comum das fôrmas de chapa cortada a laser e dobrada.

Parâmetros de dobra, planificação pela linha neutra, peça de chapa (Peca), verificações de
fabricação, arquivos digitais (DXF de corte, de corte e gravação e de desenho; SVG de
pré-visualização) e tabelas de fabricação. Os projetos (ponte, aduelas e outros) definem as
peças e importam este módulo.

ATENÇÃO
  Raio interno de dobra e fator K (tabela DOBRA) são PROVISÓRIOS. Antes de cortar, substituir
  pelos valores da tabela de dobra do fornecedor, com o ferramental real.
"""

import csv
import math
import os
import unicodedata
from dataclasses import dataclass, field

import ezdxf
from ezdxf import units

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


def grava_saidas(pecas, saida, compras, kit):
    """Arquivos digitais e tabelas de um conjunto de peças. 'compras': lista de
    (item, quantidade, unidade); 'kit': lista de (código, peça, dimensões, volume unitário,
    quantidade, fôrma) dos elementos de concreto. Interrompe se alguma verificação falhar.
    Devolve o resumo [(fôrma, massa de aço em kg, número de peças)]."""
    pastas = {k: os.path.join(saida, k) for k in ("dxf", "svg", "tabelas")}
    for pasta in pastas.values():
        os.makedirs(pasta, exist_ok=True)
    for k, ext in (("dxf", ".dxf"), ("svg", ".svg")):    # remove arquivos de versões antigas
        for nome in os.listdir(pastas[k]):
            if nome.endswith(ext):
                os.remove(os.path.join(pastas[k], nome))

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
        for linha in compras:
            wr.writerow(linha)

    with open(os.path.join(pastas["tabelas"], "kit_pecas_de_concreto.csv"), "w", newline="",
              encoding="utf-8") as f:
        wr = csv.writer(f, delimiter=";")
        wr.writerow(["codigo", "peca", "dimensoes_m", "volume_unit_m3", "peso_unit_t", "qtd",
                     "volume_total_m3", "forma"])
        for cod, nome, dim, vol, qtd, forma in kit:
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
    return resumo
