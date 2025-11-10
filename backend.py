from fastapi import FastAPI, HTTPException
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from pymongo.asynchronous.mongo_client import AsyncMongoClient
from models import SaudaModel, SaudaStatus, FRKBhejaModel, LotModel, BrokerModel, ShipmentModel
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from pydantic import BaseModel, Field
from typing import Optional, List
import datetime
import uvicorn
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import asyncio


# Input Models
class BrokerInput(BaseModel):
    name: str = Field(..., description="Broker name")
    broker_id: str = Field(..., description="Broker ID.")


class BrokerUpdate(BaseModel):
    name: Optional[str] = Field(default=None, description="Broker name")
    broker_id: Optional[str] = Field(default=None, description="Broker ID.")


class SaudaInput(BaseModel):
    name: str = Field(..., description="Sauda/deal name")
    broker_id: str = Field(..., description="The id of the broker in the system.")
    party_name: str = Field(..., description="Party or firm name")
    purchase_date: datetime.datetime = Field(..., description="Sauda date")
    total_lots: int = Field(..., ge=0, description="Total number of lots")
    rate: float = Field(..., gt=0, description="Rate per bora/product")
    rice_type: Optional[str] = Field(
        default=None, description="Type of rice and Agreement"
    )
    rice_agreement: Optional[str] = Field(default=None, description="Agreement number")


class SaudaUpdate(BaseModel):
    name: Optional[str] = Field(default=None, description="Sauda/deal name")
    broker_id: Optional[str] = Field(
        default=None, description="The id of the broker in the system."
    )
    party_name: Optional[str] = Field(default=None, description="Party or firm name")
    purchase_date: Optional[datetime.datetime] = Field(
        default=None, description="Sauda date"
    )
    total_lots: Optional[int] = Field(
        default=None, ge=0, description="Total number of lots"
    )
    rate: Optional[float] = Field(
        default=None, gt=0, description="Rate per bora/product"
    )
    rice_type: Optional[str] = Field(
        default=None, description="Type of rice and Agreement"
    )
    rice_agreement: Optional[str] = Field(default=None, description="Agreement number")
    updated_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC)
    )


class ShipmentInput(BaseModel):
    public_id: str = Field(..., description="Public IDs.")
    lot_id: str = Field(..., description="Reference to Lot")
    sent_bora_count: int = Field(..., ge=0, description="Total bora sent")
    bora_date: Optional[datetime.datetime] = Field(None, description="Shipping date")
    bora_via: Optional[str] = Field(None, description="Shipping method/vehicle")
    flap_sticker_date: Optional[datetime.datetime] = Field(
        None, description="Flap sticker date"
    )
    flap_sticker_via: Optional[str] = Field(None, description="Sticker batch info")
    gate_pass_date: Optional[datetime.datetime] = Field(
        None, description="Gate pass issue date"
    )
    gate_pass_via: Optional[str] = Field(None, description="Gate pass location")


class LotUpdate(BaseModel):
    rice_lot_no: Optional[str] = Field(default=None, description="Rice lot number")
    frk: Optional[bool] = Field(default=False, description="FRK status")
    frk_bheja: Optional[FRKBhejaModel] = Field(
        default=None, description="FRK shipment details"
    )
    total_bora_count: Optional[int] = Field(
        default=None, ge=0, description="No. of Boras in a Lot."
    )
    rice_pass_date: Optional[datetime.datetime] = Field(
        default=None, description="Rice pass date"
    )
    rice_deposit_centre: Optional[str] = Field(
        default=None, description="Storage/deposit location"
    )
    qtl: Optional[float] = Field(default=None, ge=0, description="Quantity in quintals")
    rice_bags_quantity: int = Field(default=None, ge=0, description="Number of bags")
    moisture_cut: Optional[float] = Field(
        default=None, ge=0, description="Moisture cut amount"
    )
    net_rice_bought: Optional[float] = Field(
        default=None, ge=0, description="Net rice quantity bought"
    )
    qi_expense: Optional[float] = Field(default=None, ge=0, description="QI expense")
    lot_dalali_expense: Optional[float] = Field(
        default=None, ge=0, description="Dalali/commission expense"
    )
    other_expenses: Optional[float] = Field(
        default=None, ge=0, description="Other miscellaneous costs"
    )
    brokerage: Optional[float] = Field(default=None, ge=0, description="Brokerage fees")


class BatchLotUpdate(BaseModel):
    public_lot_ids: List[str]
    update_data: LotUpdate


class DeliveryUpdate(BaseModel):
    rice_lot_no: str
    rice_pass_date: Optional[datetime.datetime] = Field(None, description="Rice pass date")
    rice_deposit_centre: Optional[str] = Field(None, description="Storage/deposit location")
    qtl: float = Field(default=0, ge=0, description="Quantity in quintals")
    rice_bags_quantity: int = Field(default=0, ge=0, description="Number of bags")
    moisture_cut: float = Field(default=0, ge=0, description="Moisture cut amount")


class BatchDeliveryUpdate(BaseModel):
    data: List[DeliveryUpdate]


class StatusUpdate(BaseModel):
    status: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        mongodb_client = AsyncMongoClient(
            "mongodb://localhost:27017/",
            connect=True,
            maxConnecting=5,
            maxPoolSize=150,
            minPoolSize=8,
        )
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or specify ["http://localhost:3000"] etc.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Read Routes - Done
@app.get("/deals/read/all")
async def get_all_deals(req: Request) -> JSONResponse:
    deals = await req.app.state.deal_collection.find(
        {},
        projection={
            "_id": False,
            "end_at": False,
            "created_at": False,
            "updated_at": False,
        },
    ).to_list()
    for deal in deals:
        deal["purchase_date"] = str(deal["purchase_date"])
    return JSONResponse(content={"response": deals}, status_code=HTTP_200_OK)


@app.get("/deals/read/{public_lot_id}")
async def get_single_deal(req: Request, public_lot_id: str) -> JSONResponse:
    deal = await req.app.state.deal_collection.find_one(
        {"public_id": public_lot_id},
        projection={
            "_id": False,
            "end_at": False,
            "created_at": False,
            "updated_at": False,
        },
    )
    deal["purchase_date"] = str(deal["purchase_date"])
    return JSONResponse(content={"response": deal}, status_code=HTTP_200_OK)


@app.get("/brokers/read/all")
async def get_all_brokers(req: Request) -> JSONResponse:
    brokers = await req.app.state.broker_collection.find(
        {}, projection={"_id": False, "created_at": False, "updated_at": False}
    ).to_list()
    return JSONResponse({"response": brokers}, status_code=HTTP_200_OK)


@app.get("/deals/read/{public_deal_id}/lot/all")  # For generating boxes
async def get_all_deal_lots(req: Request, public_deal_id: str) -> JSONResponse:
    lots = await req.app.state.lot_collection.find(
        {"sauda_id": public_deal_id},
        projection={
            "_id": False,
            "public_id": True,
            "rice_lot_no": True,
            "is_fully_shipped": True,
            "remaining_bora_count": True,
            "total_bora_count": True,
            "qi_expense": True,
            "lot_dalali_expense": True,
            "other_expenses": True,
            "brokerage": True,
            "nett_amount": True,
            "net_rice_bought": True
        },
    ).to_list()
    return JSONResponse(content={"response": lots}, status_code=HTTP_200_OK)


@app.get("/deals/read/{public_deal_id}/lot/{public_lot_id}")
async def get_lot_details(
    req: Request, public_deal_id: str, public_lot_id: str
) -> JSONResponse: # Bug fix - shipment details error
    lot = await req.app.state.lot_collection.find_one(
        {"sauda_id": public_deal_id, "public_id": public_lot_id},
        projection={"_id": False, "created_at": False, "updated_at": False}, 
    )
    if not lot:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Lot not found")
    if lot["rice_pass_date"]:
        lot["rice_pass_date"] = str(lot["rice_pass_date"])
    if lot["frk"]:
        if lot["frk_bheja"]:
                if lot["frk_bheja"]["frk_date"]:
                    lot["frk_bheja"]["frk_date"] = str(lot["frk_bheja"]["frk_date"])
    return JSONResponse(content={"response": lot}, status_code=HTTP_200_OK)


# Create Routes - Done
@app.post("/deals/create/")
async def create_deal(req: Request, deal: SaudaInput) -> JSONResponse:
    # broker = await req.app.state.broker_collection.find_one({"broker_id": deal.broker_id})
    # if not broker:
    #     raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"Broker with id {deal.broker_id} not found")

    new_sauda = SaudaModel(**deal.model_dump())
    try:
        inserted_deal = await req.app.state.deal_collection.insert_one(
            new_sauda.model_dump(by_alias=True)
        )
    except Exception:
        return JSONResponse(
            content={
                "message": "Failed creating new deal.",
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        )
    # Create empty lots
    lots_to_create = []
    for i in range(deal.total_lots):
        new_lot = LotModel(sauda_id=new_sauda.public_id)
        new_lot.rice_lot_no = f"Lot {i+1}"
        lots_to_create.append(new_lot.model_dump(by_alias=True))

    try:
        await req.app.state.lot_collection.insert_many(lots_to_create)
    except Exception:
        return JSONResponse(
            content={
                "message": "Failed creating new lots.",
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Update broker's sauda_ids
    await req.app.state.broker_collection.update_one(
        {"broker_id": deal.broker_id}, {"$push": {"sauda_ids": new_sauda.public_id}}
    )

    return JSONResponse(
        content={
            "message": "Deal created successfully!",
            "public_deal_id": str(new_sauda.public_id),
        },
        status_code=HTTP_201_CREATED,
    )


@app.post("/brokers/create/")
async def create_broker(req: Request, broker: BrokerInput) -> JSONResponse:
    if await req.app.state.broker_collection.find_one({"broker_id": broker.broker_id}):
        raise HTTPException(
            status_code=400, detail="Broker with this ID already exists"
        )

    new_broker = BrokerModel(**broker.model_dump())
    inserted = await req.app.state.broker_collection.insert_one(
        new_broker.model_dump(by_alias=True)
    )

    return JSONResponse(
        content={
            "message": "Broker created successfully!",
            "broker_id": broker.broker_id,
        },
        status_code=HTTP_201_CREATED,
    )


# Update Routes - Done
@app.post("/deals/update/{public_deal_id}")
async def update_deal(
    req: Request, public_deal_id: str, deal_update: SaudaUpdate
) -> JSONResponse:
    db_data = await req.app.state.deal_collection.find_one(
        {"public_id": public_deal_id}, projection={"_id": True, "public_id": True}
    )
    if db_data is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Deal does not exist."
        )
    update_data = {k: v for k, v in deal_update.model_dump().items() if v is not None}
    try:
        await req.app.state.deal_collection.update_one(
            {"_id": db_data["_id"]}, {"$set": update_data}, upsert=False
        )
    except Exception:
        raise HTTPException(
            HTTP_500_INTERNAL_SERVER_ERROR, "Cannot update the deal, mongodb error."
        )
    return JSONResponse(
        content={"message": "Deal updated successfully!"}, status_code=HTTP_200_OK
    )


@app.post("/brokers/update/{broker_id}")
async def update_broker(
    req: Request, broker_id: str, broker_update: BrokerUpdate
) -> JSONResponse:
    db_data = await req.app.state.broker_collection.find_one(
        {"broker_id": broker_id}, projection={"_id": True, "broker_id": True}
    )
    if db_data is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Broker does not exist."
        )
    update_data = {k: v for k, v in broker_update.model_dump().items() if v is not None}
    try:
        await req.app.state.broker_collection.update_one(
            {"_id": db_data["_id"]}, {"$set": update_data}, upsert=False
        )
    except Exception:
        raise HTTPException(
            HTTP_500_INTERNAL_SERVER_ERROR, "Cannot update the broker, mongodb error."
        )

    return JSONResponse(
        content={"message": "Broker updated successfully!"}, status_code=HTTP_200_OK
    )


@app.patch("/deals/update/{public_deal_id}/lots/{public_lot_id}/update")
async def update_single_lot(
    req: Request, public_deal_id: str, public_lot_id: str, lot_update: LotUpdate
) -> JSONResponse:
    lot = await req.app.state.lot_collection.find_one(
        {"sauda_id": public_deal_id, "public_id": public_lot_id},
        projection={"_id": True},
    )
    if not lot:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Lot not found")
    update_data = {k: v for k, v in lot_update.model_dump().items() if v is not None}
    if update_data['total_bora_count']: # Revisit this logic.
        update_data["remaining_bora_count"] = update_data["total_bora_count"]
    update_data["updated_at"] = datetime.datetime.now(datetime.UTC)

    try:
        await req.app.state.lot_collection.update_one(
            {"_id": lot["_id"]}, {"$set": update_data}
        )
    except Exception:
        raise HTTPException(
            HTTP_500_INTERNAL_SERVER_ERROR, "Cannot update the deal, mongodb error."
        )
    return JSONResponse(
        content={"message": "Lot updated successfully!"}, status_code=HTTP_200_OK
    )


@app.patch("/deals/update/{public_deal_id}/lots/batch-update")
async def update_batch_lot(
    req: Request, public_deal_id: str, batch_update: BatchLotUpdate
) -> JSONResponse:
    cursor = req.app.state.lot_collection.find(
        {"sauda_id": public_deal_id, "public_id": {"$in": batch_update.public_lot_ids}},
        projection={"_id": True, "public_id": True},
    )
    lots = []
    async for lot in cursor:
        lots.append(lot)
    if len(lots) != len(batch_update.public_lot_ids):
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Some lots are missing / don't exist. FATAL ERROR",
        )
    update_data = {
        k: v for k, v in batch_update.update_data.model_dump().items() if v is not None
    }
    if update_data.get("total_bora_count", False):
        update_data["remaining_bora_count"] = update_data["total_bora_count"]
        await req.app.state.shipment_collection.delete_many({"lot_id": {"$in": [lot["public_id"] for lot in lots]}}) # Deleting shipments that were created with old total count to maintain data integrity.
    update_data["updated_at"] = datetime.datetime.now(datetime.UTC)

    try:

        result = await req.app.state.lot_collection.update_many(
            {"_id": {"$in": [lot["_id"] for lot in lots]}},
            {"$set": update_data},
            upsert=False,
        )
    except Exception:
        raise HTTPException(
            HTTP_500_INTERNAL_SERVER_ERROR, "Cannot update the deals, mongodb error."
        )

    return JSONResponse(
        content={
            "message": f"Batch lot update successful. Modified Lots Count: {result.modified_count}"
        },
        status_code=HTTP_200_OK,
    )


@app.patch("/deals/update/{public_id}/status")
async def update_deal_status(req: Request, public_id: str, request: StatusUpdate)-> JSONResponse:
    """Update sauda status"""
    await req.app.state.deal_collection.update_one(
        {"public_id": public_id},
        {"$set": {"status": request.status, "updated_at": datetime.datetime.now(datetime.UTC)}}
    )
    return JSONResponse(content={"public_id": public_id, "status": request.status}, status_code=HTTP_200_OK)


# Delete Routes
@app.delete("/deals/delete/{public_deal_id}")
async def delete_deal(req: Request, public_deal_id: str) -> JSONResponse:
    # Find the deal to get broker_id
    deal = await req.app.state.deal_collection.find_one(
        {"public_id": public_deal_id}, projection={"_id": True, "broker_id": True}
    )
    if not deal:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Deal not found")

    # Delete lots associated with the deal
    await req.app.state.lot_collection.delete_many({"sauda_id": public_deal_id})

    # Remove deal_id from broker's sauda_ids
    await req.app.state.broker_collection.update_one(
        {"broker_id": deal["broker_id"]}, {"$pull": {"sauda_ids": public_deal_id}}
    )

    # Delete related shipments
    await req.app.state.shipment_collection.delete_many({"sauda_id": public_deal_id})

    # Delete the deal itself
    await req.app.state.deal_collection.delete_one({"_id": deal["_id"]})

    return JSONResponse(
        content={"message": "Deal and associated lots deleted successfully!"},
        status_code=HTTP_200_OK,
    )


# Shipment Crud 

class ShipmentInput(BaseModel):
    """Input model for creating a shipment"""
    sent_bora_count: int = Field(..., ge=0, description="Total bora sent")
    bora_date: Optional[datetime.datetime] = Field(None, description="Shipping date")
    bora_via: Optional[str] = Field(None, description="Shipping method/vehicle")
    flap_sticker_date: Optional[datetime.datetime] = Field(None, description="Flap sticker date")
    flap_sticker_via: Optional[str] = Field(None, description="Sticker batch info")
    gate_pass_date: Optional[datetime.datetime] = Field(None, description="Gate pass issue date")
    gate_pass_via: Optional[str] = Field(None, description="Gate pass location")


class ShipmentUpdate(BaseModel):
    """Update model for updating a shipment"""
    sent_bora_count: Optional[int] = Field(None, ge=0, description="Total bora sent")
    bora_date: Optional[datetime.datetime] = Field(None, description="Shipping date")
    bora_via: Optional[str] = Field(None, description="Shipping method/vehicle")
    flap_sticker_date: Optional[datetime.datetime] = Field(None, description="Flap sticker date")
    flap_sticker_via: Optional[str] = Field(None, description="Sticker batch info")
    gate_pass_date: Optional[datetime.datetime] = Field(None, description="Gate pass issue date")
    gate_pass_via: Optional[str] = Field(None, description="Gate pass location")


class BatchShipmentInput(BaseModel):
    public_ids: List[str]
    data: ShipmentInput


class BatchShipmentUpdate(BaseModel):
    public_ids: List[str]
    update: ShipmentUpdate



# Create - Done
@app.post("/deals/{public_deal_id}/lots/{public_lot_id}/shipment/create")
async def create_shipment(req: Request, public_deal_id: str, public_lot_id: str, shipment_data: ShipmentInput) -> JSONResponse:

    data = ShipmentModel(sauda_id=public_deal_id, lot_id=public_lot_id, **shipment_data.model_dump())
    try:
        await req.app.state.shipment_collection.insert_one(data.model_dump(by_alias=True))
        up_res = await req.app.state.lot_collection.update_one(
            {"public_id": public_lot_id},
            [
                {
                    "$set": {
                        "remaining_bora_count": {
                            "$subtract": ["$remaining_bora_count", data.sent_bora_count]
                        },
                        "shipment_details": {
                            "$concatArrays": ["$shipment_details", [data.public_id]]
                        }
                    }
                }
            ]
        )
        await req.app.state.deal_collection.update_one(
        {"public_id": public_deal_id},
        {"$set": {"status": SaudaStatus.IN_TRANSPORT.value, "updated_at": datetime.datetime.now(datetime.UTC)}}
        )
        return JSONResponse(content={"message": "Shipment created successfully and lot updated."})
    except Exception as e:
        raise e

@app.post("/deals/{public_deal_id}/lots/shipment/create-batch")
async def create_shipment_batch(req: Request, public_deal_id: str, batch_insert: BatchShipmentInput) -> JSONResponse:
    n, public_ids, data = len(batch_insert.public_ids), batch_insert.public_ids, batch_insert.data.model_dump(by_alias=True)
    data_objs = []
    for i in range(n):
        data_objs.append(ShipmentModel(sauda_id=public_deal_id, lot_id=public_ids[i], **data).model_dump(by_alias=True))
    tasks = []
    for shipment in data_objs:
        tasks.append(req.app.state.lot_collection.update_one(
                {"public_id": shipment['lot_id']},
                [
                    {
                        "$set": {
                            "remaining_bora_count": {
                                "$subtract": ["$remaining_bora_count", data["sent_bora_count"]]
                            },
                            "shipment_details": {
                                "$concatArrays": ["$shipment_details", [shipment["public_id"]]]
                            }
                        }
                    }
                ]
            )
        )   
    try:
        await req.app.state.shipment_collection.insert_many(data_objs)
        await asyncio.gather(*tasks)
        await req.app.state.deal_collection.update_one(
        {"public_id": public_deal_id},
        {"$set": {"status": SaudaStatus.IN_TRANSPORT.value, "updated_at": datetime.datetime.now(datetime.UTC)}}
        )
        return JSONResponse(content={"message": "Shipment created successfully and lot updated."})
    except Exception as e:
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail="Error batch updating shipment.")
    
# Read 
@app.post("/deals/{public_deal_id}/lots/{public_lot_id}/shipment/{public_shipment_id}/read") # Exact Shipment
async def read_sinlge_shipment(req: Request, public_deal_id: str, public_lot_id: str, public_shipment_id: str) -> JSONResponse:
    try:
        result = await req.app.state.shipment_collection.find_one({"public_id": public_shipment_id},
                                                                  projection = {"_id": False, "created_at": False, "updated_at": False})
        result2 = await req.app.state.lot_collection.find_one({"public_id": result['lot_id']}, {'_id': False, 'rice_lot_no': True, "total_bora_count": True, "shipped_bora_count": True, "remaining_bora_count": True})
        if result['bora_date']:
            result['bora_date'] = str(result['bora_date'])
        if result['flap_sticker_date']:
            result['flap_sticker_date'] = str(result['flap_sticker_date'])
        if result['gate_pass_date']:
            result['gate_pass_date'] = str(result['gate_pass_date'])
        final = result | result2
        return JSONResponse(content={"response": final},
                            status_code=HTTP_200_OK)
    except Exception as e:
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail="Error reading a single shipment detail.")
    
@app.post("/deals/{public_deal_id}/lots/{public_lot_id}/shipment/read-lot")
async def read_all_lot_shipments(req: Request, public_deal_id: str, public_lot_id: str) -> JSONResponse: # Read all the shipments for a `LOT`
    try:
        results = req.app.state.shipment_collection.find({"sauda_id": public_deal_id, "lot_id": public_lot_id},
                                                                  projection = {"_id": False, "created_at": False, "updated_at": False})
        final_result = []
        async for result in results:
            result2 = await req.app.state.lot_collection.find_one({"public_id": result['lot_id']}, {'_id': False, 'rice_lot_no': True, "total_bora_count": True, "shipped_bora_count": True, "remaining_bora_count": True})
            if result['bora_date']:
                result['bora_date'] = str(result['bora_date'])
            if result['flap_sticker_date']:
                result['flap_sticker_date'] = str(result['flap_sticker_date'])
            if result['gate_pass_date']:
                result['gate_pass_date'] = str(result['gate_pass_date'])
            final_result.append(result | result2)
        return JSONResponse(content={"response": final_result}, 
                            status_code=HTTP_200_OK)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail="Error reading a single shipment detail.")


@app.get("/deals/{public_deal_id}/lots/shipment/read-deal") # Read all shipments for a `SAUDA`
async def read_all_deal_shipments(req: Request, public_deal_id: str) -> JSONResponse:
    # try:
        results = req.app.state.shipment_collection.find({"sauda_id": public_deal_id},
                                                                  projection = {"_id": False, "created_at": False, "updated_at": False})
        final_result = []
        async for result in results:
            result2 = await req.app.state.lot_collection.find_one({"public_id": result['lot_id']}, {'_id': False, 'rice_lot_no': True, "total_bora_count": True, "shipped_bora_count": True, "remaining_bora_count": True})
            if result.get('bora_date', False):
                result['bora_date'] = str(result['bora_date'])
            if result.get('flap_sticker_date', False):
                result['flap_sticker_date'] = str(result['flap_sticker_date'])
            if result.get("gate_pass_date", False):
                result['gate_pass_date'] = str(result['gate_pass_date'])
            final_result.append(result | result2)
        print(final_result)
        return JSONResponse(content={"response": final_result}, 
                            status_code=HTTP_200_OK)
    # except Exception:
    #     raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail="Error reading a all shipment detail.")
    
# Update - Done
@app.patch("/deals/lots/shipment/{public_shipment_id}/update") # Single Shipment details update.
async def update_single_shipment(req: Request, public_shipment_id: str, data: ShipmentUpdate) -> JSONResponse:
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    try:
        res = await req.app.state.shipment_collection.update_one({"public_id": public_shipment_id},
                                                           {"$set": update_data})
        # if res["matched_count"] != 1:
        #     raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail="Error updating the lot details with shipment data.")
        return JSONResponse(content={"message": "Shipment Data updated successfully."}, status_code=HTTP_200_OK)
    except Exception as e:
        raise e


@app.patch("/deals/lots/shipment/update/batch-update") # Per Lot Shipment Updates
async def update_multiple_shipments(req: Request, data: BatchShipmentUpdate)->JSONResponse:
    update_data = {k: v for k, v in data.update.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.datetime.now(datetime.UTC)
    try:
        result = await req.app.state.shipment_collection.update_many(
            {"public_id": {"$in": data.public_ids}},
            {"$set": update_data},
            upsert=False,
        )
        # if result['modified_count'] != len(data.public_ids):
        #     raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail="Error updating multiple shipment data.")
        return JSONResponse(content={"message": "Shipment created successfully and lot updated."})
    except Exception as e:
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail="Error batch updating shipment.")


# Delete - Done
@app.delete("/deals/{public_deal_id}/lots/{public_lot_id}/shipment/{public_shipment_id}/delete")
async def delete_shipment(req: Request, public_deal_id: str, public_lot_id: str, public_shipment_id: str) -> JSONResponse:
    try:
        b_count = await req.app.state.shipment_collection.find_one({"public_id": public_shipment_id, "lot_id": public_lot_id,}, projection={"_id": True, "sent_bora_count": True})
        print(b_count)
        await req.app.state.shipment_collection.delete_one({"public_id": public_shipment_id, "lot_id": public_lot_id, "sauda_id": public_deal_id})
        await req.app.state.lot_collection.update_one({"public_id": public_lot_id}, {"$pull": {"shipment_details": public_lot_id}, "$inc": {"remaining_bora_count": b_count['sent_bora_count']}})
        return JSONResponse(content={"message": "Shipment details deleted successfully."}, status_code=HTTP_200_OK)
    except Exception:
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to delete shipment details.")
    

# Delivery Status logic - need to implement shipment details like change bora counts
@app.patch("/deals/update/lots/update-delivery-details")
async def update_delivery_details(
    req: Request, batch_update: BatchDeliveryUpdate
) -> JSONResponse:
    try:
        rice_lot_nos = [d.rice_lot_no for d in batch_update.data]
        lots_cursor = req.app.state.lot_collection.find(
            {"rice_lot_no": {"$in": rice_lot_nos}},
            projection={"public_id": True, "sauda_id": True, "rice_lot_no": True}
        )
        lots_map = {lot["rice_lot_no"]: lot async for lot in lots_cursor}

        update_tasks = []
        for d in batch_update.data:
            if d.rice_lot_no in lots_map:
                update_tasks.append(req.app.state.lot_collection.update_one(
                    {"rice_lot_no": d.rice_lot_no},
                    {"$set": {"rice_pass_date": d.rice_pass_date, "rice_deposit_centre": d.rice_deposit_centre, "qtl": d.qtl, "rice_bags_quantity": d.rice_bags_quantity, "moisture_cut": d.moisture_cut, "is_fully_shipped": True, "updated_at": datetime.datetime.now(datetime.UTC)}}
                ))
        
        if len(update_tasks) != len(batch_update.data):
             raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Some lots were not parsed / found properly. FATAL ERROR",
            )

        await asyncio.gather(*update_tasks)

        # calculation_tasks = []
        # for d in batch_update.data:
        #     if d.rice_lot_no in lots_map:
        #         lot_info = lots_map[d.rice_lot_no]
        #         calculation_tasks.append(
        #             calculate_lot_nett_amount(lot_info["sauda_id"], lot_info["public_id"], req)
        #         )
        
        # await asyncio.gather(*calculation_tasks)

        return JSONResponse(
            content={
                "message": f"Batch Delivery Status Update Successful!"
            },
            status_code=HTTP_200_OK,
        )
    except Exception:
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail="Cannot update delivery status.")
 

class CostEstimate(BaseModel):
    qi_expense: Optional[float]
    lot_dalali_expense: Optional[float]
    other_expenses: Optional[float]
    brokerage: Optional[float]

class BatchCostEstimate(BaseModel):
    public_lot_ids: List[str]
    update: CostEstimate


 
# TODO: Finish this one function
async def calculate_lot_nett_amount(rate: float, total_bora_count: int, moisture_cut: float, qi_expense: float, lot_dalali_expense: float, other_expenses: float, brokerage: float) -> float:
    gross_amount = total_bora_count * rate

    total_expenses = qi_expense + lot_dalali_expense + other_expenses + brokerage + moisture_cut
    
    nett_amount = gross_amount - total_expenses
    
    return nett_amount



@app.post("http://localhost:8000/deals/{public_deal_id}/lots/cost-estimation")
async def batch_cost_estimate_lot(req: Request, public_deal_id: str, data: BatchCostEstimate) -> JSONResponse:
    sauda_details = await req.app.state.deal_collection.find_one({"public_id": public_deal_id}, projection={"_id": False, "rate": True})
    rate = sauda_details['rate']
    cursor = req.app.state.lot_collection.find({"public_id": {"$in": data.public_lot_ids}}, projection={"_id": True, "total_bora_count": True, "moisture_cut": True, "qi_expense": True, "lot_dalali_expense": True, "other_expenses": True, "brokerage": True})
    tasks = []
    async for lot in cursor:
        nett_amount = calculate_lot_nett_amount(
            rate, lot.get("total_bora_count"), lot.get("moisture_cut", 0), lot.get("qi_expense", 0), lot.get("lot_dalali_expense", 0), lot.get("other_expenses", 0), lot.get("brokerage", 0)
        )
        tasks.append(req.app.state.lot_collection.update_one(
            {"_id": lot['_id']},
            {"$set": {"nett_amount": nett_amount}}
        ))
    try:
        results = asyncio.gather(*tasks)
    except Exception as e:
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail="Error calculating Nett amount.")