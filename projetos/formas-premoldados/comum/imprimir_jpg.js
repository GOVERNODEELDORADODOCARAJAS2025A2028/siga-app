// Captura páginas HTML em JPG: node imprimir_jpg.js <largura> <altura> <html> <jpg> [<html> <jpg> ...]
const { chromium } = require("playwright");
const path = require("path");

(async () => {
  const [w, h, ...pares] = process.argv.slice(2);
  const navegador = await chromium.launch();
  const pagina = await navegador.newPage({ viewport: { width: +w, height: +h } });
  for (let i = 0; i < pares.length; i += 2) {
    await pagina.goto("file://" + path.resolve(pares[i]));
    await pagina.screenshot({ path: pares[i + 1], type: "jpeg", quality: 90 });
  }
  await navegador.close();
})();
