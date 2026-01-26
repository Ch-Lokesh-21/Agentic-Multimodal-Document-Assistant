from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from db.mongo import get_documents_collection
from schemas.document import DocumentCreate, DocumentInDB, DocumentStatus, DocumentStatusUpdate
from utils.object_id import PyObjectId


class DocumentCRUD:
    """CRUD operations for Document records."""

    @staticmethod
    def _get_collection() -> AsyncIOMotorCollection:
        """Get documents collection."""
        return get_documents_collection()

    @classmethod
    async def create(cls, document_data: DocumentCreate) -> DocumentInDB:
        """
        Create a new document record.

        Args:
            document_data: Document creation data

        Returns:
            Created document record
        """
        collection = cls._get_collection()

        document = DocumentInDB(
            user_id=document_data.user_id,
            session_id=document_data.session_id,
            file_name=document_data.file_name,
            file_path=document_data.file_path,
            file_size=document_data.file_size,
            content_type=document_data.content_type,
            status=DocumentStatus.UPLOADED,
            created_at=datetime.now(timezone.utc),
        )

        result = await collection.insert_one(document.to_mongo_dict())
        document.id = result.inserted_id

        return document

    @classmethod
    async def get_by_id(cls, doc_id: str | PyObjectId) -> Optional[DocumentInDB]:
        """
        Get document by ID.

        Args:
            doc_id: Document ID

        Returns:
            Document record or None
        """
        collection = cls._get_collection()

        if isinstance(doc_id, str):
            doc_id = ObjectId(doc_id)

        doc = await collection.find_one({"_id": doc_id})

        if doc is None:
            return None

        return DocumentInDB.model_validate(doc)

    @classmethod
    async def get_by_id_and_user(
        cls,
        doc_id: str | PyObjectId,
        user_id: PyObjectId,
    ) -> Optional[DocumentInDB]:
        """
        Get document by ID with user ownership validation.

        Args:
            doc_id: Document ID
            user_id: User ID for validation

        Returns:
            Document record or None
        """
        collection = cls._get_collection()

        if isinstance(doc_id, str):
            doc_id = ObjectId(doc_id)

        doc = await collection.find_one({
            "_id": doc_id,
            "user_id": ObjectId(str(user_id)),
        })

        if doc is None:
            return None

        return DocumentInDB.model_validate(doc)

    @classmethod
    async def get_all_by_session(
        cls,
        session_id: str,
        user_id: PyObjectId,
        skip: int = 0,
        limit: int = 100,
    ) -> list[DocumentInDB]:
        """
        Get all documents for a session.

        Args:
            session_id: Session identifier
            user_id: User ID for validation
            skip: Number to skip
            limit: Maximum to return

        Returns:
            List of document records
        """
        collection = cls._get_collection()

        cursor = collection.find({
            "session_id": session_id,
            "user_id": ObjectId(str(user_id)),
        }).sort("created_at", -1).skip(skip).limit(limit)

        documents = []
        async for doc in cursor:
            documents.append(DocumentInDB.model_validate(doc))

        return documents

    @classmethod
    async def count_by_session(cls, session_id: str) -> int:
        """
        Count documents in a session.

        Args:
            session_id: Session identifier

        Returns:
            Number of documents
        """
        collection = cls._get_collection()
        return await collection.count_documents({"session_id": session_id})

    @classmethod
    async def get_pending_documents(
        cls,
        session_id: str,
        limit: int = 10,
    ) -> list[DocumentInDB]:
        """
        Get documents pending processing.

        Args:
            session_id: Session identifier
            limit: Maximum to return

        Returns:
            List of pending documents
        """
        collection = cls._get_collection()

        cursor = collection.find({
            "session_id": session_id,
            "status": DocumentStatus.UPLOADED.value,
        }).limit(limit)

        documents = []
        async for doc in cursor:
            documents.append(DocumentInDB.model_validate(doc))

        return documents

    @classmethod
    async def update_status(
        cls,
        doc_id: str | PyObjectId,
        status_update: DocumentStatusUpdate,
    ) -> Optional[DocumentInDB]:
        """
        Update document processing status.

        Args:
            doc_id: Document ID
            status_update: Status update data

        Returns:
            Updated document or None
        """
        collection = cls._get_collection()

        if isinstance(doc_id, str):
            doc_id = ObjectId(doc_id)

        update_dict = status_update.model_dump(exclude_none=True)
        update_dict["updated_at"] = datetime.now(timezone.utc)

        if status_update.status in [DocumentStatus.INDEXED, DocumentStatus.FAILED]:
            update_dict["processed_at"] = datetime.now(timezone.utc)

        result = await collection.find_one_and_update(
            {"_id": doc_id},
            {"$set": update_dict},
            return_document=True,
        )

        if result is None:
            return None

        return DocumentInDB.model_validate(result)

    @classmethod
    async def mark_processing(cls, doc_id: str | PyObjectId) -> bool:
        """
        Mark document as processing.

        Args:
            doc_id: Document ID

        Returns:
            True if updated
        """
        collection = cls._get_collection()

        if isinstance(doc_id, str):
            doc_id = ObjectId(doc_id)

        result = await collection.update_one(
            {"_id": doc_id},
            {
                "$set": {
                    "status": DocumentStatus.PROCESSING.value,
                    "updated_at": datetime.now(timezone.utc),
                },
            },
        )

        return result.modified_count > 0

    @classmethod
    async def mark_indexed(
        cls,
        doc_id: str | PyObjectId,
        chunk_count: int,
        page_count: int | None = None,
    ) -> bool:
        """
        Mark document as indexed.

        Args:
            doc_id: Document ID
            chunk_count: Number of indexed chunks
            page_count: Number of pages

        Returns:
            True if updated
        """
        collection = cls._get_collection()

        if isinstance(doc_id, str):
            doc_id = ObjectId(doc_id)

        update_data = {
            "status": DocumentStatus.INDEXED.value,
            "chunk_count": chunk_count,
            "processed_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        if page_count is not None:
            update_data["page_count"] = page_count

        result = await collection.update_one(
            {"_id": doc_id},
            {"$set": update_data},
        )

        return result.modified_count > 0

    @classmethod
    async def mark_failed(
        cls,
        doc_id: str | PyObjectId,
        error_message: str,
    ) -> bool:
        """
        Mark document as failed.

        Args:
            doc_id: Document ID
            error_message: Error description

        Returns:
            True if updated
        """
        collection = cls._get_collection()

        if isinstance(doc_id, str):
            doc_id = ObjectId(doc_id)

        result = await collection.update_one(
            {"_id": doc_id},
            {
                "$set": {
                    "status": DocumentStatus.FAILED.value,
                    "error_message": error_message,
                    "processed_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                },
            },
        )

        return result.modified_count > 0

    @classmethod
    async def delete(cls, doc_id: str | PyObjectId, user_id: PyObjectId) -> bool:
        """
        Delete document record.

        Args:
            doc_id: Document ID
            user_id: User ID for validation

        Returns:
            True if deleted
        """
        collection = cls._get_collection()

        if isinstance(doc_id, str):
            doc_id = ObjectId(doc_id)

        result = await collection.delete_one({
            "_id": doc_id,
            "user_id": ObjectId(str(user_id)),
        })

        return result.deleted_count > 0

    @classmethod
    async def delete_all_by_session(cls, session_id: str) -> int:
        """
        Delete all documents for a session.

        Args:
            session_id: Session identifier

        Returns:
            Number of documents deleted
        """
        collection = cls._get_collection()

        result = await collection.delete_many({"session_id": session_id})
        return result.deleted_count


document_crud = DocumentCRUD()
