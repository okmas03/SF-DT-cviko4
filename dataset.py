"""Krok 2 – spracovanie datasetu.

Zo surových hrán (výstup crawlera) odstráni duplicity a self-loopy, očísluje stránky
a uloží:
    data/dataset.csv  – unikátne hrany `source,target`
    data/nodes.csv    – zoznam stránok `id,url`

Použitie:
    python dataset.py
    python dataset.py --raw data/raw_edges.csv --out-dir data
"""
import argparse
import csv
from pathlib import Path

DEFAULT_RAW = Path("data/raw_edges.csv")
DEFAULT_OUT_DIR = Path("data")


def load_edges(path: Path) -> list[tuple[str, str]]:
    """Načíta hrany z CSV s hlavičkou `source,target`."""
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [(row["source"], row["target"]) for row in reader]


def save_edges(edges: list[tuple[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["source", "target"])
        writer.writerows(edges)


def remove_duplicates(edges: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Odstráni duplicitné hrany, zachová poradie prvého výskytu."""
    return list(dict.fromkeys(edges))


def remove_self_loops(edges: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Odstráni hrany, kde stránka odkazuje sama na seba."""
    return [(s, t) for s, t in edges if s != t]


def build_nodes(edges: list[tuple[str, str]]) -> list[str]:
    """Zoznam všetkých unikátnych stránok (zdroje aj ciele) v poradí výskytu.

    Index v zozname = id stránky (riadok/stĺpec v matici M).
    """
    nodes = {}
    for s, t in edges:
        nodes.setdefault(s, None)
        nodes.setdefault(t, None)
    return list(nodes)


def save_nodes(nodes: list[str], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "url"])
        writer.writerows(enumerate(nodes))


def main() -> None:
    parser = argparse.ArgumentParser(description="Spracovanie datasetu hrán.")
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW, help="CSV so surovými hranami")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="výstupný priečinok")
    args = parser.parse_args()

    raw = load_edges(args.raw)
    unique = remove_duplicates(raw)
    edges = remove_self_loops(unique)
    nodes = build_nodes(edges)

    save_edges(edges, args.out_dir / "dataset.csv")
    save_nodes(nodes, args.out_dir / "nodes.csv")

    sources = {s for s, _ in edges}
    dangling = [n for n in nodes if n not in sources]

    print(f"Surové hrany:                    {len(raw)}")
    print(f"Po odstránení duplicít:          {len(unique)}  (-{len(raw) - len(unique)})")
    print(f"Po odstránení self-loopov:       {len(edges)}  (-{len(unique) - len(edges)})")
    print(f"Počet stránok N:                 {len(nodes)}")
    print(f"  stránky s odchádzajúcimi linkami: {len(sources)}")
    print(f"  stránky bez odchádzajúcich linkov (dangling): {len(dangling)}")
    print(f"Uložené do {args.out_dir / 'dataset.csv'} a {args.out_dir / 'nodes.csv'}")


if __name__ == "__main__":
    main()
