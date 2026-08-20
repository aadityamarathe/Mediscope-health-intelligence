# Natural Language Processing (NLP) Module

The NLP module (`backend/nlp/ner.py`) is responsible for reading the unstructured text of a news article and accurately extracting two core entities: the **Disease** and the **Location** (Country).

## 1. Core Engine: spaCy
The project uses `spaCy`, an industry-standard open-source NLP library, loading the lightweight `en_core_web_sm` model. This model provides tokenization, part-of-speech tagging, and Named Entity Recognition (NER).

## 2. Disease Extraction
Extracting diseases is challenging because medical terminology varies widely (e.g., "COVID-19", "Coronavirus", "SARS-CoV-2").
- **Phase 1: PhraseMatcher**: MediScope utilizes spaCy's `PhraseMatcher`. A predefined list of `DISEASE_KEYWORDS` is converted into spaCy Doc objects and loaded into the matcher. The matcher scans the article text at the token level, providing extremely fast and accurate hits.
- **Phase 2: Substring Scan Fallback**: PhraseMatcher operates strictly on token boundaries. If an article mentions a "dengue-endemic region", `spaCy` might tokenize it as `["dengue-endemic", "region"]`. The matcher looking for "dengue" will fail. To catch these, MediScope implements a fallback text-scan (`if keyword in text.lower()`) using a `FALLBACK_KEYWORDS` list that bypasses tokenization.
- **Phase 3: Normalization**: Once a keyword is found (e.g., "flu"), it is passed through `DISEASE_MAP` to normalize it to the system standard ("influenza").

## 3. Location (Country) Extraction
Identifying exactly where an outbreak is happening is critical for the map rendering.
- **Phase 1: GPE Recognition**: The script iterates over `doc.ents` (entities found by spaCy's default model). It looks for entities labeled `GPE` (Geopolitical Entity).
- **Phase 2: Normalization**: A `LOCATION_MAP` dictionary translates variations into standard country names. For example, "U.S.", "USA", and "Washington" all map to "United States". "DRC" and "Democratic Republic of the Congo" map to "DR Congo".
- **Phase 3: Known-Country Fallback**: The `en_core_web_sm` model occasionally fails to recognize certain developing nations as GPEs in complex sentences. MediScope maintains a `_FALLBACK_COUNTRY_NAMES` list. If spaCy misses the location, the script does a raw substring scan for these known countries to ensure high recall.

## Algorithm Complexity
- **Time Complexity**: $O(N)$ where $N$ is the length of the text. spaCy processes the document in linear time, and the fallback dictionary scans are also $O(N)$.
- **Space Complexity**: $O(T)$ where $T$ is the number of tokens in the document, required to hold the spaCy `Doc` object in memory.
