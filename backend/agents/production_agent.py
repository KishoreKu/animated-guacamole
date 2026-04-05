import os
import time
from backend.agents.base import BaseAgent
from backend.state import GraphState
from backend.tools.production_tools import generate_images, generate_audio, stitch_video, upload_to_gcs

class ProductionAgent(BaseAgent):
    def __init__(self):
        persona = "You are a master video editor and producer. You turn assets into cinematic experiences."
        super().__init__("production", persona)

    def execute(self, state: GraphState) -> GraphState:
        state["logs"].append("🎬 Production phase started. Preparing assets...")
        BUCKET_NAME = "ghibli-assets-1775332583"
        
        # 1. Parse prompts from state["visuals"]
        prompts = [line.strip() for line in state["visuals"].split("\n") if line.strip() and (line[0].isdigit() or line.startswith("-"))]
        if not prompts:
            prompts = [state["topic"]] * 5
            
        # 2. Generate Images
        image_paths = generate_images(prompts[:5])
        image_urls = []
        for path in image_paths:
            url = upload_to_gcs(path, BUCKET_NAME)
            image_urls.append(url)
            os.remove(path) # Cleanup local
        state["image_urls"] = image_urls
        state["logs"].append(f"🖼️ {len(image_urls)} scene frames painted and stored.")
        
        # 3. Generate Audio
        scenes = state["script"].split("SCENE")
        scenes = ["SCENE" + s for s in scenes if s.strip()]
        audio_paths = generate_audio(scenes[:len(image_urls)])
        state["logs"].append(f"🎙️ Narration recorded for all scenes.")
        
        # 4. Stitch Video
        output_file = f"video_{int(time.time())}.mp4"
        stitch_video(image_paths, audio_paths, output_file)
        
        # 5. Upload Final Video
        video_url = upload_to_gcs(output_file, BUCKET_NAME)
        state["video_url"] = video_url
        
        # Cleanup
        for ap in audio_paths: os.remove(ap)
        os.remove(output_file)
        
        state["logs"].append(f"✅ Final video ready for screening!")
        return state
