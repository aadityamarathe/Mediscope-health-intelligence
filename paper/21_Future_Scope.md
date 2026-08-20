# Future Scope and Limitations

While MediScope is a fully functional prototype ready for production, several areas offer opportunities for future enhancement.

## Current Limitations
1. **Model Training Data**: The Logistic Regression classifier is currently trained on auto-labeled data from the `raw_articles` collection. This limits precision. 
2. **GHO API Gaps**: The WHO Global Health Observatory does not provide real-time case counts for COVID-19 or seasonal influenza via its public endpoints, resulting in missing quantitative data for these specific diseases.
3. **Static Geocoding**: The system relies on a static normalization map (`LOCATION_MAP`) to resolve country names to coordinates. If an outbreak occurs in a small province not in the map, it will be skipped.

## Future Improvements

### 1. Advanced NLP (Large Language Models)
- Replace the TF-IDF/Logistic Regression pipeline with a lightweight fine-tuned LLM (like Llama-3 8B or BioBERT). This would allow the system to not only extract the disease and country but also answer complex questions like "How many people were hospitalized?" directly from the text.

### 2. Dynamic Geocoding Integration
- Integrate a third-party geocoding API (e.g., Google Maps API or Mapbox). Instead of relying on a static dictionary, the system could dynamically fetch the exact Latitude/Longitude of a reported province or city, allowing for much more granular map markers (city-level vs country-level).

### 3. Automated Retraining Pipeline
- Implement an active learning loop. When an administrator corrects a false positive on the frontend, the backend should automatically append this to the training dataset and trigger `train_classifier.py` in the background to continuously improve the model.

### 4. Real-time WebSockets
- Currently, the React frontend must refresh or remount to fetch new outbreaks. Implementing WebSockets (e.g., via `Flask-SocketIO`) would allow the backend to push new outbreaks to the frontend map in real-time the moment the Scrapy spider finds them.
