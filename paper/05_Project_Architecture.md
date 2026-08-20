# Project Architecture

MediScope implements a modern, decoupled, service-oriented architecture. The system is split into two primary environments: a Python-based backend handling data ingestion, ML/NLP processing, and API routing, and a React-based frontend handling data visualization and user interaction.

## Overall Architecture Diagram

```ascii
+-----------------------------------------------------------------------------------+
|                                 External Data Sources                             |
|  [WHO RSS]     [CDC RSS]     [WHO GHO API]     [disease.sh API]                   |
+------+-------------+---------------+-------------------+--------------------------+
       |             |               |                   |
       v             v               v                   v
+-----------------------------------------------------------------------------------+
|                                 Backend: Data Ingestion                           |
|                         (Scrapy Spiders run via scheduler.py)                     |
+------------------------------------+----------------------------------------------+
                                     |
                                     v
                           +-------------------+
                           | MongoDB:          |
                           | raw_articles      |
                           +--------+----------+
                                    |
                                    v
+-----------------------------------------------------------------------------------+
|                                 Backend: NLP & ML Pipeline                        |
|                                                                                   |
|  1. processor.py reads raw_articles                                               |
|  2. relevance.py (ML) predicts outbreak probability (TF-IDF + Logistic Reg.)      |
|  3. ner.py extracts Disease & Location (spaCy + Fallbacks)                        |
|  4. enricher.py adds WHO case counts                                              |
+------------------------------------+----------------------------------------------+
                                     |
                                     v
                           +-------------------+
                           | MongoDB:          |
                           | outbreaks_v2      |
                           | diseases          |
                           +--------+----------+
                                    |
                                    v
+-----------------------------------------------------------------------------------+
|                                 Backend: API Layer                                |
|                              Flask (api/routes.py)                                |
|  - /api/outbreaks    - /api/diseases    - /api/alerts/subscribe                   |
+------------------------------------+----------------------------------------------+
                                     | (JSON over HTTP/REST)
                                     v
+-----------------------------------------------------------------------------------+
|                                 Frontend: Presentation                            |
|                               (React + Vite + Tailwind)                           |
|                                                                                   |
|  [Map.jsx (Leaflet)]   [Analytics.jsx (Chart.js)]   [Alerts.jsx]                  |
+-----------------------------------------------------------------------------------+
```

## Architectural Design Decisions

### 1. Decoupled Client-Server Model
The backend (Flask) and frontend (React) are completely decoupled. They communicate exclusively via RESTful JSON APIs. 
- **Advantage**: Allows the frontend and backend to be scaled, deployed, and tested independently.

### 2. Scheduled Batch Processing
Instead of processing data on-the-fly when a user requests it, MediScope uses a cron-like scheduler (`backend/pipeline/scheduler.py`) to scrape and process data in the background every 6 hours.
- **Advantage**: API endpoints remain lightning-fast (usually under 50ms response times) because they only query pre-computed data from MongoDB.

### 3. Graceful Degradation in ML Pipeline
The NLP and ML module is designed to never crash the pipeline. If the trained ML model files (`classifier.pkl`, `vectorizer.pkl`) are not found, `relevance.py` falls back to a deterministic keyword-matching heuristic.
- **Advantage**: Ensures system stability during "cold starts" or fresh deployments before the model has been trained.

### 4. NoSQL Database (MongoDB)
Unstructured data (news articles) and structured data (extracted outbreaks) are stored together in MongoDB Atlas.
- **Advantage**: High flexibility. As new fields (like `severity` or `case_count_source`) are added to outbreaks, the database schema does not require complex migrations.
