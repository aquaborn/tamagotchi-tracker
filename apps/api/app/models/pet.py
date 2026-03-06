from sqlalchemy import Column, Integer, BigInteger, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class PetModel(Base):
    __tablename__ = "pets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, unique=True, index=True)
    hunger = Column(Integer, default=100)
    energy = Column(Integer, default=100)
    happiness = Column(Integer, default=100)
    hygiene = Column(Integer, default=100)      # Чистота - NEW!
    health = Column(Integer, default=100)       # Здоровье - NEW!
    discipline = Column(Integer, default=50)    # Дисциплина - NEW!
    is_sick = Column(Boolean, default=False)    # Болеет ли
    is_sleeping = Column(Boolean, default=False) # Спит ли
    light_off = Column(Boolean, default=False)   # Выключен ли свет
    last_tick_at = Column(DateTime(timezone=True), server_default=func.now())