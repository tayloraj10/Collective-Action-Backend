from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.utils.storage import gcs_storage

router = APIRouter(prefix="/photos", tags=["photos"])


@router.post("/profile/{user_id}", status_code=status.HTTP_200_OK)
async def upload_profile_photo(
    user_id: str,
    file: UploadFile = File(...),
) -> str:
    """
    Upload a user profile photo to cloud storage.

    This endpoint uploads a profile photo for a specific user. The photo is stored
    with the user's ID as the filename, so uploading a new photo will replace the old one.

    Path Structure:
    - collective-action-user-images/profiles/{user_id}.{ext}

    Args:
        user_id: The ID of the user (e.g., "user_123")
        file: The image file to upload

    Returns:
        str: The public URL of the uploaded photo

    Raises:
        HTTPException: If upload fails or validation fails
    """
    if not gcs_storage:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cloud storage is not configured",
        )

    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    is_valid, error_msg = gcs_storage.validate_image_file(file.filename)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # Validate content type
    allowed_content_types = {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/gif",
        "image/webp",
    }
    if file.content_type not in allowed_content_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content type. Allowed: {', '.join(allowed_content_types)}",
        )

    try:
        # Upload file to GCS
        file_url = gcs_storage.upload_user_profile_photo(
            file=file.file,
            user_id=user_id,
            filename=file.filename,
            content_type=file.content_type,
        )

        return file_url

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload profile photo: {str(e)}",
        )


@router.post("/submission/{submission_id}", status_code=status.HTTP_200_OK)
async def upload_submission_photos(
    submission_id: str,
    files: list[UploadFile] = File(..., description="One or more image files"),
) -> list[str]:
    """
    Upload one or more submission photos to cloud storage.

    This endpoint uploads photos for a specific submission. Each file gets a unique
    filename under that submission.

    Path Structure:
    - collective-action-submissions/submissions/{submission_id}/{uuid}.{ext}

    Args:
        submission_id: The ID of the submission (e.g., "submission_123")
        files: One or more image files to upload

    Returns:
        list[str]: Public URLs of the uploaded photos (same order as input)

    Raises:
        HTTPException: If no files provided, validation fails, or upload fails
    """
    if not gcs_storage:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cloud storage is not configured",
        )

    if not files:
        raise HTTPException(status_code=400, detail="At least one file is required")

    allowed_content_types = {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/gif",
        "image/webp",
    }

    # Validate all files first
    for i, file in enumerate(files):
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail=f"File at index {i} has no filename",
            )
        is_valid, error_msg = gcs_storage.validate_image_file(file.filename)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        if file.content_type not in allowed_content_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid content type. Allowed: {', '.join(allowed_content_types)}",
            )

    # Upload each file and collect URLs
    urls: list[str] = []
    for file in files:
        try:
            file_url = gcs_storage.upload_submission_photo(
                file=file.file,
                submission_id=submission_id,
                filename=file.filename,
                content_type=file.content_type or "image/jpeg",
            )
            urls.append(file_url)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload photo {file.filename}: {str(e)}",
            )

    return urls


@router.get("/submission/{submission_id}", status_code=status.HTTP_200_OK)
async def list_submission_photos(submission_id: str) -> list[str]:
    """
    List all photos for a submission.

    Args:
        submission_id: The ID of the submission

    Returns:
        list[str]: List of photo URLs
    """
    if not gcs_storage:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cloud storage is not configured",
        )

    try:
        urls = gcs_storage.list_submission_photos(submission_id)
        return urls
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list photos: {str(e)}",
        )


@router.delete("/profile/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile_photo(user_id: str):
    """
    Delete all profile photos for a user (any file extension).

    Args:
        user_id: The ID of the user
    """
    if not gcs_storage:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cloud storage is not configured",
        )

    success = gcs_storage.delete_user_profile_photo(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile photo not found",
        )


@router.delete("/submission/{submission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_submission_photos(submission_id: str):
    """
    Delete all photos for a submission.

    Args:
        submission_id: The ID of the submission
    """
    if not gcs_storage:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cloud storage is not configured",
        )

    success = gcs_storage.delete_all_submission_photos(submission_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission photos not found",
        )


@router.delete(
    "/submission/{submission_id}/{photo_filename}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_submission_photo(submission_id: str, photo_filename: str):
    """
    Delete a specific photo from a submission.

    Args:
        submission_id: The ID of the submission
        photo_filename: The filename of the photo (e.g., "uuid.jpg")
    """
    if not gcs_storage:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cloud storage is not configured",
        )

    success = gcs_storage.delete_submission_photo(submission_id, photo_filename)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found",
        )
