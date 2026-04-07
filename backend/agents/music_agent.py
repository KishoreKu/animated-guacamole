from backend.agents.base import BaseAgent
from backend.state import GraphState
from langchain_core.messages import HumanMessage, SystemMessage

class MusicAgent(BaseAgent):
    def __init__(self):
        persona = (
            "You are a master film composer specializing in Studio Ghibli scores. "
            "Your task is to analyze a story and pick the perfect musical 'Mood'. "
            "Select EXACTLY ONE of the following moods that best fits the theme:\n"
            "- whimsical_adventure: Playful, up-tempo piano and strings.\n"
            "- nostalgic_memory: Gentle piano and flute, emotional and reflective.\n"
            "- mysterious_forest: Ambient, deep strings and magical mallets.\n"
            "- melancholy_sorrow: Solo piano, sad yet beautiful.\n"
            "- triumphant_heroic: Epic orchestral brass and fast strings.\n"
            "- peaceful_watercolor: Acoustic guitar and light piano.\n"
            "- magical_wonder: Sparkling celesta and sweeping orchestral swells.\n"
            "- spooky_shadows: Tense, low woodwinds and metallic percussion."
        )
        super().__init__("music", persona)

    def execute(self, state: GraphState) -> GraphState:
        msg = f"Pick the perfect Ghibli music mood for this concept and script:\nConcept: {state['concept']}\nScript: {state['script']}\n\nOutput only the MOOD_NAME."
        response = self.llm.invoke([
            SystemMessage(content=self.persona),
            HumanMessage(content=msg)
        ])
        
        mood = response.content.strip().lower()
        # Validation
        valid_moods = [
            "whimsical_adventure", "nostalgic_memory", "mysterious_forest", 
            "melancholy_sorrow", "triumphant_heroic", "peaceful_watercolor",
            "magical_wonder", "spooky_shadows"
        ]
        
        # Clean up any potential garbage from the LLM
        selected_mood = "peaceful_watercolor" # Default
        for m in valid_moods:
            if m in mood:
                selected_mood = m
                break
                
        return {"music_mood": selected_mood, "logs": [f"✿ Orchestrating '{selected_mood}' musical score."]}
