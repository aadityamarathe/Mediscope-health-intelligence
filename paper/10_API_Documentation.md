# API Documentation

The MediScope backend exposes a RESTful JSON API. All endpoints are prefixed with `/api` and return a standardized envelope format:
```json
{
  "success": true,
  "data": { ... },
  "message": null
}
```

## 1. Health Check
- **Endpoint**: `/api/health`
- **Method**: `GET`
- **Purpose**: Verifies the Flask server is running and reachable.
- **Request Parameters**: None
- **Response**: `{ "success": true, "data": { "status": "ok" } }`
- **Status Codes**: 200 OK

## 2. Get All Outbreaks
- **Endpoint**: `/api/outbreaks`
- **Method**: `GET`
- **Purpose**: Retrieves a list of outbreak records, formatted for map rendering.
- **Request Parameters** (Query String):
  - `region` (Optional): Filter by country/region.
  - `disease` (Optional): Filter by specific disease.
  - `date_from` (Optional, ISO8601): Start date.
  - `date_to` (Optional, ISO8601): End date.
- **Backend Function**: `get_outbreaks()` in `routes.py`
- **Collections Used**: `outbreaks_v2`
- **Frontend Pages Using It**: `Map.jsx`
- **Sample Request**: `GET /api/outbreaks?disease=cholera`

## 3. Get Outbreak Summary
- **Endpoint**: `/api/outbreaks/summary`
- **Method**: `GET`
- **Purpose**: Retrieves aggregated statistics (total cases, occurrences) grouped by disease.
- **Backend Function**: `get_outbreak_summary()` in `routes.py`
- **Collections Used**: `outbreaks_v2` (using MongoDB Aggregate pipeline)
- **Frontend Pages Using It**: `Analytics.jsx`, `Compare.jsx`

## 4. Get All Diseases
- **Endpoint**: `/api/diseases`
- **Method**: `GET`
- **Purpose**: Retrieves all disease metadata, calculating a dynamic `severity` score on-the-fly based on historical outbreak data.
- **Request Parameters**:
  - `severity` (Optional): Filter by "low", "medium", or "high".
- **Backend Function**: `get_diseases()` in `routes.py`
- **Collections Used**: `diseases`, `outbreaks_v2`
- **Frontend Pages Using It**: Sidebar filters, `Search.jsx`

## 5. Get Specific Disease
- **Endpoint**: `/api/diseases/<name>`
- **Method**: `GET`
- **Purpose**: Retrieves detailed metadata for a single disease.
- **Backend Function**: `get_disease(name)` in `routes.py`
- **Collections Used**: `diseases`
- **Status Codes**: 200 OK, 404 Not Found (if disease doesn't exist).
- **Frontend Pages Using It**: `DiseaseDetail.jsx`

## Error Responses
If an internal server error or database timeout occurs on any endpoint, the custom `_handle_errors` decorator catches it and returns:
```json
{
  "success": false,
  "data": null,
  "message": "Error description..."
}
```
With HTTP Status Code `500 Internal Server Error`.
