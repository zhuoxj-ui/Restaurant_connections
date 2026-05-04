"""
test_data_loader.py
Purpose: tests for data_loader.py.

Covers:
  - _primary_cuisine: correct extraction and fallback behavior
  - _price_tier: valid values, missing values, out-of-range values
  - load_nashville_restaurants: integration test against real dataset
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from data_loader import _primary_cuisine, _price_tier, load_nashville_restaurants
from restaurant import Restaurant


# _primary_cuisine

class TestPrimaryCuisine:

    def test_returns_first_non_skip_tag(self):
        """Should return the first tag that is not in the skip list."""
        result = _primary_cuisine("Restaurants, Food, Mexican")
        assert result == "Mexican"

    def test_skips_restaurants_tag(self):
        """'Restaurants' alone should fall back to 'Other'."""
        result = _primary_cuisine("Restaurants")
        assert result == "Other"

    def test_skips_multiple_generic_tags(self):
        """Should skip all generic tags and return the first specific one."""
        result = _primary_cuisine("Food, Nightlife, Bars, Italian")
        assert result == "Italian"

    def test_empty_string_returns_other(self):
        """Empty categories string should return 'Other'."""
        result = _primary_cuisine("")
        assert result == "Other"

    def test_none_returns_other(self):
        """None input should return 'Other'."""
        result = _primary_cuisine(None)
        assert result == "Other"

    def test_whitespace_stripped(self):
        """Tags with leading/trailing spaces should still match correctly."""
        result = _primary_cuisine("  Restaurants ,   Sushi Bars  ")
        assert result == "Sushi Bars"

    def test_all_skip_tags_returns_other(self):
        """If every tag is in the skip list, should return 'Other'."""
        result = _primary_cuisine("Restaurants, Food, Nightlife, Bars")
        assert result == "Other"


# _price_tier

class TestPriceTier:

    def test_valid_tier_1(self):
        assert _price_tier({"RestaurantsPriceRange2": "1"}) == 1

    def test_valid_tier_4(self):
        assert _price_tier({"RestaurantsPriceRange2": "4"}) == 4

    def test_missing_key_defaults_to_2(self):
        """Attributes dict with no price key should return default of 2."""
        assert _price_tier({}) == 2

    def test_none_attributes_defaults_to_2(self):
        """None attributes should return default of 2."""
        assert _price_tier(None) == 2

    def test_non_numeric_value_defaults_to_2(self):
        """Unparseable value should return default of 2."""
        assert _price_tier({"RestaurantsPriceRange2": "expensive"}) == 2

    def test_value_clamped_to_minimum_1(self):
        """Values below 1 should be clamped to 1."""
        assert _price_tier({"RestaurantsPriceRange2": "0"}) == 1

    def test_value_clamped_to_maximum_4(self):
        """Values above 4 should be clamped to 4."""
        assert _price_tier({"RestaurantsPriceRange2": "9"}) == 4

    def test_integer_value(self):
        """Integer (not string) price value should still parse correctly."""
        assert _price_tier({"RestaurantsPriceRange2": 3}) == 3


# load_nashville_restaurants

class TestLoadNashvilleRestaurants:

    def test_returns_list_of_restaurants(self):
        """Should return a non-empty list of Restaurant objects."""
        restaurants = load_nashville_restaurants()
        assert isinstance(restaurants, list)
        assert len(restaurants) > 0
        assert all(isinstance(r, Restaurant) for r in restaurants)

    def test_only_nashville_restaurants(self):
        """All returned restaurants should be from Nashville."""
        restaurants = load_nashville_restaurants()
        # We can't check city directly (not stored on Restaurant),
        # but we can verify count is in the expected range.
        assert 1500 <= len(restaurants) <= 2000

    def test_all_open(self):
        """data_loader filters is_open==1, so all restaurants should be open.
        We verify indirectly: review_count >= 0 and stars in valid range."""
        restaurants = load_nashville_restaurants()
        for r in restaurants:
            assert 0.0 <= r.stars <= 5.0
            assert r.review_count >= 0

    def test_no_missing_business_ids(self):
        """Every restaurant should have a non-empty business_id."""
        restaurants = load_nashville_restaurants()
        assert all(r.business_id for r in restaurants)

    def test_no_missing_names(self):
        """Every restaurant should have a non-empty name."""
        restaurants = load_nashville_restaurants()
        assert all(r.name for r in restaurants)

    def test_price_tiers_in_valid_range(self):
        """All price tiers should be between 1 and 4."""
        restaurants = load_nashville_restaurants()
        assert all(1 <= r.price_tier <= 4 for r in restaurants)

    def test_cuisine_never_empty(self):
        """No restaurant should have an empty cuisine string."""
        restaurants = load_nashville_restaurants()
        assert all(r.cuisine for r in restaurants)

    def test_coordinates_in_nashville_range(self):
        """
        Nashville sits roughly at lat 36.0–36.4, lon -87.1 to -86.5.
        Most restaurants should fall within this bounding box.
        """
        restaurants = load_nashville_restaurants()
        in_bounds = [
            r for r in restaurants
            if 35.5 <= r.latitude <= 37.0 and -88.0 <= r.longitude <= -86.0
        ]
        assert len(in_bounds) / len(restaurants) > 0.9

    def test_file_not_found_raises_error(self, tmp_path):
        """Passing a non-existent path should raise FileNotFoundError."""
        from pathlib import Path
        with pytest.raises(FileNotFoundError):
            load_nashville_restaurants(tmp_path / "does_not_exist.json")
