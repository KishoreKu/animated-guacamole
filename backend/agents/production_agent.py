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
        BUCKET_NAME = "ghibli-assets-1775332583"
        try:
            num_scenes = state.get('num_scenes', 5)
            # 1. Parse prompts from state["visuals"]
            prompts = [line.strip() for line in state["visuals"].split("\n") if line.strip() and (line[0].isdigit() or line.startswith("-"))]
            if not prompts:
                prompts = [state["topic"]] * num_scenes
                
            # 2. Generate Images
            print(f"ProductionAgent: Generating {num_scenes} images...")
            image_paths = generate_images(prompts[:num_scenes])
            image_urls = []
            print("ProductionAgent: Uploading images...")
            for path in image_paths:
                url = upload_to_gcs(path, BUCKET_NAME)
                image_urls.append(url)
            
            if not state.get('generate_video', True):
                print("ProductionAgent: Video generation skipped by user.")
                for ip in image_paths:
                    if os.path.exists(ip):
                        os.remove(ip)
                return {
                    "image_urls": image_urls,
                    "video_url": "",
                    "logs": ["🎬 Video generation skipped.", "✅ Images generated successfully!"]
                }
            
            # 3. Generate Audio
            print("ProductionAgent: Generating audio...")
            scenes = state["script"].split("SCENE")
            scenes = ["SCENE" + s for s in scenes if s.strip()]
            audio_paths = generate_audio(scenes[:len(image_paths)])
            
            # 4. Stitch Video
            print("ProductionAgent: Stitching video...")
            output_file = f"video_{int(time.time())}.mp4"
            stitch_video(image_paths, audio_paths, output_file)
            
            # 5. Upload Final Video
            print("ProductionAgent: Uploading final video...")
            video_url = upload_to_gcs(output_file, BUCKET_NAME)
            
            # Cleanup
            print("ProductionAgent: Cleaning up...")
            for ap in audio_paths: os.remove(ap)
            for ip in image_paths:
                if os.path.exists(ip):
                    os.remove(ip)
            os.remove(output_file)
            print("ProductionAgent: Completed successfully!")
            
            return {
                "image_urls": image_urls, 
                "video_url": video_url, 
                "logs": ["🎬 Production phase complete.", "✅ Final video ready for screening!"]
            }
        except Exception as e:
            import traceback
            err_msg = traceback.format_exc()
            print(f"CRITICAL ERROR IN PRODUCTION AGENT:\n{err_msg}")
            # Instead of crashing, return the error as a log so the UI stream doesn't abruptly drop
            # Setting a fake video_url to trigger isComplete successfully, but appending the error.
            return {
                "video_url": "ERROR",
                "logs": [f"🚨 PRODUCTION FAILED: {str(e)}", "Please check GCP logs."]
            }
