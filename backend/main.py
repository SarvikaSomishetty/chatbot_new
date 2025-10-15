import os
from dotenv import load_dotenv

load_dotenv() 

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from uuid import uuid4
from datetime import datetime, timedelta
import asyncpg
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt
import jwt
from typing import Optional
from contextlib import asynccontextmanager
from notification_service import notification_service

# Import SLA modules
from sla import sla_checker
from sla.sla_utils import calculate_sla_deadline
from sla.sla_routes import get_sla_router
from redis_client import init_redis, close_redis, push_message, get_messages

# Import chatbot module
from chatbot import GeminiChatbot, ChatQuery, ChatResponse

# Initialize chatbot
chatbot = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # PostgreSQL tables
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
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS sla_events (
                event_id VARCHAR(36) PRIMARY KEY,
                ticket_id VARCHAR(36) NOT NULL,
                event VARCHAR(100) NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    await pool.close()

    # Create default admin user if it doesn't exist
    existing_admin = await mongo_db.admins.find_one({"username": "admin"})
    if not existing_admin:
        admin_id = str(uuid4())
        hashed_password = hash_password("admin123")
        admin_doc = {
            "_id": admin_id,
            "username": "admin",
            "password": hashed_password,
            "role": "admin",
            "created_at": datetime.utcnow(),
        }
        await mongo_db.admins.insert_one(admin_doc)
        print("Default admin created: username=admin, password=admin123")

    # Start SLA background task
    await sla_checker.start_sla_checker(app, get_pg_pool, mongo_db)

    # Initialize Redis (use port 6380 per request)
    try:
        await init_redis(host="localhost", port=6380, db=0)
        print("Redis initialized on localhost:6380")
    except Exception as e:
        print(f"Could not initialize Redis: {e}")
    
    # Initialize chatbot
    global chatbot
    try:
        import redis
        redis_client = redis.Redis(host="localhost", port=6380, db=0, decode_responses=True)
        # Test Redis connection
        redis_client.ping()
        chatbot = GeminiChatbot(mongo_db, redis_client)
        print("Chatbot initialized successfully")
    except Exception as e:
        print(f"Could not initialize chatbot: {e}")
        # Create chatbot without Redis if Redis fails
        try:
            chatbot = GeminiChatbot(mongo_db, None)
            print("Chatbot initialized without Redis")
        except Exception as e2:
            print(f"Could not initialize chatbot at all: {e2}")

    yield
    
    # Shutdown
    try:
        await close_redis()
        print("Redis connection closed")
    except Exception as e:
        print(f"Error closing Redis: {e}")

app = FastAPI(title="Chatbot Ticket API", version="1.0.0", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
SECRET_KEY = "yF0QdmI6zNQHvoSwuaNYFd%VfQ7Yt@$o"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
security = HTTPBearer()

# PostgreSQL connection
async def get_pg_pool():
    return await asyncpg.create_pool(
        user="admin",
        password="adminpass",
        database="tickets",
        host="localhost",
        port=5432,
    )

# MongoDB connection
mongo_client = AsyncIOMotorClient("mongodb://localhost:27017")
mongo_db = mongo_client["tickets_db"]

# Pydantic models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


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


# Admin models
class AdminLogin(BaseModel):
    username: str
    password: str


class AdminResponse(BaseModel):
    id: str
    username: str
    role: str
    created_at: datetime


class AdminToken(BaseModel):
    access_token: str
    token_type: str
    admin: AdminResponse


class TicketUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    notes: Optional[str] = None


class ChatMessageIn(BaseModel):
    ticket_id: str
    message: str
    sender: str
    metadata: Optional[dict] = None


class TicketDetails(BaseModel):
    ticket_id: str
    user_id: str
    domain: str
    subject: str
    status: str
    priority: str
    sla_deadline: datetime
    created_at: datetime
    updated_at: datetime
    user_name: Optional[str] = None
    user_email: Optional[str] = None


# New model for ticket resolution
class TicketResolution(BaseModel):
    resolution_notes: Optional[str] = None


# Helper functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    user = await mongo_db.users.find_one({"_id": user_id})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return UserResponse(
        id=user["_id"], email=user["email"], name=user["name"], created_at=user["created_at"]
    )


async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        admin_id: str = payload.get("sub")
        role: str = payload.get("role")
        if admin_id is None or role != "admin":
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    admin = await mongo_db.admins.find_one({"_id": admin_id})
    if admin is None:
        raise HTTPException(status_code=401, detail="Admin not found")

    return AdminResponse(
        id=admin["_id"],
        username=admin["username"],
        role=admin["role"],
        created_at=admin["created_at"]
    )


@app.get("/")
async def root():
    return {"message": "Chatbot Ticket API is running!"}


# -------------------- Include SLA routes --------------------
app.include_router(get_sla_router(get_pg_pool, mongo_db))


# -------------------- Chatbot AI Routes --------------------
@app.post("/ask", response_model=ChatResponse)
async def ask_question(query: ChatQuery):
    """Main chatbot endpoint - ask AI a question"""
    if not chatbot:
        raise HTTPException(status_code=500, detail="Chatbot not initialized")
    
    try:
        response = await chatbot.process_query(query)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")

@app.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation history"""
    if not chatbot:
        raise HTTPException(status_code=500, detail="Chatbot not initialized")
    
    try:
        summary = await chatbot.get_conversation_summary(conversation_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversation: {str(e)}")

@app.get("/conversations")
async def list_conversations():
    """List all conversations for debugging"""
    if not chatbot:
        raise HTTPException(status_code=500, detail="Chatbot not initialized")
    
    try:
        conversations = await chatbot.list_all_conversations()
        return {"conversations": conversations, "total": len(conversations)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list conversations: {str(e)}")

@app.get("/domains")
async def get_supported_domains():
    """Get list of supported domains"""
    from chatbot import DOMAIN_CONTEXTS
    return {
        "domains": [
            {
                "id": domain.lower().replace(" ", "-"),
                "name": domain,
                "description": "Expert AI assistance in " + domain.lower()
            }
            for domain, context in DOMAIN_CONTEXTS.items()
        ]
    }


# -------------------- Auth, Ticket, Admin routes --------------------
@app.get("/api/admin/test")
async def test_admin_connections():
    try:
        # Test PostgreSQL
        pool = await get_pg_pool()
        async with pool.acquire() as conn:
            ticket_count = await conn.fetchval("SELECT COUNT(*) FROM tickets")
        await pool.close()

        # Test MongoDB
        user_count = await mongo_db.users.count_documents({})

        return {
            "postgresql_connected": True,
            "mongodb_connected": True,
            "ticket_count": ticket_count,
            "user_count": user_count,
        }
    except Exception as e:
        return {
            "postgresql_connected": False,
            "mongodb_connected": False,
            "error": str(e),
        }


@app.post("/api/auth/register", response_model=Token)
async def register_user(user: UserCreate):
    try:
        existing_user = await mongo_db.users.find_one({"email": user.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        user_id = str(uuid4())
        hashed_password = hash_password(user.password)
        user_doc = {
            "_id": user_id,
            "email": user.email,
            "password": hashed_password,
            "name": user.name,
            "created_at": datetime.utcnow(),
        }
        await mongo_db.users.insert_one(user_doc)

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_id}, expires_delta=access_token_expires
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(
                id=user_id,
                email=user.email,
                name=user.name,
                created_at=user_doc["created_at"],
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register user: {str(e)}")


@app.post("/api/auth/login", response_model=Token)
async def login_user(user_credentials: UserLogin):
    try:
        user = await mongo_db.users.find_one({"email": user_credentials.email})
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not verify_password(user_credentials.password, user["password"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["_id"]}, expires_delta=access_token_expires
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(
                id=user["_id"],
                email=user["email"],
                name=user["name"],
                created_at=user["created_at"],
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to login: {str(e)}")


@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    return current_user


# Ticket routes
@app.post("/api/tickets", response_model=TicketResponse)
async def create_ticket(ticket: TicketCreate):
    try:
        ticket_id = str(uuid4())
        deadline = calculate_sla_deadline(ticket.priority)

        pool = await get_pg_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO tickets (ticket_id, user_id, domain, subject, status, priority, sla_deadline)
                VALUES ($1, $2, $3, $4, 'Open', $5, $6)
            """,
                ticket_id,
                ticket.user_id,
                ticket.domain,
                ticket.summary,
                ticket.priority,
                deadline,
            )
        await pool.close()

        await mongo_db.ticket_messages.insert_one({
            "ticket_id": ticket_id,
            "message": ticket.summary,
            "sender": "user",
            "created_at": datetime.utcnow(),
            "metadata": {
                "domain": ticket.domain,
                "priority": ticket.priority,
                "user_id": ticket.user_id,
            },
        })

        # Also store the message in Redis for fast access / chat storage
        try:
            await push_message(
                ticket_id,
                {
                    "ticket_id": ticket_id,
                    "message": ticket.summary,
                    "sender": "user",
                    "created_at": datetime.utcnow().isoformat(),
                    "metadata": {
                        "domain": ticket.domain,
                        "priority": ticket.priority,
                        "user_id": ticket.user_id,
                    },
                },
            )
        except Exception as e:
            print(f"Warning: failed to push message to Redis: {e}")

        return TicketResponse(
            ticket_id=ticket_id,
            status="created",
            sla_deadline=deadline,
            message="Ticket created successfully",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create ticket: {str(e)}")


@app.get("/api/tickets/{ticket_id}")
async def get_ticket(ticket_id: str):
    try:
        pool = await get_pg_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM tickets WHERE ticket_id = $1", ticket_id)
        await pool.close()

        if not row:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return dict(row)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve ticket: {str(e)}")


# Admin endpoints
@app.post("/api/admin/login", response_model=AdminToken)
async def admin_login(admin_credentials: AdminLogin):
    try:
        # Find admin by username
        admin = await mongo_db.admins.find_one({"username": admin_credentials.username})
        if not admin:
            raise HTTPException(status_code=401, detail="Invalid username or password")

        # Verify password
        if not verify_password(admin_credentials.password, admin["password"]):
            raise HTTPException(status_code=401, detail="Invalid username or password")

        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": admin["_id"], "role": "admin"}, expires_delta=access_token_expires
        )

        return AdminToken(
            access_token=access_token,
            token_type="bearer",
            admin=AdminResponse(
                id=admin["_id"],
                username=admin["username"],
                role=admin["role"],
                created_at=admin["created_at"],
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to login: {str(e)}")


@app.get("/api/admin/me", response_model=AdminResponse)
async def get_current_admin_info(current_admin: AdminResponse = Depends(get_current_admin)):
    return current_admin


@app.get("/api/admin/tickets")
async def get_all_tickets(current_admin: AdminResponse = Depends(get_current_admin)):
    try:
        # First try to get tickets from PostgreSQL
        pool = await get_pg_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM tickets
                ORDER BY created_at DESC
            """)
        await pool.close()

        tickets = []
        for row in rows:
            # Try to get user info from MongoDB, but don't fail if it doesn't work
            user = None
            try:
                user = await mongo_db.users.find_one({"_id": row["user_id"]})
            except Exception as user_error:
                print(f"Could not fetch user {row['user_id']}: {user_error}")

            tickets.append(
                {
                    "ticket_id": str(row["ticket_id"]),
                    "user_id": str(row["user_id"]),
                    "domain": str(row["domain"]),
                    "subject": str(row["subject"]),
                    "status": str(row["status"]),
                    "priority": str(row["priority"]),
                    "sla_deadline": row["sla_deadline"].isoformat()
                    if row["sla_deadline"]
                    else None,
                    "created_at": row["created_at"].isoformat()
                    if row["created_at"]
                    else None,
                    "updated_at": row["updated_at"].isoformat()
                    if row["updated_at"]
                    else None,
                    "user_name": user["name"] if user else "Unknown User",
                    "user_email": user["email"] if user else "unknown@example.com",
                }
            )

        return tickets

    except Exception as e:
        print(f"Error in get_all_tickets: {str(e)}")  # Debug print
        # Return empty list instead of error for now
        return []


# Helper to fix ObjectId in a list of MongoDB documents
def fix_objectid_list(docs):
    for doc in docs:
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])
    return docs


@app.get("/api/admin/tickets/{ticket_id}")
async def get_ticket_details(ticket_id: str, current_admin: AdminResponse = Depends(get_current_admin)):
    try:
        pool = await get_pg_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM tickets
                WHERE ticket_id = $1
            """,
                ticket_id,
            )
        await pool.close()

        if not row:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # Try to get user info from MongoDB
        user = None
        try:
            user = await mongo_db.users.find_one({"_id": row["user_id"]})
        except Exception as user_error:
            print(f"Could not fetch user {row['user_id']}: {user_error}")

        # Try to get ticket messages from MongoDB
        messages = []
        try:
            messages = await mongo_db.ticket_messages.find({"ticket_id": ticket_id}).sort(
                "created_at", 1
            ).to_list(length=None)
            messages = fix_objectid_list(messages)
        except Exception as msg_error:
            print(f"Could not fetch messages for ticket {ticket_id}: {msg_error}")

        # Also attempt to fetch messages from Redis and merge (Redis messages are stored as dicts)
        redis_messages = []
        try:
            redis_messages = await get_messages(ticket_id)
        except Exception as redis_err:
            print(f"Could not fetch Redis messages for ticket {ticket_id}: {redis_err}")

        # Merge messages: prefer Redis messages (fast), fall back to MongoDB if Redis is empty
        if redis_messages:
            # Redis messages already have ISO timestamps and are dicts
            messages = redis_messages

        return {
            "ticket_id": str(row["ticket_id"]),
            "user_id": str(row["user_id"]),
            "domain": str(row["domain"]),
            "subject": str(row["subject"]),
            "status": str(row["status"]),
            "priority": str(row["priority"]),
            "sla_deadline": row["sla_deadline"].isoformat() if row["sla_deadline"] else None,
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
            "user_name": user["name"] if user else "Unknown User",
            "user_email": user["email"] if user else "unknown@example.com",
            "messages": messages,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_ticket_details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve ticket: {str(e)}")


@app.put("/api/admin/tickets/{ticket_id}")
async def update_ticket(
    ticket_id: str, ticket_update: TicketUpdate, current_admin: AdminResponse = Depends(get_current_admin)
):
    try:
        pool = await get_pg_pool()

        # Build update query dynamically
        update_fields = []
        params = []
        param_count = 1

        if ticket_update.status is not None:
            update_fields.append(f"status = ${param_count}")
            params.append(ticket_update.status)
            param_count += 1

        if ticket_update.priority is not None:
            update_fields.append(f"priority = ${param_count}")
            params.append(ticket_update.priority)
            param_count += 1

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        update_fields.append(f"updated_at = CURRENT_TIMESTAMP")
        params.append(ticket_id)

        # Get user_id before updating for potential email notification
        user_id = None
        if ticket_update.status and ticket_update.status.lower() == "resolved":
            async with pool.acquire() as conn:
                user_id_row = await conn.fetchrow("SELECT user_id FROM tickets WHERE ticket_id = $1", ticket_id)
                if user_id_row:
                    user_id = user_id_row['user_id']

        async with pool.acquire() as conn:
            await conn.execute(
                f"""
                UPDATE tickets 
                SET {', '.join(update_fields)}
                WHERE ticket_id = ${param_count}
            """,
                *params,
            )
        await pool.close()

        # Add admin note to MongoDB if provided
        if ticket_update.notes:
            await mongo_db.ticket_messages.insert_one(
                {
                    "ticket_id": ticket_id,
                    "message": f"[Admin Note] {ticket_update.notes}",
                    "sender": "admin",
                    "created_at": datetime.utcnow(),
                    "metadata": {
                        "admin_id": current_admin.id,
                        "admin_username": current_admin.username,
                    },
                }
            )
            # Also push admin note to Redis
            try:
                await push_message(
                    ticket_id,
                    {
                        "ticket_id": ticket_id,
                        "message": f"[Admin Note] {ticket_update.notes}",
                        "sender": "admin",
                        "created_at": datetime.utcnow().isoformat(),
                        "metadata": {
                            "admin_id": current_admin.id,
                            "admin_username": current_admin.username,
                        },
                    },
                )
            except Exception as e:
                print(f"Warning: failed to push admin note to Redis: {e}")

        # Send resolution email if ticket resolved
        if ticket_update.status and ticket_update.status.lower() == "resolved" and user_id:
            # Get user details for notification
            user = await mongo_db.users.find_one({"_id": user_id})
            if user:
                try:
                    notification_sent = await notification_service.send_ticket_resolved_notification(
                        user_email=user['email'],
                        user_name=user['name'],
                        ticket_id=ticket_id,
                        resolution_notes=ticket_update.notes or ""
                    )
                    print(f"✅ Resolution notification sent: {notification_sent}")
                except Exception as email_error:
                    print(f"❌ Failed to send email notification: {email_error}")

        return {"message": "Ticket updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update ticket: {str(e)}")


@app.put("/api/admin/tickets/{ticket_id}/resolve")
async def admin_resolve_ticket(ticket_id: str, resolution: TicketResolution, current_admin: AdminResponse = Depends(get_current_admin)):
    """Admin endpoint to resolve a ticket and send notification to user"""
    try:
        pool = await get_pg_pool()
        
        # First, get the ticket details
        async with pool.acquire() as conn:
            ticket_row = await conn.fetchrow("""
                SELECT * FROM tickets WHERE ticket_id = $1
            """, ticket_id)
        
        if not ticket_row:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        if ticket_row['status'] == 'Resolved':
            raise HTTPException(status_code=400, detail="Ticket is already resolved")
        
        # Update ticket status to resolved
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE tickets 
                SET status = 'Resolved', updated_at = CURRENT_TIMESTAMP
                WHERE ticket_id = $1
            """, ticket_id)
            
            # Log the resolution event
            await conn.execute("""
                INSERT INTO sla_events (event_id, ticket_id, event, timestamp) 
                VALUES ($1, $2, $3, NOW())
            """, str(uuid4()), ticket_id, "Ticket Resolved by Admin")
        
        await pool.close()
        
        # Add resolution message to MongoDB
        await mongo_db.ticket_messages.insert_one({
            "ticket_id": ticket_id,
            "message": f"[ADMIN] Ticket resolved by {current_admin.username}" + (f"\nResolution Notes: {resolution.resolution_notes}" if resolution.resolution_notes else ""),
            "sender": "admin",
            "created_at": datetime.utcnow(),
            "metadata": {
                "event_type": "admin_resolution",
                "admin_id": current_admin.id,
                "admin_username": current_admin.username,
                "resolution_notes": resolution.resolution_notes
            }
        })
        
        # Get user details for notification
        user = await mongo_db.users.find_one({"_id": ticket_row['user_id']})
        notification_sent = False
        
        if user:
            # Send resolution notification
            notification_sent = await notification_service.send_ticket_resolved_notification(
                user_email=user['email'],
                user_name=user['name'],
                ticket_id=ticket_id,
                resolution_notes=resolution.resolution_notes or ""
            )
        
        return {
            "message": "Ticket resolved successfully",
            "ticket_id": ticket_id,
            "status": "Resolved",
            "resolved_by": current_admin.username,
            "notification_sent": notification_sent
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve ticket: {str(e)}")


@app.post("/api/chat/messages")
async def save_chat_message(msg: ChatMessageIn):
    """Accept a chat message from frontend, persist to MongoDB (historical) and push to Redis list for fast access."""
    try:
        created_at = datetime.utcnow()
        # Persist to MongoDB
        await mongo_db.ticket_messages.insert_one({
            "ticket_id": msg.ticket_id,
            "message": msg.message,
            "sender": msg.sender,
            "created_at": created_at,
            "metadata": msg.metadata or {},
        })

        # Push to Redis for fast retrieval
        try:
            await push_message(
                msg.ticket_id,
                {
                    "ticket_id": msg.ticket_id,
                    "message": msg.message,
                    "sender": msg.sender,
                    "created_at": created_at.isoformat(),
                    "metadata": msg.metadata or {},
                },
            )
        except Exception as e:
            print(f"Warning: failed to push message to Redis: {e}")

        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save chat message: {str(e)}")


from bson import ObjectId


# Helper to fix ObjectId serialization
def fix_objectid(doc):
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


@app.get("/api/admin/users")
async def get_all_users(current_admin: AdminResponse = Depends(get_current_admin)):
    try:
        users = await mongo_db.users.find({}, {"password": 0}).sort("created_at", -1).to_list(length=None)

        # Get ticket counts for each user
        pool = await get_pg_pool()
        async with pool.acquire() as conn:
            for user in users:
                ticket_count = await conn.fetchval(
                    """
                    SELECT COUNT(*) FROM tickets WHERE user_id = $1
                """,
                    user["_id"],
                )
                user["ticket_count"] = ticket_count
        await pool.close()

        # Fix ObjectId for all users
        users = [fix_objectid(user) for user in users]
        return users

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve users: {str(e)}")


@app.get("/api/admin/stats")
async def get_admin_stats(current_admin: AdminResponse = Depends(get_current_admin)):
    try:
        pool = await get_pg_pool()
        async with pool.acquire() as conn:
            # Total tickets
            total_tickets = await conn.fetchval("SELECT COUNT(*) FROM tickets")

            # Tickets by status
            status_counts = await conn.fetch(
                """
                SELECT status, COUNT(*) as count 
                FROM tickets 
                GROUP BY status
            """
            )

            # Tickets by priority
            priority_counts = await conn.fetch(
                """
                SELECT priority, COUNT(*) as count 
                FROM tickets 
                GROUP BY priority
            """
            )

            # Tickets by domain
            domain_counts = await conn.fetch(
                """
                SELECT domain, COUNT(*) as count 
                FROM tickets 
                GROUP BY domain
            """
            )

            # Recent tickets (last 7 days)
            recent_tickets = await conn.fetchval(
                """
                SELECT COUNT(*) FROM tickets 
                WHERE created_at >= NOW() - INTERVAL '7 days'
            """
            )

        await pool.close()

        # Total users
        total_users = await mongo_db.users.count_documents({})

        return {
            "total_tickets": total_tickets,
            "total_users": total_users,
            "recent_tickets": recent_tickets,
            "status_breakdown": {row["status"]: row["count"] for row in status_counts},
            "priority_breakdown": {row["priority"]: row["count"] for row in priority_counts},
            "domain_breakdown": {row["domain"]: row["count"] for row in domain_counts},
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve stats: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)



