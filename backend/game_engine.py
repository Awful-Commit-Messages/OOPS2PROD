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
    The core game orchestrator.

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

        logger.info(f"Game engine initialized with {len(api_keys)} API keys")

    # =========================================================================
    # GAME INITIALIZATION
    # =========================================================================

    def start_game(self) -> dict:
        """
        Initializes a new game.

        Process:
        1. Load scenario configuration
        2. Create game state with NPCs
        3. Initialize the GM agent
        4. Initialize the NPC agents
        5. Initialize the Narrator agent
        6. Generate the opening scene

        Returns:
            dict: {
                scenario_name: str,
                narrator_name: str,
                narrator_intro: str,
                opening_scene: str,
                state: dict (full game state)
            }
        """

        logger.info("=" * 60)
        logger.info("STARTING NEW GAME")
        logger.info("=" * 60)

        # Step 1: Create a game state from the scenario configuration:
        self.state = self._create_game_state_from_config()

        # Step 2: Create narrator state from configuration:
        narrator_state = self._create_narrator_from_config()

        # Step 3: Initialize the agents:
        self._initialize_agents(narrator_state)

        # Step 4: Get the narrator's introduction:
        narrator_intro = self._get_narrator_intro()

        # Step 5: Get othe opening scene:
        opening_scene = (
            self.state.event_log[0].description if self.state.event_log else ""
        )

        logger.info(f"Game started: {self.state.scenario_name}")
        logger.info(f"Narrator: {narrator_state.name}")
        logger.info(f"NPCs: {list(self.state.npcs.keys())}")

        return {
            "scenario_name": self.state.scenario_name,
            "narrator_name": narrator_state.name,
            "narrator_intro": narrator_intro,
            "opening_scene": opening_scene,
            "state": self.state.to_dict(),
        }

    def _create_game_state_from_config(self) -> GameState:
        """
        Creates the game state from the SCENARIO configuration.

        Returns:
            GameState: Initialized game state with NPCs
        """

        # Create the base game state:
        state = GameState(
            scenario_name=SCENARIO["name"],
            situation_description=SCENARIO["situation"],
            player_role=SCENARIO["player_role"],
        )

        # Create NPCs from the configuration:
        for npc_config in SCENARIO["npcs"]:
            npc = NPCState(
                npc_id=npc_config["id"],
                name=npc_config["name"],
                personality=npc_config["personality"],
                current_goal=npc_config["goal"],
                secrets=npc_config["secrets"],
                urgency_level=npc_config["starting_urgency"],
            )
            state.npcs[npc.npc_id] = npc

        # Log the opening event from the scenario:
        state.log_event(
            event_type="gm_stimulus",
            actor="frank",  # FIXME!  This should be determined by the scenario somehow.
            description="blah blah blah",  # FIXME!
            location=state.player_location,
            participants=["frank"],  # FIXME!
        )

        return state

    def _create_narrator_from_config(self) -> NarratorState:
        """
        Creates the narrator's state from the NARRATOR configuration.

        Returns:
            NarratorState: Initialized narrator
        """

        return NarratorState(
            narrator_id=NARRATOR["style"],
            name=NARRATOR["name"],
            personality=NARRATOR["personality"],
            narrative_style=NARRATOR["voice"],
            blind_spots=NARRATOR["blind_spots"],
            obsessions=NARRATOR["obsessions"],
            reliability=NARRATOR["starting_reliability"],
        )
