from backend.agents.base import BaseAgent
from backend.state import GraphState
from langchain_core.messages import HumanMessage, SystemMessage
from backend.tools.style_manager import get_style_data

class ConceptAgent(BaseAgent):
    def __init__(self):
        super().__init__("concept", "Visionary Director")

    def execute(self, state: GraphState) -> GraphState:
        style_dna = get_style_data(state.get("style", "ghibli"))
        persona = (
            f"You are {style_dna['narrative_persona']} Generate a short, magical story concept "
            "(3-4 sentences) for a cinematic video. It MUST capture the exact essence of this universe. "
            "CRITICAL: Avoid repetitive tropes. Invent highly unique protagonists (e.g. outcasts, weary mechanics, "
            "elderly wanderers, unusual clockwork characters), deeply imaginative but grounded lore, "
            "and surprising subversions of the given theme. Keep it surreal, intensely emotional, and vividly unique. "
            "Return ONLY the concept text."
        )
        
        msg = f"Create a {style_dna['name']} video concept for the theme: '{state['topic']}'"
        response = self.llm.invoke([
            SystemMessage(content=persona),
            HumanMessage(content=msg)
        ])
        return {"concept": response.content, "logs": state["logs"] + [f"✦ {style_dna['name']} concept crafted."]}
