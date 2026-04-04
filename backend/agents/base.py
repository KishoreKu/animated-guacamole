import os
from typing import List, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from backend.state import GraphState
from dotenv import load_dotenv

load_dotenv()

class BaseAgent:
    def __init__(self, name: str, persona: str, tools: List[Any] = None, model_name: str = "anthropic/claude-3.5-sonnet"):
        self.name = name
        self.persona = persona
        # Configure for OpenRouter
        self.llm = ChatOpenAI(
            model=model_name,
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://ghibli-studio.io", # Optional
                "X-Title": "Ghibli Studio",
            }
        )
        if tools:
            self.llm = self.llm.bind_tools(tools)
        self.tools = tools

    def execute(self, state: GraphState) -> GraphState:
        # To be implemented by subclasses
        pass
