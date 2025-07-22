"""
Storage service for handling media files in Supabase Storage.
"""
import logging
import os
import uuid
from typing import Optional, Dict, Any, BinaryIO
from datetime import datetime
from supabase import Client

from config.settings import settings
from config.database import get_db_client

logger = logging.getLogger(__name__)


class StorageService:
    """Service for managing file uploads and storage in Supabase."""
    
    def __init__(self):
        self.client: Client = get_db_client()
        self.bucket_name = "user-media"
        
    async def create_user_folder(self, user_id: uuid.UUID) -> bool:
        """
        Create a user folder in storage (handled automatically by Supabase).
        This method ensures the folder structure exists.
        """
        try:
            # Create a placeholder file to ensure folder exists
            placeholder_path = f"user_folders/{user_id}/.placeholder"
            
            # Upload empty placeholder file
            result = self.client.storage.from_(self.bucket_name).upload(
                path=placeholder_path,
                file=b"",
                file_options={"content-type": "text/plain"}
            )
            
            logger.info(f"Created user folder for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating user folder for {user_id}: {e}")
            return False
    
    async def upload_file(
        self, 
        user_id: uuid.UUID,
        file_content: bytes,
        filename: str,
        content_type: str,
        original_filename: str
    ) -> Optional[Dict[str, Any]]:
        """
        Upload a file to user's folder in Supabase Storage.
        
        Args:
            user_id: UUID of the user
            file_content: Binary content of the file
            filename: Generated filename (with timestamp)
            content_type: MIME type of the file
            original_filename: Original filename from user
            
        Returns:
            Dict with file information or None if failed
        """
        try:
            # Generate storage path
            storage_path = f"user_folders/{user_id}/{filename}"
            
            # Upload to Supabase Storage
            result = self.client.storage.from_(self.bucket_name).upload(
                path=storage_path,
                file=file_content,
                file_options={
                    "content-type": content_type,
                    "cache-control": "3600"
                }
            )
            
            # Get signed URL for private bucket (valid for 1 hour)
            signed_url_response = self.client.storage.from_(self.bucket_name).create_signed_url(
                storage_path, 
                expires_in=3600  # 1 hour expiry
            )
            
            # For WhatsApp, we might need a longer-lived URL or use the service role
            public_url = signed_url_response.get('signedURL', '') if signed_url_response else ''
            
            file_info = {
                "storage_path": storage_path,
                "signed_url": public_url,
                "file_size": len(file_content),
                "content_type": content_type,
                "original_filename": original_filename,
                "upload_status": "completed"
            }
            
            logger.info(f"Successfully uploaded file {filename} for user {user_id}")
            return file_info
            
        except Exception as e:
            logger.error(f"Error uploading file {filename} for user {user_id}: {e}")
            return None
    
    async def download_file(self, user_id: uuid.UUID, filename: str) -> Optional[bytes]:
        """
        Download a file from user's folder.
        
        Args:
            user_id: UUID of the user
            filename: Name of the file to download
            
        Returns:
            File content as bytes or None if failed
        """
        try:
            storage_path = f"user_folders/{user_id}/{filename}"
            
            result = self.client.storage.from_(self.bucket_name).download(storage_path)
            
            if isinstance(result, bytes):
                return result
            else:
                logger.error(f"Failed to download file {filename}: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading file {filename} for user {user_id}: {e}")
            return None
    
    async def delete_file(self, user_id: uuid.UUID, filename: str) -> bool:
        """
        Delete a file from user's folder.
        
        Args:
            user_id: UUID of the user
            filename: Name of the file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            storage_path = f"user_folders/{user_id}/{filename}"
            
            result = self.client.storage.from_(self.bucket_name).remove([storage_path])
            
            if result:
                logger.info(f"Successfully deleted file {filename} for user {user_id}")
                return True
            else:
                logger.error(f"Failed to delete file {filename}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting file {filename} for user {user_id}: {e}")
            return False
    
    async def get_signed_url(self, user_id: uuid.UUID, filename: str, expires_in: int = 3600) -> Optional[str]:
        """
        Get a signed URL for accessing a private file.
        
        Args:
            user_id: UUID of the user
            filename: Name of the file
            expires_in: URL expiry time in seconds (default 1 hour)
            
        Returns:
            Signed URL string or None if failed
        """
        try:
            storage_path = f"user_folders/{user_id}/{filename}"
            
            signed_url_response = self.client.storage.from_(self.bucket_name).create_signed_url(
                storage_path, 
                expires_in=expires_in
            )
            
            if signed_url_response and 'signedURL' in signed_url_response:
                return signed_url_response['signedURL']
            else:
                logger.error(f"Failed to create signed URL for {filename}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating signed URL for {filename}: {e}")
            return None
    
    async def get_whatsapp_media_url(self, user_id: uuid.UUID, filename: str) -> Optional[str]:
        """
        Get a longer-lived signed URL suitable for WhatsApp media sharing.
        
        Args:
            user_id: UUID of the user
            filename: Name of the file
            
        Returns:
            Signed URL valid for 24 hours or None if failed
        """
        # WhatsApp might cache media, so we use a longer expiry
        return await self.get_signed_url(user_id, filename, expires_in=86400)  # 24 hours
    
    async def get_user_storage_usage(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get storage usage statistics for a user.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Dict with storage statistics
        """
        try:
            # This would typically involve querying the files table
            # For now, return a placeholder
            return {
                "total_files": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0.0,
                "images_count": 0,
                "audio_count": 0,
                "documents_count": 0,
                "videos_count": 0
            }
            
        except Exception as e:
            logger.error(f"Error getting storage usage for user {user_id}: {e}")
            return {}
    
    def generate_filename(self, original_filename: str, file_type: str) -> str:
        """
        Generate a unique filename for storage.
        
        Args:
            original_filename: Original filename from user
            file_type: Type of file (image, audio, document, video)
            
        Returns:
            Generated filename with timestamp and UUID
        """
        # Get file extension
        if "." in original_filename:
            extension = original_filename.split(".")[-1].lower()
        else:
            # Default extensions based on file type
            extensions = {
                "image": "jpg",
                "audio": "ogg",
                "document": "pdf",
                "video": "mp4"
            }
            extension = extensions.get(file_type, "bin")
        
        # Generate timestamp-based filename
        timestamp = int(datetime.now().timestamp())
        uuid_part = str(uuid.uuid4())[:8]
        
        return f"{timestamp}_{uuid_part}.{extension}"
    
    def get_file_type_from_mime(self, mime_type: str) -> str:
        """
        Determine file type from MIME type.
        
        Args:
            mime_type: MIME type of the file
            
        Returns:
            File type (image, audio, document, video)
        """
        if mime_type.startswith("image/"):
            return "image"
        elif mime_type.startswith("audio/"):
            return "audio"
        elif mime_type.startswith("video/"):
            return "video"
        else:
            return "document"
    
    async def create_storage_bucket(self) -> bool:
        """
        Create the storage bucket if it doesn't exist.
        
        Returns:
            True if bucket exists or was created successfully
        """
        try:
            # Try to get bucket info
            buckets = self.client.storage.list_buckets()
            
            bucket_exists = any(bucket.name == self.bucket_name for bucket in buckets)
            
            if not bucket_exists:
                # Create bucket
                result = self.client.storage.create_bucket(
                    self.bucket_name,
                    options={"public": False}  # Private bucket for security
                )
                
                if result:
                    logger.info(f"Created storage bucket: {self.bucket_name}")
                    return True
                else:
                    logger.error(f"Failed to create bucket: {self.bucket_name}")
                    return False
            else:
                logger.info(f"Storage bucket already exists: {self.bucket_name}")
                return True
                
        except Exception as e:
            logger.error(f"Error creating storage bucket: {e}")
            return False


# Utility functions for file processing
def save_temp_file(file_content: bytes, filename: str) -> str:
    """
    Save file temporarily for processing.
    
    Args:
        file_content: Binary content of the file
        filename: Name of the temporary file
        
    Returns:
        Path to the temporary file
    """
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    
    temp_path = os.path.join(temp_dir, filename)
    
    with open(temp_path, "wb") as f:
        f.write(file_content)
    
    return temp_path


def cleanup_temp_file(file_path: str) -> bool:
    """
    Clean up temporary file.
    
    Args:
        file_path: Path to the temporary file
        
    Returns:
        True if successful
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        return True
    except Exception as e:
        logger.error(f"Error cleaning up temp file {file_path}: {e}")
        return False


def get_max_file_size(file_type: str) -> int:
    """
    Get maximum allowed file size for different file types.
    
    Args:
        file_type: Type of file (image, audio, document, video)
        
    Returns:
        Maximum file size in bytes
    """
    max_sizes = {
        "image": 10 * 1024 * 1024,  # 10MB
        "audio": 25 * 1024 * 1024,  # 25MB
        "document": 20 * 1024 * 1024,  # 20MB
        "video": 50 * 1024 * 1024,  # 50MB
    }
    
    return max_sizes.get(file_type, 10 * 1024 * 1024)  # Default 10MB
