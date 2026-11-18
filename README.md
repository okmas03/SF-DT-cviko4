# PageRank – vlastná implementácia

Vlastná implementácia algoritmu **PageRank** (Google formulácia), otestovaná na vzorových dátach
a na datasete odkazov stiahnutom zo stránky **https://www.lua.org/**.

## Štruktúra repozitára

```
├── crawler.py          # krok 1 – zber odkazov zo stránky
├── dataset.py          # krok 2 – spracovanie datasetu
├── data/
│   ├── raw_edges.csv   # vstupné dáta – všetky odkazy (vrátane duplicít)
│   ├── dataset.csv     # spracovaný dataset – unikátne hrany bez self-loopov
│   └── nodes.csv       # zoznam stránok s ich id (index v matici M)
├── requirements.txt
└── README.md
```

## Inštalácia
ma
```bash
pip install -r requirements.txt
```

## 1. Zber odkazov (crawler)

```bash
python crawler.py                 # predvolene: https://www.lua.org/, hĺbka 2
python crawler.py --url https://example.com/ --depth 3 --out data/raw_edges.csv
```

Postup:
- **Úroveň 0**: štartovacia stránka `https://www.lua.org/`
- **Úroveň 1**: všetky odkazy z úvodnej stránky
- **Úroveň 2**: všetky odkazy zo stránok úrovne 1

Pravidlá:
- Sťahujú sa **iba stránky z domény lua.org**. Externé odkazy sa zapíšu ako cieľové uzly, ale ďalej sa nesledujú.
- **Footer sa ignoruje.** Pred hľadaním odkazov sa z HTML odstráni `<footer>` a prvky, ktoré majú v `class` alebo `id` slovo `footer`.
- Odkazy na **sociálne siete** (Facebook, Instagram, LinkedIn, X/Twitter, TikTok, Discord…) sa zahadzujú.
- Zahadzujú sa odkazy, ktoré nie sú webové stránky: `mailto:`, `javascript:`, obrázky, archívy, PDF…
- URL sa **normalizujú**: relatívne sa prevedú na absolútne, odstráni sa `#fragment`, `http` sa zmení na `https` a `.../index.html` na `.../`.
- Menu stránky sa **ponecháva**, lebo jeho odkazy sú prirodzenou súčasťou štruktúry webu.

Výsledok (`data/raw_edges.csv`, formát `source,target`):

| | Počet |
|---|---|
| Stiahnuté stránky | 9 |
| Surové hrany (vrátane duplicít) | 931 |
| Odfiltrované: odkazy vo footeri | 0 |
| Odfiltrované: sociálne siete | 5 |
| Odfiltrované: nie sú stránky | 112 |

Ukážka:

```
source,target
https://www.lua.org/,https://www.lua.org/about.html
https://www.lua.org/,https://www.lua.org/news.html
https://www.lua.org/,https://www.lua.org/start.html
...
```

## 2. Spracovanie datasetu

```bash
python dataset.py
```

Kroky:
1. **Odstránenie duplicít**: rovnaký odkaz sa na jednej stránke často opakuje (menu, obsah…).
2. **Odstránenie self-loopov**: odkaz stránky samej na seba nenesie pre PageRank žiadnu informáciu.
3. **Očíslovanie stránok**: každá unikátna URL (zdroj aj cieľ) dostane `id`, čo je jej index v matici M.

| | Počet |
|---|---|
| Surové hrany | 931 |
| Po odstránení duplicít | 623 (−308) |
| Po odstránení self-loopov | **616** (−7) |
| Počet stránok N | **401** |
| Stránky s odchádzajúcimi odkazmi | 9 |
| Stránky bez odchádzajúcich odkazov (dangling) | 392 |

Výstupy:
- `data/dataset.csv`: hrany `source,target`
- `data/nodes.csv`: stránky `id,url`

Väčšina stránok nemá v datasete odchádzajúce odkazy. Pri hĺbke 2 sa totiž stiahne len úvodná stránka a jej podstránky, ciele z úrovne 2 sa už nesťahujú. Externé stránky sa nesťahujú vôbec. Ich stĺpec v matici M by bol nulový, preto ich PageRank musí ošetriť (viď krok 3).
