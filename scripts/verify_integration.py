import os
import asyncio
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import fal_client

# Load from backend/.env
load_dotenv('backend/.env')

async def test_openrouter():
    print("--- Testing OpenRouter ---")
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ No API Key found for OpenRouter")
        return False
    
    try:
        llm = ChatOpenAI(
            model="google/gemini-2.0-flash-001",
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.7,
        )
        response = llm.invoke([HumanMessage(content="Say 'OpenRouter is working!'")])
        print(f"✅ Response: {response.content}")
        return True
    except Exception as e:
        print(f"❌ OpenRouter Error: {e}")
        return False

async def test_fal():
    print("\n--- Testing fal.ai ---")
    if not os.getenv("FAL_KEY"):
        print("❌ No FAL_KEY found")
        return False
    
    try:
        # We'll just try a very fast small generation
        handler = await fal_client.submit_async(
            "fal-ai/flux/schnell",
            arguments={
                "prompt": "A tiny Studio Ghibli soot sprite, watercolor style",
                "image_size": "square",
                "num_inference_steps": 4
            }
        )
        result = await handler.get_obj()
        if result.get("images"):
            print(f"✅ fal.ai Success! Image URL: {result['images'][0]['url']}")
            return True
        else:
            print("❌ fal.ai returned no images")
            return False
    except Exception as e:
        print(f"❌ fal.ai Error: {e}")
        return False

async def main():
    or_ok = await test_openrouter()
    fal_ok = await test_fal()
    
    if or_ok and fal_ok:
        print("\n✨ ALL SYSTEMS GO! You are ready to generate Ghibli magic.")
    else:
        print("\n⚠️ Some systems failed. Check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())
