# Backend Implementation

The backend of MediScope is a robust, Python-based system responsible for scheduling data ingestion, executing complex NLP/ML pipelines, and serving data via a REST API.

## 1. Flask Application (`app.py`)
The entry point of the backend is `backend/app.py`. 
- **Initialization**: Upon startup, it immediately calls `get_db()` and `initialize_database()` to ensure the MongoDB connection is alive and necessary collections/indexes exist before accepting traffic.
- **CORS**: It uses `flask_cors` to allow cross-origin requests from the React frontend running on `http://localhost:5173`.
- **Routing**: It registers all endpoints imported from `backend/api/routes.py`.

## 2. API Layer (`api/routes.py`)
The API layer is designed with strict error handling and serialization rules.
- **`_handle_errors` Decorator**: A custom Python decorator wraps every route. If any Exception occurs (e.g., database timeout, parsing error), the decorator catches it and returns a standardized `{ "success": False, "message": "error details" }` JSON payload with a 500 status code. This prevents the Flask server from crashing and allows the frontend to display graceful error messages.
- **`_serialize_document`**: MongoDB returns `ObjectId` and `datetime` objects which cannot be natively serialized to JSON. This utility recursively converts dates to ISO 8601 strings and ObjectIds to strings.

## 3. The Processing Pipeline (`pipeline/processor.py`)
This is the heart of the backend. It acts as the bridge between raw crawled data and the API.
- **Workflow**:
  1. Fetches unprocessed documents from the `raw_articles` collection.
  2. Passes the article title/description to `relevance.py`.
  3. If relevant, passes the text to `ner.py`.
  4. If a disease and location are found, it checks for existing duplicates in `outbreaks_v2` (to avoid inserting the same news story twice).
  5. It calls `enricher.py` to attach WHO case counts.
  6. It inserts the final structured document into `outbreaks_v2` and marks the raw article as `processed: true`.

## 4. Scheduling (`pipeline/scheduler.py`)
To ensure the dashboard reflects the latest global events without manual intervention, `scheduler.py` uses libraries (like `schedule` or `APScheduler`) to run the Scrapy crawlers and the `processor.py` script on a recurring interval (e.g., every 6 hours).

## 5. Configuration & Environment (`config.py`)
Sensitive data and environment-specific settings are kept out of the source code.
- `config.py` uses `python-dotenv` to load the `MONGODB_URI` from a `.env` file.
- It also centralizes configuration constants, ensuring that if a database name or API key changes, it only needs to be updated in one place.

## 6. Error Handling Strategy
Throughout the backend, defensive programming is employed:
- **Database Fallbacks**: If MongoDB cannot be reached, the connection utility throws a descriptive error rather than hanging.
- **NLP Fallbacks**: If the ML model is deleted, `relevance.py` silently falls back to keyword matching so processing continues uninterrupted.
- **Data Integrity**: The API validates coordinate pairs (latitude/longitude) before returning map data to the frontend, ensuring Leaflet doesn't crash on the client side due to malformed data.
