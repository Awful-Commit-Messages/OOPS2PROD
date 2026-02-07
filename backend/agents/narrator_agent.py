from anthropic import Anthropic
import json
import logging
from typing import Dict, Optional
from models.narrator_state import NarratorState
from models.game_state import GameState

logger = logging.getLogger(__name__)

class NPCAgent: