from backend.agents.base import BaseAgent
from backend.state import GraphState
from langchain_core.messages import HumanMessage, SystemMessage

class ScriptAgent(BaseAgent):
    def __init__(self):
        persona = (
            "You are a master storyteller in the style of Studio Ghibli. Write a short film "
            "script in scenes. CRITICAL: The 'Narration' text must be fluid and immersive, "
            "like a campfire story or a character's internal thoughts. "
            "NEVER start a narration with 'Scene 1' or 'Scene 2'. "
            "NEVER say 'The camera pans' or other technical terms in the narration block—keep those in the 'Visual' block. "
            "Format as:\nSCENE 1: [Title]\nVisual: [Ghibli style description]\nNarration: [Poetic, natural storytelling text]"
        )
        super().__init__("script", persona)

    def execute(self, state: GraphState) -> GraphState:
        num_scenes = state.get('num_scenes', 5)
        msg = f"Write a Ghibli-style narrated video script based on this concept (generate exactly {num_scenes} scenes):\n{state['concept']}"
        response = self.llm.invoke([
            SystemMessage(content=self.persona),
            HumanMessage(content=msg)
        ])
        return {"script": response.content, "logs": [f"✿ Script complete — {num_scenes} scenes ready."]}
