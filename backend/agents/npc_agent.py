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
    
    async def respond_to_moment(self, context: str, game_state: GameState) -> dict:
        """
        NPC responds to something that just happened

        The NPC considers:
        - What did they perceive? (based on limited knowledge)
        - How does this affect their goal?
        - What's their emotional reaction?
        - Should they speak, act, or stay silent?

        Args:
            context: What the NPC perceives (from GM)
            game_states: Current game state

        Returns:
            dict: {
                'npc_id': str,
                'npc_name': str,
                'dialogue': str or None (what they say),
                'action': str or None (what they do physically),
                'internal_though': str (private reasoning),
                'emotional_state': str,
                'urgency_change': int (-2 to +2),
                'wants_to_act_next': bool (do they want to act immediately after)
            }
        """
        # get list of other NPCs present
        other_npcs = [
            npc.name
            for npc_id, npc in game_state.npcs.items()
            if npc_id != self.npc_state.npc_id and npc.location == self.npc_state.location
        ]

        prompt = f"""
WHAT JUST HAPPENED (from your perspective):
{context}

OTHER PRESENT: {', '.join(other_npcs) if other_npcs else 'Just you and the player'}

YOUR CURRENT URGENCY: {self.npc_state.urgency_level}/10

How do you respond?

Consider:
- Does this help or hurt your goal?
- How does this make you feel?
- What do your relationship with these people suggest?
- Should you reveal information or hide it?
- Should you escalate or de-escalate?
- Are you being threatened?
- Is this an opportunity?

You can:
- Speak (dialogue)
- Act physically (action)
- Both speak and act
- Observe silently

Be specific. No "I react" but "I slam my fist on the table."
React emotionally. You are not a robot.ImportError

Respond only with valid JSON:
{{
    "dialogue": "what you say, in quotes (or null if silent)",
    "action": "what you do physically (or null if nothing)",
    "internal_thought": "your private reasoning (not visible to others)",
    "emotional_state": "your current emotion (angry/scared/calculating/desperate/calm/etc)",
    "urgency_change": -2 to +2,
    "wants_to_act_next": true/false
}}
"""
        try:
            logger.info(f"{self.npc_state.name} processing response")
            response = await self._call_claude(prompt=prompt,
                response_schema={
                    "type": "object",
                    "properties": {
                        "dialogue": {
                            "type": "string",
                            "description": "What you say, or null if silent"
                        },
                        "action": {
                            "type": "string",
                            "description": "What you do physically, or null"
                        },
                        "internal_thought": {
                            "type": "string",
                            "description": "Your private reasoning"
                        },
                        "emotional_state": {
                            "type": "string",
                            "description": "Your current emotion"
                        },
                        "urgency_change": {
                            "type": "integer",
                        },
                        "wants_to_act_next": {
                            "type": "boolean"
                        }
                    },
                    "required": ["dialogue", "action", "internal_thought", "emotional_state", "urgency_change", "wants_to_act_next"],
                    "additionalProperties": False
                })
            result = json.loads(response)

            # add NPC identification
            result['npc_id'] = self.npc_state.npc_id
            result['npc_name'] = self.npc_state.name

            # update NPC state based on response
            self._update_state_from_response(result)

            # log what the NPC did
            if result.get('dialogue'):
                logger.info(f" {self.npc_state.name} says: \"{result['dialogue'][:60]}\"")
            elif result.get('action'):
                logger.info(f" {self.npc_state.name} does: {result['action'][:60]}\"")
            else:
                logger.info(f" {self.npc_state.name} observes silently")

            return result
        
        except json.JSONDecodeError as e:
            logger.error(f"{self.npc_state.name} response JSON  parse failed: {e}")
            logger.error(f"Raw response: {response[:200]}")

            return self._fallback_response()
        
    def _update_state_from_response(self, response: dict):
        """
        Update NPC's internal state based on their response

        Args:
            response: The NPC's response dict
        """
        # update emotional state
        if response.get('emotional_state'):
            self.npc_state.emotional_state = response['emotional_state']

        # update urgency
        urgency_change = response.get('urgency_change', 0)
        self.npc_state.urgency_level = max(1, min(10, self.npc_state.urgency_level + urgency_change))

        # track last action
        if response.get('dialogue'):
            self.npc_state.last_action = f"Said: \"{response['dialogue']}\""
        elif response.get('action'):
            self.npc_state.last_action = response['action']

    def _fallback_response(self) -> dict:
        """
        Fallback response if API call fails

        Returns:
            dict: Basic response that lets the game continue
        """
        logger.warning(f"Using fallback response for {self.npc_state.name}")

        return {
            'npc_id': self.npc_state.npc_id,
            'npc_name': self.npc_state.name,
            'dialogue': self.npc_state.dialogue,
            'action': f"{self.npc_state.name} watches tensely",
            'internal_thought': "Trying to assess the situation",
            'emotional_state': self.npc_state.emotional_state,
            'urgency_change': 0,
            'wants_to_act_next': False
        }
    
    async def check_initiative(self, game_state: GameState) -> Optional[dict]:
        """
        Check if NPC wants to act autonomously

        This is called when:
        - NPC's urgency >= 7 (high urgency)
        - No player action (checking if NPCs want to drive scene)

        The NPC decides:
        - Do I need to act right now?
        - Will waiting make things worse?
        - Is this my opportunity?

        Args:
            game_state: Current game state

        Return:
            dict or None: {
                'npc_id': str,
                'npc_name': str,
                'action': str (what they want to do),
                'reasoning': str (why now)
            }
            Returns none if NPC doesn't want to act
        """
        prompt = f"""
CURRENT SITUATION:
- Your goal: {self.npc_state.current_goal}
- Your urgency: {self.npc_state.urgency_level}/10 (HIGH - you're feeling pressure)
- Your emotional state: {self.npc_state.emotional_state}
- Your goal status: {self.npc_state.goal_status}

RECENT EVENTS YOU KNOW ABOUT:
{"\n".join(self.npc_state.knowledge[-3:]) if self.npc_state.knowledge else "Nothing"}

Your urgency is HIGH. Do you need to take action right now to pursue your goal?

This is your chance to drive the scene. The player isn't acting - should you?

Consider:
- Are you threatened or in danger?
- Is there an opportunity you must seize?
- Will waiting make things worse?
- Are you about to lose what you want?
- Is time running out?
- Are you too angry/desperate to wait?

If yes, what specific action do you take?
Be concrete: Not "I do something" but "I pull out my gun and point it at Michael"

Respond only with valid JSON:
{{
    "should_act": true/false,
    "action": "sepcific action you take (if acting),
    "reasoning": "why you must act now (internal thought)
}}
"""
        try:
            logger.info(f"Checking if {self.npc_state.name} wants initiative")
            response = await self._call_claude(prompt=prompt, 
                response_schema={
                    "type": "object",
                    "properties": {
                        "should_act": {
                            "type": "boolean"
                        },
                        "action": {
                            "type": "string",
                            "description": "What you do physically, or null"
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Your private reasoning"
                        }
                    },
                    "required": ["should_act", "action", "reasoning"],
                    "additionalProperties": False
                    
                })
            result = json.loads(response)

            if result.get('should_act'):
                logger.info(f" {self.npc_state.name} WANTS TO ACT: {result['action']}")

                return {
                    'npc_id': self.npc_state.npc_id,
                    'npc_name': self.npc_state.name,
                    'action': result['action'],
                    'reasoning': result['reasoning']
                }
            else:
                logger.info(f" {self.npc_state.name} does not want to act yet")
                return None
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"{self.npc_state.name} initiative check failed: {e}")
            return None
        
    async def _call_claude(self, prompt: str, response_schema: dict) -> str:
        """
        Call Claude API with NPC's system prompt

        Args:
            prompt: User message (specific question/situation)

        Returns:
            str: Claude's response (should be JSON)
        """
        system_prompt = self.get_system_prompt()

        response = self.client.messages.create(
            model=self.model,
            max_tokens=800,
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