from langgraph.graph import StateGraph, END
from backend.state import GraphState
from backend.agents.concept_agent import ConceptAgent
from backend.agents.script_agent import ScriptAgent
from backend.agents.visual_agent import VisualAgent
from backend.agents.metadata_agent import MetadataAgent

def create_orchestrator():
    # Initialize agents
    concept_agent = ConceptAgent()
    script_agent = ScriptAgent()
    visual_agent = VisualAgent()
    metadata_agent = MetadataAgent()

    # Create the graph
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("concept", concept_agent.execute)
    workflow.add_node("script", script_agent.execute)
    workflow.add_node("visuals", visual_agent.execute)
    workflow.add_node("metadata", metadata_agent.execute)

    # Set entry point
    workflow.set_entry_point("concept")

    # Add edges
    workflow.add_edge("concept", "script")
    workflow.add_edge("script", "visuals")
    workflow.add_edge("visuals", "metadata")
    workflow.add_edge("metadata", END)

    return workflow.compile()

# Example usage:
# orchestrator = create_orchestrator()
# result = orchestrator.invoke({"topic": "Rainy Rooftop", "logs": [], "status": "running"})
