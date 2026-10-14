from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

    full_name: str = Field(
        min_length=2,
        max_length=150,
    )

    phone: str | None = Field(
        default=None,
        max_length=30,
    )

    address: str | None = Field(
        default=None,
        max_length=500,
    )


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: str
    is_active: bool

    model_config = {
        "from_attributes": True
    }