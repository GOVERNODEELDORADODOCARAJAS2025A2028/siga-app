#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ficha para o fornecedor: o que as fotos mostram sobre a máquina de corte e a dobradeira,
os dados que faltam e o que muda nas formas conforme a capacidade da dobradeira.

Gera saida/ficha/ficha_fornecedor_laser_dobradeira.pdf (A4 deitado).
Uso:  python3 gerar_ficha.py
"""

import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gerar_caderno as gc                # noqa: E402
import gerar_formas as gf                 # noqa: E402

PASTA = os.path.join(gf.SAIDA, "ficha")
HTML_OUT = os.path.join(PASTA, "ficha_fornecedor_laser_dobradeira.html")
PDF_OUT = os.path.join(PASTA, "ficha_fornecedor_laser_dobradeira.pdf")

OPCOES_V = {3.00: [20, 24, 32], 4.75: [32, 40, 50, 63], 6.30: [50, 63, 80, 100]}
CAPACIDADES = (80, 100, 125, 160)
esc, f1 = gc.esc, gc.f1


def forca(t, comprimento, v):
    return 650 * t ** 2 * (comprimento / 1000) / v / 9.81


def decisao(pecas, cap):
    """Peças que precisam de V maior para caber em 'uso_maximo' da capacidade."""
    lim = cap * gf.DOBRADEIRA["uso_maximo"]
    trocas, sem = [], []
    for p in pecas:
        v0 = gf.DOBRA[p.t]["v"]
        if forca(p.t, p.comprimento, v0) <= lim:
            continue
        cand = [v for v in OPCOES_V[p.t] if v > v0 and min(p.abas) >= gf.ABA_MINIMA_FATOR * v
                and forca(p.t, p.comprimento, v) <= lim]
        if cand:
            trocas.append((p, v0, cand[0], forca(p.t, p.comprimento, cand[0])))
        else:
            sem.append(p)
    return lim, trocas, sem


def main():
    pecas = [p for p in gf.todas_as_pecas() if p.linhas]
    os.makedirs(PASTA, exist_ok=True)
    cad = gc.Caderno(linha2="Ficha de levantamento junto ao fornecedor")

    achados = [
        ("Máquina de corte", "Resfriador S&A modelo CWFL-3000, com dois circuitos de água (H e L). "
         "O fabricante indica esse modelo para laser de fibra de 3.000 W.",
         "Corte a laser de fibra, de cerca de 3 kW (não é plasma). Confirmar na plaqueta."),
        ("Ar comprimido", "Compressor de parafuso DEHAHA DBZY-20A com secador. Anunciado como "
         "compressor de 16 bar e 15 kW para linha de corte a laser.",
         "A máquina corta com ar comprimido, além de oxigênio ou nitrogênio, se houver."),
        ("Energia", "Estabilizador de tensão Shanghai Wenfeng Electric.",
         "Acessório da instalação; não identifica a marca da máquina."),
        ("Dobradeira", "Aparece ao fundo de uma foto: pedal de comando com botão de emergência, "
         "proteção amarela e cortinas de luz. A tela do comando não está legível.",
         "Marca, força e comando ainda desconhecidos."),
        ("Marca do laser", "Nenhuma das fotos mostra logotipo ou plaqueta.",
         "Precisa da foto da plaqueta para chegar ao modelo da dobradeira da mesma marca."),
    ]
    linhas_ach = "".join(f"<tr><td><b>{esc(a)}</b></td><td>{esc(b)}</td><td>{esc(c)}</td></tr>"
                         for a, b, c in achados)
    pedir = [
        "Foto da <b>plaqueta da máquina de corte</b>: marca, modelo, potência e tamanho da mesa "
        "(por exemplo, \"3015\" = 3000 × 1500 mm).",
        "Nome e versão do <b>software de corte</b> (por exemplo, CypCut). Confirmar que importa DXF "
        "R2000 e que grava (marca) uma camada sem cortar.",
        "Foto da <b>plaqueta da dobradeira</b>: modelo, força em toneladas e comprimento útil. "
        "Em máquinas chinesas o modelo costuma trazer os dois números, como \"100T/3200\".",
        "Foto da <b>tabela de força</b> fixada na dobradeira (força por metro para cada espessura "
        "e abertura de V).",
        "Lista das <b>matrizes disponíveis</b> (aberturas de V) e o raio da ponta do punção.",
        "<b>Raio interno e fator K</b> (ou a dedução de dobra) que eles usam para chapas de 3,00, "
        "4,75 e 6,30 mm.",
        "Modelo do <b>comando da dobradeira</b> (aparece na tela). Define se o operador digita as "
        "medidas da tabela de dobras ou importa o desenho.",
        "Confirmar no <b>contrato</b> que o serviço de corte e dobra está incluído, e não só o aço.",
    ]
    corpo1 = f"""<div class="capa">
<div style="display:grid;gap:3mm;align-content:start">
<h2 style="margin:0;font-size:12pt">O que as fotos mostram</h2>
<table class="tab"><thead><tr><th>Item</th><th>O que aparece</th><th>Conclusão</th></tr></thead>
<tbody>{linhas_ach}</tbody></table>
<div class="aviso"><b>Consequência:</b> com laser, os furos e contornos saem com mais precisão que
no plasma, e as linhas de posição das soldas podem ser gravadas na própria chapa. Os arquivos
_CORTE_E_MARCA.dxf já trazem essa gravação numa camada separada.</div>
</div>
<div style="display:grid;gap:3mm;align-content:start">
<h2 style="margin:0;font-size:12pt">O que pedir ao fornecedor</h2>
<ol class="passos">{''.join(f'<li>{t}</li>' for t in pedir)}</ol>
</div></div>"""
    cad.add("Ficha para o fornecedor · corte a laser e dobradeira", corpo1, "FICHA")

    linhas_dec = []
    for cap in CAPACIDADES:
        lim, trocas, sem = decisao(pecas, cap)
        if not trocas and not sem:
            txt = "Nada muda: todas as dobras cabem com as matrizes atuais."
        else:
            txt = "; ".join(f"{p.codigo} ({gf.fmt_t(p.t)} mm × {f1(p.comprimento)} mm): V{v0} → "
                            f"V{v1}, {f1(fv)} tf" for p, v0, v1, fv in trocas)
            if sem:
                txt += "; sem solução só com matriz: " + ", ".join(p.codigo for p in sem)
        linhas_dec.append(f"<tr><td class='n'>{cap} t</td><td class='n'>{f1(lim)} tf</td>"
                          f"<td>{esc(txt)}</td></tr>")
    pior = sorted(pecas, key=lambda p: -forca(p.t, p.comprimento, gf.DOBRA[p.t]["v"]))[:8]
    linhas_f = []
    for p in pior:
        v0 = gf.DOBRA[p.t]["v"]
        alts = " · ".join(f"V{v}: {f1(forca(p.t, p.comprimento, v))}"
                          + ("" if min(p.abas) >= gf.ABA_MINIMA_FATOR * v else " (aba curta)")
                          for v in OPCOES_V[p.t])
        linhas_f.append(f"<tr><td class='n'>{p.codigo}</td><td>{esc(p.nome)}</td>"
                        f"<td class='n'>{gf.fmt_t(p.t)}</td><td class='n'>{f1(p.comprimento)}</td>"
                        f"<td class='n'>V{v0}: {f1(forca(p.t, p.comprimento, v0))}</td>"
                        f"<td class='n'>{esc(alts)}</td></tr>")
    corpo2 = f"""<div style="display:grid;gap:4mm;align-content:start;min-height:0">
<p style="margin:0;font-size:9pt">Forças estimadas pela fórmula usual de dobra no ar
(P = 650 · t² · L / V, em kN), com uso de até {int(gf.DOBRADEIRA['uso_maximo'] * 100)}% da
capacidade da máquina. V maior pede menos força, mas aumenta o raio interno e exige aba maior; as
planificações são recalculadas quando chegarem os dados reais.</p>
<table class="tab"><thead><tr><th>Capacidade da dobradeira</th><th>Força máxima por dobra</th>
<th>O que muda nas formas</th></tr></thead><tbody>{''.join(linhas_dec)}</tbody></table>
<table class="tab"><thead><tr><th>Peça</th><th>Nome</th><th>Chapa (mm)</th><th>Dobra (mm)</th>
<th>Força atual (tf)</th><th>Com outras matrizes (tf)</th></tr></thead>
<tbody>{''.join(linhas_f)}</tbody></table>
<div class="aviso"><b>Como usar:</b> quando a plaqueta informar a força, basta preencher
DOBRADEIRA["capacidade_tf"] no gerador. Ele passa a recusar qualquer dobra acima do limite, e
os arquivos saem de novo com as matrizes certas.</div>
</div>"""
    cad.add("O que muda conforme a dobradeira", corpo2, "FICHA")

    with open(HTML_OUT, "w", encoding="utf-8") as f:
        f.write(cad.render())
    js = os.path.join(os.path.dirname(os.path.abspath(__file__)), "imprimir_pdf.js")
    if shutil.which("node"):
        r = subprocess.run(["node", js, HTML_OUT, PDF_OUT], capture_output=True, text=True)
        print("PDF:", PDF_OUT if r.returncode == 0 else r.stderr.strip()[:300])
    else:
        print("HTML:", HTML_OUT)


if __name__ == "__main__":
    main()
