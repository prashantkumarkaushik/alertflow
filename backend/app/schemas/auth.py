from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    team_name: str  # creates a new team on registration


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    is_superuser: bool
    team_id: int

    # from_attributes tells pydantic that you're allowed to read data from object attributes, not just dictionaries
    # Instead of data["email"], it can work with data.email
    model_config = {"from_attributes": True}
