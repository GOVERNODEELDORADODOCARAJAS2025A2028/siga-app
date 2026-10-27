#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memorial descritivo MD-02 (formato A4) das aduelas de concreto armado pré-moldado de seção
quadrada (1,00 m, 2,00 m e 2,50 m) e das fôrmas metálicas de moldagem.

Gera saida/pranchas/MD-02_memorial_descritivo_aduelas.pdf. Volumes, massas, quantidades e
estimativas são calculados a partir dos mesmos dados do gerador das fôrmas.

Uso:  python3 gerar_memorial.py      (rodar depois de gerar_formas.py e gerar_pranchas.py)
"""

import math
import os
import sys

from pypdf import PdfReader

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gerar_formas as gf                 # noqa: E402
import gerar_pranchas as gp               # noqa: E402
import folhas as fl                       # noqa: E402

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
CABECALHO = (f"{ORGAO} &nbsp;|&nbsp; MEMORIAL DESCRITIVO MD-02 &nbsp;|&nbsp; REVISÃO {REVISAO} "
             f"&nbsp;|&nbsp; {fl.DATA}")

# hipóteses das estimativas expeditas
GAMA_SOLO, K0 = 18.0, 0.5           # kN/m³; empuxo em repouso
CIV, CNF = 1.35, 1.05               # ABNT NBR 7188: vão menor que 10 m; uma faixa
ANG_DISP = 30.0                     # dispersão da carga das rodas no aterro, com a vertical
FCK, FYK = 30.0, 500.0
RHO1 = 0.002
GAMA_CONC_FRESCO = 25.0             # kN/m³, pressão hidrostática do concreto fresco
ATERROS = (1.5, 3.0)
NBSP = "\u00a0"


def folhas_do_conjunto(cod):
    """Número de folhas do conjunto FA de um tamanho, lido do PDF de gerar_pranchas.py."""
    return len(PdfReader(os.path.join(PASTA, gp.nome_arquivo(cod) + ".pdf")).pages)


def num(v, casas=1):
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def tab(cab, linhas, titulo=None, classes=None, larguras=None):
    return fl.tabela(cab, linhas, titulo=titulo, classes=classes, larguras=larguras)


def carga_movel(Ha):
    """Pressão da carga móvel TB-450 no nível da laje superior (kPa), pela dispersão das
    áreas de contato através do aterro: maior valor entre uma roda isolada e o veículo."""
    phi = CIV * CNF
    sp = 2 * math.tan(math.radians(ANG_DISP)) * Ha
    roda = 75 * phi / ((0.20 + sp) * (0.50 + sp))
    veiculo = 450 * phi / ((3.20 + sp) * (2.50 + sp))
    return max(roda, veiculo)


def estimativa(a, Ha):
    """Pórtico fechado de rigidez constante, cargas uniformes: momentos no canto e no meio do
    vão da laje superior, cortante na face da mísula e resistência sem armadura transversal
    (ABNT NBR 6118, 19.4.1)."""
    B, t, m = a["B"] / 1000, a["t"] / 1000, a["m"] / 1000
    L = B + t
    qt = carga_movel(Ha)
    qv = GAMA_SOLO * Ha + qt + 25 * t
    qh = K0 * (GAMA_SOLO * (Ha + t + B / 2) + qt)
    Mc = (qv + qh) * L ** 2 / 24
    Mm = (2 * qv - qh) * L ** 2 / 24
    Vsd = 1.4 * qv * (L / 2 - t / 2 - m)
    d = t - 0.045
    fctd = 0.7 * 0.3 * FCK ** (2 / 3) / 1.4
    vrd1 = 0.25 * fctd * 1000 * max(1.6 - d, 1.0) * (1.2 + 40 * RHO1) * d
    Md = 1.4 * max(Mc, Mm)
    As = Md / (0.9 * d * FYK / 1.15 * 1000) * 1e4
    return dict(qt=qt, qv=qv, qh=qh, Mc=Mc, Mm=Mm, Vsd=Vsd, Vrd=vrd1, As=As, d=d)


def aterro_sobreposicao():
    """Aterro a partir do qual as áreas de dispersão das rodas de eixos vizinhos (1,50 m) e do
    mesmo eixo (2,00 m) se sobrepõem."""
    return max(1.50 - 0.20, 2.00 - 0.50) / (2 * math.tan(math.radians(ANG_DISP)))


def aterro_limite(a):
    """Maior altura de aterro, em passos de 0,5 m entre 1,5 m e 4,0 m, com VSd ≤ VRd1."""
    lim = None
    for Ha in (1.5, 2.0, 2.5, 3.0, 3.5, 4.0):
        if estimativa(a, Ha)["Vsd"] <= estimativa(a, Ha)["Vrd"]:
            lim = Ha
    return lim


def forma_expedita():
    """Verificação expedita das peças da fôrma sob a pressão hidrostática do concreto fresco,
    no caso mais desfavorável de cada peça entre os três tamanhos."""
    p = GAMA_CONC_FRESCO * gf.H_EXT / 1000                    # kPa na base
    E = 205000.0
    t = gf.E_PELE
    # chapa: maior vão entre nervuras (fôrma externa ou núcleo)
    vaos = []
    for cod in gf.ADUELAS:
        a = gf.geometria(cod)
        vaos.append((a["B"] / (a["n_ext"] + 1), cod, "fôrma externa"))
        vaos.append((a["Bn"] / (a["n_nuc"] + 1), cod, "núcleo"))
    s, cod_s, onde_s = max(vaos)
    W_ch = t ** 2 / 6
    I_ch = t ** 3 / 12
    M_ch = p / 1000 * s ** 2 / 10                             # N·mm por mm
    sig_ch = M_ch / W_ch
    d_ch = 0.0069 * (p / 1000) * s ** 4 / (E * I_ch)
    # nervura: perfil U sem colaboração da chapa
    h_n, b_n = gf.NERV[0], gf.NERV[1]
    A_ab, A_al = 2 * h_n * t, b_n * t
    y_al = h_n - t / 2
    yb = (A_ab * h_n / 2 + A_al * y_al) / (A_ab + A_al)
    I_n = 2 * t * h_n ** 3 / 12 + A_ab * (h_n / 2 - yb) ** 2 + A_al * (y_al - yb) ** 2
    L_n = gf.H_EXT - gf.CANT[0] - gf.CINTA[0]
    R = 0.5 * p * (gf.H_EXT / 1000)                           # kN por metro de face
    M_n = 0.064 * R * (s / 1000) * (L_n / 1000) * 1e6         # N·mm, carga triangular
    sig_n = M_n / (I_n / yb)
    # cinta superior: um terço da resultante; maior vão (fôrma externa da aduela de 2,50 m)
    a250 = gf.geometria("A250")
    w = R / 3                                                 # kN/m
    Lc = a250["B"] - 2 * gf.CANT[0] - 4
    alma, aba = gf.CINTA[1], gf.CINTA[0]
    I_c = t * alma ** 3 / 12 + 2 * (aba * t) * (alma / 2 - t / 2) ** 2
    M_c = w * (Lc / 1000) ** 2 / 8 * 1e6
    sig_c = M_c / (I_c / (alma / 2))
    d_c = 5 * w * Lc ** 4 / (384 * E * I_c)
    # ligações da fôrma externa (aduela de 2,50 m)
    F_junta = R * (a250["Be"] / 1000) / 2                     # kN por junta
    F_base = R * (a250["B"] / 1000) * 2 / 3 / 3               # kN por parafuso de base
    # parafuso M16 classe 8.8 (fub = 800 MPa), ABNT NBR 8800, γa2 = 1,35
    Ab = math.pi * 16 ** 2 / 4
    Ft_Rd = 0.75 * Ab * 800 / 1.35 / 1000
    Fv_Rd = 0.4 * Ab * 800 / 1.35 / 1000
    return dict(p=p, s=s, cod_s=cod_s, onde_s=onde_s, sig_ch=sig_ch, d_ch=d_ch, I_n=I_n,
                sig_n=sig_n, L_n=L_n, w=w, Lc=Lc, sig_c=sig_c, d_c=d_c, F_junta=F_junta,
                F_paraf=F_junta / 4, F_base=F_base, Ft_Rd=Ft_Rd, Fv_Rd=Fv_Rd)


def main():
    os.makedirs(PASTA, exist_ok=True)
    tam = {cod: gf.geometria(cod) for cod in gf.ADUELAS}
    for a in tam.values():
        a["nome"] = a["nome"].replace(" m", NBSP + "m")
    pecas = {cod: gf.todas_as_pecas(cod) for cod in gf.ADUELAS}
    fx = forma_expedita()
    h = []
    h.append(f"""<div class="capa">
<div class="ent"><img src="{fl.LOGO_URI}" alt="Bandeira do Município de Eldorado do Carajás">
<div><div class="t">{fl.esc(ORGAO)}</div><div class="e">CNPJ {fl.CNPJ}</div>
<div class="e">{fl.esc(fl.ENDERECO)}</div></div></div>
<h1>MEMORIAL DESCRITIVO MD-02</h1>
<div class="s">ADUELAS DE CONCRETO ARMADO PRÉ-MOLDADO DE SEÇÃO QUADRADA (1,00 × 1,00&nbsp;m,
2,00 × 2,00&nbsp;m E 2,50 × 2,50&nbsp;m) – ANTEPROJETO E FÔRMAS METÁLICAS DE MOLDAGEM</div>
{tab(None, [["PROPRIETÁRIO", f"{ORGAO}, CNPJ {fl.CNPJ}"],
            ["PREFEITO MUNICIPAL", fl.PREFEITO],
            ["LOCAL DE PRODUÇÃO E DE APLICAÇÃO", fl.LOCAL], ["SITUAÇÃO", fl.SITUACAO],
            ["REVISÃO", f"{REVISAO} – {REVISAO_TXT}"], ["DATA", fl.DATA],
            ["RESPONSÁVEL TÉCNICO PELO PROJETO", "A DESIGNAR (CREA E ART A INFORMAR)"],
            ["ANÁLISE TÉCNICA", f"{fl.ANALISTA} – {fl.ANALISTA_REGISTRO}"]],
        larguras=["32%", "68%"])}
</div>""")

    h.append("<h2>1. Objeto</h2>")
    h.append("<p>Este memorial descreve o anteprojeto de aduelas (galerias celulares) fechadas "
             "de concreto armado pré-moldado, de seção quadrada interna de 1,00 × 1,00 m, "
             "2,00 × 2,00 m e 2,50 × 2,50 m, com comprimento útil de 1,00 m e encaixe macho e "
             "fêmea, e o projeto das fôrmas metálicas de moldagem, em chapa de aço cortada a "
             "laser e dobrada, para produção das aduelas pelo Município. Estabelece as premissas, "
             "a geometria das aduelas e do encaixe, as estimativas preliminares, os critérios de "
             "fabricação, montagem e uso das fôrmas e as condicionantes técnicas e legais.</p>")

    h.append("<h2>2. Documentos integrantes</h2>")
    docs = []
    for cod, a in tam.items():
        docs.append([f"FA{cod[1:]}-01 a FA{cod[1:]}-{folhas_do_conjunto(cod):02d}",
                     f"Fôrma da aduela {a['nome']}: índice e notas; parâmetros de corte e dobra; "
                     f"aduela e encaixe; fôrma montada; base, anel superior e canto; montagem, "
                     f"soldas e lista de materiais; detalhe das {len(pecas[cod])} marcas; listas "
                     f"gerais", "A3"])
    docs += [["MD-02", "Memorial descritivo (este documento)", "A4"],
             ["Arquivos DXF", "Arquivos digitais de corte, de corte e gravação e de desenho de "
                              "cada marca, por tamanho de aduela", "DXF R2000"],
             ["Tabelas", "Lista de corte, tabela de dobras, itens comerciais e quadro da aduela, "
                         "por tamanho", "CSV"]]
    h.append(tab(["DOCUMENTO", "CONTEÚDO", "FORMATO"], docs, classes=["c", "", "c"],
                 larguras=["22%", "63%", "15%"]))

    h.append("<h2>3. Normas, referências e legislação</h2>")
    h.append(tab(["REFERÊNCIA", "ASSUNTO"], [
        ["ABNT NBR 15396:2018", "Aduelas (galerias celulares) de concreto armado pré-fabricadas: "
                                "requisitos e métodos de ensaio"],
        ["ABNT NBR 15645:2020", "Execução de obras de esgoto sanitário e drenagem de águas "
                                "pluviais utilizando tubos e aduelas de concreto"],
        ["ABNT NBR 6118", "Projeto de estruturas de concreto"],
        ["ABNT NBR 7188:2024", "Carga móvel rodoviária e de pedestres em pontes, viadutos, "
                               "passarelas e outras estruturas"],
        ["ABNT NBR 9062:2017", "Projeto e execução de estruturas de concreto pré-moldado"],
        ["ABNT NBR 15696:2025", "Sistemas de fôrmas e de escoramentos para estruturas de "
                                "concreto: projeto, dimensionamento e procedimentos executivos "
                                "(referência para as fôrmas; escopo de estruturas moldadas no "
                                "local)"],
        ["ABNT NBR 16752:2020 e NBR 16861:2020", "Desenho técnico: folhas, linhas e escrita"],
        ["ABNT NBR 8800", "Projeto de estruturas de aço e de estruturas mistas de aço e "
                          "concreto de edificações (resistência dos parafusos)"],
        ["AWS D1.1", "Soldagem estrutural de aço (procedimento de referência)"],
        ["SINAPI, caderno técnico “Galerias com aduelas de concreto” (CAIXA)",
         "Composições de referência 104493 (aduela fechada 2,00 × 2,00 m, espessura mínima de "
         "20 cm) e 104495 (aduela fechada 2,50 × 2,50 m, espessura mínima de 20 cm), com mísula "
         "de 20 × 20 cm, comprimento de 1,00 m, carga TB-45 e concreto de 30 MPa"],
        ["Coordenadoria Estadual de Proteção e Defesa Civil de São Paulo, especificação "
         "“Galerias celulares pré-fabricadas industrialmente (aduelas)”",
         "Durabilidade (fck de 30 MPa, relação água/cimento até 0,47, cobrimento nominal de "
         "40 mm, abertura de fissura até 0,3 mm), cálculo como pórtico sobre apoio elástico e "
         "fabricação conforme ABNT NBR 15396"],
        ["NR-11 e NR-18 (Ministério do Trabalho e Emprego)", "Movimentação de cargas e segurança "
                                                             "na construção"],
        ["Lei nº 5.194/1966", "Exercício das profissões de engenheiro e engenheiro-agrônomo "
                              "(arts. 13 e 14)"],
        ["Lei nº 6.496/1977", "Anotação de Responsabilidade Técnica (ART)"],
        ["Lei nº 14.133/2021", "Licitações e contratos administrativos (arts. 46, § 1º, 124 e "
                               "125)"],
        ["Lei nº 12.651/2012", "Proteção da vegetação nativa (art. 3º, VIII, b, e art. 8º)"],
        ["Lei nº 9.433/1997", "Política Nacional de Recursos Hídricos (art. 12, V)"],
    ], larguras=["32%", "68%"]))
    h.append("<p class='obs'>As composições do SINAPI são citadas como referência de "
             "especificação e de custo. O texto da ABNT NBR 15396:2018 deve ser consultado na "
             "versão vigente para os requisitos de tolerância, cobrimento, inspeção e ensaios.</p>")

    h.append("<h2>4. Premissas e dados de entrada</h2>")
    lin = []
    for cod, a in tam.items():
        lin.append([a["nome"], f"{a['t']} mm", f"{a['m']} × {a['m']}{NBSP}mm",
                    a["sinapi"] if a["sinapi"] != "–" else
                    "não identificada; menor seção localizada: 1,50 × 1,50 m (104491, espessura "
                    "mínima de 15 cm)"])
    h.append(tab(["SEÇÃO INTERNA", "ESPESSURA DAS LAJES E PAREDES", "MÍSULAS", "SINAPI DE "
                  "REFERÊNCIA"], lin, classes=["c", "c", "c", "c"],
                 titulo="Quadro 1 – Aduelas adotadas"))
    h.append(tab(["PARÂMETRO", "VALOR ADOTADO", "ORIGEM E SITUAÇÃO"], [
        ["Comprimento útil", "1,00 m (passo na galeria)", "SINAPI; usual de fabricação"],
        ["Encaixe", f"Macho e fêmea: macho de {gf.P_MACHO} mm, bolsa de {gf.P_BOLSA} mm, faces "
                    f"inclinadas", "Pré-dimensionamento; ABNT NBR 15396:2018"],
        ["Concreto", "C30, relação água/cimento até 0,47; cobrimento nominal de 40 mm",
         "SINAPI e especificação da Defesa Civil de SP; a confirmar com a classe de "
         "agressividade ambiental (ABNT NBR 6118)"],
        ["Aço", "CA-50 e CA-60 (telas)", "A definir no projeto estrutural"],
        ["Carga móvel", "TB-450 (ABNT NBR 7188:2024)", "A confirmar pelo responsável técnico"],
        ["Altura de aterro", "A definir por obra", "Estimativa da seção 6"],
        ["Moldagem", "Vertical, com o macho na base", "Concepção da fôrma"],
        ["Produção", f"{gf.FORMAS_POR_TAMANHO} jogo de fôrma por tamanho, uma aduela por dia",
         "A ajustar à demanda"],
    ], larguras=["24%", "44%", "32%"]))
    h.append("<p class='obs'>As espessuras, mísulas e o encaixe resultam de pré-dimensionamento "
             "e não constituem dimensionamento estrutural.</p>")

    h.append("<h2>5. Aduelas e encaixe</h2>")
    h.append("<p>Cada aduela é um anel de concreto armado de seção quadrada, com laje superior, "
             "laje inferior e duas paredes de mesma espessura, mísulas a 45° nos quatro cantos "
             "internos e encaixe tipo macho e fêmea nas extremidades. O macho é a parte interna "
             "da parede, saliente em uma extremidade; a bolsa (fêmea) é a parte externa da "
             "parede, saliente na outra extremidade. Na galeria, o macho de cada aduela entra na "
             "bolsa da anterior, com folga axial de "
             f"{gf.P_BOLSA - gf.P_MACHO} mm e folga radial de "
             f"{num(tam['A250']['folga_radial'], 0)} mm na boca, preenchidas com argamassa de "
             f"rejuntamento.</p>")
    lin = []
    for cod, a in tam.items():
        v, mt, zc = gf.concreto(a)
        lin.append([a["nome"], f"{a['Be']} × {a['Be']}", f"{num(a['wm'], 0)} e "
                    f"{num(a['wm_ponta'], 0)}", f"{num(a['s0'], 0)} e {num(a['s_boca'], 0)}",
                    num(v, 3), num(mt, 2), num(zc, 0)])
    h.append(tab(["SEÇÃO INTERNA", "SEÇÃO EXTERNA (mm)", "MACHO: BASE E PONTA (mm)",
                  "BOLSA: FUNDO E BOCA (mm)", "VOLUME (m³)", "MASSA (t)", "CENTRO DE GRAVIDADE "
                  "(mm)"], lin, classes=["c", "c", "c", "c", "n", "n", "n"],
                 titulo="Quadro 2 – Geometria, volume e massa das aduelas"))
    h.append("<p class='obs'>Larguras do macho e da bolsa medidas a partir da face interna da "
             "parede. Massa com massa específica de 2.500 kg/m³ do concreto armado (ABNT NBR "
             "6118, item 8.2.2), descontado o furo "
             "de içamento. Centro de gravidade medido a partir da ponta do macho, ao longo do "
             "eixo da galeria; nele fica o furo de içamento de 110 mm da laje superior.</p>")

    h.append("<h2>6. Estimativas preliminares</h2>")
    h.append("<p>Os valores a seguir são estimativas expeditas, em valores característicos salvo "
             "indicação, destinadas a verificar a coerência do pré-dimensionamento. Não "
             "substituem o cálculo estrutural do projeto executivo.</p>")
    h.append("<h3>6.1 Lajes e paredes sob aterro e carga móvel</h3>")
    h.append(f"<p>Hipóteses: aterro de {num(GAMA_SOLO, 0)} kN/m³ com empuxo em repouso "
             f"(K0 = {num(K0, 1)}); carga móvel TB-450 com seis rodas de 75 kN e área de contato "
             f"de 0,20 × 0,50 m, coeficientes CIV = {num(CIV, 2)} e CNF = {num(CNF, 2)}, "
             f"dispersão no aterro a {num(ANG_DISP, 0)}° com a vertical e pressão no nível da "
             f"laje igual ao maior valor entre roda isolada e veículo completo; pórtico fechado "
             f"de rigidez constante, com vão de eixo igual ao vão interno mais a espessura e "
             f"cargas uniformes; momentos no canto Mc = (qv + qh)·L²/24 e no meio da laje "
             f"Mm = (2qv − qh)·L²/24; cortante de cálculo na face da mísula com γf = 1,4, "
             f"comparado à resistência sem armadura transversal VRd1 da ABNT NBR 6118 (item "
             f"19.4.1), com fck = {num(FCK, 0)} MPa, altura útil igual à espessura menos 45 mm e "
             f"ρ1 = {num(RHO1 * 100, 1)}%.</p>")
    lin = []
    for cod, a in tam.items():
        for Ha in ATERROS:
            e = estimativa(a, Ha)
            lin.append([a["nome"], num(Ha, 1), num(e["qt"]), num(e["qv"]), num(e["qh"]),
                        num(e["Mc"]), num(e["Mm"]), num(e["Vsd"]), num(e["Vrd"]),
                        num(e["As"]), "atende" if e["Vsd"] <= e["Vrd"] else "não atende"])
    h.append(tab(["SEÇÃO", "ATERRO (m)", "CARGA MÓVEL (kPa)", "qv (kPa)", "qh (kPa)",
                  "Mc (kN·m/m)", "Mm (kN·m/m)", "VSd (kN/m)", "VRd1 (kN/m)", "As (cm²/m)",
                  "CORTANTE"], lin, classes=["c", "n", "n", "n", "n", "n", "n", "n", "n", "n",
                                              "c"],
                 titulo="Quadro 3 – Estimativa dos esforços na laje superior"))
    lim = {cod: aterro_limite(a) for cod, a in tam.items()}
    h.append("<p>Com o critério de cortante adotado, a espessura de pré-dimensionamento atende "
             "a aterros de até " + "; ".join(
                 f"{num(lim[c], 1)} m na aduela {tam[c]['nome']}" for c in tam) +
             " (passos de 0,5 m, limite superior pesquisado de 4,0 m). O método vale para "
             f"aterro a partir de {num(aterro_sobreposicao(), 1)} m, em que as áreas de "
             "dispersão das seis rodas se sobrepõem; para aterro menor, a carga concentrada das "
             "rodas exige verificação específica. Para aterro acima de "
             f"{num(lim['A250'], 1)} m, a mesma estimativa indica, para a aduela de 2,50 m, a "
             "espessura de 25 cm da composição SINAPI 104496; nesse caso, trocam-se os cantos "
             "da fôrma externa, a base e o anel superior, mantidos o núcleo e os painéis "
             "externos.</p>")
    h.append("<h3>6.2 Manuseio e içamento</h3>")
    h.append("<p>As massas do Quadro 2 definem o equipamento de içamento: a aduela de 2,50 m, "
             "com cerca de " + num(gf.concreto(tam["A250"])[1], 1) + " t, exige guindaste ou "
             "caminhão com guindauto de capacidade compatível no raio de trabalho real, "
             "verificada pela tabela de carga do equipamento, com plano de içamento (NR-11 e "
             "NR-18). Os insertos de içamento, a resistência mínima para desforma e içamento e o "
             "procedimento de basculamento da posição de moldagem para a de assentamento são "
             "definidos no projeto estrutural (ABNT NBR 9062:2017).</p>")
    h.append("<h3>6.3 Fôrma sob a pressão do concreto fresco</h3>")
    h.append(f"<p>Pressão hidrostática do concreto fresco, de {num(GAMA_CONC_FRESCO, 0)} kN/m³, "
             f"em toda a altura de {gf.H_EXT} mm: {num(fx['p'])} kPa na base. As nervuras "
             f"verticais apoiam-se na cantoneira de base, aparafusada na base (dois terços da "
             f"carga), e na cinta superior (um terço), que vence o vão entre os cantos.</p>")
    h.append(tab(["PEÇA", "MODELO", "RESULTADO ESTIMADO", "REFERÊNCIA"], [
        ["Chapa de 4,75 mm entre nervuras", f"faixa contínua, vão de {num(fx['s'], 0)} mm "
         f"({fx['onde_s']} da aduela {tam[fx['cod_s']]['nome']})",
         f"tensão de {num(fx['sig_ch'], 0)} MPa; flecha de {num(fx['d_ch'], 1)} mm",
         "tensão até 150 MPa; flecha até 2 mm"],
        ["Nervura vertical U 63 × 40 × 63", f"viga de {num(fx['L_n'], 0)} mm com carga "
         f"triangular, sem colaboração da chapa", f"tensão de {num(fx['sig_n'], 0)} MPa",
         "tensão até 150 MPa"],
        ["Cinta superior U 60 × 150 × 60", f"viga biapoiada de {num(fx['Lc'], 0)} mm, carga de "
         f"{num(fx['w'], 2)} kN/m (aduela de 2,50 m)",
         f"tensão de {num(fx['sig_c'], 0)} MPa; flecha de {num(fx['d_c'], 1)} mm",
         f"tensão até 150 MPa; flecha até L/400 ({num(fx['Lc'] / 400, 1)} mm)"],
        ["Junta painel-canto da fôrma externa", "metade da resultante de um lado, em 4 "
         "parafusos M16", f"{num(fx['F_junta'])} kN por junta; {num(fx['F_paraf'])} kN por "
         f"parafuso (média)", f"M16 classe 8.8: {num(fx['Ft_Rd'], 0)} kN à tração, de "
                                f"cálculo"],
        ["Parafusos de base da fôrma externa", "dois terços da carga do painel em 3 parafusos",
         f"{num(fx['F_base'])} kN por parafuso, ao corte",
         f"M16 classe 8.8: {num(fx['Fv_Rd'], 0)} kN ao corte, de cálculo"],
    ], larguras=["24%", "30%", "26%", "20%"]))
    h.append("<p class='obs'>Tensão admissível de referência de 150 MPa (0,6 fy, aço ASTM A36 "
             "com fy = 250 MPa) e módulo de elasticidade de 205 GPa; limites de tensão e de flecha "
             "adotados nesta estimativa. Chapa SAE 1020, especificada por composição química, "
             "exige o limite de escoamento no certificado da usina. Resistências de cálculo dos "
             "parafusos conforme ABNT NBR 8800 (γa2 = 1,35; plano de corte na rosca), a comparar "
             "com as forças estimadas multiplicadas por γf = 1,4. A verificação estrutural definitiva da fôrma é feita pelo responsável "
             "técnico, com referência na ABNT NBR 15696:2025.</p>")

    h.append("<h2>7. Fôrmas metálicas</h2>")
    h.append("<h3>7.1 Concepção</h3>")
    h.append("<p>A aduela é moldada na posição vertical, com o eixo da galeria na vertical. "
             "Cada jogo de fôrma é composto por:</p>")
    h.append("<ol>"
             "<li>Fôrma externa: quatro painéis com comprimento igual ao vão interno e quatro "
             "cantos dobrados com abas iguais à espessura da parede, ligados por cantoneiras "
             "aparafusadas; as juntas ficam no plano das faces internas das paredes. Os painéis "
             "têm nervuras verticais em U, cinta superior e cantoneira de base.</li>"
             "<li>Núcleo: quatro painéis e quatro cantos dobrados com a mísula, ligados por "
             "cantoneiras aparafusadas pelo lado interno; desforma por recolhimento dos painéis "
             "para o centro e retirada dos cantos na diagonal.</li>"
             "<li>Base: chapa em quatro peças iguais em catavento, soldada sobre piso de "
             "concreto nivelado, com o ressalto que molda o ombro e a face externa do "
             "macho.</li>"
             "<li>Anel superior: chapa em quatro peças com juntas a 45° e barras da saia, que "
             "moldam o fundo e a face interna da bolsa; apoiado nas cintas do núcleo.</li>"
             "<li>Acessórios: tubo-fôrma de PVC com barra roscada para o furo de içamento e "
             "régua porta-inserto para os insertos do topo da bolsa.</li></ol>")
    h.append("<p>Nenhuma dobra excede 3000 mm, comprimento útil da dobradeira do fornecedor, e "
             "nenhum painel excede 2500 mm. A fôrma externa só depende da espessura da parede "
             "pelos cantos; a base e o anel superior dependem da espessura pelo encaixe; o "
             "núcleo e os painéis externos não dependem da espessura.</p>")
    lin = []
    for cod, ps in pecas.items():
        aco = sum(p.peso * p.qtd for p in ps)
        lin.append([f"F-{cod}", tam[cod]["nome"], len(ps), sum(p.qtd for p in ps),
                    num(aco, 0), num(max(p.peso for p in ps), 1)])
    h.append(tab(["JOGO", "ADUELA", "MARCAS", "PEÇAS", "AÇO (kg)", "MAIOR PEÇA (kg)"], lin,
                 classes=["c", "c", "n", "n", "n", "n"],
                 titulo="Quadro 4 – Jogos de fôrma (um jogo por tamanho)"))
    h.append("<h3>7.2 Planificação, dobra e arquivos digitais</h3>")
    linhas_dobra = [[gf.fmt_t(t), gf.fmt(d["ri"]), f"{d['k']:.2f}".replace(".", ","), d["v"]]
                    for t, d in gf.DOBRA.items() if t in (gf.E_PELE, gf.E_PERFIL)]
    h.append("<p>As planificações são calculadas pela linha neutra, com desenvolvimento da dobra "
             "BA = θ·(Ri + K·e) e recuo externo OSSB = (Ri + e)·tg(θ/2), a partir das medidas "
             "externas das abas, com os parâmetros de referência abaixo, a substituir pelos da "
             "tabela do ferramental do fabricante antes da liberação. Para cada marca há arquivo "
             "de corte, arquivo de corte e gravação (quando há posição de solda a marcar) e "
             "arquivo de desenho, em DXF R2000, unidade milímetro.</p>")
    h.append(tab(["ESPESSURA (mm)", "RAIO INTERNO (mm)", "FATOR K", "ABERTURA DO V (mm)"],
                 linhas_dobra, classes=["c", "n", "n", "n"]))
    forcas = [(gf.forca_dobra_tf(p.t, p.comprimento), p.codigo) for ps in pecas.values()
              for p in ps if p.linhas]
    fmax = max(forcas)
    h.append(f"<p>A maior força de dobra estimada é de {num(fmax[0])} tf, na marca {fmax[1]}, o "
             f"que corresponde a capacidade nominal mínima de {num(fmax[0] / 0.85, 0)} tf com as "
             f"matrizes indicadas (uso máximo de 85%). As pranchas 02 de cada conjunto indicam "
             f"as matrizes alternativas para dobradeiras de menor capacidade.</p>")
    maior_peca = max(p.peso for ps in pecas.values() for p in ps)
    h.append("<h3>7.3 Fabricação, montagem e uso</h3>")
    h.append("<ol>"
             "<li>Fabricar o jogo e moldar uma aduela de prova, com conferência dimensional "
             "conforme ABNT NBR 15396:2018, antes da produção.</li>"
             "<li>Tolerâncias das peças de chapa: corte e posição de furos ±0,5 mm; ângulo de "
             "dobra ±1°; abas ±1 mm. Fôrma montada: dimensões ±2 mm, diferença entre diagonais "
             "até 3 mm e prumo de 2 mm em 1065 mm.</li>"
             "<li>Soldas por soldador qualificado, com procedimento de referência AWS D1.1, "
             "conforme o quadro de soldas; faces de contato com o concreto isentas de solda, "
             "respingo e rebarba e juntas soldadas esmerilhadas rente.</li>"
             f"<li>Peças de fôrma com mais de 60 kg (até {num(maior_peca, 1)} kg) movimentadas "
             "por meio mecânico ou por mais de um trabalhador (CLT, art. 198, e NR-17).</li>"
             "<li>Desmoldante e conferência de dimensões, prumo e diagonais antes de cada "
             "concretagem; vibração por imersão em camadas ou por vibradores externos de "
             "fôrma.</li>"
             "<li>Desforma e içamento com a resistência especificada no projeto estrutural; a "
             "aduela é retirada da base pelos insertos do topo da bolsa.</li></ol>")

    h.append("<h2>8. Assentamento das aduelas</h2>")
    h.append("<ol>"
             "<li>Assentamento, rejuntamento e reaterro conforme ABNT NBR 15645:2020 e projeto "
             "executivo: berço e alinhamento conforme projeto; cada aduela assentada deixa como "
             "extremidade livre a bolsa, onde se acopla o macho da aduela seguinte.</li>"
             "<li>Juntas rejuntadas com argamassa pelo lado interno e externo; furos de "
             "içamento vedados com argamassa após o assentamento.</li>"
             "<li>Reaterro em camadas compactadas simultaneamente dos dois lados, com altura "
             "mínima de cobertura antes do tráfego definida no projeto.</li>"
             "<li>Testas, alas e dissipação na saída da galeria executadas no local, conforme "
             "projeto; não integram este conjunto de fôrmas.</li></ol>")

    h.append("<h2>9. Condicionantes para a execução</h2>")
    h.append("<h3>9.1 Técnicas</h3>")
    h.append("<ol>"
             "<li>Projeto estrutural das aduelas (espessura, armadura, cobrimento, insertos, "
             "resistências de desforma e içamento e altura de aterro admissível) e projeto "
             "executivo de cada galeria, com estudo hidrológico e hidráulico, sob "
             "responsabilidade de profissional habilitado, com ART.</li>"
             "<li>Confirmação, pelo fornecedor, do raio interno, do fator K e da abertura de "
             "matriz do ferramental, da capacidade nominal da dobradeira e do formato de "
             "arquivo aceito; regeneração dos arquivos de corte com os dados confirmados.</li>"
             "<li>Aduela de prova com conferência dimensional e ensaios conforme ABNT NBR "
             "15396:2018 antes da produção.</li></ol>")
    h.append("<h3>9.2 Legais e administrativas</h3>")
    h.append("<ol>"
             "<li>Cada obra de galeria depende de projeto executivo, nos termos do art. 46, "
             "§ 1º, da Lei nº 14.133/2021, ressalvada a hipótese do art. 18, § 3º.</li>"
             "<li>A fabricação das fôrmas pelo fornecedor contratado pressupõe que o objeto do "
             "contrato abranja o serviço de corte e dobra; caso contrário, a inclusão depende de "
             "alteração contratual nos limites dos arts. 124 e 125 da Lei nº 14.133/2021 ou de "
             "nova contratação.</li>"
             "<li>Anotação de Responsabilidade Técnica do projeto, da fabricação das fôrmas, da "
             "produção das aduelas e da execução das obras (Lei nº 6.496/1977).</li>"
             "<li>Intervenção em área de preservação permanente admitida nas hipóteses de "
             "utilidade pública, que incluem obras do sistema viário, mediante autorização do "
             "órgão ambiental competente (Lei nº 12.651/2012, art. 3º, VIII, b, e art. 8º).</li>"
             "<li>Outorga de direito de uso de recursos hídricos, ou sua dispensa, pelo órgão "
             "gestor competente, para galeria que interfira em curso d'água (Lei nº "
             "9.433/1997, art. 12, V).</li></ol>")

    h.append("<h2>10. Responsabilidade técnica e análise</h2>")
    h.append("<p>Este memorial e as pranchas que o acompanham constituem anteprojeto elaborado a "
             "partir das premissas informadas pelo contratante. Os estudos, plantas e projetos "
             "de engenharia só têm valor jurídico quando seus autores forem profissionais "
             "habilitados, e os trabalhos gráficos devem conter a assinatura, o título "
             "profissional e o número do registro do signatário (Lei nº 5.194/1966, arts. 13 e "
             "14). O anteprojeto não substitui o projeto estrutural das aduelas nem o projeto "
             "executivo das obras, que devem ser elaborados e assinados por profissional "
             "legalmente habilitado, com a respectiva Anotação de Responsabilidade Técnica (Lei "
             "nº 6.496/1977, art. 1º).</p>")
    h.append(f"<p>O anteprojeto é submetido à análise técnica do Eng. {fl.ANALISTA_NOME}, "
             f"CREA-PA nº&nbsp;{fl.ANALISTA_CREA}, servidor do Município, matrícula "
             f"nº&nbsp;{fl.ANALISTA_MATRICULA}. A análise técnica não transfere a autoria nem a "
             f"responsabilidade técnica pelo projeto e é registrada no quadro a seguir e no "
             f"campo próprio da legenda das pranchas.</p>")
    h.append(tab(None, [
        ["PROFISSIONAL", fl.ANALISTA],
        ["REGISTRO", fl.ANALISTA_REGISTRO],
        ["DOCUMENTOS ANALISADOS", f"FA100, FA200 E FA250 (TODAS AS PRANCHAS) E MD-02, REVISÃO "
                                  f"{REVISAO}"],
        ["PARECER E OBSERVAÇÕES", fl.Bruto("<div style='height:22mm'></div>")],
        ["DATA", fl.Bruto("<div style='height:7mm'></div>")],
        ["ASSINATURA", fl.Bruto("<div style='height:14mm'></div>")],
    ], titulo="REGISTRO DA ANÁLISE TÉCNICA", larguras=["32%", "68%"]))

    html = ("<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'>"
            "<title>Memorial descritivo MD-02</title><style>" + CSS + "</style></head><body>"
            + "".join(h) + "</body></html>")
    html_path = os.path.join(PASTA, "MD-02_memorial_descritivo_aduelas.html")
    pdf_path = os.path.join(PASTA, "MD-02_memorial_descritivo_aduelas.pdf")
    if fl.grava_e_imprime(html, html_path, pdf_path, cabecalho=CABECALHO):
        print("PDF:", pdf_path)
    for cod, a in tam.items():
        print(cod, "aterro limite estimado", aterro_limite(a), "m")
    print({k: round(v, 2) if isinstance(v, float) else v for k, v in fx.items()})


if __name__ == "__main__":
    main()
