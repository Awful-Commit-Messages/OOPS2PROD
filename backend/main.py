from fastapi import FastAPI, APIRouter, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import time

# start FastAPI server
app = FastAPI()

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
    return { "status": "THE SERVER IS ON, OK??s" }

@api.post("/play")
async def play(request: Request):
    payload = await request.json()

    event = payload.get("event", {})
    message = event.get("message")

    #TODO: implement the backend function here
    print(event)

    time.sleep(5)
    return {
        "message": "bot says: test successful! \0"
    }
    
app.include_router(api)