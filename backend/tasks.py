import os
import asyncio
import time
from typing import List
from backend.orchestrator import create_orchestrator
from backend.state import GraphState
from backend.database import save_generation

def fetch_top_reddit_prompts(subreddit_name: str = "WritingPrompts", limit: int = 2):
    """
    Connects to Reddit and fetches the top X posts from a specific subreddit today.
    """
    import praw
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT", "GhibliBot/1.0 by AutoFactory")

    if not client_id or not client_secret:
        print(f"⚠️ Missing REDDIT_CLIENT_ID or REDDIT_CLIENT_SECRET. Skipping {subreddit_name}.")
        return []
        
    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )

        print(f"📡 Fetching top {limit} prompts from r/{subreddit_name}...")
        prompts = []
        subreddit = reddit.subreddit(subreddit_name)
        
        for submission in subreddit.top(time_filter="day", limit=limit + 5):
            if not submission.stickied and len(submission.title) > 20:
                clean_title = submission.title.replace("[WP]", "").replace("[RF]", "").strip()
                prompts.append(clean_title)
                if len(prompts) >= limit:
                    break
                    
        return prompts
    except Exception as e:
        print(f"❌ Error fetching from r/{subreddit_name}: {e}")
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
