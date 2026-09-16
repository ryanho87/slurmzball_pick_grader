"""
Prompt building and analysis framework for the Fantasy Roast Bot API
"""

from typing import Dict, Any, Optional, List
import random
from models import REQUIRED_ROSTER_POSITIONS, PlayerInfo, AvailablePlayer


def select_analysis_types(analysis_types: List[Dict[str, Any]], pick_delta: float, team_roster: Optional[List[PlayerInfo]] = None, max_types: int = 3) -> List[str]:
    """
    Select analysis types using weighted selection based on relevance and weights
    
    Args:
        analysis_types: List of analysis type configurations with weights
        pick_delta: The pick-ADP delta to determine relevance
        team_roster: Optional team roster to check for composition patterns
        max_types: Maximum number of analysis types to select
    
    Returns:
        List of selected analysis type names
    """
    if not analysis_types:
        return []
    
    # Always include adp_value for major reaches
    selected_types = []
    if pick_delta < -3:
        adp_type = next((at for at in analysis_types if at['name'] == 'adp_value'), None)
        if adp_type:
            selected_types.append(adp_type['name'])
    
    # Check for team composition patterns that would trigger diversity_analysis
    diversity_triggered = False
    if team_roster and len(team_roster) >= 3:
        # Simple heuristic: if team has 3+ players and they're all from similar demographic groups
        # This is a placeholder - you could implement more sophisticated diversity detection
        positions = [p.position for p in team_roster]
        if len(set(positions)) <= 2 and len(team_roster) >= 4:
            diversity_triggered = True
    
    # Create weighted selection pool
    available_types = []
    for at in analysis_types:
        if at['name'] not in selected_types:
            weight = at.get('weight', 0.5)
            
            # Boost weight for diversity_analysis if triggered
            if at['name'] == 'diversity_analysis' and diversity_triggered:
                weight *= 1.5
            
            # Boost weight for team_needs if team has obvious weaknesses
            if at['name'] == 'team_needs' and team_roster:
                remaining = calculate_remaining_positions(team_roster)
                if any(count > 0 for count in remaining.values()):
                    weight *= 1.3
            
            available_types.append((at['name'], weight))
    
    # Sort by weight (descending) and select top types
    available_types.sort(key=lambda x: x[1], reverse=True)
    
    # Select remaining types up to max_types
    remaining_slots = max_types - len(selected_types)
    for type_name, _ in available_types[:remaining_slots]:
        selected_types.append(type_name)
    
    return selected_types


def calculate_remaining_positions(team_roster: List[PlayerInfo]) -> Dict[str, int]:
    """
    Calculate which positions still need to be filled based on team roster
    """
    if not team_roster:
        return {}
    
    # Count how many of each position the team has
    current_positions = {}
    for player in team_roster:
        pos = player.position
        current_positions[pos] = current_positions.get(pos, 0) + 1
    
    # Calculate remaining needs
    remaining = {}
    for required_pos in REQUIRED_ROSTER_POSITIONS:
        current_count = current_positions.get(required_pos, 0)
        if current_count < 1:  # Need at least 1 of each position
            remaining[required_pos] = 1 - current_count
        elif required_pos == "BENCH":  # Can have multiple bench spots
            if current_count < 5:  # Need 5 bench spots
                remaining[required_pos] = 5 - current_count
        elif required_pos in ["WR", "RB"]:  # Can have multiple starters
            if required_pos == "WR" and current_count < 2:  # Need 2 WRs
                remaining[required_pos] = 2 - current_count
            elif required_pos == "RB" and current_count < 2:  # Need 2 RBs
                remaining[required_pos] = 2 - current_count
    
    return remaining


def build_system_prompt(persona: str, tone: str, pickNumber: int, adp: float, pick_delta: float, full_config: dict, team_roster: Optional[List[PlayerInfo]] = None, player: str = None, team: str = None) -> str:
    """Build the system prompt for OpenAI with global configuration"""
    
    # Get persona configuration from global config
    personas = full_config.get('prompts', {}).get('personas', {})
    persona_config = personas.get(persona.lower(), {})
    persona_type = persona_config.get('type', 'analytics')  # Default to analytics
    
    if persona_type == "analytics":
        return _build_analytics_prompt(persona, tone, pickNumber, adp, pick_delta, full_config, team_roster, player, team)
    elif persona_type == "reaction":
        return _build_reaction_prompt(persona, pickNumber, adp, pick_delta, full_config)
    else:
        # Fallback to legacy behavior
        ANALYTICS_PERSONAS = ["Mel", "Todd", "Shannon"]
        REACTION_PERSONAS = ["AB"]
        if persona in ANALYTICS_PERSONAS:
            return _build_analytics_prompt(persona, tone, pickNumber, adp, pick_delta, full_config, team_roster, player, team)
        elif persona in REACTION_PERSONAS:
            return _build_reaction_prompt(persona, pickNumber, adp, pick_delta, full_config)
        else:
            return _build_analytics_prompt(persona, tone, pickNumber, adp, pick_delta, full_config, team_roster, player, team)


def _build_analytics_prompt(persona: str, tone: str, pickNumber: int, adp: float, pick_delta: float, full_config: dict, team_roster: Optional[List[PlayerInfo]] = None, player: str = None, team: str = None) -> str:
    """Build structured analytics prompt for Mel, Todd, and other analytical personas"""
    # Get persona voice from full config, with fallback to defaults
    voices = {
        "Mel": full_config.get('prompts', {}).get('mel_voice', 'You are "Mel Kiper Jr."—rapid-fire expert draft analyst energy, punchy one-liners, hair-level confidence. Witty hyperbole, R-rated language welcome.'),
        "Todd": full_config.get('prompts', {}).get('todd_voice', 'You are "Todd McShay"—measured but spicy; analytics meets scouting; crisp wit with some edge.'),
        "Shannon": full_config.get('prompts', {}).get('shannon_voice', 'You are "Shannon Sharpe"—Hall of Fame tight end with that signature Southern drawl, folksy analogies, and passionate energy. Use "SKIP!" references, personal stories, and colorful metaphors about "dogs" and "ballers." Be authentic Shannon!'),
    }
    persona_line = voices.get(persona, full_config.get('prompts', {}).get('default_voice', "You are an NFL Draft analyst. Witty, R rated."))
    
    # Keep it natural but concise
    max_sentences = full_config.get('prompts', {}).get('max_sentences', 2)
    sentence_limit = "Be concise and punchy - get to the point quickly while being entertaining."
    
    # Get tone configuration from full config
    tone_config = full_config.get('prompts', {}).get('tone_config', {})
    
    # Keep tone natural - don't force specific approaches
    if pick_delta < -2:
        # Reaches - be critical but natural
        tone_line = "This is a reach - call it out in your own way."
    elif pick_delta > 2:
        # Value picks - be positive but natural
        tone_line = "This is good value - be excited in your own way."
    else:
        # Close picks - just be yourself
        tone_line = "Just react naturally to this pick."

    # Keep analysis natural - don't force specific types
    analysis_types = full_config.get('prompts', {}).get('analysis_types', [])
    
    # Simple, natural guidance instead of rigid framework
    analysis_framework = ""
    if analysis_types:
        analysis_framework = "Just react naturally to what you see. You might comment on:\n"
        analysis_framework += "- The pick value (reach vs steal)\n"
        analysis_framework += "- Team needs or roster balance\n"
        analysis_framework += "- Position scarcity or timing\n"
        analysis_framework += "- Or whatever else catches your attention\n"
        analysis_framework += "Don't force it - just be yourself!\n"
    
    # Get rules from full config - keep it simple and natural
    rules = full_config.get('prompts', {}).get('rules', [
        "Be yourself and react naturally to this pick.",
        "Use your unique voice and personality.",
        "Be entertaining and authentic - don't force structure.",
        "Comment on what stands out to you about this pick.",
        "Feel free to use grades if they feel natural, but don't force them."
    ])
    
    rules_text = "\n".join([f"- {rule}" for rule in rules])

    return (
        f"{persona_line}\n"
        f"{sentence_limit}\n"
        f"{tone_line}\n"
        f"Here's what happened: {player} was drafted by {team} at pick #{pickNumber}.\n"
        f"{analysis_framework}\n"
        "Rules:\n"
        f"{rules_text}"
    )


def _build_reaction_prompt(persona: str, pickNumber: int, adp: float, pick_delta: float, league_config: dict) -> str:
    """Build freeform reaction prompt for AB and other reaction-based personas"""
    # Get persona voice from league config
    voices = {
        "AB": league_config.get('prompts', {}).get('ab_voice', 'You are "Antonio Brown"—completely UNHINGED, conspiracy theory obsessed, ALL CAPS rants, random tangents about CTE being fake, threats to sue everyone, claims you\'re the best WR ever, emoji explosions, completely unpredictable energy.'),
        "Shannon": league_config.get('prompts', {}).get('shannon_voice', 'You are "Shannon Sharpe"—Hall of Fame tight end with that signature Southern drawl, folksy analogies, and passionate energy. Use "SKIP!" references, personal stories, and colorful metaphors about "dogs" and "ballers." Be authentic Shannon!'),
    }
    persona_line = voices.get(persona, "You are a reaction-based persona. Be entertaining and unpredictable.")
    
    # For reaction personas, just give basic context and let them react freely
    return (
        f"{persona_line}\n"
        f"REACT to this draft pick however you want. Be completely yourself.\n"
        f"Context: {persona} is reacting to pick #{pickNumber} where {adp:.1f} ADP player was selected.\n"
        f"NO RULES. NO CONSTRAINTS. NO SENTENCE LIMITS. NO GRADING. NO ANALYSIS.\n"
        f"Just be {persona} and react however you want!\n"
        f"Use ALL CAPS, emojis, and go completely unhinged if that's your style!\n"
        f"Don't analyze - just REACT!\n"
        f"Don't grade the pick - just express your feelings!\n"
        f"Don't follow any rules - be completely freeform!"
    )


def build_user_prompt(pickNumber: int, player: str, adp: float, team: str, pick_delta: float, max_sentences: int = 2, team_context: dict = None, persona: str = None) -> str:
    """Build the user prompt with optional team context"""
    
    # For reaction personas (like AB), give minimal context - just the basic pick info
    if persona in ["AB"]:
        return (
            "React to this pick however you want:\n"
            f"- Pick #{pickNumber}\n"
            f"- Player: {player}\n"
            f"- Team: {team}\n\n"
            f"Be completely yourself. No rules. No analysis. Just react!"
        )
    
    # For analytical personas (Mel, Todd, Shannon), give simple context
    context_lines = [
        f"Team {team} made pick #{pickNumber}",
        f"Player: {player}",
        f"ADP: around #{adp}"
    ]
    
    # Add simple pick quality description
    if pick_delta < -2:
        context_lines.append("This is a reach")
    elif pick_delta > 2:
        context_lines.append("This looks like good value")
    else:
        context_lines.append("This is about where expected")
    
    # Add team context if available
    if team_context:
        if team_context.get('team_roster'):
            # Group players by position for roster summary
            roster_by_position = {}
            for player_info in team_context['team_roster']:
                pos = player_info.position
                if pos not in roster_by_position:
                    roster_by_position[pos] = []
                roster_by_position[pos].append(player_info.name)
            
            roster_summary = []
            for pos, players in roster_by_position.items():
                roster_summary.append(f"{pos}: {len(players)}")
            context_lines.append(f"- Current Roster: {', '.join(roster_summary)}")
            
            # Calculate and show remaining position needs
            remaining_positions = calculate_remaining_positions(team_context['team_roster'])
            if remaining_positions:
                remaining_summary = []
                for pos, count in remaining_positions.items():
                    if count > 0:
                        remaining_summary.append(f"{pos}: {count}")
                if remaining_summary:
                    context_lines.append(f"- Still Need: {', '.join(remaining_summary)}")
        
        if team_context.get('available_players'):
            # Show top 5 available players with ranking info
            top_available = team_context['available_players'][:5]
            available_summary = []
            for player in top_available:
                available_summary.append(f"{player.name} ({player.position}, Rank: #{player.overall_ranking})")
            context_lines.append(f"- Top Available: {', '.join(available_summary)}")
    
    context_text = "\n".join(context_lines)
    
    return (
        "Here's the situation:\n"
        f"{context_text}\n\n"
        "What do you think about this pick? Keep it concise and punchy!"
    )
