"""
narrative.py
Purpose: generates a natural-language dining evening narrative for a path
through the restaurant graph, powered by the Claude API.

Usage:
    from narrative import generate_narrative
    story = generate_narrative([restaurant_a, restaurant_b, restaurant_c], reviews)
"""

import json
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")
import anthropic

from restaurant import Restaurant

# Constants
REVIEWS_FILE = Path(__file__).parent / "data" / "nashville_reviews.json"
MAX_REVIEWS_PER_STOP = 2  # how many real reviews to include per restaurant


def load_reviews(filepath: Path = REVIEWS_FILE) -> Dict[str, List[str]]:
    """
    Loads the pre-filtered Nashville reviews from disk.

    Args:
        filepath: Path to nashville_reviews.json.

    Returns:
        Dict mapping business_id -> list of review text strings.

    Raises:
        FileNotFoundError: If the reviews file does not exist.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Reviews file not found at: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def _build_prompt(path: List[Restaurant],
                  reviews: Dict[str, List[str]]) -> str:
    """
    Constructs the prompt to send to Claude.
    Injects node attributes and real customer reviews for each stop.

    Args:
        path:    Ordered list of Restaurant objects representing the evening path.
        reviews: Dict mapping business_id to review text strings.

    Returns:
        A formatted prompt string.
    """
    stops_text = ""
    for i, restaurant in enumerate(path):
        stop_reviews = reviews.get(restaurant.business_id, [])[:MAX_REVIEWS_PER_STOP]

        stops_text += f"\nStop {i + 1}: {restaurant.name}\n"
        stops_text += f"Cuisine: {restaurant.cuisine}\n"
        stops_text += f"Price: {'$' * restaurant.price_tier}\n"
        stops_text += f"Rating: {restaurant.stars}/5\n"
        if stop_reviews:
            stops_text += "What diners say:\n"
            for review in stop_reviews:
                stops_text += f"\"{review[:200]}\"\n"

    prompt = f"""You are a passionate Nashville food critic writing for a local lifestyle magazine.

A diner is spending the evening visiting these restaurants in order:
{stops_text}
Write a vivid, flowing evening narrative (3-4 paragraphs) that:
- Follows the diner through each stop in sequence
- Weaves in details from the real diner reviews above
- Captures the atmosphere, flavours, and feeling of each place
- Reads like a story, not a list

Write in second person ("you"), as if guiding the reader through the evening."""

    return prompt


def generate_narrative(path: List[Restaurant],
                       reviews: Dict[str, List[str]] = None) -> str:
    """
    Calls the Claude API to generate a dining evening narrative.

    Args:
        path:    Ordered list of Restaurant objects (2–4 recommended).
        reviews: Optional pre-loaded reviews dict. Loaded from disk if None.

    Returns:
        A natural-language narrative string.

    Raises:
        ValueError: If path is empty.
    """
    if not path:
        raise ValueError("Path must contain at least one restaurant.")

    if reviews is None:
        reviews = load_reviews()

    client = anthropic.Anthropic()
    prompt = _build_prompt(path, reviews)

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text