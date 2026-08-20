from datetime import datetime, timedelta, timezone

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from ..config import SENDGRID_API_KEY
from ..database.mongo_connection import get_db


def _get_recent_outbreaks(db, window_start):
    # Ensure window_start is naive UTC to match outbreaks schema
    naive_window = window_start.replace(tzinfo=None)
    return db["outbreaks_v2"].find({"updated_at": {"$gte": naive_window}})


def _get_subscribers_for_region(db, region):
    if not region:
        return []
    return db["subscribers"].find({"region": region})


def _ensure_alert_log_index(db):
    db["alerts_log"].create_index(
        [("email", 1), ("outbreak_id", 1)],
        unique=True,
        name="alerts_log_email_outbreak_unique",
    )


def _alert_already_sent(db, email, outbreak_id):
    return db["alerts_log"].find_one({"email": email, "outbreak_id": outbreak_id}) is not None


def _build_alert_email(email, disease, country, outbreak_date, case_count, source_url):
    formatted_date = outbreak_date.astimezone(timezone.utc).isoformat() if outbreak_date else "unknown date"
    body = (
        f"A new {disease} outbreak has been reported in {country} on {formatted_date}.\n"
        f"Reported cases: {case_count}\n"
        f"Source: {source_url}\n\n"
        "Stay informed at MediScope.\n\n"
        "DISCLAIMER: This is for informational purposes only. Not medical advice."
    )

    return Mail(
        from_email="alerts@mediscope.local",
        to_emails=email,
        subject=f"New outbreak alert: {disease} in {country}",
        plain_text_content=body,
    )


def _send_alert(email, disease, country, outbreak_date, case_count, source_url):
    if not SENDGRID_API_KEY:
        raise ValueError("SENDGRID_API_KEY is not set.")

    message = _build_alert_email(
        email=email,
        disease=disease,
        country=country,
        outbreak_date=outbreak_date,
        case_count=case_count,
        source_url=source_url,
    )
    # SendGridAPIClient(SENDGRID_API_KEY).send(message)


def check_and_send_alerts():
    db = get_db()
    _ensure_alert_log_index(db)

    now = datetime.now(timezone.utc)
    window_start = now - timedelta(hours=6)

    outbreaks = list(_get_recent_outbreaks(db, window_start))
    print(f"[DEBUG] Found {len(outbreaks)} outbreaks")

    for outbreak in outbreaks:
        disease = outbreak.get("disease", "unknown disease")
        country = outbreak.get("country") or outbreak.get("region") or "unknown region"
        outbreak_date = outbreak.get("date")
        case_count = outbreak.get("case_count", "unknown")
        source_url = outbreak.get("source_url", "")

        print(f"[DEBUG] Checking subscribers for country: {country}")
        subscribers = list(_get_subscribers_for_region(db, country))
        print(f"[DEBUG] Found {len(subscribers)} subscribers")

        for subscriber in subscribers:
            email = subscriber.get("email")
            if not email:
                continue

            if _alert_already_sent(db, email, outbreak["_id"]):
                continue

            print(f"[DEBUG] Sending alert to {email}")
            try:
                # _send_alert(...)
                print(f"[ALERT] (SIMULATED) Email to {email}")
                print(f"Disease: {disease}, Country: {country}, Cases: {case_count}")
                db["alerts_log"].insert_one(
                    {
                        "email": email,
                        "outbreak_id": outbreak["_id"],
                        "sent_at": datetime.now(timezone.utc),
                    }
                )
                print(f"[ALERT] Sent to {email} for {disease} in {country}")
            except Exception as e:
                print(f"[ERROR] Failed to send email to {email}: {e}")

if __name__ == "__main__":
    check_and_send_alerts()
