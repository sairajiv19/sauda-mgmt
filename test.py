import datetime
import uuid
import asyncio
import random
from bson import ObjectId
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from pymongo.asynchronous.mongo_client import AsyncMongoClient


# ---------- Helper ----------
def public_id_str() -> str:
    return str(uuid.uuid4())


# ---------- FRK Bheja Model ----------
class FRKBhejaModel(BaseModel):
    bheja_date: Optional[datetime.datetime] = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
    bheja_via: Optional[str] = None
    bheja_bora_count: Optional[int] = 0


# ---------- Lot Model ----------
class LotModel(BaseModel):
    """Lot Collection Model"""
    id: Optional[ObjectId] = Field(default_factory=ObjectId, alias="_id")
    public_id: str = Field(default_factory=public_id_str)
    sauda_id: str
    rice_lot_no: Optional[str] = None

    frk: bool = False
    frk_bheja: Optional[FRKBhejaModel] = None
    shipment_details: Optional[List[dict]] = Field(default_factory=list)

    total_bora_count: Optional[int] = 0
    shipped_bora_count: Optional[int] = None
    remaining_bora_count: Optional[int] = None
    is_fully_shipped: bool = False

    rice_pass_date: Optional[datetime.datetime] = None
    rice_deposit_centre: Optional[str] = None
    qtl: float = 0
    rice_bags_quantity: int = 0
    moisture_cut: float = 0

    net_rice_bought: float = 0
    qi_expense: float = 0
    lot_dalali_expense: float = 0
    other_expenses: float = 0
    brokerage: float = 3.00
    nett_amount: Optional[float] = None

    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
    updated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC))

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )


# ---------- Saudas in DB ----------
saudas_in_db = [
    {"public_id": "f0d3ade5-2279-4f81-aec8-2d577f9c9a3e", "total_lots": 8},
    {"public_id": "75395123-3486-40e7-a397-c41188476006", "total_lots": 6},
    {"public_id": "8504eebf-32b8-4926-9a09-2f14efe3350b", "total_lots": 7},
    {"public_id": "fe9fb634-44bb-4fd1-9e4a-5720196e8364", "total_lots": 6},
    {"public_id": "1ee44209-3156-4276-9ac2-c9895cbb1a3e", "total_lots": 6},
]


# ---------- Fake Lot Generator ----------
def generate_fake_lots():
    lots = []
    all_lot_count = sum(s["total_lots"] for s in saudas_in_db)

    # Randomly pick 10 lot indices to have FRK details
    frk_lot_indices = set(random.sample(range(all_lot_count), 10))
    current_index = 0

    for sauda in saudas_in_db:
        for _ in range(sauda["total_lots"]):
            # 50% chance to be "mostly empty"
            if random.random() < 0.5:
                lot_data = {
                    "sauda_id": sauda["public_id"],
                }
            else:
                # Partial data
                lot_data = {
                    "sauda_id": sauda["public_id"],
                    "rice_lot_no": f"LOT-{random.randint(1000, 9999)}",
                    "total_bora_count": random.randint(40, 120),
                    "qtl": round(random.uniform(10, 80), 2),
                    "rice_bags_quantity": random.randint(10, 30),
                    "moisture_cut": round(random.uniform(0, 3), 2),
                    "rice_deposit_centre": random.choice(
                        [None, "Central Godown", "Block A Storage", "Rice Depot 2"]
                    ),
                    "brokerage": 3.00,
                }

            # Some lots will include FRK shipment details
            if current_index in frk_lot_indices:
                lot_data["frk"] = True
                lot_data["frk_bheja"] = {
                    "bheja_date": datetime.datetime.now(datetime.UTC)
                    - datetime.timedelta(days=random.randint(1, 10)),
                    "bheja_via": random.choice(["Truck", "Tempo", "Rail"]),
                    "bheja_bora_count": random.randint(5, 20),
                }

            lots.append(LotModel(**lot_data).model_dump(by_alias=True))
            current_index += 1

    return lots


# ---------- Insert into Mongo ----------
async def insert_lots():
    client = AsyncMongoClient("mongodb://localhost:27017/")
    db = client.get_database("sauda")
    lot_collection = db.get_collection("lot")

    lots_data = generate_fake_lots()
    result = await lot_collection.insert_many(lots_data)

    print(f"✅ Inserted {len(result.inserted_ids)} lots into 'lot' collection.")

    await client.close()


# ---------- Run ----------
if __name__ == "__main__":
    asyncio.run(insert_lots())
