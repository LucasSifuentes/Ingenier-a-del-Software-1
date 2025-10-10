from pydantic import BaseModel
from datetime import date

# Esquema para crear un nuevo usuario (recibimos la información de front)
class UserCreateSchema(BaseModel):
    user_name: str
    birthday: date

# Esquema para representar un usuario ya creado (lo que el bacK devuelve)
class UserSchema(UserCreateSchema):
    user_id: int
    
    class Config:
        from_attributes = True