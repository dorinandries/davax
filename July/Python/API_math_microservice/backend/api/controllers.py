import os
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, status, HTTPException, Request
from pydantic import BaseModel, Field, EmailStr
from core.logger import setup_logging
from services.math_service import MathService
from db.database import Database
import asyncio
from core.kafka_logger import KafkaLogger
from config.settings import Settings
from auth.auth import get_current_user
from datetime import datetime, timedelta, timezone
from jose import jwt


router = APIRouter()
settings = Settings()
math_service = MathService()
db = Database()

logger = setup_logging(settings, log_days=1)


load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("JWT_ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 30

kafka_logger = KafkaLogger(
    topic=settings.kafka_topic,
    bootstrap_servers=settings.kafka_bootstrap_servers
)

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    identifier: str  # email or username
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr


class UserIdRequest(BaseModel):
    user_id: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


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


class PrimeRequest(BaseModel):
    n: int = Field(..., ge=2, description="Number to check for primality")


class PrimeResponse(BaseModel):
    operation: str
    input: dict
    is_prime: bool


@router.post("/register", response_model=UserResponse)
def register_user(req: RegisterRequest):
    user = db.register_user(req.username, req.email, req.password)
    if not user:
        logger.info(f"[Users] Register failed for {req.email} (already exists)")
        raise HTTPException(status_code=400, detail="User already exists")
    logger.info(f"[Users] New user created for email = {req.email}")
    return user


@router.post("/login", response_model=TokenResponse)
def login_user(req: LoginRequest):
    user = db.verify_user_password(req.identifier, req.password)
    if not user:
        logger.info(f"[Users] Failed login attempt for {req.identifier}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": user["id"], "exp": expire.timestamp()}
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"[Users] User logged in: {user['email']}")
    logger.info(f"access_token: {token}, token_type bearer")
    return {"access_token": token, "token_type": "bearer"}


@router.post("/user", response_model=UserResponse)
def get_user_by_id(body: UserIdRequest):
    user = db.get_user_by_id(body.user_id)
    if not user:
        logger.info(f"User not found: {body.user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    logger.info(f"User is fetched: {body.user_id}")
    return UserResponse(id=user["id"], username=user["username"], email=user["email"])


@router.delete("/user/{user_id}")
def delete_user_by_id(user_id: str):
    deleted = db.delete_user_by_id(user_id)
    if not deleted:
        logger.info(f"Delete failed for user: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    logger.info(f"User deleted: {user_id}")
    return {"message": f"User {user_id} deleted"}


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


@router.post("/prime", response_model=PrimeResponse)
async def check_prime(
    req: PrimeRequest, request: Request, user_id: str = Depends(get_current_user)
):
    payload = req.model_dump()
    operation = "prime"
    logger.info(f"User {user_id} requested method [/{operation}]")
    # Check for existing request in DB
    existing = db.get_existing_request(operation, payload)
    if existing is not None:
        logger.info(f"Prime request for n={req.n} found in DB.")
        kafka_logger.log({
            "operation": operation,
            "input": payload,
            "result": existing
        })
        # Return as PrimeResponse
        is_prime = existing == "True" or existing is True
        return PrimeResponse(operation=operation, input=payload, is_prime=is_prime)

    # Compute result
    result = await asyncio.to_thread(lambda: math_service.is_prime_service(req.n))
    logger.info(f"Prime request for n={req.n} calculated: {result['is_prime']}")
    kafka_logger.log({
        "operation": operation,
        "input": payload,
        "result": result["is_prime"]
    })

    # Save to DB
    db.save_request(operation, payload, result["is_prime"])

    return PrimeResponse(operation=operation, input=payload, is_prime=result["is_prime"])


@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.delete("/clear/table/{table_name}")
def clear_database(table_name: str):
    db.clear_requests(table_name)
    return {"message": f"'{table_name}' table has been cleared"}
