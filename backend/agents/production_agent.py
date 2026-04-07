import os
import time
import shutil
import asyncio
import re
from backend.agents.base import BaseAgent
from backend.state import GraphState
from backend.tools.production_tools import generate_images, generate_audio, stitch_video, upload_to_gcs

class ProductionAgent(BaseAgent):
    def __init__(self):
        persona = "You are a master video editor and producer. You turn assets into cinematic experiences."
        super().__init__("production", persona)

    async def generate_images_node(self, state: GraphState) -> GraphState:
        """
        [ASYNC] Generates visual assets (images) using a background thread.
        """
        try:
            num_scenes = state.get('num_scenes', 5)
            # Parse Visual Prompts
            prompts = [re.sub(r"^\d+[\.\)]\s*", "", line).strip() for line in state["visuals"].split("\n") if line.strip() and (line[0].isdigit() or line.startswith("-"))]
            if not prompts:
                prompts = [line.strip() for line in state["visuals"].split("\n") if line.strip()][:num_scenes]
            
            prompts = prompts[:num_scenes]
            
            # Offload to thread to keep heartbeat alive
            image_paths = await asyncio.to_thread(generate_images, prompts)
            
            return {
                "local_image_paths": image_paths,
                "logs": state["logs"] + [f"📸 {len(image_paths)} Ghibli-style frames captured in the cloud gallery."]
            }
        except Exception as e:
            return {"logs": state["logs"] + [f"🚨 Image generation error: {str(e)}"], "status": "error"}

    async def generate_audio_node(self, state: GraphState) -> GraphState:
        """
        [ASYNC] Synthesizes narration audio using a background thread.
        """
        try:
            if not state.get('generate_video', True):
                return {"local_audio_paths": [], "logs": state["logs"] + ["⏭️ Video generation disabled, skipping audio narration."]}
            
            # SCRUB NARRATION: Remove Scene 1, Scene 2 etc.
            raw_script = state.get("script", "")
            clean_script = re.sub(r'Scene\s+\d+[:\-]?\s*', '', raw_script, flags=re.IGNORECASE)
            narration_blocks = [s.strip() for s in clean_script.split("\n\n") if s.strip()]
            
            image_paths = state.get("local_image_paths", [])
            # Offload to thread
            audio_paths = await asyncio.to_thread(generate_audio, narration_blocks[:len(image_paths)])
            
            return {
                "local_audio_paths": audio_paths,
                "logs": state["logs"] + ["🎙️ Narration synthesized with Ghibli-esque emotional tone."]
            }
        except Exception as e:
            return {"logs": state["logs"] + [f"🚨 Audio synthesis error: {str(e)}"]}

    async def finalize_video_node(self, state: GraphState) -> GraphState:
        """
        [ASYNC] Stitches images and audio into the final Ghibli masterpiece.
        """
        BUCKET_NAME = "ghibli-assets-1775332583"
        timestamp = state.get("topic", "ghibli").replace(" ", "_").lower()
        
        try:
            image_paths = state.get("local_image_paths", [])
            audio_paths = state.get("local_audio_paths", [])
            
            if not state.get('generate_video', True):
                # Image-only mode cleanup
                return {"video_url": "", "logs": state["logs"] + ["✅ Studio mission complete (Images Only)."]}

            output_file = f"/tmp/video_{timestamp}_{int(time.time())}.mp4"
            
            # HEAVY LIFTING: Stitching video in a separate thread
            video_local = await asyncio.to_thread(
                stitch_video, 
                image_paths, 
                audio_paths, 
                output_file, 
                music_mood=state.get("music_mood")
            )
            
            # UPLOAD
            video_url = await asyncio.to_thread(upload_to_gcs, video_local, f"videos/{os.path.basename(video_local)}")
            
            # LOG SUCCESS
            return {
                "video_url": video_url,
                "status": "completed",
                "logs": state["logs"] + [
                    "🎬 Masterpiece delivered! Cinematic Ghibli video is ready.",
                    f"🎼 Ghibli Soundtrack Mastered: {state.get('music_mood', 'Peaceful')}"
                ]
            }
        except Exception as e:
            print(f"FINALIZATION ERROR: {e}")
            return {"logs": state["logs"] + [f"🚨 Finalization error: {str(e)}"], "status": "error"}
