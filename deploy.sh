#!/bin/bash

# Fantasy Roast Bot Deployment Script
echo "🚀 Deploying Fantasy Roast Bot..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create a .env file with your API keys and webhooks:"
    echo "OPENAI_API_KEY=your_openai_key_here"
    echo "DISCORD_WEBHOOK_MEL=your_mel_webhook_here"
    echo "DISCORD_WEBHOOK_TODD=your_todd_webhook_here"
    echo "OPENAI_MODEL=gpt-4o-mini"
    echo "MAX_TOKENS=280"
    exit 1
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Build and start the new container
echo "🔨 Building and starting container..."
docker-compose up --build -d

# Wait for container to be healthy
echo "⏳ Waiting for container to be healthy..."
timeout=60
counter=0

while [ $counter -lt $timeout ]; do
    if docker-compose ps | grep -q "healthy"; then
        echo "✅ Container is healthy!"
        break
    fi
    echo "⏳ Waiting... ($counter/$timeout seconds)"
    sleep 5
    counter=$((counter + 5))
done

if [ $counter -ge $timeout ]; then
    echo "❌ Container failed to become healthy within $timeout seconds"
    docker-compose logs
    exit 1
fi

# Show container status
echo "📊 Container status:"
docker-compose ps

# Test the API
echo "🧪 Testing API endpoint..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)

if [ "$response" = "200" ]; then
    echo "✅ API is responding correctly!"
    echo "🎉 Fantasy Roast Bot is now running on http://localhost:8000"
    echo "📝 API endpoint: POST http://localhost:8000/draft-pick"
else
    echo "❌ API test failed with status code: $response"
    docker-compose logs
    exit 1
fi

echo "🚀 Deployment complete!"
