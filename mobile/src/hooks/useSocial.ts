import { useState, useEffect, useCallback } from 'react';
import {
  FriendUserSummary,
  IncomingFriendRequest,
  OutgoingFriendRequest,
  UserLookupResponse,
  FriendshipResponse,
} from '../types/social';
import { SocialProfileResponse } from '../types/profile';
import { socialService } from '../services/social';

export function useSocial() {
  const [friends, setFriends] = useState<FriendUserSummary[]>([]);
  const [incomingRequests, setIncomingRequests] = useState<IncomingFriendRequest[]>([]);
  const [outgoingRequests, setOutgoingRequests] = useState<OutgoingFriendRequest[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSocialData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const [friendsData, incomingData, outgoingData] = await Promise.all([
        socialService.getFriends().catch(() => [] as FriendUserSummary[]),
        socialService.getIncomingRequests().catch(() => [] as IncomingFriendRequest[]),
        socialService.getOutgoingRequests().catch(() => [] as OutgoingFriendRequest[]),
      ]);
      setFriends(friendsData);
      setIncomingRequests(incomingData);
      setOutgoingRequests(outgoingData);
    } catch (err: any) {
      setError(err.message || 'Failed to load social connections');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSocialData();
  }, [fetchSocialData]);

  const lookupUser = async (username: string): Promise<UserLookupResponse> => {
    return socialService.lookupUser(username);
  };

  const sendFriendRequest = async (target: {
    friendId?: string;
    username?: string;
  }): Promise<FriendshipResponse> => {
    const res = await socialService.sendFriendRequest(target);
    await fetchSocialData();
    return res;
  };

  const addFriend = async (friendId: string) => {
    await sendFriendRequest({ friendId });
  };

  const acceptRequest = async (requestId: string) => {
    await socialService.acceptFriendRequest(requestId);
    await fetchSocialData();
  };

  const declineRequest = async (requestId: string) => {
    await socialService.declineFriendRequest(requestId);
    setIncomingRequests((prev) => prev.filter((r) => r.id !== requestId && r.user_id !== requestId));
  };

  const cancelRequest = async (requestId: string) => {
    await socialService.cancelFriendRequest(requestId);
    setOutgoingRequests((prev) => prev.filter((r) => r.id !== requestId && r.friend_id !== requestId));
  };

  const removeFriend = async (friendId: string) => {
    await socialService.removeFriend(friendId);
    setFriends((prev) => prev.filter((f) => f.id !== friendId));
  };

  const getFriendProfile = async (
    friendId: string
  ): Promise<SocialProfileResponse> => {
    return socialService.getFriendProfile(friendId);
  };

  return {
    friends,
    incomingRequests,
    outgoingRequests,
    isLoading,
    error,
    refreshSocial: fetchSocialData,
    refreshFriends: fetchSocialData,
    lookupUser,
    sendFriendRequest,
    addFriend,
    acceptRequest,
    declineRequest,
    cancelRequest,
    removeFriend,
    getFriendProfile,
  };
}
