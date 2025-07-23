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

from src.services.file_storage_service import FileStorageService
from src.services.supabase_service import SupabaseService
from src.models.database import Message, MessageType, SourceType

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
    
    async def download_whatsapp_media(self, media_id: str, access_token: str) -> Optional[Dict[str, Any]]:
        """Download media file from WhatsApp API.
        
        Args:
            media_id: WhatsApp media ID
            access_token: WhatsApp API access token
            
        Returns:
            Dictionary with file content, mime_type, and metadata, or None if download failed
        """
        try:
            # Step 1: Get media URL and metadata
            async with aiohttp.ClientSession() as session:
                url = f"https://graph.facebook.com/v18.0/{media_id}"
                headers = {"Authorization": f"Bearer {access_token}"}
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        media_info = await response.json()
                        media_url = media_info.get('url')
                        mime_type = media_info.get('mime_type')
                        file_size = media_info.get('file_size')
                        
                        logger.info(f"WhatsApp media info - MIME: {mime_type}, Size: {file_size}")
                        
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
                        logger.info(f"Downloaded media file: {len(file_content)} bytes, MIME: {mime_type}")
                        
                        return {
                            "content": file_content,
                            "mime_type": mime_type,
                            "file_size": file_size,
                            "media_id": media_id
                        }
                    else:
                        logger.error(f"Failed to download media file: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error downloading WhatsApp media {media_id}: {e}")
            return None
    
    def detect_file_type(self, filename: str, file_content: bytes, mime_type: Optional[str] = None) -> str:
        """Detect file type based on filename, content, and mime type.
        
        Args:
            filename: Original filename
            file_content: File content as bytes
            mime_type: MIME type from WhatsApp API
            
        Returns:
            File type category (image, audio, document, unknown)
        """
        # First check mime type (most reliable for WhatsApp media)
        if mime_type:
            if mime_type.startswith('audio/'):
                return "audio"
            elif mime_type.startswith('image/'):
                return "image"
            elif mime_type.startswith('application/') and any(doc_type in mime_type for doc_type in ['pdf', 'document', 'msword']):
                return "document"
        
        # Fallback to extension
        file_ext = os.path.splitext(filename.lower())[1]
        
        # Check by extension
        if file_ext in self.image_types:
            return "image"
        elif file_ext in self.audio_types:
            return "audio"
        elif file_ext in self.document_types:
            return "document"
        
        # Check by content (magic bytes) for unknown extensions
        if file_content:
            # OGG audio files start with "OggS"
            if file_content.startswith(b'OggS'):
                return "audio"
            # M4A files (used by WhatsApp voice notes)
            elif file_content[4:8] == b'ftyp' and b'M4A' in file_content[:20]:
                return "audio"
            # MP3 files
            elif file_content.startswith(b'ID3') or file_content.startswith(b'\xff\xfb'):
                return "audio"
            # JPEG
            elif file_content.startswith(b'\xff\xd8\xff'):
                return "image"
            # PNG
            elif file_content.startswith(b'\x89PNG'):
                return "image"
        
        return "unknown"
        
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
            
            # Generate AI description of the image using GPT-4V
            ai_description = await self.analyze_image_content(file_content, filename)
            
            # Create content for vector embedding
            content_for_embedding = f"Image: {filename}"
            if caption:
                content_for_embedding += f" - {caption}"
            if ai_description:
                content_for_embedding += f" - AI Analysis: {ai_description}"
            
            # Generate vector embedding
            vector_embedding = await self.generate_vector_embedding(content_for_embedding)
            
            result = {
                "type": "image",
                "file_info": file_info,
                "metadata": metadata,
                "content": caption or f"Image: {filename}",
                "ai_description": ai_description,
                "vector_embedding": vector_embedding,
                "processed_at": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Image processed successfully: {filename}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing image {filename}: {e}")
            raise
    
    async def analyze_image_content(self, file_content: bytes, filename: str) -> Optional[str]:
        """Analyze image content using OpenAI GPT-4V for AI description.
        
        Args:
            file_content: Image file content as bytes
            filename: Original filename
            
        Returns:
            AI-generated description of the image, or None if failed
        """
        try:
            logger.info(f"Analyzing image content for: {filename}")
            
            # Import OpenAI client
            from openai import OpenAI
            import base64
            import os
            
            # Initialize OpenAI client
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            # Convert image to base64
            base64_image = base64.b64encode(file_content).decode('utf-8')
            
            # Get the image format for the data URL
            image_format = "jpeg"  # Default
            if filename.lower().endswith('.png'):
                image_format = "png"
            elif filename.lower().endswith('.gif'):
                image_format = "gif"
            elif filename.lower().endswith('.webp'):
                image_format = "webp"
            
            # Analyze image using GPT-4V
            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL_IMAGE_RECOGNITION", "gpt-4o"),
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Please analyze this image and provide a detailed description of what you see. Include objects, people, activities, colors, setting, and any text visible in the image. Keep it concise but informative."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/{image_format};base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )
            
            # Extract the description
            description = None
            if response.choices and response.choices[0].message.content:
                description = response.choices[0].message.content.strip()
            
            if description:
                logger.info(f"Successfully analyzed image: {len(description)} characters")
                return description
            else:
                logger.warning(f"Empty description for image: {filename}")
                return None
                
        except Exception as e:
            logger.error(f"Error analyzing image content {filename}: {e}")
            return None
    
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
            logger.info(f"Processing audio file: {filename} ({len(file_content)} bytes)")
            
            # Save file to storage
            file_info = await self.file_storage.save_file(
                user_id=user_id,
                filename=filename,
                file_content=file_content,
                file_type="audio"
            )
            logger.info(f"Audio file saved to storage: {file_info.get('public_url', 'No URL')}")
            
            # Transcribe audio using OpenAI Whisper
            logger.info("Starting audio transcription with OpenAI Whisper...")
            transcription = await self.transcribe_audio(file_content, filename)
            
            if transcription:
                logger.info(f"Transcription successful: {len(transcription)} characters")
                logger.debug(f"Transcription text: {transcription[:100]}...")
            else:
                logger.warning("Transcription failed or returned empty result")
            
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
            logger.info(f"Transcribing audio file: {filename} ({len(file_content)} bytes)")
            
            # Import OpenAI client
            from openai import OpenAI
            import tempfile
            import os
            
            # Initialize OpenAI client
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            # Create a temporary file for the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix=self._get_audio_extension(filename)) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                # Transcribe using OpenAI Whisper
                with open(temp_file_path, "rb") as audio_file:
                    transcript = client.audio.transcriptions.create(
                        model=os.getenv("OPENAI_MODEL_VTT", "whisper-1"),
                        file=audio_file,
                        response_format="text"
                    )
                
                # Clean up transcription text
                transcription_text = transcript.strip() if transcript else ""
                
                if transcription_text:
                    logger.info(f"Successfully transcribed audio: {len(transcription_text)} characters")
                    return transcription_text
                else:
                    logger.warning(f"Empty transcription for {filename}")
                    return None
                    
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except Exception as cleanup_error:
                    logger.warning(f"Could not delete temp file {temp_file_path}: {cleanup_error}")
            
        except Exception as e:
            logger.error(f"Error transcribing audio {filename}: {e}")
            return None
    
    def _generate_filename_with_extension(self, filename: str, mime_type: Optional[str]) -> str:
        """Generate appropriate filename with extension based on MIME type.
        
        Args:
            filename: Base filename without extension
            mime_type: MIME type from WhatsApp API
            
        Returns:
            Filename with appropriate extension
        """
        # If filename already has an extension, keep it
        if '.' in filename and not filename.endswith('.'):
            return filename
        
        # Add extension based on MIME type
        if mime_type:
            if mime_type.startswith('audio/'):
                # Audio files
                if 'ogg' in mime_type:
                    return f"{filename}.ogg"
                elif 'mpeg' in mime_type or 'mp3' in mime_type:
                    return f"{filename}.mp3"
                elif 'm4a' in mime_type or 'mp4' in mime_type:
                    return f"{filename}.m4a"
                elif 'wav' in mime_type:
                    return f"{filename}.wav"
                else:
                    return f"{filename}.ogg"  # Default for WhatsApp voice notes
                    
            elif mime_type.startswith('image/'):
                # Image files
                if 'jpeg' in mime_type or 'jpg' in mime_type:
                    return f"{filename}.jpg"
                elif 'png' in mime_type:
                    return f"{filename}.png"
                elif 'gif' in mime_type:
                    return f"{filename}.gif"
                elif 'webp' in mime_type:
                    return f"{filename}.webp"
                else:
                    return f"{filename}.jpg"  # Default for images
                    
            elif mime_type.startswith('application/'):
                # Document files
                if 'pdf' in mime_type:
                    return f"{filename}.pdf"
                elif 'msword' in mime_type or 'document' in mime_type:
                    if 'wordprocessingml' in mime_type:
                        return f"{filename}.docx"
                    else:
                        return f"{filename}.doc"
                elif 'spreadsheet' in mime_type or 'excel' in mime_type:
                    if 'spreadsheetml' in mime_type:
                        return f"{filename}.xlsx"
                    else:
                        return f"{filename}.xls"
                elif 'presentation' in mime_type or 'powerpoint' in mime_type:
                    if 'presentationml' in mime_type:
                        return f"{filename}.pptx"
                    else:
                        return f"{filename}.ppt"
                elif 'zip' in mime_type:
                    return f"{filename}.zip"
                elif 'text' in mime_type:
                    return f"{filename}.txt"
                else:
                    return f"{filename}.bin"  # Generic binary file
                    
            elif mime_type.startswith('text/'):
                # Text files
                if 'plain' in mime_type:
                    return f"{filename}.txt"
                elif 'csv' in mime_type:
                    return f"{filename}.csv"
                else:
                    return f"{filename}.txt"
                    
            elif mime_type.startswith('video/'):
                # Video files
                if 'mp4' in mime_type:
                    return f"{filename}.mp4"
                elif 'mpeg' in mime_type:
                    return f"{filename}.mpg"
                elif 'avi' in mime_type:
                    return f"{filename}.avi"
                elif 'mov' in mime_type:
                    return f"{filename}.mov"
                else:
                    return f"{filename}.mp4"  # Default for videos
        
        # If no MIME type or unrecognized, return original filename
        return filename
    
    def _get_audio_extension(self, filename: str) -> str:
        """Get appropriate audio file extension."""
        # WhatsApp typically sends voice notes as .ogg or .m4a
        if filename.lower().endswith(('.ogg', '.m4a', '.mp3', '.wav')):
            return os.path.splitext(filename)[1]
        else:
            # Default to .ogg for WhatsApp voice notes
            return '.ogg'
    
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
            # Download the file with metadata
            download_result = await self.download_whatsapp_media(media_id, access_token)
            if not download_result:
                raise Exception("Failed to download media file")
            
            file_content = download_result["content"]
            mime_type = download_result.get("mime_type")
            file_size = download_result.get("file_size")
            
            # Generate appropriate filename with extension based on mime type
            filename = self._generate_filename_with_extension(filename, mime_type)
            
            logger.info(f"Processing media: {filename}, MIME: {mime_type}, Size: {file_size}")
            
            # Detect file type using enhanced detection
            file_type = self.detect_file_type(filename, file_content, mime_type)
            
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
