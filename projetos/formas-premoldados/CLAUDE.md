# Fôrmas metálicas de pré-moldados

Projetos de fôrmas de chapa cortada a laser de fibra (cerca de 3 kW) e dobrada (dobradeira de
3 m, da mesma marca do laser), para peças pré-moldadas de concreto. O primeiro é o kit da ponte
de vão único de 10 m em `ponte-10m/`. Capacidade nominal e ferramental da dobradeira ainda não
confirmados.

## Padrão de entrega (pedido do usuário)

1. **Cada PDF enviado diretamente na conversa** (`SendUserFile` com `display: "render"`), nunca
   só dentro do zip: arranjo geral AG-01 (A1), pranchas das fôrmas FM (A3) e memorial MD-01
   (A4), gerados por `gerar_arranjo.py`, `gerar_pranchas.py` e `gerar_memorial.py`.
2. **Pacote zip** com os DXF, as tabelas CSV e os PDFs (`SendUserFile` com
   `display: "attach"`).
3. A página do kit atualizada, quando ela existir.

## Padrão dos documentos (pedido do usuário)

- Redação técnica e formal, como pranchas e memoriais de engenharia. Os documentos não trazem
  perguntas e respostas, texto dirigido ao usuário ("o que você perguntou", "o que pedir à
  empresa") nem linguagem de conversa. Respostas e esclarecimentos vão só na conversa.
- Pranchas conforme ABNT NBR 16752:2020 (margem esquerda de 20 mm, demais de 10 mm, legenda de
  180 mm, quadro de revisões) e ABNT NBR 16861:2020 (linhas e escrita); escalas da NBR 8196.
  Texto em caixa alta, com os símbolos de unidade em minúsculas (mm, m, kg).
- Pendências escritas como condicionantes técnicas ou legais, com a base normativa.
- Estimativas declaradas como estimativas, com hipóteses e método. Nada de símbolos
  informais (setas, "≈", separadores) no lugar de texto.
- Antes de entregar, rodar a verificação de sobreposição (`verifica_folhas.js`, chamada pelos
  geradores) e conferir as folhas renderizadas em imagem.
- Legenda das pranchas e capa do memorial com a bandeira do Município (`logo_eldorado.png`,
  extraída do ícone do SIGA; substituir pelo brasão oficial quando fornecido), os dados da
  Prefeitura (CNPJ e endereço), o Prefeito Municipal, o responsável técnico pelo projeto (a
  designar) e a análise técnica do Eng. Jean Carlos da Mota Sarcedo, com campo de assinatura.
  Os dados ficam em `folhas.py`. CPF não é impresso: a Lei nº 5.194/1966, art. 14, exige
  assinatura, título e número do registro, e a LGPD (art. 6º, III) limita os dados ao
  necessário. O analista não figura como autor nem como responsável técnico.
- Página publicada (Artifact) sem nome, brasão ou marca da Prefeitura.

## Regras técnicas que valem para todas as peças

- Nenhuma dobra acima de 3 m; módulos de fôrma de até 2,50 m.
- Dados de dobra (raio interno, fator K, matriz) são provisórios até o fornecedor enviar a
  tabela da máquina dele. Registrar a força estimada de cada dobra.
- Peças sem lado: furação simétrica sempre que a peça for usada em posições espelhadas; se não
  for possível, marca própria para a peça oposta.
- `_CORTE.dxf` só com contorno e furos; o resto vai no `_DESENHO.dxf`. Posição de solda vai
  como gravação a laser no `_CORTE_E_GRAVACAO.dxf` (camada `GRAVACAO`), na face superior da
  mesa de corte; o sentido das dobras é referido a essa face.
- Tudo é anteprojeto: nada se corta sem ART do engenheiro responsável. Deixar isso escrito
  nos documentos.
