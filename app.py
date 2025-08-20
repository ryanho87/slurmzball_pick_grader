import os
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
    "McShay": os.getenv("DISCORD_WEBHOOK_MCSHAY"),
    "Default": os.getenv("DISCORD_WEBHOOK_DEFAULT"),
}

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "280"))

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY env var is required")

app = FastAPI(title="Fantasy Roast Bot (Python)")

# ---------- Schemas ----------
class DraftPick(BaseModel):
    pickNumber: int = Field(..., ge=1)
    player: str
    adp: float
    team: str
    persona: Optional[str] = Field(default="Mel")      # "Mel" | "McShay" | etc.
    tone: Optional[str] = Field(default="roast")       # "roast" | "serious" | "balanced"
    leagueType: Optional[str] = Field(default="redraft")  # "redraft" | "dynasty" | "best ball"


# ---------- Prompts ----------
def build_system_prompt(persona: str, tone: str, league: str) -> str:
    voices = {
        "Mel": 'You are "Mel Kiper Jr."—rapid-fire draft analyst energy, punchy one-liners, hair-level confidence. Witty hyperbole, no profanity. 1-3 sentences.',
        "McShay": 'You are "Todd McShay"—measured but spicy; analytics meets scouting; crisp wit. 1-3 sentences.',
    }
    persona_line = voices.get(persona, "You are an NFL Draft analyst. 1–3 sentences. Witty, R rated.")
    tone_line = {
        "roast": "Tone: savagely roast, no holds barred.",
        "serious": "Tone: serious, concise scouting evaluation.",
        "balanced": "Tone: balanced—one praise, one concern, a final verdict."
    }.get(tone, "Tone: comically roasty but light-hearted.")

    return (
        f"{persona_line}\n"
        f"{tone_line}\n"
        f"League context: {league}.\n"
        "Rules:\n"
        "- Include a quick pick grade (A–F) and a 3–6 word verdict tag in ALL CAPS at the end, e.g., 'Grade: B | VERDICT: VALUE WITH RISK'.\n"
        "- Mention ADP context briefly if relevant."
    )


def build_user_prompt(pickNumber: int, player: str, adp: float, team: str) -> str:
    return (
        "Draft pick context:\n"
        f"- Pick #: {pickNumber}\n"
        f"- Player: {player}\n"
        f"- Selecting Team: {team}\n"
        f"- Player ADP: {adp}\n\n"
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
    # Get webhook URL, with fallback logic
    webhook_url = WEBHOOKS.get(body.persona)
    if not webhook_url or webhook_url == "https://discord.com/api/webhooks/...":
        # Fallback to Default if persona webhook is missing or incomplete
        webhook_url = WEBHOOKS.get("Default")
        if body.persona != "Default":
            print(f"Warning: Using Default webhook for {body.persona} (persona webhook incomplete)")
    
    if not webhook_url:
        raise HTTPException(status_code=500, detail="No webhook configured for this persona/default.")

    system = build_system_prompt(body.persona, body.tone, body.leagueType)
    user = build_user_prompt(body.pickNumber, body.player, body.adp, body.team)

    async with httpx.AsyncClient() as client:
        content = await generate_blurb(client, system, user)

    # Create a rich Discord embed for better formatting
    embed_color = {
        "Mel": 0xFF6B35,      # Orange (Mel Kiper's signature color)
        "McShay": 0x1E88E5,   # Blue 
        "Default": 0x7B68EE   # Medium slate blue
    }.get(body.persona, 0x7B68EE)
    
    # Extract grade and verdict from the content if present
    grade_line = ""
    verdict_line = ""
    main_content = content
    
    # Look for Grade: and VERDICT: patterns
    import re
    grade_match = re.search(r'Grade:\s*([A-F][+-]?)', content, re.IGNORECASE)
    verdict_match = re.search(r'VERDICT:\s*([A-Z\s]+)', content, re.IGNORECASE)
    
    if grade_match:
        grade_line = grade_match.group(1)
        main_content = re.sub(r'Grade:\s*[A-F][+-]?\s*\|?\s*', '', main_content, flags=re.IGNORECASE)
    
    if verdict_match:
        verdict_line = verdict_match.group(1).strip()
        main_content = re.sub(r'\|\s*VERDICT:\s*[A-Z\s]+', '', main_content, flags=re.IGNORECASE)
    
    # Clean up any remaining formatting artifacts
    main_content = main_content.strip()
    
    embed = {
        "title": f"🏈 Draft Analysis: {body.player}",
        "description": main_content,
        "color": embed_color,
        "fields": [
            {
                "name": "📊 Pick Info",
                "value": f"**Pick #{body.pickNumber}** • **Team:** {body.team}\n**ADP:** {body.adp} • **League:** {body.leagueType.title()}",
                "inline": False
            }
        ],
        "footer": {
            "text": f"Analysis by {body.persona} • {body.tone.title()} tone"
        },
        "timestamp": None  # Discord will use current time
    }
    
    # Add grade and verdict as separate fields if found
    if grade_line or verdict_line:
        grade_verdict_value = ""
        if grade_line:
            grade_verdict_value += f"**Grade:** {grade_line}"
        if verdict_line:
            if grade_verdict_value:
                grade_verdict_value += f"\n**Verdict:** {verdict_line}"
            else:
                grade_verdict_value += f"**Verdict:** {verdict_line}"
        
        embed["fields"].append({
            "name": "📈 Final Assessment",
            "value": grade_verdict_value,
            "inline": True
        })

    payload = {"embeds": [embed]}

    async with httpx.AsyncClient() as client:
        dr = await post_to_discord_with_retry(client, webhook_url, payload)

    if not dr.is_success:
        raise HTTPException(status_code=502, detail=f"Discord post failed: {dr.text}")

    return {"ok": True, "persona": body.persona, "posted": True}