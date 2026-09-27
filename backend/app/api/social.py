from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.social import Friendship
from app.schemas.social import (
    FriendshipCreate,
    FriendshipResponse,
    FriendUserSummary,
    UserLookupResponse,
    IncomingFriendRequest,
    OutgoingFriendRequest,
)
from app.schemas.profile import SocialProfileResponse
from app.behavior.profile import BehaviorProfileManager
from app.core.deps import get_current_user

router = APIRouter(prefix="/social", tags=["Social & Friends"])


@router.get("/lookup", response_model=UserLookupResponse)
@router.get("/find", response_model=UserLookupResponse)
def lookup_user_by_username(
    username: str = Query(..., description="Username handle with or without @"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Look up a user by username for friend discovery.
    Returns minimal safe identity (id, name, username, bio, avatar_url)
    plus the current relationship status relative to the requesting user.
    """
    clean_username = username.lstrip("@").strip().lower()
    if not clean_username:
        raise HTTPException(status_code=400, detail="Username query parameter is required")

    target_user = db.query(User).filter(func.lower(User.username) == clean_username).first()
    if not target_user:
        raise HTTPException(status_code=404, detail=f"No user found with username @{clean_username}")

    # Determine relationship status
    if target_user.id == current_user.id:
        rel_status = "self"
    else:
        existing = (
            db.query(Friendship)
            .filter(
                ((Friendship.user_id == current_user.id) & (Friendship.friend_id == target_user.id))
                | ((Friendship.user_id == target_user.id) & (Friendship.friend_id == current_user.id))
            )
            .first()
        )
        if not existing:
            rel_status = "none"
        elif existing.status == "accepted":
            rel_status = "friends"
        elif existing.status == "pending" and existing.user_id == current_user.id:
            rel_status = "outgoing_request"
        elif existing.status == "pending" and existing.friend_id == current_user.id:
            rel_status = "incoming_request"
        else:
            rel_status = "none"

    return UserLookupResponse(
        id=target_user.id,
        name=target_user.name or "FocusLoop User",
        username=target_user.username,
        bio=target_user.bio,
        avatar_url=target_user.avatar_url,
        relationship_status=rel_status,
    )


@router.get("/friends", response_model=List[FriendUserSummary])
def list_friends(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves all confirmed friends of the current user."""
    friendships = (
        db.query(Friendship)
        .filter(
            ((Friendship.user_id == current_user.id) | (Friendship.friend_id == current_user.id)),
            Friendship.status == "accepted",
        )
        .all()
    )

    friend_summaries = []
    for f in friendships:
        other_id = f.friend_id if f.user_id == current_user.id else f.user_id
        friend_user = db.query(User).filter(User.id == other_id).first()
        if friend_user:
            friend_summaries.append(
                FriendUserSummary(
                    id=friend_user.id,
                    name=friend_user.name or "FocusLoop Friend",
                    username=friend_user.username,
                    bio=friend_user.bio,
                    avatar_url=friend_user.avatar_url,
                    friendship_status=f.status,
                    friends_since=f.created_at,
                )
            )

    return friend_summaries


@router.post("/friends", response_model=FriendshipResponse, status_code=status.HTTP_201_CREATED)
@router.post("/requests", response_model=FriendshipResponse, status_code=status.HTTP_201_CREATED)
def send_friend_request(
    payload: FriendshipCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Sends a friend request to a user by UUID or @username.
    Creates a friendship record with status='pending'.
    If the recipient had already sent a pending request to current_user,
    this automatically upgrades the relationship to 'accepted'.
    """
    target_user = None
    if payload.username:
        clean = payload.username.lstrip("@").strip().lower()
        target_user = db.query(User).filter(func.lower(User.username) == clean).first()
    elif payload.friend_id:
        target_user = db.query(User).filter(User.id == payload.friend_id).first()
    else:
        raise HTTPException(status_code=400, detail="Must provide friend_id or username")

    if not target_user:
        raise HTTPException(status_code=404, detail="Target user does not exist")

    if target_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot add yourself as a friend")

    # Check existing connection in either direction
    existing = (
        db.query(Friendship)
        .filter(
            ((Friendship.user_id == current_user.id) & (Friendship.friend_id == target_user.id))
            | ((Friendship.user_id == target_user.id) & (Friendship.friend_id == current_user.id))
        )
        .first()
    )

    if existing:
        if existing.status == "accepted":
            return existing
        # If target user previously requested current_user, current_user sending request is mutual accept
        if existing.friend_id == current_user.id:
            existing.status = "accepted"
            db.commit()
            db.refresh(existing)
            return existing
        # Already pending from current_user
        return existing

    new_friendship = Friendship(
        user_id=current_user.id,
        friend_id=target_user.id,
        status="pending",
    )
    db.add(new_friendship)
    db.commit()
    db.refresh(new_friendship)
    return new_friendship


@router.get("/requests/incoming", response_model=List[IncomingFriendRequest])
@router.get("/requests", response_model=List[IncomingFriendRequest])
def list_incoming_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves all pending incoming friend requests for the current user."""
    pending_friendships = (
        db.query(Friendship)
        .filter(
            Friendship.friend_id == current_user.id,
            Friendship.status == "pending",
        )
        .order_by(Friendship.created_at.desc())
        .all()
    )

    incoming_list = []
    for f in pending_friendships:
        sender = db.query(User).filter(User.id == f.user_id).first()
        if sender:
            incoming_list.append(
                IncomingFriendRequest(
                    id=f.id,
                    user_id=sender.id,
                    name=sender.name or "FocusLoop User",
                    username=sender.username,
                    avatar_url=sender.avatar_url,
                    bio=sender.bio,
                    created_at=f.created_at,
                )
            )
    return incoming_list


@router.get("/requests/outgoing", response_model=List[OutgoingFriendRequest])
def list_outgoing_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves all pending outgoing friend requests sent by the current user."""
    pending_friendships = (
        db.query(Friendship)
        .filter(
            Friendship.user_id == current_user.id,
            Friendship.status == "pending",
        )
        .order_by(Friendship.created_at.desc())
        .all()
    )

    outgoing_list = []
    for f in pending_friendships:
        recipient = db.query(User).filter(User.id == f.friend_id).first()
        if recipient:
            outgoing_list.append(
                OutgoingFriendRequest(
                    id=f.id,
                    friend_id=recipient.id,
                    name=recipient.name or "FocusLoop User",
                    username=recipient.username,
                    avatar_url=recipient.avatar_url,
                    bio=recipient.bio,
                    created_at=f.created_at,
                )
            )
    return outgoing_list


@router.post("/requests/{request_id}/accept", response_model=FriendshipResponse)
@router.post("/friends/{request_id}/accept", response_model=FriendshipResponse)
def accept_friend_request(
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Accepts an incoming friend request by friendship ID or sender user ID.
    Transitions status from 'pending' to 'accepted'.
    """
    # 1. Try finding by friendship.id
    friendship = db.query(Friendship).filter(Friendship.id == request_id).first()

    # 2. Try finding by sender user_id
    if not friendship:
        friendship = (
            db.query(Friendship)
            .filter(Friendship.user_id == request_id, Friendship.friend_id == current_user.id)
            .first()
        )

    if not friendship:
        raise HTTPException(status_code=404, detail="Friend request not found")

    # Only recipient can accept
    if friendship.friend_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to accept this friend request")

    if friendship.status != "accepted":
        friendship.status = "accepted"
        db.commit()
        db.refresh(friendship)

    return friendship


@router.post("/requests/{request_id}/decline", status_code=status.HTTP_204_NO_CONTENT)
@router.post("/friends/{request_id}/decline", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/requests/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def decline_friend_request(
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Declines an incoming friend request or cancels an outgoing friend request.
    Removes the friendship record.
    """
    # 1. Try finding by friendship.id
    friendship = db.query(Friendship).filter(Friendship.id == request_id).first()

    # 2. Try finding by sender or recipient user_id
    if not friendship:
        friendship = (
            db.query(Friendship)
            .filter(
                ((Friendship.user_id == request_id) & (Friendship.friend_id == current_user.id))
                | ((Friendship.user_id == current_user.id) & (Friendship.friend_id == request_id))
            )
            .first()
        )

    if not friendship:
        raise HTTPException(status_code=404, detail="Friend request not found")

    # Only involved parties can decline or cancel
    if friendship.friend_id != current_user.id and friendship.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to decline or cancel this request")

    db.delete(friendship)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/friends/{friend_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_friend(
    friend_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Removes a friendship connection."""
    friendship = (
        db.query(Friendship)
        .filter(
            ((Friendship.user_id == current_user.id) & (Friendship.friend_id == friend_id))
            | ((Friendship.user_id == friend_id) & (Friendship.friend_id == current_user.id))
        )
        .first()
    )

    if not friendship:
        raise HTTPException(status_code=404, detail="Friendship not found")

    db.delete(friendship)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/friends/{friend_id}/profile", response_model=SocialProfileResponse)
def get_friend_social_profile(
    friend_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Convenience endpoint to retrieve a friend's social profile.
    Strictly enforces backend privacy rules based on friend's visibility preferences.
    """
    target_user = db.query(User).filter(User.id == friend_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    profile_mgr = BehaviorProfileManager(db, target_user.id)
    return profile_mgr.get_social_profile(viewer_id=current_user.id)
