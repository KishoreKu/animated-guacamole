import os
import time
import shutil
from concurrent.futures import ThreadPoolExecutor
from functools import partial
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
            
            # Parallelize GCS Uploads
            print(f"☁️ Uploading {len(image_paths)} scenes to GCS in parallel...")
            with ThreadPoolExecutor(max_workers=5) as executor:
                uploader = partial(upload_to_gcs, bucket_name=BUCKET_NAME)
                image_urls = list(executor.map(uploader, image_paths))
            
            # Archiving locally for the Public Archive
            # Find project root where main.py and public/ folder should live
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            # If we are in local dev, 'project_root' is the parent of 'backend'. In production (Dockerfile COPY . .), it's the root.
            # But wait, in local dev, 'main.py' is inside 'backend/'. 
            # In production, 'main.py' is at '/app/'.
            
            # Let's use the current work dir as a fallback if the above doesn't have public/archive
            archive_dir = os.path.join(project_root, "public", "archive")
            if not os.path.exists(archive_dir):
                # Fallback to local 'backend/public/archive' if we are in root
                local_dev_path = os.path.join(project_root, "backend", "public", "archive")
                if os.path.exists(os.path.join(project_root, "backend")):
                    archive_dir = local_dev_path
            
            os.makedirs(archive_dir, exist_ok=True)
            
            for ip in image_paths:
                if os.path.exists(ip):
                    shutil.copy2(ip, os.path.join(archive_dir, os.path.basename(ip)))
            
            return {
                "local_image_paths": image_paths,
                "image_urls": image_urls,
                "logs": [f"🎨 Generated, uploaded to GCS, and archived {len(image_urls)} scenes locally."]
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
