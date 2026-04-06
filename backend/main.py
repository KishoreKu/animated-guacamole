import os
import json
import asyncio
from typing import Optional
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.orchestrator import create_orchestrator
from backend.database import get_generations, save_generation, supabase
from backend.tasks import perform_reddit_batch
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = create_orchestrator()

# --- AUTH HELPER ---

async def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authentication token")
    
    token = auth_header.split(" ")[1]
    try:
        # Verify the token with Supabase
        res = supabase.auth.get_user(token)
        if not res.user:
            raise HTTPException(status_code=401, detail="Invalid user session")
        return res.user
    except Exception as e:
        print(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")

# --- ENDPOINTS ---

@app.get("/")
def root():
    return {"status": "Ghibli Video Studio API is active"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/generations")
async def fetch_generations(request: Request, limit: int = 20):
    """
    Fetches past generation history for the logged-in user.
    """
    user = await get_current_user(request)
    data = get_generations(limit=limit, user_id=user.id)
    return {"data": data}

@app.post("/cron/reddit")
async def trigger_reddit_batch(request: Request, background_tasks: BackgroundTasks):
    """
    Cron-compatible endpoint for Reddit batch processing.
    Security: Check for X-CRON-TOKEN to prevent public trigger.
    """
    cron_token = request.headers.get("X-CRON-TOKEN")
    expected_token = os.getenv("CRON_SECRET_TOKEN", "ghibli-dev-token")
    
    if cron_token != expected_token:
        raise HTTPException(status_code=401, detail="Unauthorized cron trigger")
    
    background_tasks.add_task(perform_reddit_batch)
    return {"status": "started", "message": "Reddit automation batch is running in the background."}

# --- GENERATION LOGIC ---

@app.post("/generate")
async def generate(request: Request):
    user = await get_current_user(request)
    data = await request.json()
    topic = data.get("topic", "Enchanted Forest")
    num_scenes = data.get("numScenes", 5)
    generate_video = data.get("generateVideo", True)
    
    initial_state = {
        "topic": topic,
        "num_scenes": num_scenes,
        "generate_video": generate_video,
        "concept": "",
        "script": "",
        "visuals": "",
        "metadata": "",
        "logs": [f"🎬 Pipeline started for topic: '{topic}'"],
        "status": "running"
    }

    async def event_stream():
        try:
            accumulated_state = initial_state.copy()
            # LangGraph streaming
            async for output in orchestrator.astream(initial_state):
                for node_name, state_update in output.items():
                    accumulated_state.update(state_update)
                
                yield f"data: {json.dumps(output)}\n\n"
                await asyncio.sleep(0.1)
            
            # --- PERSISTENCE ---
            if accumulated_state.get("image_urls"):
                db_data = {
                    "topic": accumulated_state.get("topic"),
                    "concept": accumulated_state.get("concept", ""),
                    "video_url": accumulated_state.get("video_url", ""),
                    "image_urls": accumulated_state.get("image_urls", []),
                    "metadata": {"title": accumulated_state.get("metadata", ""), "tags": []},
                    "source": "manual",
                    "user_id": user.id  # Track who made this
                }
                save_generation(db_data)

            yield f"data: {json.dumps({'status': 'done'})}\n\n"
        except Exception as e:
            print(f"CRITICAL STREAM ERROR: {repr(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
