import json

nashville_ids = set()
with open("yelp_dataset/yelp_academic_dataset_business.json", "r") as f:
    for line in f:
        obj = json.loads(line)
        if obj.get("city") == "Nashville" and "Restaurants" in (obj.get("categories") or ""):
            nashville_ids.add(obj["business_id"])

print(f"Nashville Restaurants: {len(nashville_ids)}")

from collections import defaultdict
reviews = defaultdict(list)

with open("yelp_dataset/yelp_academic_dataset_review.json", "r") as f:
    for line in f:
        obj = json.loads(line)
        bid = obj.get("business_id")
        if bid in nashville_ids and obj.get("stars") >= 4:
            if len(reviews[bid]) < 3:
                reviews[bid].append(obj.get("text", ""))

with open("nashville_reviews.json", "w") as f:
    json.dump(dict(reviews), f)

print(f"No of Restaurants: {len(reviews)}")