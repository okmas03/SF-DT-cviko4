"""Krok 5 – PageRank na dátach z vybranej stránky.

Načíta spracovaný dataset (`<data-dir>/dataset.csv`), vypočíta PageRank,
uloží zoradený ranking do `<data-dir>/ranking.csv` a vypíše top N stránok.

Použitie:
    python main.py                        # data/ (hĺbka 2)
    python main.py --data-dir data/depth3 # porovnanie s hĺbkou 3
    python main.py --top 50
"""
import argparse
import csv
from pathlib import Path

from dataset import build_nodes, load_edges
from pagerank import BETA, ITERATIONS, pagerank, sort_ranking

DEFAULT_DATA_DIR = Path("data")
DEFAULT_TOP = 20


def save_ranking(ranking: list[tuple[str, float]], path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["position", "url", "rank"])
        for position, (url, rank) in enumerate(ranking, start=1):
            writer.writerow([position, url, f"{rank:.6f}"])


def main() -> None:
    parser = argparse.ArgumentParser(description="PageRank na datasete odkazov.")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR,
                        help="priečinok s dataset.csv; ranking.csv sa uloží tam")
    parser.add_argument("--top", type=int, default=DEFAULT_TOP, help="koľko stránok vypísať")
    args = parser.parse_args()

    edges = load_edges(args.data_dir / "dataset.csv")
    nodes = build_nodes(edges)
    ranking = sort_ranking(pagerank(edges, nodes=nodes))
    save_ranking(ranking, args.data_dir / "ranking.csv")

    sources = {s for s, _ in edges}
    print(f"Dataset: {args.data_dir / 'dataset.csv'}")
    print(f"Hrán: {len(edges)}, stránok N: {len(nodes)}, "
          f"dangling: {len(nodes) - len(sources)}")
    print(f"β = {BETA}, iterácií = {ITERATIONS}, súčet r = {sum(r for _, r in ranking):.4f}")
    print(f"Rozsah rankov: {ranking[-1][1]:.5f} – {ranking[0][1]:.5f} "
          f"(rovnomerne by to bolo 1/N = {1 / len(nodes):.5f})\n")

    print(f"Top {args.top}:")
    for position, (url, rank) in enumerate(ranking[: args.top], start=1):
        print(f"{position:>3}. {rank:.5f}  {url}")
    print(f"\nCelý ranking uložený do {args.data_dir / 'ranking.csv'}")


if __name__ == "__main__":
    main()
