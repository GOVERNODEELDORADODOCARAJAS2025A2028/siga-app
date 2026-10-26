// Confere a montagem das folhas: blocos que transbordam, blocos que se sobrepõem e blocos
// que invadem a legenda ou o quadro de revisões. Uso: node verifica_folhas.js folhas.html
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const [, , entrada, opcao] = process.argv;
  const navegador = await chromium.launch();
  const pagina = await navegador.newPage();
  await pagina.goto('file://' + path.resolve(entrada), { waitUntil: 'load' });
  const problemas = await pagina.evaluate((medidas) => {
    const out = [];
    const mm = 96 / 25.4;
    document.querySelectorAll('section.folha').forEach((folha, i) => {
      const quadro = folha.querySelector('.quadro').getBoundingClientRect();
      const fixos = [...folha.querySelectorAll('.leg, .rev')].map((e) => e.getBoundingClientRect());
      const blocos = [...folha.querySelectorAll('.bl')];
      const caixas = blocos.map((b) => b.getBoundingClientRect());
      blocos.forEach((b, k) => {
        const r = caixas[k];
        const nome = `folha ${i + 1}, bloco ${k + 1}`;
        if (medidas) out.push(`${nome}: conteúdo ${(b.scrollWidth / mm).toFixed(1)} x ${(b.scrollHeight / mm).toFixed(1)} mm em ${(b.clientWidth / mm).toFixed(1)} x ${(b.clientHeight / mm).toFixed(1)} mm`);
        if (!b.classList.contains('solto')) {
          const dx = (b.scrollWidth - b.clientWidth) / mm;
          const dy = (b.scrollHeight - b.clientHeight) / mm;
          if (dx > 0.3 || dy > 0.3) out.push(`${nome}: transborda ${dx.toFixed(1)} x ${dy.toFixed(1)} mm`);
        }
        if (r.left < quadro.left - 1 || r.right > quadro.right + 1 || r.top < quadro.top - 1 ||
            r.bottom > quadro.bottom + 1) out.push(`${nome}: fora do quadro`);
        fixos.forEach((f) => {
          if (r.left < f.right - 1 && r.right > f.left + 1 && r.top < f.bottom - 1 && r.bottom > f.top + 1)
            out.push(`${nome}: invade a legenda`);
        });
        caixas.forEach((o, j) => {
          if (j <= k) return;
          if (r.left < o.right - 1 && r.right > o.left + 1 && r.top < o.bottom - 1 && r.bottom > o.top + 1)
            out.push(`${nome}: sobrepõe o bloco ${j + 1}`);
        });
      });
    });
    return out;
  }, opcao === '--medidas');
  await navegador.close();
  if (problemas.length) {
    console.log(problemas.join('\n'));
    process.exit(1);
  }
  console.log('folhas sem sobreposição nem transbordamento');
})().catch((erro) => {
  console.error(erro);
  process.exit(2);
});
