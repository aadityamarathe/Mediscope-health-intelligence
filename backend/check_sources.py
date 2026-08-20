from backend.database.mongo_connection import get_db
db = get_db()
print(db["outbreaks_v2"].distinct("source"))
