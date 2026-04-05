from backend.agents.base import BaseAgent
from backend.state import GraphState
from langchain_core.messages import HumanMessage, SystemMessage

class ConceptAgent(BaseAgent):
    def __init__(self):
        persona = (
            "You are a visionary Studio Ghibli creative director. Generate a short, magical story concept "
            "(3-4 sentences) for a cinematic video. It MUST capture the quiet, awe-inspiring, and slightly "
            "melancholic Ghibli essence. CRITICAL: Avoid repetitive tropes (no generic glowing mushrooms or standard forest sprites). "
            "Invent highly unique protagonists (e.g. outcasts, weary mechanics, elderly wanderers, unusual clockwork animals), "
            "deeply imaginative but grounded lore, hidden machinery, bizarre spirits, and surprising subversions of the given theme. "
            "Keep it surreal, intensely emotional, and vividly unique. Return ONLY the concept text."
        )
        super().__init__("concept", persona)

    def execute(self, state: GraphState) -> GraphState:
        msg = f"Create a Ghibli-style video concept for the theme: '{state['topic']}'"
        response = self.llm.invoke([
            SystemMessage(content=self.persona),
            HumanMessage(content=msg)
        ])
        return {"concept": response.content, "logs": [f"✦ Concept crafted by {self.name} agent."]}
