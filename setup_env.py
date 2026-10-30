"""
setup_env.py - creates a correct .env file with fresh SECRET_KEY and MASTER_KEY.
Existing values are kept; only empty ones are filled in.
"""
import os
import secrets
from crypto import generate_master_key

DEFAULTS = {
    "AWS_ACCESS_KEY_ID": "",
    "AWS_SECRET_ACCESS_KEY": "",
    "AWS_REGION": "ap-south-1",
    "S3_BUCKET": "",
    "MASTER_KEY": "",
    "SECRET_KEY": "",
    "STORAGE_MODE": "local",
}

values = dict(DEFAULTS)

# keep anything already filled in
if os.path.exists(".env"):
    for raw in open(".env", encoding="utf-8-sig", errors="ignore"):
        line = raw.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            if k.strip() in values and v.strip():
                values[k.strip()] = v.strip().strip('"').strip("'")

if not values["SECRET_KEY"]:
    values["SECRET_KEY"] = secrets.token_hex(32)
    print("Created a new SECRET_KEY")
if not values["MASTER_KEY"]:
    values["MASTER_KEY"] = generate_master_key()
    print("Created a new MASTER_KEY")

with open(".env", "w", encoding="utf-8", newline="\n") as f:
    for k in DEFAULTS:
        f.write(f"{k}={values[k]}\n")

print()
print(".env saved here:", os.path.abspath(".env"))
print("IMPORTANT: back up the MASTER_KEY line from .env somewhere safe (not in this project folder).")