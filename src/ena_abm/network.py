from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass
from math import comb


@dataclass
class Graph:
    adjacency: list[set[int]]

    @classmethod
    def empty(cls, n: int) -> "Graph":
        return cls([set() for _ in range(n)])

    @property
    def n(self) -> int:
        return len(self.adjacency)

    def copy(self) -> "Graph":
        return Graph([set(neighbors) for neighbors in self.adjacency])

    def add_edge(self, a: int, b: int) -> None:
        if a == b:
            raise ValueError("self-loops are not allowed")
        self.adjacency[a].add(b)
        self.adjacency[b].add(a)

    def remove_edge(self, a: int, b: int) -> None:
        self.adjacency[a].remove(b)
        self.adjacency[b].remove(a)

    def has_edge(self, a: int, b: int) -> bool:
        return b in self.adjacency[a]

    def neighbors(self, node: int) -> tuple[int, ...]:
        return tuple(sorted(self.adjacency[node]))

    def degree(self, node: int) -> int:
        return len(self.adjacency[node])

    def edges(self) -> tuple[tuple[int, int], ...]:
        return tuple(
            (a, b)
            for a in range(self.n)
            for b in sorted(self.adjacency[a])
            if a < b
        )

    def validate(self) -> None:
        for a, neighbors in enumerate(self.adjacency):
            if a in neighbors:
                raise AssertionError("self-loop detected")
            for b in neighbors:
                if not 0 <= b < self.n:
                    raise AssertionError("neighbor outside graph")
                if a not in self.adjacency[b]:
                    raise AssertionError("asymmetric edge")

    def component_sizes(self) -> list[int]:
        unseen = set(range(self.n))
        sizes: list[int] = []
        while unseen:
            start = min(unseen)
            unseen.remove(start)
            queue = deque([start])
            size = 0
            while queue:
                node = queue.popleft()
                size += 1
                for neighbor in self.adjacency[node]:
                    if neighbor in unseen:
                        unseen.remove(neighbor)
                        queue.append(neighbor)
            sizes.append(size)
        return sorted(sizes, reverse=True)

    def diagnostics(self) -> dict[str, float | int]:
        edge_count = len(self.edges())
        average_degree = 2 * edge_count / self.n if self.n else 0.0
        density = 2 * edge_count / (self.n * (self.n - 1)) if self.n > 1 else 0.0
        local_clustering: list[float] = []
        for node, neighbors in enumerate(self.adjacency):
            degree = len(neighbors)
            if degree < 2:
                local_clustering.append(0.0)
                continue
            links = sum(
                1
                for a in neighbors
                for b in neighbors
                if a < b and self.has_edge(a, b)
            )
            local_clustering.append(links / comb(degree, 2))
        component_sizes = self.component_sizes()
        return {
            "network_nodes": self.n,
            "network_edges": edge_count,
            "network_average_degree": average_degree,
            "network_density": density,
            "network_average_clustering": (
                sum(local_clustering) / len(local_clustering) if local_clustering else 0.0
            ),
            "largest_component": component_sizes[0] if component_sizes else 0,
            "component_count": len(component_sizes),
        }


def ring_lattice(n: int, degree: int) -> Graph:
    if degree % 2 or degree < 2 or degree >= n:
        raise ValueError("ring degree must be even, >= 2, and < n")
    graph = Graph.empty(n)
    for node in range(n):
        for offset in range(1, degree // 2 + 1):
            graph.add_edge(node, (node + offset) % n)
    graph.validate()
    return graph


def small_world(n: int, degree: int, probability: float, rng: random.Random) -> Graph:
    if not 0.0 <= probability <= 1.0:
        raise ValueError("rewire probability must be in [0, 1]")
    graph = ring_lattice(n, degree)
    if probability == 0.0:
        return graph
    for node in range(n):
        for offset in range(1, degree // 2 + 1):
            old_neighbor = (node + offset) % n
            if not graph.has_edge(node, old_neighbor) or rng.random() >= probability:
                continue
            candidates = [
                candidate
                for candidate in range(n)
                if candidate != node and not graph.has_edge(node, candidate)
            ]
            if not candidates:
                continue
            graph.remove_edge(node, old_neighbor)
            graph.add_edge(node, rng.choice(candidates))
    graph.validate()
    return graph


def _weighted_sample_without_replacement(
    population: list[int], weights: list[float], sample_size: int, rng: random.Random
) -> list[int]:
    selected: list[int] = []
    candidates = list(population)
    candidate_weights = list(weights)
    for _ in range(min(sample_size, len(candidates))):
        total = sum(candidate_weights)
        threshold = rng.random() * total
        cumulative = 0.0
        index = len(candidates) - 1
        for idx, weight in enumerate(candidate_weights):
            cumulative += weight
            if cumulative >= threshold:
                index = idx
                break
        selected.append(candidates.pop(index))
        candidate_weights.pop(index)
    return selected


def preferential_attachment(n: int, ties_per_new_node: int, rng: random.Random) -> Graph:
    if ties_per_new_node < 1 or ties_per_new_node >= n:
        raise ValueError("ties_per_new_node must be in [1, n)")
    graph = Graph.empty(n)
    initial_size = min(n, ties_per_new_node + 1)
    for a in range(initial_size):
        for b in range(a + 1, initial_size):
            graph.add_edge(a, b)
    for node in range(initial_size, n):
        population = list(range(node))
        weights = [max(1, graph.degree(candidate)) for candidate in population]
        for target in _weighted_sample_without_replacement(
            population, weights, ties_per_new_node, rng
        ):
            graph.add_edge(node, target)
    graph.validate()
    return graph


def generate_network(
    network_type: str,
    n: int,
    mean_degree: int,
    rewire_probability: float,
    rng: random.Random,
) -> Graph:
    if network_type == "ring":
        return ring_lattice(n, mean_degree)
    if network_type == "small_world":
        return small_world(n, mean_degree, rewire_probability, rng)
    if network_type == "preferential_attachment":
        return preferential_attachment(n, max(1, mean_degree // 2), rng)
    raise ValueError(f"unsupported network type: {network_type}")
