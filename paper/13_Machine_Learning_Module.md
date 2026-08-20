# Machine Learning Module

The Machine Learning module (`backend/nlp/relevance.py`) acts as the gatekeeper for the pipeline. Not every article published by the WHO or CDC is about a new outbreak; many are about policy changes, funding, or general health guidelines. The ML module's job is to classify text into `Outbreak (Relevant)` or `Not Outbreak (Irrelevant)`.

## 1. Feature Extraction: TF-IDF
Raw text cannot be fed directly into a machine learning model; it must be converted into numerical features.
- The system uses Scikit-Learn's `TfidfVectorizer`.
- **TF (Term Frequency)**: Measures how frequently a word appears in a document.
- **IDF (Inverse Document Frequency)**: Downweights common words (like "the", "and") and upweights rare words that carry significant meaning (like "epidemic", "quarantine").
- The vectorizer transforms the article text into a sparse matrix of TF-IDF features.

## 2. Classification: Logistic Regression
A Logistic Regression algorithm was chosen for this binary classification task due to its efficiency and interpretability in text-classification tasks.
- **Training**: The model is trained (via `train_classifier.py`) on a dataset composed of historical articles stored in `raw_articles`.
- **Prediction**: When a new article arrives, `relevance.py` vectorizes it and passes it to the `_classifier.predict_proba()` method.
- **Confidence Score**: The model outputs a probability array. The probability assigned to the "Outbreak" class (Class 1) is used as the `confidence` score.
- **Threshold**: The system utilizes a threshold of `0.5`. If the confidence score is $\ge 0.5$, the article is marked as relevant and passed to the NLP extraction phase.

## 3. Graceful Fallback Strategy
Machine Learning workflows in production environments must be fault-tolerant. If MediScope is cloned to a new server, the trained `.pkl` files (`classifier.pkl` and `vectorizer.pkl`) will not exist in the `backend/nlp/models/` directory, causing a critical crash on the first pipeline run.

To prevent this, `relevance.py` implements a fallback architecture:
1. It attempts to load the `.pkl` files using `joblib.load()`.
2. If an `Exception` occurs (File Not Found, or corrupt pickle file), the `_classifier` is set to `None`.
3. When `is_relevant_article()` is called, it checks if the classifier exists. If it does not, it silently routes the text to a deterministic `_keyword_relevance()` function.
4. This fallback function checks the text against a hardcoded list of keywords ("outbreak", "cases", "deaths"). If it finds matches, it assigns an artificial confidence score and allows the pipeline to continue.

This ensures the system is highly resilient and functional immediately after cloning, before any training commands are run.
