#!/usr/bin/env python3
"""
Quick test script to verify chatbot functionality
"""

import asyncio
import sys
import os
sys.path.append('backend')

from chatbot import GeminiChatbot, ChatQuery
from motor.motor_asyncio import AsyncIOMotorClient
import redis

async def test_chatbot():
    """Test the chatbot directly"""
    try:
        # Initialize MongoDB
        mongo_client = AsyncIOMotorClient("mongodb://localhost:27017")
        mongo_db = mongo_client["tickets_db"]
        
        # Initialize Redis
        redis_client = redis.Redis(host="localhost", port=6380, db=0, decode_responses=True)
        
        # Initialize chatbot
        chatbot = GeminiChatbot(mongo_db, redis_client)
        
        # Test query
        test_query = ChatQuery(
            user_id="test_user",
            domain="customer-support",
            question="Hello, how can I help you today?"
        )
        
        print("Testing chatbot...")
        response = await chatbot.process_query(test_query)
        
        print(f"Response: {response.answer}")
        print(f"Domain: {response.domain}")
        print(f"Conversation ID: {response.conversation_id}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_chatbot())
    if success:
        print("✅ Chatbot test passed!")
    else:
        print("❌ Chatbot test failed!")
        sys.exit(1)
