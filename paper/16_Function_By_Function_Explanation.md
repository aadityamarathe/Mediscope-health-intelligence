# Function-By-Function Explanation

This chapter details the internal logic of the most critical functions across the codebase.

## 1. `_handle_errors(route_function)` [backend/api/routes.py]
- **Purpose**: A Python decorator that wraps API endpoints to catch unhandled exceptions.
- **Parameters**: `route_function` (The function being decorated).
- **Return Value**: A JSON response wrapper.
- **Internal Logic**: Wraps the execution of the route in a `try...except Exception as exc:` block. If an error occurs, it returns `{"success": False, "message": str(exc)}` with an HTTP 500 status.
- **Time Complexity**: $O(1)$ (Overhead of the wrapper).
- **Viva Question**: "Why use a decorator for error handling instead of try-catch blocks in every route?" *Answer: To adhere to the DRY (Don't Repeat Yourself) principle. It keeps route logic clean and ensures consistent API error formatting across the entire application.*

## 2. `is_relevant_article(text)` [backend/nlp/relevance.py]
- **Purpose**: Determines if a text describes a disease outbreak.
- **Parameters**: `text` (String).
- **Return Value**: `{"is_relevant": boolean, "confidence": float}`.
- **Internal Logic**: Checks if `_classifier` is loaded. If yes, it calls `_model_relevance(text)`. If no, it calls `_keyword_relevance(text)`.
- **Algorithm**: In ML mode, it transforms the text via TF-IDF and predicts the probability of Class 1 (Outbreak) using Logistic Regression. In keyword mode, it counts occurrences of specific words and calculates a mock confidence score.
- **Time Complexity**: $O(N)$ where $N$ is text length (TF-IDF transformation is roughly linear).

## 3. `extract_entities(text)` [backend/nlp/ner.py]
- **Purpose**: Finds the disease and country in a news article.
- **Parameters**: `text` (String).
- **Return Value**: `{"diseases": list, "locations": list}`.
- **Internal Logic**: 
  1. Passes text to `_nlp(text)` to generate a spaCy Doc.
  2. Iterates over `doc.ents` looking for `label_ == "GPE"`. Maps found GPEs using `LOCATION_MAP`.
  3. Iterates over `_matcher(doc)` to find exact phrase matches for diseases.
  4. Runs fallback substring scans for known countries and hyphenated diseases that spaCy misses.
- **Time Complexity**: $O(N)$ (spaCy processing).
- **Called by**: `processor.py`.

## 4. `calculate_disease_severity(total_cases, occurrences)` [backend/utils/severity.py]
- **Purpose**: Dynamically assigns a risk level to a disease.
- **Parameters**: `total_cases` (Int), `occurrences` (Int).
- **Return Value**: String (`"low"`, `"medium"`, or `"high"`).
- **Internal Logic**: Uses a weighted scoring mechanism. High total cases (e.g., > 10,000) or high frequency of outbreak reports (e.g., > 5 in the last month) push the score into the "high" threshold.
- **Calls**: None. Pure function.

## 5. `fetchData()` [frontend/src/pages/Map.jsx]
- **Purpose**: Retrieves filtered outbreak data from the backend to render on the map.
- **Internal Logic**: Triggered by a `useEffect` hook. Constructs a query string based on the current `filters` state (e.g., `?disease=cholera&region=africa`). Calls `axios.get()`. On success, calls `setOutbreaks(response.data)`. On failure, sets the local error state to display a UI warning.
