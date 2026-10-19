// SIGA — service worker: guarda a "casca" do sistema para abrir rápido e com internet fraca.
// Dados (Supabase) NUNCA ficam em cache: sempre vêm do banco, com a permissão de quem está logado.
const VERSAO = "siga-v1";
const CASCA = ["./", "./index.html", "./manifest.webmanifest", "./icone-192.png", "./icone-512.png"];
self.addEventListener("install", (e) => { e.waitUntil(caches.open(VERSAO).then((c) => c.addAll(CASCA)).then(() => self.skipWaiting())); });
self.addEventListener("activate", (e) => { e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== VERSAO).map((k) => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", (e) => {
  const u = new URL(e.request.url);
  if (e.request.method !== "GET" || u.origin !== self.location.origin) return; // banco, VLibras e demais serviços: direto na rede
  if (e.request.headers.has("range") || /\.(mp4|webm)$/.test(u.pathname)) return; // vídeo da abertura: o navegador pede por partes; vai direto à rede
  e.respondWith(fetch(e.request).then((r) => { const c = r.clone(); caches.open(VERSAO).then((k) => k.put(e.request, c)); return r; })
    .catch(() => caches.match(e.request).then((r) => r || caches.match("./index.html"))));
});
