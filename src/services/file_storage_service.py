"""
File storage service for managing user media files.
Organizes files by user GUID in Supabase storage.
"""
import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from uuid import UUID, uuid4
import hashlib
from datetime import datetime, timezone
from supabase import create_client, Client
import io
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class FileStorageService:
    """Manages file storage using Supabase Storage organized by user GUID."""
    
    def __init__(self, storage_bucket: str = "user-media"):
        """Initialize file storage service.
        
        Args:
            storage_bucket: Supabase storage bucket name (default: "user-media")
        """
        self.storage_bucket = storage_bucket
        
        # Initialize Supabase client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not supabase_url or not supabase_service_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment variables")
        
        self.supabase: Client = create_client(supabase_url, supabase_service_key)
        self.ensure_storage_bucket()
        
        # Initialize database service for file records
        from src.services.supabase_service import SupabaseService
        self.db_service = SupabaseService()
    
    def ensure_storage_bucket(self):
        """Ensure the storage bucket exists."""
        try:
            # Try to list objects in the bucket to check if it exists
            result = self.supabase.storage.list_buckets()
            
            bucket_exists = False
            if result:
                for bucket in result:
                    if hasattr(bucket, 'name') and bucket.name == self.storage_bucket:
                        bucket_exists = True
                        break
                    elif isinstance(bucket, dict) and bucket.get('name') == self.storage_bucket:
                        bucket_exists = True
                        break
            
            if not bucket_exists:
                # Create the bucket with public read access for media files
                self.supabase.storage.create_bucket(
                    self.storage_bucket,
                    options={"public": False}  # Set to False for privacy, we'll generate signed URLs
                )
                logger.info(f"Created Supabase storage bucket: {self.storage_bucket}")
            else:
                logger.info(f"Supabase storage bucket exists: {self.storage_bucket}")
                
        except Exception as e:
            logger.error(f"Failed to ensure storage bucket exists: {e}")
            raise
    
    def get_user_folder_path(self, user_id: UUID) -> str:
        """Get the storage folder path for a user within the bucket.
        
        Args:
            user_id: User's UUID
            
        Returns:
            String path for the user's storage folder
        """
        return f"{user_id}"
    
    def generate_file_name(self, original_name: str, file_content: bytes) -> str:
        """Generate a unique filename using content hash and timestamp.
        
        Args:
            original_name: Original filename
            file_content: File content as bytes
            
        Returns:
            Generated unique filename
        """
        # Get file extension
        file_ext = Path(original_name).suffix.lower()
        
        # Create hash of content for uniqueness
        content_hash = hashlib.md5(file_content).hexdigest()[:8]
        
        # Create timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        
        # Combine into unique filename
        return f"{timestamp}_{content_hash}{file_ext}"
    
    async def save_file(self, user_id: UUID, filename: str, file_content: bytes, 
                       file_type: str = "unknown", message_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Save a file for a user to Supabase storage and create database record.
        
        Args:
            user_id: User's UUID
            filename: Original filename
            file_content: File content as bytes
            file_type: Type of file (image, audio, document, etc.)
            message_id: Optional message ID to associate with the file
            
        Returns:
            Dictionary with file info including path and metadata
        """
        try:
            # Import models here to avoid circular imports
            from src.models.database import File, FileType, UploadStatus, TranscriptionStatus
            
            # Get user folder path
            user_folder_path = self.get_user_folder_path(user_id)
            
            # Generate unique filename
            unique_filename = self.generate_file_name(filename, file_content)
            
            # Create full storage path: user_id/file_type/unique_filename
            storage_path = f"{user_folder_path}/{file_type}/{unique_filename}"
            
            # Upload file to Supabase storage
            result = self.supabase.storage.from_(self.storage_bucket).upload(
                path=storage_path,
                file=file_content,
                file_options={"content-type": self._get_content_type(filename, file_type)}
            )
            
            # Get file size
            file_size = len(file_content)
            
            # Generate public URL (or signed URL if bucket is private)
            public_url = self.supabase.storage.from_(self.storage_bucket).get_public_url(storage_path)
            
            # Map file_type string to FileType enum
            file_type_enum = FileType.DOCUMENT  # Default
            if file_type == "image":
                file_type_enum = FileType.IMAGE
            elif file_type == "audio":
                file_type_enum = FileType.AUDIO
            elif file_type == "video":
                file_type_enum = FileType.VIDEO
            elif file_type == "document":
                file_type_enum = FileType.DOCUMENT
            
            # Create file record in database
            file_record = File(
                id=uuid4(),
                user_id=user_id,
                message_id=message_id,
                filename=unique_filename,
                original_filename=filename,
                file_type=file_type_enum,
                mime_type=self._get_content_type(filename, file_type),
                file_size_bytes=file_size,
                storage_path=storage_path,
                storage_bucket=self.storage_bucket,
                upload_status=UploadStatus.COMPLETED,
                transcription_status=TranscriptionStatus.NOT_APPLICABLE if file_type != "audio" else TranscriptionStatus.PENDING,
                metadata={
                    "content_hash": hashlib.md5(file_content).hexdigest()
                },
                created_at=datetime.now(timezone.utc)
            )
            
            # Save file record to database
            saved_file_record = await self.db_service.save_file_record(file_record)
            
            # Create properly serialized database record (convert UUIDs to strings)
            database_record = saved_file_record.dict()
            if database_record.get('id'):
                database_record['id'] = str(database_record['id'])
            if database_record.get('user_id'):
                database_record['user_id'] = str(database_record['user_id'])
            if database_record.get('message_id'):
                database_record['message_id'] = str(database_record['message_id'])
            if database_record.get('created_at'):
                database_record['created_at'] = database_record['created_at'].isoformat() if hasattr(database_record['created_at'], 'isoformat') else database_record['created_at']
            if database_record.get('deleted_at'):
                database_record['deleted_at'] = database_record['deleted_at'].isoformat() if hasattr(database_record['deleted_at'], 'isoformat') else database_record['deleted_at']
            
            # Create file info for backward compatibility
            file_info = {
                "original_name": filename,
                "stored_name": unique_filename,
                "storage_path": storage_path,
                "public_url": public_url,
                "file_size": file_size,
                "file_type": file_type,
                "user_id": str(user_id),
                "bucket": self.storage_bucket,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "content_hash": hashlib.md5(file_content).hexdigest(),
                "file_id": str(saved_file_record.id),  # Include database record ID
                "database_record": database_record  # Include properly serialized database record
            }
            
            logger.info(f"File uploaded successfully to Supabase: {storage_path} ({file_size} bytes), DB record: {saved_file_record.id}")
            return file_info
            
        except Exception as e:
            logger.error(f"Error uploading file for user {user_id}: {e}")
            raise
    
    def _get_content_type(self, filename: str, file_type: str) -> str:
        """Get MIME content type based on filename and file type.
        
        Args:
            filename: Original filename
            file_type: Type of file (image, audio, document, etc.)
            
        Returns:
            MIME content type string
        """
        file_ext = Path(filename).suffix.lower()
        
        # Image types
        if file_type == "image" or file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            if file_ext in ['.jpg', '.jpeg']:
                return "image/jpeg"
            elif file_ext == '.png':
                return "image/png"
            elif file_ext == '.gif':
                return "image/gif"
            elif file_ext == '.webp':
                return "image/webp"
            else:
                return "image/jpeg"  # default
        
        # Audio types
        elif file_type == "audio" or file_ext in ['.mp3', '.wav', '.ogg', '.m4a', '.aac']:
            if file_ext == '.mp3':
                return "audio/mpeg"
            elif file_ext == '.wav':
                return "audio/wav"
            elif file_ext == '.ogg':
                return "audio/ogg"
            elif file_ext in ['.m4a', '.aac']:
                return "audio/aac"
            else:
                return "audio/mpeg"  # default
        
        # Document types
        elif file_type == "document":
            if file_ext == '.pdf':
                return "application/pdf"
            elif file_ext == '.doc':
                return "application/msword"
            elif file_ext == '.docx':
                return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            elif file_ext == '.txt':
                return "text/plain"
            else:
                return "application/octet-stream"
        
        return "application/octet-stream"

    async def get_file(self, user_id: UUID, storage_path: str) -> Optional[bytes]:
        """Retrieve a file for a user from Supabase storage.
        
        Args:
            user_id: User's UUID
            storage_path: Storage path to the file
            
        Returns:
            File content as bytes, or None if not found
        """
        try:
            # Security check: ensure the path starts with user's folder
            user_folder_path = self.get_user_folder_path(user_id)
            if not storage_path.startswith(user_folder_path):
                logger.warning(f"Attempted access outside user folder: {storage_path}")
                return None
            
            # Download file from Supabase storage
            result = self.supabase.storage.from_(self.storage_bucket).download(storage_path)
            
            if result:
                logger.info(f"File retrieved successfully: {storage_path}")
                return result
            else:
                logger.warning(f"File not found: {storage_path}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving file {storage_path} for user {user_id}: {e}")
            return None
    
    async def delete_file(self, user_id: UUID, storage_path: str) -> bool:
        """Delete a file for a user from Supabase storage.
        
        Args:
            user_id: User's UUID
            storage_path: Storage path to the file
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # Security check: ensure the path starts with user's folder
            user_folder_path = self.get_user_folder_path(user_id)
            if not storage_path.startswith(user_folder_path):
                logger.warning(f"Attempted deletion outside user folder: {storage_path}")
                return False
            
            # Delete file from Supabase storage
            result = self.supabase.storage.from_(self.storage_bucket).remove([storage_path])
            
            if result:
                logger.info(f"File deleted successfully: {storage_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {storage_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting file {storage_path} for user {user_id}: {e}")
            return False
    
    def get_user_storage_stats(self, user_id: UUID) -> Dict[str, Any]:
        """Get storage statistics for a user from Supabase storage.
        
        Args:
            user_id: User's UUID
            
        Returns:
            Dictionary with storage statistics
        """
        try:
            user_folder_path = self.get_user_folder_path(user_id)
            
            # List all files in user's folder
            result = self.supabase.storage.from_(self.storage_bucket).list(user_folder_path)
            
            total_files = 0
            total_size = 0
            file_types = {}
            
            if result:
                for item in result:
                    if isinstance(item, dict) and 'name' in item:
                        # This is a file (not a folder)
                        metadata = item.get('metadata')
                        if metadata and isinstance(metadata, dict) and 'size' in metadata:
                            total_files += 1
                            try:
                                file_size = int(metadata.get('size', 0))  # Use .get() instead of []
                                if file_size > 0:
                                    total_size += file_size
                                
                                    # Get file type from path
                                    file_path = item.get('name', '')
                                    path_parts = file_path.split('/')
                                    if len(path_parts) > 1:
                                        file_type = path_parts[-2]  # Parent folder name
                                        if file_type not in file_types:
                                            file_types[file_type] = {"count": 0, "size": 0}
                                        file_types[file_type]["count"] += 1
                                        file_types[file_type]["size"] += file_size
                            except (ValueError, TypeError):
                                # Skip files with invalid size metadata
                                continue
            
            return {
                "user_id": str(user_id),
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "file_types": file_types,
                "storage_path": f"{self.storage_bucket}/{user_folder_path}"
            }
            
        except Exception as e:
            logger.error(f"Error getting storage stats for user {user_id}: {e}")
            return {
                "user_id": str(user_id),
                "error": str(e)
            }
