from backend.agents.base import BaseAgent
from backend.state import GraphState
from langchain_core.messages import HumanMessage, SystemMessage

class ScriptAgent(BaseAgent):
    def __init__(self):
        persona = (
            "You are a poetic narrator in the style of Studio Ghibli films. Write a short YouTube video "
            "script (each with a scene title, a visual description, and 2-3 sentences of "
            "narration). Use gentle, wonder-filled language. Format as: SCENE 1: [Title]\nVisual: ...\n"
            "Narration: ..."
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
