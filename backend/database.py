import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def save_generation(data: dict):
    """
    Saves a generation record to Supabase.
    Table: generations
    Fields: topic, concept, video_url, image_urls, metadata, source
    """
    if not supabase:
        print("⚠️ Supabase not configured. Skipping save.")
        return None
    
    try:
        response = supabase.table("generations").insert(data).execute()
        return response.data
    except Exception as e:
        print(f"❌ Error saving to Supabase: {e}")
        return None

def get_generations(limit: int = 20):
    """
    Fetches recent generations from Supabase.
    """
    if not supabase:
        print("⚠️ Supabase not configured. Returning empty list.")
        return []
        
    try:
        response = supabase.table("generations") \
            .select("*") \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()
        return response.data
    except Exception as e:
        print(f"❌ Error fetching from Supabase: {e}")
        return []
