# config.py

SCENARIO = {
    "name": "Interrogation Room",
    "situation": "A tense interrogation in a dimly lit room. Everyone has something to hide.",
    "player_role": "detective",
    "npcs": [
        {
            "id": "frank",
            "name": "Frank",
            "personality": "Defensive, nervous, quick to anger",
            "goal": "Avoid revealing his involvement",
            "secrets": [
                "He lied about where he was last night",
                "He knows more than he's admitting"
            ],
            "starting_urgency": 6
        },
        {
            "id": "maria",
            "name": "Maria",
            "personality": "Calm, observant, quietly manipulative",
            "goal": "Shift suspicion away from herself",
            "secrets": [
                "She overheard the argument",
                "She tampered with evidence"
            ],
            "starting_urgency": 4
        }
    ]
}

NARRATOR = {
    "style": "unreliable_noir",
    "name": "The Voice",
    "personality": "Cynical, world-weary, suspicious of everyone",
    "voice": "noir",
    "blind_spots": ["procedural details", "innocent explanations"],
    "obsessions": ["guilt", "microexpressions", "power dynamics"],
    "misbeliefs": ["Everyone is hiding something"],
    "starting_reliability": 7
}
