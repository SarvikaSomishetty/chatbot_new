import redis
import json
import asyncio

r = None

async def init_redis(host='localhost', port=6379, db=0):
    global r
    # Initialize synchronously but expose as async to be awaitable
    r = redis.Redis(host=host, port=port, db=db, decode_responses=True)
    return r

async def close_redis():
    global r
    if r:
        await asyncio.to_thread(r.close)

async def push_message(user_id, message_dict):
    key = f"chat:{user_id}"
    data = json.dumps(message_dict)
    await asyncio.to_thread(r.rpush, key, data)

async def get_messages(user_id):
    key = f"chat:{user_id}"
    messages = await asyncio.to_thread(r.lrange, key, 0, -1)
    return [json.loads(m) for m in messages]
