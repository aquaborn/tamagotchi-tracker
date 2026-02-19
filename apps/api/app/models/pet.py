from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class PetModel(Base):
    __tablename__ = "pets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True)
    hunger = Column(Integer, default=100)
    energy = Column(Integer, default=100)
    happiness = Column(Integer, default=100)
    last_tick_at = Column(DateTime(timezone=True), default=func.now())