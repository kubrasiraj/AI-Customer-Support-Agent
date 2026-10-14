from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest
from app.models.customer import Customer

def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:
    """Find a user by email address."""

    return (
        db.query(User)
        .filter(User.email == email)
        .first()
    )


def register_user(db: Session, data: RegisterRequest) -> User:
    """Create a user account and customer profile."""

    existing_user = get_user_by_email(db, data.email)

    if existing_user:
        raise ValueError("Email is already registered")

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
    )

    db.add(user)
    db.flush()

    customer = Customer(
        user_id=user.id,
        full_name=data.full_name,
        phone=data.phone,
        address=data.address,
    )

    db.add(customer)

    db.commit()
    db.refresh(user)

    return user


def authenticate_user(
    db: Session,
    data: LoginRequest,
) -> User:
    """Authenticate a user using email and password."""

    user = get_user_by_email(
        db,
        data.email,
    )

    if not user:
        raise ValueError("Invalid email or password")

    if not verify_password(
        data.password,
        user.hashed_password,
    ):
        raise ValueError("Invalid email or password")

    if not user.is_active:
        raise ValueError("User account is inactive")

    return user


def create_user_token(user: User) -> str:
    """Create a JWT access token for a user."""

    token_data = {
        "sub": str(user.id),
        "email": user.email,
    }

    return create_access_token(token_data)