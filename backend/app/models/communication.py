from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.utils.time import utc_now


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # context_type: inquiry, viewing, application, tenancy, maintenance, general
    context_type = Column(String(50), nullable=False, default="general", index=True)
    context_id = Column(Integer, nullable=True)  # ID of the related application, maintenance ticket, etc.
    status = Column(String(50), nullable=False, default="active", index=True)  # active, archived
    
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    # Relationships
    property = relationship("Property", backref="conversations")
    participants = relationship("ConversationParticipant", backref="conversation", cascade="all, delete-orphan")
    messages = relationship("Message", backref="conversation", cascade="all, delete-orphan", order_by="Message.created_at")


class ConversationParticipant(Base):
    __tablename__ = "conversation_participants"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_in_conversation = Column(String(50), nullable=True)  # tenant, manager, agent, owner, provider
    last_read_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=utc_now)

    user = relationship("User", foreign_keys=[user_id])


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    attachment_url = Column(String(500), nullable=True)
    is_system_event = Column(Boolean, nullable=False, default=False)
    
    created_at = Column(DateTime, nullable=False, default=utc_now, index=True)

    sender = relationship("User", foreign_keys=[sender_id])
