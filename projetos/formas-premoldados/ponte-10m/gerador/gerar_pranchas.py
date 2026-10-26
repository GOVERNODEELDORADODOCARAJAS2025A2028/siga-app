#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pranchas de fabricação das fôrmas metálicas da ponte pré-moldada de 10 m (formato A3).

Gera saida/pranchas/FM_formas_metalicas_A3.pdf: índice e notas gerais, parâmetros de corte e
dobra, conjunto de cada fôrma (seções, lista de materiais, montagem e soldas), detalhe de cada
marca (planificação, seção dobrada, dobras e furos) e listas gerais.

Uso:  python3 gerar_pranchas.py      (rodar depois de gerar_formas.py)
"""

import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import desenhos as dz                     # noqa: E402
import folhas as fl                       # noqa: E402
import gerar_formas as gf                 # noqa: E402

PASTA = os.path.join(gf.SAIDA, "pranchas")
QW, QH = 390, 277                 # área útil dentro do quadro (A3)
RX, RY = QW - fl.LEG_W, QH - fl.LEG_H - fl.REV_H   # canto da área reservada à legenda

FORMAS = [
    ("Longarina", "F-LON", "FÔRMA DA LONGARINA", "LONGARINA P-01, 300 × 900 × 10000",
     "1 JOGO DE 4 MÓDULOS DE 2500"),
    ("Placa de saia", "F-PLA", "FÔRMA DA PLACA DE SAIA", "PLACA DE SAIA P-07, 2000 × 500 × 150",
     "3 FÔRMAS"),
    ("Painel de laje", "F-LAJ", "FÔRMA DO PAINEL DE LAJE", "PAINEL DE LAJE P-02, 4500 × 1230 × 200",
     "2 FÔRMAS"),
]

GRAVACAO = {
    "F-LON-01": "eixos das nervuras F-LON-02",
    "F-LON-05": "eixos das nervuras F-LON-07",
    "F-PLA-01": "eixos das nervuras F-PLA-02",
    "F-LAJ-01": "eixos das nervuras F-LAJ-04",
    "F-LAJ-05": "limites da régua F-LAJ-06",
}


def f1(v):
    return gf.fmt(v)


def kg(v):
    return f"{v:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")


def kg0(v):
    return f"{v:,.0f}".replace(",", ".")


def U(s):
    """Caixa alta, mantendo os símbolos das unidades (mm, m, kg, tf)."""
    s = s.upper()
    s = re.sub(r"(\d)\s*MM\b", r"\1 mm", s)
    s = re.sub(r"(\d)\s*M\b", r"\1 m", s)
    s = re.sub(r"(\d)\s*KG\b", r"\1 kg", s)
    s = re.sub(r"(\d)\s*TF\b", r"\1 tf", s)
    return s


UNIDADES = {"jogo": "JOGO", "un": "UN", "m": "m", "conforme consumo": "CONFORME CONSUMO"}


# --------------------------------------------------------------------------
# BLOCO DE UMA MARCA
# --------------------------------------------------------------------------
def tabela_dados(p):
    arquivos = [f"{p.codigo}_CORTE.dxf"]
    if p.marcas:
        arquivos.append(f"{p.codigo}_CORTE_E_GRAVACAO.dxf")
    arq = fl.Bruto("<br>".join(f'<span class="nw">{a}</span>' for a in arquivos))
    linhas = [
        ["MATERIAL", f"ASTM A36, CHAPA {gf.fmt_t(p.t)} mm", "QUANTIDADE", f"{p.qtd} PEÇAS"],
        ["PLANIFICAÇÃO", f"{f1(p.comprimento)} × {f1(p.largura)} mm", "MASSA UNITÁRIA",
         f"{kg(p.peso)} kg"],
        ["ARQUIVO DIGITAL", (arq, 1, ""), "MASSA TOTAL", f"{kg(p.peso * p.qtd)} kg"],
    ]
    if p.marcas:
        linhas.append(["GRAVAÇÃO A LASER", (fl.esc(U(f"{GRAVACAO[p.codigo]}, na {p.lado_marca}")),
                                            3, "")])
    linhas.append(["NOTA", (fl.esc(p.obs), 3, "")])
    return fl.tabela(None, linhas, titulo=f"QUADRO DA MARCA {p.codigo}",
                     larguras=["21%", "34%", "21%", "24%"])


def tabela_dobras(p):
    if not p.linhas:
        return ""
    d = gf.DOBRA[p.t]
    linhas = []
    for r, g in zip(gf.roteiro_de_dobra(p), p.giros):
        linhas.append([r["n"], f"{f1(r['ang'])}°", "PARA CIMA" if g > 0 else "PARA BAIXO",
                       f1(r["da"]), f1(r["db"]),
                       "INFERIOR" if r["borda"] == "A" else "SUPERIOR",
                       f1(d["ri"]), d["v"], f1(gf.forca_dobra_tf(p.t, p.comprimento))])
    cab = ["DOBRA", "ÂNGULO", "SENTIDO", "DIST. À BORDA INFERIOR", "DIST. À BORDA SUPERIOR",
           "BORDA NO BATENTE", "RAIO INTERNO", "ABERTURA DO V", "FORÇA (tf)"]
    return fl.tabela(cab, linhas, titulo=f"DOBRAS (COMPRIMENTO DE DOBRA {f1(p.comprimento)} mm)",
                     classes=["c", "c", "c", "n", "n", "c", "n", "n", "n"])


def tabela_furos(p, grupos=None):
    itens = [(f1(x), f1(y), f1(dd)) for x, y, dd in p.furos]
    itens += [(f1(x), f"{f1(min(a, b))} A {f1(max(a, b))}", f"{f1(w)} (RASGO)")
              for x, a, b, w in p.rasgos]
    if not itens:
        return ""
    grupos = grupos or (4 if len(itens) > 18 else 3 if len(itens) > 8 else 2 if len(itens) > 3
                        else 1)
    por = -(-len(itens) // grupos)
    cab = []
    for _ in range(grupos):
        cab += ["FURO", "X", "Y", "DIÂM."]
    linhas = []
    for r in range(por):
        cel = []
        for g in range(grupos):
            k = g * por + r
            if k < len(itens):
                cel += [k + 1, *itens[k]]
            else:
                cel += ["", "", "", ""]
        linhas.append(cel)
    return fl.tabela(cab, linhas, titulo="FUROS (COORDENADAS A PARTIR DA ORIGEM)",
                     classes=["c", "n", "n", "n"] * grupos)


VISTA_PARCIAL = {"F-LAJ-06": (2, 200)}     # escala e comprimento da vista parcial


def vistas_marca(p, e_plan, e_sec):
    parcial = VISTA_PARCIAL.get(p.codigo)
    v = [fl.vista(dz.planificacao(p, e_plan, f"pl-{p.codigo}", simples=bool(parcial)),
                  "PLANIFICAÇÃO", f"1:{e_plan}", "VISTA PELA FACE SUPERIOR NA MESA DE CORTE")]
    if parcial:
        ep, comp = parcial
        v.append(fl.vista(dz.planificacao(p, ep, f"pp-{p.codigo}", trecho=comp),
                          "VISTA PARCIAL DA PLANIFICAÇÃO", f"1:{ep}", "EXTREMIDADE DA PEÇA"))
    if p.linhas:
        v.append(fl.vista(dz.secao_dobrada(p, e_sec, f"sd-{p.codigo}"), "SEÇÃO DA PEÇA DOBRADA",
                          f"1:{e_sec}"))
    return v


ARRANJO_COLUNA = {"F-LAJ-01"}      # vistas à esquerda e quadros empilhados à direita
GRUPOS_FUROS = {"F-LAJ-01": 3}


def conteudo_marca(p, e_plan, e_sec):
    """Bloco da marca: cabeçalho, vistas lado a lado e quadros abaixo (ou à direita)."""
    vs = vistas_marca(p, e_plan, e_sec)
    tabs = [tabela_dados(p), tabela_dobras(p), tabela_furos(p, GRUPOS_FUROS.get(p.codigo))]
    tabs = [t for t in tabs if t]
    if p.codigo in ARRANJO_COLUNA:
        cab = f'<div class="cab">MARCA {p.codigo} – {U(p.nome)}<small>{p.qtd} PEÇAS</small></div>'
        return (cab + f'<div class="linha"><div style="flex:0 0 auto">{"".join(vs)}</div>'
                f'<div class="pilha" style="flex:1 1 0">{"".join(tabs)}</div></div>')
    cls = ["dados"] + (["dobras"] if p.linhas else []) + [""] * (len(tabs) - 1 - bool(p.linhas))
    caixas = "".join(f'<div class="{c}">{t}</div>' for c, t in zip(cls, tabs))
    cab = f'<div class="cab">MARCA {p.codigo} – {U(p.nome)}<small>{p.qtd} PEÇAS</small></div>'
    return (cab + f'<div class="linha" style="justify-content:space-around;flex-wrap:wrap">'
            f'{"".join(vs)}</div><div class="tabs" style="margin-top:2mm">{caixas}</div>')


# --------------------------------------------------------------------------
# FOLHAS GERAIS
# --------------------------------------------------------------------------
CAPACIDADES = (160, 125, 100, 80, 63)

NOTAS_GERAIS = [
    "Medidas em milímetros, salvo indicação em contrário. As cotas prevalecem sobre medidas "
    "tomadas no desenho; não medir em escala.",
    "Este conjunto é anteprojeto. A fabricação somente pode ser iniciada após: (a) aprovação das "
    "dimensões das peças de concreto pelo responsável técnico do projeto estrutural, com ART "
    "registrada (Lei nº 6.496/1977); (b) confirmação, pelo fabricante, do raio interno, do "
    "fator K e da abertura de matriz do ferramental disponível e da capacidade nominal da "
    "dobradeira; (c) regeneração dos arquivos de corte com os dados confirmados; (d) fabricação "
    "e inspeção dimensional de um módulo-piloto de cada fôrma.",
    "Planificações calculadas pela linha neutra, com os parâmetros de dobra da prancha FM-02. "
    "Abas cotadas pelas faces externas (linhas de molde).",
    "Planificações representadas pela face superior na mesa de corte, com origem das coordenadas "
    "no canto inferior esquerdo. Dobra para cima: face superior no lado interno da dobra. Dobra "
    "para baixo: face superior no lado externo da dobra.",
    "Furos de 18 mm para parafusos M16 e de 14 mm para parafusos e barras M12.",
    "Linhas gravadas a laser indicam posições de solda e não são linhas de corte. Arquivos "
    "digitais em DXF R2000, unidade milímetro: arquivo de corte com contorno e furos; arquivo de "
    "corte e gravação com as camadas CORTE e GRAVACAO; arquivo de desenho, somente para "
    "conferência.",
    "Faces de contato com o concreto isentas de solda, respingo, marcação e rebarba, com planeza "
    "de 2 mm em 2500 mm. Aplicar desmoldante antes de cada concretagem.",
    "Tolerâncias de fabricação das peças de chapa: corte e posição de furos ±0,5 mm; ângulo de "
    "dobra ±1°; abas ±1 mm. Tolerâncias da fôrma montada: dimensões internas ±2 mm e diferença "
    "entre diagonais de cada módulo até 3 mm.",
    "Soldagem por arco elétrico com eletrodo E7018 ou arame ER70S-6, por soldador qualificado, "
    "com procedimento de referência AWS D1.1. Dimensões e extensões nos quadros de solda das "
    "pranchas de conjunto.",
    "Arestas inferiores da longarina e da face aparente da placa com chanfro de 20 mm; arestas "
    "inferiores e superiores das bordas do painel com chanfro de 15 mm, em perfil triangular de "
    "PVC rígido fixado à fôrma. O chanfro cobre o raio externo da dobra de apoio dos painéis e "
    "trilhos.",
    "Verificação estrutural das fôrmas (pressão do concreto fresco, deformações e ligações) "
    "conforme ABNT NBR 15696:2009, sob responsabilidade do responsável técnico.",
    "Elementos de concreto, tolerâncias e insertos conforme ABNT NBR 9062:2017 e projeto "
    "estrutural. Os insertos de içamento são especificados no projeto estrutural.",
]

MATERIAIS = [
    ("CHAPAS", "Aço-carbono laminado a quente ASTM A36 ou SAE 1020, espessuras de 3,00 mm, "
               "4,75 mm e 6,30 mm, com certificado de usina."),
    ("PARAFUSOS", "Sextavados M16 e M12, classe 8.8 (ISO 898-1), com porcas e arruelas, "
                  "zincados."),
    ("BARRAS ROSCADAS", "5/8\" e M12, aço SAE 1020, zincadas, com porcas e arruelas."),
    ("CONSUMÍVEIS DE SOLDA", "Eletrodo E7018 (AWS A5.1) ou arame ER70S-6 (AWS A5.18)."),
    ("CHANFROS", "Perfil triangular de PVC rígido, 20 × 20 mm e 15 × 15 mm."),
    ("DESMOLDANTE", "Produto para fôrma metálica, compatível com o acabamento especificado."),
]


def convencoes():
    """Legenda gráfica das linhas e representações usadas nas pranchas."""
    itens = [
        ("vis", "CONTÍNUA LARGA: CONTORNO DE CORTE E ARESTA VISÍVEL"),
        ("dim", "CONTÍNUA ESTREITA: COTA, LINHA DE CHAMADA E DE REFERÊNCIA"),
        ("dobra", "TRAÇO E PONTO ESTREITA: LINHA DE DOBRA E EIXO"),
        ("grav", "TRAÇO E DOIS PONTOS ESTREITA: LINHA GRAVADA A LASER (POSIÇÃO DE SOLDA)"),
        ("hidden", "TRACEJADA ESTREITA: ARESTA NÃO VISÍVEL"),
    ]
    h = 6.0
    alt = h * (len(itens) + 4) + 2
    o = [f'<svg class="dwg imp" viewBox="0 0 175 {alt}" style="width:175mm;height:{alt}mm">']
    y = 3
    for cls, txt in itens:
        o.append(f'<line class="{cls}" x1="2" y1="{y}" x2="34" y2="{y}"/>')
        o.append(f'<text x="40" y="{y + 0.9}" font-size="2.5">{fl.esc(txt)}</text>')
        y += h
    o.append(f'<circle class="furo" cx="10" cy="{y}" r="1.8"/><line class="cm" x1="7.3" y1="{y}" '
             f'x2="12.7" y2="{y}"/><line class="cm" x1="10" y1="{y - 2.7}" x2="10" y2="{y + 2.7}"/>'
             f'<text x="13.2" y="{y - 1.2}" font-size="1.8">3</text>'
             f'<text x="40" y="{y + 0.9}" font-size="2.5">FURO COM CRUZ DE CENTRO E NÚMERO DA '
             f'TABELA DE FUROS</text>')
    y += h
    o.append(f'<rect class="steel" x="2" y="{y - 0.9}" width="32" height="1.8"/>'
             f'<text x="40" y="{y + 0.9}" font-size="2.5">CHAPA EM SEÇÃO (ENEGRECIDA)</text>')
    y += h
    pontos = "".join(f'<circle cx="{2 + 3.6 * i + fx:.2f}" cy="{y - 2 + fz:.2f}" r="{r}"/>'
                     for i in range(8) for fx, fz, r in ((.7, 1.1, .2), (2.5, .6, .15),
                                                         (2.0, 2.9, .22)))
    o.append(f'<rect class="conc" x="2" y="{y - 2}" width="32" height="4" fill="none"/>'
             f'<g class="hd">{pontos}</g>'
             f'<polygon class="chanf" points="34,{y + 2} 30,{y + 2} 34,{y - 2}"/>'
             f'<text x="40" y="{y + 0.9}" font-size="2.5">CONCRETO DA PEÇA MOLDADA E CHANFRO '
             f'(TRIÂNGULO CINZA)</text>')
    y += h
    o.append(f'<line class="lead" x1="4" y1="{y}" x2="26" y2="{y}"/><circle class="dot" cx="4" '
             f'cy="{y}" r=".45"/><text x="28" y="{y + 0.9}" font-size="2.5" font-weight="700">'
             f'F-LON-01</text><text x="54" y="{y + 0.9}" font-size="2.5">INDICAÇÃO DE MARCA '
             f'(PEÇA DE CHAPA DETALHADA NESTE CONJUNTO)</text>')
    o.append("</svg>")
    return f'<div><div class="bloco-tit">CONVENÇÕES</div>{"".join(o)}</div>'


def folha_indice(doc, pecas, indice):
    linhas = [[n, t, e] for n, t, e in indice]
    tab_ind = fl.tabela(["PRANCHA", "CONTEÚDO", "ESCALAS"], linhas, titulo="ÍNDICE DAS PRANCHAS",
                        larguras=["15%", "68%", "17%"], classes=["c", "", "c"])
    res = []
    for forma, cod, nome, elem, jogo in FORMAS:
        ps = [p for p in pecas.values() if p.forma == forma]
        res.append([cod, nome, elem, jogo, len(ps), sum(p.qtd for p in ps),
                    kg0(sum(p.peso * p.qtd for p in ps))])
    total = sum(p.peso * p.qtd for p in pecas.values())
    res.append([fl.Bruto("<b>TOTAL</b>"), "", "", "", len(pecas),
                sum(p.qtd for p in pecas.values()), fl.Bruto(f"<b>{kg0(total)}</b>")])
    tab_res = fl.tabela(["FÔRMA", "DESCRIÇÃO", "ELEMENTO MOLDADO", "JOGO", "MARCAS", "PEÇAS",
                         "AÇO (kg)"], res, titulo="QUADRO-RESUMO DAS FÔRMAS",
                        classes=["c", "", "", "", "n", "n", "n"])
    tab_mat = fl.tabela(["ITEM", "ESPECIFICAÇÃO"], [[a, b] for a, b in MATERIAIS],
                        titulo="ESPECIFICAÇÃO DE MATERIAIS", larguras=["26%", "74%"])
    conteudo = (fl.bloco(4, 4, 200, 269, f'<div class="pilha">{tab_ind}'
                         f'{fl.notas("NOTAS GERAIS", NOTAS_GERAIS)}</div>')
                + fl.bloco(210, 4, 176, 206, f'<div class="pilha">{tab_mat}{convencoes()}'
                           f'{tab_res}</div>'))
    doc.folha("ÍNDICE, NOTAS GERAIS E ESPECIFICAÇÕES", "SEM ESCALA", conteudo)


def folha_parametros(doc, pecas):
    lin = []
    for t, d in gf.DOBRA.items():
        marcas = [p.codigo for p in pecas.values() if p.t == t and p.linhas]
        _, ba = gf.dados_dobra(t, 90)
        lin.append([f"{gf.fmt_t(t)}", f1(d["ri"]), f"{d['k']:.2f}".replace(".", ","), d["v"],
                    f1(gf.ABA_MINIMA_FATOR * d["v"]), f1(ba),
                    f1(gf.forca_dobra_tf(t, 1000)), ", ".join(marcas)])
    tab_par = fl.tabela(["ESPESSURA (mm)", "RAIO INTERNO", "FATOR K", "ABERTURA DO V",
                         "ABA MÍNIMA", "DESENVOLVIMENTO A 90°", "FORÇA POR METRO (tf/m)",
                         "MARCAS DOBRADAS"], lin, titulo="PARÂMETROS DE DOBRA ADOTADOS",
                        classes=["c", "n", "n", "n", "n", "n", "n", ""])
    expr = fl.notas("EXPRESSÕES DE CÁLCULO", [
        "Desenvolvimento da dobra: BA = θ × (Ri + K × e), com θ em radianos, Ri o raio interno "
        "e e a espessura.",
        "Recuo externo: OSSB = (Ri + e) × tg(θ/2). Trecho reto da planificação = medida externa "
        "da aba menos os recuos das dobras adjacentes.",
        "Força de dobra no ar: F = 1,42 × Rm × e² × L / V, com Rm = 450 MPa (aço-carbono de "
        "referência), L o comprimento de dobra e V a abertura da matriz.",
        "Aba mínima igual a 0,7 V. Centro de furo a pelo menos 1,5 diâmetro da borda; borda de "
        "furo a pelo menos BA/2 + 2e do eixo da dobra.",
        "Uso máximo admitido da dobradeira: 85% da capacidade nominal.",
    ])
    equip = fl.notas("EQUIPAMENTOS DE FABRICAÇÃO", [
        "Corte: máquina de corte a laser de fibra, potência aproximada de 3 kW, conforme o "
        "resfriador S&A CWFL-3000 instalado; recebe arquivos DXF.",
        "Dobra: dobradeira com comprimento útil de 3000 mm, do mesmo fabricante da máquina de "
        "corte; capacidade nominal e ferramental a confirmar pela placa de identificação e pela "
        "tabela de dobra do fabricante.",
        "Nenhuma peça tem dobra com comprimento superior a 3000 mm.",
    ])
    adeq = []
    for cap in CAPACIDADES:
        alter, sem = [], []
        for p in pecas.values():
            if not p.linhas:
                continue
            v = gf.matriz_para_capacidade(p, cap)
            if v is None:
                sem.append(p.codigo)
            elif v != gf.DOBRA[p.t]["v"]:
                alter.append(f"{p.codigo} V{v}")
        adeq.append([f"{cap} tf", f1(cap * gf.DOBRADEIRA["uso_maximo"]),
                     ", ".join(alter) or "NENHUMA ALTERAÇÃO", ", ".join(sem) or "–"])
    tab_adeq = fl.tabela(["CAPACIDADE NOMINAL", "FORÇA ADMITIDA (tf)", "MARCAS COM MATRIZ "
                          "ALTERADA", "MARCAS SEM MATRIZ VIÁVEL"], adeq,
                         titulo="ADEQUAÇÃO DA MATRIZ À CAPACIDADE DA DOBRADEIRA",
                         classes=["c", "n", "", ""], larguras=["16%", "14%", "48%", "22%"])
    obs_adeq = fl.notas(None, [
        "Matriz de abertura maior aumenta o raio interno e altera a planificação: a adoção de "
        "matriz diferente da indicada exige regeneração dos arquivos de corte.",
        "Marca sem matriz viável: alterar a espessura da chapa ou dividir a peça, com revisão "
        "do projeto da fôrma.",
    ], numerar=False)
    esf = []
    for p in pecas.values():
        if not p.linhas:
            continue
        f = gf.forca_dobra_tf(p.t, p.comprimento)
        esf.append([p.codigo, gf.fmt_t(p.t), f1(p.comprimento), gf.DOBRA[p.t]["v"],
                    len(p.linhas), f1(f), f1(f / gf.DOBRADEIRA["uso_maximo"])])
    tab_esf = fl.tabela(["MARCA", "ESPESSURA (mm)", "COMPRIMENTO DE DOBRA", "ABERTURA DO V",
                         "DOBRAS", "FORÇA (tf)", "CAPACIDADE NECESSÁRIA (tf)"], esf,
                        titulo="QUADRO DE ESFORÇOS DE DOBRA",
                        classes=["c", "c", "n", "n", "n", "n", "n"])
    conteudo = (fl.bloco(4, 4, 200, 269, f'<div class="pilha">{tab_par}{expr}{equip}{tab_adeq}'
                         f'{obs_adeq}</div>')
                + fl.bloco(210, 4, 176, 206, f'<div class="pilha">{tab_esf}</div>'))
    doc.folha("PARÂMETROS DE CORTE E DOBRA E ESFORÇOS DE DOBRA", "SEM ESCALA", conteudo)


# --------------------------------------------------------------------------
# CONJUNTOS
# --------------------------------------------------------------------------
def lista_materiais(pecas, forma, extras, titulo):
    lin = []
    for p in pecas.values():
        if p.forma != forma:
            continue
        lin.append([p.codigo, U(p.nome), gf.fmt_t(p.t), p.qtd,
                    f"{f1(p.comprimento)} × {f1(p.largura)}", kg(p.peso), kg(p.peso * p.qtd)])
    total = sum(p.peso * p.qtd for p in pecas.values() if p.forma == forma)
    lin.append(["", fl.Bruto("<b>MASSA TOTAL DE AÇO EM CHAPA</b>"), "", "", "", "",
                fl.Bruto(f"<b>{kg(total)}</b>")])
    for desc, q, un in extras:
        qt = f"{f1(q) if isinstance(q, float) else q} {UNIDADES[un]}" if un != "conforme consumo" \
            else "CONFORME CONSUMO"
        lin.append(["", U(desc), "", qt, "", "", ""])
    return fl.tabela(["MARCA", "DESCRIÇÃO", "CHAPA (mm)", "QUANT.", "PLANIFICAÇÃO (mm)",
                      "MASSA UNIT. (kg)", "MASSA TOTAL (kg)"], lin, titulo=titulo,
                     classes=["c", "", "c", "c", "c", "n", "n"])


def quadro_soldas(linhas):
    return fl.tabela(["LIGAÇÃO", "TIPO", "PERNA", "EXTENSÃO", "POSIÇÃO"], linhas,
                     titulo="QUADRO DE SOLDAS", classes=["", "c", "c", "", ""])


def compras(*chaves):
    out = []
    for desc, q, un in gf.lista_de_compras():
        if any(k in desc for k in chaves):
            out.append((desc, q, un))
    return out


def folha_conjunto_longarina(doc, pecas):
    sec = fl.vista(dz.secao_forma_longarina(10), "SEÇÃO TRANSVERSAL DA FÔRMA", "1:10")
    pla = fl.vista(dz.modulos_longarina(50), "PLANTA DE MODULAÇÃO", "1:50")
    lm = lista_materiais(pecas, "Longarina", compras("longarina"),
                         "LISTA DE MATERIAIS – 1 JOGO (4 MÓDULOS DE 2500)")
    soldas = quadro_soldas([
        ["F-LON-02 EM F-LON-01", "FILETE", "4 mm", "INTERMITENTE 50 mm A CADA 150 mm, NAS DUAS "
         "ABAS", "FACE POSTERIOR"],
        ["F-LON-03 EM F-LON-01", "FILETE", "4 mm", "CONTÍNUA", "FACE POSTERIOR"],
        ["F-LON-04 EM F-LON-01", "FILETE", "5 mm", "CONTORNO COMPLETO", "ABA SUPERIOR"],
        ["F-LON-06 EM F-LON-05", "FILETE", "4 mm", "CONTÍNUA", "FACE INFERIOR"],
        ["F-LON-07 EM F-LON-05", "FILETE", "4 mm", "INTERMITENTE 50 mm A CADA 150 mm", "FACE "
         "INFERIOR"],
    ])
    mont = fl.notas("SEQUÊNCIA DE MONTAGEM", [
        "Assentar os quatro fundos F-LON-05 sobre base de concreto nivelada, com tolerância de "
        "2 mm, e aparafusar as cantoneiras F-LON-06 entre módulos (3 parafusos M16 por junta).",
        "Fixar o perfil de chanfro de 20 mm sobre o fundo, ao longo das duas faces da viga.",
        "Posicionar os painéis F-LON-01 na largura da viga e fixar a aba de base com 4 parafusos "
        "M16 por painel, pelos rasgos do fundo.",
        "Aparafusar os painéis entre si pelas cantoneiras F-LON-03 (5 parafusos M16 por junta).",
        "Fechar as extremidades com as testeiras F-LON-08 (10 parafusos M16 em cada uma) e "
        "travar o topo com 4 tirantes de 5/8\" por módulo, pelas orelhas F-LON-04.",
        "Conferir largura, prumo, alinhamento e diagonais antes da concretagem.",
    ])
    obs = fl.notas("NOTAS", [
        "Larguras de viga de 250 mm a 360 mm pelos rasgos do fundo; a testeira é específica de "
        "cada largura. Altura de viga até 1000 mm.",
        "Viga de 5000 mm com 2 módulos e testeiras na mesma fôrma.",
    ])
    conteudo = (fl.bloco(4, 4, 150, 166, sec)
                + fl.bloco(160, 4, 226, 52, pla)
                + fl.bloco(160, 60, 226, 80, lm)
                + fl.bloco(160, 143, 226, 32, soldas)
                + fl.bloco(4, 178, 202, 95, f'<div class="pilha">{mont}{obs}</div>'))
    doc.folha("FÔRMA DA LONGARINA – CONJUNTO", "INDICADAS", conteudo)


def folha_conjunto_placa(doc, pecas):
    sec = fl.vista(dz.secao_forma_placa(5), "SEÇÃO TRANSVERSAL DA FÔRMA", "1:5")
    lm = lista_materiais(pecas, "Placa de saia", compras("placa"),
                         "LISTA DE MATERIAIS – 3 FÔRMAS")
    soldas = quadro_soldas([
        ["F-PLA-02 EM F-PLA-01", "FILETE", "4 mm", "INTERMITENTE 50 mm A CADA 150 mm, NAS DUAS "
         "ABAS", "FACE INFERIOR"],
    ])
    mont = fl.notas("SEQUÊNCIA DE MONTAGEM", [
        "Soldar as quatro nervuras F-PLA-02 sob o fundo F-PLA-01, nas linhas gravadas "
        "(275, 825, 1375 e 1925 mm).",
        "Assentar o fundo sobre base nivelada e fixar o perfil de chanfro de 20 mm no contorno "
        "da placa.",
        "Aparafusar os trilhos longitudinais F-PLA-03 de extremidade a extremidade e os trilhos "
        "transversais F-PLA-04 entre eles (16 parafusos M16 por fôrma).",
        "Fixar os tubos-fôrma de 50 mm nos furos de 14 mm: dois para içamento e um para dreno.",
    ])
    obs = fl.notas("NOTAS", [
        "A placa é moldada com a face aparente sobre o fundo; essa face fica voltada para o curso "
        "d'água e é também a face tracionada pelo empuxo: armadura principal junto ao fundo, "
        "conforme projeto estrutural.",
        "Com 3 fôrmas, as 24 placas da obra são moldadas em 8 ciclos de concretagem.",
    ])
    conteudo = (fl.bloco(4, 4, 206, 98, sec)
                + fl.bloco(216, 4, 170, 120, lm)
                + fl.bloco(216, 128, 170, 30, soldas)
                + fl.bloco(4, 108, 206, 165, f'<div class="pilha">{mont}{obs}</div>'))
    doc.folha("FÔRMA DA PLACA DE SAIA – CONJUNTO", "INDICADA", conteudo)


LEG_PLANTA_PAINEL = [
    "NICHO PARA LIGAÇÃO COM A LONGARINA, 200 × 250 NA BASE E 220 × 270 NO TOPO",
    "INSERTO DE IÇAMENTO, 4 POR PAINEL",
    "INSERTO DE NIVELAMENTO, 2 POR LONGARINA",
    "CHAVE DE CISALHAMENTO FÊMEA NAS BORDAS DE 4500",
    "FAIXA DO GUARDA-RODAS",
    "EIXO DA LONGARINA",
    "JUNTA DOS MÓDULOS DO FUNDO DA FÔRMA",
    "ESPERA DO GUARDA-RODAS",
]


def folha_conjunto_painel(doc, pecas):
    P = gf.PAINEL
    pla = fl.vista(dz.planta_painel(P, 20), "PLANTA DO PAINEL E DA FÔRMA", "1:20")
    cor = fl.vista(dz.secao_forma_painel(P, 10), "CORTE DA FÔRMA NA LINHA DOS NICHOS", "1:10")
    leg = fl.tabela(["Nº", "INDICAÇÃO"], [[i + 1, t] for i, t in enumerate(LEG_PLANTA_PAINEL)],
                    titulo="LEGENDA DA PLANTA", classes=["c", ""], larguras=["10%", "90%"])
    notas_p = fl.notas("NOTAS", [
        "Painel de 4500 × 1230 × 200 em módulo de 1250 ao longo da ponte, com junta de 20 mm "
        "entre painéis; 16 painéis na obra, moldados em 2 fôrmas.",
        "Fundo da fôrma em dois módulos iguais, intercambiáveis por giro de 180°; junta dos "
        "módulos no eixo do painel.",
        "Nichos sobre as longarinas preenchidos com graute na montagem, conforme projeto "
        "estrutural da ligação entre painel e longarina.",
        "Esperas do guarda-rodas posicionadas pela armadura do painel; não fazem parte da fôrma.",
    ])
    conteudo = (fl.bloco(4, 4, 280, 130, pla)
                + fl.bloco(290, 4, 96, 80, leg)
                + fl.bloco(4, 140, 200, 70, cor)
                + fl.bloco(210, 140, 176, 70, notas_p))
    doc.folha("FÔRMA DO PAINEL DE LAJE – CONJUNTO", "INDICADAS", conteudo)
    lm = lista_materiais(pecas, "Painel de laje", compras("painel", "nicho", "nivelamento",
                                                          "içamento"),
                         "LISTA DE MATERIAIS – 2 FÔRMAS")

    jun = fl.vista(dz.detalhe_junta(P, 5), "JUNTA ENTRE PAINÉIS", "1:5")
    soldas = quadro_soldas([
        ["F-LAJ-02 EM F-LAJ-01", "FILETE", "4 mm", "CONTÍNUA", "FACE INFERIOR"],
        ["F-LAJ-03 EM F-LAJ-01", "FILETE", "4 mm", "CONTÍNUA", "FACE INFERIOR"],
        ["F-LAJ-04 EM F-LAJ-01", "FILETE", "4 mm", "INTERMITENTE 50 mm A CADA 150 mm",
         "FACE INFERIOR"],
        ["F-LAJ-06 EM F-LAJ-05", "FILETE", "3 mm", "INTERMITENTE 40 mm A CADA 150 mm, NAS "
         "DUAS ABAS", "FACE DE CONCRETO, ESMERILHAR"],
        ["F-LAJ-08 COM F-LAJ-09", "FILETE", "3 mm", "CONTÍNUA NAS ARESTAS", "LADO INTERNO"],
        ["F-LAJ-10 EM F-LAJ-08", "FILETE", "4 mm", "CONTÍNUA", "LADO INTERNO"],
        ["PORCA M12 EM F-LAJ-01", "FILETE", "4 mm", "CONTORNO DA PORCA", "FACE INFERIOR"],
    ])
    mont = fl.notas("SEQUÊNCIA DE MONTAGEM", [
        "Soldar sob cada fundo F-LAJ-01 as cantoneiras F-LAJ-02 e F-LAJ-03, as nervuras F-LAJ-04 "
        "nas linhas gravadas e as quatro porcas M12 sob os furos de 14 mm.",
        "Assentar os dois módulos do fundo sobre base de concreto nivelada, com tolerância de "
        "2 mm, o segundo girado 180°, e aparafusar as cantoneiras da junta (4 parafusos M16).",
        "Soldar a régua F-LAJ-06 na face de concreto de cada trilho F-LAJ-05, entre as linhas "
        "gravadas, com o topo do perfil a 25 mm da face.",
        "Fixar o perfil de chanfro de 15 mm junto às faces dos trilhos, no fundo e no topo.",
        "Aparafusar os quatro trilhos longitudinais F-LAJ-05 e os dois trilhos de extremidade "
        "F-LAJ-07 no fundo.",
        "Montar as oito fôrmas de nicho (F-LAJ-08, F-LAJ-09 e F-LAJ-10) com gaxeta de espuma na "
        "base e fixá-las com barra roscada M12 na porca sob o fundo.",
        "Instalar as réguas F-LAJ-11 a 900 mm e 3600 mm da borda, com os insertos de içamento, "
        "e fixar os oito insertos de nivelamento pelos furos do fundo.",
        "Concretar, sarrafear pelas abas superiores dos trilhos e deixar o topo com acabamento "
        "rugoso. Retirar as fôrmas de nicho no início da pega.",
    ])
    obs = fl.notas("NOTAS DA JUNTA", [
        "Junta de 20 mm entre painéis, com rebaixo de 25 mm em cada borda e chanfros de 15 mm: "
        "o conjunto forma chave de cisalhamento preenchida com graute sem retração.",
        "Vedação inferior com tarugo de espuma de 25 mm; extremidades da junta vedadas na borda "
        "da ponte antes do grauteamento.",
        "Sobre o tabuleiro: manta impermeabilizante e revestimento asfáltico de 50 mm.",
    ])
    conteudo = (fl.bloco(4, 4, 200, 102, jun)
                + fl.bloco(210, 4, 176, 206, f'<div class="pilha">{lm}{soldas}</div>')
                + fl.bloco(4, 108, 202, 165, f'<div class="pilha">{mont}{obs}</div>'))
    doc.folha("FÔRMA DO PAINEL DE LAJE – MONTAGEM, SOLDAS E JUNTA", "INDICADA", conteudo)


# --------------------------------------------------------------------------
# LISTAS GERAIS
# --------------------------------------------------------------------------
def folha_listas(doc, pecas):
    lin = []
    for p in pecas.values():
        lin.append([p.codigo, U(p.nome), gf.fmt_t(p.t), p.qtd,
                    f"{f1(p.comprimento)} × {f1(p.largura)}", len(p.linhas),
                    len(p.furos) + len(p.rasgos), kg(p.peso * p.qtd)])
    tab = fl.tabela(["MARCA", "DESCRIÇÃO", "CHAPA (mm)", "QUANT.", "PLANIFICAÇÃO (mm)",
                     "DOBRAS", "FUROS", "MASSA (kg)"], lin, titulo="LISTA GERAL DE CORTE",
                    classes=["c", "", "c", "c", "c", "c", "c", "n"])
    arq = []
    for p in pecas.values():
        arq.append([p.codigo, f"{p.codigo}_CORTE.dxf",
                    f"{p.codigo}_CORTE_E_GRAVACAO.dxf" if p.marcas else "–",
                    f"{p.codigo}_DESENHO.dxf"])
    tab_arq = fl.tabela(["MARCA", "CORTE", "CORTE E GRAVAÇÃO", "DESENHO (CONFERÊNCIA)"], arq,
                        titulo="RELAÇÃO DOS ARQUIVOS DIGITAIS", classes=["c", "", "", ""])
    comp = [[U(d), "–" if u == "conforme consumo" else (f1(q) if isinstance(q, float) else q),
             UNIDADES[u]] for d, q, u in gf.lista_de_compras()]
    tab_comp = fl.tabela(["ITEM", "QUANTIDADE", "UNIDADE"], comp,
                         titulo="ITENS COMERCIAIS E MATERIAIS DE CONSUMO",
                         classes=["", "c", "c"], larguras=["76%", "12%", "12%"])
    conteudo = (fl.bloco(4, 4, 200, 269, tab)
                + fl.bloco(210, 4, 176, 206, f'<div class="pilha">{tab_arq}</div>'))
    doc.folha("LISTA GERAL DE CORTE E ARQUIVOS DIGITAIS", "SEM ESCALA", conteudo)
    doc.folha("ITENS COMERCIAIS E MATERIAIS DE CONSUMO", "SEM ESCALA",
              fl.bloco(4, 4, 200, 269, tab_comp))


# --------------------------------------------------------------------------
# DETALHES DAS MARCAS
# --------------------------------------------------------------------------
# escala da planificação e da seção dobrada de cada marca
ESCALAS = {
    "F-LON-01": (10, 10), "F-LON-02": (5, 2), "F-LON-03": (5, 2), "F-LON-04": (2, 2),
    "F-LON-05": (10, 10), "F-LON-06": (5, 2), "F-LON-07": (5, 2), "F-LON-08": (10, 10),
    "F-PLA-01": (10, 10), "F-PLA-02": (5, 2), "F-PLA-03": (10, 5), "F-PLA-04": (5, 5),
    "F-LAJ-01": (10, 10), "F-LAJ-02": (10, 2), "F-LAJ-03": (5, 2), "F-LAJ-04": (5, 2),
    "F-LAJ-05": (10, 5), "F-LAJ-06": (10, 1), "F-LAJ-07": (5, 5), "F-LAJ-08": (5, 5),
    "F-LAJ-09": (5, 5), "F-LAJ-10": (2, 2), "F-LAJ-11": (5, 2),
}
LARGO, ESTREITO = 382, 202          # larguras dos blocos: faixa inteira ou à esquerda da legenda
TOPO, FUNDO_LARGO, FUNDO = 3, RY - 3, QH - 3
VAO = 4


def mede(pecas):
    """Altura do conteúdo de cada bloco de marca nas duas larguras possíveis."""
    corpo = []
    for cod, (ep, es) in ESCALAS.items():
        html_m = conteudo_marca(pecas[cod], ep, es)
        for w in (LARGO, ESTREITO):
            corpo.append(f'<div class="medir" id="{cod}-{w}" style="width:{w}mm;margin:0 0 8mm">'
                         f'{html_m}</div>')
    pagina = (f"<!doctype html><html><head><meta charset='utf-8'><style>{fl.CSS}</style></head>"
              f"<body>{''.join(corpo)}</body></html>")
    caminho = os.path.join(PASTA, "_medidas.html")
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(pagina)
    js = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mede_blocos.js")
    r = subprocess.run(["node", js, caminho], capture_output=True, text=True, check=True)
    os.remove(caminho)
    import json
    return json.loads(r.stdout)


def _arruma(medidas, cods):
    """Posições dos blocos de uma folha, ou None se não couberem: blocos de faixa inteira
    acima da legenda e, abaixo dela, blocos estreitos à esquerda."""
    ordem = sorted(cods)
    for tentativa in (ordem, sorted(ordem, key=lambda c: medidas[f"{c}-{ESTREITO}"][0]
                                    <= ESTREITO + 0.5)):
        y, estreito, pos = TOPO, False, []
        for cod in tentativa:
            hl = medidas[f"{cod}-{LARGO}"][1]
            we, he = medidas[f"{cod}-{ESTREITO}"]
            if not estreito and y + hl <= FUNDO_LARGO:
                pos.append((cod, 4, y, LARGO, hl))
                y += hl + VAO
            elif we <= ESTREITO + 0.5 and y + he <= FUNDO:
                pos.append((cod, 4, y, ESTREITO, he))
                y += he + VAO
                estreito = True
            else:
                break
        else:
            return pos
    return None


def monta_detalhes(pecas, medidas, codigos):
    """Distribui os blocos das marcas no menor número de folhas (busca exaustiva com poda);
    em cada folha, as marcas ficam em ordem de código."""
    melhor = [None]

    def busca(k, grupos):
        if melhor[0] is not None and len(grupos) >= len(melhor[0]):
            return
        if k == len(codigos):
            melhor[0] = [list(g) for g in grupos]
            return
        cod = codigos[k]
        for g in grupos:
            if _arruma(medidas, g + [cod]) is not None:
                g.append(cod)
                busca(k + 1, grupos)
                g.pop()
        if _arruma(medidas, [cod]) is None:
            raise SystemExit(f"bloco da marca {cod} não cabe na folha A3: reduzir a escala")
        grupos.append([cod])
        busca(k + 1, grupos)
        grupos.pop()

    busca(0, [])
    folhas = [_arruma(medidas, g) for g in melhor[0]]
    return sorted(folhas, key=lambda f: min(c for c, *_ in f))


def folha_detalhe(doc, pecas, itens):
    conteudo, escalas, cods = "", set(), []
    for cod, x, y, w, h in itens:
        p = pecas[cod]
        ep, es = ESCALAS[cod]
        conteudo += fl.bloco(x, y, w, h + 0.5, conteudo_marca(p, ep, es))
        escalas.add(ep)
        if p.linhas:
            escalas.add(es)
        if cod in VISTA_PARCIAL:
            escalas.add(VISTA_PARCIAL[cod][0])
        cods.append(cod)
    forma = U(next(n for f, c, n, *_ in FORMAS if f == pecas[cods[0]].forma))
    cods = sorted(cods)
    marcas = cods[0] if len(cods) == 1 else ", ".join(cods[:-1]) + " E " + cods[-1]
    termo = "DA MARCA" if len(cods) == 1 else "DAS MARCAS"
    esc_txt = "1:" + " E 1:".join(str(e) for e in sorted(escalas)) if len(escalas) < 3 \
        else "INDICADAS"
    doc.folha(f"{forma} – DETALHE {termo} {marcas}", esc_txt, conteudo)


def main():
    os.makedirs(PASTA, exist_ok=True)
    pecas = {p.codigo: p for p in gf.todas_as_pecas()}
    medidas = mede(pecas)
    doc = fl.Documento("A3", "FÔRMAS METÁLICAS DOS ELEMENTOS PRÉ-MOLDADOS", "FM",
                       "Fôrmas metálicas dos elementos pré-moldados")
    doc.folha("ÍNDICE, NOTAS GERAIS E ESPECIFICAÇÕES", "SEM ESCALA", "")
    folha_parametros(doc, pecas)
    conjuntos = {"Longarina": folha_conjunto_longarina, "Placa de saia": folha_conjunto_placa,
                 "Painel de laje": folha_conjunto_painel}
    for forma, *_ in FORMAS:
        conjuntos[forma](doc, pecas)
        cods = [c for c in ESCALAS if pecas[c].forma == forma]
        for itens in monta_detalhes(pecas, medidas, cods):
            folha_detalhe(doc, pecas, itens)
    folha_listas(doc, pecas)
    indice = [(doc.numero(i), t, e) for i, (t, e, _) in enumerate(doc.folhas, 1)]
    capa = fl.Documento("A3", doc.assunto, "FM", doc.titulo_html)
    folha_indice(capa, pecas, indice)
    doc.folhas[0] = capa.folhas[0]

    html_path = os.path.join(PASTA, "FM_formas_metalicas_A3.html")
    pdf_path = os.path.join(PASTA, "FM_formas_metalicas_A3.pdf")
    if fl.grava_e_imprime(doc, html_path, pdf_path):
        print("PDF:", pdf_path, f"({len(doc.folhas)} folhas)")
    js = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verifica_folhas.js")
    args = ["node", js, html_path] + (["--medidas"] if "--medidas" in sys.argv else [])
    r = subprocess.run(args, capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip()[:400])


if __name__ == "__main__":
    main()
