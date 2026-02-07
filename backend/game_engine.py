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

    def _initialize_agents(self, narrator_state: NarratorState):
        """
        Creates all the different agent instances.

        Args:
            narrator_state: Narrator state configuration
        """

        # GM and Narrator share first API key (both need Sonnet):
        self.gm_agent = GMAgent(self.api_keys[0])
        self.narrator_agent = NarratorAgent(self.api_keys[0], narrator_state)

        # NPCs use the remaining API keys in round-robin.
        # This distributes the load across multiple API keys.
        self.npc_agents = {}
        for i, (npc_id, npc_state) in enumerate(self.state.npcs.items()):
            # Round-robin through available keys (skip first, it's for GM/Narrator):
            key_index = 1 + (i % max(1, len(self.api_keys) - 1))  # Math, ugh.
            if key_index >= len(self.api_keys):
                key_index = 0  # Rotate back to zero

            api_key = self.api_keys[key_index]
            self.npc_agents[npc_id] = NPCAgent(api_key, npc_state)

            logger.info(f"Created NPC agent: {npc_state.name} (key {key_index})")


def _get_narrator_intro(self) -> str:
    """
    Gets the narrator's opening line.

    Returns:
        str: Narrator's introduction
    """

    return "This is a test intro.  Please fix me!"  # FIXME!  This should probably be generated by GM/Narrator


# =============================================================================
# CORE GAME LOOP
# =============================================================================


async def process_moment(self, player_input: Optional[str] = None) -> dict:
    """
    Prcesses one moment in the story.

    This is THE core function, where the multi-agent orchestration occurs.

    Args:
        player_input: What the player typed (or None for autonomous NPC action)

    Returns:
        dict: {
            narration: str (what the player sees, through their narrator's eyes),
            narrator_reliability: int,
            npc_responses: list[dict],
            immediate_actions: list[dict],
            state: dict,
            scene_status: dict,
            debug: dict (the GM's objective truth)
        }
    """

    # Validate that the game is active:
    if not self.state or self.state.scene_concluded:
        return {"error": "Game not active or already concluded."}

    # Increment the moment counter:
    self.state.moment_count += 1

    logger.info("=" * 60)
    logger.info(f"MOMENT {self.state.moment_count}")
    logger.info("=" * 60)

    # Determine who initated this moment:
    if player_input:
        initiator = "player"
        logger.info(f"Player: {player_input}")
    else:
        # Check if any NPC wants to act autonomously:
        initiator = await self._find_urgent_npc()
        if not initiator:
            return {"error": "No action taken - no urgent NPCs"}
        logger.info(f"NPC Initiative: {self.state.npcs[initiator].name}")

    # =========================================================================
    # PHASE 1: GM INTERPRETS THE MOMENT (OBJECTIVE TRUTH)
    # =========================================================================

    logger.info("Phase 1: GM is interpreting the moment...")
    gm_interpretation = await self.gm_agent.interpret_mement(
        player_input, initiator, self.state
    )

    # Log the event to the game state:
    self.state.log_event(
        event_type="player_action" if player_input else "npc_action",
        actor=initiator,
        description=gm_interpretation["what_happens"],
        location=self.state.player_location,
        participants=["player"] + gm_interpretation.get("affected_npcs", []),
    )

    # Update tension from the GM's interpretation:
    tension_delta = gm_interpretation.get("tension_delta", 0)
    self.state.tension_level = max(1, min(10, self.state.tension_level + tension_delta))
    logger.info(f"Tension: {self.state.tension_level}/10 (Δ{tension_delta:+d})")

    # =========================================================================
    # PHASE 2: NPC AGENTS RESPOND (PARALLEL - REAL MULTI-AGENT!)
    # =========================================================================

    affected_npc_ids = gm_interpretation.get("affected_npcs", [])

    if affected_npc_ids:
        logger.info(f"Phase 2: Querying {len(affected_npc_ids)} NPCs in parallel...")

        # Create async tasks for each affected NPC:
        # This is TRUE parallel processing - all the NPCs respond simultaneously!
        npc_response_tasks = [
            self.npc_agents[npc_id].respond_to_moment(
                gm_interpretation["context_for_npcs"], self.state
            )
            for npc_id in affected_npc_ids
        ]

        # Wait for all NPCs to respond:
        npc_responses = await asyncio.gather(*npc_response_tasks)

        # Log what the NPCs did:
        for response in npc_responses:
            logger.info(
                f"  {response['npc_name']}: {response.get('dialogue') or response.get('action', 'observes')}"
            )
    else:
        logger.info("Phase 2: No NPCs affected")
        npc_responses = []

    # =========================================================================
    # PHASE 3: GM NARRATIVE SYNTHESIS (OBJECTIVE NARRATIVE)
    # =========================================================================

    logger.info("Phase 3: GM is synthesizing the narrative...")
    gm_narrative = await self.gm_agent.synthesize_narrative(
        gm_interpretation, npc_responses, self.state
    )

    # Update state from GM's synthesis:
    self.state.tension_level = gm_narrative.get(
        "tension_level", self.state.tension_level
    )
    self.state.scene_energy = gm_narrative.get("scene_energy", self.state.scene_energy)
    logger.info(f"Scene energy: {self.state.scene_energy}")

    # =========================================================================
    # PHASE 4: NARRATOR FILTERS (SUBJECTIVE RETELLING)
    # =========================================================================

    logger.info("Phase 4: Narrator is retelling the story through a distorted lens...")
    narrator_output = await self.narrator_agent.narrate_moment(
        {
            "what_happens": gm_narrative["narrative"],
            "tension": self.state.tension_level,
            "energy": self.state.scene_energy,
        },
        npc_responses,
        self.state,
    )

    logger.info(
        f"Narrator reliability: {narrator_output.get('reliability_check', 'unknown')}/10"
    )

    # Check if the narrator wants to add an aside:
    narrator_aside = await self.narrator_agent.narrator_aside(self.state)
    if narrator_aside:
        logger.info(f"Narrator aside: {narrator_aside[:50]}...")

    # =========================================================================
    # PHASE 5: CHECK SCENE STATUS
    # =========================================================================

    logger.info("Phase 5: Checking scene status...")
    scene_status = await self.gm_agent.check_scene_status(self.state)
    logger.info(f"Energy assessment: {scene_status.get('energy_assessment')}")

    # Check for natural ending:
    if scene_status.get("approaching_ending"):
        logger.info(f"Scene ending detected: {scene_status.get('ending_type')}")
        self._conclude_scene(scene_status.get("ending_type"))

    # =========================================================================
    # PHASE 6: CHECK FOR IMMEDIATE NPC INITIATIVES
    # =========================================================================

    logger.info("Phase 6: Checking for immediate NPC actions...")
    immediate_actions = await self._check_immeidate_initiatives()
    if immediate_actions:
        logger.info(f"Immediate actions: {len(immediate_actions)} NPC(s) want to act.")

    # =========================================================================
    # PHASE 7: INJECT STIMULUS IF STALLING
    # =========================================================================

    external_event = None
    if scene_status.get("energy_assessment") == "stalled" and scene_status.get(
        "need_stimulus"
    ):
        logger.info("Phase 7: Scene stalling - injecting stimulus...")
        external_event = await self.gm_agent.generate_stimulus(self.state)

        # Log the stimulus
        self.state.log_event(
            event_type="external",
            actor="environment",
            description=external_event,
            location=self.state.player_location,
        )
        logger.info(f"Stimulus: {external_event}")

    # =========================================================================
    # SAFETY RAIL: FORCE CONCLUSION IF TOO LONG
    # =========================================================================

    if (
        self.state.moment_count >= self.state.max_moments
        and not self.state.scene_concluded
    ):
        logger.warning("Scene exceeding max moments: forcing conclusion")
        self._force_conclusion()

    # =========================================================================
    # RETURN RESULT
    # =========================================================================

    logger.info("=" * 60)
    logger.info(f"MOMENT {self.state.moment_count} COMPLETE")
    logger.info("=" * 60)

    return {
        # What the player sees (narrator's filtered version):
        "narration": narrator_output["narration"],
        "narrator_reliability": self.narrator_agent.narrator_state.reliability,
        "narrator_aside": narrator_aside,
        # Metadata for UI display:
        "npc_responses": npc_responses,
        "immediate_actions": immediate_actions,
        "external_event": external_event,
        # Game state
        "state": self.state.to_dict(),
        "scene_status": scene_status,
        # Debug info (the GM's objective truth vs. the narrator's version):
        "debug": {
            "gm_objective_truth": gm_narrative["narrative"],
            "narrator_noticed": narrator_output.get("what_you_noticed", []),
            "narrator_missed": narrator_output.get("what_you_missed", []),
            "narrator_interpretation": narrator_output("your_interpretation", ""),
        },
    }
