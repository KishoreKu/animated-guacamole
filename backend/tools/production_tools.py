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
        "imagegeneration@005"
    ]
    
    image_paths = []
    
    for i, prompt in enumerate(prompts):
        print(f"🎨 Painting scene {i+1}...")
        success = False
        
        for model_id in fallback_models:
            print(f"Trying model: {model_id}")
            try:
                model = ImageGenerationModel.from_pretrained(model_id)
                response = model.generate_images(
                    prompt=f"Studio Ghibli style, soft watercolor aesthetic, high quality: {prompt}",
                    number_of_images=1,
                    language="en",
                    aspect_ratio="16:9"
                )
                path = f"scene_{i}.png"
                response[0].save(location=path, include_generation_parameters=False)
                image_paths.append(path)
                success = True
                break
            except Exception as e:
                if "429" in str(e) or "Quota exceeded" in str(e):
                    print(f"⚠️ {model_id} Quota exceeded. Falling back...")
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
    
    for i, scene in enumerate(script_scenes):
        narration = scene.split("Narration:")[-1].strip() if "Narration:" in scene else scene
        input_text = texttospeech.SynthesisInput(text=narration)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Neural2-F"
        )
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        
        response = client.synthesize_speech(input=input_text, voice=voice, audio_config=audio_config)
        
        path = f"audio_{i}.mp3"
        with open(path, "wb") as out:
            out.write(response.audio_content)
        audio_paths.append(path)
        
    return audio_paths

def stitch_video(image_paths: List[str], audio_paths: List[str], output_filename: str = "final_video.mp4"):
    """
    Stitches local images and audio into a final MP4.
    """
    clips = []
    for img_p, audio_p in zip(image_paths, audio_paths):
        audio_clip = AudioFileClip(audio_p)
        img_clip = ImageClip(img_p).set_duration(audio_clip.duration)
        img_clip = img_clip.set_audio(audio_clip)
        img_clip = img_clip.crossfadein(0.5)
        clips.append(img_clip)
        
    final_clip = concatenate_videoclips(clips, method="compose")
    final_clip.write_videofile(output_filename, fps=24, codec="libx264")
    
    return output_filename

def upload_to_gcs(local_path: str, bucket_name: str):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(os.path.basename(local_path))
    blob.upload_from_filename(local_path)
    blob.make_public()
    return blob.public_url
