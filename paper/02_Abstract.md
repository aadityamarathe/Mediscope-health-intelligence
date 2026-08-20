# Abstract

MediScope is a robust, automated disease outbreak surveillance system engineered to detect, classify, and visualize emerging global health threats in near real-time. Public health monitoring typically relies on highly latent or paywalled commercial data feeds. MediScope democratizes access to this vital intelligence by automating the ingestion and analysis of public health news.

By continuously scraping RSS feeds from authoritative sources such as the World Health Organization (WHO) and the Centers for Disease Control and Prevention (CDC), the system aggregates unstructured health data. It employs a hybrid Natural Language Processing (NLP) pipeline—combining spaCy's `PhraseMatcher` with deterministic regex and text-scan fallbacks—to accurately extract crucial entities, namely the specific disease and the geographical location of the outbreak.

To ensure high data relevance, MediScope integrates a Machine Learning module utilizing Term Frequency-Inverse Document Frequency (TF-IDF) and Logistic Regression to classify whether an article truly reports an outbreak, discarding noise. Once classified and extracted, the system enriches the outbreak records with quantitative case counts retrieved from the WHO Global Health Observatory (GHO) API.

The final synthesized data is served via a Flask RESTful API and visualized on a React-based frontend dashboard. The dashboard features an interactive Leaflet map, Chart.js analytics, comparative tools, and an automated email alert subscription service. The resulting platform provides epidemiologists, researchers, and public health officials with an intuitive, low-latency, and actionable overview of the global disease landscape.
