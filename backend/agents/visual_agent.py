from backend.agents.base import BaseAgent
from backend.state import GraphState
from langchain_core.messages import HumanMessage, SystemMessage

class VisualAgent(BaseAgent):
    def __init__(self):
        persona = (
            "You are an AI image prompt engineer specializing in Studio Ghibli aesthetics. "
            "Given a script, generate detailed image generation prompts for each scene. "
            "Each prompt should include: Ghibli art style, soft watercolor lighting, lush "
            "backgrounds, whimsical details. Format as a numbered list."
        )
        super().__init__("visuals", persona)

    def execute(self, state: GraphState) -> GraphState:
        num_scenes = state.get('num_scenes', 5)
        msg = f"Generate exactly 1 Ghibli-style image prompt per scene (Total of {num_scenes} prompts) based on this script:\n{state['script']}"
        response = self.llm.invoke([
            SystemMessage(content=self.persona),
            HumanMessage(content=msg)
        ])
        return {"visuals": response.content, "logs": [f"◈ {num_scenes} scene prompts painted."]}
