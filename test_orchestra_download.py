import os
import sys
import tempfile

# Add project root to path
sys.path.append(os.path.dirname(__file__))

from backend.tools.production_tools import MOOD_LIBRARY, download_bgm

def verify_orchestra():
    print("🎻 --- STARTING GHIBLI ORCHESTRA SOUND CHECK --- 🎻")
    success_count = 0
    total = len(MOOD_LIBRARY)
    
    for mood, url in MOOD_LIBRARY.items():
        print(f"\n🎼 Auditioning Mood: {mood}")
        print(f"🔗 URL: {url}")
        
        # Clear existing file if any for a clean test
        target_path = os.path.join(tempfile.gettempdir(), f"bgm_{mood}.mp3")
        if os.path.exists(target_path):
            os.remove(target_path)
            
        path = download_bgm(mood)
        
        if path and os.path.exists(path) and os.path.getsize(path) > 5000:
            size_kb = os.path.getsize(path) // 1024
            print(f"✅ SUCCESS: {mood} secured! ({size_kb} KB)")
            success_count += 1
        else:
            print(f"❌ FAILURE: {mood} is silent.")
            
    print(f"\n📊 Sound Check Complete: {success_count}/{total} themes active!")
    
    if success_count == total:
        print("🎭 THE ORCHESTRA IS READY! 🎭")
        return True
    else:
        print("☢️ THE STUDIO IS SILENT. FIX REQUIRED. ☢️")
        return False

if __name__ == "__main__":
    verify_orchestra()
