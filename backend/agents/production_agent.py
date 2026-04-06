import os
import time
from backend.agents.base import BaseAgent
from backend.state import GraphState
from backend.tools.production_tools import generate_images, generate_audio, stitch_video, upload_to_gcs

class ProductionAgent(BaseAgent):
    def __init__(self):
        persona = "You are a master video editor and producer. You turn assets into cinematic experiences."
        super().__init__("production", persona)

    def generate_images_node(self, state: GraphState) -> GraphState:
        BUCKET_NAME = "ghibli-assets-1775332583"
        try:
            num_scenes = state.get('num_scenes', 5)
            prompts = [line.strip() for line in state["visuals"].split("\n") if line.strip() and (line[0].isdigit() or line.startswith("-"))]
            if not prompts:
                prompts = [state["topic"]] * num_scenes
            
            prompts = prompts[:num_scenes]
            image_paths = generate_images(prompts)
            image_urls = []
            for path in image_paths:
                url = upload_to_gcs(path, BUCKET_NAME)
                image_urls.append(url)
            
            return {
                "local_image_paths": image_paths,
                "image_urls": image_urls,
                "logs": [f"🎨 Generated and uploaded {len(image_urls)} custom Ghibli scenes."]
            }
        except Exception as e:
            return {"logs": [f"🚨 Image generation error: {str(e)}"], "status": "error"}

    def generate_audio_node(self, state: GraphState) -> GraphState:
        try:
            # We skip audio if video generation is disabled
            if not state.get('generate_video', True):
                return {"local_audio_paths": [], "logs": ["⏭️ Video generation disabled, skipping audio narration."]}
            
            image_paths = state.get("local_image_paths", [])
            scenes = state["script"].split("SCENE")
            scenes = ["SCENE" + s for s in scenes if s.strip()]
            audio_paths = generate_audio(scenes[:len(image_paths)])
            
            return {
                "local_audio_paths": audio_paths,
                "logs": ["🎙️ Narration synthesized with Ghibli-esque emotional tone."]
            }
        except Exception as e:
            return {"logs": [f"🚨 Audio synthesis error: {str(e)}"]}

    def finalize_video_node(self, state: GraphState) -> GraphState:
        BUCKET_NAME = "ghibli-assets-1775332583"
        try:
            image_paths = state.get("local_image_paths", [])
            audio_paths = state.get("local_audio_paths", [])
            
            if not state.get('generate_video', True):
                # Cleanup local images since no video is being made
                for ip in image_paths:
                    if os.path.exists(ip): os.remove(ip)
                return {"video_url": "", "logs": ["✅ Studio mission complete (Images Only)."]}

            output_file = f"video_{int(time.time())}.mp4"
            stitch_video(image_paths, audio_paths, output_file)
            video_url = upload_to_gcs(output_file, BUCKET_NAME)
            
            # Cleanup
            for ap in audio_paths: 
                if os.path.exists(ap): os.remove(ap)
            for ip in image_paths:
                if os.path.exists(ip): os.remove(ip)
            if os.path.exists(output_file): os.remove(output_file)
            
            return {
                "video_url": video_url,
                "logs": ["🎬 Post-production complete.", "✨ Masterpiece delivered!"]
            }
        except Exception as e:
            return {"logs": [f"🚨 Finalization error: {str(e)}"], "status": "error"}
