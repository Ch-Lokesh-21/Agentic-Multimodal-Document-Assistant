"""
Ingestion service for PDF document processing and vectorization.
"""
import asyncio
import logging
from typing import Optional
from langsmith import traceable
from config import settings
from crud import document_crud
from db import MongoDB
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
    def validate_file(filename: str, file_size: int) -> None:
        """Validate uploaded file extension and size."""
        from pathlib import Path
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
        """Save uploaded file to GridFS and create document record."""
        cls.validate_file(filename, len(file_content))

        # Upload file to GridFS
        gridfs = MongoDB.get_gridfs()
        file_id = await gridfs.upload_file(
            filename=filename,
            file_content=file_content,
            metadata={
                "user_id": str(user_id),
                "session_id": session_id,
                "original_filename": filename,
            }
        )

        document_create = DocumentCreate(
            user_id=user_id,
            session_id=session_id,
            file_name=filename,
            gridfs_file_id=file_id,
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
        import tempfile
        from pathlib import Path
        
        try:
            await document_crud.mark_processing(document.id)

            # Download file from GridFS
            gridfs = MongoDB.get_gridfs()
            file_content = await gridfs.download_file(document.gridfs_file_id)

            # Create temporary file for processing
            with tempfile.NamedTemporaryFile(
                suffix=".pdf",
                delete=False,
                dir=settings.upload.directory
            ) as tmp_file:
                tmp_file.write(file_content)
                tmp_file_path = tmp_file.name

            try:
                chroma = ChromaManager(collection_name=document.session_id)

                chunk_count, page_count = await chroma.ingest_pdf(
                    tmp_file_path,
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

            finally:
                # Clean up temporary file
                Path(tmp_file_path).unlink(missing_ok=True)

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
        """Delete document and remove from GridFS."""
        document = await document_crud.get_by_id_and_user(document_id, user_id)

        if document is None:
            raise DocumentNotFoundError(f"Document '{document_id}' not found")

        try:
            # Delete file from GridFS
            gridfs = MongoDB.get_gridfs()
            await gridfs.delete_file(document.gridfs_file_id)
        except Exception as e:
            logger.warning(f"Failed to delete file from GridFS: {e}")

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
