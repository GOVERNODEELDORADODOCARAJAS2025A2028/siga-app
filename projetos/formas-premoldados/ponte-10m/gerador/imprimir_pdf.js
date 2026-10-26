// Imprime o caderno HTML em PDF (A4 deitado) com o Chromium do Playwright.
// Uso: node imprimir_pdf.js entrada.html saida.pdf
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const [, , entrada, saida] = process.argv;
  if (!entrada || !saida) {
    console.error('uso: node imprimir_pdf.js entrada.html saida.pdf');
    process.exit(2);
  }
  const navegador = await chromium.launch();
  const pagina = await navegador.newPage();
  await pagina.goto('file://' + path.resolve(entrada), { waitUntil: 'load' });
  await pagina.pdf({ path: saida, preferCSSPageSize: true, printBackground: true });
  await navegador.close();
})().catch((erro) => {
  console.error(erro);
  process.exit(1);
});
