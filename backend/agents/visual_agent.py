from backend.agents.base import BaseAgent
from backend.state import GraphState
from langchain_core.messages import HumanMessage, SystemMessage
from backend.tools.style_manager import get_style_data

class VisualAgent(BaseAgent):
    def __init__(self):
        super().__init__("visuals", "Master Prompt Engineer")

    def execute(self, state: GraphState) -> GraphState:
        style_dna = get_style_data(state.get("style", "ghibli"))
        num_scenes = state.get('num_scenes', 5)
        
        persona = (
            f"You are {style_dna['narrative_persona']} specializing in {style_dna['name']} aesthetics. "
            "Given a script, generate detailed image generation prompts for each scene. "
            f"Each prompt MUST strictly follow these rules: {style_dna['visual_rules']} "
            "Format as a numbered list."
        )
        
        msg = f"Generate exactly 1 {style_dna['name']} image prompt per scene (Total of {num_scenes} prompts) based on this script:\n{state['script']}"
        response = self.llm.invoke([
            SystemMessage(content=persona),
            HumanMessage(content=msg)
        ])
        return {"visuals": response.content, "logs": state["logs"] + [f"◈ {num_scenes} {style_dna['name']} scene prompts painted."]}
