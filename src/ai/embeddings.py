"""
AI service for creating vector embeddings using OpenAI.
"""
import logging
from typing import List, Optional
from openai import AsyncOpenAI
from src.config.settings import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for creating vector embeddings using OpenAI."""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = "text-embedding-3-small"  # 1536 dimensions
    
    async def create_embedding(self, text: str) -> Optional[List[float]]:
        """
        Create a vector embedding for the given text.
        
        Args:
            text: Text content to embed
            
        Returns:
            List of floats representing the embedding vector, or None on error
        """
        try:
            if not text or not text.strip():
                logger.warning("Empty text provided for embedding")
                return None
                
            # Clean the text
            clean_text = text.strip()
            if len(clean_text) > 8192:  # OpenAI's token limit
                clean_text = clean_text[:8192]
                
            response = await self.client.embeddings.create(
                model=self.model,
                input=clean_text,
                encoding_format="float"
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Created embedding with {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            logger.error(f"Error creating embedding: {e}")
            return None
    
    async def create_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Create embeddings for multiple texts in a batch (more efficient).
        
        Args:
            texts: List of text content to embed
            
        Returns:
            List of embedding vectors (or None for failures)
        """
        try:
            if not texts:
                return []
                
            # Clean texts and limit length
            clean_texts = []
            for text in texts:
                if text and text.strip():
                    clean_text = text.strip()
                    if len(clean_text) > 8192:
                        clean_text = clean_text[:8192]
                    clean_texts.append(clean_text)
                else:
                    clean_texts.append("")
                    
            if not any(clean_texts):
                logger.warning("No valid texts provided for batch embedding")
                return [None] * len(texts)
                
            response = await self.client.embeddings.create(
                model=self.model,
                input=clean_texts,
                encoding_format="float"
            )
            
            embeddings = [data.embedding if data else None for data in response.data]
            logger.debug(f"Created {len(embeddings)} embeddings in batch")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error creating batch embeddings: {e}")
            return [None] * len(texts)
