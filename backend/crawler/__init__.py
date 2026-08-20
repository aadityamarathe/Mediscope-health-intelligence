import subprocess
import sys

from .spiders.disease_api_spider import DiseaseAPISpider
from ..database.init_db import initialize_database


SCRAPY_SETTINGS = {
    "LOG_LEVEL": "ERROR",
    "TWISTED_REACTOR": "twisted.internet.selectreactor.SelectReactor",
}


def _run_scrapy_spider(module_path, class_name):
    command = [
        sys.executable,
        "-c",
        (
            "from scrapy.crawler import CrawlerProcess; "
            f"from {module_path} import {class_name}; "
            f"process = CrawlerProcess(settings={SCRAPY_SETTINGS!r}); "
            f"process.crawl({class_name}); "
            "process.start()"
        ),
    ]
    try:
        result = subprocess.run(command, check=False, timeout=900)
        if result.returncode != 0:
            print(f"{class_name} failed with exit code {result.returncode}.")
    except subprocess.TimeoutExpired:
        print(f"{class_name} timed out after 900 seconds.")


def run_all_crawlers():
    initialize_database()
    _run_scrapy_spider("backend.crawler.spiders.who_spider", "WHOHealthSpider")
    _run_scrapy_spider("backend.crawler.spiders.cdc_spider", "CDCHealthSpider")

    try:
        DiseaseAPISpider().run()
    except Exception as exc:
        print(f"DiseaseAPISpider runner error: {exc}")
