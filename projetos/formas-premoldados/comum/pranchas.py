#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Montagem das pranchas de fabricação (formato A3) comum aos projetos de fôrmas.

Quadros de cada marca (dados, dobras e furos), bloco de detalhe com planificação e seção
dobrada, distribuição automática dos blocos nas folhas, folha de parâmetros de corte e dobra,
lista de materiais, quadro de soldas, convenções e listas gerais. Cada projeto informa as
escalas, as gravações e as vistas próprias das suas marcas (classe Detalhamento).
"""

import json
import os
import re
import subprocess

import chapas as ch
import desenho as dz
import folhas as fl

QW = fl.FORMATOS["A3"][0] - fl.MARGEM["esq"] - fl.MARGEM["dir"]     # área útil do quadro
QH = fl.FORMATOS["A3"][1] - fl.MARGEM["sup"] - fl.MARGEM["inf"]
RX, RY = QW - fl.LEG_W, QH - fl.LEG_H - fl.REV_H   # canto da área reservada à legenda
H_DIR = RY - 6                    # altura dos blocos à direita, de y = 4 até 2 mm da legenda


def f1(v):
    return ch.fmt(v)


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
# QUADROS DE UMA MARCA
# --------------------------------------------------------------------------
def tabela_dados(p, gravacao=None):
    """Quadro da marca; 'gravacao' descreve as linhas gravadas a laser, quando houver."""
    arquivos = [f"{p.codigo}_CORTE.dxf"]
    if p.marcas:
        arquivos.append(f"{p.codigo}_CORTE_E_GRAVACAO.dxf")
    arq = fl.Bruto("<br>".join(f'<span class="nw">{a}</span>' for a in arquivos))
    linhas = [
        ["MATERIAL", f"ASTM A36, CHAPA {ch.fmt_t(p.t)} mm", "QUANTIDADE", f"{p.qtd} PEÇAS"],
        ["PLANIFICAÇÃO", f"{f1(p.comprimento)} × {f1(p.largura)} mm", "MASSA UNITÁRIA",
         f"{kg(p.peso)} kg"],
        ["ARQUIVO DIGITAL", (arq, 1, ""), "MASSA TOTAL", f"{kg(p.peso * p.qtd)} kg"],
    ]
    if p.marcas:
        linhas.append(["GRAVAÇÃO A LASER", (fl.esc(U(f"{gravacao}, na {p.lado_marca}")),
                                            3, "")])
    linhas.append(["NOTA", (fl.esc(p.obs), 3, "")])
    return fl.tabela(None, linhas, titulo=f"QUADRO DA MARCA {p.codigo}",
                     larguras=["21%", "34%", "21%", "24%"])


def tabela_dobras(p):
    if not p.linhas:
        return ""
    d = ch.DOBRA[p.t]
    linhas = []
    for r, g in zip(ch.roteiro_de_dobra(p), p.giros):
        linhas.append([r["n"], f"{f1(r['ang'])}°", "PARA CIMA" if g > 0 else "PARA BAIXO",
                       f1(r["da"]), f1(r["db"]),
                       "INFERIOR" if r["borda"] == "A" else "SUPERIOR",
                       f1(d["ri"]), d["v"], f1(ch.forca_dobra_tf(p.t, p.comprimento))])
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


# --------------------------------------------------------------------------
# DETALHE DAS MARCAS E DISTRIBUIÇÃO NAS FOLHAS
# --------------------------------------------------------------------------
LARGO, ESTREITO = QW - 8, RX - 8     # larguras dos blocos: faixa inteira ou à esquerda da legenda
TOPO, FUNDO_LARGO, FUNDO = 3, RY - 3, QH - 3
VAO = 4


class Detalhamento:
    """Detalhes das marcas de um projeto.

    escalas: {marca: (escala da planificação, escala da seção dobrada)}
    nomes_formas: {forma: título da fôrma no título das folhas de detalhe}
    gravacao: {marca: descrição das linhas gravadas a laser}
    vista_parcial: {marca: (escala, comprimento mostrado)} para peças longas e estreitas
    arranjo_coluna: marcas com as vistas à esquerda e os quadros empilhados à direita
    grupos_furos: {marca: número de colunas da tabela de furos}"""

    def __init__(self, escalas, nomes_formas, gravacao=None, vista_parcial=None,
                 arranjo_coluna=(), grupos_furos=None):
        self.escalas, self.nomes_formas = escalas, nomes_formas
        self.gravacao = gravacao or {}
        self.vista_parcial = vista_parcial or {}
        self.arranjo_coluna = set(arranjo_coluna)
        self.grupos_furos = grupos_furos or {}

    def vistas(self, p, e_plan, e_sec):
        parcial = self.vista_parcial.get(p.codigo)
        v = [fl.vista(dz.planificacao(p, e_plan, f"pl-{p.codigo}", simples=bool(parcial)),
                      "PLANIFICAÇÃO", f"1:{e_plan}", "VISTA PELA FACE SUPERIOR NA MESA DE CORTE")]
        if parcial:
            ep, comp = parcial
            v.append(fl.vista(dz.planificacao(p, ep, f"pp-{p.codigo}", trecho=comp),
                              "VISTA PARCIAL DA PLANIFICAÇÃO", f"1:{ep}", "EXTREMIDADE DA PEÇA"))
        if p.linhas:
            v.append(fl.vista(dz.secao_dobrada(p, e_sec, f"sd-{p.codigo}"),
                              "SEÇÃO DA PEÇA DOBRADA", f"1:{e_sec}"))
        return v

    def conteudo(self, p, e_plan, e_sec):
        """Bloco da marca: cabeçalho, vistas lado a lado e quadros abaixo (ou à direita)."""
        vs = self.vistas(p, e_plan, e_sec)
        tabs = [tabela_dados(p, self.gravacao.get(p.codigo)), tabela_dobras(p),
                tabela_furos(p, self.grupos_furos.get(p.codigo))]
        tabs = [t for t in tabs if t]
        cab = f'<div class="cab">MARCA {p.codigo} – {U(p.nome)}<small>{p.qtd} PEÇAS</small></div>'
        if p.codigo in self.arranjo_coluna:
            return (cab + f'<div class="linha"><div style="flex:0 0 auto">{"".join(vs)}</div>'
                    f'<div class="pilha" style="flex:1 1 0">{"".join(tabs)}</div></div>')
        cls = ["dados"] + (["dobras"] if p.linhas else []) + [""] * (len(tabs) - 1 - bool(p.linhas))
        caixas = "".join(f'<div class="{c}">{t}</div>' for c, t in zip(cls, tabs))
        return (cab + f'<div class="linha" style="justify-content:space-around;flex-wrap:wrap">'
                f'{"".join(vs)}</div><div class="tabs" style="margin-top:2mm">{caixas}</div>')

    def mede(self, pecas, pasta):
        """Altura do conteúdo de cada bloco de marca nas duas larguras possíveis."""
        corpo = []
        for cod, (ep, es) in self.escalas.items():
            html_m = self.conteudo(pecas[cod], ep, es)
            for w in (LARGO, ESTREITO):
                corpo.append(f'<div class="medir" id="{cod}-{w}" style="width:{w}mm;'
                             f'margin:0 0 8mm">{html_m}</div>')
        pagina = (f"<!doctype html><html><head><meta charset='utf-8'><style>{fl.CSS}</style>"
                  f"</head><body>{''.join(corpo)}</body></html>")
        caminho = os.path.join(pasta, "_medidas.html")
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(pagina)
        js = os.path.join(fl.COMUM, "mede_blocos.js")
        r = subprocess.run(["node", js, caminho], capture_output=True, text=True, check=True)
        os.remove(caminho)
        return json.loads(r.stdout)

    @staticmethod
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

    def monta(self, medidas, codigos):
        """Distribui os blocos das marcas no menor número de folhas (busca exaustiva com
        poda); em cada folha, as marcas ficam em ordem de código."""
        melhor = [None]

        def busca(k, grupos):
            if melhor[0] is not None and len(grupos) >= len(melhor[0]):
                return
            if k == len(codigos):
                melhor[0] = [list(g) for g in grupos]
                return
            cod = codigos[k]
            for g in grupos:
                if self._arruma(medidas, g + [cod]) is not None:
                    g.append(cod)
                    busca(k + 1, grupos)
                    g.pop()
            if self._arruma(medidas, [cod]) is None:
                raise SystemExit(f"bloco da marca {cod} não cabe na folha A3: reduzir a escala")
            grupos.append([cod])
            busca(k + 1, grupos)
            grupos.pop()

        busca(0, [])
        folhas = [self._arruma(medidas, g) for g in melhor[0]]
        return sorted(folhas, key=lambda f: min(c for c, *_ in f))

    def folha(self, doc, pecas, itens, titulo=None):
        """Folha de detalhe; 'titulo' substitui o nome da fôrma no título da folha."""
        conteudo, escalas, cods = "", set(), []
        for cod, x, y, w, h in itens:
            p = pecas[cod]
            ep, es = self.escalas[cod]
            conteudo += fl.bloco(x, y, w, h + 0.5, self.conteudo(p, ep, es))
            escalas.add(ep)
            if p.linhas:
                escalas.add(es)
            if cod in self.vista_parcial:
                escalas.add(self.vista_parcial[cod][0])
            cods.append(cod)
        forma = titulo or U(self.nomes_formas[pecas[cods[0]].forma])
        cods = sorted(cods)
        marcas = cods[0] if len(cods) == 1 else ", ".join(cods[:-1]) + " E " + cods[-1]
        termo = "DA MARCA" if len(cods) == 1 else "DAS MARCAS"
        esc_txt = "1:" + " E 1:".join(str(e) for e in sorted(escalas)) if len(escalas) < 3 \
            else "INDICADAS"
        doc.folha(f"{forma} – DETALHE {termo} {marcas}", esc_txt, conteudo)


# --------------------------------------------------------------------------
# FOLHAS GERAIS
# --------------------------------------------------------------------------
CAPACIDADES = (160, 125, 100, 80, 63)


def convencoes(exemplo):
    """Legenda gráfica das linhas e representações usadas nas pranchas; 'exemplo' é a marca
    mostrada na indicação de marca."""
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
             f'{fl.esc(exemplo)}</text><text x="54" y="{y + 0.9}" font-size="2.5">INDICAÇÃO DE '
             f'MARCA (PEÇA DE CHAPA DETALHADA NESTE CONJUNTO)</text>')
    o.append("</svg>")
    return f'<div><div class="bloco-tit">CONVENÇÕES</div>{"".join(o)}</div>'


def folha_parametros(doc, pecas, capacidades=CAPACIDADES):
    lin = []
    for t, d in ch.DOBRA.items():
        marcas = [p.codigo for p in pecas.values() if p.t == t and p.linhas]
        _, ba = ch.dados_dobra(t, 90)
        lin.append([f"{ch.fmt_t(t)}", f1(d["ri"]), f"{d['k']:.2f}".replace(".", ","), d["v"],
                    f1(ch.ABA_MINIMA_FATOR * d["v"]), f1(ba),
                    f1(ch.forca_dobra_tf(t, 1000)), ", ".join(marcas)])
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
    for cap in capacidades:
        alter, sem = [], []
        for p in pecas.values():
            if not p.linhas:
                continue
            v = ch.matriz_para_capacidade(p, cap)
            if v is None:
                sem.append(p.codigo)
            elif v != ch.DOBRA[p.t]["v"]:
                alter.append(f"{p.codigo} V{v}")
        adeq.append([f"{cap} tf", f1(cap * ch.DOBRADEIRA["uso_maximo"]),
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
        f = ch.forca_dobra_tf(p.t, p.comprimento)
        esf.append([p.codigo, ch.fmt_t(p.t), f1(p.comprimento), ch.DOBRA[p.t]["v"],
                    len(p.linhas), f1(f), f1(f / ch.DOBRADEIRA["uso_maximo"])])
    tab_esf = fl.tabela(["MARCA", "ESPESSURA (mm)", "COMPRIMENTO DE DOBRA", "ABERTURA DO V",
                         "DOBRAS", "FORÇA (tf)", "CAPACIDADE NECESSÁRIA (tf)"], esf,
                        titulo="QUADRO DE ESFORÇOS DE DOBRA",
                        classes=["c", "c", "n", "n", "n", "n", "n"])
    conteudo = (fl.bloco(4, 4, 200, 269, f'<div class="pilha">{tab_par}{expr}{equip}{tab_adeq}'
                         f'{obs_adeq}</div>')
                + fl.bloco(210, 4, 176, H_DIR, f'<div class="pilha">{tab_esf}</div>'))
    doc.folha("PARÂMETROS DE CORTE E DOBRA E ESFORÇOS DE DOBRA", "SEM ESCALA", conteudo)


def lista_materiais(pecas, forma, extras, titulo):
    lin = []
    for p in pecas.values():
        if p.forma != forma:
            continue
        lin.append([p.codigo, U(p.nome), ch.fmt_t(p.t), p.qtd,
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


def folha_listas(doc, pecas, compras):
    lin = []
    for p in pecas.values():
        lin.append([p.codigo, U(p.nome), ch.fmt_t(p.t), p.qtd,
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
             UNIDADES[u]] for d, q, u in compras]
    tab_comp = fl.tabela(["ITEM", "QUANTIDADE", "UNIDADE"], comp,
                         titulo="ITENS COMERCIAIS E MATERIAIS DE CONSUMO",
                         classes=["", "c", "c"], larguras=["76%", "12%", "12%"])
    conteudo = (fl.bloco(4, 4, 200, 269, tab)
                + fl.bloco(210, 4, 176, H_DIR, f'<div class="pilha">{tab_arq}</div>'))
    doc.folha("LISTA GERAL DE CORTE E ARQUIVOS DIGITAIS", "SEM ESCALA", conteudo)
    doc.folha("ITENS COMERCIAIS E MATERIAIS DE CONSUMO", "SEM ESCALA",
              fl.bloco(4, 4, 200, 269, tab_comp))


def imprime_e_verifica(doc, html_path, pdf_path, medidas=False):
    """Grava o HTML, imprime o PDF e roda a verificação de sobreposição das folhas."""
    if fl.grava_e_imprime(doc, html_path, pdf_path):
        print("PDF:", pdf_path, f"({len(doc.folhas)} folhas)")
    js = os.path.join(fl.COMUM, "verifica_folhas.js")
    args = ["node", js, html_path] + (["--medidas"] if medidas else [])
    r = subprocess.run(args, capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip()[:400])
    return r.returncode == 0
