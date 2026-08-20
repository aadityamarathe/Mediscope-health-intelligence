# Viva Preparation Notes

This chapter is designed to help the team confidently defend the project during the final year Viva/Review.

## 1. Quick Pitches

### The 2-Minute Explanation
"MediScope is an automated disease outbreak monitoring system. It solves the problem of delayed public health information by automatically scraping news from the WHO and CDC. We built a machine learning pipeline that filters out irrelevant news using TF-IDF and Logistic Regression. Then, our NLP module uses spaCy to extract the exact disease and location. This data is enriched with real case counts and displayed on a React-based interactive map, giving epidemiologists a real-time, low-latency dashboard of global health threats."

### The 5-Minute Explanation
*(Add the following to the 2-minute pitch)*: 
"Architecturally, we decoupled the system into a Flask backend and a React frontend. The backend handles a scheduled cron job that runs Scrapy spiders. The scraped text is saved to MongoDB. Our processor script then runs the ML and NLP algorithms. A major technical challenge we solved was edge cases in NLP—spaCy often missed hyphenated diseases or developing nations, so we implemented a hybrid regex fallback system. For the database, we used MongoDB Atlas because the unstructured nature of news articles fits NoSQL perfectly. Finally, the frontend uses Leaflet for mapping and Chart.js for analytics, pulling data via RESTful APIs."

## 2. Common & Tricky Viva Questions

**Q: Why use MongoDB instead of SQL (MySQL/PostgreSQL)?**
**A:** "We ingest unstructured XML/RSS data from various sources (WHO, CDC). The schema of a news article or an API response from disease.sh can change. NoSQL provides the flexibility to store this semi-structured data without constant migrations. Furthermore, MongoDB handles JSON-like documents natively, which maps perfectly to our React/Flask JSON API flow."

**Q: Why did you use Logistic Regression for text classification instead of a Neural Network or LLM?**
**A:** "Logistic Regression combined with TF-IDF is highly efficient, interpretable, and requires significantly less compute power and training data than deep learning models. For a binary classification task (Outbreak vs Not Outbreak), it provides excellent accuracy without the latency or hosting costs associated with large neural networks."

**Q: How do you prevent the same news article from being added to the map multiple times?**
**A:** "We handle deduplication at two levels. First, the `raw_articles` collection has a unique index on the article URL. Second, in the `outbreaks_v2` collection, we created a Compound Index on `[disease, country, date]`. Before inserting, the pipeline checks if an outbreak for that specific disease and country was already reported today."

**Q: What happens if your Machine Learning model crashes or the `.pkl` files are deleted?**
**A:** "We engineered a graceful fallback mechanism. If the `joblib.load()` fails to find the model files, the system catches the exception and routes the text to a deterministic keyword-matching heuristic. This ensures the pipeline never halts in production."

**Q: How is the 'Severity' of a disease calculated?**
**A:** "It is calculated dynamically. We use a MongoDB aggregation pipeline to sum up the total historical cases and occurrences of a disease. High case counts or high frequencies push the score from Low to Medium or High. We compute this on-the-fly in the `/api/diseases` endpoint."

**Q: Can you explain how the NLP PhraseMatcher works?**
**A:** "spaCy's PhraseMatcher works at the token level. We provide it a list of disease keywords, which it converts into Doc objects. It then scans the article tokens in $O(N)$ time, which is much faster than running hundreds of complex Regex patterns. However, we supplement it with substring scans to catch hyphenated words that tokenization splits up."
