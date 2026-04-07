from backend.agents.base import BaseAgent
from backend.state import GraphState
from langchain_core.messages import HumanMessage, SystemMessage
from backend.tools.style_manager import get_style_data

class ScriptAgent(BaseAgent):
    def __init__(self):
        super().__init__("script", "Poetic Scriptwriter")

    def execute(self, state: GraphState) -> GraphState:
        style_dna = get_style_data(state.get("style", "ghibli"))
        persona = (
            f"You are {style_dna['narrative_persona']} Your task is to expand a concept "
            "into a 5-scene poetic script for a cinematic video. Each scene should have a distinct "
            "'Visual:' description and a 'Narration:' block. "
            "Ensure the narration is fluid, immersive, and strictly narrative—DO NOT use markers like 'Scene 1', 'Scene 2', etc., in the narration text itself. "
            f"The tone must perfectly match the {style_dna['name']} universe."
        )
        
        msg = f"Expand this {style_dna['name']} concept into a 5-scene poetic script:\n{state['concept']}"
        response = self.llm.invoke([
            SystemMessage(content=persona),
            HumanMessage(content=msg)
        ])
        return {"script": response.content, "logs": state["logs"] + [f"✍️ {style_dna['name']} script drafted."]}
