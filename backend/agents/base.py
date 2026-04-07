import os
from typing import List, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from backend.state import GraphState
from dotenv import load_dotenv

load_dotenv()

class BaseAgent:
    def __init__(self, name: str, persona: str, tools: List[Any] = None, model_name: str = "gemini-2.0-flash"):
        self.name = name
        self.persona = persona
        # Configure for Google Gemini
        try:
            self.llm = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=os.getenv("GOOGLE_API_KEY") or "DUMMY_KEY",
                temperature=0.7,
            )
        except Exception:
            # Fallback for limited environments or test runs
            self.llm = None
        if tools:
            self.llm = self.llm.bind_tools(tools)
        self.tools = tools

    def execute(self, state: GraphState) -> GraphState:
        # To be implemented by subclasses
        pass
