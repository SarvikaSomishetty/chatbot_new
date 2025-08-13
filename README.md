# Customer Support Chatbot

A modern customer support chatbot application with user authentication, ticket management, and real-time chat functionality. Built with React, FastAPI, MongoDB, and PostgreSQL.

## 🚀 Features

- ✅ User authentication with JWT tokens
- ✅ Secure password hashing with bcrypt
- ✅ MongoDB storage for user data and chat messages
- ✅ PostgreSQL storage for ticket management
- ✅ Modern React frontend with TypeScript
- ✅ Real-time chat interface
- ✅ Domain-based ticket categorization
- ✅ Responsive design with Tailwind CSS

## 📋 Prerequisites

Before running this application, make sure you have the following installed:

- **Node.js** (v16 or higher)
- **Python** (v3.8 or higher)
- **MongoDB** (v4.4 or higher)
- **PostgreSQL** (v12 or higher)

## 🛠️ Installation & Setup

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd Chatbot
```

### 2. Install Dependencies

**Frontend Dependencies:**

```bash
npm install
```

**Backend Dependencies:**

```bash
cd backend
pip install -r requirements.txt
cd ..
```

### 3. Database Setup

#### MongoDB Setup

1. **Start MongoDB:**

   ```bash
   mongod
   ```

   _Keep this running in a separate terminal_

2. **Verify MongoDB Connection:**
   - MongoDB will run on `mongodb://localhost:27017`
   - The application will automatically create the `tickets_db` database
   - Collections (`users`, `ticket_messages`) will be created automatically

#### PostgreSQL Setup

1. **Start PostgreSQL:**

   ```bash
   # On Windows (if installed as service)
   # PostgreSQL should start automatically

   # On macOS/Linux
   sudo service postgresql start
   # or
   brew services start postgresql
   ```

2. **Create Database and User:**

   ```sql
   -- Connect to PostgreSQL
   psql -U postgres

   -- Create database
   CREATE DATABASE tickets;

   -- Create user
   CREATE USER admin WITH PASSWORD 'adminpass';

   -- Grant privileges
   GRANT ALL PRIVILEGES ON DATABASE tickets TO admin;

   -- Exit
   \q
   ```

3. **Alternative: Use Docker for PostgreSQL:**
   ```bash
   docker run --name postgres-tickets -e POSTGRES_DB=tickets -e POSTGRES_USER=admin -e POSTGRES_PASSWORD=adminpass -p 5432:5432 -d postgres:13
   ```

### 4. Start the Application

#### Start Backend Server

```bash
cd backend
python main.py
```

The backend will start on `http://localhost:8000`

#### Start Frontend Development Server

```bash
npm run dev
```

The frontend will start on `http://localhost:5173`

## 🔐 Authentication System

### Database Collections

#### MongoDB Collections (`tickets_db`)

**Users Collection:**

```json
{
  "_id": "user-uuid",
  "email": "user@example.com",
  "password": "hashed-password",
  "name": "User Name",
  "created_at": "2024-01-01T12:00:00Z"
}
```

**Ticket Messages Collection:**

```json
{
  "ticket_id": "ticket-uuid",
  "message": "User message content",
  "sender": "user",
  "created_at": "2024-01-01T12:00:00Z",
  "metadata": {
    "domain": "technical",
    "priority": "medium",
    "user_id": "user-uuid"
  }
}
```

#### PostgreSQL Tables (`tickets` database)

**Tickets Table:**

```sql
CREATE TABLE tickets (
    ticket_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    domain VARCHAR(100) NOT NULL,
    subject TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'Open',
    priority VARCHAR(50) NOT NULL,
    sla_deadline TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### API Endpoints

#### Authentication Endpoints

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user info (protected)

#### Ticket Endpoints

- `POST /api/tickets` - Create new ticket
- `GET /api/tickets/{ticket_id}` - Get ticket details

### Security Features

- **JWT Token Authentication** - Secure token-based authentication
- **Password Hashing** - bcrypt for secure password storage
- **Email Validation** - Proper email format validation
- **Token Expiration** - 30-minute token expiration
- **CORS Protection** - Configured for development

## 🧪 Testing the Application

### 1. Create a New Account

1. Open `http://localhost:5173`
2. Click "Get Started" → "Login"
3. Click "Sign up here"
4. Fill in the registration form:
   - Name: Your full name
   - Email: your-email@example.com
   - Password: your-password
5. Click "Create Account"

### 2. Login

1. Use your registered email and password
2. Or use the sample account:
   - Email: `test@example.com`
   - Password: `test123`

### 3. Verify Data in MongoDB Compass

1. Open MongoDB Compass
2. Connect to: `mongodb://localhost:27017`
3. Navigate to: `tickets_db` → `users` collection
4. You should see your registered user

### 4. Create Tickets

1. After login, select a domain
2. Start chatting with the bot
3. Create tickets and check PostgreSQL for ticket data

## 📊 Database Management

### MongoDB Compass

- **Connection String:** `mongodb://localhost:27017`
- **Database:** `tickets_db`
- **Collections:** `users`, `ticket_messages`

### PostgreSQL Management

- **Host:** `localhost`
- **Port:** `5432`
- **Database:** `tickets`
- **User:** `admin`
- **Password:** `adminpass`

## 🔧 Configuration

### Backend Configuration

The backend uses the following default configuration:

```python
# MongoDB
MONGODB_URI = "mongodb://localhost:27017"
MONGODB_DB = "tickets_db"

# PostgreSQL
POSTGRES_HOST = "localhost"
POSTGRES_PORT = 5432
POSTGRES_USER = "admin"
POSTGRES_PASSWORD = "adminpass"
POSTGRES_DB = "tickets"

# JWT
SECRET_KEY = "yF0QdmI6zNQHvoSwuaNYFd%VfQ7Yt@$o"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 30
```

### Frontend Configuration

The frontend connects to the backend API at `http://localhost:8000`

## 🚨 Troubleshooting

### Common Issues

1. **MongoDB Connection Error:**

   - Ensure MongoDB is running: `mongod`
   - Check if MongoDB is on port 27017

2. **PostgreSQL Connection Error:**

   - Ensure PostgreSQL is running
   - Verify database and user exist
   - Check connection credentials

3. **Port Already in Use:**

   - Backend: Change port in `backend/main.py` line 295
   - Frontend: Change port in `vite.config.ts`

4. **Missing Dependencies:**

   ```bash
   # Backend
   pip install fastapi uvicorn motor asyncpg bcrypt PyJWT email-validator

   # Frontend
   npm install
   ```

### Database Reset

To reset the databases:

**MongoDB:**

```bash
# Connect to MongoDB shell
mongosh
use tickets_db
db.dropDatabase()
```

**PostgreSQL:**

```sql
-- Connect to PostgreSQL
psql -U admin -d tickets

-- Drop and recreate tables
DROP TABLE IF EXISTS tickets;
```

## 📁 Project Structure

```
Chatbot/
├── backend/
│   ├── main.py              # FastAPI backend server
│   └── requirements.txt     # Python dependencies
├── src/
│   ├── components/          # React components
│   ├── pages/              # Page components
│   ├── contexts/           # React contexts
│   └── types/              # TypeScript types
├── package.json            # Node.js dependencies
└── README.md              # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

If you encounter any issues:

1. Check the troubleshooting section above
2. Verify all prerequisites are installed
3. Ensure databases are running
4. Check console logs for error messages

---

**Happy Coding! 🚀**
