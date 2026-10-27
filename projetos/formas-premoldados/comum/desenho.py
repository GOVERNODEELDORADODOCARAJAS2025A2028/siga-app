#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Desenho técnico em SVG (milímetros, z para cima) comum aos projetos de fôrmas.

Dwg: desenho em milímetros com cotas, chamadas, hachuras vetoriais e texto. Sem escala, o
desenho se ajusta à largura da página (apresentação em tela). Com escala (por exemplo,
escala=50 para 1:50), o SVG sai com largura e altura reais em milímetros de papel, texto de
2,5 mm, terminação de cota em traço oblíquo (desenho civil) ou seta (desenho mecânico) e
hachuras próprias para impressão.

Também ficam aqui os desenhos de uma peça de chapa: planificação (vista pela face superior
na mesa de corte) e seção da peça dobrada.
"""
import html
import math

import chapas as ch

TEXTO_MM = 2.5          # altura do texto no papel

# hachuras vetoriais do modo de impressão: classe -> (tipo, espaçamento em mm de papel)
HACHURAS = {"soil": ("diag", 5.0), "cip": ("cruz", 2.5), "cipd": ("cruz", 2.5),
            "conc": ("pontos", 3.6), "water": ("agua", 3.6), "grout": ("cruz", 1.6)}


def n(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def c(v):
    """Valor de cota com vírgula decimal."""
    return ch.fmt(v)


def espalha(pos, gap):
    """Distribui rótulos em uma direção, mantendo a ordem e uma distância mínima."""
    if not pos:
        return []
    ordem = sorted(range(len(pos)), key=lambda i: pos[i])
    v = [pos[i] for i in ordem]
    for _ in range(80):
        mexeu = False
        for i in range(1, len(v)):
            falta = gap - (v[i] - v[i - 1])
            if falta > 1e-6:
                v[i - 1] -= falta / 2
                v[i] += falta / 2
                mexeu = True
        if not mexeu:
            break
    out = [0.0] * len(pos)
    for k, i in enumerate(ordem):
        out[i] = v[k]
    return out


class Dwg:
    """Desenho em milímetros, com z para cima."""

    def __init__(self, xmin, xmax, zmin, zmax, fs, escala=None, term="traco"):
        self.xmin, self.xmax, self.zmin, self.zmax = xmin, xmax, zmin, zmax
        self.escala, self.term = escala, term
        self.fs = TEXTO_MM * escala if escala else fs
        self.items = []

    def X(self, x):
        return x - self.xmin

    def Z(self, z):
        return self.zmax - z

    def rect(self, x1, z1, x2, z2, cls):
        xa, xb = sorted((x1, x2))
        za, zb = sorted((z1, z2))
        if self.escala and cls in HACHURAS:
            return self._hachura([(xa, za), (xb, za), (xb, zb), (xa, zb)], cls)
        self.items.append(f'<rect class="{cls}" x="{n(self.X(xa))}" y="{n(self.Z(zb))}" '
                          f'width="{n(xb - xa)}" height="{n(zb - za)}"/>')

    def poly(self, pts, cls):
        if self.escala and cls in HACHURAS:
            return self._hachura(pts, cls)
        p = " ".join(f"{n(self.X(x))},{n(self.Z(z))}" for x, z in pts)
        self.items.append(f'<polygon class="{cls}" points="{p}"/>')

    def _hachura(self, pts, cls):
        """Hachura vetorial recortada no contorno (impressão nítida em qualquer escala)."""
        tipo, passo = HACHURAS[cls]
        s = passo * self.escala
        p = " ".join(f"{n(self.X(x))},{n(self.Z(z))}" for x, z in pts)
        k = len(self.items)
        cid = f"@@ID@@-h{k}"
        xs, zs = [x for x, _ in pts], [z for _, z in pts]
        x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
        traco = []
        if tipo in ("diag", "cruz"):
            r2 = s * math.sqrt(2)
            c = x0 - z1
            while c <= x1 - z0:
                traco.append(f"M{n(self.X(c + z0))},{n(self.Z(z0))}L{n(self.X(c + z1))},"
                             f"{n(self.Z(z1))}")
                c += r2
            if tipo == "cruz":
                c = x0 + z0
                while c <= x1 + z1:
                    traco.append(f"M{n(self.X(c - z0))},{n(self.Z(z0))}L{n(self.X(c - z1))},"
                                 f"{n(self.Z(z1))}")
                    c += r2
        elif tipo == "agua":
            a = 0.62 * s
            linha, z = 0, z0 + a / 2
            while z <= z1:
                x = x0 + (s / 2 if linha % 2 else 0)
                while x <= x1:
                    traco.append(f"M{n(self.X(x))},{n(self.Z(z))}h{n(0.6 * s)}")
                    x += s
                z += a
                linha += 1
        pontos = []
        if tipo == "pontos":
            r = 0.055 * s
            z = z0
            i = 0
            while z <= z1:
                x = x0
                while x <= x1:
                    for fx, fz, fr in ((.2, .3, 1.0), (.7, .15, .75), (.55, .75, 1.15),
                                       (.12, .82, .6)):
                        if (i + int(fx * 10)) % 5 == 4:
                            continue
                        pontos.append(f'<circle cx="{n(self.X(x + fx * s))}" '
                                      f'cy="{n(self.Z(z + fz * s))}" r="{n(r * fr)}"/>')
                    x += s
                    i += 1
                z += s
        corpo = (f'<path class="hl" d="{"".join(traco)}"/>' if traco else "") + \
            (f'<g class="hd">{"".join(pontos)}</g>' if pontos else "")
        self.items.append(f'<clipPath id="{cid}"><polygon points="{p}"/></clipPath>'
                          f'<polygon class="hfundo" points="{p}"/>'
                          f'<g clip-path="url(#{cid})">{corpo}</g>'
                          f'<polygon class="{cls}" fill="none" points="{p}"/>')

    def pline(self, pts, cls):
        p = " ".join(f"{n(self.X(x))},{n(self.Z(z))}" for x, z in pts)
        self.items.append(f'<polyline class="{cls}" points="{p}"/>')

    def line(self, x1, z1, x2, z2, cls):
        self.items.append(f'<line class="{cls}" x1="{n(self.X(x1))}" y1="{n(self.Z(z1))}" '
                          f'x2="{n(self.X(x2))}" y2="{n(self.Z(z2))}"/>')

    def circle(self, x, z, r, cls):
        self.items.append(f'<circle class="{cls}" cx="{n(self.X(x))}" cy="{n(self.Z(z))}" '
                          f'r="{n(r)}"/>')

    def rasgo(self, x, ya, yb, r, cls):
        """Rasgo oblongo alinhado em z, de centro (x, ya) a (x, yb) e raio r."""
        self.items.append(f'<rect class="{cls}" x="{n(self.X(x - r))}" y="{n(self.Z(yb + r))}" '
                          f'width="{n(2 * r)}" height="{n(yb - ya + 2 * r)}" rx="{n(r)}"/>')

    def text(self, x, z, s, anchor="middle", cls="lbl", k=1.0, rot=None):
        tr = ""
        if rot is not None:
            tr = f' transform="rotate({rot} {n(self.X(x))} {n(self.Z(z))})"'
        if self.escala:
            k = max(k, 1.0) if cls == "dimt" else k
        self.items.append(f'<text class="{cls}" x="{n(self.X(x))}" y="{n(self.Z(z))}" '
                          f'text-anchor="{anchor}" font-size="{n(self.fs * k)}"{tr}>'
                          f'{html.escape(s)}</text>')

    def _term(self, x, z, dx, dz):
        """Terminação de cota no ponto (x, z); (dx, dz) aponta para fora da cota."""
        if self.term == "seta" and self.escala:
            c, w = self.fs * 1.0, self.fs * 0.18
            px, pz = -dz, dx
            self.poly([(x, z), (x - dx * c + px * w, z - dz * c + pz * w),
                       (x - dx * c - px * w, z - dz * c - pz * w)], "arrow")
        else:
            t = self.fs * 0.35
            self.line(x - t, z - t, x + t, z + t, "tick")

    def dim_h(self, x1, x2, z, label, k=0.9, tx=None, ext=None):
        """Cota horizontal; 'ext' é a cota z dos pontos medidos (linhas de chamada)."""
        if ext is not None:
            g = self.fs * 0.4
            s = 1 if ext < z else -1
            for x in (x1, x2):
                self.line(x, ext + s * g, x, z + s * self.fs * 0.6, "dim")
        self.line(x1, z, x2, z, "dim")
        self._term(x1, z, -1, 0)
        self._term(x2, z, 1, 0)
        xt = (x1 + x2) / 2 if tx is None else tx
        self.text(xt, z + self.fs * 0.35, label, k=k, cls="dimt")

    def dim_v(self, z1, z2, x, label, k=0.9, ext=None):
        if ext is not None:
            g = self.fs * 0.4
            s = 1 if ext < x else -1
            for z in (z1, z2):
                self.line(ext + s * g, z, x + s * self.fs * 0.6, z, "dim")
        self.line(x, z1, x, z2, "dim")
        lo, hi = sorted((z1, z2))
        self._term(x, lo, 0, -1)
        self._term(x, hi, 0, 1)
        self.text(x - self.fs * 0.35, (z1 + z2) / 2, label, k=k, cls="dimt", rot=-90)

    def callout(self, num, x, z, tx=None, tz=None):
        r = self.fs * (1.45 if self.escala else 0.62)
        if tx is not None:
            self.items.append(f'<line class="lead" x1="{n(self.X(x))}" y1="{n(self.Z(z))}" '
                              f'x2="{n(self.X(tx))}" y2="{n(self.Z(tz))}"/>')
        self.items.append(f'<g class="co"><circle cx="{n(self.X(x))}" cy="{n(self.Z(z))}" '
                          f'r="{n(r)}"/><text x="{n(self.X(x))}" y="{n(self.Z(z))}" '
                          f'font-size="{n(self.fs * (1.1 if self.escala else 0.78))}">{num}'
                          f'</text></g>')

    def mm(self, v):
        """Converte milímetros de papel em unidades do desenho."""
        return v * (self.escala or self.fs / TEXTO_MM)

    def rotulo(self, texto, x, z, tx, tz, lado=None, k=1.0, ponto=True):
        """Indicação com linha de chamada: (tx, tz) é o ponto indicado, (x, z) o cotovelo."""
        lado = lado or (1 if x >= tx else -1)
        o = self.mm(2.5)
        self.line(tx, tz, x, z, "lead")
        self.line(x, z, x + lado * o, z, "lead")
        if ponto:
            self.circle(tx, tz, self.mm(0.45), "dot")
        linhas = texto if isinstance(texto, (list, tuple)) else [texto]
        h = self.fs * k * 1.3
        z0 = z - self.fs * k * 0.35 + (len(linhas) - 1) * h / 2
        for i, s in enumerate(linhas):
            self.text(x + lado * (o + self.mm(0.8)), z0 - i * h, s,
                      anchor="start" if lado > 0 else "end", cls="note", k=k)

    def dim_al(self, p1, p2, lado, dist, label, k=1.0):
        """Cota alinhada entre p1 e p2; 'lado' é o vetor unitário do afastamento e 'dist' a
        distância da linha de cota ao ponto mais afastado."""
        (x1, z1), (x2, z2) = p1, p2
        ux, uz = x2 - x1, z2 - z1
        comp = math.hypot(ux, uz) or 1
        ux, uz = ux / comp, uz / comp
        nx, nz = lado
        s1, s2 = x1 * nx + z1 * nz, x2 * nx + z2 * nz
        base = max(s1, s2) + dist
        a = (x1 + (base - s1) * nx, z1 + (base - s1) * nz)
        b = (x2 + (base - s2) * nx, z2 + (base - s2) * nz)
        g, e = self.mm(1.0), self.mm(1.5)
        for (px, pz), (qx, qz), s in (((x1, z1), a, s1), ((x2, z2), b, s2)):
            self.line(px + g * nx, pz + g * nz, qx + e * nx, qz + e * nz, "dim")
        self.line(*a, *b, "dim")
        self._term(*a, -ux, -uz)
        self._term(*b, ux, uz)
        ang = math.degrees(math.atan2(uz, ux))
        if ang > 90.001 or ang <= -90.001:
            ang -= 180 if ang > 0 else -180
        r = math.radians(ang)
        cx, cz = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        cx, cz = cx - math.sin(r) * self.mm(0.9), cz + math.cos(r) * self.mm(0.9)
        self.text(cx, cz, label, cls="dimt", k=k, rot=-ang)

    def cadeia(self, valores, pos, orient, ext, k=1.0, rotulos=None):
        """Cotas encadeadas entre valores sucessivos. orient 'h' (horizontal, na altura
        'pos') ou 'v' (vertical, na abscissa 'pos'); 'ext' é a coordenada da feição medida.
        Trechos curtos levam ponto no lugar da seta e texto do outro lado da linha."""
        vs = list(valores)
        larg = lambda s: len(s) * self.fs * k * 0.56
        g, e = self.mm(1.0), self.mm(1.5)
        sgn = 1 if pos > ext else -1
        for v in vs:
            if orient == "h":
                self.line(v, ext + sgn * g, v, pos + sgn * e, "dim")
            else:
                self.line(ext + sgn * g, v, pos + sgn * e, v, "dim")
        if orient == "h":
            self.line(vs[0], pos, vs[-1], pos, "dim")
        else:
            self.line(pos, vs[0], pos, vs[-1], "dim")
        curtos = []
        for i, (a, b) in enumerate(zip(vs, vs[1:])):
            s = rotulos[i] if rotulos else c(abs(b - a))
            meio = (a + b) / 2
            d = 1 if b > a else -1
            curto = abs(b - a) < larg(s) + self.mm(3.2)
            for v, dv in ((a, -d), (b, d)):
                px, pz = (v, pos) if orient == "h" else (pos, v)
                if curto:
                    self.circle(px, pz, self.mm(0.35), "dot")
                elif orient == "h":
                    self._term(px, pz, dv, 0)
                else:
                    self._term(px, pz, 0, dv)
            if curto:
                curtos.append((meio, s))
            elif orient == "h":
                self.text(meio, pos + self.mm(0.9), s, cls="dimt", k=k)
            else:
                self.text(pos - self.mm(0.9), meio, s, cls="dimt", k=k, rot=-90)
        if curtos:
            gap = (max(larg(s) for _, s in curtos) + self.mm(1.5)) if orient == "h" \
                else self.fs * k * 1.3
            alvo = espalha([m for m, _ in curtos], gap)
            for (m, s), t in zip(curtos, alvo):
                if orient == "h":
                    self.text(t, pos - self.mm(0.9) - self.fs * k * 0.75, s, cls="dimt", k=k)
                else:
                    self.text(pos + self.mm(0.9) + self.fs * k * 0.75, t, s, cls="dimt", k=k,
                              rot=-90)

    def ordenadas(self, valores, orient, pos, ext, k=1.0):
        """Cotagem por coordenadas a partir da origem: 'h' mede x (textos verticais em
        z = pos), 'v' mede z (textos horizontais em x = pos); 'ext' é a borda da peça."""
        vs = sorted(set(round(v, 2) for v in valores))
        if not vs:
            return
        gap = self.fs * k * 1.2
        alvo = espalha(vs, gap)
        g = self.mm(1.0)
        sgn = 1 if pos > ext else -1
        dob = self.mm(3.0)
        for v, t in zip(vs, alvo):
            if orient == "h":
                self.pline([(v, ext + sgn * g), (v, pos - sgn * dob), (t, pos - sgn * self.mm(1.0)),
                            (t, pos)], "dimo")
                self.text(t + self.fs * k * 0.35, pos + sgn * self.mm(0.8), c(v),
                          anchor="end" if sgn < 0 else "start", cls="dimt", k=k, rot=-90)
            else:
                self.pline([(ext + sgn * g, v), (pos - sgn * dob, v), (pos - sgn * self.mm(1.0), t),
                            (pos, t)], "dimo")
                self.text(pos + sgn * self.mm(0.8), t - self.fs * k * 0.35, c(v),
                          anchor="start" if sgn > 0 else "end", cls="dimt", k=k)

    def svg(self, title, minw, ident):
        w, h = self.xmax - self.xmin, self.zmax - self.zmin
        corpo = "".join(self.items)
        if not self.escala:
            return (f'<svg class="dwg" viewBox="0 0 {n(w)} {n(h)}" style="--minw:{minw}px" '
                    f'role="img" aria-labelledby="{ident}"><title id="{ident}">'
                    f'{html.escape(title)}</title>' + corpo + "</svg>")
        corpo = corpo.replace("@@ID@@", ident)
        return (f'<svg class="dwg imp" viewBox="0 0 {n(w)} {n(h)}" '
                f'style="width:{w / self.escala:.2f}mm;height:{h / self.escala:.2f}mm" '
                f'role="img" aria-labelledby="{ident}"><title id="{ident}">'
                f'{html.escape(title)}</title>' + corpo + "</svg>")


# --------------------------------------------------------------------------
def _soma(a, b, k=1.0):
    return (a[0] + k * b[0], a[1] + k * b[1])


def _intersecao(p1, d1, p2, d2):
    det = d1[0] * (-d2[1]) - d1[1] * (-d2[0])
    if abs(det) < 1e-9:
        return p1
    rx, rz = p2[0] - p1[0], p2[1] - p1[1]
    a = (rx * (-d2[1]) - rz * (-d2[0])) / det
    return (p1[0] + a * d1[0], p1[1] + a * d1[1])


def geometria_dobrada(p):
    """Seção da peça dobrada, com espessura e raios internos. A chapa parte da borda
    inferior da planificação (y = 0) no sentido +x, com a face superior do corte para cima.
    Devolve o polígono, os trechos retos e os vértices das linhas de molde de cada dobra."""
    t, ri = p.t, ch.DOBRA[p.t]["ri"]
    B, d = (0.0, 0.0), (1.0, 0.0)
    inf, sup, trechos = [], [], []

    def normal(v):
        return (-v[1], v[0])

    def marca(P, v):
        inf.append(P)
        sup.append(_soma(P, normal(v), t))

    marca(B, d)
    for i, s in enumerate(p.retos):
        b0 = B
        B = _soma(B, d, s)
        trechos.append(dict(b0=b0, b1=B, d=d, n=normal(d)))
        marca(B, d)
        if i < len(p.angulos):
            th, g = math.radians(p.angulos[i]), p.giros[i]
            nn = normal(d)
            C = _soma(B, nn, ri + t) if g > 0 else _soma(B, nn, -ri)
            passos = max(4, int(p.angulos[i] / 10))
            B0, d0 = B, d
            for k in range(1, passos + 1):
                a = g * th * k / passos
                ca, sa = math.cos(a), math.sin(a)
                vx, vz = B0[0] - C[0], B0[1] - C[1]
                B = (C[0] + vx * ca - vz * sa, C[1] + vx * sa + vz * ca)
                d = (d0[0] * ca - d0[1] * sa, d0[0] * sa + d0[1] * ca)
                marca(B, d)
    vertices = []
    for i in range(len(p.angulos)):
        s1, s2 = trechos[i], trechos[i + 1]
        if p.giros[i] > 0:
            P1, P2 = s1["b1"], s2["b0"]
        else:
            P1, P2 = _soma(s1["b1"], s1["n"], t), _soma(s2["b0"], s2["n"], t)
        vertices.append(_intersecao(P1, s1["d"], P2, s2["d"]))
    return inf + sup[::-1], trechos, vertices


def extensao_dobrada(p):
    poly, _, _ = geometria_dobrada(p)
    xs, zs = [x for x, _ in poly], [z for _, z in poly]
    return max(xs) - min(xs), max(zs) - min(zs)


def planificacao(p, escala, ident, trecho=None, simples=False):
    """Planificação vista pela face superior na mesa de corte; origem no canto inferior
    esquerdo; furos numerados conforme a tabela de furos. 'trecho' = comprimento mostrado em
    vista parcial (extremidade da peça, com linha de ruptura); 'simples' omite os rótulos e a
    cadeia de cotas das dobras (detalhadas em vista parcial)."""
    L, W = p.comprimento, p.largura
    Lv = min(L, trecho) if trecho else L
    fs = TEXTO_MM * escala
    m = lambda v: v * escala
    furos = [f for f in p.furos if f[0] <= Lv]
    rasgos = [r for r in p.rasgos if r[0] <= Lv]
    xs = [x for x, _, _ in furos] + [x for x, _, _, _ in rasgos]
    ys = [y for _, y, _ in furos] + [v for _, y1, y2, _ in rasgos for v in (y1, y2)]
    dobras = p.linhas and not simples
    esq = m(17 if dobras else 10)
    dir_ = m(16) if ys else m(6 if trecho else 4)
    inf = m(22) if xs else m(11)
    if p.contorno:
        inf += m(4)
    if trecho:
        inf = m(4)
    d = Dwg(-esq, Lv + dir_, -inf, W + m(8 if p.contorno else 4), fs, escala, "seta")
    if trecho:
        a = m(1.6)
        zz = [(Lv, W)]
        n_z = 7
        for k in range(1, n_z):
            zz.append((Lv + (a if k % 2 else -a), W - W * k / n_z))
        zz.append((Lv, 0))
        d.pline([(Lv, 0), (0, 0), (0, W), (Lv, W)], "vis")
        d.pline(zz, "rupt")
    else:
        d.poly(ch.contorno_de(p), "vis")
    gravadas = [y1 for x1, y1, x2, y2 in p.marcas if y1 == y2]
    obst = [(x - dd / 2 - m(0.9), y - dd / 2 - m(0.9), x + dd / 2 + m(2.2), y + dd / 2 + m(2.2))
            for x, y, dd in furos]
    obst += [(x - w / 2 - m(0.9), min(y1, y2) - w / 2, x + w / 2 + m(2.2), max(y1, y2) + w / 2)
             for x, y1, y2, w in rasgos]
    for i, (yl, ang, g) in enumerate(zip(p.linhas, p.angulos, p.giros), 1):
        d.line(-m(2.5), yl, Lv + (0 if trecho else m(2.5)), yl, "dobra")
        if simples:
            continue
        txt = f"DOBRA {i} – {c(ang)}° PARA {'CIMA' if g > 0 else 'BAIXO'}"
        comp, alt = len(txt) * fs * 0.8 * 0.56, fs * 0.8 * 0.75
        linhas_h = gravadas + [v for v in p.linhas if v != yl] + [0, W]
        escolha = None
        for x0 in [m(4)] + sorted(o[2] + m(1) for o in obst):
            for z0 in (yl + m(0.9), yl - m(0.9) - alt):
                z1 = z0 + alt
                if x0 + comp > Lv - m(2):
                    continue
                if any(z0 - m(0.3) < v < z1 + m(0.3) for v in linhas_h):
                    continue
                if any(x0 < o[2] and x0 + comp > o[0] and z0 < o[3] and z1 > o[1] for o in obst):
                    continue
                escolha = (x0, z0)
                break
            if escolha:
                break
        x0, z0 = escolha or (m(4), yl + m(0.9))
        d.text(x0, z0, txt, anchor="start", cls="note", k=0.8)
    for x1, y1, x2, y2 in p.marcas:
        d.line(x1, y1, min(x2, Lv), y2, "grav")
    k = 0
    for x, y, dd in p.furos:
        k += 1
        if x > Lv:
            continue
        d.circle(x, y, dd / 2, "furo")
        cr = dd / 2 + m(0.9)
        d.line(x - cr, y, x + cr, y, "cm")
        d.line(x, y - cr, x, y + cr, "cm")
        d.text(x + dd / 2 + m(0.4), y + dd / 2 + m(0.2), str(k), anchor="start", cls="nfuro",
               k=0.72)
    for x, y1, y2, w in p.rasgos:
        k += 1
        if x > Lv:
            continue
        ya, yb = sorted((y1, y2))
        d.rasgo(x, ya, yb, w / 2, "furo")
        d.line(x, ya - w / 2 - m(0.9), x, yb + w / 2 + m(0.9), "cm")
        d.text(x + w / 2 + m(0.4), yb + m(0.2), str(k), anchor="start", cls="nfuro", k=0.72)
    if not trecho:
        if p.contorno:
            b = sorted(x for x, y in p.contorno if y == 0)
            t_ = sorted(x for x, y in p.contorno if y == W)
            d.cadeia([0, b[0], b[-1], L] if b[0] > 0 else [b[0], b[-1]], -m(6), "h", 0)
            d.cadeia([t_[0], t_[-1]], W + m(4), "h", W)
        d.cadeia([0, L], -inf + m(5), "h", 0)
        if xs:
            d.ordenadas([0] + xs, "h", -m(3.5), 0, k=0.8)
    if ys:
        d.ordenadas([0] + ys, "v", Lv + m(3.5), Lv, k=0.8)
    d.cadeia([0, W], -esq + m(4), "v", 0)
    if dobras:
        d.cadeia([0, *p.linhas, W], -m(9), "v", 0, k=0.9)
    return d.svg(f"Planificação da marca {p.codigo}", 400, ident)


def secao_dobrada(p, escala, ident):
    """Seção da peça dobrada, na posição de dobra: borda inferior da planificação à esquerda
    e face superior do corte para cima no primeiro trecho. Cotas externas nas linhas de molde."""
    t = p.t
    poly, trechos, vert = geometria_dobrada(p)
    fs = TEXTO_MM * escala
    m = lambda v: v * escala
    xs, zs = [x for x, _ in poly], [z for _, z in poly]
    mg, rot = m(10), m(19)          # cotas e ângulos; rótulos das bordas
    ux, uz = trechos[-1]["d"]
    dir_ = rot if ux > 0.7 else mg
    esq = rot if ux >= -0.7 or True else mg
    d = Dwg(min(xs) - esq, max(xs) + dir_, min(zs) - mg, max(zs) + mg, fs, escala, "seta")
    d.poly(poly, "steel")
    nb = len(p.angulos)

    def face_ext(i):
        return "inf" if p.giros[min(i, nb - 1)] > 0 else "sup"

    for i, sg in enumerate(trechos):
        f = face_ext(i if i < nb else i - 1)
        pa = vert[i - 1] if i > 0 else (sg["b0"] if f == "inf" else _soma(sg["b0"], sg["n"], t))
        pb = vert[i] if i < nb else (sg["b1"] if f == "inf" else _soma(sg["b1"], sg["n"], t))
        lado = (-sg["n"][0], -sg["n"][1]) if f == "inf" else sg["n"]
        d.dim_al(pa, pb, lado, m(6), c(p.abas[i]))
    for i in range(nb):
        s1, s2 = trechos[i], trechos[i + 1]
        bx, bz = s1["d"][0] - s2["d"][0], s1["d"][1] - s2["d"][1]
        nrm = math.hypot(bx, bz) or 1
        P = vert[i]
        d.text(P[0] + bx / nrm * m(3.4), P[1] + bz / nrm * m(3.4) - fs * 0.32,
               f"{c(p.angulos[i])}°", cls="dimt", k=0.9)

    def ao_longo(sg, lado_n, texto, frac=0.5):
        """Texto paralelo ao trecho, junto à face indicada (+1 face superior, -1 inferior)."""
        ux, uz = sg["d"]
        ang = math.degrees(math.atan2(uz, ux))
        inv = ang > 90.001 or ang <= -90.001
        if inv:
            ang -= 180 if ang > 0 else -180
        r = math.radians(ang)
        cima = (-math.sin(r), math.cos(r))
        face = sg["b0"] if lado_n < 0 else _soma(sg["b0"], sg["n"], t)
        face = _soma(face, sg["d"], math.hypot(sg["b1"][0] - sg["b0"][0],
                                               sg["b1"][1] - sg["b0"][1]) * frac)
        nx, nz = sg["n"][0] * lado_n, sg["n"][1] * lado_n
        mesmo = cima[0] * nx + cima[1] * nz > 0
        off = m(1.3) if mesmo else m(1.3) + fs * 0.8 * 0.72
        d.text(face[0] + nx * off, face[1] + nz * off, texto, cls="note", k=0.8, rot=-ang)

    retos = [math.hypot(s["b1"][0] - s["b0"][0], s["b1"][1] - s["b0"][1]) for s in trechos]
    i_sup = max(range(len(trechos)), key=lambda i: retos[i])
    rot_sup, rot_conc = "FACE SUPERIOR", "FACE DE CONCRETO"
    i_conc = None
    if p.face_concreto:
        cand = [i for i, nome in enumerate(p.nomes_abas) if "concreto" in nome or nome == "topo"]
        i_conc = cand[0] if cand else i_sup
        lado_conc = 1 if p.face_concreto == "superior" else -1
        if i_conc == i_sup and lado_conc == 1:
            ao_longo(trechos[i_sup], 1, "FACE SUPERIOR E FACE DE CONCRETO", 0.42)
        else:
            ao_longo(trechos[i_sup], 1, rot_sup, 0.5 if i_conc != i_sup else 0.72)
            ao_longo(trechos[i_conc], lado_conc, rot_conc, 0.27)
    else:
        ao_longo(trechos[i_sup], 1, rot_sup)

    ini = _soma(trechos[0]["b0"], trechos[0]["n"], t / 2)
    d.text(ini[0] - m(2.2), ini[1] - fs * 0.35, "BORDA INFERIOR", anchor="end", cls="note", k=0.8)
    fim_s = trechos[-1]
    fim = _soma(fim_s["b1"], fim_s["n"], t / 2)
    ux, uz = fim_s["d"]
    if abs(ux) >= abs(uz):
        d.text(fim[0] + ux * m(2.2), fim[1] - fs * 0.35, "BORDA SUPERIOR",
               anchor="start" if ux > 0 else "end", cls="note", k=0.8)
    else:
        dz_ = m(2.4) if uz > 0 else -(m(2.4) + fs * 0.8)
        d.text(fim[0], fim[1] + dz_, "BORDA SUPERIOR", cls="note", k=0.8)
    return d.svg(f"Seção dobrada da marca {p.codigo}", 300, ident)
