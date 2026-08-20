# Database Design

MediScope utilizes MongoDB Atlas, a NoSQL database, due to the unstructured nature of raw news articles and the evolving schema requirements of outbreak records.

## 1. Collection: `raw_articles`
**Purpose**: Acts as the staging area for data ingested by the Scrapy crawlers. It holds unstructured HTML/text before it is processed by the NLP pipeline.
**Fields**:
- `_id` (ObjectId): Primary Key.
- `title` (String, Required): Headline of the article.
- `description` (String, Required): Body text or summary.
- `link` (String, Required): Original URL.
- `source` (String, Required): Origin (e.g., "WHO", "CDC").
- `pubDate` (Date, Required): Publication timestamp.
- `processed` (Boolean): Flag indicating if the pipeline has analyzed this article (Default: `false`).

**Indexes**: 
- Unique index on `link` to prevent scraping the same article twice.
- Index on `processed` to quickly query unanalyzed articles during the batch processing job.

**CRUD Interactions**:
- **Writes**: `backend/crawler/spiders/*.py` insert new documents.
- **Reads**: `backend/pipeline/processor.py` fetches documents where `processed: false`.
- **Updates**: `backend/pipeline/processor.py` sets `processed: true` after NLP analysis.

## 2. Collection: `outbreaks_v2`
**Purpose**: Stores the finalized, verified outbreak records that the frontend consumes.
**Fields**:
- `_id` (ObjectId): Primary Key.
- `disease` (String, Required): Normalized disease name (e.g., "covid-19").
- `country` (String, Required): Normalized country name (e.g., "United States").
- `lat` (Float, Required): Latitude for map plotting.
- `lng` (Float, Required): Longitude for map plotting.
- `case_count` (Integer): Enriched quantitative data.
- `date` (Date, Required): Date the outbreak was reported.
- `source_article` (String): URL linking back to the raw article.

**Indexes**:
- Compound Index on `{ disease: 1, country: 1, date: -1 }` to optimize the API's filtering queries and prevent inserting exact duplicate outbreaks on the same day.

**CRUD Interactions**:
- **Writes**: `backend/pipeline/processor.py` inserts new records after successful NLP extraction and enrichment.
- **Reads**: `backend/api/routes.py` queries this collection to serve the `/api/outbreaks` and `/api/outbreaks/summary` endpoints.

## 3. Collection: `diseases`
**Purpose**: Stores reference metadata for known pathogens.
**Fields**:
- `_id` (ObjectId): Primary Key.
- `name` (String, Required): Disease name.
- `category` (String): e.g., "Viral", "Bacterial".
- `description` (String): Overview of the disease.
- `symptoms` (Array of Strings): List of common symptoms.

**Indexes**:
- Unique index on `name`.

**CRUD Interactions**:
- **Writes**: Populated once on startup by `backend/database/seed_diseases.py`.
- **Reads**: `backend/api/routes.py` queries this to serve the `/api/diseases` and `/api/diseases/<name>` endpoints.
