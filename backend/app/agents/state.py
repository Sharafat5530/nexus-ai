from typing import TypedDict, List, Dict, Any, Optional

class AgentLog(TypedDict):
    agent: str
    action: str
    thought: str
    output: Dict[str, Any]
    timestamp: str

class TeammateState(TypedDict):
    """Shared state passed between specialized LangGraph agents."""
    organization_id: str
    customer_id: str
    conversation_id: str
    task_id: str
    user_message: str
    
    # Entity extraction
    extracted_order_number: Optional[str]
    
    # Domain records
    order_data: Optional[Dict[str, Any]]
    shipment_data: Optional[Dict[str, Any]]
    policy_data: Optional[Dict[str, Any]]
    
    # Proposal & Gate
    proposed_action: Optional[Dict[str, Any]]
    requires_approval: bool
    
    # Complete execution trail
    agent_logs: List[AgentLog]
    current_agent: str
    final_response: str
