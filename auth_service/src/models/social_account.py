from sqlalchemy import Column, String, ForeignKey, BigInteger, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.db.postgres import Base # Импортируйте вашу базовую модель

class SocialAccount(Base):
    __tablename__ = "social_accounts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    social_id = Column(String(255), nullable=False)
    provider = Column(String(50), nullable=False)

    user = relationship("User", back_populates="social_accounts")

    __table_args__ = (
        UniqueConstraint("social_id", "provider", name="uq_social_provider"),
    )

# В вашей модели User (предположительно в src/models/user.py) нужно добавить обратную связь:
# class User(Base):
#     ...
#     social_accounts = relationship("SocialAccount", back_populates="user", cascade="all, delete-orphan")
#     ...
