# Crawlers and Data Ingestion

MediScope's intelligence relies entirely on the quality and freshness of its data. To ensure a continuous stream of public health information, the system utilizes the Scrapy framework to build highly customized web spiders.

## 1. WHO RSS Spider (`who_spider.py`)
- **Purpose**: Ingests the official World Health Organization Disease Outbreak News (DONs) RSS feed.
- **Mechanism**: The spider targets the XML feed URL. It uses XPath selectors to iterate over every `<item>` node.
- **Extracted Fields**: Title, Description (the actual article summary), Link, and Publication Date.
- **Storage**: Inserts the extracted JSON dictionary directly into the MongoDB `raw_articles` collection with `processed` set to `False`.

## 2. CDC RSS Spider (`cdc_spider.py`)
- **Purpose**: Ingests updates from the Centers for Disease Control and Prevention.
- **Mechanism**: Similar to the WHO spider, it parses XML feeds. However, CDC feeds often have different namespace formatting, requiring specific XPath adjustments to extract the correct text nodes.

## 3. WHO GHO API Integration (`who_gho_spider.py`)
- **Purpose**: Retrieves quantitative data. While news articles provide qualitative alerts ("A new outbreak of Cholera in Yemen..."), they often lack exact, verified numbers. The Global Health Observatory (GHO) API provides these historical and current case counts.
- **Mechanism**: This script makes HTTP GET requests to the official WHO ATHENA API endpoints (e.g., `https://ghoapi.azureedge.net/api/`).
- **Processing**: The API returns highly nested JSON data. The script parses this, mapping specific GHO indicator codes to MediScope's internal disease names.
- **Storage**: Caches these case counts in the database so the `enricher.py` script can rapidly append them to new outbreak records without making network calls during the main pipeline execution.

## 4. disease.sh API Spider (`disease_api_spider.py`)
- **Purpose**: Acts as a supplementary data source, specifically useful for real-time dashboard data (like COVID-19 or Influenza metrics) which WHO GHO sometimes delays.
- **Mechanism**: Queries `https://disease.sh/v3/covid-19/all` and related endpoints.

## Spider Orchestration
Scrapy spiders are usually run via the CLI (`scrapy crawl who_spider`). In MediScope, they are programmatically invoked using Python's `subprocess` or `scrapy.crawler.CrawlerProcess` from within the `scheduler.py` script, allowing them to run on a background thread every 6 hours automatically.
