import os
import time
from typing import List
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
from google.cloud import texttospeech
from google.cloud import storage
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

def generate_images(prompts: List[str]) -> List[str]:
    """
    Generates images using Google Imagen via Vertex AI, with fallbacks.
    Returns a list of local paths to the generated images.
    """
    vertexai.init(project="ghibli-studio-1775332583", location="us-central1")
    
    # Ordered list of models to try if quota is zero for the newer ones
    fallback_models = [
        "imagen-3.0-generate-001",
        "imagen-3.0-fast-generate-001",
        "imagegeneration@006",
        "imagegeneration@005",
        "pollinations"
    ]
    image_paths = []
    session_id = str(int(time.time()))
    
    for i, prompt in enumerate(prompts):
        print(f"🎨 Painting scene {i+1}...")
        success = False
        
        for model_id in fallback_models:
            print(f"Trying model: {model_id}")
            try:
                path = f"scene_{session_id}_{i}.png"
                
                
                if model_id == "pollinations":
                    import requests
                    from urllib.parse import quote
                    print("⚠️ Using Pollinations.ai free fallback...")
                    # Generate a unique seed or add resolution to avoid caching identical images
                    prompt_encoded = quote(f"Studio Ghibli style, soft watercolor aesthetic, high quality animation still: {prompt}")
                    url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1280&height=720&nologo=true"
                    response = requests.get(url)
                    if response.status_code == 200:
                        with open(path, 'wb') as f:
                            f.write(response.content)
                        image_paths.append(path)
                        success = True
                        break
                    else:
                        raise Exception(f"Pollinations returned status {response.status_code}")
                
                model = ImageGenerationModel.from_pretrained(model_id)
                response = model.generate_images(
                    prompt=f"Studio Ghibli style, soft watercolor aesthetic, high quality: {prompt}",
                    number_of_images=1,
                    language="en",
                    aspect_ratio="16:9"
                )
                
                # Convert to list since some ImageGenerationResponse versions don't support len()
                images = list(response.images) if hasattr(response, 'images') else list(response)
                
                if not images or len(images) == 0:
                    raise IndexError(f"Model {model_id} returned an empty response. Likely an aspect ratio or safety block.")
                    
                images[0].save(location=path, include_generation_parameters=False)
                image_paths.append(path)
                success = True
                break
            except Exception as e:
                # Catch empty list errors, 429 quotas, 404 EOL, or 400 Bad Request (aspect ratio errors) and fall back
                err_str = str(e)
                if "429" in err_str or "Quota" in err_str or "out of range" in err_str or "empty" in err_str or "400" in err_str or "404" in err_str or "end of life" in err_str or "pollinations" in err_str.lower():
                    print(f"⚠️ {model_id} failed with: {err_str}. Falling back...")
                    continue
                else:
                    raise e
                    
        if not success:
            raise Exception("All Vertex AI Imagen models failed due to Quota Limits. Please request quota increases in GCP.")
            
        time.sleep(1) # Prevent hammering the API too fast between prompts
        
    return image_paths

def generate_audio(script_scenes: List[str]) -> List[str]:
    """
    Converts script narration to audio using Google Cloud TTS.
    Returns local paths to audio files.
    """
    client = texttospeech.TextToSpeechClient()
    audio_paths = []
    session_id = str(int(time.time()))
    
    for i, scene in enumerate(script_scenes):
        narration = scene.split("Narration:")[-1].strip() if "Narration:" in scene else scene
        input_text = texttospeech.SynthesisInput(text=narration)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Neural2-F"
        )
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        
        response = client.synthesize_speech(input=input_text, voice=voice, audio_config=audio_config)
        
        path = f"audio_{session_id}_{i}.mp3"
        with open(path, "wb") as out:
            out.write(response.audio_content)
        audio_paths.append(path)
        
    return audio_paths

def stitch_video(image_paths: List[str], audio_paths: List[str], output_filename: str = "final_video.mp4"):
    """
    Stitches local images and audio into a final MP4 with Cinematic Ken Burns Parallax effect.
    """
    from PIL import Image
    import numpy as np
    
    def make_kenburns(clip, zoom_factor=0.15):
        w, h = clip.size
        # Fallback for Pillow versions
        resample_filter = getattr(Image, 'Resampling', getattr(Image, 'LANCZOS', None))
        resample_val = resample_filter.LANCZOS if hasattr(resample_filter, 'LANCZOS') else Image.LANCZOS
        
        def effect(get_frame, t):
            img = Image.fromarray(get_frame(t))
            
            # Calculate current zoom (zooming slowly inward)
            z = 1.0 + zoom_factor * (t / clip.duration)
            
            # Calculate new cropped window
            new_w, new_h = w / z, h / z
            left = (w - new_w) / 2
            top = (h - new_h) / 2
            right = left + new_w
            bottom = top + new_h
            
            # Crop the inward box and resize it back up to normal 1080p width
            cropped = img.crop((left, top, right, bottom))
            resized = cropped.resize((w, h), resample_val)
            
            return np.array(resized)
            
        return clip.fl(effect)

    clips = []
    for i, (img_p, audio_p) in enumerate(zip(image_paths, audio_paths)):
        audio_clip = AudioFileClip(audio_p)
        img_clip = ImageClip(img_p).set_duration(audio_clip.duration)
        
        print(f"Applying Cinematic Ken Burns to Scene {i+1}...")
        img_clip = make_kenburns(img_clip, zoom_factor=0.12)
        
        img_clip = img_clip.set_audio(audio_clip)
        img_clip = img_clip.crossfadein(0.8)
        clips.append(img_clip)
        
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
