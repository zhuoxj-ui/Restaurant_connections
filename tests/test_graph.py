"""
test_graph.py
Purpose: test suite for the restaurant recommendation network.

Covers:
  - Graph construction correctness
  - Edge weighting logic
  - Search and filtering behaviors
  - Centrality calculations
  - Data loading
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from restaurant import Restaurant
from graph import RestaurantGraph, _haversine_km


# Fixtures

def make_restaurant(business_id, name, cuisine, price_tier, stars,
                    review_count=100, lat=36.16, lon=-86.78):
    """Helper to create Restaurant objects for testing."""
    return Restaurant(
        business_id=business_id,
        name=name,
        cuisine=cuisine,
        price_tier=price_tier,
        stars=stars,
        review_count=review_count,
        latitude=lat,
        longitude=lon,
        address="123 Test St",
        categories=[cuisine, "Restaurants"],
    )


@pytest.fixture
def sample_restaurants():
    """
    A small set of restaurants with known relationships:
      - r1 and r2: same cuisine (Mexican), same price ($), very close → weight 6
      - r1 and r3: same price only → weight 1
      - r2 and r3: no shared attributes → weight 0 (no edge)
    """
    r1 = make_restaurant("id1", "Taco Town", "Mexican", 1, 4.5, lat=36.1600, lon=-86.7800)
    r2 = make_restaurant("id2", "Burrito Bros", "Mexican", 1, 4.0, lat=36.1601, lon=-86.7801)
    r3 = make_restaurant("id3", "Burger Barn", "Burgers", 2, 3.5, lat=36.9000, lon=-86.0000)
    return [r1, r2, r3]


@pytest.fixture
def built_graph(sample_restaurants):
    """A RestaurantGraph already built from sample_restaurants."""
    g = RestaurantGraph()
    g.build(sample_restaurants)
    return g


# Graph Construction

class TestGraphConstruction:

    def test_node_count(self, built_graph, sample_restaurants):
        """Graph should contain exactly as many nodes as input restaurants."""
        assert len(built_graph) == len(sample_restaurants)

    def test_all_restaurants_in_graph(self, built_graph, sample_restaurants):
        """Every restaurant's business_id should appear in the graph."""
        for r in sample_restaurants:
            assert r.business_id in built_graph

    def test_unknown_id_not_in_graph(self, built_graph):
        """A made-up ID should not be in the graph."""
        assert "not_a_real_id" not in built_graph

    def test_empty_graph(self):
        """Building from an empty list should produce a graph with no nodes."""
        g = RestaurantGraph()
        g.build([])
        assert len(g) == 0
        assert g.edge_count == 0

    def test_single_node_no_edges(self):
        """A single restaurant should produce no edges."""
        g = RestaurantGraph()
        r = make_restaurant("only", "Solo Spot", "Italian", 2, 4.0)
        g.build([r])
        assert g.edge_count == 0


# Edge Weighting

class TestEdgeWeighting:

    def test_max_weight_edge(self, built_graph):
        """
        r1 and r2 share cuisine (+3), are within 0.5km (+2), and same price (+1)
        → expected weight 6.
        """
        neighbors = dict(built_graph.neighbors("id1"))
        r2 = built_graph.get_restaurant("id2")
        assert neighbors[r2] == 6

    def test_no_edge_different_price_cuisine_far(self, built_graph):
        """
        r1 (Mexican, $) and r3 (Burgers, $$, far away) share nothing → no edge.
        """
        neighbors = dict(built_graph.neighbors("id1"))
        r3 = built_graph.get_restaurant("id3")
        assert r3 not in neighbors

    def test_no_edge_when_no_shared_attributes(self, built_graph):
        """
        r2 and r3 share nothing and are far apart → no edge should exist.
        """
        neighbors = dict(built_graph.neighbors("id2"))
        r3 = built_graph.get_restaurant("id3")
        assert r3 not in neighbors

    def test_edges_are_undirected(self, built_graph):
        """
        Edge weight from r1→r2 should equal edge weight from r2→r1.
        """
        r2 = built_graph.get_restaurant("id2")
        r1 = built_graph.get_restaurant("id1")
        w_forward  = dict(built_graph.neighbors("id1"))[r2]
        w_backward = dict(built_graph.neighbors("id2"))[r1]
        assert w_forward == w_backward

    def test_neighbors_sorted_by_weight(self, built_graph):
        """Neighbors should be returned in descending weight order."""
        nbrs = built_graph.neighbors("id1")
        weights = [w for _, w in nbrs]
        assert weights == sorted(weights, reverse=True)


# Haversine Distance

class TestHaversine:

    def test_same_point_is_zero(self):
        """Distance from a point to itself should be zero."""
        assert _haversine_km(36.16, -86.78, 36.16, -86.78) == pytest.approx(0.0)

    def test_known_distance(self):
        """
        Nashville to Memphis is roughly 320 km.
        Checks that the function is in the right ballpark.
        """
        dist = _haversine_km(36.1627, -86.7816, 35.1495, -90.0490)
        assert 300 < dist < 350

    def test_proximity_threshold(self):
        """Two restaurants 0.1 km apart should be within the 0.5 km threshold."""
        dist = _haversine_km(36.1600, -86.7800, 36.1609, -86.7800)
        assert dist < 0.5


# Search

class TestSearch:

    def test_search_by_name(self, built_graph):
        """Searching 'taco' should return Taco Town."""
        results = built_graph.search("taco")
        names = [r.name for r in results]
        assert "Taco Town" in names

    def test_search_by_cuisine(self, built_graph):
        """Searching 'mexican' should return both Mexican restaurants."""
        results = built_graph.search("mexican")
        assert len(results) == 2

    def test_search_case_insensitive(self, built_graph):
        """Search should be case-insensitive."""
        assert built_graph.search("TACO") == built_graph.search("taco")

    def test_search_no_results(self, built_graph):
        """A query that matches nothing should return an empty list."""
        assert built_graph.search("sushi") == []


# Filtering

class TestFilter:

    def test_filter_by_price_tier(self, built_graph):
        """Filtering by price_tier=1 should return only $ restaurants."""
        results = built_graph.filter_by(price_tier=1)
        assert all(r.price_tier == 1 for r in results)

    def test_filter_by_min_stars(self, built_graph):
        """Filtering by min_stars=4.0 should exclude 3.5-star Burger Barn."""
        results = built_graph.filter_by(min_stars=4.0)
        names = [r.name for r in results]
        assert "Burger Barn" not in names

    def test_filter_combined(self, built_graph):
        """Combining price and stars filters should return only matching restaurants."""
        results = built_graph.filter_by(price_tier=1, min_stars=4.0)
        assert all(r.price_tier == 1 and r.stars >= 4.0 for r in results)

    def test_filter_results_sorted_by_stars(self, built_graph):
        """Filter results should be sorted by stars descending."""
        results = built_graph.filter_by(min_stars=0.0)
        stars = [r.stars for r in results]
        assert stars == sorted(stars, reverse=True)


# Ranking

class TestRanking:

    def test_top_by_stars(self, built_graph):
        """top_by stars should return highest-rated restaurant first."""
        top = built_graph.top_by("stars", n=1)
        assert top[0].name == "Taco Town"

    def test_top_by_review_count(self, built_graph):
        """top_by review_count should respect review_count ordering."""
        top = built_graph.top_by("review_count", n=3)
        counts = [r.review_count for r in top]
        assert counts == sorted(counts, reverse=True)

    def test_top_by_invalid_metric(self, built_graph):
        """Passing an invalid metric should raise ValueError."""
        with pytest.raises(ValueError):
            built_graph.top_by("invalid_metric")

    def test_top_n_limit(self, built_graph):
        """top_by should return at most n results."""
        top = built_graph.top_by("stars", n=2)
        assert len(top) <= 2


# Centrality

class TestCentrality:

    def test_centrality_keys_match_nodes(self, built_graph, sample_restaurants):
        """Centrality dict should have one entry per node."""
        cent = built_graph.centrality()
        assert set(cent.keys()) == {r.business_id for r in sample_restaurants}

    def test_centrality_values_between_0_and_1(self, built_graph):
        """All centrality scores should be normalised between 0 and 1."""
        cent = built_graph.centrality()
        for score in cent.values():
            assert 0.0 <= score <= 1.0

    def test_most_central_is_highest_weight(self, built_graph):
        """
        r1 has edges to both r2 (weight 6) and r3 (weight 1) → total 7.
        r2 has edge to r1 only (weight 6) → total 6.
        r1 should have the highest centrality.
        """
        cent = built_graph.centrality()
        most_central = max(cent, key=cent.get)
        assert most_central == "id1"

    def test_isolated_node_has_zero_centrality(self):
        """A node with no edges should have centrality score of 0."""
        g = RestaurantGraph()
        r1 = make_restaurant("a", "Place A", "Italian", 1, 4.0, lat=36.0, lon=-86.0)
        r2 = make_restaurant("b", "Place B", "Japanese", 2, 3.0, lat=40.0, lon=-80.0)
        g.build([r1, r2])
        cent = g.centrality()
        assert cent["a"] == 0.0 or cent["b"] == 0.0