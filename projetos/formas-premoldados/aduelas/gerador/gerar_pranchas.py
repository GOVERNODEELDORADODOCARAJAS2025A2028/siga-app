#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pranchas de fabricação das fôrmas metálicas das aduelas (formato A3), um conjunto por tamanho.

Gera saida/pranchas/FA<tamanho>_formas_aduela_<seção>_A3.pdf: índice e notas gerais,
parâmetros de corte e dobra, aduela (seção, corte longitudinal e quadro), encaixe e sua
moldagem, fôrma montada (planta e corte), base, anel superior e canto, montagem e lista de
materiais, detalhe de cada marca e listas gerais.

Uso:  python3 gerar_pranchas.py      (rodar depois de gerar_formas.py)
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import desenhos as dz                     # noqa: E402
import folhas as fl                       # noqa: E402
import gerar_formas as gf                 # noqa: E402

fl.configura(**gf.IDENTIFICACAO)

import pranchas as pr                     # noqa: E402
from pranchas import (H_DIR, RX, RY, Detalhamento, U, f1, folha_listas,  # noqa: E402
                      folha_parametros, imprime_e_verifica, kg, kg0, lista_materiais,
                      quadro_soldas)

PASTA = os.path.join(gf.SAIDA, "pranchas")

SUBCONJUNTOS = [
    ("Fôrma externa", "FÔRMA EXTERNA", "4 painéis, 4 cantos, cantoneiras, cintas e nervuras"),
    ("Núcleo", "NÚCLEO", "4 painéis, 4 cantos com mísula, cantoneiras, cintas e nervuras"),
    ("Base", "BASE", "chapa em catavento e ressalto que molda o macho"),
    ("Anel superior", "ANEL SUPERIOR", "chapa e barras da saia que moldam a bolsa"),
    ("Acessório", "ACESSÓRIO", "régua porta-inserto de içamento"),
]
SERIE = (1, 2, 5, 10, 20, 25, 50)


def escalas_marca(p):
    """Escalas da planificação e da seção dobrada: a maior da série que cabe no bloco. Peças
    pequenas (maior medida até 900 mm) ficam com a planificação mais baixa (até 80 mm de
    papel) e, até 400 mm, a partir de 1:5, para que vários blocos caibam em uma folha."""
    maior = max(p.comprimento, p.largura)
    minimo = 5 if maior <= 400 else 2
    altura = 110 if maior > 900 else 80
    ep = next(e for e in SERIE if e >= minimo and p.comprimento / e <= 330
              and p.largura / e <= altura)
    es = ep
    if p.linhas:
        w, h = dz.extensao_dobrada(p)
        es = next(e for e in SERIE if e >= 2 and w / e <= 70 and h / e <= 55)
    return ep, es


def tamanho_svg(svg):
    m = re.search(r'style="(?:overflow:hidden;)?width:([\d.]+)mm;height:([\d.]+)mm"', svg)
    return float(m.group(1)), float(m.group(2))


def ajusta(funcao, largura, altura, escalas, *args):
    """Desenho na maior escala da lista que cabe em largura × altura (mm de papel, já
    descontado o título da vista)."""
    for e in escalas:
        svg = funcao(*args, e) if not args else funcao(args[0], e, *args[1:])
        w, h = tamanho_svg(svg)
        if w <= largura and h <= altura:
            return svg, e
    raise SystemExit(f"{funcao.__name__}: desenho não cabe em {largura} × {altura} mm")


def nomes(cod):
    return {f: n for f, n, _ in SUBCONJUNTOS}


# --------------------------------------------------------------------------
# FOLHAS GERAIS
# --------------------------------------------------------------------------
def notas_gerais(a):
    F = f"F-{a['codigo']}"
    return [
        "Medidas em milímetros, salvo indicação em contrário. As cotas prevalecem sobre medidas "
        "tomadas no desenho; não medir em escala.",
        "Este conjunto é anteprojeto. A fabricação somente pode ser iniciada após: (a) aprovação "
        "da espessura das lajes e paredes, das mísulas, do encaixe, da armadura e dos insertos "
        "da aduela pelo responsável técnico do projeto estrutural, com ART registrada (Lei nº "
        "6.496/1977); (b) confirmação, pelo fabricante, do raio interno, do fator K e da "
        "abertura de matriz do ferramental e da capacidade nominal da dobradeira; (c) "
        "regeneração dos arquivos de corte com os dados confirmados; (d) fabricação do jogo e "
        "moldagem de uma aduela de prova, com conferência dimensional conforme ABNT NBR "
        "15396:2018.",
        "Moldagem na posição vertical, com o eixo da galeria na vertical: o macho é moldado pela "
        "base e a bolsa pelo anel superior. O painel externo e o painel do núcleo com furo do "
        f"tubo-fôrma ({F}-02 e {F}-09) ficam na mesma parede, que é a laje superior da aduela "
        "assentada.",
        "Planificações calculadas pela linha neutra, com os parâmetros de dobra da prancha 02. "
        "Abas cotadas pelas faces externas (linhas de molde).",
        "Planificações representadas pela face superior na mesa de corte, com origem das "
        "coordenadas no canto inferior esquerdo. Dobra para cima: face superior no lado interno "
        "da dobra. Dobra para baixo: face superior no lado externo da dobra.",
        "Furos de 18 mm para parafusos e barras M16.",
        "Linhas gravadas a laser indicam posições de solda e não são linhas de corte. Arquivos "
        "digitais em DXF R2000, unidade milímetro: arquivo de corte com contorno e furos; "
        "arquivo de corte e gravação com as camadas CORTE e GRAVACAO; arquivo de desenho, "
        "somente para conferência.",
        "Faces de contato com o concreto isentas de solda, respingo, marcação e rebarba, com "
        "planeza de 2 mm em 2500 mm; juntas soldadas em faces de contato esmerilhadas rente. "
        "Aplicar desmoldante antes de cada concretagem.",
        "Tolerâncias das peças de chapa: corte e posição de furos ±0,5 mm; ângulo de dobra ±1°; "
        "abas ±1 mm. Tolerâncias da fôrma montada: dimensões internas e externas ±2 mm, "
        "diferença entre diagonais até 3 mm e prumo das faces de 2 mm em 1065 mm.",
        "Soldagem por arco elétrico com eletrodo E7018 ou arame ER70S-6, por soldador "
        "qualificado, com procedimento de referência AWS D1.1, conforme o quadro de soldas.",
        "Verificação estrutural da fôrma (pressão do concreto fresco, deformações e ligações) "
        "conforme ABNT NBR 15696:2009, sob responsabilidade do responsável técnico; estimativa "
        "no memorial MD-02.",
        "Aduela, tolerâncias, inspeção e ensaios conforme ABNT NBR 15396:2018 e projeto "
        "estrutural. Os insertos de içamento são especificados no projeto estrutural.",
    ]


MATERIAIS = [
    ("CHAPAS", "Aço-carbono laminado a quente ASTM A36 ou SAE 1020, espessuras de 4,75 mm e "
               "6,30 mm, com certificado de usina."),
    ("PARAFUSOS", "Sextavados M16, classe 8.8 (ISO 898-1), com porcas e arruelas, zincados."),
    ("BARRA ROSCADA", "M16, aço SAE 1020, zincada, com porcas e arruelas."),
    ("CONSUMÍVEIS DE SOLDA", "Eletrodo E7018 (AWS A5.1) ou arame ER70S-6 (AWS A5.18)."),
    ("TUBO-FÔRMA", "Tubo de PVC rígido, diâmetro externo de 110 mm, com tampões centralizadores."),
    ("DESMOLDANTE", "Produto para fôrma metálica, compatível com o acabamento especificado."),
]


def folha_indice(doc, a, pecas, indice):
    F = f"F-{a['codigo']}"
    linhas = [[n_, t, e] for n_, t, e in indice]
    tab_ind = fl.tabela(["PRANCHA", "CONTEÚDO", "ESCALAS"], linhas, titulo="ÍNDICE DAS PRANCHAS",
                        larguras=["15%", "68%", "17%"], classes=["c", "", "c"])
    res = []
    for forma, nome, desc in SUBCONJUNTOS:
        ps = [p for p in pecas.values() if p.forma == forma]
        res.append([nome, U(desc), len(ps), sum(p.qtd for p in ps),
                    kg0(sum(p.peso * p.qtd for p in ps))])
    total = sum(p.peso * p.qtd for p in pecas.values())
    res.append([fl.Bruto("<b>TOTAL</b>"), f"1 JOGO PARA A ADUELA {a['titulo']} m", len(pecas),
                sum(p.qtd for p in pecas.values()), fl.Bruto(f"<b>{kg0(total)}</b>")])
    tab_res = fl.tabela(["SUBCONJUNTO", "COMPOSIÇÃO", "MARCAS", "PEÇAS", "AÇO (kg)"], res,
                        titulo="QUADRO-RESUMO DA FÔRMA", classes=["c", "", "n", "n", "n"],
                        larguras=["19%", "53%", "9%", "8%", "11%"])
    tab_mat = fl.tabela(["ITEM", "ESPECIFICAÇÃO"], [[x, y] for x, y in MATERIAIS],
                        titulo="ESPECIFICAÇÃO DE MATERIAIS", larguras=["26%", "74%"])
    conteudo = (fl.bloco(4, 4, 200, 269, f'<div class="pilha">{tab_ind}'
                         f'{fl.notas("NOTAS GERAIS", notas_gerais(a))}</div>')
                + fl.bloco(210, 4, 176, H_DIR, f'<div class="pilha">{tab_mat}'
                           f'{pr.convencoes(F + "-01")}{tab_res}</div>'))
    doc.folha("ÍNDICE, NOTAS GERAIS E ESPECIFICAÇÕES", "SEM ESCALA", conteudo)


# --------------------------------------------------------------------------
# ADUELA E ENCAIXE
# --------------------------------------------------------------------------
def quadro_aduela(a):
    v, massa, zc = gf.concreto(a)
    B, t, m = a["B"], a["t"], a["m"]
    lin = [
        ["SEÇÃO INTERNA (VÃO × ALTURA)", f"{B} × {B}"],
        ["ESPESSURA DAS LAJES E PAREDES", f"{t}"],
        ["SEÇÃO EXTERNA", f"{a['Be']} × {a['Be']}"],
        ["MÍSULAS INTERNAS", f"{m} × {m}"],
        ["COMPRIMENTO ÚTIL", f"{gf.L_UTIL}"],
        ["COMPRIMENTO TOTAL (COM O MACHO)", f"{gf.H_EXT}"],
        ["MACHO: COMPRIMENTO E LARGURA NA BASE", f"{gf.P_MACHO} E {f1(a['wm'])}"],
        ["BOLSA: PROFUNDIDADE E FACE NO FUNDO", f"{gf.P_BOLSA} E {f1(a['s0'])}"],
        ["VOLUME DE CONCRETO", f"{v:.3f} m³".replace(".", ",")],
        ["MASSA ESTIMADA (25 kN/m³)", f"{kg(massa * 1000)} kg"],
        ["FURO DE IÇAMENTO NA LAJE SUPERIOR", f"DIÂMETRO 110, A {gf.altura_icamento(a)} DA PONTA "
                                              f"DO MACHO"],
        ["CONCRETO E COBRIMENTO DE REFERÊNCIA", "C30; 40 mm"],
        ["COMPOSIÇÃO SINAPI DE REFERÊNCIA", a["sinapi"] if a["sinapi"] != "–"
         else "SEM COMPOSIÇÃO PARA ESTA SEÇÃO"],
    ]
    return fl.tabela(None, lin, titulo=f"QUADRO DA ADUELA {a['titulo']} m",
                     larguras=["58%", "42%"], classes=["", "c"])


def notas_aduela(a):
    return [
        "Aduela fechada de seção quadrada, em concreto armado pré-moldado, com mísulas nos "
        "quatro cantos internos e encaixe tipo macho e fêmea, conforme ABNT NBR 15396:2018.",
        "Espessura, mísulas e encaixe de pré-dimensionamento, compatíveis com as composições de "
        "referência do SINAPI para aduelas fechadas com carga TB-45 e concreto de 30 MPa. "
        "Armadura, cobrimento, altura de aterro admissível e insertos definidos no projeto "
        "estrutural.",
        "Furo de içamento na laje superior, no centro de gravidade da peça, formado pelo "
        "tubo-fôrma de PVC; vedado com argamassa após o assentamento.",
        "Massa estimada com peso específico de 25 kN/m³ (ABNT NBR 6118), descontado o furo.",
    ]


def folha_aduela(doc, a):
    w_esq, w_dir = 196, 172
    sa, e1 = ajusta(dz.secao_aduela, w_esq, 186, (10, 20, 25), a)
    cl, e2 = ajusta(dz.corte_longitudinal, 92, RY - 16, (10, 20, 25), a)
    v1 = fl.vista(sa, "SEÇÃO TRANSVERSAL DA ADUELA", f"1:{e1}", "POSIÇÃO DE ASSENTAMENTO")
    v2 = fl.vista(cl, "CORTE LONGITUDINAL", f"1:{e2}", "PELO EIXO VERTICAL")
    conteudo = (fl.bloco(4, 4, 200, 200, v1)
                + fl.bloco(4, 207, 200, 66, quadro_aduela(a))
                + fl.bloco(210, 4, 96, RY - 6, v2)
                + fl.bloco(312, 4, 74, RY - 6, fl.notas("NOTAS", notas_aduela(a))))
    esc = f"1:{e1}" if e1 == e2 else f"1:{min(e1, e2)} E 1:{max(e1, e2)}"
    doc.folha(f"ADUELA {a['titulo']} – SEÇÃO, CORTE LONGITUDINAL E QUADRO", esc, conteudo)


def folha_encaixe(doc, a):
    enc = fl.vista(dz.detalhe_encaixe(a, 2), "ENCAIXE MACHO E FÊMEA ENTRE ADUELAS", "1:2",
                   "LAJE SUPERIOR, ADUELAS ASSENTADAS")
    db = fl.vista(dz.detalhe_base(a, 5), "MOLDAGEM DO MACHO NA BASE", "1:5")
    da = fl.vista(dz.detalhe_anel(a, 5), "MOLDAGEM DA BOLSA NO ANEL SUPERIOR", "1:5")
    notas = fl.notas("NOTAS DO ENCAIXE", [
        f"Macho com {gf.P_MACHO} mm de comprimento e bolsa com {gf.P_BOLSA} mm de profundidade: "
        f"folga axial de {gf.P_BOLSA - gf.P_MACHO} mm no fundo da bolsa e folga radial de "
        f"{f1(a['folga_radial'])} mm na boca, preenchidas com argamassa de rejuntamento.",
        f"Faces do encaixe inclinadas: macho {gf.RECUO_MACHO} mm mais estreito na ponta e bolsa "
        f"{gf.RECUO_BOLSA} mm mais larga na boca, o que facilita a desforma e o acoplamento.",
        "Assentamento e rejuntamento conforme ABNT NBR 15645:2020 e projeto: cada aduela "
        "assentada deixa como extremidade livre a bolsa, onde se acopla o macho da aduela "
        "seguinte.",
    ])
    conteudo = (fl.bloco(4, 4, 200, 170, enc)
                + fl.bloco(4, 180, 200, 93, notas)
                + fl.bloco(210, 4, 176, 92, db)
                + fl.bloco(210, 100, 176, RY - 102, da))
    doc.folha(f"ADUELA {a['titulo']} – ENCAIXE E MOLDAGEM DO ENCAIXE", "1:2 E 1:5", conteudo)


# --------------------------------------------------------------------------
# FÔRMA MONTADA, BASE E ANEL SUPERIOR
# --------------------------------------------------------------------------
def folha_conjunto(doc, a, pecas):
    pf, e1 = ajusta(dz.planta_forma, 198, 255, (10, 20, 25), a)
    cf, e2 = ajusta(dz.corte_forma, 172, RY - 16, (5, 10, 20), a)
    v1 = fl.vista(pf, "PLANTA DA FÔRMA MONTADA", f"1:{e1}",
                  "CORTE HORIZONTAL NA ALTURA DO FURO DE IÇAMENTO")
    v2 = fl.vista(cf, "CORTE VERTICAL DA FÔRMA MONTADA", f"1:{e2}",
                  "PELO MEIO DO PAINEL DA LAJE SUPERIOR")
    conteudo = fl.bloco(4, 4, 200, 269, v1) + fl.bloco(210, 4, 176, RY - 6, v2)
    esc = f"1:{min(e1, e2)} E 1:{max(e1, e2)}" if e1 != e2 else f"1:{e1}"
    doc.folha(f"FÔRMA DA ADUELA {a['titulo']} – CONJUNTO", esc, conteudo)


def folha_base_anel(doc, a, pecas):
    pb, e1 = ajusta(dz.planta_base, 198, 255, (10, 20, 25, 50), a, pecas)
    pa, e2 = ajusta(dz.planta_anel, 172, 148, (10, 20, 25, 50), a, pecas)
    v1 = fl.vista(pb, "PLANTA DA BASE", f"1:{e1}", "CHAPAS EM CATAVENTO E RESSALTO")
    v2 = fl.vista(pa, "PLANTA DO ANEL SUPERIOR", f"1:{e2}", "VISTA DE CIMA")
    notas = fl.notas("NOTAS", [
        "Contornos tracejados na planta da base: face posterior da fôrma externa, face do macho "
        "na base e contorno do núcleo; na planta do anel, face do núcleo.",
        "Base soldada em peça única, assentada em piso de concreto nivelado (tolerância de "
        "2 mm) e fixada com 4 chumbadores M16; o ressalto molda o ombro e a face externa do "
        "macho.",
        "Anel superior soldado em peça única, apoiado nas cintas do núcleo e fixado com 12 "
        "parafusos M16; içamento por olhais M16 nos furos centrais.",
    ])
    conteudo = (fl.bloco(4, 4, 200, 269, v1) + fl.bloco(210, 4, 176, 158, v2)
                + fl.bloco(210, 166, 176, RY - 168, notas))
    doc.folha(f"FÔRMA DA ADUELA {a['titulo']} – BASE E ANEL SUPERIOR",
              f"1:{e1}" if e1 == e2 else f"1:{min(e1, e2)} E 1:{max(e1, e2)}", conteudo)


def folha_canto(doc, a):
    dc, e = ajusta(dz.detalhe_canto, 198, 255, (5, 10), a)
    v = fl.vista(dc, "DETALHE DO CANTO DA FÔRMA MONTADA", f"1:{e}",
                 "PLANTA, CANTO INFERIOR DIREITO, NA ALTURA DO FURO DE IÇAMENTO")
    F = lambda n_: f"F-{a['codigo']}-{n_:02d}"
    notas = fl.notas("NOTAS DO CANTO", [
        f"Fôrma externa: canto {F(3)} com abas internas iguais à espessura da parede, ligado aos "
        f"painéis {F(1)} e {F(2)} pelas cantoneiras {F(4)}, com 4 parafusos M16 por junta. As "
        f"juntas ficam no plano das faces internas das paredes.",
        f"Núcleo: canto {F(10)} com mísula, ligado aos painéis {F(8)} e {F(9)} pelas cantoneiras "
        f"{F(11)}, com 4 parafusos M16 por junta, apertados pelo lado interno.",
        "Faces das cantoneiras em contato plano, sem folga; vedar as juntas pelo lado do "
        "concreto com fita ou cordão de vedação.",
        "Desforma: a fôrma externa abre para fora (cantos na diagonal, painéis na direção "
        "normal à face) e o núcleo recolhe para o centro (painéis primeiro, cantos depois).",
    ])
    doc.folha(f"FÔRMA DA ADUELA {a['titulo']} – DETALHE DO CANTO", f"1:{e}",
              fl.bloco(4, 4, 200, 269, v) + fl.bloco(210, 4, 176, RY - 6, notas))


def folha_montagem(doc, a, pecas):
    F = lambda n_: f"F-{a['codigo']}-{n_:02d}"
    lm = []
    for forma, nome, _ in SUBCONJUNTOS:
        lm.append(lista_materiais(pecas, forma, [], f"LISTA DE MATERIAIS – {nome}"))
    soldas = quadro_soldas([
        [f"{F(7)} EM {F(1)} E {F(2)}", "FILETE", "4 mm", "INTERMITENTE 50 mm A CADA 150 mm, NAS "
         "DUAS ABAS", "FACE POSTERIOR"],
        [f"{F(4)} EM {F(1)}, {F(2)} E {F(3)}", "FILETE", "4 mm", "CONTÍNUA", "FACE POSTERIOR"],
        [f"{F(5)} E {F(6)} EM {F(1)} E {F(2)}", "FILETE", "4 mm", "CONTÍNUA", "FACE POSTERIOR"],
        [f"{F(14)} EM {F(8)} E {F(9)}", "FILETE", "4 mm", "INTERMITENTE 50 mm A CADA 150 mm, NAS "
         "DUAS ABAS", "FACE INTERNA DO NÚCLEO"],
        [f"{F(11)}, {F(12)} E {F(13)} EM {F(8)}, {F(9)} E {F(10)}", "FILETE", "4 mm", "CONTÍNUA",
         "FACE INTERNA DO NÚCLEO"],
        [f"{F(15)} EM {F(10)}", "FILETE", "4 mm", "CONTÍNUA", "LADO INTERNO"],
        [f"{F(16)} ENTRE SI", "TOPO, PENETRAÇÃO TOTAL", "–", "CONTÍNUA", "ESMERILHAR A FACE "
         "SUPERIOR"],
        [f"{F(18)} E {F(19)} EM {F(16)}; {F(17)} SOBRE AS BARRAS", "FILETE", "4 mm", "CONTÍNUA",
         "LADO OPOSTO AO CONCRETO"],
        [f"{F(20)} ENTRE SI; {F(21)} EM {F(20)}", "TOPO E FILETE", "4 mm", "CONTÍNUA",
         "ESMERILHAR AS FACES DE CONTATO"],
    ])
    mont = fl.notas("SEQUÊNCIA DE MONTAGEM E CONCRETAGEM", [
        "Limpar a base e aplicar desmoldante em todas as faces de contato.",
        f"Montar o núcleo sobre a base: cantos {F(10)} e painéis {F(8)} e {F(9)} ligados pelas "
        f"cantoneiras (4 parafusos M16 por junta) e cantoneiras de base aparafusadas na base.",
        "Posicionar a armadura com espaçadores de 40 mm, deixando a abertura do furo de "
        "içamento.",
        f"Fechar a fôrma externa: painéis {F(1)} e {F(2)} e cantos {F(3)} (4 parafusos M16 por "
        f"junta), com o painel {F(2)} na mesma parede do painel {F(9)}; aparafusar as "
        f"cantoneiras de base.",
        "Instalar o tubo-fôrma de 110 mm com a barra roscada M16 pelos furos dos painéis da laje "
        "superior. Conferir dimensões, prumo e diagonais.",
        "Concretar em camadas com vibração até o topo do núcleo, assentar o anel superior "
        "pressionado sobre o concreto e aparafusá-lo nas cintas do núcleo.",
        f"Completar a bolsa até o topo da fôrma externa, fixar os insertos de içamento com a "
        f"régua {F(22)} e sarrafear pelo topo da fôrma e da saia do anel.",
    ])
    desf = fl.notas("SEQUÊNCIA DE DESFORMA", [
        "Retirar o anel superior após o início da pega, levantando-o na vertical.",
        "Com a resistência de desforma especificada no projeto estrutural: soltar os parafusos "
        "das juntas e da base da fôrma externa, afastar os cantos na diagonal e os painéis na "
        "direção normal à face.",
        "Soltar as juntas e a base do núcleo pelo lado interno, recolher os painéis para o "
        "centro e retirar os cantos na diagonal.",
        "Içar a aduela pelos insertos do topo da bolsa e retirar o tubo-fôrma.",
    ])
    conteudo = (fl.bloco(4, 4, 200, 269, f'<div class="pilha">{"".join(lm)}{soldas}</div>')
                + fl.bloco(210, 4, 176, RY - 6, f'<div class="pilha">{mont}{desf}</div>'))
    doc.folha(f"FÔRMA DA ADUELA {a['titulo']} – MONTAGEM, SOLDAS E LISTA DE MATERIAIS",
              "SEM ESCALA", conteudo)


# --------------------------------------------------------------------------
# CONJUNTO DE UM TAMANHO
# --------------------------------------------------------------------------
def nome_arquivo(cod):
    """Nome dos arquivos do conjunto de pranchas de um tamanho, sem a extensão."""
    lado = gf.ADUELAS[cod]["B"] // 10
    return f"FA{cod[1:]}_formas_aduela_{lado}x{lado}cm_A3"


def gera(cod):
    a = gf.geometria(cod)
    os.makedirs(PASTA, exist_ok=True)
    pecas = {p.codigo: p for p in gf.todas_as_pecas(cod)}
    F = lambda n_: f"F-{cod}-{n_:02d}"
    gravacao = {F(1): f"eixos das nervuras {F(7)}", F(2): f"eixos das nervuras {F(7)}",
                F(8): f"eixos das nervuras {F(14)}", F(9): f"eixos das nervuras {F(14)}",
                F(16): f"linhas das barras {F(18)} e {F(19)}",
                F(20): f"linha da barra {F(21)}"}
    escalas = {c: escalas_marca(p) for c, p in pecas.items()}
    det = Detalhamento(escalas, nomes(cod), gravacao)
    medidas = det.mede(pecas, PASTA)
    prefixo = f"FA{cod[1:]}"
    doc = fl.Documento("A3", f"FÔRMAS METÁLICAS DA ADUELA {a['titulo']} m", prefixo,
                       f"Fôrmas metálicas da aduela {a['nome']}")
    doc.folha("ÍNDICE, NOTAS GERAIS E ESPECIFICAÇÕES", "SEM ESCALA", "")
    folha_parametros(doc, pecas)
    folha_aduela(doc, a)
    folha_encaixe(doc, a)
    folha_conjunto(doc, a, pecas)
    folha_base_anel(doc, a, pecas)
    folha_canto(doc, a)
    folha_montagem(doc, a, pecas)
    grupos = [(("Fôrma externa",), None), (("Núcleo",), None), (("Base",), None),
              (("Anel superior", "Acessório"), "ANEL SUPERIOR E ACESSÓRIO")]
    for formas, titulo in grupos:
        cods = [c for c in pecas if pecas[c].forma in formas]
        for itens in det.monta(medidas, cods):
            mistas = len({pecas[c].forma for c, *_ in itens}) > 1
            det.folha(doc, pecas, itens, titulo if mistas else None)
    folha_listas(doc, pecas, gf.lista_de_compras(cod))
    indice = [(doc.numero(i), t, e) for i, (t, e, _) in enumerate(doc.folhas, 1)]
    capa = fl.Documento("A3", doc.assunto, prefixo, doc.titulo_html)
    folha_indice(capa, a, pecas, indice)
    doc.folhas[0] = capa.folhas[0]
    nome = os.path.join(PASTA, nome_arquivo(cod))
    return imprime_e_verifica(doc, nome + ".html", nome + ".pdf", "--medidas" in sys.argv)


def main():
    ok = all([gera(cod) for cod in gf.ADUELAS])
    if not ok:
        raise SystemExit("verificação das folhas acusou problema")


if __name__ == "__main__":
    main()
