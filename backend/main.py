from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from uuid import uuid4
from datetime import datetime, timedelta
import asyncpg
from motor.motor_asyncio import AsyncIOMotorClient
import os
import bcrypt
import jwt
from typing import Optional

app = FastAPI(title="Chatbot Ticket API", version="1.0.0")

# CORS middleware
app.add_middleware(
	CORSMiddleware,
	allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite dev server
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Security
SECRET_KEY = "yF0QdmI6zNQHvoSwuaNYFd%VfQ7Yt@$o"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

# PostgreSQL Connection
async def get_pg_pool():
	return await asyncpg.create_pool(
		user="admin",
		password="adminpass",
		database="tickets",
		host="localhost",
		port=5432,
	)

# MongoDB Connection
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

# Helper functions
def hash_password(password: str) -> str:
	return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
	return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
	to_encode = data.copy()
	if expires_delta:
		expire = datetime.utcnow() + expires_delta
	else:
		expire = datetime.utcnow() + timedelta(minutes=15)
	to_encode.update({"exp": expire})
	encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
	return encoded_jwt

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
		id=user["_id"],
		email=user["email"],
		name=user["name"],
		created_at=user["created_at"]
	)

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

@app.post("/api/auth/register", response_model=Token)
async def register_user(user: UserCreate):
	try:
		# Check if user already exists
		existing_user = await mongo_db.users.find_one({"email": user.email})
		if existing_user:
			raise HTTPException(status_code=400, detail="Email already registered")
		
		# Create new user
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
		
		# Create access token
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
			)
		)
		
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to register user: {str(e)}")

@app.post("/api/auth/login", response_model=Token)
async def login_user(user_credentials: UserLogin):
	try:
		# Find user by email
		user = await mongo_db.users.find_one({"email": user_credentials.email})
		if not user:
			raise HTTPException(status_code=401, detail="Invalid email or password")
		
		# Verify password
		if not verify_password(user_credentials.password, user["password"]):
			raise HTTPException(status_code=401, detail="Invalid email or password")
		
		# Create access token
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
			)
		)
		
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to login: {str(e)}")

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
	return current_user

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
				"user_id": ticket.user_id,
			},
		})
		
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
			"created_at": row['created_at'],
		}
		
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to retrieve ticket: {str(e)}")

if __name__ == "__main__":
	import uvicorn
	uvicorn.run(app, host="0.0.0.0", port=8000) 