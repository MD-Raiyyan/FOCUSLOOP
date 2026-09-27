import { api } from './api';
import {
  FriendshipCreate,
  FriendshipResponse,
  FriendUserSummary,
  UserLookupResponse,
  IncomingFriendRequest,
  OutgoingFriendRequest,
} from '../types/social';
import { SocialProfileResponse } from '../types/profile';

export const socialService = {
  async getFriends(): Promise<FriendUserSummary[]> {
    return api.get<FriendUserSummary[]>('/api/v1/social/friends');
  },

  async lookupUser(username: string): Promise<UserLookupResponse> {
    const encoded = encodeURIComponent(username.trim());
    return api.get<UserLookupResponse>(`/api/v1/social/lookup?username=${encoded}`);
  },

  async sendFriendRequest(target: { friendId?: string; username?: string }): Promise<FriendshipResponse> {
    const payload: FriendshipCreate = {};
    if (target.friendId) payload.friend_id = target.friendId;
    if (target.username) payload.username = target.username;
    return api.post<FriendshipResponse>('/api/v1/social/friends', payload);
  },

  async addFriend(friendId: string): Promise<FriendshipResponse> {
    return this.sendFriendRequest({ friendId });
  },

  async getIncomingRequests(): Promise<IncomingFriendRequest[]> {
    return api.get<IncomingFriendRequest[]>('/api/v1/social/requests/incoming');
  },

  async getOutgoingRequests(): Promise<OutgoingFriendRequest[]> {
    return api.get<OutgoingFriendRequest[]>('/api/v1/social/requests/outgoing');
  },

  async acceptFriendRequest(requestId: string): Promise<FriendshipResponse> {
    return api.post<FriendshipResponse>(`/api/v1/social/requests/${requestId}/accept`);
  },

  async declineFriendRequest(requestId: string): Promise<void> {
    return api.post<void>(`/api/v1/social/requests/${requestId}/decline`);
  },

  async cancelFriendRequest(requestId: string): Promise<void> {
    return api.delete<void>(`/api/v1/social/requests/${requestId}`);
  },

  async removeFriend(friendId: string): Promise<void> {
    return api.delete<void>(`/api/v1/social/friends/${friendId}`);
  },

  async getFriendProfile(friendId: string): Promise<SocialProfileResponse> {
    return api.get<SocialProfileResponse>(`/api/v1/social/friends/${friendId}/profile`);
  },
};
