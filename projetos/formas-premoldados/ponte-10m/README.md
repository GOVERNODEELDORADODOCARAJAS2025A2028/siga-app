# Ponte em concreto pré-moldado, vão único de 10,00 m: anteprojeto e fôrmas metálicas

**Situação: anteprojeto para análise técnica, não liberado para fabricação.** As dimensões dos
elementos de concreto resultam de pré-dimensionamento. A fabricação das fôrmas depende das
condicionantes do memorial descritivo MD-01, seção 10.

| Identificação | Dados |
|---|---|
| Proprietário | Prefeitura Municipal de Eldorado do Carajás – PA, CNPJ 84.139.633/0001-75; Rua Rio Vermelho, esquina com Belo Horizonte, Centro, km 100, CEP 68.524-000 |
| Prefeito Municipal | Wagne Costa Machado |
| Responsável técnico pelo projeto | A designar (CREA e ART a informar) |
| Análise técnica | Eng. Jean Carlos da Mota Sarcedo, CREA-PA nº 1516847989, matrícula nº 17.120 |

## 1. Documentos

| Documento | Arquivo | Formato |
|---|---|---|
| AG-01: arranjo geral (corte longitudinal 1:50, seção transversal 1:25, cabeceira 1:50, planta do pilar 1:10, quadro dos elementos, notas gerais) | `saida/pranchas/AG-01_arranjo_geral_A1.pdf` | A1 |
| FM-01 a FM-23: fôrmas metálicas (índice e notas gerais, parâmetros de corte e dobra, conjuntos, detalhes das 23 marcas, listas gerais) | `saida/pranchas/FM_formas_metalicas_A3.pdf` | A3 |
| MD-01: memorial descritivo | `saida/pranchas/MD-01_memorial_descritivo.pdf` | A4 |
| Arquivos de corte, de corte e gravação e de desenho de cada marca | `saida/dxf/` | DXF R2000 |
| Lista de corte, tabela de dobras, itens comerciais, quadro dos elementos e resumo | `saida/tabelas/` | CSV e TXT |

As pranchas seguem a ABNT NBR 16752:2020 (folhas de desenho: margem esquerda de 20 mm,
demais de 10 mm, legenda de 180 mm) e a ABNT NBR 16861:2020 (linhas e escrita). A legenda traz
a bandeira do Município, os dados do proprietário, o Prefeito Municipal, os campos do
responsável técnico pelo projeto (nome, CREA, ART e assinatura) e o campo da análise técnica,
com assinatura e data. O registro da análise consta também do memorial MD-01, seção 11.

## 2. Configuração adotada

| Parâmetro | Valor | Situação |
|---|---|---|
| Vão | Vão único: longarina de 10,00 m, vão teórico de 9,60 m | Definição do contratante |
| Comprimento entre faces das cortinas | 10,10 m | Calculado |
| Abertura livre | 9,00 m entre as faces dos pilares, sem apoio no leito do rio | A verificar no estudo hidrológico |
| Largura | 4,50 m; pista de 3,70 m entre guarda-rodas | Definição do contratante |
| Altura útil das cabeceiras | 4,76 m (placas 3,00 m, travessa 0,60 m, cortina 1,16 m) | Ajustada ao módulo das placas |
| Apoios | 2 cabeceiras com 3 pilares cada | Definição do contratante |
| Carga móvel | TB-450 (ABNT NBR 7188:2024) | A confirmar |
| Materiais | C30 e CA-50 | A confirmar |

## 3. Fôrmas detalhadas

| Fôrma | Elemento | Jogo | Marcas | Peças | Aço |
|---|---|---|---|---|---|
| F-LON | Longarina P-01, 300 × 900 × 10000 mm | 1 jogo de 4 módulos de 2500 mm | 8 | 142 | 1.778 kg |
| F-PLA | Placa de saia P-07, 2000 × 500 × 150 mm | 3 fôrmas | 4 | 27 | 401 kg |
| F-LAJ | Painel de laje P-02, 4500 × 1230 × 200 mm | 1 fôrma (8 painéis em 8 ciclos) | 11 | 70 | 723 kg |

Fôrmas ainda não detalhadas: pilar (F-PIL), travessa (F-TRA), cortina (F-COR), sapata (F-SAP),
guarda-rodas (F-GUA) e laje de transição (F-LTR), dependentes do projeto estrutural e da
sondagem.

## 4. Arquivos digitais

- `<marca>_CORTE.dxf`: contorno e furos, em milímetros. É o arquivo de corte.
- `<marca>_CORTE_E_GRAVACAO.dxf` (F-LON-01, F-LON-05, F-PLA-01, F-LAJ-01 e F-LAJ-05): corte
  na camada `CORTE` e linhas de gravação a laser na camada `GRAVACAO` (eixos das nervuras e
  limites da régua da chave de cisalhamento).
- `<marca>_DESENHO.dxf`: conferência, com as camadas `DOBRA`, `GRAVACAO` e `TEXTO`. Não se
  destina ao corte.

Todas as peças estão representadas pela face superior na mesa de corte. O sentido de cada
dobra (para cima ou para baixo) é referido a essa face.

## 5. Geração

```
pip install ezdxf
cd gerador
python3 gerar_formas.py      # DXF, SVG e tabelas; verificações automáticas
python3 gerar_pranchas.py    # pranchas FM em A3 (Node.js com Playwright)
python3 gerar_arranjo.py     # prancha AG-01 em A1
python3 gerar_memorial.py    # memorial MD-01 em A4
```

Dados de identificação (proprietário, Prefeito, analista, situação e revisões) no início de
`gerador/folhas.py`; bandeira do Município em `gerador/logo_eldorado.png`.

Parâmetros no início de `gerador/gerar_formas.py`:

- `VIGA`, `PLACA` e `PAINEL`: dimensões dos elementos de concreto.
- `DOBRA`: raio interno, fator K e abertura da matriz por espessura (valores de referência, a
  substituir pela tabela do ferramental do fabricante).
- `DOBRADEIRA`: capacidade nominal em tf (a preencher pela placa de identificação); com ela,
  o gerador recusa dobra acima de 85% da capacidade.

O gerador verifica a distância dos furos às bordas e às linhas de dobra, a aba mínima para a
matriz, o comprimento de dobra (até 3000 mm), a intercambialidade dos módulos do fundo do
painel e a simetria da furação dos trilhos. Os desenhos em escala ficam em
`gerador/desenhos.py`; a folha, a legenda e o estilo de impressão, em `gerador/folhas.py`.

## 6. Condicionantes para liberação da fabricação

1. Aprovação das dimensões dos elementos de concreto pelo responsável técnico do projeto
   estrutural, com ART (Lei nº 6.496/1977).
2. Tabela de dobra do fabricante (raio interno, fator K, abertura de matriz) e capacidade
   nominal da dobradeira.
3. Regeneração dos arquivos de corte com os dados confirmados e emissão das pranchas em
   revisão liberada para fabricação.
4. Fabricação e inspeção dimensional de um módulo-piloto de cada fôrma.
5. Objeto contratual do fornecedor compatível com o serviço de corte e dobra (Lei nº
   14.133/2021, arts. 124 e 125).

Condicionantes da obra (projeto executivo, licenciamento ambiental e outorga de recursos
hídricos): memorial MD-01, seção 10.
