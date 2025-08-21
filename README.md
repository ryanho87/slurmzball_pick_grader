# Fantasy Football Pick Grading Bot 🏈

An intelligent bot that analyzes fantasy football draft picks based on **pick-ADP delta** and generates entertaining analysis in the style of famous NFL draft analysts.

## 🎯 **Smart Analysis Based on Value**

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

- **Mel Kiper Jr.**: Rapid-fire, punchy, hair-level confidence
- **Todd McShay**: Measured but spicy, analytics meets scouting
- **Default**: Balanced NFL draft analyst

## 🔧 **Requirements**

- OpenAI API key
- Discord webhooks
- Python 3.8+

## 🚀 **Quick Start**

1. Create and activate Python virtual environment
2. Install requirements: `pip install -r requirements.txt`
3. Set up your `.env` file with API keys and webhooks
4. Start the app: `uvicorn app:app --host 0.0.0.0 --port 8000 --reload`
5. Make requests to `http://localhost:8000/draft-pick`

## 📝 **API Usage**

**Endpoint:** `POST /draft-pick`

**Request Body:**

{
      "pickNumber": 14,        // When the player was drafted
  "player": "Najee Harris", // Player name
  "adp": 28.4,             // Average Draft Position (ADP)
  "team": "Ryan",          // Team/manager name
  "persona": "Mel",        // Analyst persona: "Mel", "McShay", or "Default"
  "tone": "roast",         // Legacy field (now auto-determined by delta)
  "leagueType": "redraft"  // League type: "redraft", "dynasty", "best ball"
}

## 🧮 **Pick-ADP Delta Calculation**

The bot automatically calculates: **`pick_delta = ADP - pickNumber`**

- **Positive delta** = Good value (player taken later than expected)
- **Negative delta** = Reach (player taken earlier than expected)

**Examples:**
- Pick #8, ADP 28.4 → Delta: +20.4 (MASSIVE STEAL! 🎉)
- Pick #14, ADP 15.2 → Delta: +1.2 (Good value ✅)
- Pick #25, ADP 22.1 → Delta: -2.9 (Reach 🚨)
- Pick #12, ADP 8.5 → Delta: -3.5 (Major reach 🔥)

## 🎨 **Discord Output**

The bot generates rich Discord embeds with:
- **Color-coded analysis**: Red for reaches, green for value
- **Value analysis field**: Shows pick-ADP delta and reach/value indicator
- **Grade and verdict**: A-F grade with verdict tag
- **Analyst attribution**: Shows which persona provided the analysis

