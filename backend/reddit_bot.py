import os
import time
import json
import asyncio
from dotenv import load_dotenv

# Ensure we have access to the backend environment variables
load_dotenv()

# Optional: Install praw via `pip install praw` before running
try:
    import praw
except ImportError:
    print("⚠️ Please run: pip install praw")
    exit(1)

from backend.orchestrator import create_orchestrator
from backend.state import GraphState

def fetch_top_reddit_prompts(subreddit_name: str = "WritingPrompts", limit: int = 3):
    """
    Connects to Reddit and fetches the top X posts from a specific subreddit today.
    Requires REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, and REDDIT_USER_AGENT in your .env
    """
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT", "GhibliBot/1.0 by AutoFactory")

    if not client_id or not client_secret:
        print("⚠️ Missing REDDIT_CLIENT_ID or REDDIT_CLIENT_SECRET in .env.")
        print("For now, using fallback test prompts...")
        return [
            "A traveler discovers a secret train hidden in the clouds.",
            "The last clockmaker in a city where time has forgotten to move forward.",
            "A forgotten god wakes up in a modern junk yard."
        ]
        
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent
    )

    print(f"📡 Fetching top {limit} prompts from r/{subreddit_name}...")
    prompts = []
    subreddit = reddit.subreddit(subreddit_name)
    
    # We fetch top posts of the day, filtering out mod posts
    for submission in subreddit.top(time_filter="day", limit=limit + 5):
        if not submission.stickied and len(submission.title) > 15:
            # Clean up the format (e.g. removing [WP] tags from WritingPrompts)
            clean_title = submission.title.replace("[WP]", "").replace("[RF]", "").strip()
            prompts.append(clean_title)
            if len(prompts) >= limit:
                break
                
    return prompts

async def generate_video(prompt: str) -> str:
    """
    Feeds the prompt directly into our local LangGraph pipeline safely, 
    bypassing the web server entirely.
    """
    print(f"\n🎬 Starting local pipeline for: '{prompt}'")
    orchestrator = create_orchestrator()
    initial_state = {
        "topic": prompt,
        "num_scenes": 5,
        "generate_video": True,
        "concept": "", "script": "", "visuals": "", "metadata": "",
        "image_urls": [], "audio_urls": [], "video_url": "", 
        "logs": [], "messages": [], "status": "pending"
    }
    
    final_video_url = None
    stream_iter = orchestrator.astream(initial_state)
    
    # Iterate through the pipeline nodes
    async for output in stream_iter:
        for node_name, state_update in output.items():
            if "logs" in state_update:
                for log in state_update["logs"]:
                    print(f"  ➜ {log}")
            
            if node_name == "production" and "video_url" in state_update:
                final_video_url = state_update["video_url"]

    if final_video_url and final_video_url != "ERROR":
        print(f"\n✨ Video Successfully Rendered!")
        print(f"🔗 View it here: {final_video_url}")
        return final_video_url
    else:
        print(f"\n❌ Pipeline failed. Check logs.")
        return None

async def main():
    print("🤖 Booting Reddit -> YouTube Automation Script...")
    
    # 1. Scrape Reddit
    prompts = fetch_top_reddit_prompts("WritingPrompts", limit=2)
    
    # 2. Process each prompt
    generated_videos = []
    for prompt in prompts:
        video_url = await generate_video(prompt)
        if video_url:
            generated_videos.append(video_url)
            
        print("\n⏳ Waiting 5 seconds before starting next video...")
        time.sleep(5)
        
    print("\n✅ NIGHTLY BATCH COMPLETE.")
    print(f"Generated {len(generated_videos)} videos tonight.")
    for url in generated_videos:
        print(f"- {url}")

if __name__ == "__main__":
    asyncio.run(main())
