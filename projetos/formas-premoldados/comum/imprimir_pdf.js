// Imprime um documento HTML em PDF com o Chromium do Playwright, no tamanho de página
// definido pelo CSS (@page). Uso: node imprimir_pdf.js entrada.html saida.pdf [rodapé]
// Com o terceiro argumento, cada página recebe cabeçalho com esse texto e rodapé com a
// numeração "Página n de N".
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const [, , entrada, saida, rodape] = process.argv;
  if (!entrada || !saida) {
    console.error('uso: node imprimir_pdf.js entrada.html saida.pdf [texto do cabeçalho]');
    process.exit(2);
  }
  const navegador = await chromium.launch();
  const pagina = await navegador.newPage();
  await pagina.goto('file://' + path.resolve(entrada), { waitUntil: 'load' });
  const opcoes = { path: saida, preferCSSPageSize: true, printBackground: true };
  if (rodape) {
    const estilo = 'font-family:Liberation Sans,Arial,sans-serif;font-size:7.5pt;color:#000;' +
      'width:100%;margin:0 15mm 0 25mm;';
    opcoes.displayHeaderFooter = true;
    opcoes.headerTemplate = `<div style="${estilo}border-bottom:0.3mm solid #000;padding-bottom:1mm">` +
      `${rodape}</div>`;
    opcoes.footerTemplate = `<div style="${estilo}text-align:right">Página ` +
      '<span class="pageNumber"></span> de <span class="totalPages"></span></div>';
  }
  await pagina.pdf(opcoes);
  await navegador.close();
})().catch((erro) => {
  console.error(erro);
  process.exit(1);
});
