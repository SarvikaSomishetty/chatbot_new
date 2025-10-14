#!/usr/bin/env python3
"""
Script to sync conversations from MongoDB to Redis
This retrieves all chat conversations from MongoDB and saves them directly to Redis
"""
import asyncio
import json
import redis
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from redis_client import init_redis, close_redis, push_message, get_messages

async def sync_conversations_to_redis():
    """Sync all conversations from MongoDB to Redis"""
    print("Syncing Conversations from MongoDB to Redis")
    print("=" * 60)
    
    # Connect to MongoDB
    mongo_client = AsyncIOMotorClient("mongodb://localhost:27017")
    mongo_db = mongo_client["tickets_db"]
    
    # Initialize Redis
    try:
        await init_redis(host="localhost", port=6380, db=0)
        print("✅ Redis initialized on localhost:6380")
    except Exception as e:
        print(f"❌ Could not initialize Redis: {e}")
        return
    
    try:
        # Get all conversations from MongoDB
        conversations = await mongo_db.conversations.find({}).sort("updated_at", -1).to_list(length=None)
        print(f"📊 Found {len(conversations)} conversations in MongoDB")
        
        if not conversations:
            print("No conversations found in MongoDB")
            return
        
        # Sync each conversation to Redis
        synced_count = 0
        for conv in conversations:
            try:
                conversation_id = conv.get("conversation_id")
                messages = conv.get("messages", [])
                user_id = conv.get("user_id")
                domain = conv.get("domain")
                
                if not conversation_id or not messages:
                    continue
                
                print(f"📝 Syncing conversation {conversation_id} ({domain}) - {len(messages)} messages")
                
                # Clear existing Redis data for this conversation
                redis_key = f"chat:{conversation_id}"
                r = redis.Redis(host="localhost", port=6380, db=0, decode_responses=True)
                r.delete(redis_key)
                
                # Add each message to Redis
                for message in messages:
                    message_data = {
                        "conversation_id": conversation_id,
                        "user_id": user_id,
                        "domain": domain,
                        "role": message.get("role", "unknown"),
                        "content": message.get("content", ""),
                        "timestamp": message.get("timestamp", datetime.utcnow().isoformat()),
                        "message_type": "chat"
                    }
                    
                    # Push to Redis
                    await push_message(conversation_id, message_data)
                
                # Set expiration to 7 days
                r.expire(redis_key, 604800)  # 7 days
                
                synced_count += 1
                print(f"   ✅ Synced {len(messages)} messages")
                
            except Exception as e:
                print(f"   ❌ Error syncing conversation {conversation_id}: {e}")
        
        print(f"\n🎉 Successfully synced {synced_count} conversations to Redis")
        
        # Verify the sync by checking Redis
        print(f"\n🔍 Verifying Redis data:")
        r = redis.Redis(host="localhost", port=6380, db=0, decode_responses=True)
        redis_keys = r.keys("chat:*")
        print(f"📊 Redis now contains {len(redis_keys)} conversation keys")
        
        # Show sample of what's in Redis
        if redis_keys:
            sample_key = redis_keys[0]
            sample_messages = await get_messages(sample_key.replace("chat:", ""))
            print(f"📝 Sample conversation ({sample_key}): {len(sample_messages)} messages")
            if sample_messages:
                print(f"   Latest message: {sample_messages[-1].get('content', '')[:100]}...")
    
    except Exception as e:
        print(f"❌ Error during sync: {e}")
    
    finally:
        # Close connections
        try:
            await close_redis()
            mongo_client.close()
            print("🔌 Connections closed")
        except Exception as e:
            print(f"⚠️ Error closing connections: {e}")

async def list_redis_conversations():
    """List all conversations currently in Redis"""
    print("\nRedis Conversations List")
    print("=" * 40)
    
    try:
        r = redis.Redis(host="localhost", port=6380, db=0, decode_responses=True)
        redis_keys = r.keys("chat:*")
        
        if not redis_keys:
            print("No conversations found in Redis")
            return
        
        print(f"Found {len(redis_keys)} conversations in Redis:")
        for key in redis_keys[:10]:  # Show first 10
            conversation_id = key.replace("chat:", "")
            messages = r.lrange(key, 0, -1)
            print(f"  📝 {conversation_id}: {len(messages)} messages")
        
        if len(redis_keys) > 10:
            print(f"  ... and {len(redis_keys) - 10} more")
            
    except Exception as e:
        print(f"❌ Error listing Redis conversations: {e}")

if __name__ == "__main__":
    print("Choose an option:")
    print("1. Sync conversations from MongoDB to Redis")
    print("2. List Redis conversations")
    print("3. Both")
    
    choice = input("Enter choice (1/2/3): ").strip()
    
    if choice == "1":
        asyncio.run(sync_conversations_to_redis())
    elif choice == "2":
        asyncio.run(list_redis_conversations())
    elif choice == "3":
        asyncio.run(sync_conversations_to_redis())
        asyncio.run(list_redis_conversations())
    else:
        print("Invalid choice. Running sync...")
        asyncio.run(sync_conversations_to_redis())
