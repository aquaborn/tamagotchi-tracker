from sqlalchemy import Column, Integer, BigInteger, DateTime, Boolean, String, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class PetModel(Base):
    __tablename__ = "pets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, unique=True, index=True)  # telegram_id пользователя
    
    # === Базовые статы ===
    hunger = Column(Integer, default=100)
    energy = Column(Integer, default=100)
    happiness = Column(Integer, default=100)
    hygiene = Column(Integer, default=100)
    health = Column(Integer, default=100)
    discipline = Column(Integer, default=50)
    is_sick = Column(Boolean, default=False)
    is_sleeping = Column(Boolean, default=False)
    light_off = Column(Boolean, default=False)
    last_tick_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # === Прокачка ===
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    
    # === Генетика и NFT ===
    pet_type = Column(String(32), default="cat")  # cat, dog, fox, dragon, etc
    rarity = Column(String(16), default="common")  # common, uncommon, rare, epic, legendary, mythic
    generation = Column(Integer, default=0)  # 0 = оригинал, 1+ = потомки
    
    # Гены (JSON): {"color": "orange", "pattern": "stripes", "eyes": "blue", "trait1": "fast", ...}
    genes = Column(JSON, default={})
    
    # Родители (для родословной)
    parent1_id = Column(Integer, nullable=True)  # ID первого родителя
    parent2_id = Column(Integer, nullable=True)  # ID второго родителя
    
    # Breeding
    breeding_count = Column(Integer, default=0)  # Сколько раз размножался
    breeding_cooldown_until = Column(DateTime(timezone=True), nullable=True)  # Когда можно снова
    
    # NFT
    nft_minted = Column(Boolean, default=False)
    nft_address = Column(String(128), nullable=True)  # TON NFT address
    nft_minted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Редкие трейты (мутации)
    mutations = Column(JSON, default=[])  # ["золотой блеск", "крылья"]
    
    # Бонусы от генов
    stat_multiplier = Column(Float, default=1.0)  # Множитель XP/токенов
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())