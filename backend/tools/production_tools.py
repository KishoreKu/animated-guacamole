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
                operation = client.operations.get_videos_operation(operation=operation)
            
            # Download the result from GCS to local tmp
            path = f"scene_{session_id}_{i}.mp4"
            # Veo returns the video bytes or URI
            content = operation.response.generated_videos[0].video_bytes
            with open(path, 'wb') as f:
                f.write(content)
            video_paths.append(path)
            
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

def stitch_video(asset_paths: List[str], audio_paths: List[str], output_filename: str = "final_video.mp4"):
    """
    Stitches local assets (images or mp4s) and audio into a final MP4.
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
            # It's a moving video from Veo
            video_clip = VideoFileClip(asset_p)
            # Match duration or loop if audio is longer
            if video_clip.duration < audio_clip.duration:
                # Loop video to match audio
                video_clip = video_clip.loop(duration=audio_clip.duration)
            else:
                video_clip = video_clip.set_duration(audio_clip.duration)
            
            video_clip = video_clip.set_audio(audio_clip)
        else:
            # It's a static image (fallback)
            img_clip = ImageClip(asset_p).set_duration(audio_clip.duration)
            print(f"Applying Cinematic Ken Burns to Scene {i+1}...")
            img_clip = make_kenburns(img_clip, zoom_factor=0.12)
            img_clip = img_clip.set_audio(audio_clip)
            video_clip = img_clip

        video_clip = video_clip.crossfadein(0.8)
        clips.append(video_clip)
        
    final_clip = concatenate_videoclips(clips, method="compose")
    final_clip.write_videofile(output_filename, fps=24, codec="libx264", audio_codec="aac")
    
    return output_filename

def upload_to_gcs(local_path: str, bucket_name: str):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(os.path.basename(local_path))
    blob.upload_from_filename(local_path)
    blob.make_public()
    return blob.public_url
