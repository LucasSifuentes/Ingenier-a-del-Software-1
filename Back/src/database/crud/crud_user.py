from sqlalchemy.orm import Session
from src.database import models
from src.schemas import user_schemas

def create_user(db: Session, user_info: user_schemas.UserCreateSchema):
    # Crea un nuevo usuario en la base de datos
    db_user = models.User(
        user_name=user_info.user_name,
        birthday=user_info.birthday,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int):
    # Obtiene un usuario de la base de datos por su user_id
    return db.query(models.User).filter(models.User.user_id == user_id).first()

