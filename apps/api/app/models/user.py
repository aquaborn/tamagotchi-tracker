from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.pet import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    language = Column(String(10), default="ru")  # User's preferred language
    
    # Pet selection
    pet_type = Column(String(50), default=None)  # Selected pet ID (kitty, labubu, etc.)
    pet_selected_at = Column(DateTime(timezone=True), nullable=True)  # When pet was selected
    owned_pets = Column(String(1024), default="")  # Comma-separated list of owned pet IDs
    stars_balance = Column(Integer, default=0)  # Telegram Stars balance
    
    # Реферальная система
    referral_code = Column(String(32), unique=True, index=True)
    referred_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    referral_count = Column(Integer, default=0)
    
    # Уровень и опыт
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    
    # Стрик
    streak_days = Column(Integer, default=0)
    last_activity_date = Column(DateTime(timezone=True), nullable=True)
    
    # VPN баланс (в часах)
    vpn_hours_balance = Column(Integer, default=0)
    
    # Бочка - накопительная система покупок
    barrel_progress = Column(Integer, default=0)  # Прогресс 0-100
    barrel_completions = Column(Integer, default=0)  # Сколько раз заполнили бочку
    total_purchases = Column(Integer, default=0)  # Всего покупок
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_support_request = Column(DateTime(timezone=True), nullable=True)  # For support cooldown
    
    # Relationships
    referred_by = relationship("User", remote_side=[id], backref="referrals")
    vpn_configs = relationship("VPNConfig", back_populates="user")


class VPNConfig(Base):
    __tablename__ = "vpn_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Конфиг
    config_data = Column(String(4096), nullable=False)  # JSON или base64
    config_type = Column(String(50), default="xray")  # xray, wireguard, etc.
    
    # Время действия
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Причина выдачи
    reward_type = Column(String(50))  # referral, level_up, streak, happy_pet, achievement
    reward_description = Column(String(255))
    
    # Relationships
    user = relationship("User", back_populates="vpn_configs")


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    achievement_type = Column(String(50), nullable=False)  # first_feed, streak_7, level_10, etc.
    unlocked_at = Column(DateTime(timezone=True), server_default=func.now())
    reward_claimed = Column(Boolean, default=False)
