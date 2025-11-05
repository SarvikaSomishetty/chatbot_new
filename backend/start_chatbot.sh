#!/bin/bash

# Customer Support Chatbot Startup Script
# This script helps start all required services

set -e

echo "🚀 Starting Customer Support Chatbot..."
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

# Function to wait for a service to be ready
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=30
    local attempt=1
    
    echo -e "${YELLOW}⏳ Waiting for $service_name to be ready...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z $host $port 2>/dev/null; then
            echo -e "${GREEN}✅ $service_name is ready!${NC}"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}❌ $service_name failed to start after $max_attempts seconds${NC}"
    return 1
}

# Check prerequisites
echo -e "${BLUE}🔍 Checking prerequisites...${NC}"

if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

if ! command_exists node; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    exit 1
fi

if ! command_exists redis-server; then
    echo -e "${RED}❌ Redis server is not installed${NC}"
    exit 1
fi

if ! command_exists mongod; then
    echo -e "${RED}❌ MongoDB is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All prerequisites found${NC}"

# Check if .env file exists
if [ ! -f "backend/.env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    if [ -f "backend/.env.example" ]; then
        cp backend/.env.example backend/.env
        echo -e "${YELLOW}📝 Please edit backend/.env and add your Gemini API key${NC}"
    else
        echo -e "${RED}❌ No .env template found${NC}"
        exit 1
    fi
fi

# Start Redis
echo -e "${BLUE}🔄 Starting Redis...${NC}"
if port_in_use 6380; then
    echo -e "${YELLOW}⚠️  Redis already running on port 6380${NC}"
else
    redis-server --port 6380 --daemonize yes
    wait_for_service localhost 6380 "Redis"
fi

# Start MongoDB
echo -e "${BLUE}🔄 Starting MongoDB...${NC}"
if port_in_use 27017; then
    echo -e "${YELLOW}⚠️  MongoDB already running on port 27017${NC}"
else
    mongod --fork --logpath /tmp/mongod.log
    wait_for_service localhost 27017 "MongoDB"
fi

# Install Python dependencies
echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
cd backend
pip install -r requirements.txt
cd ..

# Install Node dependencies
echo -e "${BLUE}📦 Installing Node.js dependencies...${NC}"
npm install

# Start backend
echo -e "${BLUE}🔄 Starting FastAPI backend...${NC}"
cd backend
python main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
wait_for_service localhost 8000 "FastAPI Backend"

# Start frontend
echo -e "${BLUE}🔄 Starting React frontend...${NC}"
npm run dev &
FRONTEND_PID=$!

# Wait for frontend to start
wait_for_service localhost 5173 "React Frontend"

echo ""
echo -e "${GREEN}🎉 All services started successfully!${NC}"
echo ""
echo -e "${BLUE}📱 Access your application:${NC}"
echo -e "   Frontend: ${GREEN}http://localhost:5173${NC}"
echo -e "   Backend API: ${GREEN}http://localhost:8000${NC}"
echo -e "   API Documentation: ${GREEN}http://localhost:8000/docs${NC}"
echo ""
echo -e "${BLUE}🔧 Service Status:${NC}"
echo -e "   Redis: ${GREEN}localhost:6380${NC}"
echo -e "   MongoDB: ${GREEN}localhost:27017${NC}"
echo -e "   PostgreSQL: ${GREEN}localhost:5432${NC}"
echo ""
echo -e "${YELLOW}💡 To stop all services, press Ctrl+C${NC}"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Stopping services...${NC}"
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    echo -e "${GREEN}✅ Services stopped${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Keep script running
echo -e "${BLUE}🔄 Services are running. Press Ctrl+C to stop.${NC}"
wait
