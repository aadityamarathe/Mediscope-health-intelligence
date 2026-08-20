import sys
sys.path.insert(0, '.')
from backend.database.mongo_connection import get_db
from datetime import datetime, timezone

db = get_db()
missing = [
    {
        'name': 'hiv/aids',
        'description': 'HIV/AIDS is a chronic, potentially life-threatening condition caused by the human immunodeficiency virus.',
        'symptoms': ['weight loss', 'fever', 'fatigue', 'swollen lymph nodes', 'recurring infections'],
        'transmission': 'Blood, sexual contact, mother to child',
        'prevention': 'Safe sex, needle exchange, antiretroviral therapy',
        'created_at': datetime.now(timezone.utc)
    },
    {
        'name': 'leprosy',
        'description': 'Leprosy is a chronic infectious disease caused by Mycobacterium leprae affecting skin and nerves.',
        'symptoms': ['skin lesions', 'numbness', 'muscle weakness', 'eye problems'],
        'transmission': 'Prolonged close contact with untreated cases',
        'prevention': 'Early detection and multidrug therapy',
        'created_at': datetime.now(timezone.utc)
    }
]

for d in missing:
    db['diseases'].update_one({'name': d['name']}, {'$set': d}, upsert=True)
    print(f"Inserted: {d['name']}")