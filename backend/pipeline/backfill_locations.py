"""
backfill_locations.py
─────────────────────
One-time backfill script that re-processes all existing outbreaks with
country="unknown" or null coordinates using the improved extraction logic.

Usage:
    python -m backend.pipeline.backfill_locations
"""
import sys
import re
from datetime import datetime, timezone

# Allow running as a script
if __name__ == "__main__":
    sys.path.insert(0, ".")

from backend.database.mongo_connection import get_db
from backend.nlp.ner import extract_entities
from backend.pipeline.processor import (
    COUNTRY_COORDS,
    _normalize_country,
    _pick_primary_country,
    _build_analysis_text,
)


def backfill():
    db = get_db()

    # Find all outbreaks with unknown country or null coordinates
    unknown_outbreaks = list(db["outbreaks"].find({
        "$or": [
            {"country": "unknown"},
            {"lat": None},
            {"lng": None},
        ]
    }))

    print(f"Found {len(unknown_outbreaks)} outbreaks to backfill")

    fixed_count = 0
    still_unknown = 0

    for outbreak in unknown_outbreaks:
        source_url = outbreak.get("source_url", "")
        disease = outbreak.get("disease", "")

        # Try to find the original raw article
        article = None
        if source_url:
            article = db["raw_articles"].find_one({"url": source_url})

        analysis_text = ""
        location_candidates = []

        if article:
            analysis_text = _build_analysis_text(article)
            entities = extract_entities(analysis_text)
            location_candidates = entities.get("locations", [])
        else:
            # No article found — try to extract from disease + country context
            # or from the outbreak's own source_url
            analysis_text = f"{disease} outbreak {source_url}"

        # Try improved country extraction
        new_country = _pick_primary_country(analysis_text, location_candidates)

        if new_country and new_country != "unknown":
            lat, lng = COUNTRY_COORDS.get(new_country, (None, None))

            update = {
                "country": new_country,
                "lat": lat,
                "lng": lng,
                "updated_at": datetime.now(timezone.utc),
            }

            db["outbreaks"].update_one(
                {"_id": outbreak["_id"]},
                {"$set": update}
            )

            fixed_count += 1
            print(f"  FIXED: {disease} | {outbreak.get('country')} -> {new_country} ({lat}, {lng})")
        else:
            still_unknown += 1

    print(f"\n{'='*55}")
    print(f"  Backfill complete")
    print(f"  Fixed:         {fixed_count}")
    print(f"  Still unknown: {still_unknown}")
    print(f"{'='*55}")

    return fixed_count


if __name__ == "__main__":
    backfill()
