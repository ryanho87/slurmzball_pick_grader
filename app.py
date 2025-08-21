import os
import random
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from dotenv import load_dotenv
load_dotenv(".env")

# ---------- Config ----------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

WEBHOOKS = {
    "Mel": os.getenv("DISCORD_WEBHOOK_MEL"),
    "Todd": os.getenv("DISCORD_WEBHOOK_TODD"),
}

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "280"))

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY env var is required")

app = FastAPI(title="Fantasy Roast Bot (Python)")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": "2024-01-19T00:00:00Z"}

# ---------- Schemas ----------
class DraftPick(BaseModel):
    pickNumber: int = Field(..., ge=1)
    player: str
    position: str = Field(..., description="Player position (QB, RB, WR, TE, etc.)")
    adp: float
    team: str
    leagueType: Optional[str] = Field(default="redraft")  # "redraft" | "dynasty" | "best ball"


# ---------- Prompts ----------
def build_system_prompt(persona: str, tone: str, league: str, pickNumber: int, adp: float, pick_delta: float) -> str:
    voices = {
        "Mel": 'You are "Mel Kiper Jr."—rapid-fire expert draft analyst energy, punchy one-liners, hair-level confidence. Witty hyperbole, R-rated language welcome. 1-2 sentences.',
        "Todd": 'You are "Todd McShay"—measured but spicy; analytics meets scouting; crisp wit with some edge. 1-2 sentences.',
    }
    persona_line = voices.get(persona, "You are an NFL Draft analyst. 1–2 sentences. Witty, R rated.")
    
    # Determine tone based on pick-ADP delta
    if pick_delta < -5:
        # Major reach - savage roast with profanity
        tone_line = "Tone: SAVAGE ROAST - This is a massive reach that deserves maximum ridicule. Be absolutely brutal, hilarious, and don't hold back on language. Use profanity if it makes the roast funnier."
    elif pick_delta < -2:
        # Moderate reach - roast with some humor
        tone_line = "Tone: ROAST - This is a reach that needs to be called out. Be critical, entertaining, and feel free to use some profanity for emphasis."
    elif pick_delta < 0:
        # Slight reach - gentle criticism
        tone_line = "Tone: CRITICAL - This is a slight reach. Be constructive but point out the questionable value. Light profanity okay if it fits."
    elif pick_delta < 3:
        # Good value - balanced praise
        tone_line = "Tone: PRAISEWORTHY - This is solid value. Highlight the good decision while noting any concerns. Keep it clean but enthusiastic."
    elif pick_delta < 8:
        # Great value - enthusiastic praise
        tone_line = "Tone: ENTHUSIASTIC - This is excellent value! Be genuinely excited about this steal. Clean language, pure celebration."
    else:
        # Massive steal - over-the-top celebration
        tone_line = "Tone: CELEBRATION - This is an absolute STEAL! Be over-the-top excited and praise the GM's brilliance. Clean, pure joy."

    return (
        f"{persona_line}\n"
        f"{tone_line}\n"
        f"League context: {league}.\n"
        f"Pick Analysis: Player was taken at pick #{pickNumber} with an ADP of {adp:.1f} (delta: {pick_delta:+.1f}).\n"
        "Rules:\n"
        "- Focus primarily on the pick-ADP delta to determine your analysis intensity.\n"
        "- Negative delta (reach) = criticize the reach, positive delta (value) = praise the value.\n"
        "- Include a quick pick grade (A–F) and a 3–6 word verdict tag in ALL CAPS at the end.\n"
        "- The grade should reflect the value: A for steals, F for major reaches, etc.\n"
        "- Be entertaining and use the persona's voice style.\n"
        "- For reaches: Don't hold back on language - use profanity if it makes the roast funnier and more savage.\n"
        "- For value picks: Keep it clean and celebratory."
    )


def build_user_prompt(pickNumber: int, player: str, adp: float, team: str, pick_delta: float) -> str:
    return (
        "Draft pick context:\n"
        f"- Pick #: {pickNumber}\n"
        f"- Player: {player}\n"
        f"- Selecting Team: {team}\n"
        f"- Player ADP: {adp}\n"
        f"- Pick-ADP Delta: {pick_delta:+.1f} (positive = value, negative = reach)\n\n"
        "Write the analyst blurb now."
    )


# ---------- OpenAI call ----------
async def generate_blurb(client: httpx.AsyncClient, system: str, user: str) -> str:
    """
    Uses the OpenAI Responses API (recommended) but falls back to Chat Completions if desired.
    Docs: Responses API & Chat Completions. 
    """
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}

    # Prefer Responses API
    resp = await client.post(
        "https://api.openai.com/v1/responses",
        headers=headers,
        json={
            "model": MODEL,
            "input": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            "max_output_tokens": MAX_TOKENS,
            "temperature": 0.9
        },
        timeout=30.0,
    )

    if resp.status_code == 404:
        # Fallback to Chat Completions if Responses not available in your account
        cc = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ],
                "max_tokens": MAX_TOKENS,
                "temperature": 0.9
            },
            timeout=30.0,
        )
        if not cc.is_success:
            raise HTTPException(status_code=502, detail=f"OpenAI error (chat): {cc.text}")
        data = cc.json()
        content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "").strip()
        if not content:
            raise HTTPException(status_code=502, detail="OpenAI returned no content (chat).")
        return content

    if not resp.is_success:
        raise HTTPException(status_code=502, detail=f"OpenAI error (responses): {resp.text}")

    data = resp.json()
    # Responses API returns content in a structured array
    content = ""
    
    # First try to get content from the output array
    output_array = data.get("output", [])
    if output_array and isinstance(output_array[0], dict):
        message = output_array[0]
        if message.get("type") == "message" and "content" in message:
            content_array = message["content"]
            for content_item in content_array:
                if isinstance(content_item, dict) and content_item.get("type") == "output_text":
                    content = content_item.get("text", "").strip()
                    break
    
    # Fallback: try to extract from any text fields
    if not content:
        for output_item in output_array:
            if isinstance(output_item, dict):
                # Try different possible content locations
                content = (output_item.get("text") or 
                          output_item.get("content") or 
                          "").strip()
                if content:
                    break
    
    if not content:
        raise HTTPException(status_code=502, detail="OpenAI returned no content.")
    return content


# ---------- Discord post with 429-aware retry ----------
async def post_to_discord_with_retry(client: httpx.AsyncClient, url: str, payload: dict, attempt: int = 0) -> httpx.Response:
    """
    Discord returns 429 on rate limit; honor Retry-After / retry_after per docs.
    """
    resp = await client.post(url, json=payload, timeout=15.0)
    if resp.status_code == 429 and attempt < 3:
        retry_after = 1.0
        # Header "Retry-After" in seconds; body may include "retry_after" too.
        try:
            retry_after = float(resp.headers.get("Retry-After", "1"))
        except ValueError:
            try:
                retry_after = float(resp.json().get("retry_after", 1))
            except Exception:
                pass
        await client.aclose()  # avoid connection reuse during sleep in some envs
        import asyncio
        await asyncio.sleep(max(0.0, retry_after))
        async with httpx.AsyncClient() as again:
            return await post_to_discord_with_retry(again, url, payload, attempt + 1)
    return resp


# ---------- Endpoint ----------
@app.post("/draft-pick")
async def draft_pick(body: DraftPick):
    # Calculate pick-ADP delta (positive = value, negative = reach)
    pick_delta = body.pickNumber - body.adp
    
    # DECISION LOGIC: Should any bot respond to this pick?
    should_respond = False
    chosen_persona = None
    
    # 1. MEL ALWAYS RESPONDS TO QB PICKS (Shedeur meltdown priority)
    if body.position.upper() == "QB":
        should_respond = True
        chosen_persona = "Mel"
    
    # 2. RANDOM RESPONSES FOR OTHER POSITIONS (not every pick needs a response)
    elif random.random() < 0.4:  # 40% chance of response for non-QB picks
        should_respond = True
        # Choose persona based on pick quality
        if pick_delta < -3:
            chosen_persona = "Mel"  # Mel for savage roasts
        elif pick_delta > 3:
            chosen_persona = "Todd"  # Todd for value analysis
        else:
            chosen_persona = random.choice(["Mel", "Todd"])  # Random for close picks
    
    # If no bot should respond, return early
    if not should_respond:
        return {"ok": True, "responded": False, "reason": "No bot response needed for this pick"}
    
    # Get webhook URL for the chosen persona
    webhook_url = WEBHOOKS.get(chosen_persona)
    
    if not webhook_url:
        raise HTTPException(status_code=500, detail=f"No webhook configured for persona '{chosen_persona}'. Available personas: {', '.join(WEBHOOKS.keys())}")
    
    # Build prompts for the chosen persona
    system = build_system_prompt(chosen_persona, "roast", body.leagueType, body.pickNumber, body.adp, pick_delta)
    user = build_user_prompt(body.pickNumber, body.player, body.adp, body.team, pick_delta)

    # Sometimes use short gut reactions for maximum impact
    
    # Check if this is a QB pick that's not Shedeur Sanders
    is_qb_pick = body.position.upper() == "QB"
    is_shedeur = "shedeur" in body.player.lower() or "sanders" in body.player.lower()
    
    # Mel Kiper Jr. Shedeur Sanders meltdown reactions
    mel_shedeur_meltdown = [
        "WHERE IS SHEDEUR SANDERS?!",
        "I CANNOT BELIEVE SHEDEUR IS STILL ON THE BOARD!",
        "This is a DISASTER! Shedeur Sanders should have been taken 10 picks ago!",
        "I'm having a MELTDOWN! Shedeur Sanders is the best QB in this draft!",
        "This is why the NFL is BROKEN! Shedeur Sanders is being IGNORED!",
        "I'm going to LOSE MY MIND if Shedeur doesn't get drafted soon!",
        "This is the WORST DRAFT I've ever seen! Where is Shedeur?!",
        "I'm literally SHAKING! Shedeur Sanders is a generational talent!",
        "This is INSANITY! Shedeur Sanders is being ROBBED!",
        "I'm about to have a BREAKDOWN! Shedeur Sanders is the answer!",
        "This is CRIMINAL! Shedeur Sanders should be the #1 pick!",
        "I'm LOSING IT! Shedeur Sanders is the most NFL-ready QB!",
        "This is EMBARRASSING! Shedeur Sanders is being DISRESPECTED!",
        "I'm going to QUIT if Shedeur doesn't get drafted!",
        "This is a TRAVESTY! Shedeur Sanders is the future of the NFL!"
    ]
    
    # Short reactions for reaches (negative deltas)
    short_reactions = [
        "Terrible pick",
        "I don't love this",
        "I saw him going later",
        "Unbelievable",
        "Could have done better",
        "That pick was absolute garbage",
        "We should have seen this one coming, this manager is an absolute joke",
        "Hate it",
        "That pick was inexcusable",
        "That might be the worst pick I've ever seen",
        "What a reach",
        "Are you kidding me?",
        "This is why you don't win championships",
        "Fire the GM immediately",
        "I'm speechless",
        "This pick physically hurts me",
        "Someone call the police, this is a crime",
        "I need to lie down after this pick",
        "This is peak comedy",
        "I'm actually laughing at how bad this is"
    ]
    
    # Short reactions for value picks (positive deltas)
    value_reactions = [
        "Great value!",
        "Love this pick",
        "Steal of the draft",
        "Someone's getting fired for letting this happen",
        "This is how you draft",
        "Absolute robbery",
        "I'm impressed",
        "This manager knows what they're doing",
        "Beautiful pick",
        "This is why you win championships",
        "Someone's going to regret this",
        "I'm taking notes",
        "This is draft mastery",
        "I'm actually jealous",
        "This is how you build a dynasty"
    ]
    
    # Determine if we should use a short reaction
    use_short_reaction = False
    
    # MEL'S SHEDEUR MELTDOWN PRIORITY - If it's Mel and a QB pick, he's losing it
    if chosen_persona == "Mel" and is_qb_pick and not is_shedeur:
        # Mel is having a meltdown about Shedeur not being drafted
        content = random.choice(mel_shedeur_meltdown)
        use_short_reaction = True  # Mark as used so we don't generate AI content
    else:
        # Normal probability logic for other cases
        if pick_delta < -5:
            # Major reaches: 40% chance of short reaction
            use_short_reaction = random.random() < 0.4
        elif pick_delta < -2:
            # Moderate reaches: 30% chance of short reaction
            use_short_reaction = random.random() < 0.3
        elif pick_delta < 0:
            # Slight reaches: 20% chance of short reaction
            use_short_reaction = random.random() < 0.2
        elif pick_delta > 5:
            # Major steals: 25% chance of short reaction
            use_short_reaction = random.random() < 0.25
        elif pick_delta > 2:
            # Good value: 15% chance of short reaction
            use_short_reaction = random.random() < 0.15
        
        if use_short_reaction:
            if pick_delta < 0:
                # Use reach reactions
                content = random.choice(short_reactions)
            else:
                # Use value reactions
                content = random.choice(value_reactions)
    
    if not use_short_reaction:
        # Generate full AI analysis
        async with httpx.AsyncClient() as client:
            content = await generate_blurb(client, system, user)

    # Create a simple colored embed that looks like a user message
    # Color based on pick delta: red for reaches, green for value
    if pick_delta < -3:
        embed_color = 0xFF4444  # Red for major reaches
    elif pick_delta < 0:
        embed_color = 0xFFAA44  # Orange for slight reaches
    elif pick_delta < 3:
        embed_color = 0x44AA44  # Green for good value
    else:
        embed_color = 0x00FF00  # Bright green for steals
    
    # Override with persona colors for very close picks (delta < 1)
    if abs(pick_delta) < 1:
        embed_color = {
            "Mel": 0xFF6B35,      # Orange (Mel Kiper's signature color)
            "Todd": 0x1E88E5,   # Blue 
        }.get(chosen_persona, 0x7B68EE)
    
    # Simple embed with just the content and color - looks like a user message
    embed = {
        "description": content,
        "color": embed_color
    }

    payload = {"embeds": [embed]}

    async with httpx.AsyncClient() as client:
        dr = await post_to_discord_with_retry(client, webhook_url, payload)

    if not dr.is_success:
        raise HTTPException(status_code=502, detail=f"Discord post failed: {dr.text}")

    return {"ok": True, "responded": True, "persona": chosen_persona, "posted": True}