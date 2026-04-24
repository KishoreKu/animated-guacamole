import os
import time
from typing import List, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from backend.state import GraphState
from dotenv import load_dotenv

load_dotenv()

class RetryLLMWrapper:
    """Wraps a LangChain LLM with exponential backoff retry for 429 errors."""
    
    def __init__(self, llm, max_retries: int = 5, base_delay: float = 2.0):
        self._llm = llm
        self.max_retries = max_retries
        self.base_delay = base_delay
    
    def invoke(self, *args, **kwargs):
        last_error = None
        for attempt in range(self.max_retries):
            try:
                return self._llm.invoke(*args, **kwargs)
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    delay = self.base_delay * (2 ** attempt)
                    print(f"⏳ Rate limited (attempt {attempt+1}/{self.max_retries}). Waiting {delay:.0f}s...")
                    time.sleep(delay)
                    last_error = e
                else:
                    raise e
        raise last_error
    
    def bind_tools(self, tools):
        self._llm = self._llm.bind_tools(tools)
        return self
    
    def __getattr__(self, name):
        return getattr(self._llm, name)

class BaseAgent:
    def __init__(self, name: str, persona: str, tools: List[Any] = None, model_name: str = "gemini-2.0-flash"):
        self.name = name
        self.persona = persona
        # Configure for Google Gemini with retry logic for rate limits
        try:
            raw_llm = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=os.getenv("GOOGLE_API_KEY"),
                temperature=0.7,
            )
            self.llm = RetryLLMWrapper(raw_llm)
        except Exception:
            # Fallback for limited environments or test runs
            self.llm = None
        if tools:
            self.llm = self.llm.bind_tools(tools)
        self.tools = tools

    def execute(self, state: GraphState) -> GraphState:
        # To be implemented by subclasses
        pass

