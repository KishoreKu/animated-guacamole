from langgraph.graph import StateGraph, END
from backend.state import GraphState

def create_orchestrator():
    # Initialize agents (Lazy import to prevent startup crashes)
    from backend.agents.concept_agent import ConceptAgent
    from backend.agents.script_agent import ScriptAgent
    from backend.agents.visual_agent import VisualAgent
    from backend.agents.metadata_agent import MetadataAgent
    from backend.agents.production_agent import ProductionAgent
    
    concept_agent = ConceptAgent()
    script_agent = ScriptAgent()
    visual_agent = VisualAgent()
    metadata_agent = MetadataAgent()
    production_agent = ProductionAgent()

    # Create the graph
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("concept", concept_agent.execute)
    workflow.add_node("script", script_agent.execute)
    workflow.add_node("visuals", visual_agent.execute)
    workflow.add_node("metadata", metadata_agent.execute)
    workflow.add_node("production", production_agent.generate_images_node)
    workflow.add_node("finalize_video", production_agent.finalize_video_node)

    # Set entry point
    workflow.set_entry_point("concept")

    # Sequential Flow: Concept -> Script -> Visuals -> Metadata -> Production -> END
    # This ensures the UI stays connected while the heavy image generation runs.
    workflow.add_edge("concept", "script")
    workflow.add_edge("script", "visuals")
    workflow.add_edge("visuals", "metadata")
    workflow.add_edge("metadata", "production")
    workflow.add_edge("production", END)
    
    # The finalize_video node remains as a manual trigger after approval
    workflow.add_edge("finalize_video", END)

    return workflow.compile()

# Example usage:
# orchestrator = create_orchestrator()
# result = orchestrator.invoke({"topic": "Rainy Rooftop", "logs": [], "status": "running"})
