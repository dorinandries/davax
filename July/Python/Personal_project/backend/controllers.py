#controllers.py
import os
import logging
from dotenv import load_dotenv
from fastapi.encoders import jsonable_encoder
from openai import OpenAI
from pydantic import BaseModel, EmailStr, constr
from fastapi import APIRouter, Depends, status, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import SessionLocal, User, RequestLog
import jwt

router = APIRouter()


# Load .env file
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
DEFAULT_EMAIL = os.getenv("DEFAULT_EMAIL")
DATABASE_URL = os.getenv("DATABASE_URL")


# Pydantic schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=6)


class LoginResponse(BaseModel):
    token: str


class UpdateUserRequest(BaseModel):
    userID: str
    role: str | None = None
    experience: str | None = None
    seniority: str | None = None


class UpdateUserResponse(BaseModel):
    message: str
    userID: str


class ClearResponse(BaseModel):
    message: str


class DefaultUserResponse(BaseModel):
    userID: str
    email: EmailStr
    role: str
    experience: str
    seniority: str


class AskRequest(BaseModel):
    persona: str
    user_context: dict
    question: str


class ResultResponse(BaseModel):
    persona: str
    answer: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_jwt_token(user: User) -> str:
    payload = {
        "userID": user.userID,
        "email": user.email,
        "role": user.role,
        "experience": user.experience,
        "seniority": user.seniority,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="User login returns JWT token"
)
async def login(credentials: LoginRequest,
                db: Session = Depends(get_db)):
    email = credentials.email
    password = credentials.password
    logger.info("Attempt login for %s", email)

    user = db.query(User).filter_by(email=email).first()

    if not user or not user.verify_password(password):
        # do not reveal which one failed
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials"
        )

    token = create_jwt_token(user)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"token": token}
    )


@router.post(
    "/update-user",
    response_model=UpdateUserResponse,
    summary="Update user context"
)
async def update_user_context(
    request: UpdateUserRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter_by(userID=request.userID).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if request.role is not None:
        user.role = request.role
    if request.experience is not None:
        user.experience = request.experience
    if request.seniority is not None:
        user.seniority = request.seniority

    db.commit()

    return {
        "message": "User updated",
        "userID": user.userID
    }

@router.post("/clear-user-details")
def clear_user_context(userID: str = Query(...), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(userID=userID).first()

    if not user:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "User-ul nu a fost găsit"}
        )

    user.role = ""
    user.experience = ""
    user.seniority = ""
    db.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"Contextul userului {userID} a fost șters"}
    )


@router.delete(
    "/clear-users",
    response_model=ClearResponse,
    summary="Delete all users"
)
async def clear_users(db: Session = Depends(get_db)):
    try:
        deleted = db.query(User).delete()
        db.commit()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content= ClearResponse(
                        message=f"{deleted} rows deleted from table 'user'"
                    ).model_dump()
        )
    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e)}
        )


@router.get(
    "/user/{user_id}",
    response_model=DefaultUserResponse,
    summary="Get user by userID"
)
async def get_user_by_id(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(userID=user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return DefaultUserResponse(
        userID=user.userID,
        email=user.email,
        role=user.role,
        experience=user.experience,
        seniority=user.seniority
    )

@router.post("/ask",
    response_model=ResultResponse,
    summary="Send a question to OpenAI and log the request"
)
async def ask(req: AskRequest):
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        prompt_path = os.path.join(os.path.dirname(__file__),
                                   "prompts", f"{req.persona}.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            persona_prompt = f.read()

        system_prompt = (f"{persona_prompt}\n\n"
                         f"Context utilizator: {req.user_context}")

        print("\tTrimit request către OpenAI...")
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": req.question}
            ]
        )
        answer = response.choices[0].message.content
        print("\tRăspuns GPT primit")
        with SessionLocal() as db:
            log = RequestLog(persona=req.persona, question=req.question)
            db.add(log)
            db.commit()
        return ResultResponse(persona="GPT", answer=answer)

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"answer": f"[Backend error]: {str(e)}"}
        )


@router.get(
    "/health",
    summary="Health check"
)
async def health_check():
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "ok"}
    )


@router.delete(
    "/clear-requests",
    response_model=ClearResponse,
    summary="Delete all request logs"
)
async def clear_requests(db: Session = Depends(get_db)):
    try:
        deleted = db.query(RequestLog).delete()
        db.commit()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={ClearResponse(
                        message=f"{deleted} rows deleted from table 'requests'"
                        ).model_dump()
            }
        )
    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e)}
        )
