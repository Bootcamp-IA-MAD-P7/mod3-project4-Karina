from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone
from db.session import get_db
from db.models import User, Subscription, Video
from auth.jwt import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register", status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email ya registrado")

    user = User(email=data.email, hashed_password=hash_password(data.password), name=data.name)
    db.add(user)
    db.flush()
    db.add(Subscription(user_id=user.id))  # plan free por defecto
    db.commit()
    return {"message": "Usuario creado", "user_id": user.id}


@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    return TokenResponse(access_token=create_access_token(user.id, user.email))


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "email": current_user.email, "name": current_user.name, "role": current_user.role}


PLAN_LIMITS = {"free": 3, "pro": None, "agency": None}


@router.get("/plan")
def plan(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    plan_name = current_user.subscription.plan.value if current_user.subscription else "free"
    limit = PLAN_LIMITS.get(plan_name)
    now = datetime.now(timezone.utc)
    used = db.query(Video).filter(
        Video.user_id == current_user.id,
        Video.uploaded_at >= now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    ).count()
    return {
        "plan": plan_name,
        "videos_este_mes": used,
        "limite_mensual": limit if limit is not None else "ilimitado",
        "restantes": (limit - used) if limit is not None else "ilimitado"
    }
