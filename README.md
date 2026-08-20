# Mediscope

NLP-powered disease outbreak surveillance dashboard.

## Overview

Mediscope scrapes WHO and CDC RSS feeds every 6 hours and uses spaCy named entity recognition combined with a TF-IDF / Logistic Regression classifier to extract disease outbreaks from news articles. Extracted records are enriched with real case counts from the WHO Global Health Observatory (GHO) API and displayed on an interactive Leaflet map with Chart.js trend visualisations. The system is designed for public health researchers and analysts who need a low-latency view of emerging disease events without paying for a commercial data feed.

## Tech Stack

| Layer | Technologies |
|---|---|
| Backend | Python 3.13, Flask, spaCy, Scrapy, scikit-learn, pymongo |
| Frontend | React 19, Vite, TailwindCSS, Leaflet, Chart.js |
| Database | MongoDB Atlas |
| Data sources | WHO RSS, CDC RSS, disease.sh API, WHO GHO API |

## Project Structure

```
Mediscopev2/
├── backend/
│   ├── app.py                        # Flask application entry point
│   ├── config.py                     # Environment variable loading
│   ├── api/
│   │   └── routes.py                 # All REST endpoints
│   ├── crawler/                      # Scrapy spiders for WHO / CDC RSS feeds
│   ├── crawlers/
│   │   └── who_gho_spider.py         # WHO GHO API case count fetcher
│   ├── database/
│   │   └── mongo_connection.py       # Shared MongoDB connection (get_db)
│   ├── nlp/
│   │   ├── ner.py                    # spaCy NER + PhraseMatcher entity extraction
│   │   ├── relevance.py              # TF-IDF / LR classifier (falls back to keywords)
│   │   ├── train_classifier.py       # Classifier training script
│   │   ├── alerts.py                 # Outbreak alert dispatch
│   │   └── models/                   # Saved classifier.pkl + vectorizer.pkl (gitignored)
│   └── pipeline/
│       ├── processor.py              # Main article processing pipeline
│       ├── enricher.py               # Case count enrichment from disease_stats
│       └── scheduler.py             # Recurring job scheduler
├── frontend/
│   ├── src/
│   │   ├── pages/                    # Route-level components (Map, Alerts, Compare …)
│   │   ├── components/               # Shared UI components
│   │   ├── services/                 # API service layer (axios)
│   │   └── utils/api.js              # Axios instance
│   └── vite.config.js
├── requirements.txt
└── .env                              # Not committed — see Setup below
```

## Setup

### Prerequisites

- Python 3.13
- Node.js 18+
- A MongoDB Atlas cluster (free tier is sufficient)

### 1. Clone the repository

```bash
git clone https://github.com/your-username/mediscope.git
cd mediscope
```

### 2. Create a `.env` file in the project root

```env
MONGODB_URI=mongodb+srv://<user>:<password>@cluster.mongodb.net/mediscope
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 4. Install frontend dependencies

```bash
cd frontend && npm install
```

### 5. Train the relevance classifier

Requires at least one run of the crawlers first so `raw_articles` is populated.

```bash
python -m backend.nlp.train_classifier
```

### 6. Fetch WHO GHO case count data

```bash
python -m backend.crawlers.who_gho_spider
```

### 7. Run the article processing pipeline

```bash
python -m backend.pipeline.processor
```

### 8. Start the backend

```bash
python -m backend.app
```

### 9. Start the frontend development server

```bash
cd frontend && npm run dev
```

The dashboard will be available at `http://localhost:5173`.

## Features

- Automated RSS ingestion from WHO and CDC every 6 hours via Scrapy
- spaCy NER combined with a TF-IDF / Logistic Regression classifier for disease and location extraction
- Real case count enrichment from the WHO GHO API, stored in MongoDB and looked up at processing time
- Interactive outbreak map with Leaflet, color-coded by severity
- Disease trend charts powered by Chart.js
- Email alert subscriptions by region, dispatched via SendGrid
- Classifier falls back to keyword matching when model files are absent, so the pipeline never crashes before first training

## Limitations

- The classifier is trained on auto-labeled data from the `raw_articles` collection. With fewer than ~100 articles the precision/recall figures are modest; retraining after accumulating more data will improve results significantly.
- WHO GHO does not provide case count data for COVID-19 or seasonal influenza via the public API. Outbreaks for these diseases will have `case_count_source: "unavailable"` until an alternative data source is wired in.
- Case counts sourced from WHO GHO reflect the most recent year available in the dataset, not real-time figures. They are used as order-of-magnitude estimates only.
- Country matching between WHO GHO country names and internal `COUNTRY_COORDS` keys is handled by a static normalization map. Countries absent from that map will be silently skipped during enrichment.

## License

MIT
