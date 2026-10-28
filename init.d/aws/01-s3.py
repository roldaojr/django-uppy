import json
import os

import boto3
from botocore.exceptions import ClientError

# O MiniStack define AWS_ENDPOINT_URL, credenciais e região para os scripts de init
session = boto3.session.Session(
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "test"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "test"),
    region_name=os.environ.get(
        "AWS_DEFAULT_REGION", os.environ.get("MINISTACK_REGION", "us-east-1")
    ),
)
ENDPOINT_URL = os.environ.get("AWS_ENDPOINT_URL", "http://localhost:4566")
BUCKET_NAME = os.environ.get("TELABRASIL_BUCKET", "bucket")


def client(service: str):
    return session.client(service, endpoint_url=ENDPOINT_URL)


def log(message: str) -> None:
    print(f"[telabrasil] {message}", flush=True)


# --- S3 ----------------------------------------------------------------------
def ensure_bucket() -> None:
    s3 = client("s3")
    try:
        s3.head_bucket(Bucket=BUCKET_NAME)
    except ClientError:
        s3.create_bucket(Bucket=BUCKET_NAME)
        log(f"bucket {BUCKET_NAME} criado")
    # Leitura pública: o CloudFront do MiniStack só lê o bucket que a policy permite
    s3.put_bucket_policy(
        Bucket=BUCKET_NAME,
        Policy=json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": "s3:GetObject",
                        "Resource": f"arn:aws:s3:::{BUCKET_NAME}/*",
                    }
                ],
            }
        ),
    )
    s3.put_bucket_cors(
        Bucket=BUCKET_NAME,
        CORSConfiguration={
            "CORSRules": [
                {
                    "AllowedOrigins": ["*"],
                    "AllowedMethods": ["GET", "HEAD", "PUT", "POST"],
                    "AllowedHeaders": ["*"],
                    "ExposeHeaders": ["ETag"],
                }
            ]
        },
    )


if __name__ == "__main__":
    ensure_bucket()
