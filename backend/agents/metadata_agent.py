from backend.agents.base import BaseAgent
from backend.state import GraphState
from langchain_core.messages import HumanMessage, SystemMessage
from backend.tools.ghibli_tools import youtube_seo_check

class MetadataAgent(BaseAgent):
    def __init__(self):
        persona = (
            "You are a YouTube SEO expert for Ghibli-style content. Generate: \n"
            "1. VIDEO TITLE (compelling, under 60 chars)\n"
            "2. DESCRIPTION (2 paragraphs, include keywords)\n"
            "3. TAGS (10 comma-separated tags)\n"
            "4. THUMBNAIL TEXT (bold 4-word overlay text)\n"
            "5. BGM PROMPT (atmospheric Ghibli-style instrumental description, e.g. 'Piano, whimsical, strings, nostalgia')\n"
            "Use the 'youtube_seo_check' tool to validate your title before finalizing. "
            "Return in that exact format with labels."
        )
        super().__init__("metadata", persona, tools=[youtube_seo_check])

    def execute(self, state: GraphState) -> GraphState:
        msg = (
            f"Create YouTube metadata for this Ghibli video:\nConcept: {state['concept']}\n\n"
            f"Theme: {state['topic']}"
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
