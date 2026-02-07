from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from models.npc_state import NPCState

@dataclass
class Event:
    """A single event in the story"""
    moment: int
    event_type: str # player_action, npc_action, external, gm_stimulus
    actor: str
    description: str
    location: str
    participants: List[str]
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self):
        return {
            'moment': self.moment,
            'type': self.event_type,
            'actor': self.actor,
            'description': self.description,
            'location': self.location,
            'participants': self.participants
        }
    
@dataclass
class GameState:
    """Complete game state"""
    scenario_name: str
    situation_description: str
    player_role: str

    # dynamic state
    moment_count: int = 0
    player_location: str = "main_scene"
    npcs: Dict[str, NPCState] = field(default_factory=dict)
    event_log: List[Event] = field(default_factory=list)

    # scene tracking
    scene_energy: str = "building" # building, plateu, climactic, resolving
    tension_level: int = 5 # 1 - 10

    # ending detection
    scene_concluded: bool = False
    conclusion_type: Optional[str] = None # violence, resolution, departure, stalemate, null
    conclusion_description: Optional[str] = None

    # safety rails
    max_moments: int = 30 # soft limit to the amount of turns

    def to_dict(self):
        return {
            'scenario_name': self.scenario_name,
            'situation_description': self.situation_description,
            'player_role': self.player_role,
            'moment_count': self.moment_count,
            'player_location': self.player_location,
            'npcs': {k: v.to_dict() for k, v in self.npcs.items()},
            'recent_events': [e.to_dict() for e in self.event_log[-5:]],
            'scene_energy': self.scene_energy,
            'tension_level': self.tension_level,
            'scene_concluded': self.scene_concluded,
            'conclusion_type': self.conclusion_type,
            'conclusion_description': self.conclusion_description
        }