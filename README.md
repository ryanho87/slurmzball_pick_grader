# 🏈 Fantasy Football Roast Bot

An intelligent, Dockerized bot that automatically analyzes fantasy football draft picks and generates entertaining roasts in the style of famous NFL draft analysts. Features **automatic response logic**, **smart persona selection**, and **Mel Kiper Jr.'s legendary Shedeur Sanders meltdown** for every QB pick!

## 🎯 **Smart Analysis Based on Pick-ADP Delta**

The bot automatically determines the tone and intensity of analysis based on the **pick-ADP delta**:

- **Negative Delta (Reach)**: Player taken earlier than ADP suggests
  - `-5 or lower`: Savage roast for major reaches
  - `-2 to -5`: Critical roast for moderate reaches  
  - `0 to -2`: Gentle criticism for slight reaches

- **Positive Delta (Value)**: Player taken later than ADP suggests
  - `0 to +3`: Praiseworthy for solid value
  - `+3 to +8`: Enthusiastic praise for great value
  - `+8 or higher`: Celebration for massive steals

## 🎭 **Analyst Personas**

- **Mel Kiper Jr.**: Rapid-fire, punchy, hair-level confidence with R-rated language
- **Todd McShay**: Measured but spicy, analytics meets scouting

## 🚀 **Quick Start with Docker**

### **Prerequisites**
- Docker and Docker Compose installed
- OpenAI API key
- Discord webhooks for Mel and Todd personas

### **Deployment**
```bash
# 1. Clone the repository
git clone <your-repo-url>
cd slurmzball_bot

# 2. Configure environment
cp env.template .env
# Edit .env with your API keys and webhooks

# 3. Deploy with one command
./deploy.sh
```

## 📝 **API Usage**

**Endpoint:** `POST /draft-pick`

**Request Body:**
```json
{
  "pickNumber": 14,        // When the player was drafted
  "player": "Najee Harris", // Player name
  "position": "RB",         // Player position (QB, RB, WR, TE, etc.)
  "adp": 28.4,             // Average Draft Position (ADP)
  "team": "Ryan"           // Team/manager name
}
```

## 🧮 **Pick-ADP Delta Calculation**

The bot automatically calculates: **`pick_delta = pickNumber - ADP`**

- **Positive delta** = Good value (player taken later than expected)
- **Negative delta** = Reach (player taken earlier than expected)

**Examples:**
- Pick #8, ADP 28.4 → Delta: +20.4 (MASSIVE STEAL! 🎉)
- Pick #14, ADP 15.2 → Delta: +1.2 (Good value ✅)
- Pick #25, ADP 22.1 → Delta: -2.9 (Reach 🚨)
- Pick #12, ADP 8.5 → Delta: -3.5 (Major reach 🔥)

## 🤖 **Automatic Response Logic**

The bot intelligently decides when and how to respond:

### **QB Picks (100% Response Rate):**
- **Mel Kiper Jr. ALWAYS responds** with Shedeur Sanders meltdown
- Guaranteed entertainment for every quarterback selection

### **Other Positions (40% Response Rate):**
- **Smart persona selection** based on pick quality:
  - **Reaches** (Delta < -3): Mel for savage roasts
  - **Value** (Delta > +3): Todd for analytical praise
  - **Close picks**: Random persona selection

### **Response Types:**
- **Short gut reactions** (pre-canned classics)
- **Full AI analysis** (detailed breakdowns)
- **Shedeur meltdowns** (Mel's signature chaos)

## 🎨 **Discord Output**

The bot generates rich Discord embeds with:
- **Color-coded analysis**: Red for reaches, green for value
- **Simple, clean appearance**: Looks like regular user messages
- **Contextual colors**: Visual indicator of pick quality

## 🐳 **Docker Deployment**

### **Production Ready Features:**
- **Health checks**: `/health` endpoint for monitoring
- **Security**: Non-root user, network isolation
- **Logging**: Structured container logs
- **Scaling**: Easy horizontal scaling
- **Updates**: Simple rollback and update process

### **Deployment Commands:**
```bash
# Build and start
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop service
docker-compose down

# Check status
docker-compose ps
```

## 🔒 **Security & Monitoring**

- **Health endpoint**: `GET /health` for monitoring
- **Container logs**: Real-time logging and debugging
- **Environment variables**: Secure credential management
- **Non-root user**: Container security best practices

## 📚 **Documentation**

- **`DEPLOYMENT.md`**: Comprehensive deployment guide
- **`env.template`**: Environment variable template
- **`deploy.sh`**: Automated deployment script

---

**🎉 Your Fantasy Roast Bot is now production-ready with Docker!**

