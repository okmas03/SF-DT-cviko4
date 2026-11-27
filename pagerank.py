"""Krok 3 – vlastná implementácia algoritmu PageRank (Google formulácia).

    r(0)   = vektor dĺžky N s hodnotami 1/N
    r(t+1) = A · r(t)
    A      = β·M + (1 − β)·(1/N)·E

    β  – pravdepodobnosť sledovania existujúcich linkov (0.85)
    N  – celkový počet stránok
    E  – matica jednotiek N×N
    M  – matica prechodov: M[i][j] = pravdepodobnosť prechodu zo stránky j na stránku i
         (súčet každého stĺpca = 1)
"""
from collections import Counter
from collections.abc import Hashable, Iterable

import numpy as np

from dataset import build_nodes

BETA = 0.85
ITERATIONS = 50


def build_transition_matrix(edges: Iterable[tuple[Hashable, Hashable]],
                            nodes: list[Hashable]) -> np.ndarray:
    """Zostaví stĺpcovo-stochastickú maticu M (N×N).

    Ak stránka j odkazuje na stránku i, potom M[i][j] = 1 / (počet odchádzajúcich linkov z j).

    Stránky bez odchádzajúcich linkov (dangling nodes) by mali nulový stĺpec, takže by sa
    z nich ranking „strácal“. Ich stĺpec sa preto vyplní hodnotou 1/N – náhodný surfer
    z takejto stránky skočí na ľubovoľnú stránku s rovnakou pravdepodobnosťou.
    """
    edges = list(edges)
    n = len(nodes)
    index = {node: i for i, node in enumerate(nodes)}
    out_degree = Counter(source for source, _ in edges)

    M = np.zeros((n, n))
    for source, target in edges:
        M[index[target], index[source]] += 1 / out_degree[source]

    dangling = M.sum(axis=0) == 0
    M[:, dangling] = 1 / n
    return M


def pagerank(edges: Iterable[tuple[Hashable, Hashable]],
             beta: float = BETA,
             iterations: int = ITERATIONS,
             nodes: list[Hashable] | None = None) -> dict[Hashable, float]:
    """Vypočíta PageRank power iteráciou a vráti {stránka: rank}.

    `nodes` určuje poradie stránok (index v matici); ak nie je zadané,
    zostaví sa z hrán v poradí výskytu.
    """
    edges = list(edges)
    if nodes is None:
        nodes = build_nodes(edges)
    n = len(nodes)

    M = build_transition_matrix(edges, nodes)
    E = np.ones((n, n))
    A = beta * M + (1 - beta) * (1 / n) * E

    r = np.full(n, 1 / n)            # r(0)
    for _ in range(iterations):      # r(t+1) = A · r(t)
        r = A @ r

    return dict(zip(nodes, r.tolist()))


def sort_ranking(ranks: dict[Hashable, float]) -> list[tuple[Hashable, float]]:
    """Zoradí stránky od najvyššieho ranku."""
    return sorted(ranks.items(), key=lambda item: item[1], reverse=True)
