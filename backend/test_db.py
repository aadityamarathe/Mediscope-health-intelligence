from database.mongo_connection import get_db

db = get_db()

# Test write
db.raw_articles.insert_one({"test": "hello"})

# Test read
doc = db.raw_articles.find_one({"test": "hello"})
print(doc)

db.raw_articles.insert_one({"url": "test_url"})
db.raw_articles.insert_one({"url": "test_url"})  # should fail if index exists

print("DB working ✅")
