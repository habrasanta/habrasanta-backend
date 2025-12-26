import boto3
import gzip
import os
import re

from botocore.client import Config


s3_client = boto3.client("s3",
    region_name="hel11",
    endpoint_url="https://hel1.your-objectstorage.com",
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    config=Config(
        signature_version="s3",
        s3={
            "payload_signing_enabled": False,
            "addressing_style": "path",
        },
    ))

p = re.compile("\\.[0-9a-f]{20}\\.")
for filename in os.listdir("dist"):
    if not p.search(filename):
        print("Skipping '{}'".format(filename))
        continue
    with open(os.path.join("dist", filename), "rb") as f:
        kwargs = {
            "Bucket": "habra-adm",
            "Key": filename,
            "CacheControl": "public, max-age=315360000",
        }

        _, ext = os.path.splitext(filename)
        kwargs["ContentType"] = {
            ".css": "text/css; charset=utf-8",
            ".jpg": "image/jpeg",
            ".js": "application/javascript; charset=utf-8",
            ".png": "image/png",
            ".woff2": "font/woff2",
        }[ext]

        data = f.read()
        compressed = gzip.compress(data, 9)
        print("Uploading '{}': compressed={}, uncompressed={}".format(filename, len(compressed), len(data)))
        if len(compressed) < len(data):
            kwargs["Body"] = compressed
            kwargs["ContentEncoding"] = "gzip"
        else:
            kwargs["Body"] = data

        s3_client.put_object(**kwargs)
