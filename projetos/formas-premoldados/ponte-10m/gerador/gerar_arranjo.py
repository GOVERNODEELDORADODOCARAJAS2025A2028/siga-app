#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prancha de arranjo geral da ponte pré-moldada de vão único de 10 m (formato A1).

Gera saida/pranchas/AG-01_arranjo_geral_A1.pdf: corte longitudinal (1:50), seção transversal
do tabuleiro (1:25), cabeceira vista do curso d'água (1:50), planta do pilar com as ranhuras
(1:10), quadro dos elementos pré-moldados, notas gerais e convenções.

Uso:  python3 gerar_arranjo.py      (rodar depois de gerar_formas.py)
"""

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import desenhos as dz                     # noqa: E402
import folhas as fl                       # noqa: E402
import gerar_formas as gf                 # noqa: E402

PASTA = os.path.join(gf.SAIDA, "pranchas")

LEG_B1 = [
    "GUARDA-RODAS P-03, MÓDULOS DE 2,50 m",
    "PAINEL DE LAJE P-02, MÓDULO DE 1,25 m",
    "LONGARINA P-01, 0,30 × 0,90 m",
    "TRAVESSA P-04",
    "PILAR DE CABECEIRA P-05, EMBUTIDO NO CÁLICE DA SAPATA",
    "PLANO DAS PLACAS DE SAIA P-07, ATRÁS DO PLANO DE CORTE",
    "CORTINA P-08",
    "LAJE DE TRANSIÇÃO P-10",
    "SAPATA P-09, COM CALCANHAR SOB O ATERRO",
    "APARELHO DE APOIO DE ELASTÔMERO FRETADO",
    "ENROCAMENTO DE PROTEÇÃO CONTRA EROSÃO",
]
LEG_B2 = [
    "GUARDA-RODAS, BASE DE 0,40 m",
    "PAINEL DE LAJE, ESPESSURA DE 0,20 m",
    "LONGARINAS (4), ESPAÇAMENTO DE 1,20 m",
    "TRAVESSA 0,90 × 0,60 m",
    "PILARES (3 POR APOIO)",
    "NICHO GRAUTEADO SOBRE A LONGARINA",
    "APARELHO DE APOIO SOB CADA LONGARINA",
]
LEG_B3 = [
    "PILAR COM RANHURA (EM TRACEJADO)",
    "PLACA DE SAIA 2,00 × 0,50 m",
    "FURO DE DRENO (BARBACÃ)",
    "TRAVESSA",
    "CORTINA",
    "EXTREMIDADE DAS LONGARINAS",
    "SAPATA EM 3 SEGMENTOS",
    "CÁLICE EMBUTIDO (OCULTO)",
]

NOTAS = [
    "Cotas em metros, salvo indicação em contrário. Níveis referidos ao topo das sapatas das "
    "cabeceiras. Não medir em escala.",
    "Arranjo geral de anteprojeto, com peças de concreto em pré-dimensionamento. O projeto "
    "executivo compreende o dimensionamento estrutural (ABNT NBR 7187:2021, NBR 6118 e "
    "NBR 9062:2017), com carga móvel TB-450 (ABNT NBR 7188:2024), o projeto de fundações "
    "(ABNT NBR 6122) com base em sondagens SPT (ABNT NBR 6484) e os estudos topográfico e "
    "hidrológico, sob responsabilidade técnica com ART registrada (Lei nº 6.496/1977).",
    "Concreto C30 e aço CA-50 adotados no pré-dimensionamento. Classe de agressividade "
    "ambiental, cobrimentos e relação água/cimento definidos no projeto estrutural.",
    "Aparelhos de apoio de elastômero fretado conforme ABNT NBR 19783; dimensões de referência "
    "de 250 × 300 mm, a confirmar no projeto estrutural.",
    "Vão único, sem apoio no leito do curso d'água. Abertura livre de 9,00 m entre as faces "
    "dos pilares das cabeceiras; verificar a suficiência da seção de vazão no estudo "
    "hidrológico.",
    "Cota de máxima cheia, borda livre e proteção contra socavação das cabeceiras definidas "
    "por estudo hidrológico e hidráulico. O enrocamento indicado é esquemático.",
    "Cabeceiras com função de contenção do aterro: pilares-contraforte de 0,30 × 0,70 m e "
    "sapatas corridas segmentadas em pré-dimensionamento. Estabilidade ao tombamento e ao "
    "deslizamento e tensões no solo verificadas no projeto executivo.",
    "Drenagem do aterro junto às saias com material drenante e manta geotêxtil; placas de saia "
    "com furo de dreno.",
    "Ligação dos painéis às longarinas por nichos grauteados; juntas entre painéis grauteadas; "
    "impermeabilização e revestimento asfáltico sobre o tabuleiro.",
    "Intervenção em área de preservação permanente e no curso d'água sujeita a autorização do "
    "órgão ambiental (Lei nº 12.651/2012, art. 8º) e a outorga ou dispensa de outorga do órgão "
    "gestor de recursos hídricos (Lei nº 9.433/1997, art. 12, V).",
    "Fôrmas metálicas dos elementos pré-moldados detalhadas no conjunto de pranchas FM, "
    "formato A3.",
]


def legenda_numerada(titulo, itens):
    return fl.tabela(["Nº", "INDICAÇÃO"], [[i + 1, t] for i, t in enumerate(itens)],
                     titulo=titulo, classes=["c", ""], larguras=["9%", "91%"])


def quadro_elementos():
    lin = []
    vt, mt = 0.0, 0.0
    for cod, nome, dim, vol, qtd, forma in gf.KIT:
        massa = vol * gf.CONCRETO_T_M3
        lin.append([cod, nome.upper().replace(" M²", " m²").replace(",50 M", ",50 m"),
                    dim.replace(" x ", " × ").upper(), f"{vol:.3f}".replace(".", ","),
                    f"{massa:.2f}".replace(".", ","), qtd, f"{vol * qtd:.2f}".replace(".", ","),
                    forma])
        vt += vol * qtd
        mt += massa * qtd
    lin.append([fl.Bruto("<b>TOTAL</b>"), "", "", "", "", "",
                fl.Bruto(f"<b>{vt:.1f}</b>".replace(".", ",")), ""])
    return fl.tabela(["CÓDIGO", "ELEMENTO", "DIMENSÕES (m)", "VOLUME UNIT. (m³)",
                      "MASSA UNIT. (t)", "QUANT.", "VOLUME TOTAL (m³)", "FÔRMA"], lin,
                     titulo="QUADRO DOS ELEMENTOS PRÉ-MOLDADOS",
                     classes=["c", "", "c", "n", "n", "c", "n", "c"])


def convencoes():
    e = 50
    d = dz.Dwg(0, 175 * e, 0, 58 * e, 0, e)
    itens = [("soil", "SOLO NATURAL E ATERRO"), ("water", "CURSO D'ÁGUA"),
             ("cip", "CONCRETO MOLDADO NO LOCAL"), ("pm", "ELEMENTO PRÉ-MOLDADO"),
             ("pm2", "LONGARINA E PILAR PRÉ-MOLDADOS"), ("brg", "APARELHO DE APOIO")]
    z = 56 * e
    for cls, txt in itens:
        d.rect(2 * e, z - 6 * e, 26 * e, z - 1 * e, cls)
        d.text(31 * e, z - 4.4 * e, txt, anchor="start", cls="note")
        z -= 9 * e
    svg = d.svg("Convenções do arranjo geral", 300, "cv")
    return f'<div><div class="bloco-tit">CONVENÇÕES</div>{svg}</div>'


def main():
    os.makedirs(PASTA, exist_ok=True)
    doc = fl.Documento("A1", "ARRANJO GERAL", "AG", "Arranjo geral da ponte pré-moldada",
                       unidade="m, SALVO INDICAÇÃO")
    b1 = fl.vista(dz.corte_longitudinal(50), "CORTE LONGITUDINAL PELO EIXO DA PONTE", "1:50")
    b2 = fl.vista(dz.secao_transversal(25), "SEÇÃO TRANSVERSAL DO TABULEIRO SOBRE A TRAVESSA",
                  "1:25")
    b3 = fl.vista(dz.cabeceira_frontal(50), "CABECEIRA – VISTA PELO CURSO D'ÁGUA", "1:50")
    b4 = fl.vista(dz.planta_pilar(10), "PLANTA DO PILAR INTERMEDIÁRIO DA CABECEIRA", "1:10",
                  "RANHURAS E PLACAS DE SAIA ENCAIXADAS")
    direita = (f'<div class="pilha">{legenda_numerada("LEGENDA DO CORTE LONGITUDINAL", LEG_B1)}'
               f'{legenda_numerada("LEGENDA DA SEÇÃO TRANSVERSAL", LEG_B2)}'
               f'{legenda_numerada("LEGENDA DA CABECEIRA", LEG_B3)}{convencoes()}</div>')
    conteudo = (fl.bloco(4, 6, 420, 226, b1)
                + fl.bloco(432, 6, 192, 182, b4)
                + fl.bloco(632, 6, 175, 499, direita)
                + fl.bloco(4, 240, 262, 182, b2)
                + fl.bloco(272, 240, 150, 200, b3)
                + fl.bloco(432, 196, 192, 258, fl.notas("NOTAS GERAIS", NOTAS))
                + fl.bloco(4, 462, 600, 100, quadro_elementos()))
    doc.folha("ARRANJO GERAL – CORTE LONGITUDINAL, SEÇÃO TRANSVERSAL E CABECEIRA", "INDICADAS",
              conteudo)
    html_path = os.path.join(PASTA, "AG-01_arranjo_geral_A1.html")
    pdf_path = os.path.join(PASTA, "AG-01_arranjo_geral_A1.pdf")
    if fl.grava_e_imprime(doc, html_path, pdf_path):
        print("PDF:", pdf_path)
    js = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verifica_folhas.js")
    args = ["node", js, html_path] + (["--medidas"] if "--medidas" in sys.argv else [])
    r = subprocess.run(args, capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip()[:400])


if __name__ == "__main__":
    main()
