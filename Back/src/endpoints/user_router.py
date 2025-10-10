from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database.db import get_db
from src.database.crud import crud_user
from src.schemas import user_schemas

user_router = APIRouter() 

@user_router.post("/register", status_code=status.HTTP_201_CREATED)
def create_user_endpoint(
    user_info: user_schemas.UserCreateSchema, 
    db: Session = Depends(get_db)
):
    """Crea un nuevo usuario."""
    db_user = crud_user.create_user(db=db, user_info=user_info)
    return user_schemas.UserSchema.from_orm(db_user)

@user_router.get("/{user_id}", response_model=user_schemas.UserSchema)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    """Obtiene un usuario por su ID."""
    db_user = crud_user.get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_user