# File-By-File Explanation

This chapter provides an exhaustive breakdown of the most critical files in the MediScope repository. It is designed as a reference guide for new developers or for Viva preparation.

## 1. `backend/app.py`
- **Purpose**: The entry point for the Flask backend.
- **Why it exists**: To configure the server, initialize the database, apply CORS policies, and start the application loop.
- **Main Functions**: `app.run()`
- **Dependencies**: `flask`, `flask_cors`, `mongo_connection.py`, `init_db.py`, `routes.py`.
- **Files that call it**: Executed directly via `python -m backend.app`.
- **Files it calls**: `api/routes.py` (registers routes), `database/init_db.py` (ensures DB is seeded).
- **What happens if removed**: The API server cannot start. The frontend will have no data source.
- **Viva Question**: "Why do you call `initialize_database()` inside `app.py` instead of running it manually?" *Answer: To ensure the database schema and required initial data (like disease metadata) are always present before the server accepts any incoming traffic, preventing runtime 500 errors.*

## 2. `backend/api/routes.py`
- **Purpose**: Defines all REST API endpoints.
- **Why it exists**: To handle HTTP requests from the React frontend, query MongoDB, and return formatted JSON.
- **Main Functions**: `get_outbreaks()`, `get_diseases()`, `get_outbreak_summary()`.
- **Database Interactions**: Heavily queries `outbreaks_v2` and `diseases` collections.
- **Libraries Used**: `flask.request`, `flask.jsonify`, `bson.ObjectId`, `datetime`.
- **What happens if removed**: The server runs, but all frontend requests will return 404 Not Found.
- **Viva Question**: "How do you handle MongoDB `ObjectId` types when returning JSON?" *Answer: A custom `_serialize_document` function iterates over the MongoDB response and casts `ObjectId` and `datetime` objects to strings before passing them to `jsonify`.*

## 3. `backend/pipeline/processor.py`
- **Purpose**: The main orchestrator of the data pipeline.
- **Why it exists**: To connect the raw data scraped by spiders to the NLP modules, and finally save it to the verified database.
- **Main Functions**: `process_pending_articles()`, `_process_single_article()`.
- **Dependencies**: `backend/nlp/relevance.py`, `backend/nlp/ner.py`, `backend/pipeline/enricher.py`.
- **What happens if removed**: The crawlers will still save raw text, but it will never be analyzed, and the map will never update.

## 4. `backend/nlp/ner.py`
- **Purpose**: Extracts entities (Disease and Location) from text.
- **Why it exists**: News articles are unstructured. We need structured `disease` and `country` fields for the database.
- **Main Functions**: `extract_entities(text)`.
- **Algorithms Used**: spaCy PhraseMatcher (Token matching), Substring scanning (Regex-like string matching).
- **Libraries Used**: `spacy`.
- **What happens if removed**: The pipeline won't know *what* the outbreak is or *where* it is happening.

## 5. `backend/nlp/relevance.py`
- **Purpose**: Classifies articles as relevant (outbreak) or irrelevant.
- **Why it exists**: To filter out general health news, policy updates, and noise.
- **Main Functions**: `is_relevant_article(text)`.
- **Algorithms Used**: TF-IDF (Feature Extraction), Logistic Regression (Classification).
- **Libraries Used**: `scikit-learn`, `joblib`.
- **Viva Question**: "What happens if your `.pkl` model files are missing?" *Answer: The code catches the `FileNotFoundError` and assigns the classifier to `None`. The `is_relevant_article()` function checks for this and gracefully falls back to a deterministic keyword-matching function.*

## 6. `frontend/src/pages/Map.jsx`
- **Purpose**: Renders the global interactive map.
- **Main Hooks**: `useEffect` (fetches `/api/outbreaks`), `useState` (manages filters).
- **Libraries Used**: `react-leaflet`, `leaflet`.
- **API Interactions**: Calls `GET /api/outbreaks` on mount and whenever a filter state changes.
- **What happens if removed**: The core visual feature of the dashboard is lost.
