from fastapi import APIRouter
from fastapi import Depends
from datetime import datetime
import asyncio
from uuid import uuid4

def get_sla_router(get_pg_pool, mongo_db):
    router = APIRouter()

    @router.get("/api/sla/tickets")
    async def list_sla_breaches():
        """List all SLA breached tickets from PostgreSQL and MongoDB"""
        pool = await get_pg_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM tickets WHERE status='Breached'")
        await pool.close()

        # Fetch SLA events from MongoDB
        events = []
        async for doc in mongo_db.sla_events.find({}):
            events.append({
                "ticket_id": doc["ticket_id"],
                "event": doc["event"],
                "timestamp": doc["timestamp"]
            })

        return {"breached_tickets": [dict(r) for r in rows], "sla_events": events}

    return router
