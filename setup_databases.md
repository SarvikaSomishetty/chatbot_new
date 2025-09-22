# Database Setup Instructions

## The Issue

The admin dashboard is getting 500 errors because PostgreSQL and MongoDB aren't running or configured properly.

## Quick Fix - Use SQLite Instead

Let me create a simpler version that uses SQLite instead of PostgreSQL to avoid database setup issues.

## Option 1: Install Required Databases

### PostgreSQL Setup

1. Download and install PostgreSQL from https://www.postgresql.org/download/
2. Create a database called `tickets`
3. Create a user `admin` with password `adminpass`

### MongoDB Setup

1. Download and install MongoDB from https://www.mongodb.com/try/download/community
2. Start MongoDB service

## Option 2: Use Docker (Recommended)

Create a `docker-compose.yml` file in your project root:

```yaml
version: "3.8"
services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: tickets
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: adminpass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  mongodb:
    image: mongo:4.4
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db

volumes:
  postgres_data:
  mongodb_data:
```

Then run:

```bash
docker-compose up -d
```

## Option 3: Simplified Version (No External Databases)

I can modify the backend to use SQLite and JSON files instead of PostgreSQL and MongoDB. This would eliminate the database setup requirements entirely.

Which option would you prefer?
