import re
from datetime import datetime, timezone
from typing import Any

from app.agents.state import TeammateState
from app.database import SessionLocal
from app.integrations.orders import order_adapter
from app.integrations.shipping import shipping_adapter


def trace(
    agent: str,
    action: str,
    summary: str,
    output: dict[str, Any],
) -> dict[str, Any]:
    return {
        "agent": agent,
        "action": action,
        # Retains compatibility with the existing response schema.
        # This contains a short decision summary, not private reasoning.
        "thought": summary,
        "output": output,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def orchestrator_node(state: TeammateState) -> dict[str, Any]:
    message = state.get("user_message", "")
    matches = re.findall(
        r"\bORD-?(\d+)\b",
        message,
        flags=re.IGNORECASE,
    )

    references = sorted({f"ORD-{number}" for number in matches})
    order_number = references[0] if len(references) == 1 else None

    summary = (
        f"Investigating order {order_number}."
        if order_number
        else "The request must identify exactly one order."
    )

    return {
        "extracted_order_number": order_number,
        "current_agent": "Operations Agent",
        "agent_logs": state.get("agent_logs", []) + [
            trace(
                "Orchestrator",
                "order_reference_validation",
                summary,
                {"order_number": order_number},
            )
        ],
    }


def operations_node(state: TeammateState) -> dict[str, Any]:
    order_number = state.get("extracted_order_number")
    organization_id = state["organization_id"]
    customer_id = state["customer_id"]

    order_data = {}
    shipment_data = {}

    if order_number:
        with SessionLocal() as db:
            order = order_adapter.get_order(
                db,
                organization_id,
                order_number,
            )

            if order is not None and order.customer_id == customer_id:
                order_data = {
                    "order_number": order.order_number,
                    "customer_id": order.customer_id,
                    "total_amount": order.total_amount,
                    "refunded_amount": order.refunded_amount,
                    "currency": order.currency,
                    "status": order.status.value,
                }

                shipment = shipping_adapter.get_shipment_by_order(
                    db,
                    organization_id,
                    order.id,
                )

                if shipment is not None:
                    shipment_data = {
                        "tracking_number": shipment.tracking_number,
                        "carrier": shipment.carrier,
                        "status": shipment.status,
                        "destination": shipment.destination_city,
                    }

    summary = (
        "Order ownership confirmed within the current organization."
        if order_data
        else "No matching order was found for this customer."
    )

    return {
        "order_data": order_data,
        "shipment_data": shipment_data,
        "current_agent": "Policy Agent",
        "agent_logs": state.get("agent_logs", []) + [
            trace(
                "Operations Agent",
                "order_and_shipment_lookup",
                summary,
                {"order": order_data, "shipment": shipment_data},
            )
        ],
    }


def policy_research_node(state: TeammateState) -> dict[str, Any]:
    order = state.get("order_data") or {}
    shipment = state.get("shipment_data") or {}

    delayed_statuses = {
        "delayed",
        "delayed_severe_weather",
        "delayed_weather",
        "carrier_delay",
    }

    remaining = round(
        order.get("total_amount", 0)
        - order.get("refunded_amount", 0),
        2,
    )

    eligible = bool(
        order
        and order.get("status") == "delayed"
        and shipment.get("status", "").lower() in delayed_statuses
        and remaining >= 35
    )

    policy = {
        "policy_id": "DEMO-DELAY-CREDIT-V1",
        "source": "local_demonstration_rule",
        "qualifies_for_credit": eligible,
        "recommended_credit_amount": 35.00 if eligible else None,
        "requires_human_gate": True,
        "remaining_balance": remaining,
    }

    return {
        "policy_data": policy,
        "current_agent": "Proposal Agent",
        "agent_logs": state.get("agent_logs", []) + [
            trace(
                "Policy Agent",
                "demonstration_eligibility_check",
                (
                    "The demonstration rule permits a proposal for human review."
                    if eligible
                    else "The demonstration rule does not permit a refund proposal."
                ),
                policy,
            )
        ],
    }


def proposal_synthesizer_node(state: TeammateState) -> dict[str, Any]:
    order = state.get("order_data") or {}
    policy = state.get("policy_data") or {}

    if not state.get("extracted_order_number"):
        response = "Provide exactly one order reference, such as ORD-4491."
    elif not order:
        response = "No matching order was found for the selected customer."
    elif not policy.get("qualifies_for_credit"):
        response = (
            "The order does not qualify under the local demonstration rule. "
            "An operator must review the case."
        )
    else:
        response = ""

    proposal = None

    if not response:
        amount = policy["recommended_credit_amount"]
        order_number = order["order_number"]

        proposal = {
            "action_type": "stripe_partial_refund",
            "target_entity": f"order:{order_number}",
            "payload": {
                "amount": amount,
                "currency": order["currency"],
                "reason": "demonstration_delayed_shipment_credit",
            },
            "idempotency_key": f"refund:{state['task_id']}",
            "requires_human_approval": True,
        }

        response = (
            f"A local ledger refund of {amount:.2f} "
            f"{order['currency']} has been proposed for {order_number}. "
            "Human approval is required before execution."
        )

    return {
        "proposed_action": proposal,
        "requires_approval": proposal is not None,
        "final_response": response,
        "current_agent": "Completed",
        "agent_logs": state.get("agent_logs", []) + [
            trace(
                "Proposal Agent",
                "proposal_decision",
                response,
                {"proposal": proposal},
            )
        ],
    }