# brand_assets-jurapark

Repozytorium assetów graficznych grupy Jurapark (Solec, Bałtów, Krasiejów) dla automatycznej kompozycji grafik kampanijnych.

## Struktura

```
_grupa/                    assety wspólne dla wszystkich parków
  logo/                    logotypy marki parasolowej
  logo-base/               sygnety (czaszka T-Rexa)
  ikony-atrakcji/          białe sylwetki atrakcji
  headline/                gotowe napisy eventowe (PNG)
  elementy-dekoracyjne/
    aple/                  kształty nieregularne (kontenery tekstu)
    tla/                   tła i faktury
solec/      logo/  brand-hero/ (Solusio)  tla/
baltow/     logo/  brand-hero/ (Juraś)     tla/
krasiejow/  logo/  brand-hero/ (Kraśka)    tla/
```

## Konwencja kolorów (kolor parku = brand hero + tło)

- Solec: zielony `#00AB69`
- Bałtów: pomarańcz `#EE7219`
- Krasiejów: żółty `#FFD14D`
- Master grupa: pomarańcz `#FF9500`

## Użycie

Raw-link wzorzec:
```
https://raw.githubusercontent.com/kuba-pelnia-studio/brand_assets-jurapark/main/<ścieżka>
```

Designer (agent) zaciąga asset z raw-linku i osadza 1:1 w grafice (SVG `<image href>` lub Python/Pillow), nie odtwarza logo ręcznie.
