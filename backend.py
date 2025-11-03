from fastapi import FastAPI, HTTPException
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from pymongo.asynchronous.mongo_client import AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection
from models import SaudaModel, SaudaStatus, FRKBhejaModel, LotModel, BrokerModel
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR
from pydantic import BaseModel, Field
from typing import Optional, List
import datetime
from bson import ObjectId
import uvicorn
from contextlib import asynccontextmanager


# Input Models
class BrokerInput(BaseModel):
    public_id: str = Field(..., description="Public IDs.")
    name: str = Field(..., description="Broker name")
    broker_id: str = Field(..., description="Broker ID.")

class SaudaInput(BaseModel):
    name: str = Field(..., description="Sauda/deal name")
    broker_id: str = Field(..., description="The id of the broker in the system.")
    party_name: str = Field(..., description="Party or firm name")
    purchase_date: datetime.datetime = Field(..., description="Sauda date")
    total_lots: int = Field(..., ge=0, description="Total number of lots")
    rate: float = Field(..., gt=0, description="Rate per bora/product")
    rice_type: Optional[str] = Field(default=None, description="Type of rice and Agreement")
    rice_agreement: Optional[str] = Field(default=None, description="Agreement number")

class ShipmentInput(BaseModel):
    public_id: str = Field(..., description="Public IDs.")
    lot_id: str = Field(..., description="Reference to Lot")
    sent_bora_count: int = Field(..., ge=0, description="Total bora sent")
    bora_date: Optional[datetime.datetime] = Field(None, description="Shipping date")
    bora_via: Optional[str] = Field(None, description="Shipping method/vehicle")
    flap_sticker_date: Optional[datetime.datetime] = Field(None, description="Flap sticker date")
    flap_sticker_via: Optional[str] = Field(None, description="Sticker batch info")
    gate_pass_date: Optional[datetime.datetime] = Field(None, description="Gate pass issue date")
    gate_pass_via: Optional[str] = Field(None, description="Gate pass location")

class LotUpdate(BaseModel):
    public_id: str = Field(..., description="Public IDs.")
    rice_lot_no: Optional[str] = Field(default=None, description="Rice lot number")
    frk: bool = Field(default=False, description="FRK status")
    frk_bheja: Optional[FRKBhejaModel] = Field(None, description="FRK shipment details")
    total_bora_count: Optional[int] = Field(default=0, ge=0, description="No. of Boras in a Lot.")
    rice_pass_date: Optional[datetime.datetime] = Field(None, description="Rice pass date")
    rice_deposit_centre: Optional[str] = Field(None, description="Storage/deposit location")
    qtl: float = Field(default=0, ge=0, description="Quantity in quintals")
    rice_bags_quantity: int = Field(default=0, ge=0, description="Number of bags")
    moisture_cut: float = Field(default=0, ge=0, description="Moisture cut amount")
    net_rice_bought: float = Field(default=0, ge=0, description="Net rice quantity bought")
    qi_expense: float = Field(default=0, ge=0, description="QI expense")
    lot_dalali_expense: float = Field(default=0, ge=0, description="Dalali/commission expense")
    other_expenses: float = Field(default=0, ge=0, description="Other miscellaneous costs")
    brokerage: float = Field(default=3.00, ge=0, description="Brokerage fees")

class BatchLotUpdate(BaseModel):
    public_lot_ids: List[str]
    update_data: LotUpdate


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        mongodb_client = AsyncMongoClient("mongodb://localhost:27017/",
                                        connect=True,
                                        maxConnecting=5,
                                        maxPoolSize=150,
                                        minPoolSize=8,)
        sauda_database = mongodb_client.get_database("sauda")
        app.state.deal_collection = sauda_database.get_collection("deal")
        app.state.lot_collection = sauda_database.get_collection("lot")
        app.state.shipment_collection = sauda_database.get_collection("shipment")
        app.state.broker_collection = sauda_database.get_collection("broker")
        print("Connected to MongoDB!")
        yield
    finally:
        await mongodb_client.close()
        print("Disconnected from MongoDB.")

app = FastAPI(lifespan=lifespan)

# Read Routes
@app.get("/deals/read/all")
async def get_all_deals(req: Request) -> JSONResponse:
    deals = await req.app.state.deal_collection.find({}, projection={"_id": False, "end_at": False, "created_at": False, "updated_at": False}).to_list() # This one is right change all of them to this
    for deal in deals:
        deal['purchase_date'] = str(deal['purchase_date'])
    return JSONResponse(content={"response": deals}, status_code=HTTP_200_OK)

@app.get("/brokers/read/all")
async def get_all_brokers(req: Request) -> JSONResponse:
    brokers =  await req.app.state.broker_collection.find({}, projection={"_id": False, "created_at": False, "updated_at": False}).to_list()
    return JSONResponse({"response": brokers}, status_code=HTTP_200_OK)

@app.get("/deals/read/{deal_id}/lot/all") # For generating boxes
async def get_all_deal_lots(req: Request, public_deal_id: str) -> JSONResponse:    
    lots = await req.app.state.lot_collection.find({"sauda_id": public_deal_id}, projection={"_id": False, "public_id": True, "rice_lot_no": True, "is_fully_shipped": True}).to_list() # waht all fields needed
    return JSONResponse(content={"response": lots}, status_code=HTTP_200_OK)

@app.get("/deals/read/{deal_id}/lot/{lot_id}")
async def get_lot_details(req: Request, public_deal_id: str, public_lot_id: str) -> JSONResponse:
    lot = await req.app.state.lot_collection.find_one({"sauda_id": public_deal_id, "public_id": public_lot_id}, projection={"_id": False, "created_at": False, "updated_at": False}).to_list()
    if not lot:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Lot not found")
    if lot["frk"]:
        lot['frk_bheja']['frk_date'] = str(lot['frk_bheja']['frk_date'])
    return JSONResponse(content={"response": lot}, status_code=HTTP_200_OK)


# Create Routes
@app.post("/deals/create/")
async def create_deal(req: Request, deal: SaudaInput) -> JSONResponse:    
    # broker = await req.app.state.broker_collection.find_one({"broker_id": deal.broker_id})
    # if not broker:
    #     raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"Broker with id {deal.broker_id} not found")

    new_sauda = SaudaModel(deal.model_dump())
    inserted_deal = await req.app.state.deal_collection.insert_one(new_sauda.model_dump(by_alias=True))
    
    # Create empty lots
    lots_to_create = []
    for _ in range(deal.total_lots):
        new_lot = LotModel(sauda_id=inserted_deal.inserted_id)
        lots_to_create.append(new_lot.model_dump(by_alias=True))
    
    if lots_to_create:
        req.app.database["lot"].insert_many(lots_to_create)

    # Update broker's sauda_ids
    req.app.database["broker"].update_one(
        {"_id": broker["_id"]},
        {"$push": {"sauda_ids": inserted_deal.inserted_id}}
    )

    return JSONResponse(
        content={"message": "Deal created successfully!", "deal_id": str(inserted_deal.inserted_id)},
        status_code=HTTP_201_CREATED
    )

@app.post("/brokers/create/")
async def create_broker(req: Request, broker: BrokerInput) -> JSONResponse:
    broker_data = broker.model_dump()
    
    if req.app.database["broker"].find_one({"broker_id": broker.broker_id}):
        raise HTTPException(status_code=400, detail="Broker with this ID already exists")

    new_broker = BrokerModel(**broker_data)
    inserted = req.app.database["broker"].insert_one(new_broker.model_dump(by_alias=True))
    
    return JSONResponse(
        content={"message": "Broker created successfully!", "broker_db_id": str(inserted.inserted_id)},
        status_code=HTTP_201_CREATED
    )


# Update Routes
@app.post("/deals/update/{deal_id}")
async def update_deal(req: Request, deal_id: str, deal_update: SaudaInput) -> JSONResponse:
    try:
        deal_object_id = ObjectId(deal_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid deal_id format")

    update_data = {k: v for k, v in deal_update.model_dump().items() if v is not None}
    
    result = req.app.database["deal"].update_one(
        {"_id": deal_object_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Deal not found")

    return JSONResponse(content={"message": "Deal updated successfully!"}, status_code=HTTP_200_OK)

@app.post("/brokers/update/{broker_id}")
async def update_broker(req: Request, broker_id: str, broker_update: BrokerInput) -> JSONResponse:
    update_data = {k: v for k, v in broker_update.model_dump().items() if v is not None}

    result = req.app.database["broker"].update_one(
        {"broker_id": broker_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Broker not found")

    return JSONResponse(content={"message": "Broker updated successfully!"}, status_code=HTTP_200_OK)

@app.patch("/deals/update/{deal_id}/lots/{lot_id}/update")
async def update_single_lot(req: Request, lot_id: str, lot_update: LotUpdate) -> JSONResponse:
    try:
        lot_object_id = ObjectId(lot_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid lot_id format")

    update_data = {k: v for k, v in lot_update.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.datetime.now(datetime.UTC)

    result = req.app.database["lot"].update_one(
        {"_id": lot_object_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Lot not found")

    return JSONResponse(content={"message": "Lot updated successfully!"}, status_code=HTTP_200_OK)

@app.patch("/deals/update/lots/batch-update")
async def update_batch_lot(req: Request, batch_update: BatchLotUpdate) -> JSONResponse:
    lot_ids_object = [ObjectId(id) for id in batch_update.lot_ids]
    update_data = {k: v for k, v in batch_update.update_data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.datetime.now(datetime.UTC)

    result = req.app.database["lot"].update_many(
        {"_id": {"$in": lot_ids_object}},
        {"$set": update_data}
    )

    return JSONResponse(
        content={"message": f"Batch update successful. Matched: {result.matched_count}, Modified: {result.modified_count}"},
        status_code=HTTP_200_OK
    )


# Delete Routes
@app.delete("/deals/{deal_id}")
async def delete_deal(req: Request, deal_id: str) -> JSONResponse:
    try:
        deal_object_id = ObjectId(deal_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid deal_id format")

    # Find the deal to get broker_id
    deal = req.app.database["deal"].find_one({"_id": deal_object_id})
    if not deal:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Deal not found")

    # Delete lots associated with the deal
    req.app.database["lot"].delete_many({"sauda_id": deal_object_id})

    # Remove deal_id from broker's sauda_ids
    req.app.database["broker"].update_one(
        {"broker_id": deal["broker_id"]},
        {"$pull": {"sauda_ids": deal_object_id}}
    )

    # Delete the deal itself
    req.app.database["deal"].delete_one({"_id": deal_object_id})

    return JSONResponse(content={"message": "Deal and associated lots deleted successfully!"}, status_code=HTTP_200_OK)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
