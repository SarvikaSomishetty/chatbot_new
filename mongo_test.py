import asyncio
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID, uuid4
import motor.motor_asyncio

# MongoDB client (make sure container is running and mapped to port 27017)
client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
db = client["ticketing_system"]

# Pydantic models for validation
class TicketMessage(BaseModel):
    message_id: str  # store as string
    ticket_id: str   # store as string
    sender: str
    text: str
    metadata: Optional[Dict] = None
    timestamp: datetime = datetime.utcnow()

class CaseMemory(BaseModel):
    case_id: str
    user_profile_snapshot: Dict
    conversation_snippets: List[str] = []
    embedding_refs: List[str] = []
    tags: List[str] = []
    resolution_summary: Optional[str] = None
    last_seen: datetime = datetime.utcnow()

# Functions
async def add_message(msg: TicketMessage):
    result = await db.ticket_messages.insert_one(msg.model_dump())
    print(f"Inserted message with _id: {result.inserted_id}")

async def create_case_memory(case: CaseMemory):
    result = await db.case_memory.insert_one(case.model_dump())
    print(f"Inserted case memory with _id: {result.inserted_id}")

# Test run
async def main():
    ticket_id = str(uuid4())

    msg = TicketMessage(
        message_id=str(uuid4()),
        ticket_id=ticket_id,
        sender="user",
        text="My order is delayed",
        metadata={"attachments": []}
    )
    await add_message(msg)

    case = CaseMemory(
        case_id=ticket_id,
        user_profile_snapshot={"name": "John Doe", "email": "john@example.com"},
        conversation_snippets=["User reported delay"],
        tags=["order", "shipping"]
    )
    await create_case_memory(case)

if __name__ == "__main__":
    asyncio.run(main())
