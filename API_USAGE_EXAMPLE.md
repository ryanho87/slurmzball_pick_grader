# API Usage with Dual-Path Bot System

## Overview
The API now supports a **dual-path bot system** with league-based configuration. Each league can have its own Discord webhooks for multiple personas, customizable prompts, and two distinct response paths:

- **Analytics Path**: Structured analysis with rules (Mel, Todd)
- **Reaction Path**: Freeform, unhinged responses (AB)

**🔄 NEW: Configuration can now be reloaded without restarting the application!**

## Configuration
Configuration is split between two files for security:

**`config/base.yaml`** contains:
- League configurations with:
  - Customizable prompt configurations
  - Message length constraints (max_sentences)
  - **Dual-path prompt system** for different persona types
  - **Structured analysis framework** with predefined analysis types
  - Customizable voice styles and tone configurations
  - Customizable rules and response probabilities

**`config/secrets.yaml` contains:**
- OpenAI settings (api_key, model, max_tokens)
- Webhook URLs for Mel, Todd, and AB personas

The application automatically merges these files at startup.

## Available Endpoints

### GET /leagues
Returns available leagues and the default league.

**Response:**
```json
{
  "leagues": ["slurmzball", "liv"],
  "default_league": "slurmzball"
}
```

### GET /leagues/{league_name}/prompts
Returns the complete prompt configuration for a specific league, including the dual-path system and analysis framework.

**Response:**
```json
{
  "league": "slurmzball",
  "prompts": {
    "max_sentences": 2,
    "mel_voice": "You are \"Mel Kiper Jr.\"—rapid-fire expert draft analyst energy...",
    "todd_voice": "You are \"Todd McShay\"—measured but spicy...",
    "ab_voice": "You are \"Antonio Brown\"—completely UNHINGED, conspiracy theory obsessed...",
    "default_voice": "You are an NFL Draft analyst. Witty, R rated.",
    "response_probabilities": {
      "qb_picks": 1.0,
      "other_positions": 0.8,
      "major_reaches": 0.9,
      "moderate_reaches": 0.8,
      "slight_reaches": 0.8,
      "good_value": 0.8,
      "great_value": 0.8,
      "massive_steals": 0.9
    },
    "short_response_config": {
      "major_reaches": 0.1,
      "moderate_reaches": 0.1,
      "slight_reaches": 0.1,
      "good_value": 0.1,
      "great_value": 0.1,
      "massive_steals": 0.1
    },
    "analysis_types": [
      {
        "name": "adp_value",
        "description": "Focus on pick-ADP delta (reach vs value)",
        "max_sentences": 1,
        "weight": 0.8
      },
      {
        "name": "team_needs",
        "description": "Analyze if this pick addresses team weaknesses",
        "max_sentences": 1,
        "weight": 0.9
      },
      {
        "name": "position_scarcity",
        "description": "Comment on position availability and timing",
        "max_sentences": 1,
        "weight": 0.7
      },
      {
        "name": "roster_balance",
        "description": "Evaluate team composition and strategy",
        "max_sentences": 1,
        "weight": 0.9
      },
      {
        "name": "draft_strategy",
        "description": "Comment on overall draft approach",
        "max_sentences": 1,
        "weight": 0.6
      },
      {
        "name": "player_comparison",
        "description": "Compare to other available players",
        "max_sentences": 1,
        "weight": 0.8
      },
      {
        "name": "diversity_analysis",
        "description": "Comment on team composition diversity and representation patterns",
        "max_sentences": 1,
        "weight": 0.9
      }
    ],
    "analysis_selection_rules": [
      "Choose 1-3 analysis types that are most relevant to this pick",
      "If it's a major reach (ADP delta > 3), always include 'adp_value'",
      "If team has glaring weaknesses, include 'team_needs' (high priority)",
      "If position is scarce, include 'position_scarcity'",
      "If team shows clear composition patterns (e.g., all white players), include 'diversity_analysis' (high priority)",
      "Use weighted selection - higher weight analysis types are more likely to be chosen",
      "Never use more than 3 analysis types in one response",
      "Focus on the most compelling insights for this specific situation"
    ],
    "tone_config": {
      "major_reach": "Tone: SAVAGE ROAST - This is a massive reach...",
      "moderate_reach": "Tone: ROAST - This is a reach that needs...",
      "slight_reach": "Tone: CRITICAL - This is a slight reach...",
      "good_value": "Tone: PRAISEWORTHY - This is solid value...",
      "great_value": "Tone: ENTHUSIASTIC - This is excellent value...",
      "massive_steal": "Tone: CELEBRATION - This is an absolute STEAL..."
    },
    "rules": [
      "CRITICAL: Write exactly 2 sentences. This is non-negotiable.",
      "ALWAYS analyze team context: roster composition, position needs, and available alternatives.",
      "Use the team roster and available players data to provide strategic insights.",
      "Don't just focus on ADP - explain WHY this pick makes sense (or doesn't) for THIS team.",
      "Comment on team composition patterns including diversity and representation when relevant.",
      "Use humor to point out obvious team building patterns (e.g., 'building the most vanilla team in fantasy history').",
      "Include a quick pick grade (A–F) and a 3–6 word verdict tag in ALL CAPS at the end.",
      "The grade should reflect both value AND team fit, not just ADP delta.",
      "Be entertaining and use the persona's voice style.",
      "For reaches: Don't hold back on language - use profanity if it makes the roast funnier and more savage.",
      "For value picks: Keep it clean and celebratory."
    ]
  },
  "webhooks": {
    "mel": "https://discord.com/api/webhooks/...",
    "todd": "https://discord.com/api/webhooks/...",
    "ab": "https://discord.com/api/webhooks/..."
  }
}
```

### POST /draft-pick
Analyzes a draft pick and posts to Discord using the configured personas.

**Request Body:**
```json
{
  "pickNumber": 14,
  "player": "Najee Harris",
  "adp": 28.4,
  "team": "Ryan",
  "position": "RB",
  "league": "slurmzball",
  "team_roster": "Name,Positions\nCeeDee Lamb,WR\nJonathan Taylor,RB\nJoe Burrow,QB",
  "available_players": "Name,Overall Ranking,Team,Positions\nChris Olave,59,NO,WR\nRashee Rice,60,KC,WR\nTravis Hunter,66,JAC,WR"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Analysis posted to Discord by Mel",
  "analysis": "Holy hell, Ryan just jumped the shark with Najee Harris at #14...",
  "persona": "Mel",
  "webhook_sent": true,
  "error": null
}
```

## Dual-Path Bot System

### Analytics Path (Mel, Todd)
- **Structured analysis** with team context and rules
- **Sentence limits** and grading requirements
- **Fantasy insights** and strategic commentary
- **Professional analyst behavior**

### Reaction Path (AB)
- **NO RULES** - completely freeform
- **NO SENTENCE LIMITS** - can rant as long as he wants
- **NO ANALYTICAL CONSTRAINTS** - just pure persona expression
- **"Don't analyze - just REACT!"**

### Smart Persona Selection
- **Independent of ADP** - all bots have equal chance
- **Configurable probabilities** via YAML
- **Random selection** among available personas

## Team Context Analysis

The API now supports rich team context for analytical personas:

### Team Roster Format
```csv
Name,Positions
CeeDee Lamb,WR
Jonathan Taylor,RB
Joe Burrow,QB
```

### Available Players Format
```csv
Name,Overall Ranking,Team,Positions
Chris Olave,59,NO,WR
Rashee Rice,60,KC,WR
Travis Hunter,66,JAC,WR
```

### Analysis Types
The bot automatically selects 1-3 analysis types based on:
- **Pick quality** (ADP delta)
- **Team composition** (position needs, diversity)
- **Available alternatives** (player comparison)
- **Weighted selection** (higher weights = more likely)

## Configuration Management

### Hot-Reload Configuration
```bash
curl -X POST http://localhost:32145/admin/reload-config
```

### Check Configuration Status
```bash
curl -X GET http://localhost:32145/admin/config-status
```

### Configuration File Watching
The application automatically watches for changes in `config/base.yaml` and reloads configuration.

## Examples

### Basic Pick Analysis
```bash
curl -X POST http://localhost:32145/draft-pick \
  -H "Content-Type: application/json" \
  -d '{
    "pickNumber": 1,
    "player": "Malik Nabers",
    "adp": 6,
    "team": "KO",
    "position": "WR",
    "league": "liv"
  }'
```

### Full Team Context Analysis
```bash
curl -X POST http://localhost:32145/draft-pick \
  -H "Content-Type: application/json" \
  -d '{
    "pickNumber": 1,
    "player": "Malik Nabers",
    "adp": 6,
    "team": "KO",
    "position": "WR",
    "league": "liv",
    "team_roster": "Name,Positions\nCeeDee Lamb,WR\nBrian Thomas Jr.,WR\nJonathan Taylor,RB\nAlvin Kamara,RB\nJoe Burrow,QB\nDavid Montgomery,RB\nRJ Harvey,RB\nKaleb Johnson,RB",
    "available_players": "Name,Overall Ranking,Team,Positions\nChris Olave,59,NO,WR\nRashee Rice,60,KC,WR\nTravis Hunter,66,JAC,WR\nJerry Jeudy,67,CLE,WR\nStefon Diggs,75,NE,WR\nKyler Murray,78,ARI,QB\nDavid Njoku,79,CLE,TE\nDak Prescott,82,DAL,QB\nJaylen Warren,83,PIT,RB\nKhalil Shakir,86,BUF,WR\nJauan Jennings,89,SF,WR\nJordan Addison,90,MIN,WR\nChris Godwin,91,TB,WR\nTravis Etienne Jr.,92,JAC,RB\nJoe Mixon,93,HOU,RB\nJustin Fields,94,NYJ,QB\nJustin Herbert,95,LAC,QB\nDeebo Samuel Sr.,96,WAS,WR"
  }'
```

## Error Handling

The API returns structured error responses:

```json
{
  "success": false,
  "message": "Error message",
  "analysis": null,
  "persona": null,
  "webhook_sent": false,
  "error": "Detailed error information"
}
```

## Rate Limiting

- **Discord API**: Automatic retry with exponential backoff
- **OpenAI API**: Configurable timeout and retry logic
- **Application**: No built-in rate limiting (configure at load balancer level)

## Monitoring

### Health Check
```bash
curl -X GET http://localhost:32145/health
```

### Configuration Status
```bash
curl -X GET http://localhost:32145/admin/config-status
```

### Logs
```bash
docker compose logs -f
```
