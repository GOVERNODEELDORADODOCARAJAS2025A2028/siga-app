#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memorial descritivo MD-01 (formato A4) da ponte pré-moldada de vão único de 10 m e das fôrmas
metálicas dos elementos pré-moldados.

Gera saida/pranchas/MD-01_memorial_descritivo.pdf. As quantidades, massas e estimativas são
calculadas a partir dos mesmos dados do gerador das fôrmas.

Uso:  python3 gerar_memorial.py      (rodar depois de gerar_formas.py)
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..",
                                "comum"))
import folhas as fl                       # noqa: E402
import gerar_formas as gf                 # noqa: E402

fl.configura(**gf.IDENTIFICACAO)

PASTA = os.path.join(gf.SAIDA, "pranchas")

CSS = """
@page{size:A4;margin:24mm 15mm 18mm 25mm}
*{box-sizing:border-box}
body{margin:0;font-family:"Liberation Sans",Arial,sans-serif;font-size:10pt;line-height:1.42;
  color:#000;text-align:justify;hyphens:auto}
h1{font-size:15pt;margin:0 0 2mm;text-align:left;letter-spacing:.01em}
h2{font-size:11pt;margin:7mm 0 2mm;text-transform:uppercase;letter-spacing:.02em;
  break-after:avoid}
h3{font-size:10pt;margin:4mm 0 1.5mm;break-after:avoid}
p{margin:0 0 2.2mm}
ol,ul{margin:0 0 2.5mm;padding-left:6mm}
li{margin:0 0 1.2mm}
table{border-collapse:collapse;width:100%;margin:1mm 0 3mm;break-inside:auto}
tr{break-inside:avoid}
th,td{border:.25mm solid #000;padding:.8mm 1.4mm;font-size:8.5pt;line-height:1.25;
  vertical-align:top;text-align:left;hyphens:manual}
th{font-weight:700;text-align:center;vertical-align:middle;background:#fff}
td.n{text-align:right;white-space:nowrap}
td.c{text-align:center}
caption{caption-side:top;text-align:left;font-weight:700;font-size:9pt;padding:0 0 1mm}
.capa{border:.5mm solid #000;padding:5mm 6mm;margin:0 0 6mm}
.capa .ent{display:flex;align-items:center;gap:4mm;border-bottom:.3mm solid #000;
  padding:0 0 3mm;margin:0 0 4mm;text-align:left}
.capa .ent img{height:17mm;width:auto;flex:0 0 auto}
.capa .ent .t{font-size:10.5pt;font-weight:700;letter-spacing:.02em;margin:0 0 .8mm}
.capa .ent .e{font-size:8.5pt;line-height:1.3}
.capa .s{font-size:10.5pt;font-weight:700;margin:0 0 3mm;text-align:left}
.capa table td{font-size:9pt}
.eq{font-family:"Liberation Serif","Times New Roman",serif;font-size:10.5pt;text-align:center;
  margin:1.5mm 0 2.5mm}
.obs{font-size:9pt}
"""

ORGAO = fl.PROPRIETARIO
REVISAO, _, REVISAO_TXT = fl.REVISOES[-1]
CABECALHO = (f"{ORGAO} &nbsp;|&nbsp; MEMORIAL DESCRITIVO MD-01 &nbsp;|&nbsp; REVISÃO {REVISAO} "
             f"&nbsp;|&nbsp; {fl.DATA}")


def num(v, casas=1):
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def tab(cab, linhas, titulo=None, classes=None, larguras=None):
    return fl.tabela(cab, linhas, titulo=titulo, classes=classes, larguras=larguras)


def estimativas():
    """Verificações expeditas do pré-dimensionamento (valores característicos)."""
    phi, gamma, q, H = 30.0, 18.0, 20.0, 4.76
    ka = (1 - math.sin(math.radians(phi))) / (1 + math.sin(math.radians(phi)))
    E = 0.5 * ka * gamma * H ** 2 + ka * q * H
    M = ka * gamma * H ** 3 / 6 + ka * q * H ** 2 / 2
    faixa = 2.17
    Mp = M * faixa
    Md = 1.4 * Mp
    d, fyd = 0.64, 500 / 1.15
    As = Md / (fyd * 1e3 * 0.9 * d) * 1e4            # cm²
    # reação de apoio da longarina mais carregada
    vao = 9.60
    g = 0.30 * 0.90 * 25 + 0.20 * 1.20 * 25 + 0.05 * 1.20 * 24 + 2 * 0.20 * 25 / 4
    Rg = g * vao / 2
    eixos = [0, 1.5, 3.0]
    Rv = sum(150 * (1 - x / vao) for x in eixos)
    a1 = (vao - 4.5) - ((vao ** 2 - 4.5 ** 2) / (2 * vao))      # trecho após o veículo
    a2 = 4.5 - 4.5 ** 2 / (2 * vao)                              # faixa ao lado do veículo
    Rp = 5 * 3.70 * a1 + 5 * (3.70 - 3.0) * a2
    coef = 1.35 * 1.05 * 1.25
    Rq = 0.5 * (Rv + Rp) * coef
    # flexão da longarina no meio do vão (eixo central do veículo no meio do vão)
    Mg = g * vao ** 2 / 8
    ordem = [vao / 4 * (1 - abs(x) / (vao / 2)) for x in (-1.5, 0, 1.5)]
    Mv = 150 * sum(ordem)
    Mql = 0.4 * Mv * 1.35 * 1.05
    Mk = Mg + Mql
    Mdl = 1.4 * Mk
    As_comp = Mdl / (fyd * 1e3 * 0.93) * 1e4          # seção composta com o painel
    As_iso = Mdl / (fyd * 1e3 * 0.75) * 1e4           # longarina isolada
    # placa de saia, fiada inferior, vão livre de 1,94 m entre ranhuras
    p_inf = ka * (gamma * H + q)
    Mpl = p_inf * 1.94 ** 2 / 8
    As_pl = 1.4 * Mpl / (fyd * 1e3 * 0.9 * 0.11) * 1e4
    return dict(ka=ka, E=E, M=M, faixa=faixa, Mp=Mp, Md=Md, As=As, g=g, Rg=Rg, Rv=Rv, Rp=Rp,
                coef=coef, Rq=Rq, R=Rg + Rq, sigma=(Rg + Rq) / (0.25 * 0.30) / 1000,
                Mg=Mg, Mv=Mv, Mql=Mql, Mk=Mk, Mdl=Mdl, As_comp=As_comp, As_iso=As_iso,
                p_inf=p_inf, Mpl=Mpl, As_pl=As_pl)


def main():
    os.makedirs(PASTA, exist_ok=True)
    pecas = gf.todas_as_pecas()
    es = estimativas()
    aco = {f: sum(p.peso * p.qtd for p in pecas if p.forma == f)
           for f in ("Longarina", "Placa de saia", "Painel de laje")}
    n_pecas = {f: sum(p.qtd for p in pecas if p.forma == f) for f in aco}
    n_marcas = {f: sum(1 for p in pecas if p.forma == f) for f in aco}
    vol_total = sum(v * q for _, _, _, v, q, _ in gf.KIT)
    max_f = max((gf.forca_dobra_tf(p.t, p.comprimento), p.codigo) for p in pecas if p.linhas)

    h = []
    h.append(f"""<div class="capa">
<div class="ent"><img src="{fl.LOGO_URI}" alt="Bandeira do Município de Eldorado do Carajás">
<div><div class="t">{fl.esc(ORGAO)}</div><div class="e">CNPJ {fl.CNPJ}</div>
<div class="e">{fl.esc(fl.ENDERECO)}</div></div></div>
<h1>MEMORIAL DESCRITIVO MD-01</h1>
<div class="s">PONTE EM CONCRETO PRÉ-MOLDADO COM VÃO ÚNICO DE 10,00 m E LARGURA DE 4,50 m –
ANTEPROJETO E FÔRMAS METÁLICAS DOS ELEMENTOS PRÉ-MOLDADOS</div>
{tab(None, [["PROPRIETÁRIO", f"{ORGAO}, CNPJ {fl.CNPJ}"],
            ["PREFEITO MUNICIPAL", fl.PREFEITO],
            ["LOCAL DA OBRA", fl.LOCAL], ["SITUAÇÃO", fl.SITUACAO],
            ["REVISÃO", f"{REVISAO} – {REVISAO_TXT}"], ["DATA", fl.DATA],
            ["RESPONSÁVEL TÉCNICO PELO PROJETO", "A DESIGNAR (CREA E ART A INFORMAR)"],
            ["ANÁLISE TÉCNICA", f"{fl.ANALISTA} – {fl.ANALISTA_REGISTRO}"]],
        larguras=["32%", "68%"])}
</div>""")

    h.append("<h2>1. Objeto</h2>")
    h.append("<p>Este memorial descreve o anteprojeto de uma ponte em concreto pré-moldado com "
             "vão único de 10,00 m e largura total de 4,50 m e o projeto das fôrmas metálicas, "
             "em chapa de aço cortada a laser e dobrada, destinadas à moldagem dos elementos "
             "pré-moldados da superestrutura e das saias das cabeceiras. Estabelece as "
             "premissas adotadas, a concepção estrutural, os elementos que compõem o sistema, "
             "as verificações preliminares, os critérios de fabricação das fôrmas e as "
             "condicionantes técnicas e legais para a execução.</p>")

    h.append("<h2>2. Documentos integrantes</h2>")
    h.append(tab(["DOCUMENTO", "CONTEÚDO", "FORMATO"], [
        ["AG-01", "Arranjo geral: corte longitudinal, seção transversal, cabeceira, planta do "
                  "pilar, quadro dos elementos pré-moldados e notas gerais", "A1"],
        ["FM-01 a FM-23", "Fôrmas metálicas: índice, notas e especificações; parâmetros de corte "
                          "e dobra; conjuntos, montagem e soldas; detalhe de cada marca; listas "
                          "gerais", "A3"],
        ["MD-01", "Memorial descritivo (este documento)", "A4"],
        ["Arquivos DXF", "Arquivos digitais de corte, de corte e gravação e de desenho de cada "
                         "marca, relacionados na prancha FM-22", "DXF R2000"],
        ["Tabelas", "Lista de corte, tabela de dobras, itens comerciais e quadro dos elementos "
                    "de concreto", "CSV"],
    ], classes=["c", "", "c"], larguras=["17%", "68%", "15%"]))

    h.append("<h2>3. Normas e legislação de referência</h2>")
    h.append(tab(["REFERÊNCIA", "ASSUNTO"], [
        ["ABNT NBR 7187:2021", "Projeto de pontes, viadutos e passarelas de concreto"],
        ["ABNT NBR 7188:2024", "Carga móvel rodoviária e de pedestres em pontes, viadutos, "
                               "passarelas e outras estruturas"],
        ["ABNT NBR 6118", "Projeto de estruturas de concreto"],
        ["ABNT NBR 9062:2017", "Projeto e execução de estruturas de concreto pré-moldado"],
        ["ABNT NBR 6122", "Projeto e execução de fundações"],
        ["ABNT NBR 6484", "Sondagem de simples reconhecimento com SPT"],
        ["ABNT NBR 15696:2009", "Fôrmas e escoramentos para estruturas de concreto"],
        ["ABNT NBR 19783", "Aparelhos de apoio de elastômero fretado"],
        ["ABNT NBR 16752:2020", "Desenho técnico: requisitos para apresentação em folhas de "
                                "desenho"],
        ["ABNT NBR 16861:2020", "Desenho técnico: requisitos para representação de linhas e "
                                "escrita"],
        ["AWS D1.1", "Soldagem estrutural de aço (procedimento de referência)"],
        ["Lei nº 5.194/1966", "Exercício das profissões de engenheiro e engenheiro-agrônomo "
                              "(arts. 13 e 14)"],
        ["Lei nº 6.496/1977", "Anotação de Responsabilidade Técnica (ART)"],
        ["Lei nº 14.133/2021", "Licitações e contratos administrativos (arts. 46, § 1º, 124 e "
                               "125)"],
        ["Lei nº 12.651/2012", "Proteção da vegetação nativa (art. 3º, VIII, b, e art. 8º)"],
        ["Lei nº 9.433/1997", "Política Nacional de Recursos Hídricos (art. 12, V)"],
    ], larguras=["27%", "73%"]))

    h.append("<h2>4. Premissas e dados de entrada</h2>")
    h.append(tab(["PARÂMETRO", "VALOR ADOTADO", "ORIGEM E SITUAÇÃO"], [
        ["Vão", "Vão único; longarina de 10,00 m e vão teórico de 9,60 m",
         "Definição do contratante"],
        ["Comprimento entre faces das cortinas", "10,10 m", "Calculado"],
        ["Abertura livre", "9,00 m entre as faces dos pilares das cabeceiras, sem apoio no "
                           "leito do curso d'água", "A verificar no estudo hidrológico"],
        ["Largura", "4,50 m, com pista de 3,70 m entre guarda-rodas (faixa única, tráfego "
                    "alternado)", "Definição do contratante"],
        ["Altura útil das cabeceiras", "4,76 m: 6 fiadas de placas (3,00 m), travessa (0,60 m) "
                                       "e cortina (1,16 m)", "Ajustada ao módulo das placas"],
        ["Apoios", "Duas cabeceiras, com 3 pilares cada", "Definição do contratante"],
        ["Carga móvel", "TB-450 (ABNT NBR 7188:2024)", "A confirmar pelo responsável técnico"],
        ["Materiais", "Concreto C30; aço CA-50", "A confirmar com a classe de agressividade"],
        ["Topografia, hidrologia e geotecnia", "Não disponíveis",
         "Condicionantes do projeto executivo"],
    ], larguras=["24%", "46%", "30%"]))
    h.append("<p class='obs'>As dimensões dos elementos de concreto resultam de "
             "pré-dimensionamento. Não constituem dimensionamento estrutural.</p>")

    h.append("<h2>5. Concepção estrutural</h2>")
    h.append("<p><b>Superestrutura.</b> Quatro longarinas pré-moldadas de 0,30 × 0,90 × "
             "10,00 m, espaçadas de 1,20 m, simplesmente apoiadas em oito aparelhos de apoio "
             "de elastômero fretado sobre as travessas das cabeceiras. Tabuleiro em oito painéis "
             "pré-moldados de "
             "espessura total de 0,20 m, com 4,50 m de comprimento e 1,23 m de largura em "
             "módulo de 1,25 m, ligados às longarinas por nichos preenchidos com graute e "
             "ligados entre si por juntas fêmea-fêmea grauteadas. Guarda-rodas pré-moldados em "
             "módulos de 2,50 m. Transversinas de apoio moldadas no local, uma em cada "
             "extremidade, da ordem de 0,6 m³ cada.</p>")
    h.append("<p><b>Mesoestrutura.</b> Sem apoio intermediário. Em cada cabeceira, travessa "
             "de 4,64 × 0,90 × 0,60 m sobre três pilares de seção 0,30 × 0,70 m, com a maior "
             "dimensão "
             "no sentido do empuxo, e ranhuras que recebem placas de saia de 2,00 × 0,50 × "
             "0,15 m; o conjunto forma a contenção do aterro. Cortinas e lajes de transição "
             "completam as cabeceiras.</p>")
    h.append("<p><b>Infraestrutura.</b> Nas cabeceiras, sapatas corridas segmentadas, com cálice "
             "para embutimento dos pilares e calcanhar sob o aterro, com dimensões dependentes "
             "da sondagem. Não há fundação no leito do curso d'água. A ligação "
             "pilar-sapata por cálice segue a ABNT NBR 9062:2017; o comprimento de embutimento "
             "de partida, de 1,10 m, deve ser verificado no projeto estrutural.</p>")

    h.append("<h2>6. Elementos pré-moldados</h2>")
    lin = []
    for cod, nome, dim, vol, qtd, forma in gf.KIT:
        lin.append([cod, nome, dim.replace(" x ", " × "), num(vol, 3),
                    num(vol * gf.CONCRETO_T_M3, 2), qtd, num(vol * qtd, 2), forma])
    lin.append([fl.Bruto("<b>TOTAL</b>"), "", "", "", "", "",
                fl.Bruto(f"<b>{num(vol_total, 1)}</b>"), ""])
    h.append(tab(["CÓDIGO", "ELEMENTO", "DIMENSÕES (m)", "VOLUME UNIT. (m³)", "MASSA UNIT. (t)",
                  "QUANT.", "VOLUME TOTAL (m³)", "FÔRMA"], lin,
                 classes=["c", "", "c", "n", "n", "c", "n", "c"]))
    h.append("<p class='obs'>Massas calculadas com peso específico de 25 kN/m³ para o concreto "
             "armado (ABNT NBR 6118). As fôrmas F-GUA, F-TRA, F-PIL, F-COR, F-SAP e F-LTR não "
             "integram este conjunto de pranchas.</p>")

    h.append("<h3>Compatibilização entre elementos</h3>")
    h.append("<ol>"
             "<li>Os nichos dos painéis ficam sobre o eixo de cada longarina (450, 1650, 2850 e "
             "4050 mm a partir da borda da ponte), a 312,5 mm + 625 mm × n ao longo da viga; os "
             "estribos que saem do topo das longarinas são agrupados nessas posições (16 grupos "
             "por viga).</li>"
             "<li>As alças de içamento das longarinas ficam dentro de um nicho ou são cortadas "
             "após a montagem, para não interferir com os painéis.</li>"
             "<li>Juntas de 20 mm entre painéis e junta da ordem de 50 mm entre o tabuleiro e "
             "cada cortina.</li>"
             "<li>Berço de graute da ordem de 20 mm entre o topo da longarina e o painel, contido "
             "por tiras de espuma nas bordas da viga; aparelho de apoio com calço da ordem de "
             "40 mm.</li>"
             "<li>Graute dos nichos, das juntas e dos cálices, transversinas de apoio e "
             "revestimento da pista executados no local.</li></ol>")

    h.append("<h2>7. Verificações preliminares</h2>")
    h.append("<p>Os valores a seguir são estimativas expeditas, em valores característicos, "
             "destinadas a orientar o pré-dimensionamento. Não substituem o cálculo estrutural "
             "e geotécnico do projeto executivo.</p>")
    h.append("<h3>7.1 Empuxo sobre a cabeceira</h3>")
    h.append(f"<p>Empuxo ativo de Rankine, com ângulo de atrito de 30° (Ka = "
             f"{num(es['ka'], 3)}), peso específico do aterro de 18 kN/m³, sobrecarga de 20 kPa "
             f"e altura de 4,76 m:</p>")
    h.append(f"<div class='eq'>E = ½·Ka·γ·H² + Ka·q·H = {num(es['E'])} kN/m &nbsp;&nbsp;&nbsp; "
             f"M = Ka·γ·H³/6 + Ka·q·H²/2 = {num(es['M'])} kN·m/m</div>")
    h.append(f"<p>Para o pilar intermediário de cada cabeceira, com faixa de influência de "
             f"{num(es['faixa'], 2)} m, o "
             f"momento na base resulta da ordem de {num(es['Mp'], 0)} kN·m (característico), "
             f"considerado o pilar em balanço sem travamento pelo tabuleiro. Com γf = 1,4, "
             f"Md = {num(es['Md'], 0)} kN·m; na seção de 0,30 × 0,70 m, com altura útil de 0,64 m, a armadura "
             f"de flexão estimada na face do aterro é da ordem de {num(es['As'], 0)} cm², o que "
             f"justifica o pilar-contraforte adotado em lugar de pilar de seção quadrada.</p>")
    h.append("<h3>7.2 Reação nos aparelhos de apoio</h3>")
    h.append(f"<p>Longarina mais carregada, vão teórico de 9,60 m. Carga permanente de "
             f"{num(es['g'])} kN/m (longarina, painel, revestimento e parcela do guarda-rodas), "
             f"com reação de {num(es['Rg'], 0)} kN. Carga móvel TB-450 posicionada junto ao apoio "
             f"({num(es['Rv'], 0)} kN dos eixos e {num(es['Rp'], 0)} kN da carga distribuída), "
             f"coeficientes CIV = 1,35, CNF = 1,05 e CIA = 1,25 (produto "
             f"{num(es['coef'], 3)}) e distribuição transversal pela regra da alavanca, com "
             f"fator de 0,5 para a longarina sob uma linha de rodas: reação de "
             f"{num(es['Rq'], 0)} kN. Reação característica total da ordem de "
             f"{num(es['R'], 0)} kN; com aparelho de 250 × 300 mm, tensão média de "
             f"{num(es['sigma'], 1)} MPa. Dimensões a confirmar conforme ABNT NBR 19783.</p>")
    h.append("<h3>7.3 Flexão da longarina</h3>")
    h.append(f"<p>Momento no meio do vão: carga permanente {num(es['Mg'], 0)} kN·m; carga móvel "
             f"com os três eixos do TB-450 centrados no vão ({num(es['Mv'], 0)} kN·m para o "
             f"veículo; desprezada a carga distribuída fora do veículo, de pequena contribuição "
             f"neste vão), coeficientes CIV = 1,35 e CNF = 1,05 e fator de distribuição de 0,4 por "
             f"longarina: {num(es['Mql'], 0)} kN·m. Momento característico total da ordem de "
             f"{num(es['Mk'], 0)} kN·m e de cálculo de {num(es['Mdl'], 0)} kN·m. A armadura "
             f"longitudinal estimada é da ordem de {num(es['As_comp'], 0)} cm², considerada a "
             f"seção composta com o painel, e de {num(es['As_iso'], 0)} cm² para a longarina "
             f"isolada; a ação conjunta depende do projeto da ligação pelos nichos.</p>")
    h.append("<h3>7.4 Flexão da placa de saia</h3>")
    h.append(f"<p>Na fiada inferior, com empuxo de {num(es['p_inf'])} kPa e vão livre de 1,94 m "
             f"entre ranhuras, o momento característico é da ordem de {num(es['Mpl'])} kN·m/m. "
             f"Na espessura de 0,15 m, com altura útil de 0,11 m, a armadura estimada é da ordem de "
             f"{num(es['As_pl'])} cm²/m, na face voltada para o curso d'água, que é a face "
             f"tracionada e a face apoiada no fundo da fôrma.</p>")
    h.append("<h3>7.5 Fundação das cabeceiras</h3>")
    h.append("<p>Para sapata corrida com 3,20 m de base no sentido do eixo, a tensão máxima no "
             "solo estimada é da ordem de 200 kPa a 260 kPa, valor que exige solo competente na "
             "cota de assentamento. A solução em sapata depende de sondagem SPT nas cabeceiras; "
             "em caso de solo de baixa capacidade, a fundação das cabeceiras deve ser em "
             "estacas.</p>")

    h.append("<h2>8. Fôrmas metálicas</h2>")
    h.append("<h3>8.1 Concepção</h3>")
    h.append("<p>As fôrmas são compostas por peças de chapa de aço-carbono de 3,00 mm, 4,75 mm "
             "e 6,30 mm, cortadas a laser e dobradas, com nervuras e cantoneiras soldadas e "
             "ligações aparafusadas com parafusos M16 entre módulos. Nenhuma dobra excede "
             "3000 mm, comprimento útil da dobradeira do fornecedor, e os módulos têm até "
             "2500 mm. Cada peça é identificada por marca, com planificação, seção dobrada, "
             "dobras e furos detalhados nas pranchas FM.</p>")
    lin = [
        ["F-LON", "Longarina P-01", "1 jogo de 4 módulos de 2500 mm (viga de 10,00 m; viga de "
                                    "5,00 m com 2 módulos); larguras de 250 mm a 360 mm; altura "
                                    "até 1000 mm", n_marcas["Longarina"], n_pecas["Longarina"],
         num(aco["Longarina"], 0)],
        ["F-PLA", "Placa de saia P-07", f"{gf.FORMAS_PLACA} fôrmas; 24 placas em "
                                        f"{-(-24 // gf.FORMAS_PLACA)} ciclos de concretagem",
         n_marcas["Placa de saia"], n_pecas["Placa de saia"], num(aco["Placa de saia"], 0)],
        ["F-LAJ", "Painel de laje P-02", f"{gf.FORMAS_PAINEL} fôrma; {gf.N_PAINEIS} painéis; "
                                         "fundo em 2 módulos intercambiáveis; chave de "
                                         "cisalhamento nas bordas; 8 nichos tronco-piramidais",
         n_marcas["Painel de laje"], n_pecas["Painel de laje"], num(aco["Painel de laje"], 0)],
    ]
    lin.append([fl.Bruto("<b>TOTAL</b>"), "", "", sum(n_marcas.values()), sum(n_pecas.values()),
                fl.Bruto(f"<b>{num(sum(aco.values()), 0)}</b>")])
    h.append(tab(["FÔRMA", "ELEMENTO", "CARACTERÍSTICAS", "MARCAS", "PEÇAS", "AÇO (kg)"], lin,
                 classes=["c", "", "", "c", "c", "n"], larguras=["9%", "17%", "46%", "9%", "9%",
                                                                "10%"]))
    h.append("<h3>8.2 Planificação e dobra</h3>")
    linhas_dobra = [[gf.fmt_t(t), gf.fmt(d["ri"]), f"{d['k']:.2f}".replace(".", ","), d["v"],
                     gf.fmt(gf.ABA_MINIMA_FATOR * d["v"])] for t, d in gf.DOBRA.items()]
    h.append("<p>As planificações são calculadas pela linha neutra, com desenvolvimento da "
             "dobra BA = θ·(Ri + K·e) e recuo externo OSSB = (Ri + e)·tg(θ/2), a partir das "
             "medidas externas das abas. Os parâmetros adotados são valores de referência para "
             "dobra no ar de aço-carbono e devem ser substituídos pelos da tabela do ferramental "
             "do fabricante antes da liberação:</p>")
    h.append(tab(["ESPESSURA (mm)", "RAIO INTERNO (mm)", "FATOR K", "ABERTURA DO V (mm)",
                  "ABA MÍNIMA (mm)"], linhas_dobra, classes=["c", "n", "n", "n", "n"]))
    h.append(f"<p>O gerador verifica, para cada peça, a distância dos furos às bordas e às "
             f"linhas de dobra, a aba mínima, o comprimento de dobra e, quando informada, a "
             f"capacidade da dobradeira, com uso máximo de 85% da capacidade nominal. A maior "
             f"força estimada é de {num(max_f[0])} tf, na marca {max_f[1]}, o que corresponde a "
             f"capacidade nominal mínima de {num(max_f[0] / 0.85, 0)} tf com as matrizes "
             f"indicadas. Para dobradeiras de menor capacidade, a prancha FM-02 indica as "
             f"matrizes alternativas; a troca de matriz altera o raio interno e exige a "
             f"regeneração dos arquivos de corte.</p>")
    h.append("<h3>8.3 Arquivos digitais e gravação a laser</h3>")
    h.append("<p>Para cada marca são fornecidos o arquivo de corte (contorno e furos), o "
             "arquivo de corte e gravação, quando há posição de solda a marcar, com as camadas "
             "CORTE e GRAVACAO, e o arquivo de desenho para conferência. Os arquivos estão em "
             "DXF R2000, unidade milímetro, com a peça vista pela face superior na mesa de "
             "corte. As linhas de gravação indicam o eixo das nervuras e os limites da régua da "
             "chave de cisalhamento.</p>")
    h.append("<h3>8.4 Fabricação, inspeção e uso</h3>")
    h.append("<ol>"
             "<li>Fabricar inicialmente um módulo-piloto de cada fôrma e realizar inspeção "
             "dimensional antes da fabricação do jogo completo.</li>"
             "<li>Tolerâncias das peças de chapa: corte e posição de furos ±0,5 mm; ângulo de "
             "dobra ±1°; abas ±1 mm. Fôrma montada: dimensões internas ±2 mm e diferença entre "
             "diagonais de cada módulo até 3 mm.</li>"
             "<li>Soldas por soldador qualificado, com procedimento de referência AWS D1.1, "
             "conforme quadros de solda das pranchas de conjunto. Faces de contato com o "
             "concreto isentas de solda, respingo e rebarba, com planeza de 2 mm em 2500 mm."
             "</li>"
             "<li>Arestas da longarina e da face aparente da placa com chanfro de 20 mm e bordas "
             "do painel com chanfro de 15 mm, por perfil triangular de PVC rígido.</li>"
             "<li>Aplicação de desmoldante e conferência de dimensões, prumo e diagonais antes "
             "de cada concretagem. Desforma e içamento conforme resistência do concreto "
             "especificada no projeto estrutural.</li>"
             "<li>Verificação estrutural das fôrmas conforme ABNT NBR 15696:2009, sob "
             "responsabilidade do responsável técnico.</li></ol>")

    h.append(f"<p>Ciclos de produção: com um jogo da fôrma da longarina, uma viga por ciclo "
             f"({gf.N_LONGARINAS} ciclos); com {gf.FORMAS_PLACA} fôrmas de placa, 24 placas em "
             f"{-(-24 // gf.FORMAS_PLACA)} ciclos; com {gf.FORMAS_PAINEL} fôrma de painel, "
             f"{gf.N_PAINEIS} painéis em {-(-gf.N_PAINEIS // gf.FORMAS_PAINEL)} ciclos.</p>")

    h.append("<h2>9. Sequência executiva</h2>")
    h.append("<ol>"
             "<li>Locação, sondagens, estudos topográfico e hidrológico e projeto executivo.</li>"
             "<li>Sapatas das cabeceiras; embutimento dos pilares nos cálices.</li>"
             "<li>Travessas e aparelhos de apoio.</li>"
             "<li>Montagem das longarinas e dos painéis de laje; grauteamento dos nichos e das "
             "juntas.</li>"
             "<li>Placas de saia, dreno e aterro compactado em camadas; cortinas e lajes de "
             "transição.</li>"
             "<li>Guarda-rodas, impermeabilização, revestimento asfáltico e proteção contra "
             "erosão.</li></ol>")
    h.append("<p>Elementos com massa superior a 6 t (longarinas, travessas e sapatas) exigem "
             "guindaste, com verificação da tabela de carga do equipamento no raio de trabalho "
             "real e plano de içamento.</p>")

    h.append("<h2>10. Condicionantes para a execução</h2>")
    h.append("<h3>10.1 Técnicas</h3>")
    h.append("<ol>"
             "<li>Projeto executivo completo, com dimensionamento estrutural, projeto de "
             "fundações, estudos hidrológico e hidráulico e verificação de socavação, sob "
             "responsabilidade de profissional habilitado, com ART.</li>"
             "<li>Confirmação, pelo fornecedor, do raio interno, do fator K e da abertura de "
             "matriz do ferramental, da capacidade nominal da dobradeira (placa de "
             "identificação), do formato de arquivo aceito e da função de gravação do "
             "equipamento de corte.</li>"
             "<li>Regeneração dos arquivos de corte com os dados confirmados e emissão das "
             "pranchas em revisão liberada para fabricação.</li></ol>")
    h.append("<h3>10.2 Legais e administrativas</h3>")
    h.append("<ol>"
             "<li>A realização da obra depende de projeto executivo, nos termos do art. 46, "
             "§ 1º, da Lei nº 14.133/2021, ressalvada a hipótese do art. 18, § 3º.</li>"
             "<li>A fabricação das fôrmas pelo fornecedor contratado pressupõe que o objeto do "
             "contrato abranja o serviço de corte e dobra. Se o contrato vigente abranger "
             "apenas o fornecimento de material, a inclusão do serviço depende de alteração "
             "contratual nos limites dos arts. 124 e 125 da Lei nº 14.133/2021 ou de nova "
             "contratação.</li>"
             "<li>Anotação de Responsabilidade Técnica do projeto, da fabricação das fôrmas e da "
             "execução da obra (Lei nº 6.496/1977).</li>"
             "<li>Intervenção em área de preservação permanente admitida nas hipóteses de "
             "utilidade pública, que incluem obras do sistema viário, mediante autorização do "
             "órgão ambiental competente (Lei nº 12.651/2012, art. 3º, VIII, b, e art. 8º).</li>"
             "<li>Outorga de direito de uso de recursos hídricos, ou sua dispensa, pelo órgão "
             "gestor competente, para a obra que interfere no curso d'água (Lei nº 9.433/1997, "
             "art. 12, V).</li></ol>")

    h.append("<h2>11. Responsabilidade técnica e análise</h2>")
    h.append("<p>Este memorial e as pranchas que o acompanham constituem anteprojeto elaborado a "
             "partir das premissas informadas pelo contratante. Os estudos, plantas e projetos "
             "de engenharia só têm valor jurídico quando seus autores forem profissionais "
             "habilitados, e os trabalhos gráficos devem conter a assinatura, o título "
             "profissional e o número do registro do signatário (Lei nº 5.194/1966, arts. 13 e "
             "14). O anteprojeto não substitui o projeto executivo, que deve ser elaborado e "
             "assinado por profissional legalmente habilitado, com a respectiva Anotação de "
             "Responsabilidade Técnica (Lei nº 6.496/1977, art. 1º).</p>")
    h.append(f"<p>O anteprojeto é submetido à análise técnica do Eng. {fl.ANALISTA_NOME}, "
             f"CREA-PA nº&nbsp;{fl.ANALISTA_CREA}, servidor do Município, matrícula "
             f"nº&nbsp;{fl.ANALISTA_MATRICULA}. A análise "
             f"técnica não transfere a autoria nem a responsabilidade técnica pelo projeto "
             f"executivo e é registrada no quadro a seguir e no campo próprio da legenda das "
             f"pranchas.</p>")
    vazio = fl.Bruto("<div style='height:22mm'></div>")
    h.append(tab(None, [
        ["PROFISSIONAL", fl.ANALISTA],
        ["REGISTRO", fl.ANALISTA_REGISTRO],
        ["DOCUMENTOS ANALISADOS", f"AG-01, FM-01 A FM-23 E MD-01, REVISÃO {REVISAO}"],
        ["PARECER E OBSERVAÇÕES", vazio],
        ["DATA", fl.Bruto("<div style='height:7mm'></div>")],
        ["ASSINATURA", fl.Bruto("<div style='height:14mm'></div>")],
    ], titulo="REGISTRO DA ANÁLISE TÉCNICA", larguras=["32%", "68%"]))

    html = ("<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'>"
            "<title>Memorial descritivo MD-01</title><style>" + CSS + "</style></head><body>"
            + "".join(h) + "</body></html>")
    html_path = os.path.join(PASTA, "MD-01_memorial_descritivo.html")
    pdf_path = os.path.join(PASTA, "MD-01_memorial_descritivo.pdf")
    if fl.grava_e_imprime(html, html_path, pdf_path, cabecalho=CABECALHO):
        print("PDF:", pdf_path)
    print(f"estimativas: E = {es['E']:.1f} kN/m; M = {es['M']:.1f} kN·m/m; pilar "
          f"{es['Mp']:.0f} kN·m; As ≈ {es['As']:.1f} cm²; reação {es['R']:.0f} kN "
          f"(g {es['Rg']:.0f} + q {es['Rq']:.0f}); tensão {es['sigma']:.1f} MPa")


if __name__ == "__main__":
    main()
