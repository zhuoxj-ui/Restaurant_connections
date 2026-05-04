"""
app.py
Streamlit web interface for the Nashville Restaurant Recommendation Network.

Run with:
    streamlit run app.py
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from data_loader import load_nashville_restaurants
from graph import RestaurantGraph
from narrative import load_reviews, generate_narrative

# Page config

st.set_page_config(
    page_title="Nashville Restaurant Network",
    page_icon="🍽️",
    layout="wide",
)

# Simple CSS

st.markdown("""
<style>
.restaurant-card {
    background: #f8f8f8;
    border-left: 4px solid #c0392b;
    padding: 0.8rem 1rem;
    margin: 0.4rem 0;
}
.restaurant-name {
    font-size: 1.1rem;
    font-weight: bold;
    color: #111111;
}
.restaurant-meta {
    font-size: 0.85rem;
    color: #444444;
    margin-top: 0.2rem;
}
.review-box {
    background: #f0f0f0;
    border-left: 3px solid #888;
    padding: 0.7rem 1rem;
    margin: 0.4rem 0;
    font-size: 0.9rem;
    color: #222222;
    line-height: 1.6;
}
.narrative-box {
    background: #fff8f0;
    border-left: 4px solid #c0392b;
    padding: 1rem 1.5rem;
    font-size: 0.95rem;
    color: #111111;
    line-height: 1.8;
}
</style>
""", unsafe_allow_html=True)

# Load data (cached)

@st.cache_resource(show_spinner="Loading restaurant data...")
def load_data():
    restaurants = load_nashville_restaurants()
    g = RestaurantGraph()
    g.build(restaurants)
    reviews = load_reviews()
    return restaurants, g, reviews


restaurants, graph, reviews = load_data()

# Sidebar

with st.sidebar:
    st.title("Nashville Restaurant Network")
    st.caption(f"{len(graph)} restaurants · {graph.edge_count:,} connections")
    st.markdown("---")
    mode = st.radio(
        "Navigation",
        ["Search", "Restaurant Profile", "Rankings", "Filter", "Deep Dive"],
    )

# Helper 

def render_card(r, weight=None):
    price = "$" * r.price_tier
    weight_str = f"  |  Match score: {weight}" if weight else ""
    st.markdown(f"""
    <div class="restaurant-card">
        <div class="restaurant-name">{r.name}</div>
        <div class="restaurant-meta">{price}  |  {r.stars} stars  |  {r.cuisine}{weight_str}</div>
        <div style="font-size:0.8rem; color:#666; margin-top:0.2rem;">{r.address}</div>
    </div>
    """, unsafe_allow_html=True)


# Search

if mode == "Search":
    st.header("Search Restaurants")
    query = st.text_input("Search by name or cuisine", placeholder="e.g. pizza, sushi, Thai...")
    if query:
        results = graph.search(query)
        st.write(f"{len(results)} results for '{query}'")
        for r in results[:30]:
            render_card(r)

# Restaurant profile

elif mode == "Restaurant Profile":
    st.header("Restaurant Profile")
    all_names = sorted([r.name for r in restaurants])
    selected_name = st.selectbox("Select a restaurant", all_names)
    selected = next((r for r in restaurants if r.name == selected_name), None)

    if selected:
        st.subheader(selected.name)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Stars", selected.stars)
        col2.metric("Reviews", f"{selected.review_count:,}")
        col3.metric("Price", "$" * selected.price_tier)
        col4.metric("Centrality", f"{graph.centrality().get(selected.business_id, 0):.2f}")
        st.caption(f"Cuisine: {selected.cuisine}  |  {selected.address}")

        st.markdown("---")
        st.subheader("Most Similar Restaurants")
        neighbors = graph.neighbors(selected.business_id)[:10]
        for r, w in neighbors:
            render_card(r, weight=w)

# Rankings

elif mode == "Rankings":
    st.header("Rankings")
    metric = st.radio(
        "Rank by",
        ["stars", "review_count", "centrality"],
        format_func=lambda x: {"stars": "Star Rating", "review_count": "Review Count", "centrality": "Network Centrality"}[x],
        horizontal=True,
    )
    n = st.slider("Number of results", 5, 50, 20)
    top = graph.top_by(metric, n)
    for i, r in enumerate(top):
        price = "$" * r.price_tier
        st.markdown(f"""
        <div class="restaurant-card">
            <div class="restaurant-name">#{i+1}  {r.name}</div>
            <div class="restaurant-meta">{price}  |  {r.stars} stars  |  {r.cuisine}  |  {r.review_count:,} reviews</div>
        </div>
        """, unsafe_allow_html=True)

# Filter

elif mode == "Filter":
    st.header("Filter Restaurants")
    col1, col2 = st.columns(2)
    with col1:
        price_option = st.selectbox(
            "Price Tier",
            ["Any", "$ Budget", "$$ Moderate", "$$$ Upscale", "$$$$ Fine Dining"],
        )
    with col2:
        min_stars = st.slider("Minimum Rating", 0.0, 5.0, 3.5, 0.5)

    price_map = {"Any": None, "$ Budget": 1, "$$ Moderate": 2, "$$$ Upscale": 3, "$$$$ Fine Dining": 4}
    results = graph.filter_by(price_tier=price_map[price_option], min_stars=min_stars)
    st.write(f"{len(results)} restaurants match your criteria")
    for r in results[:40]:
        render_card(r)

# Deep Dive

elif mode == "Deep Dive":
    st.header("Restaurant Deep Dive")
    st.caption("Browse reviews and visit Yelp for more details.")

    all_names = sorted([r.name for r in restaurants])
    selected_name = st.selectbox("Select a restaurant", all_names)
    selected = next((r for r in restaurants if r.name == selected_name), None)

    if selected:
        st.subheader(selected.name)
        st.write(f"**Cuisine:** {selected.cuisine}  |  **Price:** {'$' * selected.price_tier}  |  **Stars:** {selected.stars}  |  **Reviews:** {selected.review_count:,}")

        yelp_url = f"https://www.yelp.com/biz/{selected.business_id}"
        st.markdown(f"[View on Yelp]({yelp_url})")

        st.markdown("---")

        restaurant_reviews = reviews.get(selected.business_id, [])
        if restaurant_reviews:
            st.subheader(f"Top Reviews ({len(restaurant_reviews)} shown)")
            for review in restaurant_reviews:
                st.markdown(f'<div class="review-box">{review}</div>', unsafe_allow_html=True)
        else:
            st.info("No reviews available for this restaurant.")

        st.markdown("---")

        st.subheader("AI Dining Narrative")
        st.caption("Requires an Anthropic API key (see README).")
        if st.button("Generate Narrative"):
            try:
                with st.spinner("Generating..."):
                    story = generate_narrative([selected], reviews)
                st.markdown(f'<div class="narrative-box">{story.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
            except Exception:
                st.warning("Narrative generation requires a valid Anthropic API key. See README for setup instructions.")
