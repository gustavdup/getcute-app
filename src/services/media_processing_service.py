"""
Media processing service for handling images, voice notes, and documents.
Includes file download, storage, transcription, and vector embedding creation.
"""
import os
import logging
import aiohttp
import asyncio
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timezone
import io
from PIL import Image
import openai

from ..services.file_storage_service import FileStorageService
from ..services.supabase_service import SupabaseService
from ..models.database import Message, MessageType, SourceType

logger = logging.getLogger(__name__)

# Configure OpenAI (will be loaded from config)
# openai.api_key = os.getenv("OPENAI_API_KEY")


class MediaProcessingService:
    """Handles processing of media files (images, audio, documents)."""
    
    def __init__(self):
        self.file_storage = FileStorageService()
        self.db_service = SupabaseService()
        
        # Supported file types
        self.image_types = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
        self.audio_types = {'.mp3', '.wav', '.m4a', '.ogg', '.aac', '.opus'}
        self.document_types = {'.pdf', '.doc', '.docx', '.txt', '.rtf'}
    
    async def download_whatsapp_media(self, media_id: str, access_token: str) -> Optional[bytes]:
        """Download media file from WhatsApp API.
        
        Args:
            media_id: WhatsApp media ID
            access_token: WhatsApp API access token
            
        Returns:
            File content as bytes, or None if download failed
        """
        try:
            # Step 1: Get media URL
            async with aiohttp.ClientSession() as session:
                url = f"https://graph.facebook.com/v18.0/{media_id}"
                headers = {"Authorization": f"Bearer {access_token}"}
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        media_info = await response.json()
                        media_url = media_info.get('url')
                        
                        if not media_url:
                            logger.error(f"No URL found in media info: {media_info}")
                            return None
                    else:
                        logger.error(f"Failed to get media URL: {response.status}")
                        return None
                
                # Step 2: Download the actual file
                async with session.get(media_url, headers=headers) as response:
                    if response.status == 200:
                        file_content = await response.read()
                        logger.info(f"Downloaded media file: {len(file_content)} bytes")
                        return file_content
                    else:
                        logger.error(f"Failed to download media file: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error downloading WhatsApp media {media_id}: {e}")
            return None
    
    def detect_file_type(self, filename: str, file_content: bytes) -> str:
        """Detect file type based on filename and content.
        
        Args:
            filename: Original filename
            file_content: File content as bytes
            
        Returns:
            File type category (image, audio, document, unknown)
        """
        # Get file extension
        file_ext = os.path.splitext(filename.lower())[1]
        
        # Check by extension
        if file_ext in self.image_types:
            return "image"
        elif file_ext in self.audio_types:
            return "audio"
        elif file_ext in self.document_types:
            return "document"
        
        # Check by content (magic bytes)
        if len(file_content) >= 4:
            magic = file_content[:4]
            
            # Image magic bytes
            if magic.startswith(b'\xff\xd8\xff'):  # JPEG
                return "image"
            elif magic.startswith(b'\x89PNG'):  # PNG
                return "image"
            elif magic.startswith(b'GIF8'):  # GIF
                return "image"
            elif magic.startswith(b'RIFF'):  # Could be WAV or WEBP
                if b'WEBP' in file_content[:12]:
                    return "image"
                elif b'WAVE' in file_content[:12]:
                    return "audio"
            elif magic.startswith(b'ID3') or magic.startswith(b'\xff\xfb'):  # MP3
                return "audio"
        
        return "unknown"
    
    async def process_image(self, user_id: UUID, filename: str, file_content: bytes,
                           caption: Optional[str] = None) -> Dict[str, Any]:
        """Process an image file.
        
        Args:
            user_id: User's UUID
            filename: Original filename
            file_content: File content as bytes
            caption: Optional caption/description
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Save file to storage
            file_info = await self.file_storage.save_file(
                user_id=user_id,
                filename=filename,
                file_content=file_content,
                file_type="image"
            )
            
            # Get image metadata
            try:
                image = Image.open(io.BytesIO(file_content))
                metadata = {
                    "width": image.width,
                    "height": image.height,
                    "format": image.format,
                    "mode": image.mode
                }
            except Exception as e:
                logger.warning(f"Could not extract image metadata: {e}")
                metadata = {}
            
            # Create content for vector embedding
            content_for_embedding = f"Image: {filename}"
            if caption:
                content_for_embedding += f" - {caption}"
            
            # Generate vector embedding
            vector_embedding = await self.generate_vector_embedding(content_for_embedding)
            
            result = {
                "type": "image",
                "file_info": file_info,
                "metadata": metadata,
                "content": caption or f"Image: {filename}",
                "vector_embedding": vector_embedding,
                "processed_at": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Image processed successfully: {filename}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing image {filename}: {e}")
            raise
    
    async def process_audio(self, user_id: UUID, filename: str, file_content: bytes) -> Dict[str, Any]:
        """Process an audio file (voice note).
        
        Args:
            user_id: User's UUID
            filename: Original filename
            file_content: File content as bytes
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Save file to storage
            file_info = await self.file_storage.save_file(
                user_id=user_id,
                filename=filename,
                file_content=file_content,
                file_type="audio"
            )
            
            # Transcribe audio using OpenAI Whisper
            transcription = await self.transcribe_audio(file_content, filename)
            
            # Create content for vector embedding
            content_for_embedding = transcription or f"Voice note: {filename}"
            
            # Generate vector embedding
            vector_embedding = await self.generate_vector_embedding(content_for_embedding)
            
            result = {
                "type": "audio",
                "file_info": file_info,
                "transcription": transcription,
                "content": transcription or f"Voice note: {filename}",
                "vector_embedding": vector_embedding,
                "processed_at": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Audio processed successfully: {filename}, transcription length: {len(transcription or '')}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing audio {filename}: {e}")
            raise
    
    async def process_document(self, user_id: UUID, filename: str, file_content: bytes) -> Dict[str, Any]:
        """Process a document file.
        
        Args:
            user_id: User's UUID
            filename: Original filename
            file_content: File content as bytes
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Save file to storage
            file_info = await self.file_storage.save_file(
                user_id=user_id,
                filename=filename,
                file_content=file_content,
                file_type="document"
            )
            
            # Try to extract text content (basic implementation)
            extracted_text = await self.extract_document_text(file_content, filename)
            
            # Create content for vector embedding
            content_for_embedding = extracted_text or f"Document: {filename}"
            
            # Generate vector embedding
            vector_embedding = await self.generate_vector_embedding(content_for_embedding)
            
            result = {
                "type": "document",
                "file_info": file_info,
                "extracted_text": extracted_text,
                "content": extracted_text or f"Document: {filename}",
                "vector_embedding": vector_embedding,
                "processed_at": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Document processed successfully: {filename}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing document {filename}: {e}")
            raise
    
    async def transcribe_audio(self, file_content: bytes, filename: str) -> Optional[str]:
        """Transcribe audio using OpenAI Whisper API.
        
        Args:
            file_content: Audio file content as bytes
            filename: Original filename
            
        Returns:
            Transcription text, or None if failed
        """
        try:
            # For now, return a placeholder - would implement OpenAI Whisper API call
            logger.info(f"Transcribing audio file: {filename}")
            
            # TODO: Implement actual OpenAI Whisper API call
            # This would involve:
            # 1. Creating a temporary file or using BytesIO
            # 2. Calling openai.Audio.transcribe()
            # 3. Returning the transcription text
            
            # Placeholder implementation
            return f"[Transcription placeholder for {filename}]"
            
        except Exception as e:
            logger.error(f"Error transcribing audio {filename}: {e}")
            return None
    
    async def extract_document_text(self, file_content: bytes, filename: str) -> Optional[str]:
        """Extract text from document file.
        
        Args:
            file_content: Document file content as bytes
            filename: Original filename
            
        Returns:
            Extracted text, or None if failed
        """
        try:
            file_ext = os.path.splitext(filename.lower())[1]
            
            if file_ext == '.txt':
                # Simple text file
                return file_content.decode('utf-8', errors='ignore')
            else:
                # TODO: Implement extraction for PDF, DOC, DOCX files
                # This would require additional libraries like PyPDF2, python-docx, etc.
                logger.info(f"Document text extraction not implemented for {file_ext}")
                return f"Document: {filename} (text extraction not implemented)"
                
        except Exception as e:
            logger.error(f"Error extracting text from {filename}: {e}")
            return None
    
    async def generate_vector_embedding(self, text: str) -> Optional[List[float]]:
        """Generate vector embedding for text using OpenAI.
        
        Args:
            text: Text to embed
            
        Returns:
            Vector embedding as list of floats, or None if failed
        """
        try:
            # TODO: Implement actual OpenAI embeddings API call
            # This would involve calling openai.Embedding.create()
            
            logger.info(f"Generating vector embedding for text: {text[:50]}...")
            
            # Placeholder implementation - would return actual embeddings
            # return openai.Embedding.create(input=text, model="text-embedding-ada-002")['data'][0]['embedding']
            
            # For now, return None to indicate no embedding
            return None
            
        except Exception as e:
            logger.error(f"Error generating vector embedding: {e}")
            return None
    
    async def process_media_message(self, user_id: UUID, media_id: str, filename: str,
                                  access_token: str, caption: Optional[str] = None) -> Message:
        """Process a media message from WhatsApp.
        
        Args:
            user_id: User's UUID
            media_id: WhatsApp media ID
            filename: Original filename
            access_token: WhatsApp API access token
            caption: Optional caption/description
            
        Returns:
            Message object with media processing results
        """
        try:
            # Download the file
            file_content = await self.download_whatsapp_media(media_id, access_token)
            if not file_content:
                raise Exception("Failed to download media file")
            
            # Detect file type
            file_type = self.detect_file_type(filename, file_content)
            
            # Process based on type (without saving to database yet)
            if file_type == "image":
                processing_result = await self.process_image(user_id, filename, file_content, caption)
                source_type = SourceType.IMAGE
                message_type = MessageType.NOTE
            elif file_type == "audio":
                processing_result = await self.process_audio(user_id, filename, file_content)
                source_type = SourceType.AUDIO
                message_type = MessageType.NOTE
            elif file_type == "document":
                processing_result = await self.process_document(user_id, filename, file_content)
                source_type = SourceType.DOCUMENT
                message_type = MessageType.NOTE
            else:
                # Unknown file type - still save it
                file_info = await self.file_storage.save_file(
                    user_id=user_id,
                    filename=filename,
                    file_content=file_content,
                    file_type="unknown"
                )
                processing_result = {
                    "type": "unknown",
                    "file_info": file_info,
                    "content": f"File: {filename}",
                    "vector_embedding": None
                }
                source_type = SourceType.DOCUMENT
                message_type = MessageType.NOTE
            
            # Create message object
            message = Message(
                user_id=user_id,
                message_timestamp=datetime.now(timezone.utc),
                type=message_type,
                content=processing_result["content"],
                tags=[],  # Will be extracted from caption or content
                source_type=source_type,
                vector_embedding=processing_result.get("vector_embedding"),
                transcription=processing_result.get("transcription"),
                media_url=processing_result["file_info"]["public_url"],  # Updated for Supabase storage
                metadata={
                    "original_filename": filename,
                    "file_type": file_type,
                    "file_size": processing_result["file_info"]["file_size"],
                    "storage_path": processing_result["file_info"]["storage_path"],  # Store Supabase path
                    "bucket": processing_result["file_info"]["bucket"],  # Store bucket name
                    "file_id": processing_result["file_info"].get("file_id"),  # Store file database record ID
                    "processing_result": processing_result
                }
            )
            
            logger.info(f"Media message processed successfully: {filename} ({file_type})")
            return message
            
        except Exception as e:
            logger.error(f"Error processing media message {filename}: {e}")
            raise
    
    async def update_file_message_association(self, file_id: UUID, message_id: UUID) -> bool:
        """Update file record with associated message ID after message is saved.
        
        Args:
            file_id: File record ID
            message_id: Message ID to associate with
            
        Returns:
            True if update was successful
        """
        try:
            # Initialize database service if not already done
            if not hasattr(self, 'db_service'):
                from src.services.supabase_service import SupabaseService
                self.db_service = SupabaseService()
            
            # Update the file record with the message ID
            result = self.db_service.admin_client.table("files").update({
                "message_id": str(message_id)
            }).eq("id", str(file_id)).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error updating file-message association: {e}")
            return False
