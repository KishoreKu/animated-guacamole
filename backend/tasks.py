import os
import asyncio
import time
from typing import List
from backend.orchestrator import create_orchestrator
from backend.state import GraphState
from backend.database import save_generation

def fetch_top_reddit_prompts(subreddit_name: str = "WritingPrompts", limit: int = 2):
    """
    Connects to Reddit via public RSS Feed (No API keys required!).
    """
    import requests
    import xml.etree.ElementTree as ET
    from urllib.parse import quote
    
    url = f"https://www.reddit.com/r/{subreddit_name}/top/.rss?t=day&limit={limit+5}"
    # Reddit RSS needs a unique User-Agent or it will block you
    headers = {'User-Agent': 'GhibliBot/1.0 by AutoFactory (Public RSS)'}
    
    try:
        print(f"📡 Fetching top prompts from r/{subreddit_name} (via RSS)...")
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"⚠️ RSS Feed failed for {subreddit_name} (Status: {response.status_code}).")
            return []

        # Parse the XML (RSS is an Atom feed)
        root = ET.fromstring(response.content)
        # Atom namespaces
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        prompts = []
        for entry in root.findall('atom:entry', ns):
            title = entry.find('atom:title', ns).text
            # Skip noise and short titles
            if "[WP]" in title or "[RF]" in title or len(title) > 20:
                clean_title = title.replace("[WP]", "").replace("[RF]", "").strip()
                prompts.append(clean_title)
                if len(prompts) >= limit:
                    break
        
        return prompts
    except Exception as e:
        print(f"❌ RSS Error for r/{subreddit_name}: {e}")
        return []

async def run_generation_pipeline(prompt: str, source: str = "manual", num_scenes: int = 5, generate_video: bool = True):
    """
    Runs the full LangGraph pipeline for a single prompt and saves the result to the database.
    """
    print(f"🎬 Starting generation for: '{prompt}' (Source: {source})")
    orchestrator = create_orchestrator()
    initial_state = {
        "topic": prompt,
        "num_scenes": num_scenes,
        "generate_video": generate_video,
        "concept": "", "script": "", "visuals": "", "metadata": "",
        "bgm_prompt": "",
        "image_urls": [], "audio_urls": [], "video_url": "", 
        "logs": [], "messages": [], "status": "pending"
    }
    
    try:
        # For background tasks, ainvoke is safer as it returns the full final state
        final_state = await orchestrator.ainvoke(initial_state)
    except Exception as e:
        print(f"❌ Pipeline failed for '{prompt}': {e}")
        return None

    # Save to Database
    if final_state and final_state.get("image_urls"):
        db_data = {
            "topic": prompt,
            "concept": final_state.get("concept", ""),
            "video_url": final_state.get("video_url", ""),
            "image_urls": final_state.get("image_urls", []),
            "metadata": {"title": final_state.get("metadata", ""), "tags": []},
            "script": final_state.get("script", ""),
            "visuals": final_state.get("visuals", ""),
            "bgm_prompt": final_state.get("bgm_prompt", ""),
            "source": source
        }
        save_generation(db_data)
        print(f"✅ Generation saved to database: {prompt}")
        return final_state
    
    return None

async def perform_reddit_batch():
    """
    The main cron task: Scrapes multiple subreddits and runs generations.
    """
    subreddits = ["WritingPrompts", "ShortScaryStories", "Fantasy"]
    all_prompts = []
    
    for sub in subreddits:
        prompts = fetch_top_reddit_prompts(sub, limit=1) # 1 from each to reach ~2-3 per batch
        all_prompts.extend(prompts)

    # Limit to absolute total of 2 as requested
    all_prompts = all_prompts[:2]
    
    results = []
    for prompt in all_prompts:
        res = await run_generation_pipeline(prompt, source="reddit", num_scenes=5, generate_video=True)
        results.append(res)
        await asyncio.sleep(5) # Cooldown between generations
        
    return results
