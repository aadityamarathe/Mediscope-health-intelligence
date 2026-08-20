import time

import schedule

from ..crawler import run_all_crawlers
from ..crawler.spiders.who_gho_spider import WHOGHOSpider
from ..nlp.alerts import check_and_send_alerts
from ..pipeline.processor import process_articles


def run_scheduled_jobs():
    try:
        run_all_crawlers()
    except Exception as e:
        print(f"Error during crawling, skipping processing and alerts: {e}")
        return

    try:
        process_articles()
    except Exception as e:
        print(f"Error during article processing, skipping alerts: {e}")
        return

    try:
        check_and_send_alerts()
    except Exception as e:
        print(f"Error during alert check: {e}")

def run_who_spider():
    try:
        spider = WHOGHOSpider()
        spider.run()
    except Exception as e:
        print(f"Error running WHOGHOSpider: {e}")

def start_scheduler():
    schedule.every(6).hours.do(run_scheduled_jobs)
    schedule.every(24).hours.do(run_who_spider)

    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            print(f"Error in scheduler loop: {e}")
        time.sleep(60)


if __name__ == "__main__":
    start_scheduler()
