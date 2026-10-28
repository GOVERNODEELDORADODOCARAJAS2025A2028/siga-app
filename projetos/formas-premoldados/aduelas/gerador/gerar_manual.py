#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manual de serviço MS-02 (formato A4) do corte a laser e da dobra das fôrmas das aduelas:
peça de teste, sequência de corte, sequência de dobra e registros de conferência.

Gera saida/pranchas/MS-02_manual_de_corte_e_dobra.pdf e uma imagem JPG por página em
saida/manual_jpg/.

Uso:  python3 gerar_manual.py      (rodar depois de gerar_formas.py e gerar_vistas_3d.py)
"""

import base64
import glob
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gerar_formas as gf                 # noqa: E402
import chapas as ch                       # noqa: E402
import folhas as fl                       # noqa: E402

fl.configura(**gf.IDENTIFICACAO)

PASTA = os.path.join(gf.SAIDA, "pranchas")
PASTA_JPG = os.path.join(gf.SAIDA, "manual_jpg")
TESTE = ("A100", 13)          # peça de teste: corte, furos e duas dobras em chapa de 4,75 mm

# sequência de corte: uma troca de espessura; as peças que vão à dobradeira saem primeiro
FASES_CORTE = [
    ("1", 4.75, "Peças a dobrar", (3, 10, 7, 14, 6, 13)),
    ("2", 4.75, "Painéis planos (com gravação)", (1, 2, 8, 9)),
    ("3", 6.30, "Cantoneiras a dobrar", (4, 11, 5, 12)),
    ("4", 6.30, "Peças planas da base, do anel e acessórios", (16, 17, 18, 19, 20, 21, 15, 22)),
]
# sequência de dobra: matriz V 40 (4,75 mm) e depois V 50 (6,30 mm); perfis iguais em seguida
ORDEM_DOBRA = (3, 10, 7, 14, 6, 13, 4, 11, 5, 12)

CSS = """
@page{size:A4;margin:22mm 14mm 16mm 22mm}
*{box-sizing:border-box}
body{margin:0;font-family:"Liberation Sans",Arial,sans-serif;font-size:10pt;line-height:1.4;
  color:#000;text-align:justify;hyphens:auto}
h1{font-size:15pt;margin:0 0 2mm;text-align:left}
h2{font-size:11pt;margin:6mm 0 2mm;text-transform:uppercase;break-after:avoid}
h3{font-size:10pt;margin:4mm 0 1.5mm;break-after:avoid}
p{margin:0 0 2mm;orphans:3;widows:3}
ol{margin:0 0 2.5mm;padding-left:6mm}
li{margin:0 0 1.2mm}
table{border-collapse:collapse;width:100%;margin:1mm 0 3mm;break-inside:avoid}
tr{break-inside:avoid}
th,td{border:.25mm solid #000;padding:.7mm 1.2mm;font-size:8.3pt;line-height:1.22;
  vertical-align:top;text-align:left}
th{font-weight:700;text-align:center;vertical-align:middle}
td.n{text-align:right;white-space:nowrap}
td.c{text-align:center}
caption{caption-side:top;text-align:left;font-weight:700;font-size:9pt;padding:0 0 1mm}
.capa{border:.5mm solid #000;padding:5mm 6mm;margin:0 0 5mm}
.capa .ent{display:flex;align-items:center;gap:4mm;border-bottom:.3mm solid #000;
  padding:0 0 3mm;margin:0 0 4mm;text-align:left}
.capa .ent img{height:17mm}
.capa .ent .t{font-size:10.5pt;font-weight:700;margin:0 0 .8mm}
.capa .ent .e{font-size:8.5pt;line-height:1.3}
.capa .s{font-size:10.5pt;font-weight:700;margin:0 0 3mm;text-align:left}
.fig{width:100%;border:.25mm solid #000;margin:1mm 0 3mm;break-inside:avoid}
.quebra{break-before:page}
.obs{font-size:9pt}
"""


def num(v, casas=1):
    s = f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s[:-2] if s.endswith(",0") else s


def tab(cab, linhas, titulo=None, classes=None, larguras=None):
    return fl.tabela(cab, linhas, titulo=titulo, classes=classes, larguras=larguras)


def figura(caminho):
    with open(caminho, "rb") as f:
        dado = base64.b64encode(f.read()).decode()
    return f'<img class="fig" src="data:image/jpeg;base64,{dado}">'


def marca(cod, n):
    return f"F-{cod}-{n:02d}"


def arquivo(p):
    return f"{p.codigo}_CORTE{'_E_GRAVACAO' if p.marcas else ''}.dxf"


def dobras(p):
    """Passos de dobra: número, ângulo, sentido, borda no batente e distância da linha de
    dobra a essa borda, na ordem de execução."""
    for r, g in zip(ch.roteiro_de_dobra(p), p.giros):
        yield (r["n"], f"{num(r['ang'])}°", "PARA CIMA" if g > 0 else "PARA BAIXO",
               "INFERIOR" if r["borda"] == "A" else "SUPERIOR",
               num(r["da"] if r["borda"] == "A" else r["db"]))


def secao_teste(h):
    cod, n = TESTE
    p = {q.codigo: q for q in gf.todas_as_pecas(cod)}[marca(cod, n)]
    d = ch.DOBRA[p.t]
    h.append("<h2>2. Peça de teste</h2>")
    h.append(f"<p>Antes do lote, corta-se e dobra-se uma única peça, a marca {p.codigo} "
             f"({p.nome.lower()}), em chapa de {ch.fmt_t(p.t)} mm. A peça reúne contorno, "
             f"{len(p.furos)} furos e {len(p.linhas)} dobras de 90°, e permite conferir de uma "
             f"vez a escala do arquivo, a posição dos furos, o raio interno e o desenvolvimento "
             f"da dobra com o ferramental da dobradeira. O resultado é registrado no quadro "
             f"desta seção e submetido à análise técnica antes da liberação do lote.</p>")
    h.append(figura(os.path.join(gf.SAIDA, cod, "vistas_3d", p.codigo + ".jpg")))
    passos = [
        f"Conferir a espessura da chapa com paquímetro ({ch.fmt_t(p.t)} mm) e registrar o valor "
        f"medido.",
        f"Carregar no laser o arquivo {arquivo(p)}, em milímetros, sem escala nem espelhamento, "
        f"com a face superior da chapa para cima.",
        "Cortar uma peça e retirar a rebarba das bordas e dos furos.",
        f"Medir a planificação ({num(p.comprimento)} × {num(p.largura)} mm) e a posição dos "
        f"furos em relação à origem (canto inferior esquerdo da vista pela face superior), "
        f"conforme a prancha de detalhe da marca.",
        f"Preparar a dobradeira com matriz de abertura {d['v']} mm e punção compatível com raio "
        f"interno de {num(d['ri'])} mm.",
    ]
    for k, (nd, ang, sentido, borda, dist) in enumerate(dobras(p), 6):
        passos.append(f"Dobra {nd}: {ang} {sentido.lower()}, com a borda {borda.lower()} no "
                      f"batente e a linha de dobra a {dist} mm dessa borda.")
    passos.append(f"Medir as abas externas ({' / '.join(num(x) for x in p.abas)} mm), os "
                  f"ângulos e o comprimento ({num(p.comprimento)} mm) e preencher o quadro.")
    passos.append("Se alguma aba estiver fora da tolerância, informar o raio interno real do "
                  "ferramental e a medida obtida, para recálculo das planificações e nova "
                  "emissão dos arquivos de corte, antes do lote.")
    h.append("<ol>" + "".join(f"<li>{fl.esc(s)}</li>" for s in passos) + "</ol>")
    vazio = fl.Bruto("&nbsp;")
    lin = [["Espessura da chapa", f"{ch.fmt_t(p.t)} mm", "conforme norma da chapa", vazio, vazio],
           ["Comprimento", f"{num(p.comprimento)} mm", "±0,5 mm", vazio, vazio],
           ["Largura planificada", f"{num(p.largura)} mm", "±0,5 mm", vazio, vazio]]
    for i, (x, y, dd) in enumerate(p.furos, 1):
        lin.append([f"Furo {i} (X; Y; diâmetro)", f"{num(x)}; {num(y)}; {num(dd)} mm",
                    "±0,5 mm", vazio, vazio])
    for i, a in enumerate(p.abas, 1):
        lin.append([f"Aba externa {i}", f"{num(a)} mm", "±1 mm", vazio, vazio])
    for i in range(len(p.angulos)):
        lin.append([f"Ângulo da dobra {i + 1}", f"{num(p.angulos[i])}°", "±1°", vazio, vazio])
    h.append(tab(["ITEM", "VALOR DE PROJETO", "TOLERÂNCIA", "MEDIDO", "CONFORME"], lin,
                 titulo=f"Quadro 1 – Conferência da peça de teste {p.codigo}",
                 classes=["", "c", "c", "c", "c"], larguras=["30%", "24%", "18%", "16%", "12%"]))
    h.append(tab(None, [["Operador do corte (nome e data)", vazio],
                        ["Operador da dobra (nome e data)", vazio],
                        ["Análise técnica", f"{fl.ANALISTA} – {fl.ANALISTA_REGISTRO}"],
                        ["Resultado e assinatura da análise",
                         fl.Bruto("<div style='height:16mm'></div>")]],
                 titulo="Registro do teste", larguras=["38%", "62%"]))


def secao_corte(h, cod, a, pecas):
    h.append(f"<h3>Aduela {a['nome']} – sequência de corte</h3>")
    lin, ordem = [], 1
    for fase, t, desc, marcas in FASES_CORTE:
        for n in marcas:
            p = pecas[marca(cod, n)]
            assert p.t == t
            lin.append([ordem, f"{fase} – {ch.fmt_t(t)} mm", p.codigo, p.nome, p.qtd,
                        f"{num(p.comprimento)} × {num(p.largura)}", arquivo(p),
                        "SIM" if p.linhas else "NÃO"])
            ordem += 1
    assert ordem - 1 == len(pecas)
    h.append(tab(["ORDEM", "FASE E CHAPA", "MARCA", "PEÇA", "QTD.", "PLANIFICAÇÃO (mm)",
                  "ARQUIVO DE CORTE", "DOBRA"], lin,
                 classes=["c", "c", "c", "", "c", "c", "", "c"],
                 larguras=["6%", "10%", "12%", "27%", "5%", "12%", "21%", "7%"]))


def secao_dobra(h, cod, a, pecas):
    h.append(f"<h3>Aduela {a['nome']} – sequência de dobra</h3>")
    grupos, ordem = {}, 1
    for n in ORDEM_DOBRA:
        p = pecas[marca(cod, n)]
        grupos.setdefault(ch.DOBRA[p.t]["v"], (p.t, []))[1].append(p)
    for v, (t, ps) in grupos.items():
        d = ch.DOBRA[t]
        lin = []
        for p in ps:
            for nd, ang, sentido, borda, dist in dobras(p):
                lin.append([ordem, p.codigo, p.qtd, num(p.comprimento), nd, ang, sentido, borda,
                            dist, num(ch.forca_dobra_tf(p.t, p.comprimento))])
                ordem += 1
        h.append(tab(["ORDEM", "MARCA", "QTD.", "COMPR. DE DOBRA (mm)", "DOBRA", "ÂNGULO",
                      "SENTIDO", "BORDA NO BATENTE", "LINHA DE DOBRA À BORDA (mm)",
                      "FORÇA (tf)"], lin,
                     titulo=f"Matriz V {v} – chapa {ch.fmt_t(t)} mm – raio interno "
                            f"{num(d['ri'])} mm",
                     classes=["c", "c", "c", "n", "c", "c", "c", "c", "n", "n"],
                     larguras=["7%", "13%", "6%", "11%", "7%", "8%", "12%", "12%", "14%",
                               "10%"]))


def main():
    os.makedirs(PASTA, exist_ok=True)
    os.makedirs(PASTA_JPG, exist_ok=True)
    rev, data, rev_txt = fl.REVISOES[-1]
    h = [f"""<div class="capa">
<div class="ent"><img src="{fl.LOGO_URI}" alt="Bandeira do Município de Eldorado do Carajás">
<div><div class="t">{fl.esc(fl.PROPRIETARIO)}</div><div class="e">CNPJ {fl.CNPJ}</div>
<div class="e">{fl.esc(fl.ENDERECO)}</div></div></div>
<h1>MANUAL DE SERVIÇO MS-02</h1>
<div class="s">CORTE A LASER E DOBRA DAS FÔRMAS METÁLICAS DAS ADUELAS DE 1,00 m, 2,00 m E
2,50 m – PEÇA DE TESTE, SEQUÊNCIA DE CORTE E SEQUÊNCIA DE DOBRA</div>
{tab(None, [["PROPRIETÁRIO", f"{fl.PROPRIETARIO}, CNPJ {fl.CNPJ}"],
            ["PREFEITO MUNICIPAL", fl.PREFEITO], ["SITUAÇÃO", fl.SITUACAO],
            ["REVISÃO", f"{rev} – {rev_txt}"], ["DATA", fl.DATA],
            ["RESPONSÁVEL TÉCNICO PELO PROJETO", "A DESIGNAR (CREA E ART A INFORMAR)"],
            ["ANÁLISE TÉCNICA", f"{fl.ANALISTA} – {fl.ANALISTA_REGISTRO}"]],
        larguras=["32%", "68%"])}
</div>"""]
    h.append("<h2>1. Objeto e documentos de referência</h2>")
    h.append("<p>Este manual estabelece a ordem de execução do corte a laser e da dobra das "
             "peças de chapa das fôrmas das aduelas, a peça de teste que antecede o lote e os "
             "registros de conferência. As medidas, furos e dobras de cada marca constam das "
             "pranchas FA100, FA200 e FA250; os arquivos de corte, das pastas dxf de cada "
             "tamanho; e as vistas em perspectiva de cada marca, antes e depois da dobra, das "
             "pastas vistas_3d. Prevalecem as pranchas em caso de divergência.</p>")
    h.append("<ol>"
             "<li>Raio interno, fator K e abertura de matriz adotados são de referência e devem "
             "ser confirmados com o ferramental da dobradeira na peça de teste.</li>"
             "<li>Todas as peças estão representadas pela face superior na mesa de corte; o "
             "sentido de cada dobra (para cima ou para baixo) refere-se a essa face.</li>"
             "<li>As peças com gravação recebem as linhas de posição de solda na camada GRAVACAO "
             "do arquivo de corte e gravação, executada antes do corte do contorno.</li>"
             "<li>Cada peça é identificada com a marca, a giz ou marcador industrial, na face "
             "que não fica em contato com o concreto, logo após o corte.</li></ol>")
    secao_teste(h)
    h.append("<h2 class='quebra'>3. Sequência de corte</h2>")
    h.append("<p>O corte é feito em quatro fases, com uma única troca de espessura de chapa. "
             "As peças que vão à dobradeira saem primeiro, de modo que a dobra começa enquanto o "
             "laser corta os painéis e as peças planas. Dentro de cada fase, as peças maiores "
             "são aninhadas primeiro na chapa e as menores ocupam as sobras.</p>")
    tam = {cod: gf.geometria(cod) for cod in gf.ADUELAS}
    pecas = {cod: {p.codigo: p for p in gf.todas_as_pecas(cod)} for cod in gf.ADUELAS}
    for cod in gf.ADUELAS:
        secao_corte(h, cod, tam[cod], pecas[cod])
    h.append("<h2 class='quebra'>4. Sequência de dobra</h2>")
    h.append("<p>A dobra começa pelas peças de 4,75 mm, com matriz V 40, e passa às de 6,30 mm, "
             "com matriz V 50, com uma única troca de ferramental. Peças de mesmo perfil são "
             "dobradas em seguida, sem mudar o batente. Em peças com mais de uma dobra, todas as "
             "peças do lote recebem a dobra 1 antes da dobra 2. A distância indicada vai da "
             "borda encostada no batente ao centro da linha de dobra da planificação.</p>")
    for cod in gf.ADUELAS:
        secao_dobra(h, cod, tam[cod], pecas[cod])
    h.append("<h2>5. Cuidados de operação</h2>")
    h.append("<ol>"
             "<li>Nervuras em perfil U com alma de 40 mm e abas de 63 mm (marcas 07 e 14): na "
             "dobra 2, verificar a folga entre a aba já dobrada e o punção; se houver "
             "interferência, usar punção do tipo pescoço de ganso.</li>"
             "<li>Cantoneiras de 6,30 mm com mais de 2,0 m de comprimento de dobra exigem a "
             "força indicada na sequência de dobra; acima da capacidade da dobradeira, adotar a "
             "matriz alternativa da prancha 02 de cada conjunto.</li>"
             "<li>Conferir o ângulo da primeira peça de cada marca com esquadro ou goniômetro "
             "antes de dobrar as demais.</li>"
             "<li>Peças de fôrma com mais de 60 kg são movimentadas por meio mecânico ou por "
             "mais de um trabalhador (CLT, art. 198, e NR-17); uso de luvas, óculos e calçado de "
             "segurança no corte e na dobra (NR-6 e NR-12).</li>"
             "<li>Faces em contato com o concreto ficam isentas de respingo, rebarba e marca de "
             "solda.</li></ol>")
    h.append("<h2>6. Condicionante</h2>")
    h.append("<p>As peças e os arquivos integram anteprojeto para análise técnica. A produção do "
             "lote depende da aprovação da peça de teste e da Anotação de Responsabilidade "
             "Técnica do profissional responsável pelo projeto e pela fabricação das fôrmas "
             "(Lei nº 6.496/1977, art. 1º).</p>")
    doc = ("<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'><title>Manual de "
           "serviço MS-02</title><style>" + CSS + "</style></head><body>" + "".join(h) +
           "</body></html>")
    base = os.path.join(PASTA, "MS-02_manual_de_corte_e_dobra")
    cab = (f"{fl.PROPRIETARIO} &nbsp;|&nbsp; MANUAL DE SERVIÇO MS-02 &nbsp;|&nbsp; REVISÃO {rev} "
           f"&nbsp;|&nbsp; {fl.DATA}")
    if fl.grava_e_imprime(doc, base + ".html", base + ".pdf", cabecalho=cab):
        os.remove(base + ".html")
        for antiga in glob.glob(os.path.join(PASTA_JPG, "MS-02_pagina-*.jpg")):
            os.remove(antiga)
        subprocess.run(["pdftoppm", "-r", "150", "-jpeg", "-jpegopt", "quality=90", base + ".pdf",
                        os.path.join(PASTA_JPG, "MS-02_pagina")], check=True)
        print("PDF:", base + ".pdf", "| páginas em JPG:", PASTA_JPG)


if __name__ == "__main__":
    main()
