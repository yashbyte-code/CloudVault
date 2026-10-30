import os
from dotenv import load_dotenv

load_dotenv()

STORAGE_MODE = os.getenv("STORAGE_MODE", "local").lower()   # "local" or "s3"
LOCAL_STORAGE_DIR = os.getenv("LOCAL_STORAGE_DIR", "local_storage")
DB_PATH = os.getenv("DB_PATH", "cloudvault.db")

S3_BUCKET = os.getenv("S3_BUCKET")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

MASTER_KEY = os.getenv("MASTER_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")