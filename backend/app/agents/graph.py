from langgraph.graph import StateGraph, END
from app.agents.state import TeammateState
from app.agents.nodes import (
    orchestrator_node,
    operations_node,
    policy_research_node,
    proposal_synthesizer_node
)

def build_workflow_graph():
    """Builds the compiled LangGraph workflow pipeline."""
    workflow = StateGraph(TeammateState)
    
    # Register agent nodes
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("operations", operations_node)
    workflow.add_node("policy_research", policy_research_node)
    workflow.add_node("proposal_synthesizer", proposal_synthesizer_node)
    
    # Define linear execution flow
    workflow.set_entry_point("orchestrator")
    workflow.add_edge("orchestrator", "operations")
    workflow.add_edge("operations", "policy_research")
    workflow.add_edge("policy_research", "proposal_synthesizer")
    workflow.add_edge("proposal_synthesizer", END)
    
    return workflow.compile()

workflow_graph = build_workflow_graph()
