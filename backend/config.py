import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
DATABASE_NAME = "mediscope"
