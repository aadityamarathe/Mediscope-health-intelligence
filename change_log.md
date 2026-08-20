# Change Log: implementationPaper.txt

### Section 1: SYSTEM OVERVIEW
**Old Text**:
```text
  6. Stores all data in MongoDB Atlas (collections: raw_articles,
     processed_articles, diseases, outbreaks, subscribers, disease_stats,
     alerts_log).
```
**New Text**:
```text
  6. Stores all data in MongoDB Atlas (collections: raw_articles,
     processed_articles, diseases, outbreaks_v2, subscribers, disease_stats,
     alerts_log).
```
**Reason for change**: The `outbreaks` collection was migrated to `outbreaks_v2` in the codebase.

---

### Section 1: SYSTEM OVERVIEW
**Old Text**:
```text
  8. Displays results on a React + Vite frontend with an interactive Leaflet
     map, Chart.js trend visualizations, disease comparison tables, symptom
     search, and email alert subscription.
```
**New Text**:
```text
  8. Displays results on a React + Vite frontend with an interactive Leaflet
     map, a dedicated Analytics dashboard, disease comparison tables, symptom
     search, and email alert subscription.
```
**Reason for change**: The Map Trend visualizations were removed from the user interface and a new dedicated Analytics dashboard was added.

---

### Section 2: ARCHITECTURE — TEXT-BASED DATA FLOW DIAGRAM
**Old Text**:
```text
│              ┌─────────────────┐           ┌─────────────────┐               │
│              │ raw_articles    │           │ outbreaks        │               │
│              │ (MongoDB)       │           │ (MongoDB, direct)│               │
│              └────────┬────────┘           └─────────────────┘               │
```
**New Text**:
```text
│              ┌─────────────────┐           ┌─────────────────┐               │
│              │ raw_articles    │           │ outbreaks_v2     │               │
│              │ (MongoDB)       │           │ (MongoDB, deduplicated)│      │
│              └────────┬────────┘           └─────────────────┘               │
```
**Reason for change**: Architecture was updated to write deduplicated records to `outbreaks_v2`.

---

### Section 2: ARCHITECTURE — TEXT-BASED DATA FLOW DIAGRAM
**Old Text**:
```text
│  ┌──────────────────────────────────────────────┐                            │
│  │  React Frontend (Vite, port 5173)             │                            │
│  │  ├── Home        → /api/outbreaks/summary     │                            │
│  │  ├── Map         → /api/outbreaks/map         │                            │
│  │  │                  /api/outbreaks/trends      │                            │
│  │  ├── DiseaseDetail → /api/diseases/<name>     │                            │
│  │  ├── Compare     → /api/compare?d1=X&d2=Y    │                            │
│  │  ├── Search      → /api/search?symptoms=X    │                            │
│  │  └── Alerts      → /api/alerts/subscribe      │                            │
│  └──────────────────────────────────────────────┘                            │
```
**New Text**:
```text
│  ┌──────────────────────────────────────────────┐                            │
│  │  React Frontend (Vite, port 5173)             │                            │
│  │  ├── Home        → /api/outbreaks/summary     │                            │
│  │  ├── Map         → /api/outbreaks/map         │                            │
│  │  ├── DiseaseDetail → /api/diseases/<name>     │                            │
│  │  ├── Compare     → /api/compare?d1=X&d2=Y    │                            │
│  │  ├── Search      → /api/search?symptoms=X    │                            │
│  │  ├── Alerts      → /api/alerts/subscribe      │                            │
│  │  └── Analytics   → /api/analytics/activity    │                            │
│  └──────────────────────────────────────────────┘                            │
```
**Reason for change**: Trends line removed from the Map node; new Analytics node added pointing to `/api/analytics/activity`.

---

### Section 4.3: backend/api/routes.py
**Old Text**:
```text
Endpoints: (see Section 6 for full reference)
  GET  /api/health
  GET  /api/diseases
  GET  /api/diseases/<name>
  GET  /api/outbreaks
  GET  /api/outbreaks/summary
  GET  /api/outbreaks/map
  GET  /api/outbreaks/trends
  GET  /api/search
  GET  /api/compare
  GET  /api/export/csv
  POST /api/alerts/subscribe
```
**New Text**:
```text
Endpoints: (see Section 6 for full reference)
  GET  /api/health
  GET  /api/diseases
  GET  /api/diseases/<name>
  GET  /api/outbreaks
  GET  /api/outbreaks/summary
  GET  /api/outbreaks/map
  GET  /api/outbreaks/trends (Deprecated)
  GET  /api/search
  GET  /api/compare
  GET  /api/export/csv
  POST /api/alerts/subscribe
  GET  /api/analytics/activity
```
**Reason for change**: Endpoint list was updated to mark `trends` as deprecated (as it still exists in code) and added the new `analytics/activity` endpoint.

---

### Section 4.7: backend/crawler/spiders/disease_api_spider.py
**Old Text**:
```text
Purpose: Non-Scrapy crawler that fetches COVID-19 case data per country from
  the disease.sh REST API and inserts records directly into the outbreaks
  collection (bypasses the NLP pipeline).
```
**New Text**:
```text
Purpose: Non-Scrapy crawler that fetches COVID-19 case data per country from
  the disease.sh REST API and inserts records directly into the outbreaks_v2
  collection (bypasses the NLP pipeline), utilizing source-aware survivor logic
  to deduplicate records by disease and country.
```
**Reason for change**: Spider was synchronized with `outbreaks_v2` and now uses source-aware survivor logic to deduplicate records.

---

### Section 4.10: backend/database/init_db.py
**Old Text**:
```text
Collections Created:
  - raw_articles
  - processed_articles
  - diseases
  - outbreaks
  - subscribers
```
**New Text**:
```text
Collections Created:
  - raw_articles
  - processed_articles
  - diseases
  - outbreaks (Note: This is a legacy collection name in init_db.py; active pipelines write to outbreaks_v2)
  - subscribers
```
**Reason for change**: `init_db.py` was never updated to index `outbreaks_v2`. A note was added reflecting the codebase reality without fabricating non-existent code updates.

---

### Section 4.18: backend/pipeline/processor.py
**Old Text**:
```text
       f. Calculate severity
       g. Upsert to outbreaks (keyed on disease + country + date)
    6. Print statistics summary
```
**New Text**:
```text
       f. Calculate severity
       g. Upsert to outbreaks_v2 (keyed on disease + country, using source-aware survivor logic to keep the most reliable case counts)
    6. Print statistics summary
```
**Reason for change**: Processor was updated to target `outbreaks_v2` deduplicated strictly by disease+country, and utilizes source-aware survivor logic.

---

### Section 4.19: backend/pipeline/enricher.py
**Old Text**:
```text
Strategy:
  1. Try exact match: disease + country (case-insensitive regex on country)
  2. Fallback: find highest case_count globally for that disease
  3. Return int or None
```
**New Text**:
```text
Strategy:
  1. Try exact match: disease + country (case-insensitive regex on country)
  2. Removed global fallback to prevent unsafe data enrichment; returns None if exact country match fails
  3. Return int or None
```
**Reason for change**: The global fallback (assigning highest case counts to unrelated countries) was removed.

---

### Section 4B.2: frontend/src/App.jsx
**Old Text**:
```text
Routes:
  /          → Home
  /map       → MapPage
  /disease/* → DiseaseDetail (wildcard route for disease name in path)
  /compare   → Compare
  /search    → Search
  /alerts    → Alerts
All routes are nested under Layout
```
**New Text**:
```text
Routes:
  /          → Home
  /map       → MapPage
  /disease/* → DiseaseDetail (wildcard route for disease name in path)
  /compare   → Compare
  /search    → Search
  /alerts    → Alerts
  /analytics → Analytics
All routes are nested under Layout
```
**Reason for change**: The `/analytics` route was added to `App.jsx`.

---

### Section 4B.4: frontend/src/components/Navbar.jsx
**Old Text**:
```text
Purpose: Navigation bar with links to Home, Map, Compare, Search, Alerts.
```
**New Text**:
```text
Purpose: Navigation bar with links to Home, Map, Compare, Search, Alerts, Analytics.
```
**Reason for change**: The Analytics link was added to the navigation bar component.

---

### Section 4B.9: frontend/src/pages/Map.jsx
**Old Text**:
```text
Trend Chart Section:
  - Dropdown to select disease (populated from /api/outbreaks via
    fetchOutbreakDiseases helper)
  - Line chart (Chart.js) showing case count over time for selected disease
  - Fetches /api/outbreaks/trends?disease=X on selection change

State Management: useState + useEffect
APIs Consumed:
  - GET /api/outbreaks/map
  - GET /api/outbreaks (for disease list)
  - GET /api/outbreaks/trends?disease=X
```
**New Text**:
```text
Trend Chart Section (Hidden from UI via feature toggle):
  - Dropdown to select disease
  - Line chart (Chart.js) logic remains in code but is disabled from rendering.
  - Fetches /api/outbreaks/trends?disease=X on selection change (still executes)

State Management: useState + useEffect
APIs Consumed:
  - GET /api/outbreaks/map
  - GET /api/outbreaks (for disease list)
  - GET /api/outbreaks/trends?disease=X (legacy)
```
**Reason for change**: Reflects that the Trend section is hidden via `{false && (...)}` but still exists in code.

---

### Section 5: DATABASE SCHEMA
**Old Text**:
```text
COLLECTION: outbreaks
─────────────────────
Field                 Type        Description
disease               string      Normalized disease name (INDEX)
country               string      Country name (INDEX)
region                string      Region/country (used by disease_api_spider)
lat                   float       Latitude
lng                   float       Longitude
location              object      GeoJSON Point {type, coordinates} (2DSPHERE INDEX)
date                  datetime    Outbreak date (INDEX)
case_count            int         Number of cases
case_count_estimated  boolean     True if case_count was not extracted from text
case_count_source     string      "extracted" | "who_gho" | "unavailable"
severity              string      "low" | "medium" | "high"
source                string      "WHO" | "CDC" | "disease.sh"
source_url            string      URL of source article/API
```
**New Text**:
```text
COLLECTION: outbreaks_v2
─────────────────────
Field                 Type        Description
disease               string      Normalized disease name (INDEX)
country               string      Country name (INDEX)
lat                   float       Latitude
lng                   float       Longitude
location              object      GeoJSON Point {type, coordinates} (2DSPHERE INDEX)
date                  datetime    Outbreak date
case_count            int         Number of cases
case_count_estimated  boolean     True if case_count was not extracted from text
case_count_source     string      "extracted" | "who_gho" | "missing" | "disease.sh"
severity              string      "low" | "medium" | "high"
source                string      "WHO" | "CDC" | "disease.sh"
source_url            string      URL of source article/API
created_at            datetime    UTC timestamp
updated_at            datetime    UTC timestamp
```
**Reason for change**: Schema was entirely replaced with `outbreaks_v2`, showcasing removed indexing on `date`, loss of `region` field, added timestamps, and updated tracking parameters.

---

### Section 6: API REFERENCE
**Old Text**:
```text
────────────────────────────────────────────────────────────────────────────────
GET /api/outbreaks/trends
────────────────────────────────────────────────────────────────────────────────
Purpose: Case count time series for a specific disease
Query Params:
  - disease (REQUIRED): Disease name (case-insensitive)
Response Data: Array of {date: "YYYY-MM-DD", case_count: int}
Sorted by date ascending
Status: 400 if disease param missing
```
**New Text**:
```text
────────────────────────────────────────────────────────────────────────────────
GET /api/outbreaks/trends (Deprecated)
────────────────────────────────────────────────────────────────────────────────
Purpose: Case count time series for a specific disease (Currently hidden in UI)
Query Params:
  - disease (REQUIRED): Disease name (case-insensitive)
Response Data: Array of {date: "YYYY-MM-DD", case_count: int}
Sorted by date ascending
Status: 400 if disease param missing

────────────────────────────────────────────────────────────────────────────────
GET /api/analytics/activity
────────────────────────────────────────────────────────────────────────────────
Purpose: Outbreak activity analytics
Response Data: Object containing arrays for articles_over_time, top_diseases,
  reports_by_source, and top_countries.
Status: 200 on success
```
**Reason for change**: Annotated `trends` route as deprecated and documented the new `analytics/activity` API.

---

### Section 7: DATA PIPELINE FLOW
**Old Text**:
```text
  1c. DiseaseAPISpider fetches disease.sh → outbreaks (direct, COVID-19 only)
...
  2i. Case Count Enrichment (if no count extracted):
      - enricher.py → disease_stats lookup (country-specific, then global max)
      - Records source as "who_gho" or "unavailable"
...
  2k. Upsert to outbreaks collection (key: disease + country + date)
```
**New Text**:
```text
  1c. DiseaseAPISpider fetches disease.sh → outbreaks_v2 (direct, COVID-19 only)
...
  2i. Case Count Enrichment (if no count extracted):
      - enricher.py → disease_stats lookup (country-specific, no global fallback)
      - Records source as "who_gho" or "missing"
...
  2k. Upsert to outbreaks_v2 collection (key: disease + country, applying source-aware survivor logic for updates)
```
**Reason for change**: Outlined shifts regarding deduplicated collection target, loss of fallback, and integration of logic gates.

---

### Section 10: OPEN QUESTIONS FOR THE AUTHOR
**Old Text**:
```text
 10. COVID-19 data path: DiseaseAPISpider writes directly to outbreaks
     (bypassing NLP pipeline). Is this intentional because COVID data from
     disease.sh is already structured, or should it go through the pipeline?
```
**New Text**:
```text
 10. COVID-19 data path: DiseaseAPISpider writes directly to outbreaks_v2
     (bypassing NLP pipeline). Is this intentional because COVID data from
     disease.sh is already structured, or should it go through the pipeline?
```
**Reason for change**: Updated collection reference to accurately reflect current codebase behavior.
