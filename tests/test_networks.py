import random
import unittest

from ena_abm.network import (
    Graph,
    preferential_attachment,
    ring_lattice,
    small_world,
)


class NetworkTests(unittest.TestCase):
    def test_ring_has_requested_degree_and_no_invalid_edges(self):
        graph = ring_lattice(12, 4)
        graph.validate()
        self.assertTrue(all(graph.degree(node) == 4 for node in range(12)))
        self.assertEqual(len(graph.edges()), 24)
        self.assertEqual(graph.component_sizes(), [12])

    def test_zero_rewiring_is_exact_ring(self):
        ring = ring_lattice(20, 6)
        world = small_world(20, 6, 0.0, random.Random(7))
        self.assertEqual(ring.edges(), world.edges())

    def test_preferential_attachment_is_connected_and_heterogeneous(self):
        graph = preferential_attachment(50, 3, random.Random(11))
        graph.validate()
        self.assertEqual(graph.component_sizes(), [50])
        degrees = [graph.degree(node) for node in range(50)]
        self.assertGreater(max(degrees), min(degrees))

    def test_isolated_graph_reports_all_components(self):
        graph = Graph.empty(5)
        graph.validate()
        self.assertEqual(graph.component_sizes(), [1, 1, 1, 1, 1])
        self.assertEqual(graph.diagnostics()["network_density"], 0.0)

    def test_complete_graph_has_density_one(self):
        graph = Graph.empty(5)
        for a in range(5):
            for b in range(a + 1, 5):
                graph.add_edge(a, b)
        graph.validate()
        self.assertEqual(graph.diagnostics()["network_density"], 1.0)
        self.assertEqual(graph.diagnostics()["component_count"], 1)

    def test_fragmented_graph_reports_multiple_components(self):
        graph = Graph.empty(6)
        graph.add_edge(0, 1)
        graph.add_edge(1, 2)
        graph.add_edge(3, 4)
        graph.validate()
        self.assertEqual(graph.component_sizes(), [3, 2, 1])


if __name__ == "__main__":
    unittest.main()
