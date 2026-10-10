from typing import List, Optional
from datetime import datetime
from app.utils.time import utc_now
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict

from app.database.database import get_db
from app.config.settings import settings
from app.auth.deps import get_current_user
from app.auth.roles import company_resource_access, require_user, same_company
from app.models.communication import Conversation, ConversationParticipant, Message
from app.models.user import User
from app.models.property import Property
from app.models.notification import Notification
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/communications", tags=["communications"])


class ConversationCreate(BaseModel):
    title: Optional[str] = None
    recipient_id: int
    property_id: Optional[int] = None
    context_type: Optional[str] = "general"
    context_id: Optional[int] = None
    initial_message: str


class MessageCreate(BaseModel):
    content: str
    attachment_url: Optional[str] = None


class MessageOut(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    sender_name: Optional[str] = None
    content: str
    attachment_url: Optional[str]
    is_system_event: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationOut(BaseModel):
    id: int
    title: Optional[str]
    property_id: Optional[int]
    property_name: Optional[str] = None
    context_type: str
    status: str
    updated_at: datetime
    last_message: Optional[str] = None
    unread_count: int = 0
    participants: List[dict] = []

    model_config = ConfigDict(from_attributes=True)


@router.get("/conversations", response_model=List[ConversationOut])
def list_my_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=settings.MAX_PAGE_SIZE),
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    List all conversations the current user is a participant in.
    """
    convos = (
        db.query(Conversation)
        .join(ConversationParticipant)
        .filter(ConversationParticipant.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    out = []
    for c in convos:
        item = ConversationOut.model_validate(c, from_attributes=True)
        if c.property:
            item.property_name = c.property.name
        
        # Latest message
        latest = db.query(Message).filter(Message.conversation_id == c.id).order_by(Message.created_at.desc()).first()
        if latest:
            item.last_message = latest.content
        
        # Participants list
        item.participants = [
            {"user_id": cp.user_id, "name": cp.user.full_name or cp.user.email, "role": cp.user.role}
            for cp in c.participants if cp.user
        ]

        out.append(item)
    return out


@router.post("/conversations", response_model=ConversationOut)
def start_conversation(
    payload: ConversationCreate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Start a conversation between current user and recipient.
    """
    recipient = db.query(User).filter(User.id == payload.recipient_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient user not found")
    if current_user.company_id is not None and not same_company(current_user, recipient):
        raise HTTPException(status_code=404, detail="Recipient user not found")

    property_obj = None
    if payload.property_id is not None:
        property_obj = db.query(Property).filter(Property.id == payload.property_id).first()
        if not property_obj or not company_resource_access(current_user, property_obj):
            raise HTTPException(status_code=404, detail="Property not found")

    title = payload.title or f"Conversation with {recipient.full_name or recipient.email}"
    convo = Conversation(
        title=title,
        property_id=property_obj.id if property_obj else None,
        context_type=payload.context_type or "general",
        context_id=payload.context_id,
        status="active"
    )
    db.add(convo)
    db.commit()
    db.refresh(convo)

    # Add participants
    p1 = ConversationParticipant(conversation_id=convo.id, user_id=current_user.id, role_in_conversation=current_user.role, last_read_at=utc_now())
    p2 = ConversationParticipant(conversation_id=convo.id, user_id=recipient.id, role_in_conversation=recipient.role)
    db.add_all([p1, p2])

    # Add initial message
    msg = Message(
        conversation_id=convo.id,
        sender_id=current_user.id,
        content=payload.initial_message,
        is_system_event=False
    )
    db.add(msg)
    db.commit()

    # Notify recipient
    notif = Notification(
        recipient_id=recipient.id,
        notification_type="MESSAGE",
        title="New Message Received",
        message=f"{current_user.full_name or current_user.email}: {payload.initial_message[:100]}",
        priority="NORMAL",
        related_entity_type="CONVERSATION",
        related_entity_id=convo.id,
    )
    db.add(notif)
    db.commit()

    log_audit_event(db, current_user.id, "START_CONVERSATION", "conversation", convo.id)

    res = ConversationOut.model_validate(convo, from_attributes=True)
    res.last_message = payload.initial_message
    return res


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageOut])
def get_conversation_messages(
    conversation_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=settings.MAX_PAGE_SIZE),
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Fetch all messages in a conversation.
    Enforces authorization: Only participants can read messages.
    """
    participant = db.query(ConversationParticipant).filter(
        ConversationParticipant.conversation_id == conversation_id,
        ConversationParticipant.user_id == current_user.id
    ).first()

    if not participant and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to access this conversation")

    # Update last read timestamp
    if participant:
        participant.last_read_at = utc_now()
        db.commit()

    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.asc(), Message.id.asc()).offset(skip).limit(limit).all()

    out = []
    for m in messages:
        item = MessageOut.model_validate(m, from_attributes=True)
        if m.sender:
            item.sender_name = m.sender.full_name or m.sender.email
        out.append(item)
    return out


@router.post("/conversations/{conversation_id}/messages", response_model=MessageOut)
def send_message(
    conversation_id: int,
    payload: MessageCreate,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """
    Send a message within an existing conversation.
    """
    convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if convo.property and not company_resource_access(current_user, convo.property):
        raise HTTPException(status_code=404, detail="Conversation not found")

    is_participant = db.query(ConversationParticipant).filter(
        ConversationParticipant.conversation_id == conversation_id,
        ConversationParticipant.user_id == current_user.id
    ).first()

    if not is_participant and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to send messages in this conversation")

    msg = Message(
        conversation_id=conversation_id,
        sender_id=current_user.id,
        content=payload.content,
        attachment_url=payload.attachment_url,
        is_system_event=False
    )
    db.add(msg)
    convo.updated_at = utc_now()
    db.commit()
    db.refresh(msg)

    # Notify other participants
    other_participants = db.query(ConversationParticipant).filter(
        ConversationParticipant.conversation_id == conversation_id,
        ConversationParticipant.user_id != current_user.id
    ).all()

    for p in other_participants:
        notif = Notification(
            recipient_id=p.user_id,
            notification_type="MESSAGE",
            title=f"Message from {current_user.full_name or current_user.email}",
            message=payload.content[:120],
            priority="NORMAL",
            related_entity_type="CONVERSATION",
            related_entity_id=conversation_id,
        )
        db.add(notif)
    db.commit()

    res = MessageOut.model_validate(msg, from_attributes=True)
    res.sender_name = current_user.full_name or current_user.email
    return res
