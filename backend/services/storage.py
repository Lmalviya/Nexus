import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from typing import Optional


load_dotenv()

class StorageService:
    def __init__(self):
        """Initialize storage client for MinIO (local S3-compatible storage)."""
        # MinIO configuration
        self.endpoint_url = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
        self.bucket_name = os.getenv("MINIO_BUCKET", "nexus-files")

        # Validate that required credentials are present
        if not all([self.access_key, self.secret_key, self.bucket_name]):
            raise ValueError(
                "MinIO credentials not configured. Set MINIO_ACCESS_KEY, MINIO_SECRET_KEY, and MINIO_BUCKET env variables."
            )

        # Create the boto3 S3 client for internal operations (backend -> MinIO)
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name="auto",
        )

        # Create a separate client for generating public URLs (browser -> MinIO)
        # This ensures the signature matches the Host header sent by the browser (localhost)
        self.public_endpoint_url = os.getenv("MINIO_PUBLIC_ENDPOINT", "http://localhost:9000")
        self.public_s3_client = boto3.client(
            "s3",
            endpoint_url=self.public_endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name="auto",
            config=boto3.session.Config(signature_version='s3v4')
        )

        # Ensure bucket exists
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError:
            self.s3_client.create_bucket(Bucket=self.bucket_name)
            print(f"Created MinIO bucket: {self.bucket_name}")

    def get_user_file_prefix(self, org_id: str, user_id: str) -> str:
        """Generate folder prefix for user-specific file storage.
        Returns: 'org_{org_id}/user_{user_id}/'
        """
        return f"org_{org_id}/user_{user_id}/"

    def create_user_folder(self, org_id: str, user_id: str) -> bool:
        """Create a placeholder object to initialize the user's folder structure.
        This ensures the directory appears in MinIO browser immediately.
        """
        prefix = self.get_user_file_prefix(org_id, user_id)
        key = f"{prefix}.keep"
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=b"",
                ContentType="application/x-directory"
            )
            print(f"Created user folder: {prefix}")
            return True
        except ClientError as e:
            print(f"Error creating user folder: {e}")
            return False

    def get_presigned_url(self, object_name: str, prefix: str = "", expiration: int = 3600, content_type: str = "application/octet-stream") -> Optional[str]:
        """Generate a presigned URL for uploading a file.
        Args:
            object_name: The filename to upload
            prefix: Optional folder prefix (e.g., 'org_123/user_456/')
            expiration: URL expiration time in seconds
            content_type: The MIME type of the file (required for signature matching)
        Returns the URL string or ``None`` on error.
        """
        # Combine prefix and object name
        full_key = f"{prefix}{object_name}" if prefix else object_name
        
        try:
            # Use the public client to generate the URL so the signature matches localhost
            # IMPORTANT: We DO NOT include ContentType in Params to allow flexibility (e.g. charset)
            response = self.public_s3_client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": self.bucket_name, 
                    "Key": full_key
                },
                ExpiresIn=expiration,
            )
            return response
        except ClientError as e:
            print(f"Error generating presigned URL: {e}")
            return None

    def delete_file(self, object_name: str) -> bool:
        """Delete a file from the bucket. Returns ``True`` on success."""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=object_name)
            return True
        except ClientError as e:
            print(f"Error deleting file: {e}")
            return False

    def delete_user_files(self, org_id: str, user_id: str) -> bool:
        """Delete all files for a specific user.
        This is called when a user account is deleted.
        Returns ``True`` if successful.
        """
        prefix = self.get_user_file_prefix(org_id, user_id)
        try:
            # List all objects with the user's prefix
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            # Delete all objects if any exist
            if 'Contents' in response:
                objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
                self.s3_client.delete_objects(
                    Bucket=self.bucket_name,
                    Delete={'Objects': objects_to_delete}
                )
                print(f"Deleted {len(objects_to_delete)} files for user {user_id}")
            
            return True
        except ClientError as e:
            print(f"Error deleting user files: {e}")
            return False

    def get_file_url(self, object_name: str) -> str:
        """Return a public URL for the stored object in MinIO.
        Args:
            object_name: The full key/path of the object (including any prefix)
        """
        return f"{self.public_endpoint_url}/{self.bucket_name}/{object_name}"

    def list_user_files(self, org_id: str, user_id: str) -> list:
        """List all files for a specific user.
        Returns a list of dicts with file metadata.
        """
        prefix = self.get_user_file_prefix(org_id, user_id)
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    # Skip the placeholder .keep file
                    if key.endswith('.keep'):
                        continue
                        
                    filename = key.replace(prefix, "")
                    files.append({
                        "file_key": key,
                        "filename": filename,
                        "size": obj['Size'],
                        "last_modified": obj['LastModified'].isoformat(),
                        "url": self.get_file_url(key)
                    })
            return files
        except ClientError as e:
            print(f"Error listing user files: {e}")
            return []

