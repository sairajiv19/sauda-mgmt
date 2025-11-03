import random
import uuid
import datetime
from bson import ObjectId
from pymongo import MongoClient

# -------------------------------
# MongoDB Connection Setup
# -------------------------------
# Adjust the connection string as per your environment
client = MongoClient("mongodb://localhost:27017/")
db = client["sauda"]
lot_collection = db["lot"]

# -------------------------------
# Sample Sauda Data (reference)
# -------------------------------
saudas = [
    {"_id": {"$oid": "69065670aa1839e1d4aac509"}, "public_id": "f0d3ade5-2279-4f81-aec8-2d577f9c9a3e", "total_lots": 8},
    {"_id": {"$oid": "69065670aa1839e1d4aac50e"}, "public_id": "75395123-3486-40e7-a397-c41188476006", "total_lots": 6},
    {"_id": {"$oid": "69065670aa1839e1d4aac50f"}, "public_id": "8504eebf-32b8-4926-9a09-2f14efe3350b", "total_lots": 7},
    {"_id": {"$oid": "69065670aa1839e1d4aac510"}, "public_id": "fe9fb634-44bb-4fd1-9e4a-5720196e8364", "total_lots": 6},
    {"_id": {"$oid": "69065670aa1839e1d4aac511"}, "public_id": "1ee44209-3156-4276-9ac2-c9895cbb1a3e", "total_lots": 6},
]

# -------------------------------
# Helper Generators
# -------------------------------
rice_centres = ["Bilaspur Depot", "Raipur Storage", "Kawardha Godown", "Bhatapara Mill", "Korba Storage"]
shipment_modes = ["Truck", "Tractor", "Mini Van", "Tempo"]

def random_date(start=datetime.date(2025, 10, 1), end=datetime.date(2025, 11, 2)):
    delta = end - start
    random_days = random.randint(0, delta.days)
    return datetime.datetime.combine(start + datetime.timedelta(days=random_days), datetime.datetime.min.time())

def random_shipment():
    return [{
        "vehicle_no": f"CG-{random.randint(4,30)}-{random.randint(1000,9999)}",
        "driver_name": random.choice(["Ravi", "Suresh", "Vikas", "Ajay", "Manoj"]),
        "gate_pass_no": f"GP-{random.randint(1000,9999)}",
        "bora_sent": random.randint(20, 80),
        "date": random_date()
    } for _ in range(random.randint(0, 2))]

def random_frk_bheja():
    return {
        "frk_via": random.choice(shipment_modes),
        "frk_qty": round(random.uniform(0.5, 3.0), 2),
        "frk_date": random_date()
    }

# -------------------------------
# Main Data Generation
# -------------------------------
all_lots = []
frk_bheja_count = 0
MAX_FRK_BHEJA = 10  # only 10 lots will have frk_bheja info

for sauda in saudas:
    for i in range(sauda["total_lots"]):
        frk_status = random.choice([True, False])

        # Assign FRK Bheja only if FRK is True and we haven't reached max limit
        frk_bheja = None
        if frk_status and frk_bheja_count < MAX_FRK_BHEJA and random.random() > 0.5:
            frk_bheja = random_frk_bheja()
            frk_bheja_count += 1

        lot = {
            "_id": ObjectId(),
            "public_id": str(uuid.uuid4()),
            "sauda_id": sauda["public_id"],
            "rice_lot_no": f"RL-{random.randint(1000,9999)}" if random.random() > 0.3 else None,
            "frk": frk_status,
            "frk_bheja": frk_bheja,
            "shipment_details": random_shipment(),
            "total_bora_count": random.randint(50, 150),
            "shipped_bora_count": random.choice([None, random.randint(0, 150)]),
            "remaining_bora_count": random.choice([None, random.randint(0, 150)]),
            "is_fully_shipped": random.choice([True, False]),
            "rice_pass_date": random.choice([random_date(), None]),
            "rice_deposit_centre": random.choice(rice_centres + [None]),
            "qtl": round(random.uniform(10, 90), 2),
            "rice_bags_quantity": random.randint(20, 100),
            "moisture_cut": round(random.uniform(0, 2), 2),
            "net_rice_bought": round(random.uniform(10, 90), 2),
            "qi_expense": round(random.uniform(100, 500), 2),
            "lot_dalali_expense": round(random.uniform(100, 300), 2),
            "other_expenses": round(random.uniform(50, 200), 2),
            "brokerage": 3.0,
            "nett_amount": None if random.random() > 0.6 else round(random.uniform(10000, 50000), 2),
            "created_at": datetime.datetime.now(datetime.UTC),
            "updated_at": datetime.datetime.now(datetime.UTC),
        }

        all_lots.append(lot)

# -------------------------------
# Insert into MongoDB
# -------------------------------
if all_lots:
    result = lot_collection.insert_many(all_lots)
    print(f"✅ Inserted {len(result.inserted_ids)} lots into 'sauda.lot' collection.")
    print(f"✅ FRK Bheja applied to {frk_bheja_count} lots.")
else:
    print("⚠️ No lots generated.")
