from backend.agents.base import BaseAgent
from backend.state import GraphState
from langchain_core.messages import HumanMessage, SystemMessage

class ConceptAgent(BaseAgent):
    def __init__(self):
        persona = (
            "You are a Studio Ghibli creative director. Generate a short, magical story concept "
            "(3-4 sentences) for a YouTube video in the Ghibli style. Focus on wonder, nature spirits, "
            "and quiet beauty. Return ONLY the concept text."
        )
        super().__init__("concept", persona)

    def execute(self, state: GraphState) -> GraphState:
        msg = f"Create a Ghibli-style video concept for the theme: '{state['topic']}'"
        response = self.llm.invoke([
            SystemMessage(content=self.persona),
            HumanMessage(content=msg)
        ])
        return {"concept": response.content, "logs": [f"✦ Concept crafted by {self.name} agent."]}
