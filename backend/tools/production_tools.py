import os
import time
import requests
import json
import re
from typing import List
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
from google.cloud import texttospeech
from google.cloud import storage
from moviepy.editor import ImageClip, AudioFileClip, VideoFileClip, concatenate_videoclips
from google import genai
from google.genai import types

def _generate_single_image(prompt: str, i: int, session_id: str) -> str:
    """Helper for parallel image generation."""
    import os
    import vertexai
    vertexai.init(project=os.getenv("VERTEX_PROJECT_ID", "ghibli-studio-prod"), location="us-central1")
    # Use only the production-grade Imagen 3 model if needed as a base
    model_id = "imagen-3.0-generate-001"
    
    print(f"🎨 Painting scene {i+1}...")
    path = f"scene_{session_id}_{i}.png"
    
    for _ in range(1): # Try once with production model
        try:
            client = genai.Client(vertexai=True, project=os.getenv("VERTEX_PROJECT_ID", "ghibli-studio-prod"), location="us-central1")
            response = client.models.generate_images(
                model=model_id,
                prompt=f"Studio Ghibli style, soft watercolor aesthetic, high quality: {prompt}",
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="16:9"
                )
            )
            
            if not response.generated_images:
                raise IndexError(f"Model {model_id} returned empty response.")
                
            with open(path, 'wb') as f:
                f.write(response.generated_images[0].image.image_bytes)
            return path
            
        except Exception as e:
            print(f"❌ Imagen production error for scene {i+1}: {str(e)}")
            raise e

def generate_images(prompts: List[str]) -> List[str]:
    """
    Generates images using Google Imagen via Vertex AI in parallel.
    """
    vertexai.init(project=os.getenv("VERTEX_PROJECT_ID", "ghibli-studio-prod"), location="us-central1")
    session_id = str(int(time.time()))
    
    # Process up to 5 scenes in parallel to stay within reasonable quota limits
    with ThreadPoolExecutor(max_workers=5) as executor:
        worker = partial(_generate_single_image, session_id=session_id)
        # We need to maintain order, so we use executor.map or just a list of futures
        image_paths = list(executor.map(lambda x: worker(x[1], x[0]), enumerate(prompts)))
    
    return image_paths

def generate_video_clips(prompts: List[str], style: str = "ghibli") -> List[str]:
    """
    Generates moving video clips using Google Veo on Vertex AI.
    """
    from backend.tools.style_manager import get_style_data
    style_dna = get_style_data(style)
    
    client = genai.Client(vertexai=True, project=os.getenv("VERTEX_PROJECT_ID", "ghibli-studio-prod"), location="us-central1")
    session_id = str(int(time.time()))
    video_paths = []
    
    for i, prompt in enumerate(prompts):
        print(f"🎬 Creating {style_dna['name']} scene {i+1} with Veo...")
        try:
            # Construct the cinematic prompt based on the universe DNA
            veo_prompt = f"{style_dna['visual_rules']}, cinematic movement, high-fidelity: {prompt}"
            
            # Start asynchronous video generation
            operation = client.models.generate_videos(
                model="veo-3.1-generate-001",
                prompt=veo_prompt,
                config=types.GenerateVideosConfig(
                    aspect_ratio="16:9",
                )
            )
            
            # Poll for completion (video takes about 60-120 seconds)
            max_retries = 36 # 6 minutes total (Veo 3.1 can be slow for high-fidelity)
            retries = 0
            
            # Get the operation name safely
            if isinstance(operation, str):
                operation_id = operation
            elif hasattr(operation, 'name'):
                operation_id = operation.name
            else:
                operation_id = str(operation)
            
            print(f"  ◈ Tracking animation with ID: {operation_id}")
            
            while retries < max_retries:
                # Refresh the operation status using the object itself
                operation = client.operations.get(operation)
                
                if operation.done:
                    print(f"  ◈ Scene {i+1} animation FINISHED.")
                    break
                
                retries += 1
                print(f"  ◈ Scene {i+1} animation in progress (Wait pulse {retries})...")
                time.sleep(10)

            if not operation.done:
                raise TimeoutError(f"Veo timed out after 3 minutes for scene {i+1}")
            
            # Use local path for final assembly
            path = f"scene_{session_id}_{i}.mp4"
            
            # Check for Errors first
            if operation.error:
                raise Exception(f"Veo Error: {operation.error.message}")

            # Extract video (Aggressive Scavenging)
            uri = None
            video_bytes = None
            
            if operation.response:
                # 1. Check generated_videos list
                if hasattr(operation.response, 'generated_videos') and operation.response.generated_videos:
                    source = operation.response.generated_videos[0]
                    # Check for video.uri or video.data
                    if hasattr(source, 'video'):
                        uri = getattr(source.video, 'uri', None)
                        video_bytes = getattr(source.video, 'data', None)
                    # Check for direct uri/data
                    if not uri: uri = getattr(source, 'uri', None)
                    if not video_bytes: video_bytes = getattr(source, 'data', None)
                
                # 2. Check for direct video object in response
                elif hasattr(operation.response, 'video'):
                    uri = getattr(operation.response.video, 'uri', None)
                    video_bytes = getattr(operation.response.video, 'data', None)

            if video_bytes:
                print(f"📥 Saving cinematic scene from inlined data ({len(video_bytes)} bytes)...")
                with open(path, 'wb') as f:
                    f.write(video_bytes)
                video_paths.append(path)
            elif uri:
                print(f"📥 Downloading cinematic scene from {uri}...")
                parts = uri.replace("gs://", "").split("/")
                bucket_name = parts[0]
                object_name = "/".join(parts[1:])
                storage_client = storage.Client()
                bucket = storage_client.bucket(bucket_name)
                blob = bucket.blob(object_name)
                blob.download_to_filename(path)
                video_paths.append(path)
            else:
                # DEBUG: If we still can't find it, print the whole response structure
                print(f"❌ DEBUG: Operation Response Structure: {operation.response}")
                raise Exception("Production response missing video URI or data. This may be due to a safety block or an unsupported response format.")
            
        except Exception as e:
            print(f"❌ Veo production error for scene {i+1}: {str(e)}")
            raise e
            
    return video_paths

def _generate_single_audio(scene: str, i: int, session_id: str, style: str = "ghibli") -> str:
    """Helper for parallel human-like audio synthesis."""
    from google.cloud import texttospeech
    client = texttospeech.TextToSpeechClient()
    
    # Human Touch Mapping
    VOICE_REGISTRY = {
        "ghibli": "en-US-Studio-O",
        "shinkai": "en-US-Studio-O",
        "disney": "en-US-Studio-Q",
        "cyberpunk": "en-US-Journey-F",
        "spiderverse": "en-US-Journey-F"
    }
    
    voice_name = VOICE_REGISTRY.get(style, "en-US-Studio-O")
    
    # CLEANING: Remove any remaining AI markers (Scene 1, Narration: etc.)
    narration = scene.split("Narration:")[-1].strip() if "Narration:" in scene else scene
    narration = re.sub(r'Scene\s+\d+[:\-]?\s*', '', narration, flags=re.IGNORECASE)
    
    input_text = texttospeech.SynthesisInput(text=narration)
    
    # Use STUDIO or JOURNEY for human touch
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", 
        name=voice_name
    )
    
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        pitch=0.0,
        speaking_rate=0.95 # Slightly slower for better human cadence
    )
    
    print(f"🎙️ Synthesizing human-touch narration for scene {i+1} using {voice_name}...")
    response = client.synthesize_speech(input=input_text, voice=voice, audio_config=audio_config)
    
    path = f"audio_{session_id}_{i}.mp3"
    with open(path, "wb") as out:
        out.write(response.audio_content)
    return path

def generate_audio(script_scenes: List[str], style: str = "ghibli") -> List[str]:
    """
    Converts script narration to audio using Studio-grade TTS in parallel.
    """
    session_id = str(int(time.time()))
    with ThreadPoolExecutor(max_workers=5) as executor:
        worker = partial(_generate_single_audio, session_id=session_id, style=style)
        audio_paths = list(executor.map(lambda x: worker(x[1], x[0]), enumerate(script_scenes)))
    
    return audio_paths

# --- MUSIC MOOD HUB ---
# --- MUSIC MOOD HUB (Verified 2024-2026) ---
MOOD_LIBRARY = {
    "whimsical_adventure": "https://cdn.pixabay.com/audio/2024/08/02/audio_fb4d5edf55.mp3", # Ghibli style (2)
    "nostalgic_memory": "https://cdn.pixabay.com/audio/2026/01/18/audio_1ea436c9ad.mp3", # The Wind Awakening
    "mysterious_forest": "https://cdn.pixabay.com/audio/2025/11/26/audio_b1c3dff2f2.mp3", # Mysterious Mystical
    "melancholy_sorrow": "https://cdn.pixabay.com/audio/2021/12/07/audio_58bf641d31.mp3", # Melancholy (Tomomi)
    "triumphant_heroic": "https://cdn.pixabay.com/audio/2025/03/31/audio_e4e008ac7b.mp3", # Triumphant Fanfare
    "peaceful_watercolor": "https://cdn.pixabay.com/audio/2025/05/05/audio_129b0732f2.mp3", # Days for You
    "magical_wonder": "https://cdn.pixabay.com/audio/2025/08/13/audio_f6b46af9c5.mp3", # Magical Storytime
    "spooky_shadows": "https://cdn.pixabay.com/audio/2025/11/16/audio_dfc469e098.mp3"  # Spooky
}

def download_bgm(mood: str) -> str:
    """Downloads the BGM for the given mood to /tmp using Studio Pass (headers)."""
    import requests
    import tempfile
    url = MOOD_LIBRARY.get(mood, MOOD_LIBRARY["peaceful_watercolor"])
    local_path = os.path.join(tempfile.gettempdir(), f"bgm_{mood}.mp3")
    
    # Studio Pass: Browser-like headers to avoid 403s
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "audio/mpeg, */*",
        "Referer": "https://pixabay.com/"
    }
    
    if not os.path.exists(local_path) or os.path.getsize(local_path) < 1000:
        print(f"🎵 Auditioning Theme: {mood}...")
        try:
            r = requests.get(url, stream=True, timeout=15, headers=headers)
            r.raise_for_status()
            with open(local_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk: f.write(chunk)
            print(f"✅ Theme Secured: {mood} ({os.path.getsize(local_path)} bytes)")
        except Exception as e:
            print(f"⚠️ Audition failed for {mood}: {e}")
            return ""
            
    return local_path

def stitch_video(asset_paths: List[str], audio_paths: List[str], output_filename: str = "final_video.mp4", music_mood: str = None):
    """
    Stitches local assets and audio into a final MP4 with background music.
    """
    from PIL import Image
    import numpy as np
    
    def make_kenburns(clip, zoom_factor=0.15):
        w, h = clip.size
        resample_filter = getattr(Image, 'Resampling', getattr(Image, 'LANCZOS', None))
        resample_val = resample_filter.LANCZOS if hasattr(resample_filter, 'LANCZOS') else Image.LANCZOS
        
        def effect(get_frame, t):
            img = Image.fromarray(get_frame(t))
            z = 1.0 + zoom_factor * (t / clip.duration)
            new_w, new_h = w / z, h / z
            left = (w - new_w) / 2
            top = (h - new_h) / 2
            right = left + new_w
            bottom = top + new_h
            cropped = img.crop((left, top, right, bottom))
            resized = cropped.resize((w, h), resample_val)
            return np.array(resized)
            
        return clip.fl(effect)

    clips = []
    # Use asset_paths as the master list so we don't skip scenes if audio is missing
    for i, asset_p in enumerate(asset_paths):
        audio_p = audio_paths[i] if i < len(audio_paths) else None
        if asset_p.endswith(".mp4"):
            video_clip = VideoFileClip(asset_p)
            # Use native audio if present
            if video_clip.audio:
                audio_clip = video_clip.audio
                duration = video_clip.duration
            elif audio_p and os.path.exists(audio_p):
                audio_clip = AudioFileClip(audio_p)
                duration = audio_clip.duration
            else:
                audio_clip = None
                duration = 5.0
            
            if video_clip.duration < duration:
                video_clip = video_clip.loop(duration=duration)
            else:
                video_clip = video_clip.set_duration(duration)
            if audio_clip:
                video_clip = video_clip.set_audio(audio_clip)
        else:
            img_clip = ImageClip(asset_p).set_duration(duration)
            img_clip = make_kenburns(img_clip, zoom_factor=0.12)
            if audio_clip:
                img_clip = img_clip.set_audio(audio_clip)
            video_clip = img_clip

        video_clip = video_clip.crossfadein(0.8)
        clips.append(video_clip)
    
    if not clips:
        raise ValueError("Cinematic sequence is empty. No assets found to stitch.")

    final_clip = concatenate_videoclips(clips, method="compose")
    
    # --- BACKGROUND MUSIC MIXING ---
    if music_mood:
        try:
            bgm_path = download_bgm(music_mood)
            if bgm_path and os.path.exists(bgm_path) and os.path.getsize(bgm_path) > 1000:
                bgm_clip = AudioFileClip(bgm_path).volumex(0.25)
                
                # Loop bgm if shorter than video
                if bgm_clip.duration < final_clip.duration:
                    bgm_clip = bgm_clip.loop(duration=final_clip.duration)
                else:
                    bgm_clip = bgm_clip.set_duration(final_clip.duration)
                
                # Fade out BGM at the end
                bgm_clip = bgm_clip.audio_fadeout(2)
                
                # Composite Audio
                from moviepy.audio.AudioClip import CompositeAudioClip
                if final_clip.audio:
                    new_audio = CompositeAudioClip([final_clip.audio, bgm_clip])
                    final_clip = final_clip.set_audio(new_audio)
                    print(f"🎼 Music Layered: {music_mood} (Verified Output)")
            else:
                print(f"⚠️ Music Layering Skipped: BGM file missing or empty for {music_mood}")
        except Exception as e:
            print(f"⚠️ Music mixing failed: {e}")

    final_clip.write_videofile(output_filename, fps=24, codec="libx264", audio_codec="aac")
    return output_filename

def upload_to_gcs(local_path: str, bucket_name: str, destination_blob_name: str = None):
    """Uploads a file to GCS. Uses basename if destination_blob_name is omitted."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    
    # If no destination name provided, use the local filename
    blob_name = destination_blob_name if destination_blob_name else os.path.basename(local_path)
    
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(local_path)
    # With uniform bucket-level access, objects don't use ACLs
    # The URL pattern for public GCS files is:
    return f"https://storage.googleapis.com/{bucket_name}/{blob_name}"
