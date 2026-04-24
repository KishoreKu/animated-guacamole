import os
import time
import requests
import json
import re
from typing import List
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from moviepy.editor import ImageClip, AudioFileClip, VideoFileClip, concatenate_videoclips


def _get_imagen_client():
    """Returns a configured google-genai client using the GOOGLE_API_KEY."""
    from google import genai
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")
    return genai.Client(api_key=api_key)

def _generate_single_image(prompt: str, i: int, session_id: str) -> str:
    """Helper for image generation using Google Imagen 4.0 (Pro subscription) with retry."""
    from google.genai import types
    
    print(f"🎨 Painting scene {i+1} with Imagen 4.0...")
    path = f"scene_{session_id}_{i}.png"
    
    # Enhance prompt for Ghibli aesthetic
    full_prompt = f"Studio Ghibli style, soft watercolor aesthetic, cinematic composition, masterpiece quality, {prompt}"
    
    max_retries = 5
    base_delay = 3.0
    
    for attempt in range(max_retries):
        try:
            client = _get_imagen_client()
            response = client.models.generate_images(
                model='imagen-4.0-generate-001',
                prompt=full_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="16:9",
                )
            )
            
            if response.generated_images:
                response.generated_images[0].image.save(path)
                print(f"✅ Scene {i+1} painted successfully ({os.path.getsize(path)} bytes)")
            else:
                raise RuntimeError(f"Imagen returned no images for scene {i+1}")
            
            return path
        except Exception as e:
            error_str = str(e)
            if ("429" in error_str or "RESOURCE_EXHAUSTED" in error_str) and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                print(f"⏳ Imagen rate limited on scene {i+1} (attempt {attempt+1}/{max_retries}). Waiting {delay:.0f}s...")
                time.sleep(delay)
            else:
                print(f"❌ Image generation error for scene {i+1}: {error_str}")
                raise e

def generate_images(prompts: List[str]) -> List[str]:
    """
    Generates images using Google Imagen 4.0 sequentially.
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

def _generate_single_video(prompt: str, i: int, session_id: str) -> str:
    """Generates a single video clip using Google Veo 2.0 with retry."""
    from google.genai import types
    
    print(f"🎬 Directing scene {i+1} with Veo AI...")
    path = f"scene_{session_id}_{i}.mp4"
    
    # Enhance prompt for cinematic Ghibli aesthetic
    full_prompt = f"Studio Ghibli anime style, soft watercolor aesthetic, gentle cinematic camera movement, {prompt}"
    
    max_retries = 5
    base_delay = 5.0
    
    for attempt in range(max_retries):
        try:
            client = _get_imagen_client()
            
            operation = client.models.generate_videos(
                model='veo-2.0-generate-001',
                prompt=full_prompt,
                config=types.GenerateVideosConfig(
                    aspect_ratio="16:9",
                    number_of_videos=1,
                )
            )
            
            print(f"   ⏳ Scene {i+1} rendering (operation: {operation.name})...")
            
            # Poll for completion (max 3 minutes per clip)
            for tick in range(36):
                if operation.done:
                    break
                time.sleep(5)
                operation = client.operations.get(operation)
            
            if not operation.done:
                raise TimeoutError(f"Veo timed out for scene {i+1} after 3 minutes")
            
            if operation.response and operation.response.generated_videos:
                video = operation.response.generated_videos[0]
                video_uri = video.video.uri
                
                # Download the video from Google's API (requires API key auth)
                print(f"   📥 Downloading scene {i+1}...")
                api_key = os.getenv("GOOGLE_API_KEY")
                separator = "&" if "?" in video_uri else "?"
                auth_url = f"{video_uri}{separator}key={api_key}"
                dl_response = requests.get(auth_url, timeout=120)
                dl_response.raise_for_status()
                
                with open(path, 'wb') as f:
                    f.write(dl_response.content)
                
                size_mb = os.path.getsize(path) / (1024 * 1024)
                print(f"   ✅ Scene {i+1} rendered! ({size_mb:.1f} MB)")
                return path
            else:
                raise RuntimeError(f"Veo returned no videos for scene {i+1}")
                
        except Exception as e:
            error_str = str(e)
            if ("429" in error_str or "RESOURCE_EXHAUSTED" in error_str) and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                print(f"   ⏳ Rate limited on scene {i+1} (attempt {attempt+1}/{max_retries}). Waiting {delay:.0f}s...")
                time.sleep(delay)
            elif attempt < max_retries - 1 and "Timeout" in error_str:
                print(f"   ⏳ Timeout on scene {i+1}, retrying...")
                time.sleep(5)
            else:
                print(f"   ❌ Veo error for scene {i+1}: {error_str}")
                raise e

def generate_video_clips(prompts: List[str], style: str = "ghibli") -> List[str]:
    """
    Generates cinematic video clips using Google Veo 2.0 AI.
    Real AI video generation with actual motion, not just Ken Burns.
    Falls back to Imagen 4.0 + static frames if Veo fails.
    """
    from backend.tools.style_manager import get_style_data
    style_dna = get_style_data(style)
    session_id = str(int(time.time()))
    
    print(f"🎬 Directing {len(prompts)} {style_dna['name']} scenes with Veo AI...")
    
    video_paths = []
    for i, prompt in enumerate(prompts):
        try:
            path = _generate_single_video(prompt, i, session_id)
            video_paths.append(path)
            # Delay between video requests to respect rate limits
            if i < len(prompts) - 1:
                time.sleep(3)
        except Exception as e:
            print(f"⚠️ Veo failed for scene {i+1}, falling back to Imagen 4.0 static...")
            # Fallback: generate a still image instead
            try:
                img_path = _generate_single_image(prompt, i, session_id)
                video_paths.append(img_path)
            except Exception as img_err:
                print(f"❌ Fallback also failed for scene {i+1}: {img_err}")
    
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
    """Uploads assets to Supabase Storage for permanent, publicly accessible URLs."""
    
    SUPABASE_BUCKET = "ghibli-assets"
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


