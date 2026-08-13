from datetime import datetime
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

class Base(DeclarativeBase):
    """Classe base da qual todos os modelos irão herdar."""
    metadata = MetaData(naming_convention=convention)

class TimestampMixin:
    """Mixin para adicionar campos de auditoria automaticamente nas tabelas que dele herdarem."""
    criado_em: Mapped[datetime] = mapped_column(server_default=func.now())
    actualizado_em: Mapped[datetime] = mapped_column(
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=True
    )