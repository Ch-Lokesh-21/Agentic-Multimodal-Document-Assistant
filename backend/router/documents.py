from fastapi import APIRouter, HTTPException, UploadFile, File, status

from middleware import CurrentUserDep
from schemas import (
    DocumentResponse,
    DocumentUploadResponse,
    DocumentListResponse,
    APIResponse,
    ErrorResponse,
)
from services import (
    SessionNotFoundError,
    IngestionError,
    DocumentNotFoundError,
    session_service,
    ingestion_service,
)

router = APIRouter(tags=["Documents"])


@router.post(
    "/sessions/{session_id}/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Document uploaded and ingested successfully"},
        400: {"model": ErrorResponse, "description": "Invalid file"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Session not found"},
        413: {"model": ErrorResponse, "description": "File too large"},
    },
    summary="Upload a PDF document",
    description="Upload a PDF file to a session and ingest it into the vector store.",
)
async def upload_document(
    session_id: str,
    current_user: CurrentUserDep,
    file: UploadFile = File(..., description="PDF file to upload"),
) -> DocumentUploadResponse:
    """
    Upload and ingest a PDF document.
    """
    try:
        await session_service.validate_session_access(session_id, current_user.id)
    except SessionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read file: {str(e)}",
        )

    try:
        document = await ingestion_service.upload_and_ingest(
            user_id=current_user.id,
            session_id=session_id,
            filename=file.filename or "document.pdf",
            file_content=content,
        )

        return DocumentUploadResponse(
            success=True,
            message="Document uploaded and ingested successfully",
            document=document,
        )

    except IngestionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/sessions/{session_id}/documents",
    response_model=DocumentListResponse,
    responses={
        200: {"description": "Documents retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Session not found"},
    },
    summary="List documents in session",
    description="Get all documents uploaded to a session.",
)
async def list_documents(
    session_id: str,
    current_user: CurrentUserDep,
) -> DocumentListResponse:
    """
    List all documents in a session.

    - **session_id**: Session to list documents from
    """
    try:
        await session_service.validate_session_access(session_id, current_user.id)
    except SessionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    return await ingestion_service.list_documents(session_id, current_user.id)


@router.get(
    "/documents/{document_id}",
    response_model=DocumentResponse,
    responses={
        200: {"description": "Document retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Document not found"},
    },
    summary="Get document by ID",
    description="Get a specific document by its ID.",
)
async def get_document(
    document_id: str,
    current_user: CurrentUserDep,
) -> DocumentResponse:
    """
    Get document details.

    - **document_id**: Document ID
    """
    try:
        return await ingestion_service.get_document(document_id, current_user.id)
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete(
    "/documents/{document_id}",
    response_model=APIResponse,
    responses={
        200: {"description": "Document deleted successfully"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Document not found"},
    },
    summary="Delete document",
    description="Delete a document and remove it from the vector store.",
)
async def delete_document(
    document_id: str,
    current_user: CurrentUserDep,
) -> APIResponse:
    """
    Delete a document.

    - **document_id**: Document to delete
    """
    try:
        await ingestion_service.delete_document(document_id, current_user.id)
        return APIResponse(
            success=True,
            message="Document deleted successfully",
        )
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/documents/{document_id}/retry",
    response_model=DocumentResponse,
    responses={
        200: {"description": "Document reprocessed successfully"},
        400: {"model": ErrorResponse, "description": "Document not in failed state"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Document not found"},
    },
    summary="Retry failed document",
    description="Retry ingestion of a failed document.",
)
async def retry_document(
    document_id: str,
    current_user: CurrentUserDep,
) -> DocumentResponse:
    """
    Retry ingestion of a failed document.

    - **document_id**: Failed document to retry
    """
    try:
        return await ingestion_service.retry_failed_document(
            document_id,
            current_user.id,
        )
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except IngestionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
