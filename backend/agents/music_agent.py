from backend.agents.base import BaseAgent
from backend.state import GraphState
from langchain_core.messages import HumanMessage, SystemMessage
from backend.tools.style_manager import get_style_data

class MusicAgent(BaseAgent):
    def __init__(self):
        super().__init__("music", "Universal Film Composer")

    def execute(self, state: GraphState) -> GraphState:
        style_dna = get_style_data(state.get("style", "ghibli"))
        persona = (
            f"You are a master film composer specializing in {style_dna['name']} scores. "
            "Your task is to analyze a story and pick the perfect musical 'Mood' for this universe. "
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
        
        msg = f"Pick the perfect musical mood for this {style_dna['name']} concept and script:\nConcept: {state['concept']}\nScript: {state['script']}\n\nOutput only the MOOD_NAME."
        response = self.llm.invoke([
            SystemMessage(content=persona),
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
                
        return {"music_mood": selected_mood, "logs": state["logs"] + [f"✿ Orchestrating '{selected_mood}' score for {style_dna['name']}."]}
