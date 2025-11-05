"""
Chatbot module with Gemini AI integration
Handles domain-specific conversations and stores chat history in MongoDB
"""
import os
import json
import re
from datetime import datetime
import time
import urllib.request
import urllib.error
import urllib.parse
import asyncio
from typing import Dict, List, Optional
import google.generativeai as genai
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase
import redis
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini AI - single API key
def _get_gemini_api_key() -> str:
    """Get the single Gemini API key from environment"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Warning: No Gemini API key found. Set GEMINI_API_KEY in .env")
        return "YOUR_GEMINI_API_KEY"
    return api_key.strip()

# Domain-specific contexts (restricted to required domains only)

GLOBAL_CONTEXT = """
You are Gemini, a high-accuracy AI assistant integrated into a professional chatbot system.
Your communication style mirrors ChatGPT’s tone — confident, concise, human-like, and polished.

Core Behavior:
- Always provide clear, factual, and well-structured answers in 1–4 sentences.
- Use Markdown formatting for readability: **bold** key terms, bullet points for lists, and short paragraphs.
- When a question asks for real-world or numerical data (e.g., currency rates, stock prices, weather, population, etc.), 
  return the **most recent known or web-estimated value** and note that values fluctuate, instead of refusing.
- Be professional yet approachable — no unnecessary disclaimers, over-formality, or robotic phrasing.
- Avoid filler like “As an AI language model” or “I cannot access real-time data.”
- If a question is unclear, ask for clarification instead of guessing.
- Always maintain context awareness. Merge knowledge from multiple domains when necessary.
- When summarizing or explaining, use headings, short lists, or formatting to make responses scannable.
- Never repeat previous conversation text unless explicitly asked.

Example formatting style:
**Question:** How does compound interest differ from simple interest?  
**Answer:**  
- **Simple Interest:** Calculated only on the principal.  
- **Compound Interest:** Calculated on the principal plus accumulated interest — grows exponentially over time.

Your goal: sound like a human expert who respects the user’s time — precise, calm, and current.
"""


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
    
    Communication style: Professional, clear, and informative. Provide factual, detailed answers with specific information.
    When domain-specific data is provided, use it directly as the authoritative source.
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
    
    Communication style: Professional, clear, and structured. When domain-specific data is provided, use it directly.
    Provide step-by-step technical solutions with clear, detailed explanations.
    Present information in an organized, easy-to-follow format.
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
    
    Communication style: Professional, factual, and precise. When domain-specific data is provided, use it directly.
    Answer with exact numbers, percentages, and specific strategies when available.
    Structure financial information clearly with tables or organized lists when appropriate.
    Provide clear, practical financial guidance. Note that this is not professional financial advice when applicable.
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
    
    Communication style: Professional, informative, and detailed. When domain-specific data is provided, use it directly.
    Provide comprehensive travel information in a clear, organized manner.
    Help users plan safe, enjoyable, and memorable travel experiences.
    Always provide specific, factual information and remind users to verify details independently when appropriate.
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
    tts_path: Optional[str] = None

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
        # Single API key configuration
        self._gemini_api_key = _get_gemini_api_key()
        self.llm_available = False
        self._init_llm()  # configure and validate the API key
        # Elasticsearch endpoint (optional). If not running, logging will be skipped gracefully.
        self.elasticsearch_url = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
        self.elasticsearch_index = os.getenv("ELASTICSEARCH_INDEX", "chatbot_logs")
        # Load domain-specific data
        self.domain_data_cache = {}
        self._load_domain_data()

    def _configure_genai(self):
        genai.configure(api_key=self._gemini_api_key)

    def _init_llm(self) -> None:
        
        """Initialize Gemini AI with the configured API key."""
        try:
            print(f"Gemini: configuring with API key")
            self._configure_genai()
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            self.llm_available = True
            print("Gemini: LLM initialized successfully")
        except Exception as e:
            self.llm_available = False
            print(f"Gemini init error: {e}")

    def _load_domain_data(self) -> None:
        """Load domain-specific data from JSON files"""
        domain_file_mapping = {
            "Customer Support": "customer_support.json",
            "Technical Support": "technical_support.json",
            "Finance": "finance.json",
            "Travel": "travel.json"
        }
        
        # Get the data directory path (in backend/data/)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(current_dir, "data")
        
        for domain_name, filename in domain_file_mapping.items():
            file_path = os.path.join(data_dir, filename)
            try:
                if os.path.exists(file_path):
                    with open(file_path, "r", encoding="utf-8") as f:
                        self.domain_data_cache[domain_name] = json.load(f)
                    print(f"✅ Loaded {len(self.domain_data_cache[domain_name])} Q&A pairs for {domain_name}")
                else:
                    print(f"⚠️ Domain data file not found: {file_path}")
                    self.domain_data_cache[domain_name] = []
            except Exception as e:
                print(f"❌ Error loading domain data for {domain_name}: {e}")
                self.domain_data_cache[domain_name] = []
    
    def _find_relevant_answer(self, user_query: str, domain_data: List[Dict]) -> Optional[str]:
        """
        Find relevant answer from domain data using keyword matching.
        Returns the best matching answer if found, None otherwise.
        """
        if not domain_data:
            return None
        
        user_query_lower = user_query.lower().strip()
        # Remove common stop words for better matching
        stop_words = {'the', 'a', 'an', 'and', 'or', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are', 'was', 'were', 'what', 'how', 'when', 'where', 'why', 'do', 'does', 'did', 'can', 'could', 'should', 'will', 'would'}
        query_words = set(word for word in user_query_lower.split() if word not in stop_words and len(word) > 2)
        
        if not query_words:  # If all words were stop words, use all words
            query_words = set(user_query_lower.split())
        
        best_match = None
        best_score = 0
        
        for item in domain_data:
            question = item.get("question", "").lower()
            answer = item.get("answer", "")
            
            if not question or not answer:
                continue
            
            # Check both question and answer for matches (answers often contain keywords)
            question_words = set(word for word in question.split() if word not in stop_words and len(word) > 2)
            if not question_words:
                question_words = set(question.split())
            
            answer_words = set(word for word in answer.lower().split() if word not in stop_words and len(word) > 2)
            if not answer_words:
                answer_words = set(answer.lower().split())
            
            # Combine question and answer words for broader matching
            combined_words = question_words.union(answer_words)
            common_words = query_words.intersection(combined_words)
            
            # Score based on word overlap
            if common_words:
                # Higher score if more words match
                score = len(common_words) / max(len(query_words), 1)
                
                # Big bonus if exact phrase match in question
                if user_query_lower in question:
                    score += 0.8
                # Medium bonus if query words appear in sequence in question
                elif any(phrase in question for phrase in [user_query_lower[:len(user_query_lower)//2], user_query_lower[-len(user_query_lower)//2:]]):
                    score += 0.3
                
                # Bonus if matching words appear in answer (shows relevance)
                answer_matches = query_words.intersection(answer_words)
                if answer_matches:
                    score += 0.2 * (len(answer_matches) / max(len(query_words), 1))
                
                if score > best_score:
                    best_score = score
                    best_match = answer
        
        # Lower threshold (25%) for better coverage, but still ensure quality matches
        if best_score >= 0.25:
            print(f"[DEBUG] Domain data match found with score: {best_score:.2f}")
            return best_match
        
        return None
    
    def _find_top_relevant_qas(self, user_query: str, domain_data: List[Dict], top_k: int = 5) -> List[Dict]:
        """
        Find top K most relevant Q&A pairs from domain data.
        Returns list of dictionaries with 'question', 'answer', and 'score'.
        """
        if not domain_data:
            return []
        
        user_query_lower = user_query.lower().strip()
        stop_words = {'the', 'a', 'an', 'and', 'or', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are', 'was', 'were', 'what', 'how', 'when', 'where', 'why', 'do', 'does', 'did', 'can', 'could', 'should', 'will', 'would'}
        query_words = set(word for word in user_query_lower.split() if word not in stop_words and len(word) > 2)
        
        if not query_words:
            query_words = set(user_query_lower.split())
        
        scored_qas = []
        
        for item in domain_data:
            question = item.get("question", "").lower()
            answer = item.get("answer", "")
            
            if not question or not answer:
                continue
            
            question_words = set(word for word in question.split() if word not in stop_words and len(word) > 2)
            if not question_words:
                question_words = set(question.split())
            
            answer_words = set(word for word in answer.lower().split() if word not in stop_words and len(word) > 2)
            if not answer_words:
                answer_words = set(answer.lower().split())
            
            combined_words = question_words.union(answer_words)
            common_words = query_words.intersection(combined_words)
            
            if common_words:
                score = len(common_words) / max(len(query_words), 1)
                
                if user_query_lower in question:
                    score += 0.8
                elif any(phrase in question for phrase in [user_query_lower[:len(user_query_lower)//2], user_query_lower[-len(user_query_lower)//2:]]):
                    score += 0.3
                
                answer_matches = query_words.intersection(answer_words)
                if answer_matches:
                    score += 0.2 * (len(answer_matches) / max(len(query_words), 1))
                
                scored_qas.append({
                    'question': item.get("question", ""),
                    'answer': answer,
                    'score': score
                })
        
        # Sort by score descending and return top K
        scored_qas.sort(key=lambda x: x['score'], reverse=True)
        return scored_qas[:top_k]

    
    async def ask_llm(self, prompt: str, temperature: float = 0.6) -> str:
        """Ask Gemini AI with automatic quota handling and retries"""
        if not self.llm_available:
            raise RuntimeError("LLM unavailable")

        gen_kwargs = {
            'generation_config': {
                'temperature': temperature,
                'max_output_tokens': 2000,  # Allow longer responses to avoid MAX_TOKENS truncation
                'top_p': 0.9,
                'top_k': 40
            }
        }

        async def _extract_response_text(response) -> str:
            """Extract text from Gemini response with multiple fallback methods"""
            # Method 1: Direct text attribute
            try:
                if hasattr(response, 'text'):
                    text_value = response.text
                    if text_value and str(text_value).strip():
                        return str(text_value).strip()
            except Exception as e:
                print(f"[DEBUG] Method 1 failed: {e}")

            # Method 2: Candidates structure (most common)
            try:
                candidates = getattr(response, 'candidates', [])
                if not candidates and hasattr(response, '_raw_response'):
                    # Try to get candidates from raw response
                    raw = response._raw_response
                    if isinstance(raw, dict):
                        candidates = raw.get('candidates', [])
                
                if candidates:
                    for cand in candidates:
                        try:
                            # Handle both object and dict formats
                            if isinstance(cand, dict):
                                content = cand.get('content', {})
                                parts = content.get('parts', []) if isinstance(content, dict) else []
                            else:
                                content = getattr(cand, 'content', None)
                                if content:
                                    parts = getattr(content, 'parts', []) if hasattr(content, 'parts') else []
                                else:
                                    parts = []
                            
                            # Some SDK variants may return content as a list of parts directly
                            if not parts and isinstance(content, list):
                                parts = content

                            # Try direct content text if exposed
                            try:
                                direct_content_texts = []
                                if isinstance(content, dict) and 'text' in content:
                                    direct_content_texts.append(content.get('text', ''))
                                elif hasattr(content, 'text'):
                                    direct_content_texts.append(getattr(content, 'text'))
                                direct_content_texts = [t for t in direct_content_texts if t]
                                if direct_content_texts:
                                    joined = " ".join(str(t) for t in direct_content_texts).strip()
                                    if joined:
                                        return joined
                            except Exception as _e:
                                pass

                            if parts:
                                parts_texts = []
                                for p in parts:
                                    if isinstance(p, dict):
                                        parts_texts.append(p.get('text', ''))
                                    elif hasattr(p, 'text'):
                                        parts_texts.append(p.text)
                                    elif isinstance(p, str):
                                        parts_texts.append(p)
                                
                                parts_text = " ".join(str(t) for t in parts_texts if t).strip()
                                if parts_text:
                                    return parts_text
                        except Exception as e:
                            print(f"[DEBUG] Error processing candidate: {e}")
                            continue
            except Exception as e:
                print(f"[DEBUG] Method 2 failed: {e}")
            
            # Method 3: Try string conversion
            try:
                response_str = str(response)
                if response_str and response_str.strip() and response_str != str(type(response)):
                    # Check if it looks like actual content, not just object representation
                    if len(response_str) > 50 and not response_str.startswith('<'):
                        return response_str.strip()
            except Exception as e:
                print(f"[DEBUG] Method 3 failed: {e}")
                
            # Method 4: Raw dictionary access
            try:
                if hasattr(response, '_raw_response'):
                    raw = response._raw_response
                    if isinstance(raw, dict) and 'candidates' in raw:
                        for cand in raw['candidates']:
                            if 'content' in cand and 'parts' in cand['content']:
                                parts_text = " ".join(
                                    str(p.get('text', '')) for p in cand['content']['parts'] if isinstance(p, dict) and 'text' in p
                                ).strip()
                                if parts_text:
                                    return parts_text
            except Exception as e:
                print(f"[DEBUG] Method 4 failed: {e}")
                
            return ""

        for attempt in range(3):
            try:
                # First attempt with original prompt
                current_prompt = prompt
                if attempt == 1:  # Second attempt with simplified prompt
                    # Truncate prompt if too long (Gemini has limits)
                    if len(prompt) > 20000:
                        current_prompt = prompt[:15000] + "\n\n[Previous context truncated for retry]"
                    else:
                        current_prompt = prompt
                elif attempt == 2:  # Third attempt with minimal prompt
                    # Try with just the question and minimal context
                    current_prompt = f"Answer the following question clearly and in detail:\n\n{prompt.split('Current question:')[-1] if 'Current question:' in prompt else prompt[-1000:]}"

                async def _call_gen():
                    return await asyncio.to_thread(self.model.generate_content, current_prompt, **gen_kwargs)

                print(f"[DEBUG] Attempt {attempt + 1}: Calling Gemini API with prompt length {len(current_prompt)}")
                response = await asyncio.wait_for(_call_gen(), timeout=30.0)
                
                # Try to extract response text
                response_text = await _extract_response_text(response)
                
                # Debug: Print response structure if extraction failed
                if not response_text:
                    print(f"[DEBUG] Response extraction failed. Response type: {type(response)}")
                    print(f"[DEBUG] Response attributes: {dir(response)}")
                    if hasattr(response, 'prompt_feedback'):
                        print(f"[DEBUG] Prompt feedback: {response.prompt_feedback}")
                    if hasattr(response, 'candidates'):
                        print(f"[DEBUG] Candidates: {response.candidates}")
                
                # If we got a valid response, return it
                if response_text:
                    print(f"[DEBUG] Successfully extracted response ({len(response_text)} chars)")
                    return response_text
                
                # If we're on the last attempt, log more details
                if attempt == 2:
                    print(f"[ERROR] Failed to get response after 3 attempts. Response object: {response}")
                    print(f"[ERROR] Trying fallback extraction methods...")
                    # Try one more direct extraction
                    try:
                        if hasattr(response, 'text'):
                            direct_text = str(response.text)
                            if direct_text:
                                return direct_text
                    except:
                        pass
                    return "I'm temporarily unable to respond. Please try again with a different question or check back later."
                
                # Otherwise, log and continue to next attempt
                print(f"[Attempt {attempt + 1}] Empty response, retrying with different prompt...")
                
            except Exception as e:
                err_msg = str(e)
                print(f"[ERROR] Gemini attempt {attempt + 1} failed: {err_msg}")
                import traceback
                traceback.print_exc()
                
                # If it's the last attempt, return a fallback message
                if attempt == 2:
                    return "I'm experiencing technical difficulties. Please try again in a moment."
                    
                # Handle rate limiting
                if any(term in err_msg.lower() for term in ["quota", "429", "rate limit"]):
                    # extract retry delay if mentioned
                    match = re.search(r"retry in ([0-9.]+)s", err_msg)
                    delay = float(match.group(1)) if match else 30.0
                    print(f"⚠️ Quota hit. Retrying in {delay:.1f}s...")
                    await asyncio.sleep(delay)
                    continue

                # Handle timeout or transient network errors
                if "timeout" in err_msg.lower():
                    print("⚠️ Timeout — retrying in 5s...")
                    await asyncio.sleep(5)
                    continue

                # For other errors, break
                break

        # If we failed after retries
        return (
            "I can't reach the assistant right now. You can try again shortly, "
            "or create a support ticket so we can follow up."
        )
    async def get_conversation_history(self, conversation_id: str) -> List[Dict]:
        """Get conversation history from Redis first, then MongoDB as fallback"""
        try:
            # Try Redis first for fast access
            if self.redis_client:
                cached_messages = await self.get_cached_messages(conversation_id)
                if cached_messages:
                    print(f"✅ Retrieved {len(cached_messages)} messages from Redis cache for conversation {conversation_id}")
                    return cached_messages
            
            # Fallback to MongoDB
            conversation = await self.mongo_db.conversations.find_one({
                "conversation_id": conversation_id
            })
            messages = conversation.get("messages", []) if conversation else []
            
            # Cache the messages in Redis for future fast access
            if messages and self.redis_client:
                await self.cache_recent_messages(conversation_id, messages[-10:])  # Cache last 10 messages
                print(f"✅ Cached {len(messages[-10:])} recent messages from MongoDB to Redis for conversation {conversation_id}")
            
            return messages
        except Exception as e:
            print(f"❌ Error fetching conversation history: {e}")
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
            
            print(f"💾 Saving conversation {conversation_id} for user {user_id} in domain {domain} with {len(messages)} messages")
            
            result = await self.mongo_db.conversations.update_one(
                {"conversation_id": conversation_id},
                {"$set": conversation_data},
                upsert=True
            )
            
            if os.getenv("CHATBOT_DEBUG", "").lower() in ("1", "true", "yes"):
                print(f"Saved conversation {conversation_id} to MongoDB - Domain: {domain}, Messages: {len(messages)}, User: {user_id}")
                print(f"MongoDB result: {result.upserted_id if result.upserted_id else result.modified_count} documents affected")
            
            # Also cache all messages in Redis for fast access (if Redis is available)
            if self.redis_client:
                await self.cache_recent_messages(conversation_id, messages)  # All messages
                print(f"✅ Cached all {len(messages)} messages for conversation {conversation_id} in Redis")
            
        except Exception as e:
            print(f"❌ Error saving conversation: {e}")
    
    async def cache_recent_messages(self, conversation_id: str, messages: List[Dict]):
        """Cache recent messages in Redis for fast access using async redis_client"""
        # Temporarily disable Redis caching to isolate issues
        if not self.redis_client or os.getenv("DISABLE_REDIS_CACHE", "0") == "1":
            print(f"[DEBUG] Redis caching disabled for conversation {conversation_id}")
            return
        try:
            # Import the async Redis functions
            from redis_client import push_message
            
            # Clear existing cache first
            redis_key = f"chat:{conversation_id}"
            self.redis_client.delete(redis_key)
            
            # Add each message using the async push_message function
            for message in messages:
                await push_message(conversation_id, message)
            
            # Set expiration to 24 hours
            self.redis_client.expire(redis_key, 86400)
            if os.getenv("CHATBOT_DEBUG", "").lower() in ("1", "true", "yes"):
                print(f"Cached {len(messages)} messages for conversation {conversation_id} in Redis")
        except Exception as e:
            print(f"[DEBUG] Error caching messages in Redis: {e}")
    
    async def get_cached_messages(self, conversation_id: str) -> List[Dict]:
        """Get cached messages from Redis using async redis_client"""
        if not self.redis_client:
            return []
        try:
            # Import the async Redis functions
            from redis_client import get_messages
            return await get_messages(conversation_id)
        except Exception as e:
            print(f"❌ Error getting cached messages: {e}")
            return []
    
    async def process_query(self, query: ChatQuery) -> ChatResponse:
        """Process a chat query and return AI response"""
        print(f"[DEBUG] Processing query for user {query.user_id}, conversation {query.conversation_id}")
        print(f"[DEBUG] LLM available: {self.llm_available}")
        
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
            
            # Retrieve relevant domain-specific data - ALWAYS provide domain data to Gemini
            domain_data_context = ""
            domain_data = self.domain_data_cache.get(domain_name, [])
            if domain_data:
                # Find best matching answer (exact match)
                best_match = self._find_relevant_answer(query.question, domain_data)
                
                # Also find top 3-5 relevant Q&A pairs for broader context
                relevant_qas = self._find_top_relevant_qas(query.question, domain_data, top_k=5)
                
                if best_match:
                    # Use best match as primary, with top relevant Q&As as additional context
                    if len(relevant_qas) > 1:
                        # Multiple relevant items found
                        additional_context = "\n\nAdditional relevant information from our knowledge base:\n"
                        for i, qa in enumerate(relevant_qas[:4], 1):  # Top 4 additional items
                            if qa['answer'] != best_match:  # Don't repeat the best match
                                additional_context += f"\n{i}. Q: {qa['question']}\n   A: {qa['answer']}\n"
                        
                        domain_data_context = f"""
CRITICAL: The following information is from our company's knowledge base for {domain_name}. You MUST use this information as your primary source and provide detailed, specific answers based on it.

PRIMARY KNOWLEDGE BASE INFORMATION:
{best_match}
{additional_context}

User's Question: {query.question}

You MUST answer using the above knowledge base information. Be CONCISE (2-4 short paragraphs or bullet points max). Get straight to the point - no lengthy introductions. Use the specific data directly but summarize it briefly."""
                    else:
                        # Single best match
                        domain_data_context = f"""
CRITICAL: The following information is from our company's knowledge base for {domain_name}. You MUST use this information as your primary source and provide detailed, specific answers based on it.

KNOWLEDGE BASE INFORMATION:
{best_match}

User's Question: {query.question}

You MUST answer using the above knowledge base information. Be CONCISE (2-3 short paragraphs or bullet points). Get straight to the point with the key information."""
                    print(f"[DEBUG] Found relevant domain data for {domain_name} (1 exact match + {len(relevant_qas)} relevant items)")
                elif relevant_qas:
                    # No exact match, but we have relevant Q&As - provide them all
                    context_text = ""
                    for i, qa in enumerate(relevant_qas[:5], 1):
                        context_text += f"\n{i}. Q: {qa['question']}\n   A: {qa['answer']}\n"
                    
                    domain_data_context = f"""
CRITICAL: The following information is from our company's knowledge base for {domain_name}. You MUST use this information to answer the user's question.

KNOWLEDGE BASE INFORMATION:
{context_text}

User's Question: {query.question}

Use the relevant information from the knowledge base above to answer the question CONCISELY (2-4 short paragraphs or bullet points). If multiple items are relevant, summarize the key points briefly. Base your answer on this data, not general knowledge."""
                    print(f"[DEBUG] No exact match, but found {len(relevant_qas)} relevant Q&As for {domain_name}")
                else:
                    # No relevant data found - still provide domain context for Gemini to work with
                    # Give Gemini a few example Q&As from this domain so it knows the domain style
                    sample_qas = domain_data[:3]  # First 3 Q&As as domain examples
                    sample_context = "\n".join([f"Q: {qa['question']}\nA: {qa['answer']}" for qa in sample_qas])
                    
                    domain_data_context = f"""
You are answering a question about {domain_name}. While we don't have an exact match in our knowledge base, here are some examples of the type of information we provide for this domain:

Example knowledge base entries:
{sample_context}

User's Question: {query.question}

Answer the question CONCISELY (2-3 short paragraphs) in the same style as the examples above. Be brief, direct, and informative."""
                    print(f"[DEBUG] No relevant match found, but providing domain context examples for {domain_name}")
            else:
                print(f"[DEBUG] No domain data available for {domain_name}")
            
            # Create the prompt
            if domain_data_context:
                # Use domain data context when available
                prompt = f"""
{domain_context}

Previous conversation context:
{context_messages}

{domain_data_context}

CRITICAL INSTRUCTIONS:
- You have been provided with specific, factual information from our knowledge base above.
- You MUST answer the user's question using this specific information as your primary source.
- Keep responses CONCISE and SCANNABLE - aim for 2-4 short paragraphs maximum, or bullet points.
- Lead with the key answer immediately - no lengthy introductions or filler.
- Include the most important details from the knowledge base (numbers, timelines, specific steps) but be brief.
- Do NOT say things like "it depends", "varies by", "check with your provider", or other generic disclaimers when you have specific data available.
- Structure with short paragraphs (2-3 sentences each) or bullet points for quick reading.
- Avoid verbose explanations - get straight to the point.
- If multiple items are relevant, summarize the key points concisely rather than listing everything.
- Format for readability: Short paragraphs, bullet points, or numbered lists - NOT long walls of text.
- Maximum length: 150-250 words for simple questions, up to 400 words for complex topics requiring multiple details.
- Tone: Professional, direct, and helpful - like a quick reference guide, not a detailed manual.
- Be comprehensive but brief - answer fully without unnecessary elaboration.
"""
            else:
                # Original prompt when no domain data match found
                prompt = f"""
{domain_context}

Previous conversation context:
{context_messages}

Current question: {query.question}

Instructions:
- Answer the question directly and concisely (2-3 short paragraphs maximum).
- Be brief, professional, and get straight to the point.
- If the question clearly belongs to another domain or is general, still answer politely.
- Always prioritize helpfulness and factual correctness over strict domain filtering.
- Do not say you lack real-time data unless essential — use your best known recent info.
- Maximum length: 200-300 words. Avoid long explanations or walls of text.
"""

            
            # Get AI response with latency measurement
            start_time = time.perf_counter()
            try:
                # Check prompt length and truncate if necessary (Gemini has token limits)
                max_prompt_length = 30000  # Rough estimate for safety
                if len(prompt) > max_prompt_length:
                    print(f"[WARNING] Prompt too long ({len(prompt)} chars), truncating to {max_prompt_length}")
                    # Keep the beginning and end, truncate middle
                    keep_start = prompt[:5000]
                    keep_end = prompt[-5000:]
                    prompt = keep_start + "\n\n[... context truncated ...]\n\n" + keep_end
                
                print(f"[DEBUG] Calling ask_llm with prompt length: {len(prompt)}")
                answer = await self.ask_llm(prompt)
                print(f"[DEBUG] ask_llm returned answer length: {len(answer) if answer else 0}")
                
                if not answer or len(answer.strip()) < 10:
                    print(f"[WARNING] Answer seems too short or empty: '{answer}'")
                
                # Clean up the response - preserve useful formatting but remove excessive markdown
                if answer:
                    import re
                    # Keep tables and structured lists, but clean up excessive markdown
                    # Convert markdown bold to plain text (keep content)
                    answer = re.sub(r'\*\*(.*?)\*\*', r'\1', answer)
                    # Convert markdown italic to plain text (keep content)
                    answer = re.sub(r'\*(.*?)\*', r'\1', answer)
                    # Preserve list formatting - convert markdown lists to plain text lists
                    # Keep bullet points by converting * - + to regular bullets
                    answer = re.sub(r'^\s*[\*\-\+]\s+', '• ', answer, flags=re.MULTILINE)
                    # Clean up extra whitespace but preserve paragraph breaks
                    answer = re.sub(r'\n{3,}', '\n\n', answer)
                    answer = answer.strip()
                    
            except Exception as e:
                print(f"[ask_llm ERROR]: {e}")
                answer = ""
            
            if not answer:
                # Graceful fallback answer when LLM unavailable
                answer = (
                    "I can't reach the assistant right now. You can try again shortly, "
                    "or create a support ticket so we can follow up."
                )
            # --- Add TTS generation here ---
            tts_audio_path = ""
            if answer and os.getenv("DISABLE_TTS", "1") != "1":
                try:
                    tts_audio_path = await self.generate_tts(answer, conversation_id)
                except Exception as e:
                    print(f"[DEBUG] TTS generation failed: {e}")
                    tts_audio_path = ""

            latency_ms = int((time.perf_counter() - start_time) * 1000)
            
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

            # Fire-and-forget: log to Elasticsearch (non-blocking)
            try:
                await self.log_to_elasticsearch(
                    {
                        "conversation_id": conversation_id,
                        "user_id": query.user_id,
                        "domain": domain_name,
                        "question": query.question,
                        "answer": answer,
                        "response_time_ms": latency_ms,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )
            except Exception as _log_err:
                # Swallow logging errors to avoid impacting user flow
                print(f"⚠️ Elasticsearch logging skipped: {_log_err}")
            
            return ChatResponse(
                answer=answer,
                conversation_id=conversation_id,
                domain=domain_name,
                timestamp=datetime.utcnow().isoformat(),
                tts_path=tts_audio_path or None
            )
            
        except Exception as e:
            print(f"[process_query ERROR]: {e}")
            return ChatResponse(
                answer=f"I apologize, but I encountered an error processing your request. Please try again later.",
                conversation_id=query.conversation_id or f"conv_{query.user_id}_{int(datetime.utcnow().timestamp())}",
                domain=query.domain,
                timestamp=datetime.utcnow().isoformat()
            )
    async def generate_tts(self, text: str, conversation_id: str) -> str:
        """
        Generate TTS audio from the assistant's text.
        Returns the local file path of the audio.
        """
        print(f"[DEBUG] Starting TTS generation for conversation {conversation_id}")
        try:
            import pyttsx3
            import os

            # Get the tts_audio directory path (in backend/tts_audio/)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            audio_dir = os.path.join(current_dir, "tts_audio")
            os.makedirs(audio_dir, exist_ok=True)
            base_name = f"{conversation_id}_{int(datetime.utcnow().timestamp())}.wav"
            filename = os.path.join(audio_dir, base_name)
            print(f"[DEBUG] TTS filename: {filename}")

            def _synthesize():
                print(f"[DEBUG] Initializing TTS engine")
                engine = pyttsx3.init()
                print(f"[DEBUG] Saving TTS to file: {filename}")
                engine.save_to_file(text, filename)
                print(f"[DEBUG] Running TTS engine")
                engine.runAndWait()
                print(f"[DEBUG] TTS generation completed")

            await asyncio.to_thread(_synthesize)
            tts_path = f"/tts/{base_name}"
            print(f"[DEBUG] TTS path returned: {tts_path}")
            return tts_path
        except Exception as e:
            print(f"[DEBUG] TTS generation failed: {e}")
            return ""

    async def log_to_elasticsearch(self, document: Dict) -> None:
        """Send a single log document to Elasticsearch using standard library, without blocking the main flow."""
        # If ES URL seems disabled, skip
        if not self.elasticsearch_url:
            return
        try:
            url = f"{self.elasticsearch_url.rstrip('/')}/{self.elasticsearch_index}/_doc"
            data = json.dumps(document).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

            # Perform in a background thread to avoid blocking the event loop
            def _do_request():
                try:
                    with urllib.request.urlopen(req, timeout=2) as resp:
                        # Best-effort: don't parse response
                        _ = resp.read()
                except Exception as e:
                    # Suppress errors to keep chat responsive
                    raise e

            await asyncio.to_thread(_do_request)
        except Exception as e:
            # Surface minimal info to logs, but never raise
            print(f"Elasticsearch log error: {e}")
    
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
