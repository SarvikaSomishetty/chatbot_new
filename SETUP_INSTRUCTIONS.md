# 🚀 Complete Ticket System Setup Guide

This guide will help you set up the complete ticket system with frontend, backend API, PostgreSQL, and MongoDB.

## 📋 Prerequisites

- Docker and Docker Compose
- Node.js (v16 or higher)
- Python (v3.8 or higher)
- pip (Python package manager)

## 🗄️ Step 1: Start the Databases

First, start PostgreSQL and MongoDB using Docker Compose:

```bash
docker-compose up -d postgres mongodb
```

This will start:

- PostgreSQL on `localhost:5432`
- MongoDB on `localhost:27017`

## 🐍 Step 2: Set Up the Backend

1. **Install Python dependencies:**

   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Start the FastAPI server:**

   ```bash
   cd backend
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

   The API will be available at: `http://localhost:8000`

   - API docs: `http://localhost:8000/docs`
   - Root endpoint: `http://localhost:8000/`

## ⚛️ Step 3: Start the Frontend

1. **Install Node.js dependencies:**

   ```bash
   npm install
   ```

2. **Start the development server:**

   ```bash
   npm run dev
   ```

   The frontend will be available at: `http://localhost:5173`

## 🧪 Step 4: Test the Complete Flow

1. **Test the API directly:**

   ```bash
   python test_api.py
   ```

2. **Test through the frontend:**
   - Open `http://localhost:5173`
   - Navigate to any domain (e.g., Travel)
   - Click "Create Ticket"
   - Fill out the form and submit
   - Check the success message with ticket ID

## 📊 Step 5: Verify Data Storage

### PostgreSQL Check:

```bash
# Connect to PostgreSQL container
docker exec -it postgres psql -U admin -d tickets

# List all tickets
SELECT * FROM tickets;

# Exit
\q
```

### MongoDB Check:

```bash
# Connect to MongoDB container
docker exec -it mongodb mongosh -u admin -p adminpass

# Switch to database
use tickets_db

# List all ticket messages
db.ticket_messages.find()

# Exit
exit
```

## 🔧 API Endpoints

### Create Ticket

```http
POST http://localhost:8000/api/tickets
Content-Type: application/json

{
  "user_id": "user123",
  "domain": "Travel",
  "summary": "Flight cancellation issue",
  "priority": "high"
}
```

### Get Ticket

```http
GET http://localhost:8000/api/tickets/{ticket_id}
```

## 🗂️ Project Structure

```
Chatbot/
├── backend/
│   ├── main.py              # FastAPI application
│   └── requirements.txt     # Python dependencies
├── src/
│   ├── components/
│   │   └── TicketModal.tsx  # Ticket creation form
│   └── ...
├── docker-compose.yml       # Database containers
├── test_api.py             # API testing script
└── SETUP_INSTRUCTIONS.md   # This file
```

## 🚨 Troubleshooting

### Database Connection Issues

- Ensure Docker containers are running: `docker ps`
- Check container logs: `docker logs postgres` or `docker logs mongodb`
- Restart containers: `docker-compose restart postgres mongodb`

### API Connection Issues

- Verify backend is running on port 8000
- Check CORS settings in `backend/main.py`
- Ensure frontend is making requests to `http://localhost:8000`

### Frontend Issues

- Clear browser cache
- Check browser console for errors
- Verify all dependencies are installed: `npm install`

## 🎯 Expected Flow

1. User fills out ticket form in frontend
2. Frontend sends POST request to `http://localhost:8000/api/tickets`
3. Backend creates ticket in PostgreSQL
4. Backend stores message in MongoDB
5. Backend returns ticket ID and SLA deadline
6. Frontend shows success message with ticket details

## 📈 Monitoring

- **API Health**: `http://localhost:8000/`
- **API Documentation**: `http://localhost:8000/docs`
- **Frontend**: `http://localhost:5173`
- **PostgreSQL**: `localhost:5432`
- **MongoDB**: `localhost:27017`

## 🎉 Success Indicators

✅ Frontend loads without errors  
✅ Ticket form submits successfully  
✅ Ticket ID is generated and displayed  
✅ Data appears in PostgreSQL tickets table  
✅ Message appears in MongoDB ticket_messages collection  
✅ SLA deadline is calculated correctly

---

**Happy coding! 🚀**
