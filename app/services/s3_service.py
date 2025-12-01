from __future__ import annotations

import uuid

import boto3
from botocore.config import Config

from app.core.config import Settings


class S3Service:
    def __init__(self, settings: Settings) -> None:
        if not settings.aws_s3_bucket:
            raise ValueError("S3 bucket is not configured.")
        self.bucket = settings.aws_s3_bucket
        self.region = settings.aws_region
        config = Config(
            region_name=settings.aws_region,
            signature_version="s3v4",
            s3={"addressing_style": "virtual"},
        )
        self.client = boto3.client(
            "s3",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            config=config,
        )

    def generate_presigned_upload(self, *, content_type: str) -> tuple[str, str]:
        key = f"listings/{uuid.uuid4()}"
        upload_url = self.client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self.bucket,
                "Key": key,
                "ContentType": content_type,
            },
            ExpiresIn=3600,
        )
        final_url = f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{key}"
        return upload_url, final_url
