import asyncio
from datetime import datetime
from uuid import uuid4

async def sla_background_task(get_pg_pool, mongo_db):
    while True:
        try:
            pool = await get_pg_pool()
            async with pool.acquire() as conn:
                rows = await conn.fetch("SELECT ticket_id, sla_deadline, status FROM tickets WHERE status='Open'")
                for row in rows:
                    if row['sla_deadline'] < datetime.utcnow():
                        await conn.execute(
                            "UPDATE tickets SET status='Breached', updated_at=NOW() WHERE ticket_id=$1",
                            row['ticket_id']
                        )
                        await conn.execute(
                            "INSERT INTO sla_events (event_id, ticket_id, event, timestamp) VALUES ($1, $2, $3, NOW())",
                            str(uuid4()), row['ticket_id'], "SLA Breached"
                        )
                        await mongo_db.sla_events.insert_one({
                            "ticket_id": row['ticket_id'],
                            "event": "SLA Breached",
                            "timestamp": datetime.utcnow()
                        })
            await pool.close()
        except Exception as e:
            print(f"[SLA CHECKER ERROR] {str(e)}")
        await asyncio.sleep(300)  # 10 seconds for testing

async def start_sla_checker(app, get_pg_pool, mongo_db):
    asyncio.create_task(sla_background_task(get_pg_pool, mongo_db))
