# Bug Fixes and Improvements

During the development and testing of MediScope, several critical bugs were identified and resolved. Additionally, significant architectural improvements were made to transition the project from a prototype to a production-ready state.

## 1. The spaCy Fallback Fix
- **Bug Found**: The NLP module (`ner.py`) was failing to extract locations for developing nations (e.g., "DR Congo", "Ivory Coast") and was failing to identify hyphenated diseases (e.g., "COVID-19").
- **Root Cause**: The `en_core_web_sm` spaCy model is lightweight and lacks context for certain global regions. Furthermore, `PhraseMatcher` operates on strict token boundaries; it tokenizes "COVID-19" as `["COVID", "-", "19"]`, failing to match the single keyword "COVID-19".
- **Fix Applied**: Implemented Phase 3 Fallback logic. After spaCy runs, the script performs a direct substring scan (`if keyword in text.lower()`) against a list of known problem countries and hyphenated diseases.
- **Impact**: Increased recall significantly. Outbreaks in Africa and the Middle East are now accurately plotted on the map.

## 2. ML Cold-Start Crash
- **Bug Found**: The pipeline would crash with a `FileNotFoundError` when deployed to a new environment because `classifier.pkl` was not present in the git repository (it is in `.gitignore`).
- **Root Cause**: `relevance.py` hard-required the ML models to load at import time.
- **Fix Applied**: Wrapped the `joblib.load()` calls in a `try...except` block. If it fails, the classifier is set to `None`. The `is_relevant_article()` function was rewritten to check for `None` and fall back to a legacy keyword-matching heuristic.
- **Impact**: The system is now fault-tolerant and can run immediately upon cloning without manual ML training.

## 3. Artificial Duplication Fix
- **Bug Found**: The `outbreaks` collection was filling up with duplicate records.
- **Root Cause**: The WHO often updates the same article multiple times. The pipeline was reading the updated article and inserting a brand new outbreak record with `datetime.now()`, causing multiple identical markers on the map.
- **Fix Applied**: Created the `outbreaks_v2` collection with a Compound Index on `{ disease: 1, country: 1, date: -1 }`. The `processor.py` was updated to check for existing records within the same 24-hour window before inserting.
- **Impact**: Cleaned up the map UI and reduced database storage costs.

## Legacy and Unused Files
Through continuous refactoring, some files were rendered obsolete but were kept in the repository for historical auditing:
- **`backend/pipeline/migrate_outbreaks_v2.py`**: A one-off script used to migrate data from the old buggy `outbreaks` collection to the cleanly indexed `outbreaks_v2` collection. It is no longer executed.
- **`backend/pipeline/analyze_dupes.py`**: A diagnostic script used to prove the existence of the duplication bug. It is strictly legacy.
- **`backend/dry_run.py` & `revised_dry_run.py`**: Scripts used for local testing of the NLP pipeline without hitting the MongoDB database. They are not part of the production pipeline.
