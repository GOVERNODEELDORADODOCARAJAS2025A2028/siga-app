# Formas metálicas de pré-moldados

Projetos de formas de chapa cortada a laser de fibra (cerca de 3 kW) e dobrada (dobradeira de
3 m, da mesma marca do laser), para peças pré-moldadas de concreto. O primeiro é o kit da ponte
de 2 × 10 m em `ponte-10m/`. Marca, modelo e força da dobradeira ainda não confirmados: ver
`ponte-10m/README.md`, seção 8a.

## Padrão de entrega (pedido do usuário)

Toda entrega de forma ou desenho vai com:
1. **Caderno de fabricação em PDF**, enviado na conversa para abrir na hora
   (`SendUserFile` com `display: "render"`). Gerado por `gerador/gerar_caderno.py`.
2. **Pacote zip** com os DXF de corte, os DXF de desenho, as tabelas CSV e o memorial
   (`SendUserFile` com `display: "attach"`).
3. A página do kit atualizada, quando ela existir.

## Regras técnicas que valem para todas as peças

- Nenhuma dobra acima de 3 m; módulos de forma de até 2,50 m.
- Dados de dobra (raio interno, fator K, matriz) são provisórios até o fornecedor enviar a
  tabela da máquina dele. Registrar a força estimada de cada dobra.
- `_CORTE.dxf` só com contorno e furos; o resto vai no `_DESENHO.dxf`. Posição de solda vai
  como gravação a laser no `_CORTE_E_MARCA.dxf` (camada `2_SO_MARCAR`).
- Tudo é anteprojeto: nada se corta sem ART do engenheiro responsável. Deixar isso escrito
  nos arquivos.
