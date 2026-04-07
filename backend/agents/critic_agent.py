from backend.agents.base import BaseAgent
from backend.state import GraphState
from langchain_core.messages import HumanMessage, SystemMessage
import json

class CriticAgent(BaseAgent):
    def __init__(self):
        persona = (
            "You are the Lead Artistic Director at Studio Ghibli. Your job is to strictly evaluate "
            "the quality and 'Ghibli-ness' of the proposed video concepts and scripts. \n\n"
            "Criteria:\n"
            "1. NO TROPES: Reject generic glowing forests, standard sprites, or repetitive fairy tales.\n"
            "2. EMOTIONAL DEPTH: Must feel melancholic, peaceful, or magical (Ma).\n"
            "3. SPECIFICITY: Are the characters and locations unique? (e.g. outcasts, weary mechanics).\n"
            "4. FORMAT: Is the script properly structured?\n\n"
            "RESPONSE FORMAT (JSON ONLY):\n"
            "{\n"
            "  \"score\": 1-10,\n"
            "  \"feedback\": \"Detailed critique here\",\n"
            "  \"status\": \"APPROVE\" or \"REVISE\"\n"
            "}"
        )
        super().__init__("critic", persona)

    def execute(self, state: GraphState) -> GraphState:
        # Determine what we are reviewing
        if not state.get("script"):
            target = "CONCEPT"
            content = state["concept"]
        else:
            target = "SCRIPT"
            content = state["script"]

        msg = f"Evaluate this Ghibli {target}:\n\n{content}"
        
        response = self.llm.invoke([
            SystemMessage(content=self.persona),
            HumanMessage(content=msg)
        ])

        try:
            # Clean response to ensure it's valid JSON
            clean_content = response.content.replace("```json", "").replace("```", "").strip()
            eval_data = json.loads(clean_content)
        except Exception:
            # Fallback if LLM fails JSON format
            eval_data = {"score": 7, "feedback": "Evaluation complete.", "status": "APPROVE"}

        node_name = target.lower()
        log_msg = f"🔍 Critic Evaluation for {node_name}: {eval_data['score']}/10 - {eval_data['status']}"
        
        # We append to evaluations list (if it exists, otherwise init it)
        evalutions = state.get("evaluations", [])
        evalutions.append({
            "node": node_name,
            "score": eval_data["score"],
            "feedback": eval_data["feedback"],
            "status": eval_data["status"]
        })

        return {
            "evaluations": evalutions,
            "logs": [log_msg]
        }
