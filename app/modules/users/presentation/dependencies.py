from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.users.infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from app.modules.users.application.usecases.create_user import CreateUserUseCase
from app.modules.users.application.usecases.get_user import GetUserUseCase
from app.modules.users.application.usecases.update_user import UpdateUserUseCase
from app.modules.users.application.usecases.list_users import ListUsersUseCase

def get_user_repository(db: Session = Depends(get_db)):
    return SQLAlchemyUserRepository(db)

def get_create_user_usecase(repo: SQLAlchemyUserRepository = Depends(get_user_repository)):
    return CreateUserUseCase(repo)

def get_get_user_usecase(repo: SQLAlchemyUserRepository = Depends(get_user_repository)):
    return GetUserUseCase(repo)

def get_update_user_usecase(repo: SQLAlchemyUserRepository = Depends(get_user_repository)):
    return UpdateUserUseCase(repo)

def get_list_users_usecase(repo: SQLAlchemyUserRepository = Depends(get_user_repository)):
    return ListUsersUseCase(repo)
