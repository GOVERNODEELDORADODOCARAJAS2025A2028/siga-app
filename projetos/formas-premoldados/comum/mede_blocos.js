// Mede, em milímetros, a largura e a altura do conteúdo de cada elemento com a classe
// "medir" de uma página HTML. Uso: node mede_blocos.js pagina.html  (saída em JSON)
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const [, , entrada] = process.argv;
  const navegador = await chromium.launch();
  const pagina = await navegador.newPage();
  await pagina.goto('file://' + path.resolve(entrada), { waitUntil: 'load' });
  const medidas = await pagina.evaluate(() => {
    const mm = 96 / 25.4;
    const out = {};
    document.querySelectorAll('.medir').forEach((e) => {
      out[e.id] = [e.scrollWidth / mm, e.scrollHeight / mm];
    });
    return out;
  });
  await navegador.close();
  console.log(JSON.stringify(medidas));
})().catch((erro) => {
  console.error(erro);
  process.exit(2);
});
