from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.integrations.base import BaseIntegrationAdapter
from app.models.business_entities import Shipment

class ShippingAdapter(BaseIntegrationAdapter):
    """Authoritative adapter for carrier tracking and shipment upgrades."""

    @property
    def system_name(self) -> str:
        return "carrier_shipping_system"

    def get_shipment_by_order(self, db: Session, organization_id: str, order_id: str) -> Optional[Shipment]:
        return db.query(Shipment).filter(
            Shipment.organization_id == organization_id,
            Shipment.order_id == order_id
        ).first()

    def get_shipment_by_tracking(self, db: Session, organization_id: str, tracking_number: str) -> Optional[Shipment]:
        return db.query(Shipment).filter(
            Shipment.organization_id == organization_id,
            Shipment.tracking_number == tracking_number
        ).first()

shipping_adapter = ShippingAdapter()
