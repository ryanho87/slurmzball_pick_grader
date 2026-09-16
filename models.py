"""
Data models and schemas for the Fantasy Roast Bot API
"""

from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field, field_validator
import csv
from io import StringIO


# Static roster positions that every team needs to fill
REQUIRED_ROSTER_POSITIONS = [
    "QB", "WR", "WR", "RB", "RB", "TE", "FLEX", 
    "K", "DST", "BENCH", "BENCH", "BENCH", "BENCH", "BENCH"
]


class PlayerInfo(BaseModel):
    """Individual player information"""
    name: str
    position: str


class AvailablePlayer(BaseModel):
    """Available player with ranking information"""
    name: str
    overall_ranking: int
    team: str
    position: str


class DraftPick(BaseModel):
    """Draft pick submission model with enhanced team context"""
    pickNumber: int = Field(..., ge=1, description="Draft pick number")
    player: str = Field(..., description="Player name")
    position: str = Field(..., description="Player position (QB, RB, WR, TE, etc.)")
    adp: float = Field(..., description="Average Draft Position")
    team: str = Field(..., description="Team name")
    league: str = Field(..., description="League name to use for webhook selection")
    
    # Enhanced context fields (all optional for backward compatibility)
    team_roster: Optional[List[PlayerInfo]] = Field(
        None, 
        description="Current team composition as list of players with positions (CSV format: Name,Positions)"
    )
    available_players: Optional[List[AvailablePlayer]] = Field(
        None, 
        description="Top available players by ranking (CSV format: Name,Overall Ranking,Team,Positions)"
    )

    @field_validator('team_roster', mode='before')
    @classmethod
    def parse_team_roster_csv(cls, v):
        if isinstance(v, str):
            # Parse space-separated format: "Name,Positions Player1,Pos1 Player2,Pos2 ..."
            try:
                # Split by spaces to get individual player entries
                parts = v.strip().split()
                players = []
                
                for part in parts:
                    if ',' in part:
                        # Split by comma to get name and position
                        name_pos = part.split(',', 1)
                        if len(name_pos) == 2:
                            name = name_pos[0].strip()
                            position = name_pos[1].strip()
                            
                            # Skip header entries
                            if name.lower() == 'name' or position.lower() == 'positions':
                                continue
                                
                            if name and position:
                                players.append(PlayerInfo(name=name, position=position))
                
                return players
            except Exception as e:
                raise ValueError(f"Failed to parse team_roster: {e}")
        return v

    @field_validator('available_players', mode='before')
    @classmethod
    def parse_available_players_csv(cls, v):
        if isinstance(v, str):
            # Parse space-separated format: "Name,Overall Ranking,Team,Positions Player1,Rank1,Team1,Pos1 Player2,Rank2,Team2,Pos2 ..."
            try:
                # Split by spaces to get individual player entries
                parts = v.strip().split()
                players = []
                
                for part in parts:
                    if part.count(',') == 3:  # Should have 4 fields: name,ranking,team,position
                        # Split by comma to get all fields
                        fields = part.split(',')
                        if len(fields) == 4:
                            name = fields[0].strip()
                            ranking_str = fields[1].strip()
                            team = fields[2].strip()
                            position = fields[3].strip()
                            
                            # Skip header entries
                            if name.lower() == 'name' or ranking_str.lower() == 'overall ranking':
                                continue
                                
                            try:
                                overall_ranking = int(ranking_str)
                                if name and team and position:
                                    players.append(AvailablePlayer(
                                        name=name,
                                        overall_ranking=overall_ranking,
                                        team=team,
                                        position=position
                                    ))
                            except ValueError:
                                # Skip rows where ranking can't be parsed as int
                                continue
                
                return players
            except Exception as e:
                raise ValueError(f"Failed to parse available_players: {e}")
        return v


class ResponseProbabilityConfig(BaseModel):
    """Configuration for bot response probabilities"""
    qb_picks: float = Field(1.0, ge=0.0, le=1.0, description="Probability of responding to QB picks (1.0 = always)")
    other_positions: float = Field(0.4, ge=0.0, le=1.0, description="Probability of responding to non-QB picks")
    major_reaches: float = Field(0.8, ge=0.0, le=1.0, description="Probability of responding to major reaches (ADP delta < -5)")
    moderate_reaches: float = Field(0.6, ge=0.0, le=1.0, description="Probability of responding to moderate reaches (ADP delta -5 to -2)")
    slight_reaches: float = Field(0.5, ge=0.0, le=1.0, description="Probability of responding to slight reaches (ADP delta -2 to 0)")
    good_value: float = Field(0.4, ge=0.0, le=1.0, description="Probability of responding to good value (ADP delta 0 to 3)")
    great_value: float = Field(0.6, ge=0.0, le=1.0, description="Probability of responding to great value (ADP delta 3 to 8)")
    massive_steals: float = Field(0.7, ge=0.0, le=1.0, description="Probability of responding to massive steals (ADP delta > 8)")


class ShortResponseConfig(BaseModel):
    """Configuration for short response probabilities"""
    major_reaches: float = Field(0.4, ge=0.0, le=1.0, description="Probability of using short response for major reaches")
    moderate_reaches: float = Field(0.3, ge=0.0, le=1.0, description="Probability of using short response for moderate reaches")
    slight_reaches: float = Field(0.2, ge=0.0, le=1.0, description="Probability of using short response for slight reaches")
    good_value: float = Field(0.15, ge=0.0, le=1.0, description="Probability of using short response for good value")
    great_value: float = Field(0.25, ge=0.0, le=1.0, description="Probability of using short response for great value")
    massive_steals: float = Field(0.2, ge=0.0, le=1.0, description="Probability of using short response for massive steals")


class ShedeurReactionConfig(BaseModel):
    """Configuration for Shedeur Sanders reactions"""
    enabled: bool = Field(True, description="Whether to enable special Shedeur reactions")
    max_sentences: int = Field(2, ge=1, le=3, description="Maximum sentences for Shedeur reactions")
    use_ai_generation: bool = Field(True, description="Whether to use AI generation for Shedeur reactions")
    fallback_reactions: List[str] = Field(
        default=[
            "WHERE IS SHEDEUR SANDERS?!",
            "I CANNOT BELIEVE SHEDEUR IS STILL ON THE BOARD!",
            "This is a DISASTER! Shedeur Sanders should have been taken 10 picks ago!",
            "I'm having a MELTDOWN! Shedeur Sanders is the best QB in this draft!",
            "This is why the NFL is BROKEN! Shedeur Sanders is being IGNORED!"
        ],
        description="Fallback reactions if AI generation fails"
    )


class LeagueConfig(BaseModel):
    """League configuration model"""
    name: str
    mel: str  # Discord webhook URL for Mel
    todd: str  # Discord webhook URL for Todd
    prompts: Optional[Dict[str, Any]] = None


class AnalysisType(BaseModel):
    """Analysis type configuration model"""
    name: str
    description: str
    max_sentences: int = 1
    weight: float = Field(0.5, ge=0.0, le=1.0, description="Weight for analysis type selection (higher = more likely to be chosen)")


class ToneConfig(BaseModel):
    """Tone configuration model"""
    major_reach: str
    moderate_reach: str
    slight_reach: str
    good_value: str
    great_value: str
    massive_steal: str


class PromptConfig(BaseModel):
    """Prompt configuration model"""
    max_sentences: int = 2
    mel_voice: str
    todd_voice: str
    default_voice: str
    tone_config: Optional[ToneConfig] = None
    analysis_types: Optional[List[AnalysisType]] = None
    analysis_selection_rules: Optional[List[str]] = None
    rules: Optional[List[str]] = None
    response_probabilities: Optional[ResponseProbabilityConfig] = None
    short_response_config: Optional[ShortResponseConfig] = None
    shedeur_reactions: Optional[ShedeurReactionConfig] = None


class OpenAIConfig(BaseModel):
    """OpenAI configuration model"""
    model: str = "gpt-4o-mini"
    max_tokens: int = 280


class Config(BaseModel):
    """Main configuration model"""
    openai: OpenAIConfig
    leagues: List[LeagueConfig]


class ConfigResponse(BaseModel):
    """Configuration response model"""
    message: str
    timestamp: str
    config_hash: str


class ConfigStatusResponse(BaseModel):
    """Configuration status response model"""
    status: str
    last_loaded: str
    config_hash: str
    leagues: List[str]


class ConfigStatus(BaseModel):
    """Configuration status model"""
    status: str
    last_loaded: str
    config_hash: str
    leagues: List[str]


class ReloadResponse(BaseModel):
    """Configuration reload response model"""
    status: str
    message: str
    timestamp: str
    config_summary: Dict[str, Any]


class DraftPickResponse(BaseModel):
    """Response model for draft pick analysis"""
    success: bool
    message: str
    analysis: Optional[str] = None
    persona: Optional[str] = None
    webhook_sent: bool = False
    error: Optional[str] = None


class LeagueResponse(BaseModel):
    """Response model for leagues list"""
    leagues: List[str]
    default_league: Optional[str] = None


class LeaguePromptsResponse(BaseModel):
    """Response model for league prompts"""
    league: str
    prompts: Dict[str, Any]
    webhooks: Dict[str, str]
