"""
restaurant.py
Purpose: core data class representing a single restaurant node in the graph.
"""

from dataclasses import dataclass, field

@dataclass
class Restaurant:
    """
    Represents a single restaurant as a graph node.
    
    Attributes:
        business_id: unique Yelp business identifier.
        name: restaurant name.
        cuisine: primary cuisine category (first Restaurants-adjacent tag).
        price_tier: price level 1-4 (from Yelp's RestaurantsPriceRange2).
        stars: average star rating (0.0 - 5.0).
        review_count: total number of reviews.
        latitude: geographic latitude.
        longitude: geographic longitude.
        address: street address.
        categories: full list of Yelp category strings.
        """
    
    business_id: str
    name: str
    cuisine: str
    price_tier: int
    stars: float
    review_count: int
    latitude: float
    longitude: float
    address: str
    categories: list = field(default_factory=list)


    def __repr__(self) -> str:
        return (
            f"Restaurant({self.name!r}, cuisine={self.cuisine!r}, "
            f"price={'$' * self.price_tier}, stars={self.stars})"
        )
 
    def __eq__(self, other) -> bool:
        return isinstance(other, Restaurant) and self.business_id == other.business_id
 
    def __hash__(self) -> int:
        return hash(self.business_id)