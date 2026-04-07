import asyncio
from backend.orchestrator import create_orchestrator
import json

async def main():
    orchestrator = create_orchestrator()
    initial_state = {
        "topic": "Enchanted Forest",
        "concept": "",
        "script": "",
        "visuals": "",
        "metadata": "",
        "logs": [],
        "status": "running"
    }
    try:
        stream_iter = orchestrator.astream(initial_state)
        task = asyncio.create_task(stream_iter.__anext__())
        print(await task)
    except Exception as e:
        print(f"FAILED: {repr(e)}")

asyncio.run(main())
