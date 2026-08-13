from sqlalchemy.orm import Session
from app.modules.users.domain.repositories.user_repository import IUserRepository
from app.modules.users.domain.entities.user import Utilizador
from app.modules.users.domain.entities.schemas import UserCreate, UserUpdate
import uuid
from typing import List, Optional

class SQLAlchemyUserRepository(IUserRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: uuid.UUID) -> Optional[Utilizador]:
        return self.db.query(Utilizador).filter(Utilizador.id == user_id).first()
        
    def get_by_telefone(self, telefone: str) -> Optional[Utilizador]:
        return self.db.query(Utilizador).filter(Utilizador.telefone == telefone).first()

    def create(self, user: UserCreate) -> Utilizador:
        db_user = Utilizador(**user.model_dump())
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def update(self, user_id: uuid.UUID, user_update: UserUpdate) -> Optional[Utilizador]:
        db_user = self.get_by_id(user_id)
        if db_user:
            update_data = user_update.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_user, key, value)
            self.db.commit()
            self.db.refresh(db_user)
        return db_user

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Utilizador]:
        return self.db.query(Utilizador).offset(skip).limit(limit).all()
