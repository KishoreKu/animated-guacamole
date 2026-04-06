from backend.agents.base import BaseAgent
from backend.state import GraphState
from langchain_core.messages import HumanMessage, SystemMessage
from backend.tools.ghibli_tools import youtube_seo_check

class MetadataAgent(BaseAgent):
    def __init__(self):
        persona = (
            "You are a YouTube SEO and Sound Design expert for Ghibli-style content. \n"
            "Based on the provided concept and scene-by-scene visual descriptions, generate: \n"
            "1. VIDEO TITLE (compelling, under 60 chars)\n"
            "2. DESCRIPTION (2 paragraphs, include keywords)\n"
            "3. TAGS (10 comma-separated tags)\n"
            "4. THUMBNAIL TEXT (bold 4-word overlay text)\n"
            "5. BGM PROMPT (a highly tailored atmospheric instrumental description that matches the specific mood of the scenes: e.g. 'Staccato piano, whimsical oboe, light rain ambiance, nostalgic')\n"
            "Use the 'youtube_seo_check' tool to validate your title. Return labels for all 5 points."
        )
        super().__init__("metadata", persona, tools=[youtube_seo_check])

    def execute(self, state: GraphState) -> GraphState:
        msg = (
            f"Create YouTube metadata and an atmospheric BGM prompt for this Ghibli video:\n\n"
            f"Concept: {state['concept']}\n"
            f"Theme: {state['topic']}\n"
            f"Script Outline: {state['script'][:500]}...\n"
            f"Visual Style / Scene Descriptions: {state['visuals']}\n\n"
            "Ensure the BGM PROMPT reflects the specific mood, instrumentation, and art style mentioned in the visuals above."
        )
        response = self.llm.invoke([
            SystemMessage(content=self.persona),
            HumanMessage(content=msg)
        ])
        
        content = response.content
        bgm_prompt = "Atmospheric Ghibli instrumental music" # Fallback
        
        if "BGM PROMPT:" in content:
            parts = content.split("BGM PROMPT:")
            bgm_prompt = parts[-1].strip()
            
        return {
            "metadata": content, 
            "bgm_prompt": bgm_prompt,
            "logs": ["❋ YouTube metadata and BGM prompt ready."]
        }
