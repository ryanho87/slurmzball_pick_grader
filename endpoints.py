"""
API endpoints for the Fantasy Roast Bot API
"""

import httpx
from fastapi import APIRouter, HTTPException
from models import (
    DraftPick, DraftPickResponse, LeagueResponse, LeaguePromptsResponse,
    ConfigStatus, ReloadResponse
)
from config import config_manager
from prompts import build_system_prompt, build_user_prompt
from services import (
    analyze_draft_pick, should_use_short_reaction, generate_blurb,
    post_to_discord_with_retry, get_embed_color, generate_shedeur_reaction
)

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": "2024-01-19T00:00:00Z"}


@router.get("/leagues", response_model=LeagueResponse)
async def get_leagues():
    """Get available leagues and their webhook configurations"""
    return {
        "leagues": list(config_manager.league_webhooks.keys()),
        "default_league": list(config_manager.league_webhooks.keys())[0] if config_manager.league_webhooks else None
    }


@router.get("/leagues/{league_name}/prompts", response_model=LeaguePromptsResponse)
async def get_league_prompts(league_name: str):
    """Get prompt configuration for a specific league"""
    league_config = config_manager.get_league_config(league_name)
    
    if not league_config:
        available_leagues = [league['name'] for league in config_manager.config.get('leagues', [])]
        raise HTTPException(
            status_code=404,
            detail=f"League '{league_name}' not found. Available leagues: {', '.join(available_leagues)}"
        )
    
    # Get global prompts configuration
    full_config = config_manager.get_full_config()
    global_prompts = full_config.get('prompts', {}) if full_config else {}
    
    return {
        "league": league_name,
        "prompts": global_prompts,
        "webhooks": {
            "mel": league_config.get('mel'),
            "todd": league_config.get('todd'),
            "shannon": league_config.get('shannon'),
            "ab": league_config.get('ab')
        }
    }


@router.post("/admin/reload-config", response_model=ReloadResponse)
async def reload_config():
    """Reload configuration from YAML file without restarting the application"""
    success, message = config_manager.reload_configuration()
    
    if success:
        return {
            "status": "success",
            "message": message,
            "timestamp": "2024-01-19T00:00:00Z",
            "config_summary": {
                "leagues": list(config_manager.league_webhooks.keys()),
                "openai_model": config_manager.model,
                "max_tokens": config_manager.max_tokens
            }
        }
    else:
        raise HTTPException(status_code=500, detail=message)


@router.get("/admin/config-status", response_model=ConfigStatus)
async def get_config_status():
    """Get current configuration status and last reload information"""
    return config_manager.get_config_status()


@router.post("/draft-pick", response_model=DraftPickResponse)
async def draft_pick(body: DraftPick):
    """Process a draft pick and generate commentary"""
    # Validate league exists
    if body.league not in config_manager.league_webhooks:
        available_leagues = list(config_manager.league_webhooks.keys())
        raise HTTPException(
            status_code=400,
            detail=f"League '{body.league}' not found. Available leagues: {', '.join(available_leagues)}"
        )
    
    # Calculate pick-ADP delta (positive = value, negative = reach)
    pick_delta = body.pickNumber - body.adp
    
    # Get full configuration including global prompts
    full_config = config_manager.get_full_config()
    
    # Analyze if we should respond to this pick
    should_respond, chosen_persona = analyze_draft_pick(pick_delta, body.position, body.player, full_config)
    
    # If no bot should respond, return early
    if not should_respond:
        return DraftPickResponse(
            success=True, 
            message="No bot response needed for this pick",
            webhook_sent=False
        )
    
    # Get webhook URL for the chosen persona from the specified league
    league_webhooks = config_manager.league_webhooks.get(body.league)
    if not league_webhooks:
        available_leagues = list(config_manager.league_webhooks.keys())
        raise HTTPException(
            status_code=400, 
            detail=f"League '{body.league}' not found. Available leagues: {', '.join(available_leagues)}"
        )
    
    webhook_url = league_webhooks.get(chosen_persona)
    if not webhook_url:
        raise HTTPException(
            status_code=500, 
            detail=f"No webhook configured for persona '{chosen_persona}' in league '{body.league}'. Available personas: {', '.join(league_webhooks.keys())}"
        )
    
    # Build team context for enhanced analysis
    team_context = {}
    if body.team_roster:
        team_context['team_roster'] = body.team_roster
    if body.available_players:
        team_context['available_players'] = body.available_players
    
    # Check if we should use a short reaction
    use_short_reaction, short_content = should_use_short_reaction(pick_delta, chosen_persona, body.position, body.player, full_config)
    
    if use_short_reaction:
        if short_content == "SHEDEUR_AI_GENERATION":
            # Generate AI-powered Shedeur reaction
            async with httpx.AsyncClient() as client:
                content = await generate_shedeur_reaction(client, full_config)
        else:
            # Use pre-written short reaction
            content = short_content
    else:
        # Generate full AI analysis
        # Build prompts for the chosen persona
        system = build_system_prompt(chosen_persona, "roast", body.pickNumber, body.adp, pick_delta, full_config, body.team_roster, body.player, body.team)
        max_sentences = full_config.get('prompts', {}).get('max_sentences', 2)
        user = build_user_prompt(body.pickNumber, body.player, body.adp, body.team, pick_delta, max_sentences, team_context, chosen_persona)
        
        async with httpx.AsyncClient() as client:
            content = await generate_blurb(client, system, user)

    # Create embed with appropriate color
    embed_color = get_embed_color(pick_delta, chosen_persona)
    
    # Simple embed with just the content and color - looks like a user message
    embed = {
        "description": content,
        "color": embed_color
    }

    payload = {"embeds": [embed]}

    # Post to Discord
    async with httpx.AsyncClient() as client:
        dr = await post_to_discord_with_retry(client, webhook_url, payload)

    if not dr.is_success:
        raise HTTPException(status_code=502, detail=f"Discord post failed: {dr.text}")

    return DraftPickResponse(
        success=True,
        message=f"Analysis posted to Discord by {chosen_persona}",
        analysis=content,
        persona=chosen_persona,
        webhook_sent=True
    )
