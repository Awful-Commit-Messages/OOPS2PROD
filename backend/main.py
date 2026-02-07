from fastapi import FastAPI, APIRouter, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import time
from backend.game_engine import OrganicMultiAgentEngine

# start FastAPI server
app = FastAPI()
engine = OrganicMultiAgentEngine(api_keys=[])

# =======================================================
# =======================================================
# ===== Front end routes start at root directory / ======
# =======================================================
# =======================================================

# mount frontend assets
app.mount("/assets", StaticFiles(directory="./frontend/assets"), name="assets")

# root route return frontend html with assets
@app.get("/")
def root():
    return FileResponse("frontend/app.html")

# =======================================================
# =======================================================
# =====          These routes exist at /api/          ===
# ===== All backend logic will pass throgh api routes === 
# =======================================================
# =======================================================
api = APIRouter(prefix="/api")

# API status 
@api.get("/status")
def status():
    return { 
        "message": "THE SERVER IS ON, OK??", 
        "status": "OK"
    }
    
@api.post("/start")
def start_game():
    return engine.start_game()

@api.post("/play")
async def play(request: Request):
    payload = await request.json()

    event = payload.get("event", {})
    message = event.get("message")

    if not message:
        return {"error": "No message provided"}

    print(event)
    result = await engine.process_moment(message)

    print(result)
    
    return { "message": result["narration"] }
    
app.include_router(api)