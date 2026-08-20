import csv
import io
import re
from datetime import datetime, timezone
from functools import wraps

from bson import ObjectId
from flask import Response, request, jsonify

from ..database.mongo_connection import get_db
from ..utils.severity import calculate_disease_severity

EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

def _response(success, data=None, message=None, status=200):
    return (
        jsonify(
            {
                "success": success,
                "data": data,
                "message": message,
            }
        ),
        status,
    )

def _handle_errors(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        try:
            return route_function(*args, **kwargs)
        except Exception as exc:
            return _response(False, message=str(exc), status=500)

    return wrapper

def _serialize_value(value):
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize_value(item) for key, item in value.items()}
    return value

def _serialize_document(document):
    if document is None:
        return None
    return {key: _serialize_value(value) for key, value in document.items() if key != "_id"}

def _is_valid_coordinate_pair(lat, lng):
    if lat is None or lng is None:
        return False

    try:
        lat_value = float(lat)
        lng_value = float(lng)
    except (TypeError, ValueError):
        return False

    return -90 <= lat_value <= 90 and -180 <= lng_value <= 180 and not (lat_value == 0.0 and lng_value == 0.0)

def _build_map_outbreak(document, severity="low"):
    disease = (document.get("disease") or "").strip()
    country = (document.get("country") or "Unknown").strip() or "Unknown"
    lat = document.get("lat")
    lng = document.get("lng")

    if not disease or disease.lower() == "unknown disease":
        return None
    if not _is_valid_coordinate_pair(lat, lng):
        return None

    return {
        "disease": disease,
        "country": country,
        "lat": float(lat),
        "lng": float(lng),
        "case_count": int(document.get("case_count") or 0),
        "severity": severity,
        "date": str(document.get("date")),
        "source": document.get("source", ""),
    }

def _parse_date(date_string):
    if not date_string:
        return None

    cleaned = date_string.strip()
    if not cleaned:
        return None

    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"

    parsed = datetime.fromisoformat(cleaned)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)

def _build_outbreak_query(args):
    query = {}

    region = args.get("region")
    disease = args.get("disease")
    date_from = _parse_date(args.get("date_from"))
    date_to = _parse_date(args.get("date_to"))

    if region:
        query["region"] = region
    if disease:
        query["disease"] = disease
    if date_from or date_to:
        query["date"] = {}
        if date_from:
            query["date"]["$gte"] = date_from
        if date_to:
            query["date"]["$lte"] = date_to

    return query

def _fetch_disease_by_name(name):
    return get_db()["diseases"].find_one(
        {"name": {"$regex": f"^{re.escape(name)}$", "$options": "i"}}
    )

def _resolve_outbreak_severity(disease_name):
    db = get_db()
    pipeline = [
        {"$match": {"disease": disease_name.strip().lower()}},
        {
            "$group": {
                "_id": "$disease",
                "total_cases": {"$sum": "$case_count"},
                "occurrences": {"$sum": 1},
            }
        },
    ]

    result = list(db["outbreaks_v2"].aggregate(pipeline))
    if not result:
        return "low"

    return calculate_disease_severity(
        result[0].get("total_cases", 0),
        result[0].get("occurrences", 0)
    )

def register_routes(app):

    @app.route("/api/health")
    def health():
        return {
            "success": True,
            "data": {
                "status": "ok"
            }
        }

    @app.route("/api/diseases")
    @_handle_errors
    def get_diseases():
        db = get_db()
        
        # 1. Pre-calculate all disease severities for consistency
        pipeline = [
            {
                "$group": {
                    "_id": "$disease",
                    "total_cases": {"$sum": "$case_count"},
                    "occurrences": {"$sum": 1},
                }
            }
        ]
        
        disease_stats_map = {}
        for item in db["outbreaks_v2"].aggregate(pipeline):
            d_name = (item.get("_id") or "").strip().lower()
            if d_name:
                disease_stats_map[d_name] = calculate_disease_severity(
                    item.get("total_cases", 0),
                    item.get("occurrences", 0)
                )

        # 2. Fetch all diseases and override severity field
        req_severity = request.args.get("severity", "").lower()
        
        all_diseases = []
        for doc in db["diseases"].find({}):
            serialized = _serialize_document(doc)
            d_name = (serialized.get("name") or "").strip().lower()
            
            # Map dynamic severity
            calc_severity = disease_stats_map.get(d_name, "low")
            serialized["severity"] = calc_severity
            
            # Filter if requested
            if not req_severity or calc_severity == req_severity:
                all_diseases.append(serialized)

        return _response(True, data=all_diseases)

    @app.route("/api/diseases/<path:name>")
    @_handle_errors
    def get_disease(name):
        disease = _fetch_disease_by_name(name)
        if disease is None:
            return _response(False, data=None, message="Disease not found.", status=404)

        serialized = _serialize_document(disease)
        serialized["name"] = (serialized.get("name") or name).strip().lower()
        serialized["severity"] = _resolve_outbreak_severity(serialized["name"])

        return _response(True, data=serialized)

    @app.route("/api/outbreaks")
    @_handle_errors
    def get_outbreaks():
        query = _build_outbreak_query(request.args)
        outbreaks = [
            _serialize_document(item)
            for item in get_db()["outbreaks_v2"].find(query).limit(100)
        ]
        return _response(True, data=outbreaks)

    @app.route("/api/outbreaks/summary", methods=["GET"])
    @_handle_errors
    def get_outbreak_summary():
        db = get_db()

        pipeline = [
            {
                "$group": {
                    "_id": "$disease",
                    "total_cases": {"$sum": "$case_count"},
                    "occurrences": {"$sum": 1},
                }
            },
            {
                "$project": {
                    "disease": "$_id",
                    "total_cases": 1,
                    "occurrences": 1,
                    "_id": 0,
                }
            },
            {
                "$sort": {"total_cases": -1}
            },
        ]

        results = []
        for item in db["outbreaks_v2"].aggregate(pipeline):
            results.append(
                {
                    "disease": item.get("disease"),
                    "total_cases": item.get("total_cases", 0),
                    "occurrences": item.get("occurrences", 0),
                    "severity": calculate_disease_severity(
                        item.get("total_cases", 0),
                        item.get("occurrences", 0)
                    ),
                }
            )

        return jsonify({
            "success": True,
            "data": results
        })

    @app.route("/api/outbreaks/map")
    @_handle_errors
    def get_outbreak_map():
        db = get_db()
        
        # 1. Fetch all outbreaks with coordinates
        outbreaks = list(
            db["outbreaks_v2"].find(
                {
                    "lat": {"$ne": None},
                    "lng": {"$ne": None},
                }
            )
        )

        result = []
        for outbreak in outbreaks:
            severity = outbreak.get("severity", "low")
            
            item = _build_map_outbreak(outbreak, severity=severity)
            if item is not None:
                result.append(item)

        return _response(True, data=result)

    @app.route("/api/outbreaks/trends")
    @_handle_errors
    def get_outbreak_trends():
        disease = (request.args.get("disease") or "").strip().lower()
        if not disease:
            return _response(False, data=None, message="disease is required.", status=400)

        pipeline = [
            {"$match": {"disease": disease}},
            {
                "$group": {
                    "_id": {
                        "$dateToString": {"format": "%Y-%m-%d", "date": "$date"}
                    },
                    "case_count": {"$sum": "$case_count"},
                }
            },
            {"$sort": {"_id": 1}},
        ]

        trends = [
            {"date": item["_id"], "case_count": int(item["case_count"])}
            for item in get_db()["outbreaks_v2"].aggregate(pipeline)
        ]
        return _response(True, data=trends)

    @app.route("/api/search")
    @_handle_errors
    def search_diseases():
        symptoms_param = request.args.get("symptoms", "")
        symptoms = [item.strip() for item in symptoms_param.split(",") if item.strip()]

        diseases = []
        if symptoms:
            diseases = [
                _serialize_document(item)
                for item in get_db()["diseases"].find({"symptoms": {"$in": symptoms}})
            ]

        return _response(True, data=diseases)

    def _get_disease_outbreak_stats(db, disease_name):
        normalized_name = (disease_name or "").strip().lower()
        total_cases = 0
        recorded_outbreaks = 0

        if not normalized_name:
            return {
                "total_cases": 0,
                "recorded_outbreaks": 0,
            }

        for outbreak in db["outbreaks_v2"].find({"disease": normalized_name}):
            total_cases += int(outbreak.get("case_count") or 0)
            recorded_outbreaks += 1

        return {
            "total_cases": total_cases,
            "recorded_outbreaks": recorded_outbreaks,
        }

    def _pick_primary_symptom_profile(symptoms):
        symptom_categories = {
            "respiratory": {"cough", "shortness of breath", "sore throat", "runny nose", "respiratory"},
            "digestive": {"diarrhea", "vomiting", "abdominal pain", "nausea", "dehydration", "appetite"},
            "skin": {"rash", "swollen lymph nodes", "jaundice", "red eyes"},
            "systemic": {"fever", "fatigue", "chills", "sweating", "headache", "weight loss", "muscle pain", "muscle aches", "weakness"},
        }

        counts = {category: 0 for category in symptom_categories}
        for symptom in symptoms:
            lowered = (symptom or "").strip().lower()
            for category, keywords in symptom_categories.items():
                if any(keyword in lowered for keyword in keywords):
                    counts[category] += 1

        best_category = ""
        best_count = 0
        for category, count in counts.items():
            if count > best_count:
                best_category = category
                best_count = count

        return best_category if best_count else ""

    def _build_highlight_list(values, limit=2):
        cleaned = []
        for value in values or []:
            text = (value or "").strip()
            if text and text not in cleaned:
                cleaned.append(text)
            if len(cleaned) >= limit:
                break
        return ", ".join(cleaned)

    def _generate_compare_insights(first, second):
        insights = []
        first_name = first.get("name", "The first disease")
        second_name = second.get("name", "The second disease")

        first_transmission = (first.get("transmission") or "").strip()
        second_transmission = (second.get("transmission") or "").strip()
        if first_transmission and second_transmission and first_transmission.lower() != second_transmission.lower():
            insights.append(
                f"{first_name} spreads via {first_transmission.lower()}, while {second_name} spreads via {second_transmission.lower()}."
            )

        first_profile = _pick_primary_symptom_profile(first.get("symptoms") or [])
        second_profile = _pick_primary_symptom_profile(second.get("symptoms") or [])
        if first_profile and second_profile and first_profile != second_profile:
            insights.append(
                f"{first_name} mainly shows {first_profile}-related symptoms, while {second_name} mainly shows {second_profile}-related symptoms."
            )

        first_symptoms = _build_highlight_list(first.get("symptoms") or [])
        second_symptoms = _build_highlight_list(second.get("symptoms") or [])
        if first_symptoms and second_symptoms and first_symptoms.lower() != second_symptoms.lower():
            insights.append(
                f"{first_name} more often highlights symptoms such as {first_symptoms.lower()}, while {second_name} highlights {second_symptoms.lower()}."
            )

        first_prevention = (first.get("prevention") or "").strip()
        second_prevention = (second.get("prevention") or "").strip()
        if first_prevention and second_prevention and first_prevention.lower() != second_prevention.lower():
            insights.append(
                f"Prevention guidance differs: {first_name} emphasizes {first_prevention.lower()}, while {second_name} emphasizes {second_prevention.lower()}."
            )

        return insights

    @app.route("/api/compare")
    @_handle_errors
    def compare_diseases():
        db = get_db()
        disease_one = request.args.get("d1")
        disease_two = request.args.get("d2")

        if not disease_one or not disease_two:
            return _response(False, data=None, message="d1 and d2 are required.", status=400)

        first = _fetch_disease_by_name(disease_one)
        second = _fetch_disease_by_name(disease_two)

        if first is None or second is None:
            return _response(False, data=None, message="One or more diseases not found.", status=404)

        d1 = _serialize_document(first)
        d2 = _serialize_document(second)

        d1_stats = _get_disease_outbreak_stats(db, d1.get("name"))
        d1["total_cases"] = d1_stats["total_cases"]
        d1["recorded_outbreaks"] = d1_stats["recorded_outbreaks"]

        d2_stats = _get_disease_outbreak_stats(db, d2.get("name"))
        d2["total_cases"] = d2_stats["total_cases"]
        d2["recorded_outbreaks"] = d2_stats["recorded_outbreaks"]

        key_differences = _generate_compare_insights(d1, d2)

        return _response(
            True,
            data={
                "d1": d1,
                "d2": d2,
                "key_differences": key_differences,
            },
        )

    @app.route("/api/export/csv")
    @_handle_errors
    def export_outbreaks_csv():
        query = _build_outbreak_query(request.args)
        projection = {
            "_id": 0,
            "disease": 1,
            "country": 1,
            "region": 1,
            "lat": 1,
            "lng": 1,
            "date": 1,
            "case_count": 1,
            "source": 1,
            "source_url": 1,
        }
        outbreaks = [_serialize_document(item) for item in get_db()["outbreaks_v2"].find(query, projection)]

        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "disease",
                "country",
                "region",
                "lat",
                "lng",
                "date",
                "case_count",
                "source",
                "source_url",
            ],
        )
        writer.writeheader()
        writer.writerows(outbreaks)

        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=outbreaks.csv"},
        )

    @app.route("/api/alerts/subscribe", methods=["POST"])
    @_handle_errors
    def subscribe_to_alerts():
        payload = request.get_json(silent=True) or {}
        email = (payload.get("email") or "").strip()
        region = (payload.get("region") or "").strip()

        if not EMAIL_REGEX.match(email):
            return _response(False, data=None, message="Invalid email address.", status=400)

        if not region:
            return _response(False, data=None, message="Region is required.", status=400)

        subscribers = get_db()["subscribers"]
        existing = subscribers.find_one({"email": email, "region": region})
        if existing is not None:
            return _response(False, data=None, message="Subscriber already exists.", status=409)

        subscribers.insert_one(
            {
                "email": email,
                "region": region,
                "subscribed_at": datetime.now(timezone.utc),
            }
        )
        return _response(True, data={"email": email, "region": region}, message="Subscription created.", status=201)

    @app.route("/api/analytics/activity", methods=["GET"])
    @_handle_errors
    def get_analytics_activity():
        db = get_db()
        
        # 1. Articles Over Time (from raw_articles)
        # Assuming crawled_at or published_date exists. We will group by crawled_at formatted as YYYY-MM-DD
        articles_pipeline = [
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": {"$ifNull": ["$crawled_at", "$published_date", datetime.utcnow()]}
                        }
                    },
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        articles_over_time = [{"date": item["_id"], "count": item["count"]} for item in db["raw_articles"].aggregate(articles_pipeline) if item["_id"]]

        # 2. Top Diseases (from outbreaks_v2)
        top_diseases_pipeline = [
            {"$group": {"_id": "$disease", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        top_diseases = [{"disease": item["_id"], "count": item["count"]} for item in db["outbreaks_v2"].aggregate(top_diseases_pipeline) if item["_id"]]

        # 3. Reports by Source (from outbreaks_v2)
        source_pipeline = [
            {"$group": {"_id": "$source", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        reports_by_source = [{"source": item["_id"] or "Unknown", "count": item["count"]} for item in db["outbreaks_v2"].aggregate(source_pipeline)]

        # 4. Top Countries (Disease Diversity)
        countries_pipeline = [
            {"$match": {"country": {"$ne": "unknown"}}},
            {"$group": {"_id": "$country", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        top_countries = [{"country": item["_id"], "count": item["count"]} for item in db["outbreaks_v2"].aggregate(countries_pipeline) if item["_id"]]

        return _response(True, data={
            "articles_over_time": articles_over_time,
            "top_diseases": top_diseases,
            "reports_by_source": reports_by_source,
            "top_countries": top_countries
        })
