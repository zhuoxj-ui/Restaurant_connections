"""
graph.py
Purpose: builds and queries the restaurant recommendation graph.

Edge weight rules (additive):
  +3  shared primary cuisine
  +2  geographic distance <= 0.5 km
  +1  same price tier
"""

import math
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from restaurant import Restaurant

# Constants
WEIGHT_CUISINE = 3
WEIGHT_PROXIMITY = 2
WEIGHT_PRICE = 1
PROXIMITY_KM = 0.5


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Returns the great-circle distance in kilometres between two coordinates.

    Args:
        lat1, lon1: Coordinates of the first point.
        lat2, lon2: Coordinates of the second point.

    Returns:
        Distance in kilometres.
    """
    R = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) ** 2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(d_lon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


class RestaurantGraph:
    """
    Weighted undirected graph of Restaurant nodes.

    Nodes  — Restaurant objects keyed by business_id.
    Edges  — Weighted by shared cuisine (+3), proximity (+2), price tier (+1).

    Public Methods:
        build(restaurants)      — Populate nodes and edges.
        neighbors(business_id)  — Return sorted (Restaurant, weight) neighbors.
        search(query)           — Find restaurants by name or cuisine substring.
        top_by(metric, n)       — Rank restaurants by stars, reviews, or centrality.
        filter_by(price, stars) — Filter restaurants by price tier and min rating.
        centrality()            — Weighted degree centrality for every node.
    """

    def __init__(self) -> None:
        self._nodes: Dict[str, Restaurant] = {}
        # adjacency: business_id -> {business_id: weight}
        self._adj: Dict[str, Dict[str, int]] = defaultdict(dict)

    # Construction

    def build(self, restaurants: List[Restaurant]) -> None:
        """
        Populates the graph from a list of Restaurant objects.
        Computes all pairwise edges where at least one weight criterion is met.

        Args:
            restaurants: List of Restaurant objects to add as nodes.
        """
        self._nodes = {r.business_id: r for r in restaurants}
        self._adj = defaultdict(dict)

        ids = list(self._nodes.keys())
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                a = self._nodes[ids[i]]
                b = self._nodes[ids[j]]
                weight = self._edge_weight(a, b)
                if weight > 0:
                    self._adj[a.business_id][b.business_id] = weight
                    self._adj[b.business_id][a.business_id] = weight

    @staticmethod
    def _edge_weight(a: Restaurant, b: Restaurant) -> int:
        """
        Computes the additive edge weight between two restaurants.

        Args:
            a: First Restaurant.
            b: Second Restaurant.

        Returns:
            Total weight (0 means no edge).
        """
        weight = 0
        if a.cuisine == b.cuisine:
            weight += WEIGHT_CUISINE
        dist = _haversine_km(a.latitude, a.longitude, b.latitude, b.longitude)
        if dist <= PROXIMITY_KM:
            weight += WEIGHT_PROXIMITY
        if a.price_tier == b.price_tier:
            weight += WEIGHT_PRICE
        return weight

    # Querying

    def neighbors(self, business_id: str) -> List[Tuple[Restaurant, int]]:
        """
        Returns the neighbors of a node sorted by edge weight (descending).

        Args:
            business_id: The node's Yelp business ID.

        Returns:
            List of (Restaurant, weight) tuples.

        Raises:
            KeyError: If business_id is not in the graph.
        """
        if business_id not in self._nodes:
            raise KeyError(f"Restaurant '{business_id}' not found in graph.")
        return sorted(
            [(self._nodes[nbr], w) for nbr, w in self._adj[business_id].items()],
            key=lambda x: x[1],
            reverse=True,
        )

    def search(self, query: str) -> List[Restaurant]:
        """
        Returns restaurants whose name or cuisine contains the query string
        (case-insensitive).

        Args:
            query: Substring to search for.

        Returns:
            List of matching Restaurant objects.
        """
        q = query.lower()
        return [
            r for r in self._nodes.values()
            if q in r.name.lower() or q in r.cuisine.lower()
        ]

    def top_by(self, metric: str = "stars", n: int = 10) -> List[Restaurant]:
        """
        Returns the top-n restaurants ranked by a given metric.

        Args:
            metric: One of 'stars', 'review_count', or 'centrality'.
            n:      Number of results to return.

        Returns:
            List of Restaurant objects in descending order.

        Raises:
            ValueError: If metric is not one of the allowed values.
        """
        allowed = {"stars", "review_count", "centrality"}
        if metric not in allowed:
            raise ValueError(f"metric must be one of {allowed}, got {metric!r}")

        if metric == "centrality":
            cent = self.centrality()
            return sorted(self._nodes.values(), key=lambda r: cent[r.business_id], reverse=True)[:n]

        return sorted(self._nodes.values(), key=lambda r: getattr(r, metric), reverse=True)[:n]

    def filter_by(self, price_tier: Optional[int] = None,
                  min_stars: float = 0.0) -> List[Restaurant]:
        """
        Filters restaurants by price tier and minimum star rating.

        Args:
            price_tier: If provided, only return restaurants with this price tier.
            min_stars:  Minimum acceptable star rating (inclusive).

        Returns:
            List of matching Restaurant objects.
        """
        results = [
            r for r in self._nodes.values()
            if r.stars >= min_stars
        ]
        if price_tier is not None:
            results = [r for r in results if r.price_tier == price_tier]
        return sorted(results, key=lambda r: r.stars, reverse=True)

    def centrality(self) -> Dict[str, float]:
        """
        Computes weighted degree centrality for every node.
        Defined as the sum of edge weights divided by the maximum possible
        sum (to normalise between 0 and 1).

        Returns:
            Dict mapping business_id -> centrality score.
        """
        raw = {bid: sum(self._adj[bid].values()) for bid in self._nodes}
        max_val = max(raw.values()) if any(v > 0 for v in raw.values()) else 1
        return {bid: score / max_val for bid, score in raw.items()}

    # Helpers

    def __len__(self) -> int:
        return len(self._nodes)

    def __contains__(self, business_id: str) -> bool:
        return business_id in self._nodes

    def get_restaurant(self, business_id: str) -> Optional[Restaurant]:
        """Returns the Restaurant for a given business_id, or None."""
        return self._nodes.get(business_id)

    @property
    def edge_count(self) -> int:
        """Total number of undirected edges in the graph."""
        return sum(len(v) for v in self._adj.values()) // 2