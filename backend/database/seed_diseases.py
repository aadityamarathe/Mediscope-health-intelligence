from datetime import datetime, timezone
from pathlib import Path
import sys


if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from .mongo_connection import get_db


outbreaks = [
    {
        "disease": "Dengue",
        "country": "India",
        "case_count": 120000,
        "date": datetime.utcnow(),
        "lat": 20.5937,
        "lng": 78.9629,
        "severity": "high",
        "source": "WHO",
        "source_url": "https://www.who.int"
    },
    {
        "disease": "Cholera",
        "country": "Yemen",
        "case_count": 50000,
        "date": datetime.utcnow(),
        "lat": 15.5527,
        "lng": 48.5164,
        "severity": "medium",
        "source": "WHO",
        "source_url": "https://www.who.int"
    }
]
DISEASES = [
    {
        "name": "dengue",
        "symptoms": ["high fever", "headache", "joint pain", "muscle pain", "rash"],
        "transmission": "Spread through the bite of infected Aedes mosquitoes.",
        "prevention": "Prevent mosquito bites and remove standing water around homes.",
        "severity": "medium",
    },
    {
        "name": "cholera",
        "symptoms": ["watery diarrhea", "vomiting", "dehydration", "muscle cramps"],
        "transmission": "Spread through contaminated water or food.",
        "prevention": "Use safe water, eat properly prepared food, and wash hands often.",
        "severity": "high",
    },
    {
        "name": "malaria",
        "symptoms": ["fever", "chills", "sweating", "headache", "fatigue"],
        "transmission": "Spread through the bite of infected Anopheles mosquitoes.",
        "prevention": "Use insecticide-treated nets, repellents, and mosquito control measures.",
        "severity": "high",
    },
    {
        "name": "tuberculosis",
        "symptoms": ["persistent cough", "fever", "night sweats", "weight loss"],
        "transmission": "Spread through the air when a person with active TB coughs or sneezes.",
        "prevention": "Improve ventilation, seek early treatment, and reduce close exposure to active TB.",
        "severity": "high",
    },
    {
        "name": "covid-19",
        "symptoms": ["fever", "cough", "fatigue", "sore throat", "shortness of breath"],
        "transmission": "Spread mainly through respiratory droplets and aerosols.",
        "prevention": "Stay up to date with vaccination, improve ventilation, and avoid close contact when sick.",
        "severity": "medium",
    },
    {
        "name": "influenza",
        "symptoms": ["fever", "cough", "sore throat", "muscle aches", "fatigue"],
        "transmission": "Spread through respiratory droplets and close contact.",
        "prevention": "Get vaccinated yearly, wash hands, and stay home when ill.",
        "severity": "medium",
    },
    {
        "name": "hepatitis b",
        "symptoms": ["fatigue", "nausea", "abdominal pain", "dark urine", "jaundice"],
        "transmission": "Spread through contact with infected blood or body fluids.",
        "prevention": "Get vaccinated and avoid sharing needles or personal items that may carry blood.",
        "severity": "high",
    },
    {
        "name": "typhoid",
        "symptoms": ["prolonged fever", "abdominal pain", "headache", "weakness", "loss of appetite"],
        "transmission": "Spread through contaminated food or water.",
        "prevention": "Drink safe water, practice hand hygiene, and use proper sanitation.",
        "severity": "medium",
    },
    {
        "name": "measles",
        "symptoms": ["fever", "cough", "runny nose", "red eyes", "rash"],
        "transmission": "Spread through the air from coughing and sneezing.",
        "prevention": "Get vaccinated and avoid exposure to infected individuals.",
        "severity": "high",
    },
    {
        "name": "monkeypox",
        "symptoms": ["fever", "swollen lymph nodes", "rash", "muscle aches", "fatigue"],
        "transmission": "Spread through close contact with infected people, animals, or contaminated materials.",
        "prevention": "Avoid close contact with infected individuals and follow hygiene precautions.",
        "severity": "medium",
    },
]


def seed_diseases():
    db = get_db()
    collection = db["diseases"]
    inserted_names = []
    current_time = datetime.now(timezone.utc)

    for disease in DISEASES:
        if collection.find_one({"name": disease["name"]}) is None:
            document = {
                **disease,
                "last_updated": current_time,
            }
            collection.insert_one(document)
            inserted_names.append(disease["name"])

    print("Inserted diseases:")
    for name in inserted_names:
        print(f"* {name}")

    print("All diseases:")
    for disease in collection.find({}, {"_id": 0, "name": 1}).sort("name", 1):
        print(f"* {disease['name']}")


if __name__ == "__main__":
    seed_diseases()
