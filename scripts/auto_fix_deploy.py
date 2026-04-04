import os
import time
import subprocess
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

# Configuration
REPO_OWNER = "KishoreKu"
REPO_NAME = "animated-guacamole"
BRANCH = "main"
POLL_INTERVAL = 30 # seconds

# Initialize Gemini
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip()

def get_latest_run():
    stdout, _ = run_command(f"gh run list --branch {BRANCH} --limit 1 --json databaseId,status,conclusion")
    runs = json.loads(stdout)
    return runs[0] if runs else None

def get_run_logs(run_id):
    stdout, _ = run_command(f"gh run view {run_id} --log")
    return stdout

def apply_fix(error_logs):
    print("🤖 Analyzing failure logs with Gemini...")
    
    prompt = f"""
    The GitHub Actions deployment failed. Here are the logs:
    {error_logs[:5000]} # Limit logs for context window
    
    As an expert DevOps engineer, analyze the error and provide a Python script that I can run LOCALLY to fix the codebase. 
    The script should make the necessary file changes (e.g., using open().write() or similar).
    Return ONLY the raw Python code to perform the fix. No explanation.
    """
    
    response = llm.invoke([
        SystemMessage(content="You are an autonomous self-healing agent."),
        HumanMessage(content=prompt)
    ])
    
    fix_code = response.content.replace("```python", "").replace("```", "").strip()
    
    with open("temp_fix.py", "w") as f:
        with open("temp_fix.py", "w") as f:
            f.write(fix_code)
    
    print("🛠️ Applying fix...")
    run_command("python3 temp_fix.py")
    os.remove("temp_fix.py")
    
    print("📤 Pushing fixed code...")
    run_command("git add . && git commit -m 'Auto-fix deployment failure' && git push origin main")

def main():
    print(f"🕵️ Monitoring {REPO_NAME} deployment...")
    last_processed_run = None
    
    while True:
        run = get_latest_run()
        if not run:
            time.sleep(POLL_INTERVAL)
            continue
            
        run_id = run['databaseId']
        status = run['status']
        conclusion = run['conclusion']
        
        if run_id != last_processed_run:
            if status == "completed":
                if conclusion == "success":
                    print(f"✅ Run {run_id} succeeded!")
                    last_processed_run = run_id
                elif conclusion == "failure":
                    print(f"❌ Run {run_id} failed. Starting healing process...")
                    logs = get_run_logs(run_id)
                    apply_fix(logs)
                    last_processed_run = run_id
                else:
                    print(f"⚠️ Run {run_id} ended with {conclusion}")
                    last_processed_run = run_id
            else:
                print(f"⏳ Run {run_id} is currently {status}...")
        
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
