"""S3-compatible blob storage; boto3 runs in a worker thread."""

from __future__ import annotations

import asyncio
import hashlib
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from exchange.models.ports.storage import StoredObject


class StorageUnavailable(Exception):
    """The object store rejected or could not serve a request."""


class S3BlobStore:
    """Small adapter around the boto3 S3 client."""

    def __init__(
        self,
        *,
        endpoint: str,
        public_endpoint: str,
        region: str,
        bucket: str,
        access_key: str,
        secret_key: str,
        use_ssl: bool,
    ) -> None:
        self._bucket = bucket
        self._public_endpoint = public_endpoint
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            use_ssl=use_ssl,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )
        self._public = boto3.client(
            "s3",
            endpoint_url=public_endpoint,
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            use_ssl=use_ssl,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )

    async def put(self, key: str, payload: bytes) -> StoredObject:
        """Write bytes with server-side encryption enabled."""
        digest = hashlib.sha256(payload).hexdigest()
        await self._call(
            self._client.put_object,
            Bucket=self._bucket,
            Key=key,
            Body=payload,
            ContentType="application/octet-stream",
            ServerSideEncryption="AES256",
        )
        return StoredObject(key=key, size=len(payload), checksum_sha256=digest)

    async def get(self, key: str) -> bytes:
        """Read bytes by key."""
        response: dict[str, Any] = await self._call(
            self._client.get_object, Bucket=self._bucket, Key=key
        )
        body = response["Body"]
        data: bytes = await asyncio.to_thread(body.read)
        return data

    async def delete(self, key: str) -> None:
        """Delete idempotently."""
        await self._call(self._client.delete_object, Bucket=self._bucket, Key=key)

    async def presign_put(self, key: str, content_type: str, ttl: int) -> str:
        """Presign a PUT for the client-visible endpoint."""
        return await self._presign("put_object", key, ttl, ContentType=content_type)

    async def presign_get(self, key: str, ttl: int) -> str:
        """Presign a GET for the client-visible endpoint."""
        return await self._presign("get_object", key, ttl)

    async def _presign(self, operation: str, key: str, ttl: int, **extra: Any) -> str:
        url: str = await asyncio.to_thread(
            self._public.generate_presigned_url,
            operation,
            Params={"Bucket": self._bucket, "Key": key, **extra},
            ExpiresIn=ttl,
        )
        return url

    async def _call(self, function: Any, **kwargs: Any) -> Any:
        try:
            return await asyncio.to_thread(function, **kwargs)
        except (BotoCoreError, ClientError) as exc:
            raise StorageUnavailable("object storage request failed") from exc
