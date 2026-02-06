# backend/game_engine.py

import asyncio
import logging
from typing import List, Dict, Optional

from models.game_state import GameState
from models.npc_state import NPCState
from models.narrator_state import NarratorState

from agents.gm_agent import GMAgent
from agents.npc_agent import NPCAgent
from agents.narrator_agent import NarratorAgent

from config import SCENARIO, NARRATOR

# Create a logger object to handle logging functionality:
logger = logging.getLogger(__name__)


class OrganicMultiAgentEngine:
    """
    Our core game orchestrator

    Responsibilities:
    1. Initialize all the agents (GM, NPCs, Narrator)
    2. Coordinate thhe multi-agent game loop
    3. Manage the game state
    4. Handle parallel NPC processing
    5. Monitor scene health
    """

    def __init__(self, api_keys: List[str]):
        """
        Initialize the engine with API keys

        Args:
            api_keys: List of Anthropic API keys
                      - api_keys[0] -> GM and Narrator (Sonnet)
                      - api_keys[1:] -> NPCs (Haiku), round-robin key rotation
        """

        self.api_keys = api_keys

        # These will be initialized by start_game():
        self.state: Optional[GameState] = None
        self.gm_agent: Optional[GMAgent] = None
        self.npc_agents: Dict[str, NPCAgent] = {}
        self.narrator_agent: Optional[NarratorAgent] = None

        logger.info("Game engine initialized with {len(api_keys)} API keys")
