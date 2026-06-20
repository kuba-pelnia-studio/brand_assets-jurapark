"""
Generator KV Jurapark: składa grafikę kampanijną z assetów repo.
Pipeline: repo raw-link -> Pillow composite -> tekst Montserrat -> PNG.

Wymaga: Pillow (pip install pillow). Reszta (urllib, argparse) to stdlib.

Przyklad:
  python kv_generator.py --park solec --typ eventowy ^
    --headline "Dzień Dziecka" --sub "w Jurapark Solec" ^
    --linia1 "Świętuj z nami" --linia2 "OD 30 MAJA DO 7 CZERWCA" ^
    --oferta1 "NOWE ATRAKCJE" --oferta2 "NA SEZON 2026" ^
    --hero solusio_odkrywca.png --out kv_solec.png

Reguly (z Jurapark_Brand_System / Design_Wzorce):
  - tlo = faktura akwarela z repo (nie plaski kolor)
  - apla akcentowa w kolorze uzupelniajacym (park siostrzany)
  - headline bialy na nasyconym tle, czarny na jasnym (Krasiejow)
  - font Montserrat (ExtraBold naglowki, Regular dopiski)
"""
import argparse, io, urllib.request
from PIL import Image, ImageDraw, ImageFont

BASE = "https://raw.githubusercontent.com/kuba-pelnia-studio/brand_assets-jurapark/main/"

# profile per park: bg faktura, kolor akcentu (uzupelniajacy), kolor headline, logo, hero
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

def font(bold, size):
    return ImageFont.truetype(io.BytesIO(fetch_bytes(FONT_BOLD if bold else FONT_REG)), size)

def fit_font(draw, text, bold, max_w, start, min_size=16):
    """Zwraca najwiekszy font ktory miesci tekst w max_w (eliminuje przepelnienie)."""
    s = start
    while s > min_size:
        f = font(bold, s)
        if draw.textlength(text, font=f) <= max_w:
            return f
        s -= 2
    return font(bold, min_size)

def ctext(draw, x, y, text, f, fill):
    draw.text((x, y), text, font=f, fill=fill, anchor="mm")

def place(canvas, img, x, y, w):
    h = int(img.height * w / img.width)
    canvas.alpha_composite(img.resize((w, h)), (x, y))
    return h

W = H = 1080

def base_canvas(cfg):
    c = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    c.alpha_composite(fetch_img(cfg["faktura"]).resize((W, H)))
    return c

def kv_eventowy(cfg, p):
    c = base_canvas(cfg)
    place(c, fetch_img(cfg["logo"]), W // 2 - 140, 48, 280)
    d = ImageDraw.Draw(c)
    hf = fit_font(d, p["headline"], True, 920, 104)
    ctext(d, 540, 360, p["headline"], hf, cfg["headline"])
    if p["sub"]:
        ctext(d, 540, 432, p["sub"], font(False, 40), cfg["headline"])
    hero = fetch_img(cfg["hero_dir"] + p["hero"])
    place(c, hero, 20, H - int(hero.height * 500 / hero.width) - 20, 500)
    # apla biala (daty)
    d.rounded_rectangle([556, 568, 1052, 718], radius=75, fill=(255, 255, 255, 255))
    if p["linia1"]:
        ctext(d, 804, 612, p["linia1"], font(False, 30), cfg["apla_dark"])
    ctext(d, 804, 664, p["linia2"], fit_font(d, p["linia2"], True, 440, 38), cfg["accent"])
    # apla akcentowa (oferta) - kolor uzupelniajacy
    d.rounded_rectangle([556, 740, 1052, 920], radius=75, fill=cfg["accent"])
    ctext(d, 804, 800, p["oferta1"], fit_font(d, p["oferta1"], True, 440, 46), (255, 255, 255))
    ctext(d, 804, 858, p["oferta2"], fit_font(d, p["oferta2"], True, 440, 46), (255, 255, 255))
    return c

def kv_promocyjny(cfg, p):
    c = base_canvas(cfg)
    place(c, fetch_img(cfg["logo"]), W // 2 - 150, 70, 300)
    d = ImageDraw.Draw(c)
    hf = fit_font(d, p["headline"], True, 960, 120)
    ctext(d, 540, 430, p["headline"], hf, cfg["headline"])
    if p["sub"]:
        ctext(d, 540, 505, p["sub"], font(False, 40), cfg["headline"])
    # duza apla oferty (owal) - benefit cenowy najwiekszy element
    d.rounded_rectangle([240, 660, 840, 940], radius=140, fill=cfg["accent"])
    ctext(d, 540, 730, p["oferta1"], fit_font(d, p["oferta1"], True, 540, 56), (255, 255, 255))
    ctext(d, 540, 850, p["oferta2"], fit_font(d, p["oferta2"], True, 540, 150), (255, 255, 255))
    return c

LAYOUTS = {"eventowy": kv_eventowy, "promocyjny": kv_promocyjny}

def main():
    ap = argparse.ArgumentParser(description="Generator KV Jurapark")
    ap.add_argument("--park", required=True, choices=PARKS.keys())
    ap.add_argument("--typ", required=True, choices=LAYOUTS.keys())
    ap.add_argument("--headline", required=True)
    ap.add_argument("--sub", default="")
    ap.add_argument("--linia1", default="")
    ap.add_argument("--linia2", default="")
    ap.add_argument("--oferta1", default="")
    ap.add_argument("--oferta2", default="")
    ap.add_argument("--hero", default="")
    ap.add_argument("--out", default="kv.png")
    a = ap.parse_args()
    cfg = PARKS[a.park]
    p = {
        "headline": a.headline, "sub": a.sub, "linia1": a.linia1, "linia2": a.linia2,
        "oferta1": a.oferta1, "oferta2": a.oferta2, "hero": a.hero or cfg["hero_default"],
    }
    img = LAYOUTS[a.typ](cfg, p)
    img.convert("RGB").save(a.out, "PNG")
    print("OK zapisano:", a.out, a.park, a.typ)

if __name__ == "__main__":
    main()
