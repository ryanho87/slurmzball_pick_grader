# 🏈 Fantasy Football Roast Bot

An intelligent, Dockerized bot that automatically analyzes fantasy football draft picks and generates entertaining roasts in the style of famous NFL draft analysts. Features **automatic response logic**, **smart persona selection**, **dual-path prompt system**, and **league-based configuration**!

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

## 🎭 **Dual-Path Bot Personas**

### **Analytics Path** (Structured Analysis)
- **Mel Kiper Jr.**: Rapid-fire, punchy, hair-level confidence with R-rated language
- **Todd McShay**: Measured but spicy, analytics meets scouting

### **Reaction Path** (Freeform Chaos)
- **Antonio Brown (AB)**: Completely unhinged, conspiracy theory obsessed, ALL CAPS rants, random tangents about CTE being fake, threats to sue everyone, claims you're the best WR ever, emoji explosions, completely unpredictable energy

## 🚀 **Quick Start with Docker**

### **Prerequisites**
- Docker and Docker Compose installed
- OpenAI API key
- Discord webhooks for your chosen personas

### **Deployment**
```bash
# 1. Clone the repository
git clone <your-repo-url>
cd slurmzball_pick_grader

# 2. Configure your leagues
cp config/config.template.yaml config/my-league.yaml
cp config/secrets.template.yaml config/my-secrets.yaml

# Edit with your actual values
nano config/my-league.yaml    # Non-sensitive config
nano config/my-secrets.yaml   # Sensitive info (API keys, webhooks)

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
  "team": "Ryan",          // Team/manager name
  "league": "slurmzball",  // League identifier
  "team_roster": "Name,Positions\nCeeDee Lamb,WR\nJonathan Taylor,RB", // Optional CSV
  "available_players": "Name,Overall Ranking,Team,Positions\nChris Olave,59,NO,WR" // Optional CSV
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

## 🤖 **Dual-Path Response System**

The bot intelligently routes responses through two distinct paths:

### **Analytics Path** (Mel, Todd)
- **Structured analysis** with team context
- **Sentence limits** and grading requirements
- **Fantasy insights** and strategic commentary
- **Professional analyst behavior**

### **Reaction Path** (AB)
- **NO RULES** - completely freeform
- **NO SENTENCE LIMITS** - can rant as long as he wants
- **NO ANALYTICAL CONSTRAINTS** - just pure persona expression
- **"Don't analyze - just REACT!"**

### **Smart Persona Selection**
- **Independent of ADP** - all bots have equal chance
- **Configurable probabilities** via YAML
- **Random selection** among available personas

## 🎨 **Discord Output**

The bot generates rich Discord embeds with:
- **Color-coded analysis**: Red for reaches, green for value
- **Persona-specific colors**: Each bot has their own theme
- **Simple, clean appearance**: Looks like regular user messages

## ⚙️ **League-Based Configuration**

### **YAML Configuration**
Configuration is split between two files for security:

**`config/base.yaml`** - Non-sensitive configuration:
```yaml
leagues:
  - name: slurmzball
    prompts:
      max_sentences: 2
      response_probabilities:
        qb_picks: 1.0
        other_positions: 0.8
      short_response_config:
        major_reaches: 0.1
      analysis_types:
        - name: "team_needs"
          weight: 0.9
```

**`config/secrets.yaml`** - Sensitive information:
```yaml
openai:
  api_key: your_openai_api_key_here
  model: gpt-4o-mini
  max_tokens: 280

leagues:
  - name: slurmzball
    mel: https://discord.com/api/webhooks/your_mel_webhook
    todd: https://discord.com/api/webhooks/your_todd_webhook
    ab: https://discord.com/api/webhooks/your_ab_webhook
```

The application automatically merges these files at startup.

### **Hot-Reloading**
Configuration can be updated without restarting:
```bash
curl -X POST http://localhost:32145/admin/reload-config
```

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
docker compose up --build -d

# View logs
docker compose logs -f

# Stop service
docker compose down

# Check status
docker compose ps
```

## 🔒 **Security & Monitoring**

- **Health endpoint**: `GET /health` for monitoring
- **Config status**: `GET /admin/config-status` for configuration monitoring
- **Container logs**: Real-time logging and debugging
- **Environment variables**: Secure credential management
- **Non-root user**: Container security best practices

## 📚 **Documentation**

- **`DEPLOYMENT.md`**: Comprehensive deployment guide
- **`API_USAGE_EXAMPLE.md`**: Detailed API usage examples
- **`env.template`**: Environment variable template
- **`deploy.sh`**: Automated deployment script

---

**🎉 Your Fantasy Roast Bot is now production-ready with Docker and dual-path personas!**

