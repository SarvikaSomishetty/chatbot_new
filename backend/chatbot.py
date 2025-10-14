"""
Chatbot module with Gemini AI integration
Handles domain-specific conversations and stores chat history in MongoDB
"""
import os
import json
from datetime import datetime
import asyncio
from typing import Dict, List, Optional
import google.generativeai as genai
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase
import redis
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY not found in environment variables")
    print("Please set your Gemini API key in the .env file")
    GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"

genai.configure(api_key=GEMINI_API_KEY)

# Domain-specific contexts (restricted to required domains only)
DOMAIN_CONTEXTS = {
    "Customer Support": """
    You are a professional customer support AI assistant specializing in:
    - Product support and troubleshooting
    - Account management and billing inquiries
    - Service requests and escalations
    - Policy explanations and procedures
    - General customer service inquiries
    - Refund and return processes
    - Order status and shipping information
    
    Always be helpful, empathetic, and solution-oriented. Provide clear, actionable responses.
    If you cannot resolve an issue, guide the user to the appropriate escalation path.
    """,

    "Technical Support": """
    You are a technical support AI assistant expert in:
    - System diagnostics and troubleshooting
    - Software installation and configuration
    - Network connectivity and performance issues
    - Hardware problems and maintenance
    - Technical documentation and user guides
    - Error message interpretation
    - Performance optimization
    
    Provide step-by-step technical solutions with clear explanations.
    Always verify the user's technical level and adjust your explanations accordingly.
    """,

    "Finance": """
    You are an expert financial AI assistant covering:
    - Personal finance and budgeting advice
    - Investment strategies and risk management
    - Banking services and account management
    - Insurance and financial planning
    - Economic trends and market analysis
    - Tax planning and preparation guidance
    - Credit and loan information
    
    Provide clear, practical financial guidance while always noting that this is not professional financial advice.
    Recommend consulting with qualified financial professionals for complex matters.
    """,

    "Travel": """
    You are a travel AI assistant specializing in:
    - Travel planning and booking assistance
    - Destination information and recommendations
    - Travel documentation and visa requirements
    - Transportation options and routes
    - Accommodation suggestions and booking
    - Travel safety tips and advisories
    - Local customs and cultural information
    - Weather and seasonal considerations
    
    Help users plan safe, enjoyable, and memorable travel experiences.
    Always provide up-to-date information and remind users to verify details independently.
    """
}

class ChatQuery(BaseModel):
    user_id: str
    domain: str
    question: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    conversation_id: str
    domain: str
    timestamp: str

class ChatHistory(BaseModel):
    conversation_id: str
    user_id: str
    domain: str
    messages: List[Dict]
    created_at: datetime
    updated_at: datetime

class GeminiChatbot:
    def __init__(self, mongo_db: AsyncIOMotorDatabase, redis_client: Optional[redis.Redis] = None):
        self.mongo_db = mongo_db
        self.redis_client = redis_client
        self.model = genai.GenerativeModel('gemini-2.5-pro')
    
    async def ask_llm(self, prompt: str, temperature: float = 0.7) -> str:
        """Ask Gemini AI with a text prompt"""
        try:
            gen_kwargs = {
                'generation_config': {
                    'temperature': temperature,
                    'max_output_tokens': 2000,  # Increased from 1000
                    'top_p': 0.8,
                    'top_k': 40
                }
            }

            async def _call_gen():
                return await asyncio.to_thread(self.model.generate_content, prompt, **gen_kwargs)

            # Try once with timeout, then one retry
            try:
                response = await asyncio.wait_for(_call_gen(), timeout=20.0)
            except Exception:
                response = await asyncio.wait_for(_call_gen(), timeout=20.0)
            
            # Safely extract text from response - handle both simple and multi-part responses
            try:
                # First try the simple text accessor
                if hasattr(response, 'text') and response.text:
                    return response.text
            except Exception as e:
                print(f"Error accessing response.text: {e}")

            # Fallback: extract text from parts (for multi-part responses)
            parts = []
            try:
                # Check if response has candidates
                if hasattr(response, 'candidates') and response.candidates:
                    for candidate in response.candidates:
                        if hasattr(candidate, 'content') and candidate.content:
                            if hasattr(candidate.content, 'parts') and candidate.content.parts:
                                for part in candidate.content.parts:
                                    if hasattr(part, 'text') and part.text:
                                        parts.append(part.text)
                        # Check for finish_reason to handle truncated responses
                        if hasattr(candidate, 'finish_reason'):
                            finish_reason = candidate.finish_reason
                            if finish_reason == 'MAX_TOKENS':
                                print("Response truncated due to token limit")
                            elif finish_reason == 'SAFETY':
                                print("Response blocked due to safety concerns")
                # Alternative: check if response has parts directly
                elif hasattr(response, 'parts') and response.parts:
                    for part in response.parts:
                        if hasattr(part, 'text') and part.text:
                            parts.append(part.text)
            except Exception as e:
                print(f"Error extracting parts: {e}")

            if parts:
                return "\n".join(parts)

            # If we still don't have text, try to get any text content
            try:
                if hasattr(response, 'result') and response.result:
                    if hasattr(response.result, 'text'):
                        return response.result.text
                    elif hasattr(response.result, 'parts'):
                        text_parts = [p.text for p in response.result.parts if hasattr(p, 'text') and p.text]
                        if text_parts:
                            return "\n".join(text_parts)
            except Exception as e:
                print(f"Error accessing response.result: {e}")

            return "I apologize, but I'm experiencing technical difficulties. Please try again later."
        except Exception as e:
            print(f"Error in ask_llm: {e}")
            return f"I apologize, but I'm experiencing technical difficulties. Please try again later. Error: {str(e)}"
    
    async def get_conversation_history(self, conversation_id: str) -> List[Dict]:
        """Get conversation history from MongoDB"""
        try:
            conversation = await self.mongo_db.conversations.find_one({
                "conversation_id": conversation_id
            })
            return conversation.get("messages", []) if conversation else []
        except Exception as e:
            print(f"Error fetching conversation history: {e}")
            return []
    
    async def save_conversation(self, conversation_id: str, user_id: str, domain: str, messages: List[Dict]):
        """Save conversation to MongoDB"""
        try:
            conversation_data = {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "domain": domain,
                "messages": messages,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await self.mongo_db.conversations.update_one(
                {"conversation_id": conversation_id},
                {"$set": conversation_data},
                upsert=True
            )
            
            print(f"Saved conversation {conversation_id} to MongoDB - Domain: {domain}, Messages: {len(messages)}")
            
            # Also cache recent messages in Redis for fast access (if Redis is available)
            if self.redis_client:
                await self.cache_recent_messages(conversation_id, messages[-10:])  # Last 10 messages
                print(f"Cached recent messages for conversation {conversation_id} in Redis")
            
        except Exception as e:
            print(f"Error saving conversation: {e}")
    
    async def cache_recent_messages(self, conversation_id: str, messages: List[Dict]):
        """Cache recent messages in Redis for fast access"""
        if not self.redis_client:
            return
        try:
            redis_key = f"chat:{conversation_id}"
            # Clear existing cache and add recent messages
            self.redis_client.delete(redis_key)
            for message in messages:
                self.redis_client.rpush(redis_key, json.dumps(message))
            # Set expiration to 24 hours
            self.redis_client.expire(redis_key, 86400)
        except Exception as e:
            print(f"Error caching messages in Redis: {e}")
    
    async def get_cached_messages(self, conversation_id: str) -> List[Dict]:
        """Get cached messages from Redis"""
        if not self.redis_client:
            return []
        try:
            redis_key = f"chat:{conversation_id}"
            messages = self.redis_client.lrange(redis_key, 0, -1)
            return [json.loads(msg) for msg in messages]
        except Exception as e:
            print(f"Error getting cached messages: {e}")
            return []
    
    async def process_query(self, query: ChatQuery) -> ChatResponse:
        """Process a chat query and return AI response"""
        try:
            # Map domain ID to domain name (restricted)
            domain_mapping = {
                'customer-support': 'Customer Support',
                'technical-support': 'Technical Support', 
                'finance': 'Finance',
                'travel': 'Travel'
            }
            
            domain_name = domain_mapping.get(query.domain, query.domain)
            
            # Get domain context
            domain_context = DOMAIN_CONTEXTS.get(domain_name, "")
            if not domain_context:
                return ChatResponse(
                    answer=f"I'm sorry, but I don't have expertise in the {query.domain} domain. Please select a supported domain.",
                    conversation_id=query.conversation_id or f"conv_{query.user_id}_{int(datetime.utcnow().timestamp())}",
                    domain=query.domain,
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Generate conversation ID if not provided
            conversation_id = query.conversation_id or f"conv_{query.user_id}_{int(datetime.utcnow().timestamp())}"
            
            # Get conversation history
            history = await self.get_conversation_history(conversation_id)
            
            # Build context from recent conversation
            context_messages = ""
            if history:
                recent_messages = history[-6:]  # Last 6 messages for context
                context_messages = "\n".join([
                    f"{msg.get('role', 'user').title()}: {msg.get('content', '')}" 
                    for msg in recent_messages
                ])
            
            # Create the prompt
            prompt = f"""
{domain_context}

Previous conversation context:
{context_messages}

Current question: {query.question}

Please provide a helpful, accurate, and concise response. Keep your answer focused and practical. If the question is outside your domain expertise, politely redirect to the appropriate domain or suggest contacting a human specialist.
"""
            
            # Get AI response
            answer = await self.ask_llm(prompt)
            
            # Prepare messages for storage
            user_message = {
                "role": "user",
                "content": query.question,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            bot_message = {
                "role": "assistant", 
                "content": answer,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Update conversation history
            updated_messages = history + [user_message, bot_message]
            
            # Save conversation
            await self.save_conversation(conversation_id, query.user_id, domain_name, updated_messages)
            
            return ChatResponse(
                answer=answer,
                conversation_id=conversation_id,
                domain=domain_name,
                timestamp=datetime.utcnow().isoformat()
            )
            
        except Exception as e:
            return ChatResponse(
                answer=f"I apologize, but I encountered an error processing your request. Please try again later.",
                conversation_id=query.conversation_id or f"conv_{query.user_id}_{int(datetime.utcnow().timestamp())}",
                domain=query.domain,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def get_conversation_summary(self, conversation_id: str) -> Dict:
        """Get a summary of a conversation"""
        try:
            conversation = await self.mongo_db.conversations.find_one({
                "conversation_id": conversation_id
            })
            
            if not conversation:
                return {"error": "Conversation not found"}
            
            messages = conversation.get("messages", [])
            return {
                "conversation_id": conversation_id,
                "domain": conversation.get("domain"),
                "user_id": conversation.get("user_id"),
                "message_count": len(messages),
                "created_at": conversation.get("created_at"),
                "updated_at": conversation.get("updated_at"),
                "recent_messages": messages[-5:] if messages else []
            }
        except Exception as e:
            return {"error": f"Failed to get conversation summary: {str(e)}"}
    
    async def list_all_conversations(self) -> List[Dict]:
        """List all conversations in MongoDB for debugging"""
        try:
            conversations = await self.mongo_db.conversations.find({}).sort("updated_at", -1).to_list(length=None)
            result = []
            for conv in conversations:
                result.append({
                    "conversation_id": conv.get("conversation_id"),
                    "user_id": conv.get("user_id"),
                    "domain": conv.get("domain"),
                    "message_count": len(conv.get("messages", [])),
                    "created_at": conv.get("created_at"),
                    "updated_at": conv.get("updated_at")
                })
            return result
        except Exception as e:
            print(f"Error listing conversations: {e}")
            return []
