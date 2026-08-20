# Team Contribution

The MediScope project was developed collaboratively by a team of four, with responsibilities divided based on domain expertise while ensuring seamless integration across the stack.

## Member 1: Backend & API Developer
- **Responsibilities**: Designed and implemented the Flask application architecture, API routing, and server deployment configurations.
- **Modules Handled**: `app.py`, `api/routes.py`, `utils/severity.py`.
- **Technologies Used**: Python, Flask, Flask-CORS.
- **Testing/Documentation**: Wrote API documentation (Postman/Swagger) and manually tested endpoint error handling (`_handle_errors` decorator).

## Member 2: NLP & Machine Learning Developer
- **Responsibilities**: Engineered the core "brain" of the application, responsible for text classification and entity extraction.
- **Modules Handled**: `nlp/ner.py`, `nlp/relevance.py`, `nlp/train_classifier.py`.
- **Technologies Used**: spaCy (`en_core_web_sm`), Scikit-Learn (TF-IDF, Logistic Regression), Joblib.
- **Testing/Documentation**: Documented the fallback heuristics and evaluated the ML model's precision/recall on test datasets.

## Member 3: Data Pipeline & Database Engineer
- **Responsibilities**: Built the autonomous web scrapers, orchestrated the processing pipeline, and designed the MongoDB schemas.
- **Modules Handled**: `crawler/spiders/*.py`, `pipeline/processor.py`, `database/mongo_connection.py`.
- **Technologies Used**: Scrapy, PyMongo, MongoDB Atlas, XPath/Regex.
- **Testing/Documentation**: Optimized database queries by adding Compound Indexes and documented the data flow diagrams.

## Member 4: Frontend & Visualization Developer
- **Responsibilities**: Created the interactive Single Page Application, ensuring a responsive and intuitive user experience.
- **Modules Handled**: Entire `frontend/src/` directory (React pages, components, services).
- **Technologies Used**: React 19, Vite, Tailwind CSS, Leaflet.js, Chart.js, Axios.
- **Testing/Documentation**: Conducted UI/UX testing across mobile and desktop viewports and documented the component hierarchy.
