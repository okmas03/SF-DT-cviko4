# PageRank – vlastná implementácia

Vlastná implementácia algoritmu **PageRank** (Google formulácia), otestovaná na vzorových dátach
a na datasete odkazov stiahnutom zo stránky **https://www.lua.org/**.

## Štruktúra repozitára

```
├── crawler.py          # krok 1 – zber odkazov zo stránky
├── dataset.py          # krok 2 – spracovanie datasetu
├── pagerank.py         # krok 3 – implementácia PageRank
├── sample.py           # krok 4 – ukážka na vzorových dátach
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

## 3. Implementácia PageRank

Súbor `pagerank.py`, Google formulácia:

```
r(0)   = vektor dĺžky N s hodnotami 1/N
r(t+1) = A · r(t)
A      = β·M + (1 − β)·(1/N)·E
```

- `β = 0.85`: pravdepodobnosť sledovania existujúcich odkazov
- `N`: celkový počet stránok
- `E`: matica jednotiek N×N
- `M`: matica prechodov, `M[i][j] = 1 / (počet odchádzajúcich odkazov z j)`, ak `j → i`. Súčet každého stĺpca je 1.
- Počet iterácií: 50, teda výsledok je `r(50)`.

**Dangling nodes:** stránka bez odchádzajúcich odkazov by mala v M nulový stĺpec a ranking by sa z nej „strácal“ (súčet `r` by klesal pod 1). Jej stĺpec sa preto vyplní hodnotou `1/N`: náhodný surfer z takej stránky skočí na ľubovoľnú stránku.

Použitie:

```python
from pagerank import pagerank, sort_ranking

ranks = pagerank([(1, 2), (1, 3), (2, 4), (3, 1), (3, 2), (3, 4), (4, 3)])
for page, rank in sort_ranking(ranks):
    print(page, round(rank, 4))
```

Správnosť som overil nezávislým výpočtom. Stacionárny vektor `r = A·r` je vlastný vektor matice A pre vlastné číslo 1 (`numpy.linalg.eig`) a zhoduje sa s výsledkom power iterácie.

## 4. Ukážka na vzorových dátach

```bash
python sample.py
```

Vzorové dáta zo zadania: `{1 -> 2, 1 -> 3, 2 -> 4, 3 -> 1, 3 -> 2, 3 -> 4, 4 -> 3}`, kde N = 4 a β = 0.85.

Matica M (stĺpec j = prechody zo stránky j):

```
             1       2       3       4
     1  0.0000  0.0000  0.3333  0.0000
     2  0.5000  0.0000  0.3333  0.0000
     3  0.5000  0.0000  0.0000  1.0000
     4  0.0000  1.0000  0.3333  0.0000
```

Matica A = β·M + (1−β)·(1/N)·E:

```
             1       2       3       4
     1  0.0375  0.0375  0.3208  0.0375
     2  0.4625  0.0375  0.3208  0.0375
     3  0.4625  0.0375  0.0375  0.8875
     4  0.0375  0.8875  0.3208  0.0375
```

Priebeh iterácií r(t):

```
     t       1       2       3       4
     0  0.2500  0.2500  0.2500  0.2500
     1  0.1083  0.2146  0.3562  0.3208
     2  0.1384  0.1845  0.3562  0.3208
     3  0.1384  0.1973  0.3690  0.2952
     5  0.1359  0.1963  0.3612  0.3067
    10  0.1388  0.1976  0.3569  0.3067
    20  0.1387  0.1976  0.3571  0.3066
    50  0.1387  0.1976  0.3571  0.3066
```

**Výsledné ranky r(50):**

| Poradie | Stránka | Rank |
|---|---|---|
| 1. | 3 | 0.3571 |
| 2. | 4 | 0.3066 |
| 3. | 2 | 0.1976 |
| 4. | 1 | 0.1387 |
| | **súčet** | **1.0000** |

Algoritmus skonverguje približne po 20 iteráciách. Najvyšší rank má stránka 3: odkazuje na ňu stránka 1 a stránka 4 posiela celý svoj rank práve jej. Výsledok sa zhoduje s vlastným vektorom matice A (`r = A·r`), ktorý vypočíta `numpy.linalg.eig`.
