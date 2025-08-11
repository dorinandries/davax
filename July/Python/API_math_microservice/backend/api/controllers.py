from fastapi import APIRouter
from pydantic import BaseModel, Field
from services.math_service import MathService
from db.database import Database
import asyncio
from core.kafka_logger import KafkaLogger
from config.settings import Settings

router = APIRouter()
settings = Settings()


kafka_logger = KafkaLogger(
    topic=settings.kafka_topic,
    bootstrap_servers=settings.kafka_bootstrap_servers
)


# Request and response models
class PowRequest(BaseModel):
    x: float = Field(..., description="Base")
    y: float = Field(..., description="Exponent")


class FiboRequest(BaseModel):
    n: int = Field(..., ge=0, description="Fibonacci index (n ≥ 0)")


class FactRequest(BaseModel):
    n: int = Field(..., ge=0, description="Factorial argument (n ≥ 0)")


class ResultResponse(BaseModel):
    operation: str
    input: dict
    result: float | int


# Instantiate service and database objects
math_service = MathService()
db = Database()


@router.post("/putere", response_model=ResultResponse)
async def putere_endpoint(req: PowRequest):
    payload = req.model_dump()
    existing = db.get_existing_request("pow", payload)
    if existing is not None:
        return ResultResponse(operation="pow", input=payload, result=float(existing))

    result = await asyncio.to_thread(math_service.pow, req.x, req.y)
    db.save_request("pow", payload, result)
    kafka_logger.log({
        "operation": "pow",
        "input": payload,
        "result": result
    })
    return ResultResponse(operation="pow", input=payload, result=result)

@router.post("/fibo", response_model=ResultResponse)
async def fibo_endpoint(req: FiboRequest):
    payload = req.model_dump()
    existing = db.get_existing_request("fibo", payload)
    if existing is not None:
        return ResultResponse(operation="fibo", input=payload, result=int(existing))

    result = await asyncio.to_thread(math_service.fibo, req.n)
    db.save_request("fibo", payload, result)
    kafka_logger.log({
        "operation": "fibonacci",
        "input": payload,
        "result": result
    })
    return ResultResponse(operation="fibo", input=payload, result=result)

@router.post("/factorial", response_model=ResultResponse)
async def fact_endpoint(req: FactRequest):
    payload = req.model_dump()
    existing = db.get_existing_request("factorial", payload)
    if existing is not None:
        return ResultResponse(operation="factorial", input=payload, result=int(existing))

    result = await asyncio.to_thread(math_service.factorial, req.n)
    db.save_request("factorial", payload, result)
    kafka_logger.log({
        "operation": "factorial",
        "input": payload,
        "result": result
    })
    return ResultResponse(operation="factorial", input=payload, result=result)


@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.delete("/clear")
def clear_database():
    db.clear_requests()
    return {"message": "'requests' table has been emptied"}
