import operator
from typing import Annotated, TypedDict, List
from langgraph.graph.message import add_messages

class GraphState(TypedDict):
    """
    Represents the state of our Ghibli Video Studio graph.
    """
    topic: str
    num_scenes: int
    generate_video: bool
    concept: str
    script: str
    visuals: str
    metadata: str
    bgm_prompt: str
    image_urls: List[str]
    audio_urls: List[str]
    video_url: str
    local_image_paths: List[str]
    local_audio_paths: List[str]
    logs: Annotated[List[str], operator.add]
    messages: Annotated[List, add_messages]
    evaluations: List[dict] # List of {node: str, score: int, feedback: str}
    status: str # idle | running | done | error
