import asyncio
from models.game_state import GameState
from models.npc_state import NPCState
from agents.gm_agent import GMAgent

n1 = NPCState("001",
    "Gustav Gorfoffensonn",
    "A silly little guy who doesn't take his job seriously",
    "To do little work as possible",
    ["Gustav hates animals", "He doesn't like the player"])
n1.urgency_level = 7

n2 = NPCState("002",
    "Dr. Frankenfurter",
    "A serious veterinarian who cares deeply for his patients",
    "Finish the surgery on Ms Puff, a large orange cat",
    ["He has a gun"])

gs = GameState("Vet Hospital",
"""
The player is at work for the overnight shift and is in charge of caring for the animals
receiving inpatient care. 
""", "Caretaker")
gs.npcs[n1.npc_id] = n1
gs.npcs[n2.npc_id] = n2

async def main():
    gm = GMAgent()
    interpretation = await gm.interpret_moment(player_input = None, initiator=n1.npc_id, game_state=gs)
    print("interpretation: ", interpretation)

    responses = [
        {
            'npc_name': "Gustav Gorfoffensonn",
            'dialogue': "Hello, how are you?",
            'action': "brushes his hand through his hair"
        }
    ]
    narrative = await gm.synthesize_narrative(interpretation=interpretation, npc_responses=responses, game_state=gs)
    print("narrative: ", narrative)

    scene_status = await gm.check_scene_status(game_state=gs)
    print("scene_status: ", scene_status)

    stimulus = await gm.generate_stimulus(game_state=gs)
    print("stimulus: ", stimulus)




asyncio.run(main())

