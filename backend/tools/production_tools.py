import os
import time
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
    fallback_models = [
        "imagen-3.0-generate-001",
        "imagen-3.0-fast-generate-001",
        "imagegeneration@006",
        "imagegeneration@005",
        "pollinations"
    ]
    
    print(f"🎨 Painting scene {i+1}...")
    path = f"scene_{session_id}_{i}.png"
    
    for model_id in fallback_models:
        try:
            if model_id == "pollinations":
                import requests
                from urllib.parse import quote
                prompt_encoded = quote(f"Studio Ghibli style, soft watercolor aesthetic, high quality animation still: {prompt}")
                url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1280&height=720&nologo=true"
                response = requests.get(url)
                if response.status_code == 200:
                    with open(path, 'wb') as f:
                        f.write(response.content)
                    return path
                else:
                    raise Exception(f"Pollinations returned status {response.status_code}")
            
            model = ImageGenerationModel.from_pretrained(model_id)
            response = model.generate_images(
                prompt=f"Studio Ghibli style, soft watercolor aesthetic, high quality: {prompt}",
                number_of_images=1,
                language="en",
                aspect_ratio="16:9"
            )
            
            images = list(response.images) if hasattr(response, 'images') else list(response)
            if not images:
                raise IndexError(f"Model {model_id} returned empty response.")
                
            images[0].save(location=path, include_generation_parameters=False)
            return path
            
        except Exception as e:
            err_str = str(e)
            if any(x in err_str for x in ["429", "Quota", "range", "empty", "400", "404", "life", "pollinations"]):
                print(f"⚠️ {model_id} failed for scene {i+1}. Falling back...")
                continue
            else:
                raise e
                
    raise Exception(f"All models failed for scene {i+1}")

def generate_images(prompts: List[str]) -> List[str]:
    """
    Generates images using Google Imagen via Vertex AI in parallel.
    """
    vertexai.init(project="ghibli-studio-1775332583", location="us-central1")
    session_id = str(int(time.time()))
    
    # Process up to 5 scenes in parallel to stay within reasonable quota limits
    with ThreadPoolExecutor(max_workers=5) as executor:
        worker = partial(_generate_single_image, session_id=session_id)
        # We need to maintain order, so we use executor.map or just a list of futures
        image_paths = list(executor.map(lambda x: worker(x[1], x[0]), enumerate(prompts)))
    
    return image_paths

def generate_video_clips(prompts: List[str]) -> List[str]:
    """
    Generates moving video clips using Google Veo on Vertex AI.
    """
    client = genai.Client(vertexai=True, project="ghibli-studio-1775332583", location="us-central1")
    session_id = str(int(time.time()))
    video_paths = []
    
    for i, prompt in enumerate(prompts):
        print(f"🎬 Creating cinematic scene {i+1} with Veo...")
        try:
            # Start asynchronous video generation
            operation = client.models.generate_videos(
                model="veo-3.1-generate-001",
                prompt=f"Studio Ghibli style animation still, soft watercolor aesthetic, cinematic movement: {prompt}",
                config=types.GenerateVideosConfig(
                    aspect_ratio="16:9",
                )
            )
            
            # Poll for completion (video takes about 60-120 seconds)
            while not operation.done:
                time.sleep(10)
                # Correct SDK method for polling
                operation = client.operations.get(operation)
            
            # Download the result from GCS to local tmp
            path = f"scene_{session_id}_{i}.mp4"
            
            # Check for Cloud Storage URI or Direct Bytes
            source = operation.response.generated_videos[0]
            uri = None
            if hasattr(source, 'video'):
                if hasattr(source.video, 'uri') and source.video.uri:
                    uri = source.video.uri
                elif hasattr(source.video, 'video_bytes') and source.video.video_bytes:
                    print("💾 Extracting video bytes directly from response...")
                    with open(path, 'wb') as f:
                        f.write(source.video.video_bytes)
                    video_paths.append(path)
                    continue
            
            if not uri and hasattr(source, 'uri'):
                uri = source.uri
                
            if uri:
                print(f"📥 Downloading video from {uri}...")
                bucket_name = uri.split("/")[2]
                object_name = "/".join(uri.split("/")[3:])
                storage_client = storage.Client()
                bucket = storage_client.bucket(bucket_name)
                blob = bucket.blob(object_name)
                blob.download_to_filename(path)
                video_paths.append(path)
            else:
                raise Exception("Produced video data not found in Veo response.")
            
        except Exception as e:
            print(f"⚠️ Veo failed for scene {i+1}: {e}. Falling back to image-to-video...")
            # If video fails, generate an image and we'll use Ken Burns later
            img_path = _generate_single_image(prompt, i, session_id)
            video_paths.append(img_path)
            
    return video_paths

def _generate_single_audio(scene: str, i: int, session_id: str) -> str:
    """Helper for parallel audio synthesis."""
    from google.cloud import texttospeech
    client = texttospeech.TextToSpeechClient()
    narration = scene.split("Narration:")[-1].strip() if "Narration:" in scene else scene
    input_text = texttospeech.SynthesisInput(text=narration)
    voice = texttospeech.VoiceSelectionParams(language_code="en-US", name="en-US-Neural2-F")
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    
    print(f"🎙️ Synthesizing narration for scene {i+1}...")
    response = client.synthesize_speech(input=input_text, voice=voice, audio_config=audio_config)
    
    path = f"audio_{session_id}_{i}.mp3"
    with open(path, "wb") as out:
        out.write(response.audio_content)
    return path

def generate_audio(script_scenes: List[str]) -> List[str]:
    """
    Converts script narration to audio using Google Cloud TTS in parallel.
    """
    session_id = str(int(time.time()))
    with ThreadPoolExecutor(max_workers=5) as executor:
        worker = partial(_generate_single_audio, session_id=session_id)
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
    for i, (asset_p, audio_p) in enumerate(zip(asset_paths, audio_paths)):
        audio_clip = AudioFileClip(audio_p)
        
        if asset_p.endswith(".mp4"):
            video_clip = VideoFileClip(asset_p)
            if video_clip.duration < audio_clip.duration:
                video_clip = video_clip.loop(duration=audio_clip.duration)
            else:
                video_clip = video_clip.set_duration(audio_clip.duration)
            video_clip = video_clip.set_audio(audio_clip)
        else:
            img_clip = ImageClip(asset_p).set_duration(audio_clip.duration)
            img_clip = make_kenburns(img_clip, zoom_factor=0.12)
            img_clip = img_clip.set_audio(audio_clip)
            video_clip = img_clip

        video_clip = video_clip.crossfadein(0.8)
        clips.append(video_clip)
        
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
    blob.make_public()
    return blob.public_url
