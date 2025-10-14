# 🤖 Customer Support Chatbot with Gemini AI

A modern, full-stack customer support chatbot built with React, FastAPI, and Google's Gemini AI. Features domain-specific AI assistance, conversation history, and ticket management.

## 🏗️ Architecture

- **Frontend**: React + TypeScript + Tailwind CSS
- **Backend**: FastAPI + Python
- **AI**: Google Gemini AI (gemini-1.5-flash)
- **Database**: MongoDB (conversations) + PostgreSQL (tickets)
- **Cache**: Redis (fast message access)
- **Authentication**: JWT tokens

## ✨ Features

### 🤖 AI-Powered Chat

- Domain-specific AI assistants (Healthcare, Education, Finance, etc.)
- Context-aware conversations with memory
- Real-time responses using Gemini AI
- Conversation history persistence

### 🎯 Domain Support

- **Healthcare**: Medical information and health guidance
- **Education**: Learning support and educational guidance
- **Finance**: Personal finance and investment advice
- **Environment**: Environmental conservation and sustainability
- **Technology**: Software development and technical support
- **Customer Support**: General inquiries and product support
- **Technical Support**: System diagnostics and troubleshooting
- **Travel**: Travel planning and booking assistance

### 📊 Admin Dashboard

- Ticket management and SLA tracking
- User management
- Analytics and reporting
- Real-time monitoring

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- Redis server
- MongoDB
- PostgreSQL
- Gemini API key

### 1. Clone and Setup

```bash
git clone <your-repo>
cd customer_support_chatbot
python setup.py
```

### 2. Configure Environment

Edit `backend/.env`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
MONGODB_URL=mongodb://localhost:27017
REDIS_URL=redis://localhost:6380
POSTGRES_URL=postgresql://admin:adminpass@localhost:5432/tickets
```

### 3. Start Services

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start MongoDB
mongod

# Terminal 3: Start PostgreSQL (if not running)
# Follow your system's PostgreSQL startup instructions

# Terminal 4: Start Backend
cd backend
python main.py

# Terminal 5: Start Frontend
npm run dev
```

### 4. Access the Application

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 🔧 API Endpoints

### Chatbot Endpoints

- `POST /ask` - Ask AI a question
- `GET /conversation/{id}` - Get conversation history
- `GET /domains` - Get supported domains

### Authentication

- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user

### Tickets

- `POST /api/tickets` - Create ticket
- `GET /api/tickets/{id}` - Get ticket details
- `POST /api/chat/messages` - Save chat message

### Admin

- `POST /api/admin/login` - Admin login
- `GET /api/admin/tickets` - Get all tickets
- `GET /api/admin/users` - Get all users
- `GET /api/admin/stats` - Get analytics

## 🎨 Frontend Usage

### Basic Chat Integration

```typescript
// Send a question to the AI
const response = await fetch("http://localhost:8000/ask", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    user_id: "user123",
    domain: "Healthcare",
    question: "What are the symptoms of flu?",
    conversation_id: "optional-conversation-id",
  }),
});

const data = await response.json();
console.log(data.answer); // AI response
```

### Domain Selection

```typescript
// Get available domains
const domains = await fetch("http://localhost:8000/domains");
const data = await domains.json();
console.log(data.domains); // Array of supported domains
```

## 🗄️ Database Schema

### MongoDB Collections

#### conversations

```json
{
  "conversation_id": "conv_user123_1234567890",
  "user_id": "user123",
  "domain": "Healthcare",
  "messages": [
    {
      "role": "user",
      "content": "What are flu symptoms?",
      "timestamp": "2024-01-01T12:00:00Z"
    },
    {
      "role": "assistant",
      "content": "Common flu symptoms include...",
      "timestamp": "2024-01-01T12:00:30Z"
    }
  ],
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:30Z"
}
```

### PostgreSQL Tables

#### tickets

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

## 🔐 Authentication

### User Authentication

```typescript
// Register
const registerResponse = await fetch("/api/auth/register", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    email: "user@example.com",
    password: "password123",
    name: "John Doe",
  }),
});

// Login
const loginResponse = await fetch("/api/auth/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    email: "user@example.com",
    password: "password123",
  }),
});
```

### Admin Authentication

```typescript
// Admin login
const adminLogin = await fetch("/api/admin/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    username: "admin",
    password: "admin123",
  }),
});
```

## 🎯 Domain Configuration

### Adding New Domains

Edit `backend/chatbot.py`:

```python
DOMAIN_CONTEXTS = {
    "Your Domain": """
    You are an expert in Your Domain AI assistant. You can help with:
    - Specific expertise area 1
    - Specific expertise area 2
    - Specific expertise area 3

    Provide helpful, accurate guidance in this domain.
    """
}
```

### Customizing AI Responses

```python
# In chatbot.py, modify the ask_llm function
async def ask_llm(self, prompt: str, temperature: float = 0.7) -> str:
    try:
        response = self.model.generate_content(
            prompt,
            generation_config={
                'temperature': temperature,  # Adjust creativity (0-1)
                'max_output_tokens': 1000,  # Adjust response length
                'top_p': 0.8,              # Adjust response diversity
                'top_k': 40                 # Adjust vocabulary selection
            }
        )
        return response.text
    except Exception as e:
        return f"Error: {e}"
```

## 🚀 Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build
```

### Environment Variables for Production

```env
GEMINI_API_KEY=your_production_api_key
MONGODB_URL=mongodb://your-mongo-host:27017
REDIS_URL=redis://your-redis-host:6380
POSTGRES_URL=postgresql://user:pass@your-postgres-host:5432/tickets
SECRET_KEY=your-secure-secret-key
```

## 🧪 Testing

### Backend Tests

```bash
cd backend
python -m pytest tests/
```

### Frontend Tests

```bash
npm test
```

## 📊 Monitoring

### Health Checks

- Backend: `GET /` - API status
- Admin: `GET /api/admin/test` - Database connections

### Metrics

- Response times
- Conversation counts
- Error rates
- User engagement

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:

1. Check the [Issues](../../issues) page
2. Create a new issue with detailed information
3. Include logs and error messages

## 🔗 Links

- [Gemini AI Documentation](https://ai.google.dev/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [MongoDB Documentation](https://docs.mongodb.com/)
- [Redis Documentation](https://redis.io/docs/)
