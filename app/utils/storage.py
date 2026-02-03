import os
import uuid
from datetime import datetime, timedelta
from typing import BinaryIO

from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError

from app.config import settings


class GCSStorage:
    """
    Google Cloud Storage utility class for handling file uploads and management.
    Supports multiple buckets with structured paths for easy migration.
    """

    def __init__(self):
        """Initialize GCS client with credentials from environment.
        
        Supports two authentication modes:
        1. Local dev: Uses GOOGLE_APPLICATION_CREDENTIALS file path
        2. Cloud Run: Uses workload identity (automatic authentication)
        """
        if not settings.GCS_USER_IMAGES_BUCKET or not settings.GCS_SUBMISSIONS_BUCKET:
            raise ValueError("GCS bucket names are not configured")

        self.user_images_bucket = settings.GCS_USER_IMAGES_BUCKET
        self.submissions_bucket = settings.GCS_SUBMISSIONS_BUCKET
        
        # If GOOGLE_APPLICATION_CREDENTIALS is set, use it (local dev)
        # Otherwise, use Application Default Credentials (Cloud Run)
        if settings.GOOGLE_APPLICATION_CREDENTIALS:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GOOGLE_APPLICATION_CREDENTIALS
            self.client = storage.Client(project=settings.GCS_PROJECT_ID)
        else:
            # On Cloud Run, use workload identity (no credentials file needed)
            self.client = storage.Client(project=settings.GCS_PROJECT_ID)

    def upload_user_profile_photo(
        self,
        file: BinaryIO,
        user_id: str,
        filename: str,
        content_type: str = "image/jpeg",
    ) -> str:
        """
        Upload a user profile photo to the user images bucket.
        
        Path structure: profiles/{user_id}.{ext}
        This will delete any existing profile photos for the user (all extensions)
        before uploading the new one, ensuring only one photo per user.

        Args:
            file: Binary file object to upload
            user_id: ID of the user (e.g., "user_123")
            filename: Original filename (used to get extension)
            content_type: MIME type of the file

        Returns:
            str: Public URL of the uploaded file

        Raises:
            Exception: If upload fails
        """
        try:
            bucket = self.client.bucket(self.user_images_bucket)

            # Delete any existing profile photos for this user (all extensions)
            self._delete_all_user_profile_photos(user_id)

            # Use user_id as filename with original extension
            file_extension = os.path.splitext(filename)[1].lower()
            blob_name = f"profiles/{user_id}{file_extension}"

            # Create blob and upload
            blob = bucket.blob(blob_name)
            blob.content_type = content_type

            # Upload from file object
            file.seek(0)
            blob.upload_from_file(file, content_type=content_type)

            return blob.public_url

        except GoogleCloudError as e:
            raise Exception(f"Failed to upload profile photo to GCS: {str(e)}")
        except Exception as e:
            raise Exception(f"Upload error: {str(e)}")

    def upload_submission_photo(
        self,
        file: BinaryIO,
        submission_id: str,
        filename: str,
        content_type: str = "image/jpeg",
    ) -> str:
        """
        Upload a submission photo to the submissions bucket.
        
        Path structure: submissions/{submission_id}/{uuid}.{ext}
        Allows multiple photos per submission.

        Args:
            file: Binary file object to upload
            submission_id: ID of the submission (e.g., "submission_123")
            filename: Original filename (used to get extension)
            content_type: MIME type of the file

        Returns:
            str: Public URL of the uploaded file

        Raises:
            Exception: If upload fails
        """
        try:
            bucket = self.client.bucket(self.submissions_bucket)

            # Generate unique filename for this photo
            file_extension = os.path.splitext(filename)[1].lower()
            unique_id = uuid.uuid4()
            blob_name = f"submissions/{submission_id}/{unique_id}{file_extension}"

            # Create blob and upload
            blob = bucket.blob(blob_name)
            blob.content_type = content_type

            # Upload from file object
            file.seek(0)
            blob.upload_from_file(file, content_type=content_type)

            return blob.public_url

        except GoogleCloudError as e:
            raise Exception(f"Failed to upload submission photo to GCS: {str(e)}")
        except Exception as e:
            raise Exception(f"Upload error: {str(e)}")

    def _delete_all_user_profile_photos(self, user_id: str) -> None:
        """
        Internal method to delete all existing profile photos for a user.
        This ensures only one photo per user by removing all extensions.

        Args:
            user_id: The user ID
        """
        try:
            bucket = self.client.bucket(self.user_images_bucket)
            # List all blobs that start with profiles/{user_id}
            blobs = bucket.list_blobs(prefix=f"profiles/{user_id}")
            for blob in blobs:
                # Only delete if it matches the exact pattern (with extension)
                # This prevents deleting "user_123" when looking for "user_12"
                blob_filename = os.path.basename(blob.name)
                if blob_filename.startswith(user_id + "."):
                    blob.delete()
        except GoogleCloudError:
            # Ignore errors - if nothing to delete, that's fine
            pass

    def delete_user_profile_photo(self, user_id: str) -> bool:
        """
        Delete all profile photos for a user from Google Cloud Storage.
        This removes photos with any file extension.

        Args:
            user_id: The user ID

        Returns:
            bool: True if at least one photo was deleted, False otherwise
        """
        try:
            bucket = self.client.bucket(self.user_images_bucket)
            blobs = bucket.list_blobs(prefix=f"profiles/{user_id}")
            deleted_any = False
            
            for blob in blobs:
                # Only delete if it matches the exact pattern (with extension)
                blob_filename = os.path.basename(blob.name)
                if blob_filename.startswith(user_id + "."):
                    blob.delete()
                    deleted_any = True
            
            return deleted_any
        except GoogleCloudError:
            return False

    def delete_submission_photo(self, submission_id: str, photo_filename: str) -> bool:
        """
        Delete a specific submission photo from Google Cloud Storage.

        Args:
            submission_id: The submission ID
            photo_filename: The filename of the photo to delete (e.g., "uuid.jpg")

        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            blob_name = f"submissions/{submission_id}/{photo_filename}"
            bucket = self.client.bucket(self.submissions_bucket)
            blob = bucket.blob(blob_name)
            blob.delete()
            return True
        except GoogleCloudError:
            return False

    def delete_all_submission_photos(self, submission_id: str) -> bool:
        """
        Delete all photos for a submission.

        Args:
            submission_id: The submission ID

        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            bucket = self.client.bucket(self.submissions_bucket)
            blobs = bucket.list_blobs(prefix=f"submissions/{submission_id}/")
            for blob in blobs:
                blob.delete()
            return True
        except GoogleCloudError:
            return False

    def list_submission_photos(self, submission_id: str) -> list[str]:
        """
        List all photo URLs for a submission.

        Args:
            submission_id: The submission ID

        Returns:
            list[str]: List of public URLs
        """
        try:
            bucket = self.client.bucket(self.submissions_bucket)
            blobs = bucket.list_blobs(prefix=f"submissions/{submission_id}/")
            return [blob.public_url for blob in blobs]
        except GoogleCloudError:
            return []

    def delete_file(self, file_url: str) -> bool:
        """
        Delete a file from Google Cloud Storage using its public URL.

        Args:
            file_url: The public URL of the file to delete

        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            # Determine which bucket and extract blob name
            if self.user_images_bucket in file_url:
                bucket_name = self.user_images_bucket
            elif self.submissions_bucket in file_url:
                bucket_name = self.submissions_bucket
            else:
                return False

            # Extract blob name from URL
            blob_name = file_url.split(f"{bucket_name}/")[-1]

            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            blob.delete()
            return True

        except GoogleCloudError:
            return False

    def validate_image_file(self, filename: str) -> tuple[bool, str]:
        """
        Validate image file by extension.

        Args:
            filename: Name of the file

        Returns:
            tuple: (is_valid, error_message)
        """
        allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
        file_extension = os.path.splitext(filename)[1].lower()

        if file_extension not in allowed_extensions:
            return False, f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"

        return True, ""


# Singleton instance
gcs_storage = (
    GCSStorage()
    if settings.GCS_USER_IMAGES_BUCKET and settings.GCS_SUBMISSIONS_BUCKET
    else None
)
