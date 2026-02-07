from anthropic import Anthropic
import json
import logging
from typing import Dict, List, Optional

from backend.models.game_state import GameState

# Logging of prompts, player actions, and state
logger = logging.getLogger(__name__)

class GMAgent:
    """
    Game Master Agent

    The GM know everything:
    - All NPC secrets and motivations
    - Complete world state
    - Objective truth of what's happening

    The GM's job:
    - Interpret player and NPC actions objectively
    - Determine realistic consequences
    - Synthesize NPC reasons into coherent scenes
    - Inject stimulus when needed

    The GM is neutral and does not favour player or NPCs.
    """

    def __init__(self):
        """
        Initialize GM Agent
        """
        self.client = Anthropic()
        self.model = "claude-sonnet-4-5-20250929"

        logger.info("GM Agent initialized")

    def get_system_prompt(self, game_state: GameState) -> str:
        """
        GM's system prompt defining its role and knowledge

        GM needs to know everything to arbitrate fairly
        
        Args:
            game_state: Current game state
        
        Returns:
            str: Complete system prompt with all context
        """
        return f"""You are the game master for an organic, emergent narrative experience.

        CORE PRINCIPLES:
        1. You are OMNISCIENT: you know all NPC secrets, goals, and the complete world state
        2. You are NEUTRAL: do not favor player or any NPC
        3. You are REALISTIC: describe waht would actually happen based on phyics and human psychology
        4. You are OBJECTIVE: report evevnts as they occur, without bias

        YOUR ROLE:
        - Interpret actions and determine their realistic consequences
        - Track what each character knows (limited information for NPCs)
        - Synthesize NPC reactions into a coherent narrative
        - Monitor scene energy and pacing
        - Allow organic endings

        CURRENT SCENARIO:
        {game_state.situation_description}

        NPCs (you know their secrets):
        {json.dumps({
            npc_id: {
                'name': npc.name,
                'goal': npc.current_goal,
                'secrets': npc.secrets,
                'emotional_state': npc.emotional_state,
                'urgency': npc.urgency_level,
                'knowledge': npc.knowledge[-3:] # last 3 things they know
            }
            for npc_id, npc in game_state.npcs.items()
        }, indent=2)}

        CRITICAL RULES:
        - NPCs only know what they've witnessed or been told (limited knowledge)
        - You see everything, but NPCs have blind spots
        - Describe realistic consequences (injury, fear, mistakes happen)
        - Don't prevent NPCs from making bad decisions
        - Don't steer towar "good" or "happy" endings
        - Let tension build organically from character conflict

        Always respond in valid JSON format
        """
    
    async def interpret_moment(self, player_input: Optional[str], initiator: str, game_state: GameState) -> dict:
        """
        Interpret what's happening this moment

        The GM answers:
        - What literally happened?
        - Who would notice/be affected?
        - What context do NPCs have?
        - How does this affect tension?

        Args:
            player_input: What player typed (or None if NPC initiated)
            initiator: Who initiated this moment ('player' or npc_id)
            game_state: Current game state

        Returns:
            dict: {
                'what_happens': str (objective description),
                'affected_npcs': list[str] (who should respond),
                'context_for_npcs': str (what NPCs perceive),
                'consequences': str (physical/environmental changes),
                'tension_delta': int (-2 to +2)
            }
        """
        # build the prompt
        if player_input:
            moment_description = f"PLAYER ACTION: {player_input}"
        else:
            npc_name = game_state.npcs[initiator].name
            moment_description = f"NPC '{npc_name}' is taking initiative based on their high urgency"

        prompt = f"""
CURRENT SITUATION:
Location: {game_state.player_location}
Moment: {game_state.moment_count}
Current Tension: {game_state.tension_level}/10
Scene Energy: {game_state.scene_energy}

NPCS PRESENT:
{json.dumps({
    npc_id: {
        'name': npc.name,
        'emotional_state': npc.emotional_state,
        'urgency': npc.urgency_level,
        'location': npc.location
    } for npc_id, npc in game_state.npcs.items()
}, indent=2)}

RECENT EVENTS (what just happened):
{game_state.get_recent_narrative(3)}

{moment_description}

Interpret this moment objectively and realistically:
1. What is LITERALLY happening? (physical actions, words spoken)
2. Which NPCs would notice or be affected? (same location, mentioned, involved)
3. What context would those NPCs have? (what they can see/hear)
4. What are immediate physical consequences? (objects moved, sounds, changes)
5. How does this affect tension? (-2 to +2)

Be specific and concrete. Avoid vague descriptions.and

Respond ONLY with valid JSON without any markdown or formatting:
{{
    "what_happens": "objective, specific description of the action",
    "affected_npcs": ["npc_id1", "npc_id2"],
    "context_for_npcs": "what the affected NPCs would perceive",
    "consequences": "immediate physical/environmental changes",
    "tension_delta": -2 to +2
}}
"""
        
        try:
            logger.info("GM interpreting moment.")
            response = await self._call_claude(
                prompt=prompt,
                game_state=game_state,
                response_schema={
                    "type": "object",
                    "properties": {
                        "what_happens": {
                            "type": "string",
                            "description": "Objective, specific description of the action"
                        },
                        "affected_npcs": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "NPC IDs who would notice or be affected"
                        },
                        "context_for_npcs": {
                            "type": "string",
                            "description": "What the affected NPCs would perceive"
                        },
                        "consequences": {
                            "type": "string",
                            "description": "Immediate physical/environmental changes"
                        },
                        "tension_delta": {
                            "type": "integer",
                            "description": "Change in tension level",
                        }
                    },
                    "required": ["what_happens", "affected_npcs", "context_for_npcs", "consequences", "tension_delta"],
                    "additionalProperties": False
                }
            )
            result = json.loads(response)

            logger.info(f"GM interpretation: {result['what_happens'][:80]}")
            logger.info(f"Affected NPCs: {result['affected_npcs']}")
            logger.info(f"Tension change: {result['tension_delta']:+d}")

            return result
        
        except json.JSONDecodeError as e:
            logger.error(f"GM interpretation JSON parse failed: {e}")
            logger.error(f"Raw response: {response[:200]}...")

            # fallback to basic intepretation
            return self._fallback_interpretation(player_input, initiator, game_state)
        
    def _fallback_interpretation(self, player_input: Optional[str], initiator: str, game_state: GameState) -> dict:
        """
        Fallback if JSON parsing fails
        
        Returns basic interpretation so game can continue 
        """
        logger.warning("Using fallback interpretation")

        return {
            "what_happens": player_input or f"{initiator} takes action",
            "affected_npcs": list(game_state.npcs.keys()), # all NPCs
            "context_for_npcs": player_input or "Something happens",
            "consequences": "The situation evolves",
            "tension_delta": 0
        }
    
    async def synthesize_narrative(self, interpretation: dict, npc_responses: List[dict], game_state: GameState) -> dict:
        """
        Combine everything into coherent objective narrative

        The GM takes:
        - Their interpretation of what happened
        - How each NPC reacted
        - Current scene state

        And creates:
        - Vivd, objective description
        - Updated tension level
        - Scene energy assessment

        This is the objective truth that the narrator will filter

        Args:
            interpretation: GM's interpreation
            npc_responses: List of NPC reaction dicts
            game_state: Current game state

        Returns:
            dict: {
                'narrative': str (objective prose),
                'tension_level': int (1-10),
                'scene_energy': str (building/plateu/climactic/resolving),
                'notable_changes': list[str]    
            }
        """
        # Format NPC responses for prompt
        npc_reactions = []
        for response in npc_responses:
            reaction = f"{response['npc_name']}: "
            if response.get('dialogue'):
                reaction += f'Says: "{response["dialogue"]}"'
            if response.get('action'):
                if response.get('dialogue'):
                    reaction += f" AND "
                reaction += f"Does: {response['action']}"
            if not response.get('dialogue') and not response.get('action'):
                reaction += "Observes silently"

            npc_reactions.append(reaction)

        npc_reactions_text = "\n".join(npc_reactions)

        prompt = f"""
WHAT HAPPENED (your interpretation):
{interpretation['what_happens']}

NPC REACTIONS:
{npc_reactions_text}

CURRENT SCENE STATE:
- Tension: {game_state.tension_level}/10
- Energy: {game_state.scene_energy}
- Location {game_state.player_location}

Your task: Create a vivid, objective narrative that:
1. Describes what happens from an omniscient perspective
2. Integrates NPC reactions naturally and specifically
3. Shows environmental details and consequences
4. Maintains appropriate tension
5. Sets up the next decision point clearly

WRITING GUIDELINES:
- Be concrete and specific (not "someone reacts" but "Frank slams his fist")
- Use sensory details (sounds, sights, physical sensations)
- Show, don't tell (not "Frank is angry" but "Frank's knuckles turn white")
- Keep it objective; no interpretation, just what's visible/audible
- Write in present tense for immediacy

This is the objective truth before the narrator filters it.staticmethod

Respond only with valid JSON:
{{
    "narrative": "vivid, specific, objective prose description (3-5 sentences)",
    "tension_level": 1-10,
    "scene_energy": "building|plateu|climactic|resolving",
    "notable_changes": ["specific", "state", "changes"]
}}
"""
        try:
            logger.info("GM synthesizing narrative")
            response = await self._call_claude(
                prompt=prompt,
                game_state=game_state,
                response_schema={
                    "type": "object",
                    "properties": {
                        "narrative": {
                            "type": "string",
                            "description": "Vivid, specific, objective prose description (3-5 sentences)"
                        },
                        "tension_level": {
                            "type": "integer",
                            "description": "Current tension level",
                        },
                        "scene_energy": {
                            "type": "string",
                            "enum": ["building", "plateu", "climactic", "resolving"],
                            "description": "Current scene energy state"
                        },
                        "notable_changes": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific state changes"
                        }
                    },
                    "required": ["narrative", "tension_level", "scene_energy", "notable_changes"],
                    "additionalProperties": False
                }
            )
            result = json.loads(response)

            logger.info(f"GM narrative created (tension: {result['tension_level']}, energy: {result['scene_energy']})")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"GM synthesis JSON parse failed: {e}")
            logger.error(f"Raw response: {response[:200]}...")

            return self._fallback_narrative(interpretation, npc_responses)
        
    def _fallback_narrative(self, interpretation: dict, npc_responses: List[dict]) -> dict:
        """
        Fallback narrative if JSON parsing fails
        """
        logger.warning("Using fallback narrative")

        narrative = interpretation['what_happens']

        if npc_responses:
            narrative += "\n\n"
            for response in npc_responses:
                if response.get('dialogue'):
                    narrative += f"{response['npc_name']}: \"{response['dialogue']}\""
                elif response.get('action'):
                    narrative += f"{response['npc_name']} {response['action']}."

        return {
            'narrative': narrative,
            'tension_level': 5,
            'scene_energy': 'plateu',
            'notable_changes': []
        }
    
    async def check_scene_status(self, game_state: GameState) -> dict:
        """
        Monitor scene health and progression

        The GM checks:
        - Is tension rising or falling?
        - Are NPCs actively pursuing goals?
        - Does scene need external stimulus?
        - Is scene naturally approaching an ending?

        Args:
            game_state: Current game state

        Returns:
            dict: {
                'energy_assessment': str (rising/plateu/falling/stalled),
                'needs_stimulus': bool,
                'stimulus_suggestion': str (if needed),
                'approaching_ending': bool,
                'ending_type': str (violence/resolution/departure/stalemate/null)
            }
        """
        prompt = f"""
CURRENT SITUATION:
{game_state.situation_description}

SCENE PROGRESS:
- Moment: {game_state.moment_count}
- Tension: {game_state.tension_level}/10
- Energy: {game_state.scene_energy}

RECENT EVENTSS:
{game_state.get_recent_narrative(5)}

NPC STATES:
{json.dumps({
    npc_id: {
        'goal': npc.current_goal,
        'goal_status': npc.goal_status,
        'urgency': npc.urgency_level,
        'emotional_state': npc.emotional_state
    } for npc_id, npc in game_state.npcs.items()
}, indent=2)}

Assess the scene objectively:
1. ENERGY: Is tension/action rising, flat, falling, or completely stalled?
    - Rising: NPCs escalating, tension building
    - Plateu: Steadh state, neither rising nor falling
    - Falling: De-escalation happening
    - Stalled: Nothing happening, scene stuck

2. STIMULUS: Does the scene need external intervention to maintain momentum?
    - Only if truly stalled (same conversation looping, no progress)

3. ENDING: Is the scene naturally approaching a conclusion?
    - Violence: Physical conflict imminent/occurred
    - Resolution: Goals achieved/conflict settled
    - Departure: Someone leaving ends the scene
    - Stalemate: Unresolvable standoff
    - Null: Scene continues

Respond only with valid JSON:
{{
    "energy_assessment": "rising|plateu|falling|stalled",
    "needs_stimulus": true/false,
    "stimulus_suggestion": "what external event could inject energy (if needed)",
    "approaching_ending": true/false,
    "ending_type": "violence|resolution|departure|stalemate|null"
}}
"""
        try:
            logger.info("GM checking scene status")
            response = await self._call_claude(
                prompt=prompt,
                game_state=game_state,
                response_schema={
                    "type": "object",
                    "properties": {
                        "energy_assessment": {
                            "type": "string",
                            "enum": ["rising", "plateu", "falling", "stalled"],
                            "description": "Current energy trend"
                        },
                        "needs_stimulus": {
                            "type": "boolean",
                            "description": "Whether external stimulus is needed"
                        },
                        "stimulus_suggestion": {
                            "type": "string",
                            "description": "What external event could inject energy"
                        },
                        "approaching_ending": {
                            "type": "boolean",
                            "description": "Whether scene is nearing conclusion"
                        },
                        "ending_type": {
                            "type": ["string", "null"],
                            "enum": ["violence", "resolution", "departure", "stalemate", "null"],
                            "description": "Type of ending if approaching"
                        }
                    },
                    "required": ["energy_assessment", "needs_stimulus", "stimulus_suggestion", "approaching_ending", "ending_type"],
                    "additionalProperties": False
                }
            )
            result = json.loads(response)

            logger.info(f"Scene status: {result['energy_assessment']}, ending: {result['approaching_ending']}")

            return result
        
        except json.JSONDecodeError as e:
            logger.error(f"GM scene check JSON parse failed: {e}")

            # Default scene fallback
            return {
                'energy_assessment': 'plateu',
                'needs_stimulus': False,
                'stimulus_suggestion': '',
                'approaching_ending': False,
                'ending_type': None
            }
        
    async def generate_stimulus(self, game_state: GameState) -> str:
        """
        Generate external event to inject energy when scene stalls

        The GM creates realistic external events:
        - Someone new arrives
        - Phone rings / alarm sounds
        - Something breaks
        - Weather/environment changes
        - Time pressure emerges

        Args:
            game_state: Current game state

        Returns:
            str: Description of external stimulus
        """
        prompt = f"""
The scene has stalled, the energy is dropping, and NPCs aren't driving action.PermissionError

SITUATION: {game_state.situation_description}
LOCATION: {game_state.player_location}
RECENT EVENTS: {game_state.get_recent_narrative(3)}

Generate ONE external stimulus that:
- Is realistic for this setting
- Injects new tension or urgency
- Gives NPCs something to react to
- Doesn't solve the conflict (just adds pressure)

Examples:
- Door slams open and someone unexpected enters
- Phone rings with an urgent call
- Glass shatters / loud crash outside
- Police sirens getting closer
- Lights flicker and go out
- Timer/deadline suddenly matters

Keep it SHORT (one sentence) and CONCRETE.

Respond only with valid JSON:
{{
    "stimulus": "one sentence description of what happened"
}}
"""
        try:
            logger.info("GM generating stimulus")
            response = await self._call_claude(
                prompt=prompt,
                game_state=game_state,
                response_schema={
                    "type": "object",
                    "properties": {
                        "stimulus": {
                            "type": "string",
                            "description": "One sentence description of what happened"
                        }
                    },
                    "required": ["stimulus"],
                    "additionalProperties": False
                }
            )
            result = json.loads(response)

            stimulus = result['stimulus']
            logger.info(f"Stimulus: {stimulus}")

            return stimulus
        
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Stimulus generation failed: {e}")

            # Default stimulus fallback
            return "A loud crash from outside makes everyone freeze."
        
    async def _call_claude(self, prompt: str, game_state: GameState, response_schema: dict) -> str:
        """
        Call Claude API wih GM's system prompt

        Args:
            prompt: User message (the specific question)
            game_state: Current game state

        Returns:
            str: Claude's response
        """
        system_prompt = self.get_system_prompt(game_state)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            output_config={
                "format": {
                    "type": "json_schema",
                    "schema": response_schema
                }
            }
        )

        return response.content[0].text