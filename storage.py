"""
storage.py - store encrypted chunks either in a local folder or in Amazon S3.
Switch with STORAGE_MODE=local / s3 in .env. The functions are identical either way.
"""
import os
import shutil
import config

# ---------- local folder mode ----------

def _local_path(key):
    base = os.path.abspath(config.LOCAL_STORAGE_DIR)
    path = os.path.abspath(os.path.join(base, *key.split("/")))
    if not path.startswith(base + os.sep):      # block path tricks like ../
        raise ValueError("Invalid storage key")
    return path

# ---------- S3 mode ----------

_client = None

def _s3():
    global _client
    if _client is None:
        import boto3
        _client = boto3.client("s3", region_name=config.AWS_REGION)
    return _client

# ---------- public functions ----------

def put_chunk(key, data: bytes):
    if config.STORAGE_MODE == "s3":
        _s3().put_object(Bucket=config.S3_BUCKET, Key=key, Body=data)
    else:
        path = _local_path(key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)


def get_chunk(key) -> bytes:
    if config.STORAGE_MODE == "s3":
        return _s3().get_object(Bucket=config.S3_BUCKET, Key=key)["Body"].read()
    with open(_local_path(key), "rb") as f:
        return f.read()


def delete_prefix(prefix):
    """Delete every chunk under a prefix like 'files/<file_id>/'."""
    if config.STORAGE_MODE == "s3":
        paginator = _s3().get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=config.S3_BUCKET, Prefix=prefix):
            objects = [{"Key": o["Key"]} for o in page.get("Contents", [])]
            if objects:
                _s3().delete_objects(Bucket=config.S3_BUCKET, Delete={"Objects": objects})
    else:
        path = _local_path(prefix.rstrip("/"))
        if os.path.isdir(path):
            shutil.rmtree(path)