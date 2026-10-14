from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    """Convert a plain password into a secure hash."""
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """Check whether a plain password matches its stored hash."""
    return pwd_context.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(data: dict) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        return payload

    except JWTError:
        raise ValueError("Invalid or expired token")

"""
Function	Purpose
hash_password() : Password ko database mein safely store karne ke liye hash karta hai
verify_password() :	Login ke waqt password verify karta hai
create_access_token() :	Successful login ke baad JWT banata hai
decode_access_token() :	Protected API par JWT verify karta hai
"""