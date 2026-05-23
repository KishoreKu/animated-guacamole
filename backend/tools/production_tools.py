import os
import time
import requests
import json
import re
from typing import List
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from moviepy.editor import ImageClip, AudioFileClip, VideoFileClip, concatenate_videoclips




def _generate_single_image_fal(prompt: str, i: int, session_id: str) -> str:
    """Helper for image generation using fal.ai (Flux.1 Schnell) - High speed/quality."""
    import fal_client

    print(f"🎨 Painting scene {i+1} with fal.ai (Flux.1)...")
    path = f"scene_{session_id}_{i}.png"

    # Enhance prompt for Ghibli aesthetic
    full_prompt = f"Studio Ghibli style, soft watercolor aesthetic, cinematic composition, masterpiece quality, {prompt}"

    try:
        handler = fal_client.submit(
            "fal-ai/flux/schnell",
            arguments={
                "prompt": full_prompt,
                "image_size": "landscape_16_9",
                "num_inference_steps": 4,
                "enable_safety_checker": True
            }
        )
        result = handler.get()
        if result and result.get("images"):
            image_url = result["images"][0]["url"]
            print(f"   📥 Downloading scene {i+1} painting from fal.ai...")
            img_response = requests.get(image_url, timeout=60)
            img_response.raise_for_status()
            with open(path, "wb") as f:
                f.write(img_response.content)
            print(f"✅ Scene {i+1} painted successfully ({os.path.getsize(path)} bytes)")
            return path
        else:
            raise RuntimeError("fal.ai returned no images")
    except Exception as e:
        print(f"❌ fal.ai error for scene {i+1}: {e}")
        raise e

def _generate_single_image(prompt: str, i: int, session_id: str) -> str:
    """Helper for image generation using fal.ai."""
    if os.getenv("FAL_KEY"):
        return _generate_single_image_fal(prompt, i, session_id)
    raise ValueError("FAL_KEY is missing. Image generation requires fal.ai.")

def generate_images(prompts: List[str]) -> List[str]:
    """
    Generates images using fal.ai sequentially.
    Sequential with delays to respect API rate limits.
    """
    session_id = str(int(time.time()))
    image_paths = []
    
    for i, prompt in enumerate(prompts):
        path = _generate_single_image(prompt, i, session_id)
        image_paths.append(path)
        # 2s delay between requests to proactively avoid rate limits
        if i < len(prompts) - 1:
            time.sleep(2)
    
    return image_paths

def _generate_single_video_openrouter(prompt: str, i: int, session_id: str, video_model: str) -> str:
    """Helper for cinematic video generation using OpenRouter."""
    print(f"🎬 Directing scene {i+1} with {video_model} via OpenRouter...")
    path = f"scene_{session_id}_{i}.mp4"
    
    # ENHANCED MOTION PROMPT: Emphasizing movement and storytelling
    full_prompt = (
        f"Studio Ghibli anime style, soft watercolor aesthetic, masterpiece quality. "
        f"CHARACTER MOTION: The characters are actively moving, walking, or interacting. "
        f"CINEMATOGRAPHY: Dynamic camera movement, slow zoom or pan. "
        f"SCENE: {prompt}"
    )
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is missing. Video generation requires OpenRouter.")
        
    try:
        # Step 1: Submit the video generation job
        submit_url = "https://openrouter.ai/api/v1/videos"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": video_model,
            "prompt": full_prompt,
            "aspect_ratio": "16:9"
        }
        
        response = requests.post(submit_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        job_data = response.json()
        
        polling_url = job_data.get("polling_url")
        if not polling_url:
            raise RuntimeError(f"OpenRouter did not return a polling URL: {job_data}")
            
        print(f"   ⏳ Job submitted. Polling for completion of scene {i+1}...")
        
        # Step 2: Poll until completed
        max_attempts = 120 # Wait up to 20 minutes (120 * 10s)
        video_url = None
        for attempt in range(max_attempts):
            time.sleep(10)
            poll_resp = requests.get(polling_url, headers={"Authorization": f"Bearer {api_key}"})
            poll_resp.raise_for_status()
            status_data = poll_resp.json()
            
            status = status_data.get("status")
            if status == "completed":
                # OpenRouter returns the video URL in a list called 'unsigned_urls'
                if "unsigned_urls" in status_data and len(status_data["unsigned_urls"]) > 0:
                    video_url = status_data["unsigned_urls"][0]
                else:
                    video_url = status_data.get("url") or status_data.get("content_url") or status_data.get("video_url")
                    if "video" in status_data and isinstance(status_data["video"], dict):
                        video_url = video_url or status_data["video"].get("url")
                break
            elif status in ["failed", "error"]:
                raise RuntimeError(f"OpenRouter video generation failed: {status_data}")
            
            if attempt % 6 == 0:
                print(f"   ⏳ Still rendering scene {i+1} (elapsed: {attempt*10}s)...")
                
        if not video_url:
            raise RuntimeError("Timed out waiting for OpenRouter video generation.")
            
        print(f"   📥 Downloading scene {i+1} video from OpenRouter...")
        v_response = requests.get(video_url, timeout=180)
        v_response.raise_for_status()
        with open(path, "wb") as f:
            f.write(v_response.content)
        print(f"✅ Scene {i+1} video rendered! ({os.path.getsize(path)} bytes)")
        return path
    except Exception as e:
        print(f"❌ OpenRouter video error for scene {i+1}: {e}")
        raise e

def _generate_single_video(prompt: str, i: int, session_id: str, video_model: str) -> str:
    """Helper for video generation using OpenRouter."""
    if os.getenv("OPENROUTER_API_KEY"):
        return _generate_single_video_openrouter(prompt, i, session_id, video_model)
    raise ValueError("OPENROUTER_API_KEY is missing. Video generation requires OpenRouter.")

def generate_video_clips(prompts: List[str], video_model: str = "alibaba/wan-2.6", style: str = "ghibli") -> List[str]:
    """
    Generates cinematic video clips using OpenRouter in parallel.
    """
    session_id = str(int(time.time()))
    with ThreadPoolExecutor(max_workers=5) as executor:
        from functools import partial
        worker = partial(_generate_single_video, session_id=session_id, video_model=video_model)
        video_paths = list(executor.map(lambda x: worker(x[1], x[0]), enumerate(prompts)))
    
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
        audio_clip = None
        duration = 5.0 # Default duration
        
        # 1. Determine Audio and Duration
        if audio_p and os.path.exists(audio_p):
            audio_clip = AudioFileClip(audio_p)
            duration = audio_clip.duration
            
        # 2. Process Asset
        if asset_p.endswith(".mp4"):
            video_clip = VideoFileClip(asset_p)
            # If video has its own audio and we don't have a separate narration, use video duration
            if video_clip.audio and not audio_clip:
                audio_clip = video_clip.audio
                duration = video_clip.duration
            
            # Match durations
            if video_clip.duration < duration:
                video_clip = video_clip.loop(duration=duration)
            else:
                video_clip = video_clip.set_duration(duration)
            
            if audio_clip:
                video_clip = video_clip.set_audio(audio_clip)
        else:
            # Handle Static Images
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
    """Uploads assets to Supabase Storage for permanent, publicly accessible URLs."""
    
    SUPABASE_BUCKET = bucket_name # Respect the passed bucket name
    filename = destination_blob_name if destination_blob_name else os.path.basename(local_path)
    supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    
    # Determine content type
    if local_path.endswith(".mp4"):
        content_type = "video/mp4"
    elif local_path.endswith(".png"):
        content_type = "image/png"
    elif local_path.endswith(".jpg") or local_path.endswith(".jpeg"):
        content_type = "image/jpeg"
    else:
        content_type = "application/octet-stream"
    
    with open(local_path, "rb") as f:
        file_data = f.read()
    
    # Try Supabase Python SDK first
    try:
        from backend.database import supabase as sb_client
        if sb_client:
            # Fallback if the requested bucket doesn't exist
            try:
                sb_client.storage.get_bucket(SUPABASE_BUCKET)
            except:
                SUPABASE_BUCKET = "ghibli-assets"

            sb_client.storage.from_(SUPABASE_BUCKET).upload(
                path=filename,
                file=file_data,
                file_options={"content-type": content_type, "upsert": "true"}
            )
            public_url = f"{supabase_url}/storage/v1/object/public/{SUPABASE_BUCKET}/{filename}"
            print(f"✅ Uploaded to Supabase Storage: {filename} ({len(file_data) // 1024} KB)")
            return public_url
    except Exception as sdk_err:
        print(f"⚠️ SDK upload failed ({sdk_err}), trying REST fallback...")
    
    # Fallback: direct REST API upload via requests
    try:
        upload_url = f"{supabase_url}/storage/v1/object/{SUPABASE_BUCKET}/{filename}"
        headers = {
            "Authorization": f"Bearer {supabase_key}",
            "apikey": supabase_key,
            "Content-Type": content_type,
            "x-upsert": "true",
        }
        resp = requests.post(upload_url, headers=headers, data=file_data, timeout=60)
        resp.raise_for_status()
        
        public_url = f"{supabase_url}/storage/v1/object/public/{SUPABASE_BUCKET}/{filename}"
        print(f"✅ Uploaded via REST: {filename} ({len(file_data) // 1024} KB)")
        return public_url
    except Exception as e:
        print(f"❌ All upload methods failed: {e}")
        return local_path


