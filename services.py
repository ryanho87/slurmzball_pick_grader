"""
Business logic services for the Fantasy Roast Bot API
"""

import random
import httpx
from fastapi import HTTPException
from typing import Dict, Any, Optional
from config import config_manager


# ---------- OpenAI call ----------
async def generate_blurb(client: httpx.AsyncClient, system: str, user: str) -> str:
    """
    Uses the OpenAI Responses API (recommended) but falls back to Chat Completions if desired.
    Docs: Responses API & Chat Completions. 
    """
    from config import config_manager

    # Get API key from config manager
    headers = {"Authorization": f"Bearer {config_manager.get_api_key()}"}

    # Prefer Responses API
    resp = await client.post(
        "https://api.openai.com/v1/responses",
        headers=headers,
        json={
            "model": config_manager.model,
            "input": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            "max_output_tokens": config_manager.max_tokens,
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
                "model": config_manager.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ],
                "max_tokens": config_manager.max_tokens,
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


# ---------- Draft Analysis Logic ----------
def analyze_draft_pick(pick_delta: float, position: str, player: str, league_config: dict) -> tuple:
    """
    Analyze whether a bot should respond to this draft pick and which persona to use.
    Returns (should_respond, chosen_persona)
    """
    # Get response probability configuration from global config
    response_config = league_config.get('prompts', {}).get('response_probabilities', {})
    
    # DECISION LOGIC: Should any bot respond to this pick?
    should_respond = False
    chosen_persona = None
    
    # 1. QB PICKS - Use configurable probability
    if position.upper() == "QB":
        qb_prob = response_config.get('qb_picks', 1.0)
        should_respond = random.random() < qb_prob
        if should_respond:
            # Choose persona randomly - all bots have equal chance regardless of position
            chosen_persona = random.choice(["Mel", "Todd", "Shannon", "AB"])
    
    # 2. OTHER POSITIONS - Use configurable probability based on pick quality
    else:
        # Determine pick quality category
        if pick_delta < -5:
            prob = response_config.get('major_reaches', 0.9)
        elif pick_delta < -2:
            prob = response_config.get('moderate_reaches', 0.8)
        elif pick_delta < 0:
            prob = response_config.get('slight_reaches', 0.8)
        elif pick_delta < 3:
            prob = response_config.get('good_value', 0.8)
        elif pick_delta < 8:
            prob = response_config.get('great_value', 0.8)
        else:
            prob = response_config.get('massive_steals', 0.9)
        
        should_respond = random.random() < prob
        
        if should_respond:
            # Choose persona randomly - all bots have equal chance regardless of ADP
            chosen_persona = random.choice(["Mel", "Todd", "Shannon", "AB"])
    
    return should_respond, chosen_persona


def should_use_short_reaction(pick_delta: float, chosen_persona: str, position: str, player: str, league_config: dict) -> tuple:
    """
    Determine if we should use a short reaction instead of AI generation.
    Returns (use_short_reaction, content)
    """
    # Get short response configuration from global config
    short_config = league_config.get('prompts', {}).get('short_response_config', {})
    
    # Check if this is a QB pick that's not Shedeur Sanders
    is_qb_pick = position.upper() == "QB"
    is_shedeur = "shedeur" in player.lower() or "sanders" in player.lower()
    
    # MEL'S SHEDEUR MELTDOWN PRIORITY - If it's Mel and a QB pick, he's losing it
    if chosen_persona == "Mel" and is_qb_pick and not is_shedeur:
        # Check if Shedeur reactions are enabled
        shedeur_config = league_config.get('prompts', {}).get('shedeur_reactions', {})
        if shedeur_config.get('enabled', True):
            # Use AI generation if enabled, otherwise fallback
            if shedeur_config.get('use_ai_generation', True):
                return True, "SHEDEUR_AI_GENERATION"  # Special flag for AI generation
            else:
                # Use fallback reactions
                fallback_reactions = shedeur_config.get('fallback_reactions', [
                    "WHERE IS SHEDEUR SANDERS?!",
                    "I CANNOT BELIEVE SHEDEUR IS STILL ON THE BOARD!",
                    "This is a DISASTER! Shedeur Sanders should have been taken 10 picks ago!"
                ])
                return True, random.choice(fallback_reactions)
    
    # Normal probability logic for other cases
    use_short_reaction = False
    
    if pick_delta < -5:
        # Major reaches: configurable probability
        use_short_reaction = random.random() < short_config.get('major_reaches', 0.4)
    elif pick_delta < -2:
        # Moderate reaches: configurable probability
        use_short_reaction = random.random() < short_config.get('moderate_reaches', 0.3)
    elif pick_delta < 0:
        # Slight reaches: configurable probability
        use_short_reaction = random.random() < short_config.get('slight_reaches', 0.2)
    elif pick_delta > 5:
        # Major steals: configurable probability
        use_short_reaction = random.random() < short_config.get('massive_steals', 0.2)
    elif pick_delta > 2:
        # Good value: configurable probability
        use_short_reaction = random.random() < short_config.get('great_value', 0.25)
    
    if use_short_reaction:
        # AB gets his own special unhinged reactions
        if chosen_persona == "AB":
            ab_reactions = [
                "CTE IS A MYTH!!! 🧠❌",
                "I'M THE BEST WR EVER!!! 🏆🔥",
                "CRACKER OF THE DAY!!! 🥖👑",
                "THEY'RE TRYING TO SILENCE ME!!! 🤐🚫",
                "I'LL SUE EVERYONE!!! ⚖️💸",
                "THIS IS A CONSPIRACY!!! 🕵️‍♂️🔍",
                "I'M GOING TO THE TOP!!! 📈🚀",
                "NOBODY CAN STOP ME!!! 💪😤",
                "I'M UNSTOPPABLE!!! ⚡💯",
                "THEY DON'T KNOW MY POWER!!! 💥👑",
                "I'M THE GOAT!!! 🐐🔥",
                "THIS IS MY DESTINY!!! ⭐🎯",
                "I'M BREAKING ALL RECORDS!!! 📊🏅",
                "THEY'RE SCARED OF ME!!! 😱💀",
                "I'M THE CHOSEN ONE!!! ✨👑",
                "THIS IS MY MOMENT!!! 🌟⚡"
            ]
            content = random.choice(ab_reactions)
            return True, content
        else:
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
        
        if pick_delta < 0:
            # Use reach reactions
            content = random.choice(short_reactions)
        else:
            # Use value reactions
            content = random.choice(value_reactions)
        
        return True, content
    
    return False, ""


async def generate_shedeur_reaction(client: httpx.AsyncClient, league_config: dict) -> str:
    """
    Generate a Shedeur Sanders reaction using AI with strict constraints
    """
    shedeur_config = league_config.get('prompts', {}).get('shedeur_reactions', {})
    max_sentences = shedeur_config.get('max_sentences', 2)
    
    # Create a very specific system prompt for Shedeur reactions
    system_prompt = f"""You are Mel Kiper Jr. and you are having a MELTDOWN because Shedeur Sanders is not being drafted!

CRITICAL CONSTRAINTS:
- Write EXACTLY {max_sentences} sentence{'s' if max_sentences > 1 else ''}
- Maximum 15 words per sentence
- Focus on your absolute disbelief and outrage
- Use ALL CAPS for emphasis on key words
- Include "Shedeur Sanders" in every response
- Be absolutely MELODRAMATIC and over-the-top
- Use exclamation marks and emotional language
- This is your #1 priority - you're losing your mind!

Tone: ABSOLUTE MELTDOWN - You're having a breakdown because Shedeur Sanders is being ignored!"""

    user_prompt = f"Generate a {max_sentences}-sentence meltdown about Shedeur Sanders not being drafted. Be absolutely over-the-top emotional!"

    try:
        content = await generate_blurb(client, system_prompt, user_prompt)
        return content
    except Exception as e:
        # Fallback to pre-written reactions if AI generation fails
        fallback_reactions = shedeur_config.get('fallback_reactions', [
            "WHERE IS SHEDEUR SANDERS?!",
            "I CANNOT BELIEVE SHEDEUR IS STILL ON THE BOARD!",
            "This is a DISASTER! Shedeur Sanders should have been taken 10 picks ago!"
        ])
        return random.choice(fallback_reactions)


def get_embed_color(pick_delta: float, chosen_persona: str) -> int:
    """Get the appropriate embed color based on pick delta and persona"""
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
            "Shannon": 0xFFD700,  # Gold (Shannon Sharpe's signature color)
            "AB": 0x9C27B0,     # Purple (AB's signature color)
        }.get(chosen_persona, 0x7B68EE)
    
    return embed_color
