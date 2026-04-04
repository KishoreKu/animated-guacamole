from typing import Annotated, TypedDict, List
from langgraph.graph.message import add_messages

class GraphState(TypedDict):
    """
    Represents the state of our Ghibli Video Studio graph.
    """
    topic: str
    concept: str
    script: str
    visuals: str
    metadata: str
    logs: List[str]
    messages: Annotated[List, add_messages]
    status: str # idle | running | done | error
