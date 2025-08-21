# 🚀 Fantasy Roast Bot Deployment Guide

## 📋 Prerequisites

- Docker installed on your server
- Docker Compose installed
- OpenAI API key
- Discord webhook URLs for Mel and Todd personas

## 🔧 Quick Deployment

### 1. **Clone and Setup**
```bash
git clone <your-repo-url>
cd slurmzball_bot
```

### 2. **Configure Environment**
```bash
# Copy the template
cp env.template .env

# Edit with your actual values
nano .env
```

**Required .env contents:**
```bash
OPENAI_API_KEY=sk-your-actual-openai-key-here
DISCORD_WEBHOOK_MEL=https://discord.com/api/webhooks/your_mel_webhook
DISCORD_WEBHOOK_TODD=https://discord.com/api/webhooks/your_todd_webhook
OPENAI_MODEL=gpt-4o-mini
MAX_TOKENS=280
```

### 3. **Deploy with Script**
```bash
./deploy.sh
```

## 🐳 Manual Docker Commands

### **Build and Start**
```bash
# Build the container
docker-compose build

# Start the service
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### **Stop and Remove**
```bash
# Stop the service
docker-compose down

# Remove containers and images
docker-compose down --rmi all
```

## 🌐 Production Deployment

### **Reverse Proxy (Nginx)**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### **SSL with Let's Encrypt**
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

## 📊 Monitoring

### **Health Check**
```bash
# Test health endpoint
curl http://localhost:8000/health

# Expected response: {"status": "healthy", "timestamp": "..."}
```

### **Container Logs**
```bash
# View real-time logs
docker-compose logs -f

# View last 100 lines
docker-compose logs --tail=100
```

### **Resource Usage**
```bash
# Check container stats
docker stats fantasy-roast-bot

# Check disk usage
docker system df
```

## 🔒 Security Considerations

- ✅ **Non-root user**: Container runs as `app` user
- ✅ **Health checks**: Automatic health monitoring
- ✅ **Restart policy**: Automatic restart on failure
- ✅ **Network isolation**: Custom bridge network
- ✅ **Environment variables**: Secure credential management

## 🚨 Troubleshooting

### **Container Won't Start**
```bash
# Check logs
docker-compose logs

# Check environment variables
docker-compose config

# Rebuild from scratch
docker-compose down --rmi all
docker-compose up --build
```

### **API Not Responding**
```bash
# Check if container is running
docker-compose ps

# Test health endpoint
curl http://localhost:8000/health

# Check port binding
netstat -tlnp | grep 8000
```

### **Discord Webhook Issues**
```bash
# Test webhook manually
curl -X POST YOUR_WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -d '{"content": "Test message"}'
```

## 📈 Scaling

### **Multiple Instances**
```bash
# Scale to multiple containers
docker-compose up -d --scale fantasy-roast-bot=3
```

### **Load Balancer**
```nginx
upstream fantasy_bots {
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
}
```

## 🔄 Updates

### **Automatic Updates**
```bash
# Pull latest code
git pull origin main

# Redeploy
./deploy.sh
```

### **Rollback**
```bash
# Check out previous version
git checkout HEAD~1

# Redeploy
./deploy.sh
```

## 📞 Support

If you encounter issues:
1. Check the logs: `docker-compose logs -f`
2. Verify environment variables: `docker-compose config`
3. Test the health endpoint: `curl http://localhost:8000/health`
4. Check container status: `docker-compose ps`

---

**🎉 Your Fantasy Roast Bot is now ready for production!**
