#!/bin/bash

# FoodPal Development Startup Script

echo "🍽️ Starting FoodPal Development Environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Create environment files if they don't exist
if [ ! -f backend/.env ]; then
    echo "📄 Creating backend/.env from example..."
    cp backend/.env.example backend/.env
fi

if [ ! -f frontend/.env ]; then
    echo "📄 Creating frontend/.env from example..."
    cp frontend/.env.example frontend/.env
fi

# Create media directory
mkdir -p media

echo "🚀 Starting services with Docker Compose..."
docker-compose up --build

echo "✅ FoodPal development environment started!"
echo ""
echo "Access points:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  API Documentation: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"