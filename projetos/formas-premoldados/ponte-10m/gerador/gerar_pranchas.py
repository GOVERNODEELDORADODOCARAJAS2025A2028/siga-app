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
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..",
                                "comum"))
import desenhos as dz                     # noqa: E402
import folhas as fl                       # noqa: E402
import gerar_formas as gf                 # noqa: E402

fl.configura(**gf.IDENTIFICACAO)

from pranchas import (H_DIR, RY, Detalhamento, folha_listas, folha_parametros,  # noqa: E402
                      imprime_e_verifica, kg0, lista_materiais, quadro_soldas)
import pranchas as pr                     # noqa: E402

PASTA = os.path.join(gf.SAIDA, "pranchas")

FORMAS = [
    ("Longarina", "F-LON", "FÔRMA DA LONGARINA", "LONGARINA P-01, 300 × 900 × 10000",
     "1 JOGO DE 4 MÓDULOS DE 2500"),
    ("Placa de saia", "F-PLA", "FÔRMA DA PLACA DE SAIA", "PLACA DE SAIA P-07, 2000 × 500 × 150",
     f"{gf.FORMAS_PLACA} FÔRMAS"),
    ("Painel de laje", "F-LAJ", "FÔRMA DO PAINEL DE LAJE", "PAINEL DE LAJE P-02, 4500 × 1230 × 200",
     f"{gf.FORMAS_PAINEL} FÔRMA" if gf.FORMAS_PAINEL == 1 else f"{gf.FORMAS_PAINEL} FÔRMAS"),
]

# --------------------------------------------------------------------------
# DETALHES DAS MARCAS
# --------------------------------------------------------------------------
GRAVACAO = {
    "F-LON-01": "eixos das nervuras F-LON-02",
    "F-LON-05": "eixos das nervuras F-LON-07",
    "F-PLA-01": "eixos das nervuras F-PLA-02",
    "F-LAJ-01": "eixos das nervuras F-LAJ-04",
    "F-LAJ-05": "limites da régua F-LAJ-06",
}
VISTA_PARCIAL = {"F-LAJ-06": (2, 200)}     # escala e comprimento da vista parcial
ARRANJO_COLUNA = {"F-LAJ-01"}      # vistas à esquerda e quadros empilhados à direita
GRUPOS_FUROS = {"F-LAJ-01": 3}

# escala da planificação e da seção dobrada de cada marca
ESCALAS = {
    "F-LON-01": (10, 10), "F-LON-02": (5, 2), "F-LON-03": (5, 2), "F-LON-04": (2, 2),
    "F-LON-05": (10, 10), "F-LON-06": (5, 2), "F-LON-07": (5, 2), "F-LON-08": (10, 10),
    "F-PLA-01": (10, 10), "F-PLA-02": (5, 2), "F-PLA-03": (10, 5), "F-PLA-04": (5, 5),
    "F-LAJ-01": (10, 10), "F-LAJ-02": (10, 2), "F-LAJ-03": (5, 2), "F-LAJ-04": (5, 2),
    "F-LAJ-05": (10, 5), "F-LAJ-06": (10, 1), "F-LAJ-07": (5, 5), "F-LAJ-08": (5, 5),
    "F-LAJ-09": (5, 5), "F-LAJ-10": (2, 2), "F-LAJ-11": (5, 2),
}

DET = Detalhamento(ESCALAS, {f: n for f, _, n, *_ in FORMAS}, GRAVACAO, VISTA_PARCIAL,
                   ARRANJO_COLUNA, GRUPOS_FUROS)


# --------------------------------------------------------------------------
# FOLHAS GERAIS
# --------------------------------------------------------------------------

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
                + fl.bloco(210, 4, 176, H_DIR, f'<div class="pilha">{tab_mat}{pr.convencoes('F-LON-01')}'
                           f'{tab_res}</div>'))
    doc.folha("ÍNDICE, NOTAS GERAIS E ESPECIFICAÇÕES", "SEM ESCALA", conteudo)


# --------------------------------------------------------------------------
# CONJUNTOS
# --------------------------------------------------------------------------


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
        "A mesma fôrma permite vigas de 5000 mm, com 2 módulos e as mesmas testeiras.",
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
                         f"LISTA DE MATERIAIS – {gf.FORMAS_PLACA} FÔRMAS")
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
        f"Com {gf.FORMAS_PLACA} fôrmas, as 24 placas da obra são moldadas em "
        f"{-(-24 // gf.FORMAS_PLACA)} ciclos de concretagem.",
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
        f"entre painéis; {gf.N_PAINEIS} painéis na obra, moldados em "
        f"{gf.FORMAS_PAINEL} fôrma, em {-(-gf.N_PAINEIS // gf.FORMAS_PAINEL)} ciclos.",
        "Fundo da fôrma em dois módulos iguais, intercambiáveis por giro de 180°; junta dos "
        "módulos no eixo do painel.",
        "Nichos sobre as longarinas preenchidos com graute na montagem, conforme projeto "
        "estrutural da ligação entre painel e longarina.",
        "Esperas do guarda-rodas posicionadas pela armadura do painel; não fazem parte da fôrma.",
    ])
    conteudo = (fl.bloco(4, 4, 280, 130, pla)
                + fl.bloco(290, 4, 96, 80, leg)
                + fl.bloco(4, 140, 200, 70, cor)
                + fl.bloco(210, 140, 176, RY - 142, notas_p))
    doc.folha("FÔRMA DO PAINEL DE LAJE – CONJUNTO", "INDICADAS", conteudo)
    lm = lista_materiais(pecas, "Painel de laje", compras("painel", "nicho"),
                         "LISTA DE MATERIAIS – 1 FÔRMA" if gf.FORMAS_PAINEL == 1 else
                         f"LISTA DE MATERIAIS – {gf.FORMAS_PAINEL} FÔRMAS")

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
                + fl.bloco(210, 4, 176, H_DIR, f'<div class="pilha">{lm}{soldas}</div>')
                + fl.bloco(4, 108, 202, 165, f'<div class="pilha">{mont}{obs}</div>'))
    doc.folha("FÔRMA DO PAINEL DE LAJE – MONTAGEM, SOLDAS E JUNTA", "INDICADA", conteudo)


def main():
    os.makedirs(PASTA, exist_ok=True)
    pecas = {p.codigo: p for p in gf.todas_as_pecas()}
    medidas = DET.mede(pecas, PASTA)
    doc = fl.Documento("A3", "FÔRMAS METÁLICAS DOS ELEMENTOS PRÉ-MOLDADOS", "FM",
                       "Fôrmas metálicas dos elementos pré-moldados")
    doc.folha("ÍNDICE, NOTAS GERAIS E ESPECIFICAÇÕES", "SEM ESCALA", "")
    folha_parametros(doc, pecas)
    conjuntos = {"Longarina": folha_conjunto_longarina, "Placa de saia": folha_conjunto_placa,
                 "Painel de laje": folha_conjunto_painel}
    for forma, *_ in FORMAS:
        conjuntos[forma](doc, pecas)
        cods = [c for c in ESCALAS if pecas[c].forma == forma]
        for itens in DET.monta(medidas, cods):
            DET.folha(doc, pecas, itens)
    folha_listas(doc, pecas, gf.lista_de_compras())
    indice = [(doc.numero(i), t, e) for i, (t, e, _) in enumerate(doc.folhas, 1)]
    capa = fl.Documento("A3", doc.assunto, "FM", doc.titulo_html)
    folha_indice(capa, pecas, indice)
    doc.folhas[0] = capa.folhas[0]

    html_path = os.path.join(PASTA, "FM_formas_metalicas_A3.html")
    pdf_path = os.path.join(PASTA, "FM_formas_metalicas_A3.pdf")
    imprime_e_verifica(doc, html_path, pdf_path, "--medidas" in sys.argv)


if __name__ == "__main__":
    main()
