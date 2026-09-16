#!/bin/bash

# Fantasy Roast Bot Deployment Script
echo "🚀 Deploying Fantasy Roast Bot..."

# Check if config files exist
if [ ! -f config/base.yaml ]; then
    echo "❌ Error: config/base.yaml file not found!"
    echo "Please create a config/base.yaml file with your league configuration:"
    echo "Include your prompt settings, rules, and analysis types for each league."
    echo "You can copy from config/config.template.yaml to get started."
    exit 1
fi

if [ ! -f config/secrets.yaml ]; then
    echo "❌ Error: config/secrets.yaml file not found!"
    echo "Please create a config/secrets.yaml file with your sensitive information:"
    echo "Include OpenAI API key and Discord webhook URLs for each league."
    echo "You can copy from config/secrets.template.yaml to get started."
    exit 1
fi

# Check if .env file exists (optional fallback)
if [ ! -f .env ]; then
    echo "ℹ️  Info: .env file not found - this is optional now."
    echo "Configuration is loaded from config/base.yaml and config/secrets.yaml"
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker compose down

# Build and start the new container
echo "🔨 Building and starting container..."
docker compose up --build -d

# Wait for container to be healthy
echo "⏳ Waiting for container to be healthy..."
timeout=60
counter=0

while [ $counter -lt $timeout ]; do
    if docker compose ps | grep -q "Up"; then
        echo "✅ Container is running!"
        break
    fi
    echo "⏳ Waiting... ($counter/$timeout seconds)"
    sleep 5
    counter=$((counter + 5))
done

if [ $counter -ge $timeout ]; then
    echo "❌ Container failed to start within $timeout seconds"
    docker compose logs
    exit 1
fi

# Show container status
echo "📊 Container status:"
docker compose ps

# Test the API
echo "🧪 Testing API endpoint..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:32145/health)

if [ "$response" = "200" ]; then
    echo "✅ API is responding correctly!"
    echo "🎉 Fantasy Roast Bot is now running on http://localhost:32145"
    echo "📝 API endpoint: POST http://localhost:32145/draft-pick"
    echo "🔧 Configuration endpoint: GET http://localhost:32145/leagues"
    echo "🔄 Reload config: POST http://localhost:32145/admin/reload-config"
else
    echo "❌ API test failed with status code: $response"
    docker compose logs
    exit 1
fi

echo "🚀 Deployment complete!"
echo ""
echo "📚 Next steps:"
echo "1. Your configuration is loaded from config/base.yaml and config/secrets.yaml"
echo "2. Test with: curl -X GET http://localhost:32145/leagues"
echo "3. Reload config: curl -X POST http://localhost:32145/admin/reload-config"
echo "4. To update configuration, edit the YAML files and reload"
