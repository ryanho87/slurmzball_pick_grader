# 🚀 Fantasy Roast Bot Deployment Guide

## 📋 Prerequisites

- Docker installed on your server
- Docker Compose installed
- OpenAI API key
- Discord webhook URLs for your chosen personas (Mel, Todd, AB)

## 🔧 Quick Deployment

### 1. **Clone and Setup**
```bash
git clone <your-repo-url>
cd slurmzball_pick_grader
```

### 2. **Configure Your Leagues**
```bash
# Copy and edit the configuration templates
cp config/base.yaml config/my-league.yaml
cp config/secrets.yaml config/my-secrets.yaml

# Edit with your actual values
nano config/my-league.yaml    # Non-sensitive config
nano config/my-secrets.yaml   # Sensitive info (API keys, webhooks)
```

**Required config/my-league.yaml contents:**
```yaml
leagues:
  - name: myleague
    prompts:
      max_sentences: 2
      response_probabilities:
        qb_picks: 1.0
        other_positions: 0.8
```

**Required config/my-secrets.yaml contents:**
```yaml
openai:
  api_key: YOUR_OPENAI_API_KEY
  model: gpt-4o-mini
  max_tokens: 280

leagues:
  - name: myleague
    mel: YOUR_DISCORD_WEBHOOK_URL
    todd: YOUR_DISCORD_WEBHOOK_URL
    ab: YOUR_DISCORD_WEBHOOK_URL
```

### 3. **Configure Environment (Optional)**
```bash
# Copy the template (optional fallback)
cp env.template .env

# Edit with your OpenAI API key (only if not using secrets.yaml)
nano .env
```

**Optional .env contents (fallback only):**
```bash
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
```

### 4. **Deploy with Script**
```bash
./deploy.sh
```

## 🐳 Manual Docker Commands

### **Build and Start**
```bash
# Build the container
docker compose build

# Start the service
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

### **Stop and Remove**
```bash
# Stop the service
docker compose down

# Remove containers and images
docker compose down --rmi all
```

## 🌐 Production Deployment

### **Reverse Proxy (Nginx)**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:32145;
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
curl http://localhost:32145/health

# Expected response: {"status": "healthy", "timestamp": "..."}
```

### **Container Logs**
```bash
# View real-time logs
docker compose logs -f

# View last 100 lines
docker compose logs --tail=100
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
docker compose logs

# Check configuration
docker compose config

# Rebuild from scratch
docker compose down --rmi all
docker compose up --build
```

### **API Not Responding**
```bash
# Check if container is running
docker compose ps

# Test health endpoint
curl http://localhost:32145/health

# Check port binding
netstat -tlnp | grep 32145
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
docker compose up -d --scale fantasy-roast-bot=3
```

### **Load Balancer**
```nginx
upstream fantasy_bots {
    server localhost:32145;
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
1. Check the logs: `docker compose logs -f`
2. Verify configuration: `docker compose config`
3. Test the health endpoint: `curl http://localhost:32145/health`
4. Check container status: `docker compose ps`

---

**🎉 Your Fantasy Roast Bot is now ready for production!**
