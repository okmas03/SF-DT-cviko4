"""Krok 4 – ukážka PageRank na vzorových dátach zo zadania.

    {1 -> 2, 1 -> 3, 2 -> 4, 3 -> 1, 3 -> 2, 3 -> 4, 4 -> 3}

Použitie:
    python sample.py
"""
import numpy as np

from pagerank import BETA, ITERATIONS, build_transition_matrix, pagerank, sort_ranking

SAMPLE_EDGES = [(1, 2), (1, 3), (2, 4), (3, 1), (3, 2), (3, 4), (4, 3)]
SHOW_ITERATIONS = (0, 1, 2, 3, 5, 10, 20, 50)


def print_matrix(name: str, matrix: np.ndarray, labels: list) -> None:
    print(f"{name}:")
    print("      " + "".join(f"{label:>8}" for label in labels))
    for label, row in zip(labels, matrix):
        print(f"{label:>6}" + "".join(f"{value:8.4f}" for value in row))
    print()


def main() -> None:
    nodes = sorted({node for edge in SAMPLE_EDGES for node in edge})
    n = len(nodes)

    print("Vzorové dáta:", ", ".join(f"{s} -> {t}" for s, t in SAMPLE_EDGES))
    print(f"N = {n}, β = {BETA}, iterácií = {ITERATIONS}\n")

    M = build_transition_matrix(SAMPLE_EDGES, nodes)
    A = BETA * M + (1 - BETA) * (1 / n) * np.ones((n, n))
    print_matrix("Matica M (stĺpec j = prechody zo stránky j)", M, nodes)
    print_matrix("Matica A = β·M + (1−β)·(1/N)·E", A, nodes)

    # priebeh power iterácie (len na zobrazenie, výsledok počíta funkcia pagerank)
    print("Priebeh iterácií r(t):")
    print("     t" + "".join(f"{node:>8}" for node in nodes))
    for t in SHOW_ITERATIONS:
        r = pagerank(SAMPLE_EDGES, iterations=t, nodes=nodes)
        print(f"{t:>6}" + "".join(f"{r[node]:8.4f}" for node in nodes))
    print()

    ranks = pagerank(SAMPLE_EDGES, nodes=nodes)
    print(f"Výsledné ranky r({ITERATIONS}), zoradené:")
    for page, rank in sort_ranking(ranks):
        print(f"  stránka {page}: {rank:.4f}")
    print(f"  súčet: {sum(ranks.values()):.4f}\n")

    # nezávislé overenie: r je vlastný vektor A pre vlastné číslo 1
    eigenvalues, eigenvectors = np.linalg.eig(A)
    v = np.real(eigenvectors[:, np.argmax(np.real(eigenvalues))])
    v = v / v.sum()
    ok = np.allclose(v, [ranks[node] for node in nodes], atol=1e-6)
    print("Overenie vlastným vektorom A (r = A·r):",
          ", ".join(f"{node}: {value:.4f}" for node, value in zip(nodes, v)))
    print("Zhoda s power iteráciou:", "ÁNO" if ok else "NIE")


if __name__ == "__main__":
    main()
