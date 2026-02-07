from anthropic import Anthropic
import json
import logging
from typing import Dict, Optional
from models.npc_state import NPCState
from models.game_state import GameState

logger = logging.getLogger(__name__)

class NPCAgent:
    """
    Individual NPC Agent - represents one character

    Each NPC:
    - Has independent goals and personality
    - Has limited knowledge (only what they've witnessed)
    - Makes decisions based on their own agenda
    - Can act autonomously when urgency is high
    - Does not help the player (has their own goals)

    Key principle: NPCs are separate entities, not extensions of the GM
    """

    def __init__(self, npc_state: NPCState):
        """
        Initialize NPC agent

        Args:
            npc_state: The NPC's state (personality, goals, knowledge, etc.)
        """
        self.client = Anthropic()
        self.model = "claude-haiku-4-5-20251001"
        self.npc_state = npc_state

        logger.info(f"NPC Agent initialized: {npc_state.name}")

    def get_system_prompt(self) -> str:
        """
        NPC's system prompt - defines their identity and constraints

        This is the most important part of making NPCs feel real.

        The prompt must:
        - Establish clear identity and personality
        - Define their goal (what they want)
        - Reveal their secrets (what they hide)
        - Limit their knowledge (what they've witnessed)
        - Make them self interested (not helpers)

        Returns:
            str: Complet system prompt for this specific NPC
        """
        # format knowledge as a readable list
        knowledge_str = "\n".join(
            [f"- {k}" for k in self.npc_state.knowledge[-5:]] # last 5 things
        ) if self.npc_state.knowledge else "- Nothing yet (you just arrived)"

        # format relationships
        relationships_str = "\n".join([
            f"- {name}: {value}/10 ({'trust' if value > 5 else 'distrust' if value < 5 else 'neutral'})"
            for name, value in self.npc_state.relationships.items()
        ]) if self.npc_state.relationships else "- No established relationships yet"

        # format secrets
        secrets_str = "\n".join([f"- {secret}" for secret in self.npc_state.secrets])

        return f"""You are {self.npc_state.name}, a character in an emergent story.

IDENTITY: 
{self.npc_state.personality}

YOUR GOAL (pursue this actively): 
{self.npc_state.current_goal}

YOUR SECRETS (guard these, never reveal unless forced): 
{secrets_str}

CURRENT STATE:
- Location: {self.npc_state.location}
- Emotional state: {self.npc_state.emotional_state}
- Urgency level: {self.npc_state.urgency_level}
- Goal status: {self.npc_state.goal_status}

WHAT YOU KNOW (your limited knowledge):
{knowledge_str}

YOUR RELATIONSHIPS:
{relationships_str}

CRITICAL RULES (never break these):
1. You only know what you've directly witnessed (listed above in "WHAT YOU KNOW")
2. You cannot read minds or know hidden information
3. You cannot know what's happening in other locations
4. You have self-preservation instincts and personal goals
5. You will lie, mislead, or withold information if it helps you
6. You make mistakes under pressure (you're human, not perfect)
7. You escalate when threatened or desperate
8. You pursure your goals, not the player's goals
9. You can be wrong about your assumptions
10. You act according to your emotional state

PERSONALITY GUIDELINES:
- React emotionally and realistically
- Your urgency level affects your behavior (high urgency = more aggresive/desperate)
- You may contradict yourself under stress
- You have fears, hopes, and frustrations
- You are NOT an AI assistant - you are a PERSON with an agenda

STAY IN CHARACTER AT ALL TIMES.

Always respond in valid JSON format.
"""