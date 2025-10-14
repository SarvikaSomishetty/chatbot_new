#!/usr/bin/env python3
"""
Simple script to view and manage conversations from MongoDB
"""
import asyncio
import json
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

async def view_mongodb_conversations():
    """View all conversations in MongoDB"""
    print("MongoDB Conversations")
    print("=" * 50)
    
    # Connect to MongoDB
    mongo_client = AsyncIOMotorClient("mongodb://localhost:27017")
    mongo_db = mongo_client["tickets_db"]
    
    try:
        # Get all conversations
        conversations = await mongo_db.conversations.find({}).sort("updated_at", -1).to_list(length=None)
        
        if not conversations:
            print("No conversations found in MongoDB")
            return
        
        print(f"Found {len(conversations)} conversations:")
        print()
        
        for i, conv in enumerate(conversations[:20]):  # Show first 20
            conversation_id = conv.get("conversation_id", "unknown")
            user_id = conv.get("user_id", "unknown")
            domain = conv.get("domain", "unknown")
            messages = conv.get("messages", [])
            created_at = conv.get("created_at")
            updated_at = conv.get("updated_at")
            
            print(f"{i+1:2d}. Conversation: {conversation_id}")
            print(f"    User: {user_id}")
            print(f"    Domain: {domain}")
            print(f"    Messages: {len(messages)}")
            print(f"    Created: {created_at}")
            print(f"    Updated: {updated_at}")
            
            # Show first and last message
            if messages:
                first_msg = messages[0]
                last_msg = messages[-1]
                print(f"    First: {first_msg.get('role', 'unknown')}: {first_msg.get('content', '')[:60]}...")
                print(f"    Last:  {last_msg.get('role', 'unknown')}: {last_msg.get('content', '')[:60]}...")
            print()
        
        if len(conversations) > 20:
            print(f"... and {len(conversations) - 20} more conversations")
        
        # Show summary by domain
        print("\nSummary by Domain:")
        domain_counts = {}
        for conv in conversations:
            domain = conv.get("domain", "unknown")
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        for domain, count in domain_counts.items():
            print(f"  {domain}: {count} conversations")
        
        # Show summary by user
        print("\nSummary by User:")
        user_counts = {}
        for conv in conversations:
            user_id = conv.get("user_id", "unknown")
            user_counts[user_id] = user_counts.get(user_id, 0) + 1
        
        for user_id, count in list(user_counts.items())[:10]:  # Show top 10 users
            print(f"  {user_id}: {count} conversations")
        
        if len(user_counts) > 10:
            print(f"  ... and {len(user_counts) - 10} more users")
            
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        mongo_client.close()

if __name__ == "__main__":
    asyncio.run(view_mongodb_conversations())
