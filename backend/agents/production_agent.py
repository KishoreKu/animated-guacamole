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
            import re
            
            num_scenes = state.get('num_scenes', 5)
            # 1. Parse Visual Prompts (Numbered list or paragraphs)
            prompts = [re.sub(r"^\d+[\.\)]\s*", "", line).strip() for line in state["visuals"].split("\n") if line.strip() and (line[0].isdigit() or line.startswith("-"))]
            if not prompts:
                # Fallback if list is not numbered
                prompts = [line.strip() for line in state["visuals"].split("\n") if line.strip()][:num_scenes]
            
            # 2. Parse Narration Blocks (Extracting only 'Narration:' content)
            # This ensures extra lines or titles don't create audio clips
            narration_blocks = re.findall(r"Narration:\s*(.*?)(?=\nSCENE|\nVisual|\n$|$)", state["script"], re.DOTALL | re.IGNORECASE)
            
            # --- SCENE SCRUBBER ---
            # Remove "Scene 1", "Scene 2", etc. if they hallucinate into the narration
            cleaned_narrations = []
            for nb in narration_blocks:
                cleaned = re.sub(r"^(Scene\s*\d+[:\-]?\s*)", "", nb.strip(), flags=re.IGNORECASE)
                cleaned_narrations.append(cleaned)
            narration_blocks = cleaned_narrations

            # Fallback if LLM deviates from 'Narration:' format
            if not narration_blocks or len(narration_blocks) < num_scenes:
                print("⚠️ Narration parser fallback: splitting by scenes...")
                raw_scenes = [s for s in state["script"].split("SCENE") if s.strip()]
                narration_blocks = []
                for s in raw_scenes:
                    if "Narration:" in s:
                        text = s.split("Narration:")[-1].strip()
                        # Scrub here too
                        text = re.sub(r"^(Scene\s*\d+[:\-]?\s*)", "", text, flags=re.IGNORECASE)
                        narration_blocks.append(text)
                    else:
                        text = s.strip()
                        text = re.sub(r"^(Scene\s*\d+[:\-]?\s*)", "", text, flags=re.IGNORECASE)
                        narration_blocks.append(text)

            # Clamp to requested scene count
            prompts = prompts[:num_scenes]
            narration_blocks = narration_blocks[:len(prompts)]
            
            # --- VIDEO VS IMAGE MODE ---
            if state.get('generate_video', False):
                from backend.tools.production_tools import generate_video_clips, generate_audio, stitch_video, upload_to_gcs
                from moviepy.editor import VideoFileClip
                
                # 1. Generate real moving video clips
                asset_paths = generate_video_clips(prompts)
                
                # 2. Generate Narration (TTS) using our CLEANED blocks
                audio_paths = generate_audio(narration_blocks)
                
                # 3. Stitch moving clips with narrations + Music
                video_filename = f"final_{int(time.time())}.mp4"
                local_video = stitch_video(asset_paths, audio_paths, video_filename, music_mood=state.get("music_mood"))
                
                # 4. Upload Final Video to GCS
                public_video_url = upload_to_gcs(local_video, BUCKET_NAME)
                
                # 5. Generate and Upload Thumbnail for Gallery
                thumb_path = f"thumb_{int(time.time())}.png"
                try:
                    # Capture frame at 0.5s or start
                    clip = VideoFileClip(asset_paths[0])
                    clip.save_frame(thumb_path, t=0.1)
                    public_thumb_url = upload_to_gcs(thumb_path, BUCKET_NAME)
                except Exception as thumb_err:
                    print(f"⚠️ Thumbnail generation failed: {thumb_err}")
                    public_thumb_url = public_video_url # Fallback if error
                
                # Archive locally as well
                archive_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public", "archive")
                os.makedirs(archive_dir, exist_ok=True)
                shutil.copy(local_video, os.path.join(archive_dir, os.path.basename(local_video)))
                
                return {
                    "video_url": public_video_url,
                    "image_urls": [public_thumb_url], 
                    "status": "completed",
                    "logs": state["logs"] + ["🎥 True AI cinematic video and cloud thumbnail generated!"]
                }
            else:
                from backend.tools.production_tools import generate_images, generate_audio, stitch_video, upload_to_gcs
                
                # 1. Generate Static Visual Artifacts (Imagen)
                image_paths = generate_images(prompts)
                
                # 2. Generate Narration (TTS) using our CLEANED blocks
                audio_paths = generate_audio(narration_blocks)
                
                # 3. Stitch with Ken Burns effect + Music
                video_filename = f"final_{int(time.time())}.mp4"
                local_video = stitch_video(image_paths, audio_paths, video_filename, music_mood=state.get("music_mood"))
                
                # 4. Upload all to GCS
                public_video_url = upload_to_gcs(local_video, BUCKET_NAME)
                image_gcs_urls = []
                for img in image_paths:
                    image_gcs_urls.append(upload_to_gcs(img, BUCKET_NAME))
                
                # Archive locally
                archive_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public", "archive")
                os.makedirs(archive_dir, exist_ok=True)
                for img in image_paths:
                    shutil.copy(img, os.path.join(archive_dir, os.path.basename(img)))
                shutil.copy(local_video, os.path.join(archive_dir, os.path.basename(local_video)))
                
                return {
                    "video_url": public_video_url,
                    "image_urls": image_gcs_urls,
                    "status": "completed",
                    "logs": state["logs"] + ["✅ Static Ghibli gallery and video hosted in Cloud!"]
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
