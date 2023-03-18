import re
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


PG_DSN = 'postgresql+asyncpg://artur:8114@127.0.0.1:5431/my_db'
engine = create_async_engine(PG_DSN)
Session = sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

BaseModel = declarative_base()


class Announcement(BaseModel):
    __tablename__ = 'announcement'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    creation_time = Column(DateTime, server_default=func.now()) 
    email = Column(String)

