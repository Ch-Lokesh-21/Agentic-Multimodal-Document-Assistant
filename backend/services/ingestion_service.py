"""
Ingestion service for PDF document processing and vectorization.
"""
import aiofiles
import aiofiles.os
import asyncio
import logging
import os
import shutil
from pathlib import Path
from typing import Optional
from langsmith import traceable
from config import settings
from crud import document_crud
from schemas import (
    DocumentCreate,
    DocumentInDB,
    DocumentResponse,
    DocumentStatus,
    DocumentListResponse,
)
from services.session_service import session_service
from utils.object_id import PyObjectId
from vectorstore.chroma import ChromaManager

logger = logging.getLogger(__name__)


class IngestionError(Exception):
    """Raised when document ingestion fails."""
    pass


class DocumentNotFoundError(Exception):
    """Raised when document is not found."""
    pass


class IngestionService:
    """Service for document upload and ingestion."""

    @staticmethod
    def get_session_upload_dir(session_id: str) -> Path:
        """Get upload directory for session."""
        upload_dir = Path(settings.upload.directory) / session_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        return upload_dir

    @staticmethod
    def validate_file(filename: str, file_size: int) -> None:
        """Validate uploaded file extension and size."""
        ext = Path(filename).suffix.lower().lstrip(".")
        if ext not in settings.upload.allowed_extensions:
            raise IngestionError(
                f"Invalid file type: .{ext}. Allowed: {settings.upload.allowed_extensions}"
            )

        if file_size > settings.upload_max_bytes:
            raise IngestionError(
                f"File too large: {file_size / 1024 / 1024:.1f}MB. "
                f"Maximum: {settings.upload.max_file_size_mb}MB"
            )

    @classmethod
    async def save_uploaded_file(
        cls,
        user_id: PyObjectId,
        session_id: str,
        filename: str,
        file_content: bytes,
    ) -> DocumentInDB:
        """Save uploaded file and create document record."""
        cls.validate_file(filename, len(file_content))

        upload_dir = cls.get_session_upload_dir(session_id)

        safe_filename = Path(filename).name
        file_path = upload_dir / safe_filename

        counter = 1
        while file_path.exists():
            stem = Path(filename).stem
            suffix = Path(filename).suffix
            safe_filename = f"{stem}_{counter}{suffix}"
            file_path = upload_dir / safe_filename
            counter += 1

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_content)

        document_create = DocumentCreate(
            user_id=user_id,
            session_id=session_id,
            file_name=filename,
            file_path=str(file_path),
            file_size=len(file_content),
            content_type="application/pdf",
        )

        document = await document_crud.create(document_create)

        await session_service.increment_documents(session_id)

        return document

    @classmethod
    @traceable(name="Ingest Document Function")
    async def ingest_document(
        cls,
        document: DocumentInDB,
    ) -> DocumentInDB:
        """Ingest document into vector store."""
        try:
            await document_crud.mark_processing(document.id)

            chroma = ChromaManager(collection_name=document.session_id)

            chunk_count, page_count = await chroma.ingest_pdf(
                document.file_path,
            )

            await document_crud.mark_indexed(
                document.id,
                chunk_count=chunk_count,
                page_count=page_count,
            )

            logger.info(
                f"Ingested document {document.file_name}: "
                f"{chunk_count} chunks, {page_count} pages"
            )

            return await document_crud.get_by_id(document.id)

        except Exception as e:
            logger.error(
                f"Ingestion failed for {document.file_name}: {str(e)}")
            await document_crud.mark_failed(document.id, str(e))
            raise IngestionError(f"Failed to ingest document: {str(e)}")

    @classmethod
    @traceable(name="Upload and Ingest Document Function")
    async def upload_and_ingest(
        cls,
        user_id: PyObjectId,
        session_id: str,
        filename: str,
        file_content: bytes,
    ) -> DocumentResponse:
        """Upload and ingest document in one operation."""
        document = await cls.save_uploaded_file(
            user_id, session_id, filename, file_content
        )

        try:
            document = await cls.ingest_document(document)
        except IngestionError:
            document = await document_crud.get_by_id(document.id)

        return DocumentResponse.from_db(document)

    @classmethod
    async def get_document(
        cls,
        document_id: str,
        user_id: PyObjectId,
    ) -> DocumentResponse:
        """Get document by ID."""
        document = await document_crud.get_by_id_and_user(document_id, user_id)

        if document is None:
            raise DocumentNotFoundError(f"Document '{document_id}' not found")

        return DocumentResponse.from_db(document)

    @classmethod
    async def list_documents(
        cls,
        session_id: str,
        user_id: PyObjectId,
    ) -> DocumentListResponse:
        """List documents in session."""
        documents = await document_crud.get_all_by_session(session_id, user_id)

        return DocumentListResponse(
            documents=[DocumentResponse.from_db(d) for d in documents],
            total=len(documents),
        )

    @classmethod
    async def delete_document(
        cls,
        document_id: str,
        user_id: PyObjectId,
    ) -> bool:
        """Delete document and its file."""
        document = await document_crud.get_by_id_and_user(document_id, user_id)

        if document is None:
            raise DocumentNotFoundError(f"Document '{document_id}' not found")

        try:
            if os.path.exists(document.file_path):
                await aiofiles.os.remove(document.file_path)
        except Exception as e:
            logger.warning(f"Failed to delete file {document.file_path}: {e}")

        try:
            chroma = ChromaManager(collection_name=document.session_id)
            await chroma.delete_by_source(document.file_name)
        except Exception as e:
            logger.warning(f"Failed to delete from vector store: {e}")

        deleted = await document_crud.delete(document_id, user_id)

        if deleted:
            await session_service.increment_documents(document.session_id, -1)

        return deleted

    @classmethod
    async def retry_failed_document(
        cls,
        document_id: str,
        user_id: PyObjectId,
    ) -> DocumentResponse:
        """
        Retry ingestion of a failed document.

        Args:
            document_id: Document ID
            user_id: User ID for validation

        Returns:
            Updated document response
        """
        document = await document_crud.get_by_id_and_user(document_id, user_id)

        if document is None:
            raise DocumentNotFoundError(f"Document '{document_id}' not found")

        if document.status != DocumentStatus.FAILED:
            raise IngestionError("Document is not in failed state")

        document = await cls.ingest_document(document)

        return DocumentResponse.from_db(document)


ingestion_service = IngestionService()
