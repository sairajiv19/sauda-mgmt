from pydantic import BaseModel, Field
from typing import Optional, List
import datetime
from bson import ObjectId
from enum import Enum


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class SaudaStatus(str, Enum):
    """Sauda status enum"""
    INITIATE_PHASE = "Initialized"
    UNKNOWN = "Unknown"
    READY_FOR_PICKUP = "Ready for pickup"
    IN_TRANSPORT = "In transport"
    SHIPPED = "Shipped"


class BrokerModel(BaseModel):
    """Broker Collection Model"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(..., description="Broker name")
    sauda_ids: List[PyObjectId] = Field(default_factory=list, description="Linked deals")
    created_at: datetime = Field(default_factory=datetime.datetime.now(datetime.UTC))
    updated_at: datetime = Field(default_factory=datetime.datetime.now(datetime.UTC))

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "name": "Ramesh Trading Co.",
                "party_name": "Sharma Exports",
                "sauda_ids": [],
            }
        }


class SaudaModel(BaseModel):
    """Sauda (Deal) Collection Model"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(..., description="Sauda/deal name")
    broker_id: PyObjectId = Field(..., description="The id of the broker in the system.")
    party_name: str = Field(..., description="Party or firm name")
    date: datetime = Field(..., description="Deal date")
    total_lots: int = Field(..., ge=0, description="Total number of lots")
    rate: float = Field(..., gt=0, description="Rate per quintal/ton")
    # list_of_lot_id: List[PyObjectId] = Field(default_factory=list, description="Lots under this deal")
    created_at: datetime = Field(default_factory=datetime.datetime.now(datetime.UTC))
    end_at:datetime = Field(None, description="Final date when sauda is complete.")
    status: str = Field(default=SaudaStatus.INITIATE_PHASE, description="Status of the sauda.")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "name": "Deal 2025-01",
                "date": "2025-10-27T00:00:00Z",
                "total_lots": 3,
                "rate": 2450.50,
                "list_of_lot_id": [],
            }
        }


class FRKBhejaModel(BaseModel):
    """FRK Bheja nested model"""
    via: str = Field(..., description="Transport method")
    qty: float = Field(..., gt=0, description="Quantity sent")


class LotModel(BaseModel):
    """Lot Collection Model (Merged Purchase + Cost)"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    sauda_id: PyObjectId = Field(..., description="Reference to parent sauda")
    rice_lot_no: Optional[str] = Field(..., default=None,  description="Rice lot number")
    rice_agreement: Optional[str] = Field(..., default=None, description="Agreement number")
    rice_type: Optional[str] = Field(..., default=None, description="Type of rice")
    
    # FRK and Gate Pass
    frk: bool = Field(default=False, description="FRK status")
    frk_bheja: Optional[FRKBhejaModel] = Field(None, description="FRK shipment details")
    frk_bheja_date: Optional[datetime.datetime] = Field(None, description="FRK shipment date")
    gate_pass_date: Optional[datetime.datetime] = Field(None, description="Gate pass issue date")
    gate_pass_via: Optional[str] = Field(None, description="Gate pass location")
    
    # Purchase + Cost merged fields
    rice_pass_date: Optional[datetime.datetime] = Field(None, description="Rice pass date")
    rice_deposit_centre: Optional[str] = Field(None, description="Storage/deposit location")
    qtl: float = Field(..., gt=0, description="Quantity in quintals")
    rice_bags_quantity: int = Field(..., ge=0, description="Number of bags")
    net_rice_bought: float = Field(..., gt=0, description="Net rice quantity bought")
    moisture_cut: float = Field(default=0, ge=0, description="Moisture cut amount")
    qi_expense: float = Field(default=0, ge=0, description="QI expense")
    lot_dalali_expense: float = Field(default=0, ge=0, description="Dalali/commission expense")
    other_costs: float = Field(default=0, ge=0, description="Other miscellaneous costs")
    brokerage: float = Field(default=0, ge=0, description="Brokerage fees")
    nett_amount: Optional[float] = Field(None, description="Computed total amount")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "sauda_id": "507f1f77bcf86cd799439011",
                "rice_lot_no": "RICE-2025-002",
                "rice_agreement": "AGR-4567",
                "rice_type": "Basmati",
                "frk": True,
                "frk_bheja": {"via": "Truck", "qty": 50},
                "qtl": 150.25,
                "rice_bags_quantity": 300,
                "net_rice_bought": 148.0,
                "moisture_cut": 2.25,
                "nett_amount": 367000,
            }
        }


class ProductModel(BaseModel):
    """Product Collection Model"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    lot_id: PyObjectId = Field(..., description="Reference to Lot")
    total_count: int = Field(..., ge=0, description="Total product count")
    shipping_date: Optional[datetime.datetime] = Field(None, description="Shipping date")
    shipped_via: Optional[str] = Field(None, description="Shipping method/vehicle")
    flap_sticker_t_date: Optional[datetime.datetime] = Field(None, description="Flap sticker date")
    flap_sticker_t_via: Optional[str] = Field(None, description="Sticker batch info")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "lot_id": "507f1f77bcf86cd799439011",
                "total_count": 280,
                "shipping_date": "2025-10-23T00:00:00Z",
                "shipped_via": "Truck - CG07AB1234",
                "flap_sticker_t_date": "2025-10-24T00:00:00Z",
                "flap_sticker_t_via": "Sticker Batch #32",
            }
        }