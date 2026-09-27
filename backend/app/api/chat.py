from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.chat import Conversation, Message
from app.schemas.chat import (
    MessageCreate,
    MessageResponse,
    ConversationResponse,
    AIExplanationRequest,
    AIExplanationResponse,
)
from app.ai.context_builder import AIContextBuilder
from app.ai.llm import llm_service

router = APIRouter(prefix="/chat", tags=["AI Companion & Explanation"])


@router.post("/explain", response_model=AIExplanationResponse)
def get_behavioral_explanation(
    payload: AIExplanationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    AI Behavioral Explainer for authenticated user.
    Prepares verified, question-relevant quantitative evidence and passes it to the LLM
    to generate an empathetic explanation and micro-experiment.
    """
    context_builder = AIContextBuilder(db, current_user.id)
    context = context_builder.build_context(
        question=payload.question,
        specific_pattern_id=payload.pattern_id,
    )

    result = llm_service.generate_explanation(context=context, question=payload.question)
    return AIExplanationResponse(**result)


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_or_get_conversation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Creates or fetches the active companion conversation for authenticated user."""
    convo = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .first()
    )
    if not convo:
        convo = Conversation(
            user_id=current_user.id,
            title="FocusLoop Companion Session",
        )
        db.add(convo)
        db.commit()
        db.refresh(convo)

    return convo


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves conversation thread and message history, enforcing ownership authorization."""
    convo = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not convo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found or unauthorized")
    return convo


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
def send_message(
    conversation_id: str,
    payload: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Sends a user message and returns an empathetic, grounded AI companion reply."""
    convo = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not convo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found or unauthorized")

    # 1. Save user message
    user_msg = Message(
        conversation_id=convo.id,
        sender="user",
        content=payload.content,
    )
    db.add(user_msg)
    db.commit()

    # 2. Collect recent history (up to last 6 messages)
    history = [
        {"role": m.sender, "content": m.content}
        for m in convo.messages[-6:]
    ]

    # 3. Build question-relevant structured AI context
    context_builder = AIContextBuilder(db, current_user.id)
    context = context_builder.build_context(
        question=payload.content,
        conversation_history=history,
    )

    # 4. Generate grounded AI reply
    assistant_reply = llm_service.generate_chat_reply(messages=history, context=context)

    # 5. Save assistant message
    ai_msg = Message(
        conversation_id=convo.id,
        sender="assistant",
        content=assistant_reply,
    )
    db.add(ai_msg)
    db.commit()
    db.refresh(ai_msg)

    return ai_msg
