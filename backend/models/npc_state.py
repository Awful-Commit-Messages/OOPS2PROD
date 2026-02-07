from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class NPCState:
    """State for a single NPC agent"""

    npc_id: str
    name: str
    personality: str
    current_goal: str
    secrets: List[str]

    # dynamic state
    location: str = "main_scene"
    emotional_state: str = "calm"
    urgency_level: int = 5  # Ranked 1-10 how badly they want to act now
    knowledge: List[str] = field(default_factory=list)
    relationships: Dict[str, int] = field(default_factory=dict)  # name, -10 to 10
    goal_status: str = "pursuing"  # pursuing|achieved|blocked|abandoned
    last_action: Optional[str] = None

    def to_dict(self):
        return {
            "npc_id": self.npc_id,
            "name": self.name,
            "personality": self.personality,
            "current_goal": self.current_goal,
            "secrets": self.secrets,
            "location": self.location,
            "emotional_state": self.emotional_state,
            "urgency_level": self.urgency_level,
            "knowledge": self.knowledge[-5:],  # last 5 things only
            "relationships": self.relationships,
            "goal_status": self.goal_status,
            "last_action": self.last_action,
        }

    def can_perceive_event(self, event: dict) -> bool:
        """Can this NPC know about this event?"""
        # same location
        if event.get("location") == self.location:
            return True

        # directly involved
        if self.npc_id in event.get("participants", []):
            return True

        # mentioned by name
        if self.name.lower() in event.get("description", "").lower():
            return True

        return False

    def update_urgency(self, event_type: str):
        """Dynamically adjust urgency based on events"""
        urgency_modifiers = {
            "threat": +3,
            "opportunity": +2,
            "setback": +2,
            "success": -1,
            "wait": -1,
        }

        delta = urgency_modifiers.get(event_type, 0)
        self.urgency_level = max(1, min(10, self.urgency_level + delta))

    def to_public_dict(self):
        # No secrets, no current_goal, and keep knowledge minimal (or omit entirely)
        return {
            "npc_id": self.npc_id,
            "name": self.name,
            "personality": self.personality,
            "location": self.location,
            "emotional_state": self.emotional_state,
            "urgency_level": self.urgency_level,
            "relationships": self.relationships,
            "goal_status": self.goal_status,
            "last_action": self.last_action,
        }
