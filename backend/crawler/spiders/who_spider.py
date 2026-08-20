import json
from datetime import datetime, timezone

import scrapy
from pymongo.errors import DuplicateKeyError

from ...database.mongo_connection import get_db


class WHOHealthSpider(scrapy.Spider):
    name = "who_health"
    allowed_domains = ["who.int"]
    start_urls = ["https://www.who.int/api/news/diseaseoutbreaknews"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = get_db()
        self.item_count = 0

    def parse(self, response):
        try:
            data = json.loads(response.body)
            items = data.get("value", [])
        except json.JSONDecodeError:
            print("WHO spider error: Failed to parse JSON response")
            return

        for item in items:
            title = item.get("Title", "")
            overview = item.get("Overview", "")
            # Clean up the overview HTML using Scrapy's Selector if needed, or store raw.
            # Storing raw is fine, or we can just extract text. Let's do raw for now, 
            # the downstream pipeline might handle HTML, but let's strip tags just in case:
            content_selector = scrapy.Selector(text=overview)
            content_text = " ".join(content_selector.xpath("//text()").getall()).strip()
            
            url_name = item.get("UrlName", "")
            url = f"https://www.who.int/emergencies/disease-outbreak-news/item/{url_name}" if url_name else ""

            article = {
                "source": "WHO",
                "credibility": "verified",
                "title": title.strip(),
                "content": content_text,
                "url": url,
                "crawled_at": datetime.now(timezone.utc),
                "processed": False,
            }

            if not article["url"]:
                continue

            try:
                self.db["raw_articles"].insert_one(article)
                self.item_count += 1
            except DuplicateKeyError:
                continue
            except Exception as exc:
                print(f"WHO spider error: {exc}")

    def closed(self, reason):
        print(f"WHOHealthSpider scraped {self.item_count} items. Reason: {reason}")
