from langgraph.graph import StateGraph, END
from backend.state import GraphState
from backend.agents.concept_agent import ConceptAgent
from backend.agents.script_agent import ScriptAgent
from backend.agents.music_agent import MusicAgent
from backend.agents.visual_agent import VisualAgent
from backend.agents.metadata_agent import MetadataAgent
from backend.agents.production_agent import ProductionAgent

def create_orchestrator():
    # Initialize agents
    concept_agent = ConceptAgent()
    script_agent = ScriptAgent()
    music_agent = MusicAgent()
    visual_agent = VisualAgent()
    metadata_agent = MetadataAgent()
    production_agent = ProductionAgent()

    # Create the graph
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("concept", concept_agent.execute)
    workflow.add_node("script", script_agent.execute)
    workflow.add_node("music", music_agent.execute)
    workflow.add_node("visuals", visual_agent.execute)
    workflow.add_node("metadata", metadata_agent.execute)
    workflow.add_node("image_gen", production_agent.generate_images_node)
    workflow.add_node("audio_gen", production_agent.generate_audio_node)
    workflow.add_node("finalize_video", production_agent.finalize_video_node)

    # Set entry point
    workflow.set_entry_point("concept")

    # Add linear edges
    workflow.add_edge("concept", "script")
    workflow.add_edge("script", "music")
    workflow.add_edge("music", "visuals")
    workflow.add_edge("script", "metadata")
    
    # Asset pipeline: visuals -> image_gen -> audio_gen -> finalize_video
    workflow.add_edge("visuals", "image_gen")
    workflow.add_edge("image_gen", "audio_gen")
    workflow.add_edge("audio_gen", "finalize_video")
    workflow.add_edge("finalize_video", END)
    
    # metadata can finish on its own or join finalize_video if you want to wait. 
    # Let's let it finish naturally so other agents don't wait for it if they are faster.
    workflow.add_edge("metadata", END)

    return workflow.compile()

# Example usage:
# orchestrator = create_orchestrator()
# result = orchestrator.invoke({"topic": "Rainy Rooftop", "logs": [], "status": "running"})
