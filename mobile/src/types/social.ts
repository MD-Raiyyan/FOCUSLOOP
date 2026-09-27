export interface FriendshipCreate {
  friend_id?: string;
  username?: string;
}

export interface FriendshipResponse {
  id: string;
  user_id: string;
  friend_id: string;
  status: string;
  created_at: string;
}

export interface FriendUserSummary {
  id: string;
  name: string;
  username?: string | null;
  bio?: string | null;
  avatar_url?: string | null;
  friendship_status: string;
  friends_since: string;
}

export interface UserLookupResponse {
  id: string;
  name: string;
  username?: string | null;
  bio?: string | null;
  avatar_url?: string | null;
  relationship_status?: 'none' | 'friends' | 'incoming_request' | 'outgoing_request' | 'self';
}

export interface IncomingFriendRequest {
  id: string;
  user_id: string;
  name: string;
  username?: string | null;
  avatar_url?: string | null;
  bio?: string | null;
  created_at: string;
}

export interface OutgoingFriendRequest {
  id: string;
  friend_id: string;
  name: string;
  username?: string | null;
  avatar_url?: string | null;
  bio?: string | null;
  created_at: string;
}
