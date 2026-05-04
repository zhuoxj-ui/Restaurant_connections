"""
data_loader.py
Purpose: reads the Yelp Open Dataset business.json and returns Restaurant objects
filtered to Nashville, TN restaurants that are currently open.
"""

import json
from pathlib import Path
from typing import List

from restaurant import Restaurant

# Constants
CITY = "Nashville"
DATA_FILE = Path(__file__).parent / "data" / "yelp_academic_dataset_business.json"

# Categroeis to skip when picking the primary cuisine label
_SKIP_CATEGORIES = {
    "Restaurants", "Food", "Nightlife", "Bars", "Event Planning & Services",
    "Arts & Entertainment", "Shopping", "Beauty & Spas", "Health & Medical",
}


def _primary_cuisine(categories_str: str) -> str:
    """
    Returns the first meaningful cuisine tag from a comma-separated
    Yelp categories string, falling back to 'Other' if none found.
    
    Args:
        categories_str: Raw categories string from Yelp JSON.
        
    Returns:
        A single cuisine label string.
    """
    if not categories_str:
        return "Other"
    tags = [c.strip() for c in categories_str.split(",")]
    for tag in tags:
        if tag not in _SKIP_CATEGORIES:
            return tag
    return "Other"


def _price_tier(attributes: dict) -> int:
    """
    Extracts the price tier (1-4) from the attributes dict.
    Defaults to 2 if missing or unparseable.
    
    Args:
        attributes: Yelp business attributes dict.
        
    Returns:
        Integer price tier between 1 and 4.
    """
    if not attributes:
        return 2
    raw = attributes.get("RestaurantsPriceRange2")
    try:
        tier = int(raw)
        return max(1, min(4, tier))
    except (TypeError, ValueError):
        return 2
    

def load_nashville_restaurants(filepath: Path = DATA_FILE) -> List[Restaurant]:
    """
    Loads and returns all open Nashville restaurants from the Yelp dataset.
    
    Args:
        filepath: Path to yelp_academic_dataset_business.json.
        
    Returns:
        List of Restaurants objects.
        
    Raises:
        FileNotFoundError: if the dataset file does not exist at filepath.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Dataset not found at: {filepath}")
    
    restaurants = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            if obj.get("city") != CITY:
                continue
            cats = obj.get("categories") or ""
            if "Restaurants" not in cats:
                continue
            if obj.get("is_open") != 1:
                continue

            restaurants.append(Restaurant(
                business_id=obj["business_id"],
                name=obj["name"],
                cuisine=_primary_cuisine(cats),
                price_tier=_price_tier(obj.get("attributes")),
                stars=float(obj.get("stars", 0)),
                review_count=int(obj.get("review_count", 0)),
                latitude=float(obj.get("latitude", 0)),
                longitude=float(obj.get("longitude", 0)),
                address=obj.get("address", ""),
                categories=[c.strip() for c in cats.split(",")],
            ))
 
    return restaurants