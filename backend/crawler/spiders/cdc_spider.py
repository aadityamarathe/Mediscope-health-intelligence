from datetime import datetime, timezone

import scrapy
from pymongo.errors import DuplicateKeyError

from ...database.mongo_connection import get_db


class CDCHealthSpider(scrapy.Spider):
    name = "cdc_health"
    allowed_domains = ["cdc.gov", "tools.cdc.gov"]
    start_urls = ["https://www.cdc.gov/mmwr/rss/mmwr.xml"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = get_db()
        self.item_count = 0

    def parse(self, response):
        for item in response.xpath("//item"):
            article = {
                "source": "CDC",
                "credibility": "verified",
                "title": (item.xpath("title/text()").get() or "").strip(),
                "content": (item.xpath("description/text()").get() or "").strip(),
                "url": (item.xpath("link/text()").get() or "").strip(),
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
                print(f"CDC spider error: {exc}")

    def closed(self, reason):
        print(f"CDCHealthSpider scraped {self.item_count} items. Reason: {reason}")
