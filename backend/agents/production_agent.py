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
            
            # --- VIDEO VS IMAGE MODE ---
            if state.get('generate_video', False):
                from backend.tools.production_tools import generate_video_clips, generate_audio, stitch_video, upload_to_gcs
                
                # 1. Generate real moving video clips
                asset_paths = generate_video_clips(prompts)
                
                # 2. Generate Narration (TTS)
                script_scenes = [s for s in state["script"].split("\n\n") if s.strip()]
                audio_paths = generate_audio(script_scenes)
                
                # 3. Stitch moving clips with narrations
                video_filename = f"final_{int(time.time())}.mp4"
                local_video = stitch_video(asset_paths, audio_paths, video_filename)
                
                # 4. Upload to GCS
                public_url = upload_to_gcs(local_video, BUCKET_NAME)
                
                # Archive the final video locally for the gallery
                archive_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public", "archive")
                os.makedirs(archive_dir, exist_ok=True)
                shutil.copy(local_video, os.path.join(archive_dir, os.path.basename(local_video)))
                
                return {
                    "video_url": public_url,
                    "image_urls": [public_url], # In video mode, video is the display asset
                    "status": "completed",
                    "logs": state["logs"] + ["🎥 True AI cinematic video generated and archived!"]
                }
            else:
                from backend.tools.production_tools import generate_images, generate_audio, stitch_video, upload_to_gcs
                
                # 1. Generate Static Visual Artifacts (Imagen)
                image_paths = generate_images(prompts)
                
                # 2. Generate Narration (TTS)
                script_scenes = [s for s in state["script"].split("\n\n") if s.strip()]
                audio_paths = generate_audio(script_scenes)
                
                # 3. Stitch with Ken Burns effect
                video_filename = f"final_{int(time.time())}.mp4"
                local_video = stitch_video(image_paths, audio_paths, video_filename)
                
                # 4. Upload to GCS
                public_url = upload_to_gcs(local_video, BUCKET_NAME)
                
                # Archive results (images and video)
                archive_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public", "archive")
                os.makedirs(archive_dir, exist_ok=True)
                for img in image_paths:
                    shutil.copy(img, os.path.join(archive_dir, os.path.basename(img)))
                shutil.copy(local_video, os.path.join(archive_dir, os.path.basename(local_video)))
                
                image_archive_urls = [f"/archive/{os.path.basename(img)}" for img in image_paths]
                
                return {
                    "video_url": public_url,
                    "image_urls": image_archive_urls,
                    "status": "completed",
                    "logs": state["logs"] + ["✅ Static Ghibli video generated and archived!"]
                }
                
        except Exception as e:
            return {"logs": state["logs"] + [f"🚨 Production error: {str(e)}"], "status": "error"}

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
