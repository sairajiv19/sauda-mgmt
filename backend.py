from fastapi import FastAPI
from pymongo.asynchronous.mongo_client import AsyncMongoClient
from models import SaudaModel, SaudaStatus, FRKBhejaModel, LotModel, BrokerModel


app = FastAPI()

async def lifespan():
    try:
        client = AsyncMongoClient()
    finally:
        await client.close()