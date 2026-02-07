import asyncio

from models.game_state import GameState
from models.npc_state import NPCState
from models.narrator_state import NarratorState
from agents.narrator_agent import NarratorAgent

n1 = NPCState("001",
    "Gustav Gorfoffensonn",
    "A silly little guy who doesn't take his job seriously",
    "To do little work as possible",
    ["Gustav hates animals", "He doesn't like the player"])
n1.urgency_level = 7
n1.emotional_state = "annoyed"
n1.location = "Vet Hospital"

n2 = NPCState("002",
    "Dr. Frankenfurter",
    "A serious veterinarian who cares deeply for his patients",
    "Finish the surgery on Ms Puff, a large orange cat",
    ["He has a gun hidden in his desk"])
n2.urgency_level = 9
n2.emotional_state = "focused"
n2.location = "Surgery Room"

gs = GameState("Vet Hospital",
"""
The player is at work for the overnight shift and is in charge of caring for the animals
receiving inpatient care. Dr. Frankenfurter is in surgery with a critical patient.
""", "Caretaker")
gs.npcs[n1.npc_id] = n1
gs.npcs[n2.npc_id] = n2
gs.tension_level = 6

narrator_state = NarratorState(
    narrator_id="001",
    name="The Anxious Observer",
    personality="A nervous, detail-oriented narrator who sees danger everywhere",
    narrative_style="Tense, hurried prose with lots of sensory details about sounds and smells",
    blind_spots=["positive emotions", "humor", "calm moments"],
    obsessions=["potential dangers", "things that could go wrong", "suspicious behavior"],
    misbeliefs=["Everyone is hiding something", "Silence means something bad is about to happen"]
)
narrator_state.emotional_state = "paranoid"
narrator_state.reliability = 6

async def main():
    narrator = NarratorAgent(narrator_state)

    gm_facts = {
        "what_happens": "Gustav slouches into the kennel area, clipboard dangling from one hand. He glances at the cages of recovering animals, then immediately turns toward the break room.",
        "affected_npcs": ["001"],
        "context_for_npcs": "Gustav is clearly avoiding his responsibilities",
        "consequences": "The animals remain unattended",
        "tension_delta": 1
    }
    
    npc_responses = [
        {
            "npc_name": "Gustav Gorfoffensonn",
            "dialogue": "Yeah, yeah, I'll get to it in a minute...",
            "action": "waves dismissively without looking back",
            "internal_thought": "These animals can wait, I need a coffee break",
            "emotional_state": "indifferent"
        }
    ]
    
    result = await narrator.narrate_moment(gm_facts, npc_responses, gs)
    
    print("NARRATOR'S FILTERED VERSION:")
    print(f"Narration: {result['narration']}\n")
    print(f"What narrator noticed: {result['what_you_noticed']}")
    print(f"What narrator missed: {result['what_you_missed']}")
    print(f"Narrator's interpretation: {result['your_interpretation']}")
    print(f"Reliability check: {result['reliability_check']}/10")

    gs.tension_level = 8
    #gs.narrative_history.extend([
    #    "Gustav ignored the animals again",
    #   "Dr. Frankenfurter's surgery took a dangerous turn",
    #    "Strange noises came from the surgery room"
    #])
    
    narrator = NarratorAgent(narrator_state)
    
    aside = await narrator.narrator_aside(gs)
    
    if aside:
        print(f"NARRATOR ADDS ASIDE:")
        print(f"  \"{aside}\"\n")
    else:
        print("Narrator chose not to add commentary\n")

    unreliable_narrator_state = NarratorState(
        narrator_id = "002",
        name = "The Conspiracy Theorist",
        personality = "Sees hidden meanings and connections everywhere",
        narrative_style = "Breathless, rambling prose full of implications",
        blind_spots=["mundane explanations", "coincidences"],
        obsessions=["hidden meanings", "secret motives", "conspiracies"],
        misbeliefs=["Nothing happens by accident", "Everyone is secretly working together"]
    )
    unreliable_narrator_state.emotional_state = "manic"
    unreliable_narrator_state.reliability = 3  # Very unreliable
    
    # Simple, mundane facts
    gm_facts = {
        "what_happens": "Dr. Frankenfurter walks to the sink and washes his hands thoroughly after the surgery.",
        "affected_npcs": ["002"],
        "context_for_npcs": "The surgery was successful",
        "consequences": "Ms Puff is stable",
        "tension_delta": -1
    }
    
    npc_responses = [
        {
            "npc_name": "Dr. Frankenfurter",
            "dialogue": None,
            "action": "dries hands methodically",
            "internal_thought": "Good work, the cat will be fine",
            "emotional_state": "relieved"
        }
    ]
    
    result = await narrator.narrate_moment(gm_facts, npc_responses, gs)
    
    print("UNRELIABLE NARRATOR'S VERSION:")
    print(f"Narration: {result['narration']}\n")
    print(f"Narrator's (probably wrong) interpretation: {result['your_interpretation']}")
    print(f"Reliability: {result['reliability_check']}/10")

    print(f"Initial reliability: {narrator.narrator_state.reliability}/10")
    print(f"Initial emotional state: {narrator.narrator_state.emotional_state}\n")
    
    # something suspicious
    gm_facts_1 = {
        "what_happens": "Gustav whispers something to Dr. Frankenfurter when he thinks no one is looking.",
        "affected_npcs": ["001", "002"],
        "context_for_npcs": "Private conversation",
        "consequences": "Both look toward the player nervously",
        "tension_delta": 2
    }
    
    result_1 = await narrator.narrate_moment(gm_facts_1, [], gs)
    print(f"After suspicious event:")
    print(f"  Reliability: {narrator.narrator_state.reliability}/10")
    print(f"  Knowledge gained: {narrator.narrator_state.knowledge[-1]}\n")
    
    # something boring
    gm_facts_2 = {
        "what_happens": "A cat purrs contentedly in its kennel, recovering well.",
        "affected_npcs": [],
        "context_for_npcs": "Peaceful moment",
        "consequences": "The atmosphere briefly relaxes",
        "tension_delta": -1
    }
    
    result_2 = await narrator.narrate_moment(gm_facts_2, [], gs)
    print(f"After peaceful moment:")
    print(f"  Narration: {result_2['narration']}")
    print(f"  What narrator missed: {result_2['what_you_missed']}")

asyncio.run(main())