import json
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.orchestrator import create_orchestrator
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

@app.get("/")
def root():
    return {"status": "Ghibli Video Studio API is active"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/generate")
async def generate(request: Request):
    data = await request.json()
    topic = data.get("topic", "Enchanted Forest")
    
    initial_state = {
        "topic": topic,
        "concept": "",
        "script": "",
        "visuals": "",
        "metadata": "",
        "logs": [f"🎬 Pipeline started for topic: '{topic}'"],
        "status": "running"
    }

    async def event_stream():
        try:
            # LangGraph streaming
            # Note: LangGraph's .astream returns an async iterator
            stream_iter = orchestrator.astream(initial_state)
            
            while True:
                try:
                    task = asyncio.create_task(stream_iter.__anext__())
                    while not task.done():
                        # Wait for up to 10 seconds for the task to finish
                        done, pending = await asyncio.wait([task], timeout=10.0)
                        if not done:
                            # Send an SSE comment to keep the connection alive
                            yield ": ping\n\n"
                    
                    output = task.result()
                    yield f"data: {json.dumps(output)}\n\n"
                    await asyncio.sleep(0.1) # Small delay for smoother UI
                except StopAsyncIteration:
                    break
            
            yield f"data: {json.dumps({'status': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
