import asyncio
from models.game_state import GameState
from models.npc_state import NPCState
from agents.npc_agent import NPCAgent

n1 = NPCState("001",
    "Gustav Gorfoffensonn",
    "A silly little guy who doesn't take his job seriously",
    "To do little work as possible",
    ["Gustav hates animals", "He doesn't like the player"])
n1.urgency_level = 7
n1.emotional_state = "annoyed"
n1.location = "Vet Hospital"
n1.knowledge = [
    "The player just arrived for their shift",
    "Dr. Frankenfurter is performing surgery on Ms Puff",
    "There are several animals in kennels that need care"
]

n2 = NPCState("002",
    "Dr. Frankenfurter",
    "A serious veterinarian who cares deeply for his patients",
    "Finish the surgery on Ms Puff, a large orange cat",
    ["He has a gun hidden in his desk"])
n2.urgency_level = 9
n2.emotional_state = "focused"
n2.location = "Surgery Room"
n2.knowledge = [
    "Ms Puff's surgery is going well but requires concentration",
    "Gustav is supposed to be monitoring the kennels",
    "The player just started their shift"
]

n3 = NPCState("003",
    "Sandra Martinez",
    "A worried pet owner waiting for news about her dog",
    "Find out if her dog Rex survived the emergency surgery",
    ["She blames herself for the accident", "She's considering stealing Rex if the bill is too high"])
n3.urgency_level = 3
n3.emotional_state = "anxious"
n3.location = "Waiting Room"
n3.knowledge = [
    "Rex was hit by a car an hour ago",
    "The surgery has been going on for 45 minutes",
    "No one has given her an update yet"
]

gs = GameState("Vet Hospital",
"""
The player is at work for the overnight shift and is in charge of caring for the animals
receiving inpatient care. Dr. Frankenfurter is in surgery with a critical patient.
""", "Caretaker")
gs.npcs[n1.npc_id] = n1
gs.npcs[n2.npc_id] = n2
gs.npcs[n3.npc_id] = n3

async def main():
    agent1 = NPCAgent(n1)
    context = "The player approaches Gustav and asks if he can feed the animals in the kennels"
    response = await agent1.respond_to_moment(context, gs)

    print(f"{n1.name} responds:")
    print(f"  Dialogue: {response.get('dialogue')}")
    print(f"  Action: {response.get('action')}")
    print(f"  Internal thought: {response.get('internal_thought')}")
    print(f"  Emotional state: {response.get('emotional_state')}")
    print(f"  Urgency change: {response.get('urgency_change')}")
    print(f"  Wants to act next: {response.get('wants_to_act_next')}")

    initiative = await agent1.check_initiative(gs)
    print(f"{n1.name} (urgency {n1.urgency_level}):")
    if initiative:
        print(f"  WANTS TO ACT!")
        print(f"  Action: {initiative.get('action')}")
        print(f"  Reasoning: {initiative.get('reasoning')}")
    else:
        print(f"  Does not want to act")

asyncio.run(main())