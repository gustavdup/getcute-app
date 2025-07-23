"""
AI-powered message classification service using OpenAI.
"""
import logging
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from openai import AsyncOpenAI
from src.config.settings import settings
from src.models.message_types import ClassificationResult

logger = logging.getLogger(__name__)


class MessageClassifier:
    """AI service for classifying and extracting information from messages."""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
    
    async def generate_completion(self, messages, max_tokens=500, temperature=0.1):
        """
        Generate a completion using OpenAI for general use by handlers.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            String response content
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            content = response.choices[0].message.content
            return content.strip() if content else ""
        except Exception as e:
            logger.error(f"OpenAI completion error: {e}")
            return None
    
    async def classify_message(self, content: str, user_context: Optional[Dict[str, Any]] = None) -> ClassificationResult:
        """
        Classify a message as note, reminder, birthday, or slash command.
        Extract relevant information based on the classification.
        """
        try:
            # Quick check for slash commands
            if content.strip().startswith('/'):
                return ClassificationResult(
                    message_type="slash_command",
                    confidence=1.0,
                    extracted_data={"command": content.strip().split()[0]},
                    requires_followup=False
                )
            
            # Quick check for tag-only messages (brain dump initiation)
            if self._is_tags_only(content):
                tags = self._extract_tags(content)
                return ClassificationResult(
                    message_type="brain_dump_start",
                    confidence=1.0,
                    extracted_data={"tags": tags},
                    requires_followup=False
                )
            
            # Use AI for complex classification
            system_prompt = self._get_classification_prompt()
            user_prompt = self._build_user_prompt(content, user_context)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            result_text = response.choices[0].message.content
            if not result_text or not result_text.strip():
                logger.warning("Empty response from OpenAI")
                return self._fallback_classification(content)
            
            # Clean up the response text - sometimes OpenAI adds extra characters or markdown
            result_text = result_text.strip()
            
            # Handle markdown code blocks
            if result_text.startswith('```json'):
                result_text = result_text[7:]  # Remove ```json
                if result_text.endswith('```'):
                    result_text = result_text[:-3]  # Remove closing ```
                result_text = result_text.strip()
            elif result_text.startswith('```'):
                result_text = result_text[3:]  # Remove opening ```
                if result_text.endswith('```'):
                    result_text = result_text[:-3]  # Remove closing ```
                result_text = result_text.strip()
                
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError as je:
                logger.warning(f"Could not parse AI response as JSON: {result_text[:100]}...")
                logger.error(f"Full JSON decode error: {je}")
                return self._fallback_classification(content)
            
            return ClassificationResult(
                message_type=result.get("message_type", "note"),
                confidence=float(result.get("confidence", 0.5)),
                extracted_data=result.get("extracted_data", {}),
                suggested_tags=result.get("suggested_tags", []),
                requires_followup=result.get("requires_followup", False),
                followup_type=result.get("followup_type")
            )
            
        except Exception as e:
            logger.error(f"Error in message classification: {e}")
            # Fallback to simple rule-based classification
            return self._fallback_classification(content)
    
    def _get_classification_prompt(self) -> str:
        """Get the system prompt for message classification."""
        return """You are an AI assistant that classifies WhatsApp messages for a personal productivity bot.

Classify messages into these types:
1. "note" - General information, thoughts, or content to save
2. "reminder" - Messages about future tasks or events with time/date references
3. "birthday" - Messages about someone's birthday with a person's name and date

IMPORTANT: Respond with valid JSON only, no markdown formatting or extra text.

{
    "message_type": "note|reminder|birthday",
    "confidence": 0.0-1.0,
    "extracted_data": {
        "title": "string",
        "description": "string"
    },
    "suggested_tags": ["tag1", "tag2"],
    "requires_followup": false,
    "followup_type": null
}

Rules:
- If message mentions time/date/scheduling: likely a reminder
- If message mentions person + birthday/bday/birth: likely a birthday
- If unclear, default to "note"
- Extract all hashtags as suggested_tags
- For reminders, parse natural language time expressions
- Use current context: """ + datetime.now().strftime("%Y-%m-%d %H:%M")
    
    def _build_user_prompt(self, content: str, context: Optional[Dict[str, Any]]) -> str:
        """Build the user prompt with message content and context."""
        prompt = f"Message to classify: {content}"
        
        if context:
            if context.get("recent_tags"):
                prompt += f"\nUser's recent tags: {', '.join(context['recent_tags'])}"
            if context.get("timezone"):
                prompt += f"\nUser timezone: {context['timezone']}"
        
        return prompt
    
    def _is_tags_only(self, content: str) -> bool:
        """Check if message contains only hashtags and looks like a brain dump session start."""
        # Remove whitespace and check if all words start with #
        words = content.strip().split()
        if not words or not all(word.startswith('#') for word in words):
            return False
        
        # Must have multiple tags (brain dumps typically use multiple tags)
        if len(words) < 2:
            return False
        
        # Additional context check - avoid misclassifying simple tag responses
        # Brain dumps typically have 2+ tags and often more meaningful combinations
        return len(words) >= 2
    
    def _extract_tags(self, content: str) -> List[str]:
        """Extract hashtags from content."""
        tags = re.findall(r'#(\w+)', content)
        return [tag.lower() for tag in tags]
    
    def _fallback_classification(self, content: str) -> ClassificationResult:
        """Simple rule-based fallback classification."""
        content_lower = content.lower()
        
        # Check for time/date keywords for reminders
        time_keywords = ['remind', 'at', 'tomorrow', 'today', 'next', 'every', 'daily', 'weekly', 'monthly']
        if any(keyword in content_lower for keyword in time_keywords):
            return ClassificationResult(
                message_type="reminder",
                confidence=0.6,
                extracted_data={"title": content, "needs_parsing": True},
                requires_followup=True,
                followup_type="time_clarification"
            )
        
        # Check for birthday keywords
        birthday_keywords = ['birthday', 'bday', 'birth']
        if any(keyword in content_lower for keyword in birthday_keywords):
            return ClassificationResult(
                message_type="birthday",
                confidence=0.6,
                extracted_data={"raw_text": content, "needs_parsing": True},
                requires_followup=True,
                followup_type="birthday_clarification"
            )
        
        # Default to note
        tags = self._extract_tags(content)
        return ClassificationResult(
            message_type="note",
            confidence=0.7,
            extracted_data={"content": content},
            suggested_tags=tags,
            requires_followup=len(tags) == 0  # Prompt for tags if none found
        )
    
    async def suggest_tags(self, content: str, user_tags: List[str]) -> List[str]:
        """Suggest relevant tags for content based on user's existing tags."""
        try:
            system_prompt = f"""Suggest 1-3 relevant hashtags for this content based on the user's existing tags.
            
User's existing tags: {', '.join(user_tags[:20])}

IMPORTANT: Respond with valid JSON array only, no markdown formatting.

["tag1", "tag2", "tag3"]

Only suggest existing tags or very obvious new ones."""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Content: {content}"}
                ],
                temperature=0.3,
                max_tokens=100
            )
            
            result_text = response.choices[0].message.content
            if not result_text:
                logger.warning("Empty response from OpenAI for tag suggestions")
                return []
            
            # Clean up markdown formatting
            result_text = result_text.strip()
            if result_text.startswith('```json'):
                result_text = result_text[7:]
                if result_text.endswith('```'):
                    result_text = result_text[:-3]
                result_text = result_text.strip()
            elif result_text.startswith('```'):
                result_text = result_text[3:]
                if result_text.endswith('```'):
                    result_text = result_text[:-3]
                result_text = result_text.strip()
                
            try:
                suggested_tags = json.loads(result_text)
            except json.JSONDecodeError as e:
                logger.warning(f"Could not parse tag suggestions as JSON: {result_text[:100]}...")
                return []
            
            return suggested_tags[:3]  # Limit to 3 suggestions
            
        except Exception as e:
            logger.error(f"Error suggesting tags: {e}")
            return []
    
    async def extract_search_intent(self, query: str) -> Dict[str, Any]:
        """Extract search intent and parameters from natural language query."""
        try:
            system_prompt = """Extract search intent from natural language queries.

IMPORTANT: Respond with valid JSON only, no markdown formatting.

{
    "search_type": "text|semantic|date_range|tag_filter",
    "query_terms": ["term1", "term2"],
    "filters": {
        "tags": ["tag1"],
        "date_range": {"start": "ISO_date", "end": "ISO_date"},
        "content_type": "text|image|audio|all"
    },
    "intent": "find_specific|browse_recent|search_concept"
}"""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Query: {query}"}
                ],
                temperature=0.1,
                max_tokens=300
            )
            
            result_text = response.choices[0].message.content
            if not result_text:
                logger.warning("Empty response from OpenAI for search intent")
                return {
                    "search_type": "text",
                    "query_terms": [query],
                    "filters": {},
                    "intent": "find_specific"
                }
            
            # Clean up markdown formatting
            result_text = result_text.strip()
            if result_text.startswith('```json'):
                result_text = result_text[7:]
                if result_text.endswith('```'):
                    result_text = result_text[:-3]
                result_text = result_text.strip()
            elif result_text.startswith('```'):
                result_text = result_text[3:]
                if result_text.endswith('```'):
                    result_text = result_text[:-3]
                result_text = result_text.strip()
                
            try:
                return json.loads(result_text)
            except json.JSONDecodeError as e:
                logger.warning(f"Could not parse search intent as JSON: {result_text[:100]}...")
                return {
                    "search_type": "text",
                    "query_terms": [query],
                    "filters": {},
                    "intent": "find_specific"
                }
            
        except Exception as e:
            logger.error(f"Error extracting search intent: {e}")
            return {
                "search_type": "text",
                "query_terms": [query],
                "filters": {},
                "intent": "find_specific"
            }
