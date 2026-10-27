from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base, SessionLocal
from app.models.tenant import Organization, User, UserRole
from app.models.workflow import Task, TaskStatus, ActionProposal, ProposalStatus, Approval, ApprovalStatus
from app.models.business_entities import Customer, Order, OrderStatus, Shipment
from app.models.conversation import Conversation, ConversationStatus, Message, MessageSender
from app.models.audit import AuditEvent, AuditEventType
from app.core.security import get_password_hash
from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.approvals import router as approvals_router
from app.api.v1.audit import router as audit_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.business import router as business_router
from app.api.v1.workflows import router as workflows_router
from app.api.v1.gateway import router as gateway_router
from app.api.v1.outcomes import router as outcomes_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        demo_org = db.query(Organization).filter(Organization.id == "org_acme_global_01").first()
        if not demo_org:
            demo_org = Organization(id="org_acme_global_01", name="Acme Global Operations", slug="acme-global", is_active=True)
            db.add(demo_org)
            db.commit()

        demo_user = db.query(User).filter(User.id == "usr_alex_dunhill_01").first()
        if not demo_user:
            demo_user = User(
                id="usr_alex_dunhill_01",
                organization_id="org_acme_global_01",
                email="admin@nexus.ai",
                hashed_password=get_password_hash("NexusAdmin2026!"),
                full_name="Alex Dunhill",
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(demo_user)
            db.commit()

        demo_customer = db.query(Customer).filter(Customer.id == "cust_marcus_vance_01").first()
        if not demo_customer:
            demo_customer = Customer(
                id="cust_marcus_vance_01",
                organization_id="org_acme_global_01",
                name="Marcus Vance",
                email="marcus.vance@example.com",
                phone="+1-555-019-2831"
            )
            db.add(demo_customer)
            db.commit()

        demo_order = db.query(Order).filter(Order.id == "ord_4491_v1").first()
        if not demo_order:
            demo_order = Order(
                id="ord_4491_v1",
                organization_id="org_acme_global_01",
                customer_id="cust_marcus_vance_01",
                order_number="ORD-4491",
                total_amount=149.99,
                currency="USD",
                status=OrderStatus.DELAYED
            )
            db.add(demo_order)
            db.commit()

        demo_shipment = db.query(Shipment).filter(Shipment.id == "shp_9928172901").first()
        if not demo_shipment:
            demo_shipment = Shipment(
                id="shp_9928172901",
                organization_id="org_acme_global_01",
                order_id="ord_4491_v1",
                tracking_number="TRK-9928172901",
                carrier="FedEx Express",
                status="delayed_severe_weather",
                destination_city="Seattle, WA"
            )
            db.add(demo_shipment)
            db.commit()

        primary_task = db.query(Task).filter(Task.id == "tsk_982e01df").first()
        if not primary_task:
            primary_task = Task(
                id="tsk_982e01df",
                organization_id="org_acme_global_01",
                customer_id="cust_marcus_vance_01",
                title="Resolve Delayed Order #ORD-4491",
                description="Customer Marcus Vance reported shipment delayed by 5 days. Investigated: carrier weather delay. Policy allows up to $50 goodwill credit. Proposing $35 partial refund.",
                status=TaskStatus.AWAITING_APPROVAL,
                priority="high",
                workflow_type="delayed_order_resolution",
                meta={"order_number": "ORD-4491", "delay_days": 5}
            )
            db.add(primary_task)
            db.commit()

        proposal = db.query(ActionProposal).filter(ActionProposal.id == "prp_stripe_refund_35").first()
        if not proposal:
            proposal = ActionProposal(
                id="prp_stripe_refund_35",
                organization_id="org_acme_global_01",
                task_id="tsk_982e01df",
                action_type="stripe_partial_refund",
                target_entity="order:ORD-4491",
                payload={"amount": 35.00, "currency": "USD", "reason": "goodwill_delay_credit"},
                idempotency_key="idemp_refund_ord_4491_v1",
                requires_human_approval=True,
                status=ProposalStatus.PENDING
            )
            db.add(proposal)
            db.commit()

            approval = Approval(
                id="appr_gate_refund_35",
                organization_id="org_acme_global_01",
                action_proposal_id="prp_stripe_refund_35",
                status=ApprovalStatus.PENDING,
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            db.add(approval)
            db.commit()

        demo_convo = db.query(Conversation).filter(Conversation.id == "cnv_marcus_vance_01").first()
        if not demo_convo:
            demo_convo = Conversation(
                id="cnv_marcus_vance_01",
                organization_id="org_acme_global_01",
                customer_id="cust_marcus_vance_01",
                task_id="tsk_982e01df",
                status=ConversationStatus.INVESTIGATING,
                channel="customer_portal"
            )
            db.add(demo_convo)
            db.commit()

            msg1 = Message(
                id="msg_01_user_delay",
                organization_id="org_acme_global_01",
                conversation_id="cnv_marcus_vance_01",
                sender=MessageSender.CUSTOMER,
                content="My order is delayed. Please resolve it."
            )
            msg2 = Message(
                id="msg_02_agent_investigate",
                organization_id="org_acme_global_01",
                conversation_id="cnv_marcus_vance_01",
                sender=MessageSender.AGENT,
                content="I'm investigating order #ORD-4491 right now. Our Operations Agent confirmed a severe weather delay with FedEx in Seattle. I've prepared a $35 goodwill credit resolution and routed it for quick supervisor approval."
            )
            db.add_all([msg1, msg2])
            db.commit()

    finally:
        db.close()

    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Deterministic Multi-Agent Teammate Platform API with Two-Phase Policy Gateway and Read-Back Proof.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(approvals_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")
app.include_router(conversations_router, prefix="/api/v1")
app.include_router(business_router, prefix="/api/v1")
app.include_router(workflows_router, prefix="/api/v1")
app.include_router(gateway_router, prefix="/api/v1")
app.include_router(outcomes_router, prefix="/api/v1")

@app.get("/")
def root():
    return {
        "platform": settings.PROJECT_NAME,
        "status": "online",
        "docs_url": "/docs"
    }
