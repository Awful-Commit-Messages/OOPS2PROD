from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class NarratorState:
    """State for the unreliable narrator agent"""
    narrator_id: str
    name: str
    personality: str
    narrative_style: str # noir, paranoid, drunk, optimistic, etc

    # narrator's biases
    blind_spots: List[str]
    obsessions: List[str]
    misbeliefs: List[str]

    # dynamic state
    emotional_state: str = "focused"
    reliability: int = 7 # 1 - 10
    knowledge: List[str] = field(default_factory=list)

    narrator_goal: Optional[str] = None 

    def to_dict(self):
        return {
            'narrator_id': self.narrator_id,
            'name': self.name,
            'personality': self.personality,
            'narrative_style': self.narrative_style,
            'blind_spots': self.blind_spots,
            'obsessions': self.obsessions,
            'misbeliefs': self.misbeliefs,
            'emotional_state': self.emotional_state,
            'reliability': self.reliability,
            'knowledge': self.knowledge,
            'narrator_goal': self.narrator_goal
        }