# Pydantic models for request/response validation and serialization.
from pydantic import BaseModel

# Request body model for the login endpoint.
# Pydantic automatically validates that both fields are present and are strings.
class LoginRequest(BaseModel):
    username: str
    password: str
