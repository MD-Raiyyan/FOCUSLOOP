from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class FriendshipCreate(BaseModel):
    friend_id: Optional[str] = None
    username: Optional[str] = None


class FriendshipResponse(BaseModel):
    id: str
    user_id: str
    friend_id: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FriendUserSummary(BaseModel):
    id: str
    name: str
    username: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    friendship_status: str
    friends_since: datetime


class UserLookupResponse(BaseModel):
    id: str
    name: str
    username: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    relationship_status: Optional[str] = None  # "none", "friends", "incoming_request", "outgoing_request", "self"


class IncomingFriendRequest(BaseModel):
    id: str
    user_id: str
    name: str
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    created_at: datetime


class OutgoingFriendRequest(BaseModel):
    id: str
    friend_id: str
    name: str
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    created_at: datetime
