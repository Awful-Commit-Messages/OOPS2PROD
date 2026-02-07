# backend/game_engine.py

import asyncio
import logging
from typing import List, Dict, Optional

from backend.models.game_state import GameState
from backend.models.npc_state import NPCState
from backend.models.narrator_state import NarratorState

from backend.agents.gm_agent import GMAgent
from backend.agents.npc_agent import NPCAgent
from backend.agents.narrator_agent import NarratorAgent

from config import SCENARIO, NARRATOR

logger = logging.getLogger(__name__)


class OrganicMultiAgentEngine:
    """
    Core game orchestrator
    """

    def __init__(self, api_keys: Optional[List[str]] = None):
        # api_keys kept for future use, not required right now
        self.api_keys = api_keys or []

        self.state: Optional[GameState] = None
        self.gm_agent: Optional[GMAgent] = None
        self.narrator_agent: Optional[NarratorAgent] = None
        self.npc_agents: Dict[str, NPCAgent] = {}

        logger.info("Game engine initialized")

    # =========================================================================
    # GAME INITIALIZATION
    # =========================================================================

    async def start_game(self) -> dict:
        logger.info("=" * 60)
        logger.info("STARTING NEW GAME")
        logger.info("=" * 60)

        self.state = self._create_game_state_from_config()
        narrator_state = self._create_narrator_from_config()
        self._initialize_agents(narrator_state)

        opening = await self.gm_agent.generate_opening_scene(self.state)
        self.state.tension_level = opening.get(
            "initial_tension_level", self.state.tension_level
        )
        self.state.scene_energy = opening.get(
            "initial_scene_energy", self.state.scene_energy
        )

        npc_briefings = opening.get("npc_briefings") or []

        # Backwards compatibility: allow either dict (old) or list (new)
        if isinstance(npc_briefings, dict):
            iterable = [{"npc_id": k, "briefing": v} for k, v in npc_briefings.items()]
        else:
            iterable = npc_briefings

        for item in iterable:
            npc_id = item.get("npc_id")
            briefing = item.get("briefing")
            if npc_id in self.state.npcs and briefing:
                self.state.npcs[npc_id].knowledge.append(f"[Scene start] {briefing}")

        self.state.log_event(
            event_type="gm_stimulus",
            actor="environment",
            description="The interrogation begins.  Everyone waits for the detective to speak.",
            location=self.state.player_location,
            participants=["player"] + list(self.state.npcs.keys()),
        )

        narrator_output = await self.narrator_agent.narrate_moment(
            {
                "what_happens": opening.get("player_intro", ""),
                "tension": self.state.tension_level,
                "energy": self.state.scene_energy,
            },
            [],
            self.state,
        )

        return {
            "scenario_name": self.state.scenario_name,
            "narrator_name": narrator_state.name,
            "player_role": self.state.player_role,
            "narrator_intro": narrator_output.get("narration", ""),
            "opening_scene": opening.get("player_intro", ""),
            "player_instructions": opening.get("player_instructions", ""),
            "suggested_actions": opening.get("suggested_actions", []),
            "state": self.state.to_public_dict()
            if hasattr(self.state, "to_public_dict")
            else self.state.to_dict(),
            "debug": {
                "gm_private_notes": opening.get("gm_private_notes", ""),
                "narrator_briefing": opening.get("narrator_briefing", ""),
            },
        }

    def _create_game_state_from_config(self) -> GameState:
        state = GameState(
            scenario_name=SCENARIO["name"],
            situation_description=SCENARIO["situation"],
            player_role=SCENARIO["player_role"],
        )

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

        state.log_event(
            event_type="gm_stimulus",
            actor="environment",
            description="The situation begins.",
            location=state.player_location,
        )

        return state

    def _create_narrator_from_config(self) -> NarratorState:
        return NarratorState(
            narrator_id=NARRATOR["style"],
            name=NARRATOR["name"],
            personality=NARRATOR["personality"],
            narrative_style=NARRATOR["voice"],
            blind_spots=NARRATOR["blind_spots"],
            obsessions=NARRATOR["obsessions"],
            misbeliefs=NARRATOR.get("misbeliefs", []),
            reliability=NARRATOR["starting_reliability"],
        )

    def _initialize_agents(self, narrator_state: NarratorState):
        self.gm_agent = GMAgent()
        self.narrator_agent = NarratorAgent(narrator_state)

        self.npc_agents = {}
        for npc_id, npc_state in self.state.npcs.items():
            self.npc_agents[npc_id] = NPCAgent(npc_state)
            logger.info(f"Created NPC agent: {npc_state.name}")

    def _get_narrator_intro(self) -> str:
        return "The room feels tense as the story begins."

    # =========================================================================
    # CORE GAME LOOP
    # =========================================================================

    async def process_moment(self, player_input: Optional[str] = None) -> dict:
        if not self.state or self.state.scene_concluded:
            return {"error": "Game not active or already concluded."}

        self.state.moment_count += 1

        if player_input:
            initiator = "player"
        else:
            initiator = await self._find_urgent_npc()
            if not initiator:
                return {"error": "No action taken"}

        gm_interpretation = await self.gm_agent.interpret_moment(
            player_input, initiator, self.state
        )

        self.state.log_event(
            event_type="player_action" if player_input else "npc_action",
            actor=initiator,
            description=gm_interpretation["what_happens"],
            location=self.state.player_location,
            participants=["player"] + gm_interpretation.get("affected_npcs", []),
        )

        self.state.tension_level = max(
            1,
            min(
                10, self.state.tension_level + gm_interpretation.get("tension_delta", 0)
            ),
        )

        affected_npcs = gm_interpretation.get("affected_npcs", [])
        npc_responses = (
            await asyncio.gather(
                *[
                    self.npc_agents[npc_id].respond_to_moment(
                        gm_interpretation["context_for_npcs"], self.state
                    )
                    for npc_id in affected_npcs
                    if npc_id in self.npc_agents
                ]
            )
            if affected_npcs
            else []
        )

        gm_narrative = await self.gm_agent.synthesize_narrative(
            gm_interpretation, npc_responses, self.state
        )

        self.state.tension_level = gm_narrative.get(
            "tension_level", self.state.tension_level
        )
        self.state.scene_energy = gm_narrative.get(
            "scene_energy", self.state.scene_energy
        )

        narrator_output = await self.narrator_agent.narrate_moment(
            {
                "what_happens": gm_narrative["narrative"],
                "tension": self.state.tension_level,
                "energy": self.state.scene_energy,
            },
            npc_responses,
            self.state,
        )

        narrator_aside = await self.narrator_agent.narrator_aside(self.state)

        scene_status = await self.gm_agent.check_scene_status(self.state)

        if scene_status.get("approaching_ending"):
            self._conclude_scene(scene_status.get("ending_type"))

        external_event = None
        if scene_status.get("energy_assessment") == "stalled" and scene_status.get(
            "needs_stimulus"
        ):
            external_event = await self.gm_agent.generate_stimulus(self.state)
            self.state.log_event(
                event_type="external",
                actor="environment",
                description=external_event,
                location=self.state.player_location,
            )

        if (
            self.state.moment_count >= self.state.max_moments
            and not self.state.scene_concluded
        ):
            self._force_conclusion()

        return {
            "narration": narrator_output["narration"],
            "narrator_reliability": self.narrator_agent.narrator_state.reliability,
            "narrator_aside": narrator_aside,
            "npc_responses": npc_responses,
            "external_event": external_event,
            "state": self.state.to_dict(),
            "scene_status": scene_status,
            "debug": {
                "gm_objective_truth": gm_narrative["narrative"],
                "narrator_noticed": narrator_output.get("what_you_noticed", []),
                "narrator_missed": narrator_output.get("what_you_missed", []),
                "narrator_interpretation": narrator_output.get(
                    "your_interpretation", ""
                ),
            },
        }

    # =========================================================================
    # HELPERS
    # =========================================================================

    async def _find_urgent_npc(self) -> Optional[str]:
        urgent = [
            npc_id for npc_id, npc in self.state.npcs.items() if npc.urgency_level >= 7
        ]

        if not urgent:
            return None

        initiatives = await asyncio.gather(
            *[self.npc_agents[npc_id].check_initiative(self.state) for npc_id in urgent]
        )

        for init in initiatives:
            if init:
                return init["npc_id"]

        return None

    def _conclude_scene(self, ending_type: Optional[str]):
        self.state.scene_concluded = True
        self.state.conclusion_type = ending_type or "resolution"
        self.state.conclusion_description = "The scene concludes."

    def _force_conclusion(self):
        self.state.scene_concluded = True
        self.state.conclusion_type = "time_limit"
        self.state.conclusion_description = "Time runs out."

    def get_state(self) -> dict:
        return self.state.to_dict() if self.state else {"error": "No active game"}
