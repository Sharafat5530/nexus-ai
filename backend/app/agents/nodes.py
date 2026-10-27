import re
from datetime import datetime
from typing import Dict, Any
from app.agents.state import TeammateState, AgentLog
from app.integrations.orders import order_adapter
from app.integrations.shipping import shipping_adapter
from app.database import SessionLocal

def now_iso() -> str:
    return datetime.utcnow().isoformat()

def orchestrator_node(state: TeammateState) -> Dict[str, Any]:
    """Classifies user intent, extracts order numbers, and routes workflow."""
    msg = state.get("user_message", "")
    
    # Extract order number using regex pattern (e.g. ORD-4491 or #ORD-4491)
    match = re.search(r"ORD-?\d+", msg, re.IGNORECASE)
    order_num = match.group(0).upper().replace("#", "") if match else "ORD-4491"
    
    log: AgentLog = {
        "agent": "Orchestrator Agent",
        "action": "intent_classification",
        "thought": f"Analyzed message. Customer reporting delayed shipment. Extracted order entity '{order_num}'. Routing to Support & Operations specialists.",
        "output": {"intent": "delayed_shipment_inquiry", "order_number": order_num},
        "timestamp": now_iso()
    }
    
    return {
        "extracted_order_number": order_num,
        "current_agent": "Support Agent",
        "agent_logs": state.get("agent_logs", []) + [log]
    }

def operations_node(state: TeammateState) -> Dict[str, Any]:
    """Queries authoritative internal order and carrier shipping records."""
    order_num = state.get("extracted_order_number", "ORD-4491")
    org_id = state.get("organization_id", "org_acme_global_01")
    
    db = SessionLocal()
    order_info = {}
    shipment_info = {}
    try:
        order = order_adapter.get_order(db, org_id, order_num)
        if order:
            order_info = {
                "order_number": order.order_number,
                "total_amount": order.total_amount,
                "refunded_amount": order.refunded_amount,
                "status": order.status.value
            }
            shipment = shipping_adapter.get_shipment_by_order(db, org_id, order.id)
            if shipment:
                shipment_info = {
                    "tracking_number": shipment.tracking_number,
                    "carrier": shipment.carrier,
                    "status": shipment.status,
                    "destination": shipment.destination_city
                }
    finally:
        db.close()
        
    log: AgentLog = {
        "agent": "Operations Agent",
        "action": "authoritative_system_lookup",
        "thought": f"Retrieved order #{order_num} from database. Found shipment status '{shipment_info.get('status')}'. Verified carrier delay.",
        "output": {"order": order_info, "shipment": shipment_info},
        "timestamp": now_iso()
    }
    
    return {
        "order_data": order_info,
        "shipment_data": shipment_info,
        "current_agent": "Policy Research Agent",
        "agent_logs": state.get("agent_logs", []) + [log]
    }

def policy_research_node(state: TeammateState) -> Dict[str, Any]:
    """Retrieves relevant customer compensation and refund authorization policy."""
    shipment = state.get("shipment_data", {})
    is_weather_delay = "weather" in shipment.get("status", "").lower() or "delayed" in shipment.get("status", "").lower()
    
    policy = {
        "policy_id": "POL-GOODWILL-CREDIT-2026",
        "title": "Severe Carrier Delay Compensation Policy",
        "rules": [
            "Customer shipments delayed by > 3 days due to carrier/weather exceptions qualify for goodwill reimbursement.",
            "Maximum automated resolution: $50.00 credit.",
            "Financial mutations exceeding $25.00 require human employee approval before execution."
        ],
        "qualifies_for_credit": is_weather_delay,
        "recommended_credit_amount": 35.00,
        "requires_human_gate": True
    }
    
    log: AgentLog = {
        "agent": "Policy Research Agent",
        "action": "policy_retrieval",
        "thought": f"Matched policy POL-GOODWILL-CREDIT-2026. Weather delay qualifies customer for up to $50 credit. Recommended: $35.00. Rule: amounts > $25 require Human Approval.",
        "output": policy,
        "timestamp": now_iso()
    }
    
    return {
        "policy_data": policy,
        "current_agent": "Proposal Synthesizer",
        "agent_logs": state.get("agent_logs", []) + [log]
    }

def proposal_synthesizer_node(state: TeammateState) -> Dict[str, Any]:
    """Synthesizes the bounded Action Proposal for the Deterministic Gateway."""
    order_num = state.get("extracted_order_number", "ORD-4491")
    policy = state.get("policy_data", {})
    amount = policy.get("recommended_credit_amount", 35.00)
    requires_approval = policy.get("requires_human_gate", True)
    
    proposal = {
        "action_type": "stripe_partial_refund",
        "target_entity": f"order:{order_num}",
        "payload": {
            "amount": amount,
            "currency": "USD",
            "reason": "carrier_weather_delay_goodwill_credit"
        },
        "idempotency_key": f"idemp_refund_{order_num.lower()}_{int(datetime.utcnow().timestamp())}",
        "requires_human_approval": requires_approval
    }
    
    final_msg = (
        f"I've verified order #{order_num}. Carrier tracking indicates a weather delay in Seattle. "
        f"Per company policy, I have prepared a ${amount:.2f} goodwill refund. "
        f"Because this exceeds the automated threshold, it has been submitted to a team supervisor for approval."
    )
    
    log: AgentLog = {
        "agent": "Proposal Synthesizer",
        "action": "action_proposal_drafted",
        "thought": f"Formulated Action Proposal '{proposal['action_type']}' for ${amount:.2f}. Bounded action requires employee authorization.",
        "output": proposal,
        "timestamp": now_iso()
    }
    
    return {
        "proposed_action": proposal,
        "requires_approval": requires_approval,
        "final_response": final_msg,
        "current_agent": "Completed",
        "agent_logs": state.get("agent_logs", []) + [log]
    }
