"""
Generator KV Jurapark: składa grafikę kampanijną z assetów repo.
Pipeline: repo raw-link -> Pillow composite -> tekst Montserrat -> PNG.

Wymaga: Pillow (pip install pillow). Reszta to stdlib.

Typy KV:   eventowy (B) / promocyjny (A) / sezonowy (C, foto-split)
Formaty:   1:1 (1080) / 4:5 (1080x1350) / 9:16 (1080x1920 story)
Headline:  generowany tekst (Montserrat, falka opcjonalna, litera->ikona)
           lub gotowy PNG z repo (_grupa/headline/) przez --headline-img
Dorysowanki: programowe (sun / iskra) lub overlay assetu (--dorysowanka-img)

Przyklady:
  python kv_generator.py --park solec --typ eventowy --headline "Dzień Dziecka" ^
    --ikona _grupa/ikony-atrakcji/ikona_muzeum.png --ikona-litera "z" ^
    --dorysowanka sun --linia1 "Świętuj z nami" --linia2 "OD 30 MAJA DO 7 CZERWCA" ^
    --oferta1 "NOWE ATRAKCJE" --oferta2 "NA SEZON 2026" --out kv.png

  python kv_generator.py --park solec --typ eventowy ^
    --headline-img _grupa/headline/headline_dzien-dinozaura.png --out kv2.png

Reguly: tlo=faktura, apla=kolor uzupelniajacy, headline bialy/czarny wg jasnosci,
        font Montserrat, falka=falujacy baseline eventowego.
"""
import argparse, io, math, urllib.request
from PIL import Image, ImageDraw, ImageFont

BASE = "https://raw.githubusercontent.com/kuba-pelnia-studio/brand_assets-jurapark/main/"

PARKS = {
    "solec":     {"accent": (238, 114, 25), "headline": (255, 255, 255), "apla_dark": (15, 110, 86),  "dory": (255, 209, 77),
                  "faktura": "solec/tla/tlo_special.png",     "logo": "solec/logo/logo_solec.png",         "hero_dir": "solec/brand-hero/",     "hero_default": "solusio_odkrywca.png"},
    "baltow":    {"accent": (0, 171, 105),  "headline": (255, 255, 255), "apla_dark": (153, 60, 29),  "dory": (255, 209, 77),
                  "faktura": "baltow/tla/tlo_baltow.png",     "logo": "baltow/logo/logo_baltow.png",       "hero_dir": "baltow/brand-hero/",    "hero_default": "juras_odkrywca.png"},
    "krasiejow": {"accent": (238, 114, 25), "headline": (0, 0, 0),       "apla_dark": (133, 79, 11),  "dory": (238, 114, 25),
                  "faktura": "krasiejow/tla/tlo_special.png", "logo": "krasiejow/logo/logo_krasiejow.png", "hero_dir": "krasiejow/brand-hero/", "hero_default": "kraska_dzungla.png"},
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
    if "://" in src:
        with urllib.request.urlopen(src, timeout=30) as r:
            return Image.open(io.BytesIO(r.read())).convert("RGBA")
    return Image.open(src).convert("RGBA")

def asset_img(src):
    """Asset z repo (sciezka wzgledna) lub URL/lokalnie."""
    if "://" in src or ":\\" in src or src.startswith("/"):
        return load_img(src)
    return fetch_img(src)

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

def render_headline(canvas, draw, cx, cy, text, f, fill, wave=False, amp=0, wav=1, icon=None, icon_char=None):
    """Headline glyph po glyphie: wave (falka) + litera->ikona."""
    isz = int(f.size * 0.95)
    glyphs, replaced = [], False
    for ch in text:
        if icon is not None and icon_char and ch.lower() == icon_char.lower() and not replaced:
            glyphs.append(("icon", isz)); replaced = True
        else:
            glyphs.append((ch, draw.textlength(ch, font=f)))
    total = sum(g[1] for g in glyphs)
    x = cx - total / 2
    for content, w in glyphs:
        gx = x + w / 2
        gy = cy + (amp * math.sin((gx - cx) / wav * 2 * math.pi) if wave else 0)
        if content == "icon":
            canvas.alpha_composite(icon.resize((isz, isz)), (int(gx - isz / 2), int(gy - isz / 2)))
        else:
            draw.text((gx, gy), content, font=f, fill=fill, anchor="mm")
        x += w

def dorysowanka(canvas, draw, kind, cx, cy, r, color):
    if kind == "sun":
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=max(4, r // 6))
        for a in range(0, 360, 45):
            rad = math.radians(a)
            x1, y1 = cx + (r + 10) * math.cos(rad), cy + (r + 10) * math.sin(rad)
            x2, y2 = cx + (r + 10 + r * 0.55) * math.cos(rad), cy + (r + 10 + r * 0.55) * math.sin(rad)
            draw.line([x1, y1, x2, y2], fill=color, width=max(3, r // 8))
    elif kind == "iskra":
        w = max(3, r // 6)
        for dx, dy in [(r, 0), (0, r), (r * 0.6, r * 0.6), (-r * 0.6, r * 0.6)]:
            draw.line([cx - dx, cy - dy, cx + dx, cy + dy], fill=color, width=w)

def place(canvas, img, x, y, w):
    h = int(img.height * w / img.width)
    canvas.alpha_composite(img.resize((w, h)), (int(x), int(y)))
    return h

def cover(img, w, h):
    rr = max(w / img.width, h / img.height)
    img = img.resize((int(img.width * rr), int(img.height * rr)))
    l, t = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((l, t, l + w, t + h))

def faktura_bg(cfg, W, H):
    c = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    c.alpha_composite(cover(fetch_img(cfg["faktura"]), W, H))
    return c

def headline_block(canvas, draw, cfg, p, cx, cy, max_w, start, wave):
    """Headline jako gotowy PNG (--headline-img) albo generowany tekst."""
    if p["headline_img"]:
        img = asset_img(p["headline_img"])
        place(canvas, img, cx - max_w / 2, cy - img.height * max_w / img.width / 2, int(max_w))
        return start * 0.9
    f = fit_font(draw, p["headline"], True, max_w, start)
    icon = asset_img(p["ikona"]) if p["ikona"] else None
    render_headline(canvas, draw, cx, cy, p["headline"], f, cfg["headline"],
                    wave=wave, amp=0.018 * canvas.height, wav=0.42 * canvas.width,
                    icon=icon, icon_char=p["ikona_litera"])
    return f.size

def add_dorysowanka(canvas, draw, cfg, p, cx, cy, r):
    if not p["dorysowanka"]:
        return
    if p["dorysowanka"] in ("sun", "iskra"):
        dorysowanka(canvas, draw, p["dorysowanka"], cx, cy, r, cfg["dory"])
    else:
        place(canvas, asset_img(p["dorysowanka"]), cx - r, cy - r, int(r * 2))

# ---------- KV EVENTOWY ----------
def kv_eventowy(cfg, p, W, H, falka):
    c = faktura_bg(cfg, W, H)
    place(c, fetch_img(cfg["logo"]), W / 2 - 0.13 * W, 0.04 * H, int(0.26 * W))
    d = ImageDraw.Draw(c)
    hs = headline_block(c, d, cfg, p, W / 2, 0.30 * H, 0.85 * W, int(0.10 * W), falka)
    if p["sub"]:
        ctext(d, W / 2, 0.30 * H + hs * 0.85, p["sub"], font(False, int(0.037 * W)), cfg["headline"])
    add_dorysowanka(c, d, cfg, p, 0.86 * W, 0.20 * H, int(0.05 * W))
    hero = fetch_img(cfg["hero_dir"] + p["hero"])
    hw = int(0.46 * W)
    place(c, hero, 0.018 * W, H - int(hero.height * hw / hero.width) - 0.018 * H, hw)
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

# ---------- KV PROMOCYJNY ----------
def kv_promocyjny(cfg, p, W, H, falka):
    c = faktura_bg(cfg, W, H)
    place(c, fetch_img(cfg["logo"]), W / 2 - 0.14 * W, 0.06 * H, int(0.28 * W))
    d = ImageDraw.Draw(c)
    hs = headline_block(c, d, cfg, p, W / 2, 0.40 * H, 0.90 * W, int(0.11 * W), falka)
    if p["sub"]:
        ctext(d, W / 2, 0.40 * H + hs * 0.8, p["sub"], font(False, int(0.037 * W)), cfg["headline"])
    add_dorysowanka(c, d, cfg, p, 0.84 * W, 0.20 * H, int(0.05 * W))
    d.rounded_rectangle([0.22 * W, 0.61 * H, 0.78 * W, 0.87 * H], radius=int(0.13 * W), fill=cfg["accent"])
    ctext(d, W / 2, 0.675 * H, p["oferta1"], fit_font(d, p["oferta1"], True, 0.5 * W, int(0.052 * W)), (255, 255, 255))
    ctext(d, W / 2, 0.79 * H, p["oferta2"], fit_font(d, p["oferta2"], True, 0.5 * W, int(0.14 * W)), (255, 255, 255))
    return c

# ---------- KV SEZONOWY (foto-split) ----------
def kv_sezonowy(cfg, p, W, H, falka):
    if not p["foto"]:
        raise SystemExit("KV sezonowy wymaga --foto (URL lub sciezka)")
    c = cover(load_img(p["foto"]), W, H)
    split, amp = int(0.46 * W), int(0.03 * W)
    panel = faktura_bg(cfg, W, H)
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    pts = [(W, 0)] + [(split + amp * math.sin(H * i / 40 / H * 3 * math.pi), H * i / 40) for i in range(41)] + [(W, H)]
    md.polygon(pts, fill=255)
    c.paste(panel, (0, 0), mask)
    d = ImageDraw.Draw(c)
    pcx, pw = int((split + W) / 2 + 0.02 * W), int(W - split - 0.08 * W)
    place(c, fetch_img(cfg["logo"]), pcx - 0.12 * W, 0.05 * H, int(0.24 * W))
    if p["headline_img"]:
        img = asset_img(p["headline_img"])
        place(c, img, pcx - pw / 2, 0.40 * H, pw)
    else:
        hf = fit_font(d, p["headline"], True, pw, int(0.06 * W))
        words, lines, cur = p["headline"].split(), [], ""
        for w in words:
            t = (cur + " " + w).strip()
            if d.textlength(t, font=hf) <= pw: cur = t
            else: lines.append(cur); cur = w
        lines.append(cur)
        y0 = 0.40 * H
        for ln in lines:
            ctext(d, pcx, y0, ln, hf, cfg["headline"]); y0 += hf.size * 1.12
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
    ap.add_argument("--headline", default="")
    ap.add_argument("--headline-img", default="", help="gotowy headline PNG z repo (_grupa/headline/) lub sciezka")
    ap.add_argument("--ikona", default="", help="asset ikony do litera->ikona")
    ap.add_argument("--ikona-litera", default="", help="ktora litere zastapic ikona (pierwsze wystapienie)")
    ap.add_argument("--dorysowanka", default="", help="sun | iskra | sciezka do assetu")
    ap.add_argument("--sub", default="")
    ap.add_argument("--linia1", default="")
    ap.add_argument("--linia2", default="")
    ap.add_argument("--oferta1", default="")
    ap.add_argument("--oferta2", default="")
    ap.add_argument("--hero", default="")
    ap.add_argument("--foto", default="")
    ap.add_argument("--falka", action=argparse.BooleanOptionalAction, default=None)
    ap.add_argument("--out", default="kv.png")
    a = ap.parse_args()
    if not a.headline and not a.headline_img:
        raise SystemExit("Podaj --headline lub --headline-img")
    cfg = PARKS[a.park]
    W, H = FORMATS[a.format]
    falka = a.falka if a.falka is not None else (a.typ == "eventowy")
    p = {k: getattr(a, k) for k in ("headline", "sub", "linia1", "linia2", "oferta1", "oferta2", "foto")}
    p["headline_img"] = a.headline_img
    p["ikona"] = a.ikona
    p["ikona_litera"] = a.ikona_litera
    p["dorysowanka"] = a.dorysowanka
    p["hero"] = a.hero or cfg["hero_default"]
    img = LAYOUTS[a.typ](cfg, p, W, H, falka)
    img.convert("RGB").save(a.out, "PNG")
    print("OK zapisano:", a.out, a.park, a.typ, a.format)

if __name__ == "__main__":
    main()
