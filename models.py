from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, TypedDict
import datetime
from bson import ObjectId
from enum import Enum
from uuid import uuid4

class SaudaStatus(str, Enum):
    """Sauda status enum"""
    INITIATE_PHASE = "Initialized"
    READY_FOR_PICKUP = "Ready for pickup"
    IN_TRANSPORT = "In transport"
    SHIPPED = "Shipped"
    COMPLETED = "Completed"


def public_id_str():
    return str(uuid4())

class BrokerModel(BaseModel):
    """Broker Collection Model"""
    id: Optional[ObjectId] = Field(default_factory=ObjectId, alias="_id")
    broker_id: str = Field(..., description="User given Broker ID")
    name: str = Field(..., description="Broker name")
    sauda_ids: List[str] = Field(default_factory=list, description="Linked saudas")
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
    updated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))

    model_config=ConfigDict(
        populate_by_name = True,
        arbitrary_types_allowed = True,
        json_encoders = {ObjectId: str},)


class SaudaModel(BaseModel):
    """Sauda (Deal) Collection Model"""
    id: Optional[ObjectId] = Field(default_factory=ObjectId, alias="_id")
    public_id: str = Field(default_factory=public_id_str, description="Public ID.")
    name: str = Field(..., description="Sauda/deal name")
    broker_id: str = Field(..., description="The id of the broker in the system.")
    party_name: str = Field(..., description="Party or firm name")
    purchase_date: datetime.datetime = Field(..., description="Sauda date")
    total_lots: int = Field(..., ge=0, description="Total number of lots")
    rate: float = Field(..., gt=0, description="Rate per bora/product")
    rice_type: Optional[str] = Field(default=None, description="Type of rice and Agreement")
    rice_agreement: Optional[str] = Field(default=None, description="Agreement number")
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
    updated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
    end_at: Optional[datetime.datetime] = Field(None, description="Final date when sauda is complete.")
    status: str = Field(default=SaudaStatus.INITIATE_PHASE.value, description="Status of the sauda.")

    model_config=ConfigDict(
        populate_by_name = True,
        arbitrary_types_allowed = True,
        json_encoders = {ObjectId: str},)


class FRKBhejaModel(TypedDict):
    """FRK Bheja nested model"""
    frk_via: Optional[str]
    frk_qty: Optional[float]
    frk_date: Optional[datetime.datetime]


class ShipmentModel(BaseModel):
    """Lot/Bora Shipment Model"""
    id: Optional[ObjectId] = Field(default_factory=ObjectId, alias="_id")
    public_id: str = Field(default_factory=public_id_str, description="Public ID.")
    lot_id: str = Field(..., description="Reference to public Lot Id")
    sauda_id: str = Field(..., description="Reference to public Sauda Id")
    sent_bora_count: int = Field(..., ge=0, description="Total bora sent")
    bora_date: Optional[datetime.datetime] = Field(None, description="Shipping date")
    bora_via: Optional[str] = Field(None, description="Shipping method/vehicle")
    flap_sticker_date: Optional[datetime.datetime] = Field(None, description="Flap sticker date")
    flap_sticker_via: Optional[str] = Field(None, description="Sticker batch info")
    gate_pass_date: Optional[datetime.datetime] = Field(None, description="Gate pass issue date")
    gate_pass_via: Optional[str] = Field(None, description="Gate pass location")
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
    updated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))

    model_config=ConfigDict(
        populate_by_name = True,
        arbitrary_types_allowed = True,
        json_encoders = {ObjectId: str},)


class LotModel(BaseModel):
    """Lot Collection Model"""
    id: Optional[ObjectId] = Field(default_factory=ObjectId, alias="_id")
    public_id: str = Field(default_factory=public_id_str, description="Public ID.")
    sauda_id: str = Field(..., description="Reference to parent public sauda id")
    rice_lot_no: Optional[str] = Field(default=None, description="Rice lot number")

    # FRK and Gate Pass
    frk: bool = Field(default=False, description="FRK status")
    frk_bheja: Optional[FRKBhejaModel] = Field(None, description="FRK shipment details")
    shipment_details: Optional[List[ShipmentModel]] = Field(default_factory=list)
    total_bora_count: Optional[int] = Field(default=0, ge=0, description="No. of Boras in a Lot.")
    shipped_bora_count: Optional[int] = None
    remaining_bora_count: Optional[int] = None
    is_fully_shipped: bool = Field(default=False, description="Whether the lot is fully shipped or not.")

    # Govt Website Data
    rice_pass_date: Optional[datetime.datetime] = Field(None, description="Rice pass date")
    rice_deposit_centre: Optional[str] = Field(None, description="Storage/deposit location")
    qtl: float = Field(default=0, ge=0, description="Quantity in quintals")
    rice_bags_quantity: int = Field(default=0, ge=0, description="Number of bags")
    moisture_cut: float = Field(default=0, ge=0, description="Moisture cut amount")

    # Purchase Related information
    net_rice_bought: float = Field(default=0, ge=0, description="Net rice quantity bought")
    qi_expense: float = Field(default=0, ge=0, description="QI expense")
    lot_dalali_expense: float = Field(default=0, ge=0, description="Dalali/commission expense")
    other_expenses: float = Field(default=0, ge=0, description="Other miscellaneous costs")
    brokerage: float = Field(default=3.00, ge=0, description="Brokerage fees")
    nett_amount: Optional[float] = Field(None, description="Computed total amount")

    # Tracking fields
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
    updated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))

    model_config=ConfigDict(
        populate_by_name = True,
        arbitrary_types_allowed = True,
        json_encoders = {ObjectId: str},)

