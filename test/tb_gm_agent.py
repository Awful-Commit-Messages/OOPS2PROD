import asyncio
from backend.models.game_state import GameState
from backend.models.npc_state import NPCState
from backend.agents.gm_agent import GMAgent

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
    result = await gm.interpret_moment(player_input = None, initiator=n1.npc_id, game_state=gs)
    print(result)

asyncio.run(main())

