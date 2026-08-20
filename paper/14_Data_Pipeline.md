# Complete Data Pipeline

This chapter outlines the exact, step-by-step lifecycle of data as it flows through the MediScope architecture, from raw internet text to a visual dot on the frontend map.

## The Pipeline Workflow

### Step 1: Web Crawling
1. The `scheduler.py` cron job triggers `scrapy crawl who_spider`.
2. The spider fetches `https://www.who.int/feeds/entity/csr/don/en/rss.xml`.
3. The spider extracts an article: *"New Ebola cases confirmed in DR Congo"*.
4. The spider saves this as a JSON document in the MongoDB `raw_articles` collection, marking `processed: false`.

### Step 2: Relevance Classification (ML)
1. The main orchestrator, `processor.py`, queries MongoDB for all documents where `processed == False`.
2. It sends the article text to `relevance.py`.
3. The TF-IDF Vectorizer transforms the text.
4. The Logistic Regression model predicts a high likelihood of this being an outbreak. It returns `{"is_relevant": True, "confidence": 0.92}`.

### Step 3: Entity Extraction (NLP)
1. Because it is relevant, `processor.py` sends the text to `ner.py`.
2. `spaCy PhraseMatcher` identifies "Ebola". The normalization map confirms it as "ebola".
3. `spaCy GPE` recognizer identifies "DR Congo". The normalization map confirms it as "DR Congo".
4. Output: `{"diseases": ["ebola"], "locations": ["DR Congo"]}`.

### Step 4: Data Enrichment
1. The processor needs to know how many cases are associated with this event.
2. It calls `enricher.py`, requesting historical data for "ebola" in "DR Congo".
3. The enricher queries the data previously cached by `who_gho_spider.py`.
4. It finds an estimated count and returns `case_count: 45`.

### Step 5: Storage and Deduplication
1. The processor attempts to save this to the `outbreaks_v2` collection.
2. It first checks if an outbreak for "ebola" in "DR Congo" already exists for today's date (to prevent inserting duplicates if the WHO publishes two updates on the same day).
3. If no duplicate exists, it inserts the new document with coordinates (looked up via a static dictionary mapping countries to lat/lng).
4. The original document in `raw_articles` is updated to `processed: true`.

### Step 6: API Delivery
1. A user navigates to `http://localhost:5173`.
2. The React `Map.jsx` component mounts and executes an Axios `GET` request to `http://localhost:5000/api/outbreaks`.
3. The Flask API (`routes.py`) queries `outbreaks_v2`, serializes the ObjectId and Datetime fields, and returns the JSON payload.

### Step 7: Frontend Rendering
1. Axios receives the JSON payload.
2. The React `outbreaks` state is updated.
3. Leaflet iterates over the array, placing a marker at the coordinates for DR Congo. The color of the marker is determined by the dynamic `severity` attribute calculated by the backend.

### Diagram: The Data Pipeline
```ascii
[Internet RSS] 
      |
 (Scrapy Spider)
      |
      v
[ raw_articles ] ---> (processor.py) ---> [ relevance.py (ML) ]
                                |
                                +-------> [ ner.py (NLP) ]
                                |
                                +-------> [ enricher.py ]
                                |
      +-------------------------+
      |
      v
[ outbreaks_v2 ] <--- (routes.py / API) <--- [ React Frontend ]
```
