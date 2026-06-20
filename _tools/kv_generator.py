"""
Generator KV Jurapark: składa grafikę kampanijną z assetów repo.
Pipeline: repo raw-link -> Pillow composite -> tekst Montserrat -> PNG.

Wymaga: Pillow (pip install pillow). Reszta (urllib, argparse, math) to stdlib.

Typy KV:
  eventowy   (Template B): logo + falka headline + brand hero + 2 aple
  promocyjny (Template A): logo + headline + duza apla oferty (benefit)
  sezonowy   (Template C): foto-split (zdjecie | panel faktury, falista krawedz) + aple

Formaty: 1:1 (1080x1080), 4:5 (1080x1350), 9:16 (1080x1920 story)

Przyklad:
  python kv_generator.py --park solec --typ eventowy --format 1:1 ^
    --headline "Dzień Dziecka" --sub "w Jurapark Solec" ^
    --linia1 "Świętuj z nami" --linia2 "OD 30 MAJA DO 7 CZERWCA" ^
    --oferta1 "NOWE ATRAKCJE" --oferta2 "NA SEZON 2026" --out kv.png

  python kv_generator.py --park krasiejow --typ sezonowy ^
    --headline "TEGO LATA ODWIEDŹ KRASIEJÓW" --foto https://.../foto.jpg --out kv2.png

Reguly (z Jurapark_Brand_System / Design_Wzorce):
  - tlo = faktura akwarela z repo (nie plaski kolor)
  - apla akcentowa w kolorze uzupelniajacym (park siostrzany)
  - headline bialy na nasyconym tle, czarny na jasnym (Krasiejow)
  - font Montserrat (ExtraBold naglowki, Regular dopiski)
  - falka = falujacy baseline headline eventowego
"""
import argparse, io, math, os, urllib.request
from PIL import Image, ImageDraw, ImageFont

BASE = "https://raw.githubusercontent.com/kuba-pelnia-studio/brand_assets-jurapark/main/"

PARKS = {
    "solec": {
        "accent": (238, 114, 25), "headline": (255, 255, 255), "apla_dark": (15, 110, 86),
        "faktura": "solec/tla/tlo_special.png", "logo": "solec/logo/logo_solec.png",
        "hero_dir": "solec/brand-hero/", "hero_default": "solusio_odkrywca.png",
    },
    "baltow": {
        "accent": (0, 171, 105), "headline": (255, 255, 255), "apla_dark": (153, 60, 29),
        "faktura": "baltow/tla/tlo_baltow.png", "logo": "baltow/logo/logo_baltow.png",
        "hero_dir": "baltow/brand-hero/", "hero_default": "juras_odkrywca.png",
    },
    "krasiejow": {
        "accent": (238, 114, 25), "headline": (0, 0, 0), "apla_dark": (133, 79, 11),
        "faktura": "krasiejow/tla/tlo_special.png", "logo": "krasiejow/logo/logo_krasiejow.png",
        "hero_dir": "krasiejow/brand-hero/", "hero_default": "kraska_dzungla.png",
    },
}
FORMATS = {"1:1": (1080, 1080), "4:5": (1080, 1350), "9:16": (1080, 1920)}
FONT_BOLD = "_grupa/fonty/Montserrat-ExtraBold.ttf"
FONT_REG = "_grupa/fonty/Montserrat-Regular.ttf"

_cache = {}
def fetch_bytes(path):
    if path not in _cache:
        with urllib.request.urlopen(BASE + path, timeout=30) as r:
            _cache[path] = r.read()
    return _cache[path]

def fetch_img(path):
    return Image.open(io.BytesIO(fetch_bytes(path))).convert("RGBA")

def load_img(src):
    """Zdjecie z URL (http...) lub lokalnej sciezki."""
    if "://" in src:
        with urllib.request.urlopen(src, timeout=30) as r:
            return Image.open(io.BytesIO(r.read())).convert("RGBA")
    return Image.open(src).convert("RGBA")

def font(bold, size):
    return ImageFont.truetype(io.BytesIO(fetch_bytes(FONT_BOLD if bold else FONT_REG)), size)

def fit_font(draw, text, bold, max_w, start, min_size=16):
    s = start
    while s > min_size:
        f = font(bold, s)
        if draw.textlength(text, font=f) <= max_w:
            return f
        s -= 2
    return font(bold, min_size)

def ctext(draw, x, y, text, f, fill):
    draw.text((x, y), text, font=f, fill=fill, anchor="mm")

def wave_text(draw, cx, cy, text, f, fill, amp, wav):
    """Headline na falujacym baseline (falka)."""
    widths = [draw.textlength(c, font=f) for c in text]
    total = sum(widths)
    x = cx - total / 2
    for c, w in zip(text, widths):
        gx = x + w / 2
        gy = cy + amp * math.sin((gx - cx) / wav * 2 * math.pi)
        draw.text((gx, gy), c, font=f, fill=fill, anchor="mm")
        x += w

def place(canvas, img, x, y, w):
    h = int(img.height * w / img.width)
    canvas.alpha_composite(img.resize((w, h)), (int(x), int(y)))
    return h

def cover(img, w, h):
    """Skaluj+przytnij zdjecie do wymiaru (jak background-size: cover)."""
    r = max(w / img.width, h / img.height)
    img = img.resize((int(img.width * r), int(img.height * r)))
    l = (img.width - w) // 2
    t = (img.height - h) // 2
    return img.crop((l, t, l + w, t + h))

def faktura_bg(cfg, W, H):
    c = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    c.alpha_composite(cover(fetch_img(cfg["faktura"]), W, H))
    return c

# ---------- KV EVENTOWY (Template B) ----------
def kv_eventowy(cfg, p, W, H, falka):
    c = faktura_bg(cfg, W, H)
    place(c, fetch_img(cfg["logo"]), W / 2 - 0.13 * W, 0.04 * H, int(0.26 * W))
    d = ImageDraw.Draw(c)
    hf = fit_font(d, p["headline"], True, 0.85 * W, int(0.10 * W))
    if falka:
        wave_text(d, W / 2, 0.30 * H, p["headline"], hf, cfg["headline"], amp=0.018 * H, wav=0.42 * W)
    else:
        ctext(d, W / 2, 0.30 * H, p["headline"], hf, cfg["headline"])
    if p["sub"]:
        ctext(d, W / 2, 0.30 * H + hf.size * 0.85, p["sub"], font(False, int(0.037 * W)), cfg["headline"])
    hero = fetch_img(cfg["hero_dir"] + p["hero"])
    hw = int(0.46 * W)
    hh = int(hero.height * hw / hero.width)
    place(c, hero, 0.018 * W, H - hh - 0.018 * H, hw)
    ax0, ax1, acx = 0.515 * W, 0.975 * W, 0.745 * W
    aw = ax1 - ax0 - 0.04 * W
    d.rounded_rectangle([ax0, 0.525 * H, ax1, 0.665 * H], radius=int(0.07 * W), fill=(255, 255, 255, 255))
    if p["linia1"]:
        ctext(d, acx, 0.567 * H, p["linia1"], font(False, int(0.028 * W)), cfg["apla_dark"])
    ctext(d, acx, 0.615 * H, p["linia2"], fit_font(d, p["linia2"], True, aw, int(0.036 * W)), cfg["accent"])
    d.rounded_rectangle([ax0, 0.685 * H, ax1, 0.852 * H], radius=int(0.07 * W), fill=cfg["accent"])
    ctext(d, acx, 0.74 * H, p["oferta1"], fit_font(d, p["oferta1"], True, aw, int(0.043 * W)), (255, 255, 255))
    ctext(d, acx, 0.795 * H, p["oferta2"], fit_font(d, p["oferta2"], True, aw, int(0.043 * W)), (255, 255, 255))
    return c

# ---------- KV PROMOCYJNY (Template A) ----------
def kv_promocyjny(cfg, p, W, H, falka):
    c = faktura_bg(cfg, W, H)
    place(c, fetch_img(cfg["logo"]), W / 2 - 0.14 * W, 0.06 * H, int(0.28 * W))
    d = ImageDraw.Draw(c)
    hf = fit_font(d, p["headline"], True, 0.90 * W, int(0.11 * W))
    ctext(d, W / 2, 0.40 * H, p["headline"], hf, cfg["headline"])
    if p["sub"]:
        ctext(d, W / 2, 0.40 * H + hf.size * 0.8, p["sub"], font(False, int(0.037 * W)), cfg["headline"])
    d.rounded_rectangle([0.22 * W, 0.61 * H, 0.78 * W, 0.87 * H], radius=int(0.13 * W), fill=cfg["accent"])
    aw = 0.5 * W
    ctext(d, W / 2, 0.675 * H, p["oferta1"], fit_font(d, p["oferta1"], True, aw, int(0.052 * W)), (255, 255, 255))
    ctext(d, W / 2, 0.79 * H, p["oferta2"], fit_font(d, p["oferta2"], True, aw, int(0.14 * W)), (255, 255, 255))
    return c

# ---------- KV SEZONOWY (Template C, foto-split) ----------
def kv_sezonowy(cfg, p, W, H, falka):
    if not p["foto"]:
        raise SystemExit("KV sezonowy wymaga --foto (URL lub sciezka do zdjecia)")
    c = cover(load_img(p["foto"]), W, H)  # zdjecie jako tlo
    split = int(0.46 * W)
    amp = int(0.03 * W)
    panel = faktura_bg(cfg, W, H)
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    pts = [(W, 0)]
    steps = 40
    for i in range(steps + 1):
        y = H * i / steps
        x = split + amp * math.sin(y / H * 3 * math.pi)
        pts.append((x, y))
    pts.append((W, H))
    md.polygon(pts, fill=255)
    c.paste(panel, (0, 0), mask)  # panel faktury po prawej, falista krawedz
    d = ImageDraw.Draw(c)
    pcx = int((split + W) / 2 + 0.02 * W)
    pw = int(W - split - 0.08 * W)
    place(c, fetch_img(cfg["logo"]), pcx - 0.12 * W, 0.05 * H, int(0.24 * W))
    hf = fit_font(d, p["headline"], True, pw, int(0.058 * W))
    # headline wieloliniowy w panelu
    words = p["headline"].split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=hf) <= pw:
            cur = t
        else:
            lines.append(cur); cur = w
    lines.append(cur)
    y0 = 0.42 * H
    for ln in lines:
        ctext(d, pcx, y0, ln, hf, cfg["headline"])
        y0 += hf.size * 1.15
    if p["oferta1"]:
        d.rounded_rectangle([split + 0.03 * W, 0.72 * H, W - 0.04 * W, 0.84 * H], radius=int(0.06 * W), fill=cfg["accent"])
        ctext(d, pcx, 0.78 * H, p["oferta1"], fit_font(d, p["oferta1"], True, pw - 0.04 * W, int(0.04 * W)), (255, 255, 255))
    return c

LAYOUTS = {"eventowy": kv_eventowy, "promocyjny": kv_promocyjny, "sezonowy": kv_sezonowy}

def main():
    ap = argparse.ArgumentParser(description="Generator KV Jurapark")
    ap.add_argument("--park", required=True, choices=PARKS.keys())
    ap.add_argument("--typ", required=True, choices=LAYOUTS.keys())
    ap.add_argument("--format", default="1:1", choices=FORMATS.keys())
    ap.add_argument("--headline", required=True)
    ap.add_argument("--sub", default="")
    ap.add_argument("--linia1", default="")
    ap.add_argument("--linia2", default="")
    ap.add_argument("--oferta1", default="")
    ap.add_argument("--oferta2", default="")
    ap.add_argument("--hero", default="")
    ap.add_argument("--foto", default="")
    ap.add_argument("--falka", action=argparse.BooleanOptionalAction, default=None,
                    help="falka w headline (domyslnie wlaczona dla eventowego)")
    ap.add_argument("--out", default="kv.png")
    a = ap.parse_args()
    cfg = PARKS[a.park]
    W, H = FORMATS[a.format]
    falka = a.falka if a.falka is not None else (a.typ == "eventowy")
    p = {
        "headline": a.headline, "sub": a.sub, "linia1": a.linia1, "linia2": a.linia2,
        "oferta1": a.oferta1, "oferta2": a.oferta2, "foto": a.foto,
        "hero": a.hero or cfg["hero_default"],
    }
    img = LAYOUTS[a.typ](cfg, p, W, H, falka)
    img.convert("RGB").save(a.out, "PNG")
    print("OK zapisano:", a.out, a.park, a.typ, a.format)

if __name__ == "__main__":
    main()
