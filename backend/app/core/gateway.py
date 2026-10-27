import re
from typing import Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.workflow import ActionProposal, ProposalStatus, Approval, ApprovalStatus, Task, TaskStatus
from app.models.audit import AuditEvent, AuditEventType
from app.integrations.orders import order_adapter

class DeterministicActionGateway:
    """
    Server-side deterministic security gate.
    Every state mutation must pass this gateway before hitting business adapters.
    """
    
    # Global Platform Kill Switch
    KILL_SWITCH_ENGAGED: bool = False
    
    # Allowed action allowlist
    ALLOWED_ACTIONS = {
        "stripe_partial_refund",
        "carrier_upgrade",
        "crm_update_lead",
        "calendar_book_meeting"
    }
    
    # Hard parameter constraints
    MAX_REFUND_LIMIT = 50.00
    
    # Prompt injection signatures
    INJECTION_PATTERNS = [
        r"ignore previous instructions",
        r"system override",
        r"admin bypass",
        r"grant full refund",
        r"drop table",
        r"<script>",
        r"bash -i"
    ]

    @classmethod
    def set_kill_switch(cls, enabled: bool) -> bool:
        cls.KILL_SWITCH_ENGAGED = enabled
        return cls.KILL_SWITCH_ENGAGED

    def evaluate_and_execute(
        self,
        db: Session,
        organization_id: str,
        proposal_id: str,
        actor_id: str
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Revalidates security rules, human sign-offs, and executes the permitted side effect.
        """
        # 1. Kill Switch Check
        if self.KILL_SWITCH_ENGAGED:
            self._log_violation(db, organization_id, proposal_id, actor_id, "Platform Kill Switch is Active. All side effects frozen.")
            return False, "Execution blocked: Global Kill Switch is engaged.", {}

        # 2. Fetch and verify proposal exists in tenant
        proposal = db.query(ActionProposal).filter(
            ActionProposal.id == proposal_id,
            ActionProposal.organization_id == organization_id
        ).first()
        if not proposal:
            return False, "Action Proposal not found or unauthorized tenant.", {}

        # 3. Action Allowlist Check
        if proposal.action_type not in self.ALLOWED_ACTIONS:
            self._log_violation(db, organization_id, proposal.id, actor_id, f"Unauthorized tool action: '{proposal.action_type}'")
            proposal.status = ProposalStatus.BLOCKED
            db.commit()
            return False, f"Gateway Policy Violation: Tool '{proposal.action_type}' is not allowlisted.", {}

        # 4. Prompt Injection & Malicious Content Scan
        payload_str = str(proposal.payload).lower()
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, payload_str):
                self._log_violation(db, organization_id, proposal.id, actor_id, f"Prompt injection signature detected: '{pattern}'")
                proposal.status = ProposalStatus.BLOCKED
                db.commit()
                return False, "Gateway Security Alert: Prompt injection pattern detected in payload.", {}

        # 5. Hard Parameter Validation (Refund Ceiling)
        if proposal.action_type == "stripe_partial_refund":
            amount = float(proposal.payload.get("amount", 0.0))
            if amount <= 0:
                return False, "Invalid refund amount: Must be greater than $0.00.", {}
            if amount > self.MAX_REFUND_LIMIT:
                self._log_violation(db, organization_id, proposal.id, actor_id, f"Proposed amount ${amount} exceeds ceiling ${self.MAX_REFUND_LIMIT}")
                proposal.status = ProposalStatus.BLOCKED
                db.commit()
                return False, f"Policy Violation: Refund amount ${amount:.2f} exceeds hard limit of ${self.MAX_REFUND_LIMIT:.2f}.", {}

        # 6. Human Approval Revalidation & Expiration Check
        if proposal.requires_human_approval:
            approval = proposal.approval
            if not approval:
                return False, "Restricted action requires an approval gate record.", {}
            if approval.status != ApprovalStatus.APPROVED:
                return False, f"Action cannot execute: Approval status is '{approval.status.value}'.", {}
            if approval.expires_at and datetime.utcnow() > approval.expires_at:
                approval.status = ApprovalStatus.EXPIRED
                proposal.status = ProposalStatus.BLOCKED
                db.commit()
                return False, "Approval has expired. Action must be re-evaluated.", {}

        # 7. Execute Permitted Mutation via Typed Business Adapter
        execution_result = {}
        if proposal.action_type == "stripe_partial_refund":
            order_num = proposal.target_entity.replace("order:", "")
            execution_result = order_adapter.process_refund(
                db=db,
                organization_id=organization_id,
                order_number=order_num,
                amount=float(proposal.payload.get("amount")),
                reason=proposal.payload.get("reason", "Goodwill credit"),
                idempotency_key=proposal.idempotency_key,
                actor_id=actor_id
            )

        # 8. Advance State to Pending Independent Verification
        proposal.status = ProposalStatus.EXECUTED
        task = proposal.task
        if task:
            task.status = TaskStatus.EXECUTING
        db.commit()

        return True, "Action successfully verified and executed by Gateway.", execution_result

    def _log_violation(self, db: Session, org_id: str, target_id: str, actor_id: str, summary: str):
        audit = AuditEvent(
            organization_id=org_id,
            event_type=AuditEventType.ACTION_BLOCKED,
            actor_id=actor_id,
            target_id=target_id,
            summary=f"ZERO-TRUST GATEWAY INTERVENTION: {summary}",
            details={"timestamp": datetime.utcnow().isoformat()}
        )
        db.add(audit)
        db.commit()

action_gateway = DeterministicActionGateway()
