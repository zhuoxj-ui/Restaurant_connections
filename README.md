# Nashville Restaurant Recommendation Network
SI 507 Final Project

This project builds a weighted graph of Nashville restaurants using the Yelp Open Dataset.
Restaurants are connected based on shared cuisine, geographic proximity, and price tier.
The Streamlit app lets you search, filter, rank, and explore the network interactively.

## Project Structure

```
restaurant_network/
├── app.py              # Streamlit web interface
├── restaurant.py       # Restaurant node class
├── data_loader.py      # Loads and cleans Yelp data
├── graph.py            # Graph construction and queries
├── narrative.py        # LLM dining narrative (optional)
├── review_data.py      # Script to generate nashville_reviews.json
├── data/               # Data files (not included in repo, see below)
└── tests/              # Test suite
```

## Setup

Install dependencies:
```
pip install -r requirements.txt
```

## Data

This project uses the [Yelp Open Dataset](https://www.yelp.com/dataset).
Download it and place `yelp_academic_dataset_business.json` in the `data/` folder.

Then generate the Nashville reviews file by running:
```
python3 review_data.py
```

This script reads `yelp_academic_dataset_review.json` from the same folder and outputs
`nashville_reviews.json` into `data/`. Make sure both Yelp files are in the same directory
before running.

## Running the App

```
streamlit run app.py
```

## Running Tests

```
python3 -m pytest tests/ -v
```

## LLM Narrative Feature (optional)

The Deep Dive page has an option to generate an AI dining narrative using the Claude API.
To enable it, create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=your_key_here
```

Without a key, all other features still work normally.
