from langgraph.graph import StateGraph, END
from backend.state import GraphState
from backend.agents.concept_agent import ConceptAgent
from backend.agents.script_agent import ScriptAgent
from backend.agents.visual_agent import VisualAgent
from backend.agents.metadata_agent import MetadataAgent
from backend.agents.production_agent import ProductionAgent
from backend.agents.critic_agent import CriticAgent

def create_orchestrator():
    # Initialize agents
    concept_agent = ConceptAgent()
    script_agent = ScriptAgent()
    visual_agent = VisualAgent()
    metadata_agent = MetadataAgent()
    production_agent = ProductionAgent()
    critic_agent = CriticAgent()

    # Create the graph
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("concept", concept_agent.execute)
    workflow.add_node("script", script_agent.execute)
    workflow.add_node("visuals", visual_agent.execute)
    workflow.add_node("metadata", metadata_agent.execute)
    workflow.add_node("production", production_agent.execute)
    workflow.add_node("critic", critic_agent.execute)

    # Logic: Concept -> Critic -> [If Revise: Concept, Else: Script] -> Critic -> [If Revise: Script, Else: Visuals] -> ...

    def should_revise_concept(state: GraphState):
        last_eval = state.get("evaluations", [])[-1] if state.get("evaluations") else None
        if last_eval and last_eval["node"] == "concept" and last_eval["status"] == "REVISE":
            return "concept"
        return "script"

    def should_revise_script(state: GraphState):
        last_eval = state.get("evaluations", [])[-1] if state.get("evaluations") else None
        if last_eval and last_eval["node"] == "script" and last_eval["status"] == "REVISE":
            return "script"
        return "visuals"

    # Set entry point
    workflow.set_entry_point("concept")

    # Add edges
    workflow.add_edge("concept", "critic")
    workflow.add_conditional_edges(
        "critic",
        should_revise_concept,
        {
            "concept": "concept",
            "script": "script"
        }
    )
    
    workflow.add_edge("script", "critic")
    workflow.add_conditional_edges(
        "critic",
        should_revise_script,
        {
            "script": "script",
            "visuals": "visuals"
        }
    )

    workflow.add_edge("visuals", "metadata")
    workflow.add_edge("metadata", "production")
    workflow.add_edge("production", END)

    return workflow.compile()

# Example usage:
# orchestrator = create_orchestrator()
# result = orchestrator.invoke({"topic": "Rainy Rooftop", "logs": [], "status": "running"})
