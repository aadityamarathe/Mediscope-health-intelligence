# MediScope: NLP-Powered Disease Outbreak Monitoring System
## Comprehensive Implementation Paper

---

## 1. Abstract
MediScope is an advanced, automated disease outbreak surveillance system designed to provide researchers and public health analysts with a low-latency, real-time view of emerging global health threats. By ingesting RSS feeds from authoritative sources such as the World Health Organization (WHO) and the Centers for Disease Control and Prevention (CDC), the system leverages Natural Language Processing (NLP) and Machine Learning (ML) to extract actionable outbreak intelligence. This data is enriched with real case counts and presented via an interactive, map-driven frontend dashboard.

---

## 2. Introduction
Traditional disease tracking methods often suffer from high latency and reliance on commercial data feeds. MediScope addresses this gap by implementing an automated pipeline that continuously scrapes public health news, classifies its relevance, and extracts critical entities (diseases and locations). The final output is an intuitive dashboard featuring an interactive map, trend analytics, and automated alerting, enabling proactive outbreak monitoring.

---

## 3. Technology Stack
The project is built on a modern, scalable technology stack:
- **Backend**: Python 3.13, Flask
- **Data Ingestion**: Scrapy (Web Crawling)
- **Database**: MongoDB Atlas (NoSQL)
- **Machine Learning & NLP**: spaCy, Scikit-Learn
- **Frontend**: React 19, Vite, TailwindCSS
- **Visualizations**: Leaflet (Mapping), Chart.js (Data Analytics)

---

## 4. System Architecture
The system follows a decoupled, client-server architecture:
1. **Data Ingestion Layer**: Scrapy spiders routinely fetch data from WHO, CDC, and WHO Global Health Observatory (GHO) APIs.
2. **Processing & NLP Layer**: Articles are processed to determine relevance using an ML classifier. Relevant articles undergo Named Entity Recognition (NER) to extract the disease and location.
3. **Storage Layer**: Processed outbreaks and enriched data are stored in MongoDB.
4. **API Layer**: A Flask-based REST API serves aggregated data, disease profiles, and outbreak statistics.
5. **Presentation Layer**: A React SPA consumes the API to render maps, comparison charts, and alerts.

---

## 5. Backend Implementation

### 5.1 Core Application
The backend is powered by a Flask application (`backend/app.py`). It enforces strict database initialization on startup and configures Cross-Origin Resource Sharing (CORS) to communicate seamlessly with the React frontend.

### 5.2 API Layer (`backend/api/routes.py`)
The RESTful API provides several endpoints designed with robust error handling and response serialization:
- `GET /api/health`: System health check.
- `GET /api/diseases`: Retrieves all registered diseases. It dynamically calculates a `severity` metric (low, medium, high) based on total case counts and historical occurrences.
- `GET /api/diseases/<name>`: Fetches detailed information for a specific disease.
- `GET /api/outbreaks`: Retrieves outbreak records, supporting query parameters for filtering by `region`, `disease`, and `date_from`/`date_to`.
- `GET /api/outbreaks/summary`: Aggregates outbreak data using MongoDB pipelines to return total cases and occurrences grouped by disease.

### 5.3 Data Ingestion & Crawlers (`backend/crawler/spiders/`)
Scrapy spiders form the backbone of the data ingestion pipeline:
- **`who_spider.py` & `cdc_spider.py`**: Scrape RSS feeds and news sections to gather raw text articles regarding global health events.
- **`who_gho_spider.py`**: Integrates with the WHO Global Health Observatory to fetch realistic case count estimates.
- **`disease_api_spider.py`**: Interacts with the disease.sh API for auxiliary data.

### 5.4 Processing Pipeline (`backend/pipeline/`)
The processing pipeline orchestrates the flow of data:
- **`processor.py`**: Acts as the main orchestrator. It reads raw scraped articles, runs them through the NLP relevance classifier, extracts entities, and inserts verified outbreaks into the database.
- **`enricher.py`**: Responsible for enriching extracted outbreak records with historical or real-time case counts.
- **`scheduler.py`**: Manages the recurring execution of spiders and processing jobs (e.g., running every 6 hours).

---

## 6. NLP and Machine Learning Modules

### 6.1 Named Entity Recognition (`backend/nlp/ner.py`)
Entity extraction relies on a hybrid approach combining spaCy and rule-based fallback mechanisms:
- **spaCy PhraseMatcher**: Utilizes `en_core_web_sm` to match disease keywords efficiently.
- **Location Extraction**: Uses spaCy's `GPE` (Geopolitical Entity) labels, subsequently normalized via a comprehensive `LOCATION_MAP` (e.g., mapping "U.S.", "USA" to "United States").
- **Fallback Mechanisms**: Because lightweight models occasionally miss complex hyphenated diseases or certain country names (e.g., "DR Congo", "Ivory Coast"), the system includes a direct substring text-scan fallback to ensure high recall.

### 6.2 Relevance Classification (`backend/nlp/relevance.py` & `train_classifier.py`)
Determining if an article constitutes a genuine outbreak is handled by an ML classifier:
- **Model**: A TF-IDF Vectorizer combined with a Logistic Regression classifier (`classifier.pkl`, `vectorizer.pkl`).
- **Prediction**: The model computes the probability of an article being relevant. A confidence score $\ge 0.5$ classifies the article as an outbreak.
- **Fault Tolerance**: If the model files are missing (e.g., prior to initial training), the system gracefully falls back to a deterministic keyword-matching heuristic (checking for terms like "cases", "deaths", "epidemic"). This ensures the pipeline never crashes during cold starts.

---

## 7. Database & Storage
MongoDB Atlas is utilized for its flexible schema design, accommodating unstructured article data alongside structured outbreak records.
- **Collections**: `raw_articles` (unprocessed text), `outbreaks_v2` (finalized events), and `diseases` (metadata).
- **Connection Management**: `mongo_connection.py` implements a singleton pattern (`get_db`) to prevent connection leaks across Flask routes.

---

## 8. Frontend Implementation
The user interface is built with React 19 and Vite, styled using Tailwind CSS for a modern, responsive design.

### 8.1 Core Pages (`frontend/src/pages/`)
- **`Map.jsx`**: Integrates Leaflet to render a global, interactive map. Outbreaks are plotted as geographical markers, color-coded based on the dynamically calculated severity metric.
- **`Analytics.jsx`**: Utilizes Chart.js to display time-series data and categorical breakdowns of diseases.
- **`Compare.jsx`**: Allows side-by-side comparative analysis of multiple diseases or regions over specified timeframes.
- **`Alerts.jsx`**: Provides an interface for users to subscribe to email alerts for specific regions or diseases (dispatched via SendGrid on the backend).
- **`Search.jsx` & `DiseaseDetail.jsx`**: Facilitate granular exploration of specific pathogens, displaying enriched historical data.

### 8.2 API Integration (`frontend/src/services/`)
All backend communication is abstracted into service modules utilizing `axios`. This ensures centralized error handling, request timeouts, and clean component logic.

---

## 9. Limitations and Future Work
- **Training Data**: The Logistic Regression classifier is currently trained on auto-labeled data. Increasing the volume of manually annotated training samples will improve precision and recall.
- **Data Source Restrictions**: The WHO GHO API currently lacks real-time data for COVID-19 and seasonal influenza. Integrating supplementary APIs for these specific diseases would eliminate gaps in case count reporting.
- **Geocoding**: Country matching currently relies on a static normalization map. Implementing dynamic geocoding could handle unrecognized regions more gracefully.

---

## 10. Conclusion
MediScope successfully demonstrates a fully automated, end-to-end pipeline for global disease surveillance. By synergizing web scraping, NLP-based entity extraction, and Machine Learning relevance classification, it synthesizes vast amounts of unstructured news into an interactive, highly visual, and actionable public health dashboard.
