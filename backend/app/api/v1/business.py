from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.integrations.orders import order_adapter
from app.integrations.shipping import shipping_adapter
from app.models.tenant import User
from app.core.security import get_current_user

router = APIRouter(prefix="/business", tags=["Business Systems Inspection"])

@router.get("/orders/{order_number}")
def get_order_state(
    order_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Direct authoritative read from the order management system."""
    order = order_adapter.get_order(db, current_user.organization_id, order_number)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_number} not found")
    
    shipment = shipping_adapter.get_shipment_by_order(db, current_user.organization_id, order.id)
    return {
        "order_number": order.order_number,
        "total_amount": order.total_amount,
        "refunded_amount": order.refunded_amount,
        "status": order.status.value,
        "customer_id": order.customer_id,
        "shipment": {
            "tracking_number": shipment.tracking_number if shipment else None,
            "carrier": shipment.carrier if shipment else None,
            "status": shipment.status if shipment else None,
            "destination": shipment.destination_city if shipment else None
        } if shipment else None
    }

@router.get("/shipments/{tracking_number}")
def get_shipment_state(
    tracking_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Direct authoritative carrier lookup."""
    shipment = shipping_adapter.get_shipment_by_tracking(db, current_user.organization_id, tracking_number)
    if not shipment:
        raise HTTPException(status_code=404, detail=f"Shipment {tracking_number} not found")
    return {
        "tracking_number": shipment.tracking_number,
        "carrier": shipment.carrier,
        "status": shipment.status,
        "destination_city": shipment.destination_city
    }
