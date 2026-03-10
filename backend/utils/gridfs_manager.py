"""GridFS manager for MongoDB file storage."""
import asyncio
import logging
from io import BytesIO
from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorGridFSBucket
from gridfs.errors import NoFile

logger = logging.getLogger(__name__)


class GridFSManager:
    """Manager for storing and retrieving files from MongoDB GridFS."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize GridFS manager."""
        self.db = db
        self.bucket = AsyncIOMotorGridFSBucket(db)

    async def upload_file(
        self,
        filename: str,
        file_content: bytes,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Upload file to GridFS.

        Args:
            filename: Original filename
            file_content: File content as bytes
            metadata: Optional metadata dictionary

        Returns:
            GridFS file_id as string
        """
        try:
            # Convert bytes to BytesIO stream
            file_stream = BytesIO(file_content)
            
            file_id = await self.bucket.upload_from_stream(
                filename,
                file_stream,
                metadata=metadata or {},
            )
            logger.info(f"Uploaded file to GridFS: {filename} (ID: {file_id})")
            return str(file_id)
        except Exception as e:
            logger.error(f"Failed to upload file to GridFS: {e}")
            raise

    async def download_file(self, file_id: str) -> bytes:
        """
        Download file from GridFS.

        Args:
            file_id: GridFS file_id (string or ObjectId)

        Returns:
            File content as bytes
        """
        try:
            # Convert string to ObjectId if needed
            if isinstance(file_id, str):
                file_id = ObjectId(file_id)
                
            grid_out = await self.bucket.open_download_stream(file_id)
            content = await grid_out.read()
            logger.info(f"Downloaded file from GridFS: {file_id}")
            return content
        except NoFile:
            logger.error(f"File not found in GridFS: {file_id}")
            raise FileNotFoundError(f"File not found: {file_id}")
        except Exception as e:
            logger.error(f"Failed to download file from GridFS: {e}")
            raise

    async def delete_file(self, file_id: str) -> None:
        """
        Delete file from GridFS.

        Args:
            file_id: GridFS file_id (string or ObjectId)
        """
        try:
            # Convert string to ObjectId if needed
            if isinstance(file_id, str):
                file_id = ObjectId(file_id)
                
            await self.bucket.delete(file_id)
            logger.info(f"Deleted file from GridFS: {file_id}")
        except NoFile:
            logger.warning(f"File not found in GridFS: {file_id}")
        except Exception as e:
            logger.error(f"Failed to delete file from GridFS: {e}")
            raise

    async def get_file_info(self, file_id: str) -> dict:
        """
        Get file information from GridFS.

        Args:
            file_id: GridFS file_id (string or ObjectId)

        Returns:
            File information dictionary
        """
        try:
            # Convert string to ObjectId if needed
            if isinstance(file_id, str):
                file_id = ObjectId(file_id)
                
            grid_out = await self.bucket.open_download_stream(file_id)
            return {
                "filename": grid_out.filename,
                "size": grid_out.length,
                "upload_date": grid_out.upload_date,
                "metadata": grid_out.metadata or {},
            }
        except NoFile:
            logger.error(f"File not found in GridFS: {file_id}")
            raise FileNotFoundError(f"File not found: {file_id}")
        except Exception as e:
            logger.error(f"Failed to get file info from GridFS: {e}")
            raise

    async def file_exists(self, file_id: str) -> bool:
        """
        Check if file exists in GridFS.

        Args:
            file_id: GridFS file_id (string or ObjectId)

        Returns:
            True if file exists, False otherwise
        """
        try:
            # Convert string to ObjectId if needed
            if isinstance(file_id, str):
                file_id = ObjectId(file_id)
                
            await self.bucket.open_download_stream(file_id)
            return True
        except NoFile:
            return False
        except Exception as e:
            logger.error(f"Error checking file existence: {e}")
            return False
