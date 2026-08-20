# Project Overview

## High-Level Workflow
MediScope operates as a continuous, automated pipeline divided into distinct phases: Ingestion, Processing, Storage, and Presentation.

### 1. Ingestion Phase
A scheduled task (running every 6 hours) triggers Scrapy spiders (`who_spider.py`, `cdc_spider.py`). These spiders fetch the latest XML feeds from the WHO and CDC, extract the article titles, descriptions, publication dates, and URLs, and insert this raw data into the `raw_articles` MongoDB collection.

### 2. Processing Phase (NLP & ML)
The `processor.py` script pulls unprocessed articles from the database. 
- **Classification**: Each article's text is passed to the ML classifier (`relevance.py`). Using a TF-IDF Vectorizer and Logistic Regression model, the system calculates a confidence score. Articles with a score $\ge 0.5$ are deemed relevant outbreaks.
- **Extraction**: Relevant articles are passed to the NLP module (`ner.py`). spaCy's `PhraseMatcher` and fallback text-scans extract the disease name and location, normalizing them against standard maps.
- **Enrichment**: The `enricher.py` script queries historical/real-time case counts for the specific disease and country (previously fetched by the `who_gho_spider.py`) to append a `case_count` to the outbreak record.

### 3. Storage Phase
Verified, extracted, and enriched outbreak records are saved to the `outbreaks_v2` MongoDB collection. The system also calculates dynamic severity scores (Low, Medium, High) based on global case counts and occurrence frequencies.

### 4. Presentation Phase
Users access the React frontend (`http://localhost:5173`). The frontend makes asynchronous requests to the Flask backend API (`/api/outbreaks`, `/api/diseases`). Data is visualized using Leaflet maps (`Map.jsx`) and Chart.js graphs (`Analytics.jsx`). Users can also subscribe to email alerts via the `/api/alerts/subscribe` endpoint.

## Key Features Implemented in the Final Code
- **Scheduled Autonomous Scraping**: Fully automated Scrapy pipeline that requires zero user input to keep the database updated.
- **Hybrid NLP Engine**: Combines spaCy's machine-learning tokenization with deterministic regex/substring fallbacks to catch edge cases (like hyphenated diseases or countries missing from spaCy's small model).
- **Graceful ML Fallback**: If the TF-IDF/Logistic Regression model files are absent (e.g., on first run), the system seamlessly falls back to a keyword-matching heuristic, ensuring the pipeline never crashes.
- **Dynamic Severity Calculation**: Disease severity isn't hardcoded; it is computed dynamically by aggregating total historical cases and outbreak frequencies from the database.
- **Interactive Global Map**: Visualizes outbreaks with color-coded markers (Yellow = Low, Orange = Medium, Red = High severity).
- **Comparative Analytics**: Allows side-by-side comparison of multiple diseases or countries over custom date ranges.
- **Automated Alerts**: Integration with SendGrid (or SMTP) to dispatch notifications to subscribed users when an outbreak matches their preferences.

## Recommended Code Reading Order (For New Developers)
If a new developer joins the project today, they should read the files in this specific order to understand the flow of data:
1. `backend/app.py` - Understands how the server starts and initializes the DB.
2. `backend/api/routes.py` - Shows exactly what data the frontend can request.
3. `backend/crawler/spiders/who_spider.py` - Shows how raw data enters the system.
4. `backend/pipeline/processor.py` - The core orchestrator. Shows how raw data is turned into structured outbreaks.
5. `backend/nlp/relevance.py` & `backend/nlp/ner.py` - Explains the "brain" of the extraction process.
6. `frontend/src/App.jsx` - The entry point for the UI.
7. `frontend/src/pages/Map.jsx` - The most complex and feature-rich UI component.
