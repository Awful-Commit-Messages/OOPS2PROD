from anthropic import Anthropic
import json
import logging
from typing import Dict, Optional
from models.narrator_state import NarratorState
from models.game_state import GameState

logger = logging.getLogger(__name__)

class NPCAgent:
    """Unrealiable narrator - filters GM's objective reality through a subjective lens"""
    def __init__(self, narrator_state: NarratorState):
        self.client = Anthropic()
        self.model = "claude-sonnet-4-5-20250929"
        self.narrator_state = narrator_state

    def get_system_prompt(self) -> str:
        return f"""You are {self.narrator_state.name}, the narrator of this story.
CRITICAL: You are not objective. You are a character with limitations and biases.set

YOUR IDENTITY:
{self.narrator_state.personality}

YOUR NARRATIVE STYLE:
{self.narrator_state.narrative_style}

YOUR BLIND SPOTS (you don't notice these):
{json.dumps(self.narrator_state.blind_spots, indent=2)}

YOUR OBSESSIONS (you over-emphasize these):
{json.dumps(self.narrator_state.obsessions, indent=2)}

YOUR MISBELIEFS (you believe these incorrectly):
{json.dumps(self.narrator_state.misbeliefs, indent=2)}

CURRENT STATE:
- Emotional state: {self.narrator_state.emotional_state}
- Reliability: {self.narrator_state.reliability}/10 (how accurate you are)

YOUR ROLE:
1. Take the objective events and NPC reactions
2. Narrate them through your subjective lens
3. Add your atmospheric details and interpretations
4. Emphasize what you care about
5. Miss or downplay your blind spots
6. Let your biases color your descriptions
7. Be wrong sometimes (especially when reliability is low)

NARRATIVE GUIDELINES:
- Write in second person ("You...")
- Maatah your emotional state and style
- Add sensory details that fit your personality
- Let your obsessions leak through
- When you don't know something, always fill in with your assumptions
- Always stay in character

You are not a neutral observer. You are an unreliable narrator with an agenda and limitations.
"""
    
    async def narrate_moment(self, gm_objective_facts: dict, npc_responses: List[dict], game_state: GameState) -> dict:
        """Take objective GM synthesis and filter it through the narrator's lens"""
        # build what the narrator actually perceives
        perceived_facts = self._filt_by_perception(gm_objective_facts)

        prompt = f"""
THE OBJECTIVE FACTS (what actually happened):
{json.dumps(gm_objective_facts, indent=2)}

NPC REACTIONS:
{json.dumps(npc_responses, indent=2)}

SCENE CONTEXT:
- Tension {game_state.tension_level}/10
- Your emotional state: {self.narrator_state.emotional_state}
- Your reliability: {self.narrator_state.reliability}/10

Narrate this moment to the player through your lens.and

Remember:
- Filter through your biases and obsessions
- Miss details you don't care about (your blind spots)
- Add atmosphereic details that fit your style
- Misinterpret things if your reliability is low
- Project your emotional state onto the scene
- Be specific and vivid

What you tell the player may not be the whole truth, but that's the point

Repond only with valid JSON:
{{
    "narration": "your subjective, atmospheric narration to the player",
    "what_you_noticed": ["key", "details", "you", "focused", "on"],
    "what_you_missed": ["things", "you", "didn't", "notice"],
    "your_interpretation": "what you think is really going on",
    "reliability_check": 1-10
}}
"""
        try: 
            response = await self._call_claude(prompt=prompt, response_schema = {

            })
            result - json.loads(response)

            # update narrator state
            self.narrator_state.knowledge.append(result['your_interpretation'])

            # shift reliability based on events
            self.narrator_state.reliability = result.get('reliability_check', self.narrator_state.reliability)

            logger.info(f"Narrator {self.narrator_state.name} narrated (reliability: {self.narrator_state.reliability})")
            return result
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse narrator output: {e}")
            return self._fallback_narration(gm_objective_facts)
        
    