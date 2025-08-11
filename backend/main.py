from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime, timedelta
import asyncpg
from motor.motor_asyncio import AsyncIOMotorClient
import os

app = FastAPI(title="Chatbot Ticket API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PostgreSQL Connection
async def get_pg_pool():
    return await asyncpg.create_pool(
        user="admin", 
        password="adminpass", 
        database="tickets", 
        host="localhost", 
        port=5432
    )

# MongoDB Connection
mongo_client = AsyncIOMotorClient("mongodb://localhost:27017")
mongo_db = mongo_client["tickets_db"]

# Pydantic models
class TicketCreate(BaseModel):
    user_id: str
    domain: str
    summary: str
    priority: str

class TicketResponse(BaseModel):
    ticket_id: str
    status: str
    sla_deadline: datetime
    message: str

@app.on_event("startup")
async def startup_event():
    # Create PostgreSQL table if it doesn't exist
    pool = await get_pg_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                domain VARCHAR(100) NOT NULL,
                subject TEXT NOT NULL,
                status VARCHAR(50) DEFAULT 'Open',
                priority VARCHAR(50) NOT NULL,
                sla_deadline TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    await pool.close()

@app.get("/")
async def root():
    return {"message": "Chatbot Ticket API is running!"}

@app.post("/api/tickets", response_model=TicketResponse)
async def create_ticket(ticket: TicketCreate):
    try:
        ticket_id = str(uuid4())

        # SLA calculation
        sla_hours = {"low": 24, "medium": 8, "high": 4, "urgent": 2}
        deadline = datetime.utcnow() + timedelta(hours=sla_hours.get(ticket.priority.lower(), 8))

        # Insert into PostgreSQL
        pool = await get_pg_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO tickets (ticket_id, user_id, domain, subject, status, priority, sla_deadline)
                VALUES ($1, $2, $3, $4, 'Open', $5, $6)
            """, ticket_id, ticket.user_id, ticket.domain, ticket.summary, ticket.priority, deadline)
        await pool.close()

        # Insert into MongoDB for message tracking
        await mongo_db.ticket_messages.insert_one({
            "ticket_id": ticket_id,
            "message": ticket.summary,
            "sender": "user",
            "created_at": datetime.utcnow(),
            "metadata": {
                "domain": ticket.domain,
                "priority": ticket.priority,
                "user_id": ticket.user_id
            }
        })

        return TicketResponse(
            ticket_id=ticket_id,
            status="created",
            sla_deadline=deadline,
            message="Ticket created successfully"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create ticket: {str(e)}")

@app.get("/api/tickets/{ticket_id}")
async def get_ticket(ticket_id: str):
    try:
        # Get from PostgreSQL
        pool = await get_pg_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM tickets WHERE ticket_id = $1
            """, ticket_id)
        await pool.close()

        if not row:
            raise HTTPException(status_code=404, detail="Ticket not found")

        return {
            "ticket_id": row['ticket_id'],
            "user_id": row['user_id'],
            "domain": row['domain'],
            "subject": row['subject'],
            "status": row['status'],
            "priority": row['priority'],
            "sla_deadline": row['sla_deadline'],
            "created_at": row['created_at']
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve ticket: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 