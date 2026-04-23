from langgraph.graph import StateGraph, END
from backend.state import GraphState
from backend.agents.visual_agent import VisualAgent
from backend.agents.metadata_agent import MetadataAgent
from backend.agents.production_agent import ProductionAgent

def create_orchestrator():
    # Initialize agents
    from backend.agents.concept_agent import ConceptAgent
    concept_agent = ConceptAgent()
    visual_agent = VisualAgent()
    metadata_agent = MetadataAgent()
    production_agent = ProductionAgent()

    # Create the graph
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("concept", concept_agent.execute)
    workflow.add_node("visuals", visual_agent.execute)
    workflow.add_node("metadata", metadata_agent.execute)
    workflow.add_node("image_gen", production_agent.generate_images_node)
    workflow.add_node("finalize_video", production_agent.finalize_video_node)

    # Set entry point
    workflow.set_entry_point("concept")

    # Sequential Flow: Concept -> Visuals -> Image Gen -> Metadata -> END
    # This ensures the UI stays connected while the heavy image generation runs.
    workflow.add_edge("concept", "visuals")
    workflow.add_edge("visuals", "image_gen")
    workflow.add_edge("image_gen", "metadata")
    workflow.add_edge("metadata", END)
    
    # The finalize_video node remains as a manual trigger after approval
    workflow.add_edge("finalize_video", END)

    return workflow.compile()

# Example usage:
# orchestrator = create_orchestrator()
# result = orchestrator.invoke({"topic": "Rainy Rooftop", "logs": [], "status": "running"})
