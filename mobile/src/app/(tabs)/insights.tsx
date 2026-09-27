import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
  ActivityIndicator,
  Modal,
  TextInput,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Header } from '@/components/Header';
import { Colors } from '@/constants/theme';
import { useProfile } from '@/hooks/useProfile';
import { useBehavior } from '@/hooks/useBehavior';
import { useSocial } from '@/hooks/useSocial';
import { SocialProfileResponse } from '@/types/profile';
import { UserLookupResponse } from '@/types/social';
import { PatternEvidenceCard } from '@/components/PatternEvidenceCard';

export default function InsightsScreen() {
  const router = useRouter();
  const { profile, curve, isLoading: profileLoading } = useProfile();
  const { summary, patterns, isLoading: behaviorLoading } = useBehavior();
  const {
    friends,
    incomingRequests,
    outgoingRequests,
    isLoading: friendsLoading,
    refreshSocial,
    lookupUser,
    sendFriendRequest,
    acceptRequest,
    declineRequest,
    cancelRequest,
    removeFriend,
    getFriendProfile,
  } = useSocial();

  const [activeSegment, setActiveSegment] = useState<'Overview' | 'Impact' | 'Peer'>('Overview');

  // Add friend / username search modal state
  const [isAddFriendModalVisible, setIsAddFriendModalVisible] = useState(false);
  const [usernameInput, setUsernameInput] = useState('');
  const [isSearchingUser, setIsSearchingUser] = useState(false);
  const [searchResult, setSearchResult] = useState<UserLookupResponse | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [isSendingRequest, setIsSendingRequest] = useState(false);
  const [processingRequestId, setProcessingRequestId] = useState<string | null>(null);

  // Friend profile modal state
  const [selectedFriendProfile, setSelectedFriendProfile] = useState<SocialProfileResponse | null>(null);
  const [isLoadingFriendProfile, setIsLoadingFriendProfile] = useState(false);

  const handleSearchUser = async () => {
    const raw = usernameInput.trim();
    if (!raw || raw === '@') {
      setSearchError('Please enter a username to search');
      setSearchResult(null);
      return;
    }
    try {
      setIsSearchingUser(true);
      setSearchError(null);
      setSearchResult(null);
      const user = await lookupUser(raw);
      setSearchResult(user);
    } catch (err: any) {
      setSearchError(err.message || 'No user found with that username.');
      setSearchResult(null);
    } finally {
      setIsSearchingUser(false);
    }
  };

  const handleSendRequest = async () => {
    if (!searchResult) return;
    try {
      setIsSendingRequest(true);
      await sendFriendRequest({ friendId: searchResult.id });
      setSearchResult((prev) => (prev ? { ...prev, relationship_status: 'outgoing_request' } : null));
      Alert.alert('Request Sent', `Friend request sent to ${searchResult.name}!`);
    } catch (err: any) {
      Alert.alert('Notice', err.message || 'Could not send friend request.');
    } finally {
      setIsSendingRequest(false);
    }
  };

  const handleAcceptRequest = async (requestId: string, senderName: string) => {
    try {
      setProcessingRequestId(requestId);
      await acceptRequest(requestId);
      Alert.alert('Connected', `You and ${senderName} are now connected in Peer Circles!`);
    } catch (err: any) {
      Alert.alert('Notice', err.message || 'Could not accept friend request.');
    } finally {
      setProcessingRequestId(null);
    }
  };

  const handleDeclineRequest = async (requestId: string) => {
    try {
      setProcessingRequestId(requestId);
      await declineRequest(requestId);
    } catch (err: any) {
      Alert.alert('Notice', err.message || 'Could not decline friend request.');
    } finally {
      setProcessingRequestId(null);
    }
  };

  const handleCancelRequest = async (requestId: string) => {
    try {
      setProcessingRequestId(requestId);
      await cancelRequest(requestId);
    } catch (err: any) {
      Alert.alert('Notice', err.message || 'Could not cancel friend request.');
    } finally {
      setProcessingRequestId(null);
    }
  };

  const handleOpenFriendProfile = async (friendId: string) => {
    try {
      setIsLoadingFriendProfile(true);
      const socialProfile = await getFriendProfile(friendId);
      setSelectedFriendProfile(socialProfile);
    } catch (err: any) {
      Alert.alert('Profile Notice', err.message || 'Could not load friend profile.');
    } finally {
      setIsLoadingFriendProfile(false);
    }
  };



  return (
    <SafeAreaView style={styles.safeArea}>
      <Header title="Insights" />

      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Top Segmented Sliding Toggle */}
        <View style={styles.segmentedRail}>
          <TouchableOpacity
            style={[styles.segmentBtn, activeSegment === 'Overview' && styles.segmentBtnActive]}
            onPress={() => setActiveSegment('Overview')}
          >
            <Text style={[styles.segmentText, activeSegment === 'Overview' && styles.segmentTextActive]}>
              Overview & Curve
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.segmentBtn, activeSegment === 'Impact' && styles.segmentBtnActive]}
            onPress={() => setActiveSegment('Impact')}
          >
            <Text style={[styles.segmentText, activeSegment === 'Impact' && styles.segmentTextActive]}>
              Impact & Level
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.segmentBtn, activeSegment === 'Peer' && styles.segmentBtnActive]}
            onPress={() => setActiveSegment('Peer')}
          >
            <Text style={[styles.segmentText, activeSegment === 'Peer' && styles.segmentTextActive]}>
              Peer Circles
            </Text>
          </TouchableOpacity>
        </View>

        {/* OVERVIEW & CURVE VIEW */}
        {activeSegment === 'Overview' && (
          <View style={styles.tabContent}>
            {/* Top Productivity Score Hero Card */}
            <View style={styles.scoreHeroCard}>
              <View style={styles.scoreHeaderRow}>
                <View>
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
                    <Ionicons name="analytics-outline" size={14} color={Colors.primaryFixedDim} />
                    <Text style={styles.scoreLabel}>BEHAVIOR SCORE (PRIVATE)</Text>
                  </View>
                  <View style={styles.scoreMetricRow}>
                    <Text style={styles.scoreNumber}>
                      {profileLoading ? '...' : (profile?.metrics?.behavior_score ? profile.metrics.behavior_score.toFixed(0) : '—')}
                    </Text>
                    <View style={styles.trendPill}>
                      <Ionicons name="shield-checkmark" size={12} color={Colors.secondaryFixed} />
                      <Text style={styles.trendPillText}>Owner Only</Text>
                    </View>
                  </View>
                  <Text style={styles.scoreSubTitle}>
                    Current Level: {profile?.metrics?.current_level || '1 — Foundation'}
                  </Text>
                </View>
                <View style={styles.vsBadge}>
                  <Text style={styles.vsBadgeText}>
                    Consistency: {profile?.metrics?.consistency != null ? `${Math.round(profile.metrics.consistency)}%` : '—'}
                  </Text>
                </View>
              </View>
            </View>

            {/* 14-Day Progress Curve Card */}
            <View style={styles.card}>
              <View style={styles.cardHeaderRow}>
                <View style={styles.cardIconBox}>
                  <Ionicons name="trending-up-outline" size={16} color={Colors.primary} />
                </View>
                <Text style={styles.cardTitle}>14-Day Progress Trajectory</Text>
              </View>

              {curve.length === 0 ? (
                <View style={styles.emptyContainer}>
                  <Ionicons name="pulse-outline" size={24} color={Colors.textMuted} />
                  <Text style={styles.emptyText}>No curve points generated yet.</Text>
                </View>
              ) : (
                <View style={styles.curveList}>
                  {curve.map((pt, i) => (
                    <View key={i} style={styles.curveRow}>
                      <Text style={styles.curveDate}>{pt.date}</Text>
                      <View style={styles.curveScoreBar}>
                        <View
                          style={[
                            styles.curveFill,
                            {
                              width: `${Math.min(100, Math.max(10, pt.progress_score))}%`,
                              backgroundColor:
                                pt.trend === 'improving' || pt.trend === 'recovery'
                                  ? Colors.secondary
                                  : pt.trend === 'setback'
                                  ? Colors.accentCoral
                                  : Colors.primary,
                            },
                          ]}
                        />
                      </View>
                      <Text style={styles.curveTrend}>{pt.trend.charAt(0).toUpperCase() + pt.trend.slice(1)}</Text>
                    </View>
                  ))}
                </View>
              )}
            </View>

            {/* Key Behavioral Patterns Cards */}
            <View style={{ gap: 10 }}>
              <Text style={styles.sectionHeaderTitle}>Key Behavioral Patterns</Text>

              {patterns.length === 0 ? (
                <View style={styles.emptyPatternsCard}>
                  <Ionicons name="sparkles-outline" size={24} color={Colors.textMuted} />
                  <Text style={styles.emptyPatternsTitle}>No Behavioral Patterns Detected Yet</Text>
                  <Text style={styles.emptyPatternsSubtitle}>
                    As you record task check-ins and delay logs, the FocusLoop behavioral engine detects initiation hesitation and focus trends.
                  </Text>
                </View>
              ) : (
                patterns.map((pat) => (
                  <PatternEvidenceCard key={pat.id} pattern={pat} />
                ))
              )}
            </View>
          </View>
        )}

        {/* IMPACT & LEVEL VIEW */}
        {activeSegment === 'Impact' && (
          <View style={styles.tabContent}>
            {/* Protocol Effectiveness Hero */}
            <View style={styles.impactHeroCard}>
              <View style={styles.impactTopRow}>
                <View style={[styles.gradeBox, { backgroundColor: Colors.surfaceContainer }]}>
                  <Ionicons name="flask-outline" size={24} color={Colors.primary} />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.impactSubHeader}>Experiment Effectiveness</Text>
                  <Text style={styles.impactScoreBig}>
                    {profile?.metrics?.experiment_effectiveness != null
                      ? `${Math.round(profile.metrics.experiment_effectiveness)}%`
                      : '—'}
                  </Text>
                  <Text style={{ fontSize: 11, color: Colors.textSubtle }}>
                    Empirical outcome of evaluated lab protocols
                  </Text>
                </View>
              </View>

              {/* 3 Metrics Row */}
              <View style={styles.metricsRow}>
                <View style={styles.metricTile}>
                  <Text style={styles.metricVal}>
                    {profile?.metrics?.improvement_score != null
                      ? profile.metrics.improvement_score.toFixed(1)
                      : '—'}
                  </Text>
                  <Text style={styles.metricLabel}>Improvement Score</Text>
                </View>
                <View style={styles.metricTile}>
                  <Text style={[styles.metricVal, { color: Colors.primary }]}>
                    {profile?.milestones?.length ?? 0}
                  </Text>
                  <Text style={styles.metricLabel}>Milestones Met</Text>
                </View>
                <View style={styles.metricTile}>
                  <Text style={[styles.metricVal, { color: Colors.secondary }]}>
                    {profile?.metrics?.consistency != null
                      ? `${Math.round(profile.metrics.consistency)}%`
                      : '—'}
                  </Text>
                  <Text style={styles.metricLabel}>Consistency</Text>
                </View>
              </View>
            </View>

            {/* Current Level Evolution Path */}
            <View style={styles.card}>
              <Text style={{ fontSize: 10, fontWeight: '700', color: Colors.primary, letterSpacing: 0.5 }}>
                CURRENT FOCUS LEVEL
              </Text>
              <Text style={styles.cardTitle}>{profile?.metrics?.current_level || '1 — Foundation'}</Text>
              <View style={{ marginTop: 8 }}>
                <Text style={{ fontSize: 12, color: Colors.textStrong, marginBottom: 4 }}>
                  {profile?.metrics?.level_info?.title || 'Behavioral Foundation'}
                </Text>
                <Text style={{ fontSize: 11, color: Colors.textSubtle, lineHeight: 16 }}>
                  {profile?.metrics?.level_info?.description ||
                    'FocusLoop progression is calibrated purely against your recorded completion consistency and initiation friction.'}
                </Text>
              </View>
            </View>

            {/* Milestones Card */}
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Verified Milestones</Text>
              {profile?.milestones && profile.milestones.length > 0 ? (
                <View style={{ gap: 8, marginTop: 8 }}>
                  {profile.milestones.map((m, idx) => (
                    <View key={idx} style={styles.milestoneRow}>
                      <Ionicons name="checkmark-done-circle" size={16} color={Colors.secondary} />
                      <Text style={styles.milestoneText}>{m}</Text>
                    </View>
                  ))}
                </View>
              ) : (
                <Text style={{ fontSize: 12, color: Colors.textSubtle, marginTop: 8 }}>
                  No milestones achieved yet. Complete tasks and protocols to reach milestones.
                </Text>
              )}
            </View>
          </View>
        )}

        {/* FRIENDS & PRIVACY VIEW */}
        {activeSegment === 'Peer' && (
          <View style={styles.tabContent}>
            {/* INCOMING FRIEND REQUESTS CARD (if any) */}
            {incomingRequests.length > 0 && (
              <View style={[styles.card, styles.incomingRequestsCard]}>
                <View style={styles.cardHeaderRow}>
                  <View style={[styles.cardIconBox, { backgroundColor: '#E0F2FE' }]}>
                    <Ionicons name="mail-unread" size={16} color={Colors.accentSky} />
                  </View>
                  <Text style={styles.cardTitle}>Friend Requests ({incomingRequests.length})</Text>
                  <View style={styles.requestCountBadge}>
                    <Text style={styles.requestCountText}>{incomingRequests.length} new</Text>
                  </View>
                </View>
                <Text style={{ fontSize: 11, color: Colors.textSubtle, marginTop: 2 }}>
                  Peers who want to share focus accountability with you.
                </Text>

                <View style={{ gap: 10, marginTop: 12 }}>
                  {incomingRequests.map((req) => {
                    const isProcessing = processingRequestId === req.id;
                    return (
                      <View key={req.id} style={styles.requestItemRow}>
                        <View style={styles.requestAvatar}>
                          <Text style={styles.requestInitial}>
                            {req.name.charAt(0).toUpperCase()}
                          </Text>
                        </View>
                        <View style={{ flex: 1 }}>
                          <Text style={styles.requestName}>{req.name}</Text>
                          <Text style={styles.requestHandle}>
                            {req.username ? `@${req.username}` : 'FocusLoop Peer'}
                          </Text>
                        </View>
                        <View style={styles.requestActionButtons}>
                          <TouchableOpacity
                            style={[styles.acceptBtn, isProcessing && { opacity: 0.6 }]}
                            onPress={() => handleAcceptRequest(req.id, req.name)}
                            disabled={isProcessing}
                          >
                            <Ionicons name="checkmark" size={14} color="#FFFFFF" />
                            <Text style={styles.acceptBtnText}>Accept</Text>
                          </TouchableOpacity>
                          <TouchableOpacity
                            style={[styles.declineBtn, isProcessing && { opacity: 0.6 }]}
                            onPress={() => handleDeclineRequest(req.id)}
                            disabled={isProcessing}
                          >
                            <Ionicons name="close" size={14} color={Colors.accentCoral} />
                            <Text style={styles.declineBtnText}>Decline</Text>
                          </TouchableOpacity>
                        </View>
                      </View>
                    );
                  })}
                </View>
              </View>
            )}

            {/* Confirmed Friends Circles Card */}
            <View style={styles.card}>
              <View style={styles.cardHeaderRow}>
                <Text style={styles.cardTitle}>Friends & Social Circles ({friends.length})</Text>
                <TouchableOpacity
                  style={styles.addFriendHeaderBtn}
                  onPress={() => {
                    setUsernameInput('');
                    setSearchResult(null);
                    setSearchError(null);
                    setIsAddFriendModalVisible(true);
                  }}
                >
                  <Ionicons name="person-add" size={14} color="#FFFFFF" />
                  <Text style={styles.addFriendHeaderText}>Add Friend</Text>
                </TouchableOpacity>
              </View>
              <Text style={{ fontSize: 11, color: Colors.textSubtle, marginTop: 2 }}>
                Shared focus accountability. Zero competitive ranking or points.
              </Text>

              {friendsLoading ? (
                <View style={{ padding: 20, alignItems: 'center' }}>
                  <ActivityIndicator size="small" color={Colors.primary} />
                </View>
              ) : friends.length === 0 ? (
                <View style={styles.emptyFriendsCard}>
                  <Ionicons name="people-outline" size={28} color={Colors.textMuted} />
                  <Text style={styles.emptyFriendsTitle}>No Friends Connected Yet</Text>
                  <Text style={styles.emptyFriendsSubtitle}>
                    Search for friends by @username to connect and share consistency progress.
                  </Text>
                  <TouchableOpacity
                    style={[styles.addFriendHeaderBtn, { marginTop: 12, alignSelf: 'center' }]}
                    onPress={() => {
                      setUsernameInput('');
                      setSearchResult(null);
                      setSearchError(null);
                      setIsAddFriendModalVisible(true);
                    }}
                  >
                    <Ionicons name="search" size={14} color="#FFFFFF" />
                    <Text style={styles.addFriendHeaderText}>Find by @username</Text>
                  </TouchableOpacity>
                </View>
              ) : (
                <View style={{ gap: 10, marginTop: 12 }}>
                  {friends.map((friend) => (
                    <TouchableOpacity
                      key={friend.id}
                      style={styles.friendRow}
                      onPress={() => handleOpenFriendProfile(friend.id)}
                      activeOpacity={0.7}
                    >
                      <View style={styles.friendAvatar}>
                        <Text style={styles.friendInitial}>
                          {friend.name.charAt(0).toUpperCase()}
                        </Text>
                      </View>
                      <View style={{ flex: 1 }}>
                        <Text style={styles.friendName}>{friend.name}</Text>
                        <Text style={styles.friendSub}>
                          {friend.username ? `@${friend.username}` : `Friend ID: ${friend.id.slice(0, 8)}`}
                        </Text>
                      </View>
                      <TouchableOpacity
                        onPress={() => removeFriend(friend.id)}
                        hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
                      >
                        <Ionicons name="person-remove-outline" size={16} color={Colors.textMuted} />
                      </TouchableOpacity>
                    </TouchableOpacity>
                  ))}
                </View>
              )}
            </View>

            {/* OUTGOING PENDING REQUESTS (if any) */}
            {outgoingRequests.length > 0 && (
              <View style={styles.card}>
                <View style={styles.cardHeaderRow}>
                  <View style={[styles.cardIconBox, { backgroundColor: '#FEF3C7' }]}>
                    <Ionicons name="time-outline" size={16} color="#D97706" />
                  </View>
                  <Text style={styles.cardTitle}>Sent Requests ({outgoingRequests.length})</Text>
                </View>
                <Text style={{ fontSize: 11, color: Colors.textSubtle, marginTop: 2 }}>
                  Waiting for recipient to accept.
                </Text>
                <View style={{ gap: 10, marginTop: 12 }}>
                  {outgoingRequests.map((out) => {
                    const isProcessing = processingRequestId === out.id;
                    return (
                      <View key={out.id} style={styles.requestItemRow}>
                        <View style={[styles.requestAvatar, { backgroundColor: '#F3F4F6' }]}>
                          <Text style={[styles.requestInitial, { color: Colors.textSubtle }]}>
                            {out.name.charAt(0).toUpperCase()}
                          </Text>
                        </View>
                        <View style={{ flex: 1 }}>
                          <Text style={styles.requestName}>{out.name}</Text>
                          <Text style={styles.requestHandle}>
                            {out.username ? `@${out.username}` : 'Pending connection'}
                          </Text>
                        </View>
                        <TouchableOpacity
                          style={[styles.cancelBtn, isProcessing && { opacity: 0.6 }]}
                          onPress={() => handleCancelRequest(out.id)}
                          disabled={isProcessing}
                        >
                          <Text style={styles.cancelBtnText}>Cancel</Text>
                        </TouchableOpacity>
                      </View>
                    );
                  })}
                </View>
              </View>
            )}

            {/* Link to My Profile Privacy & Sharing */}
            <TouchableOpacity
              style={styles.privacyLinkCard}
              onPress={() => router.push('/profile' as any)}
              activeOpacity={0.8}
            >
              <View style={[styles.cardIconBox, { backgroundColor: Colors.surfaceTintMint }]}>
                <Ionicons name="shield-checkmark-outline" size={16} color={Colors.secondary} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.privacyLinkTitle}>Privacy & Sharing Controls</Text>
                <Text style={styles.privacyLinkSubtitle}>
                  Manage what friends can view on your public profile in My Profile.
                </Text>
              </View>
              <Ionicons name="chevron-forward" size={18} color={Colors.textMuted} />
            </TouchableOpacity>
          </View>
        )}
      </ScrollView>

      {/* Add Friend / Username Search Modal */}
      <Modal visible={isAddFriendModalVisible} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                <View style={[styles.cardIconBox, { backgroundColor: Colors.surfaceTintViolet }]}>
                  <Ionicons name="person-add" size={16} color={Colors.primary} />
                </View>
                <Text style={styles.modalTitle}>Add Friend</Text>
              </View>
              <TouchableOpacity
                onPress={() => {
                  setIsAddFriendModalVisible(false);
                  setSearchResult(null);
                  setSearchError(null);
                  setUsernameInput('');
                }}
              >
                <Ionicons name="close" size={24} color={Colors.textStrong} />
              </TouchableOpacity>
            </View>

            <Text style={{ fontSize: 12, color: Colors.textSubtle }}>
              Search for peers by their unique @username to send a friend request.
            </Text>

            {/* Search Input Box */}
            <View style={styles.searchRow}>
              <View style={styles.searchInputContainer}>
                <Text style={styles.atSymbol}>@</Text>
                <TextInput
                  style={styles.usernameInput}
                  placeholder="username"
                  placeholderTextColor="#9896B0"
                  value={usernameInput.startsWith('@') ? usernameInput.slice(1) : usernameInput}
                  onChangeText={(text) => {
                    setUsernameInput(text.trim());
                    setSearchError(null);
                  }}
                  onSubmitEditing={handleSearchUser}
                  autoCapitalize="none"
                  autoCorrect={false}
                  returnKeyType="search"
                />
              </View>
              <TouchableOpacity
                style={[styles.searchActionBtn, isSearchingUser && { opacity: 0.6 }]}
                onPress={handleSearchUser}
                disabled={isSearchingUser}
              >
                {isSearchingUser ? (
                  <ActivityIndicator color="#FFFFFF" size="small" />
                ) : (
                  <Ionicons name="search" size={18} color="#FFFFFF" />
                )}
              </TouchableOpacity>
            </View>

            {/* Search Error Notice */}
            {searchError && (
              <View style={styles.searchErrorBox}>
                <Ionicons name="alert-circle-outline" size={16} color={Colors.accentCoral} />
                <Text style={styles.searchErrorText}>{searchError}</Text>
              </View>
            )}

            {/* Search Result Identity Preview */}
            {searchResult && (
              <View style={styles.previewCard}>
                <View style={styles.previewHeaderRow}>
                  <View style={styles.previewAvatar}>
                    <Text style={styles.previewInitial}>
                      {searchResult.name.charAt(0).toUpperCase()}
                    </Text>
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.previewName}>{searchResult.name}</Text>
                    <Text style={styles.previewHandle}>
                      {searchResult.username ? `@${searchResult.username}` : ''}
                    </Text>
                    {searchResult.bio ? (
                      <Text style={styles.previewBio} numberOfLines={2}>
                        {searchResult.bio}
                      </Text>
                    ) : null}
                  </View>
                </View>

                {/* Relationship status CTA */}
                <View style={{ marginTop: 12 }}>
                  {searchResult.relationship_status === 'self' && (
                    <View style={styles.statusPillNeutral}>
                      <Ionicons name="person" size={14} color={Colors.textSubtle} />
                      <Text style={styles.statusPillNeutralText}>This is your account</Text>
                    </View>
                  )}

                  {searchResult.relationship_status === 'friends' && (
                    <View style={styles.statusPillSuccess}>
                      <Ionicons name="checkmark-circle" size={14} color={Colors.secondary} />
                      <Text style={styles.statusPillSuccessText}>Already in your Peer Circles</Text>
                    </View>
                  )}

                  {searchResult.relationship_status === 'outgoing_request' && (
                    <View style={styles.statusPillPending}>
                      <Ionicons name="time" size={14} color="#D97706" />
                      <Text style={styles.statusPillPendingText}>Friend Request Pending</Text>
                    </View>
                  )}

                  {searchResult.relationship_status === 'incoming_request' && (
                    <TouchableOpacity
                      style={styles.previewActionBtn}
                      onPress={() => {
                        handleAcceptRequest(searchResult.id, searchResult.name);
                        setIsAddFriendModalVisible(false);
                      }}
                    >
                      <Ionicons name="checkmark" size={16} color="#FFFFFF" />
                      <Text style={styles.previewActionBtnText}>Accept Incoming Request</Text>
                    </TouchableOpacity>
                  )}

                  {(!searchResult.relationship_status || searchResult.relationship_status === 'none') && (
                    <TouchableOpacity
                      style={[styles.previewActionBtn, isSendingRequest && { opacity: 0.6 }]}
                      onPress={handleSendRequest}
                      disabled={isSendingRequest}
                    >
                      {isSendingRequest ? (
                        <ActivityIndicator color="#FFFFFF" size="small" />
                      ) : (
                        <>
                          <Ionicons name="paper-plane-outline" size={16} color="#FFFFFF" />
                          <Text style={styles.previewActionBtnText}>Send Friend Request</Text>
                        </>
                      )}
                    </TouchableOpacity>
                  )}
                </View>
              </View>
            )}
          </View>
        </View>
      </Modal>

      {/* Friend Social Profile Modal */}
      <Modal visible={!!selectedFriendProfile} transparent animationType="fade">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Friend Profile</Text>
              <TouchableOpacity onPress={() => setSelectedFriendProfile(null)}>
                <Ionicons name="close" size={24} color={Colors.textStrong} />
              </TouchableOpacity>
            </View>

            {selectedFriendProfile && (
              <ScrollView style={{ maxHeight: 400 }}>
                <View style={styles.friendProfileHeader}>
                  <View style={styles.avatarCircle}>
                    <Text style={styles.avatarInitial}>
                      {selectedFriendProfile.identity.name.charAt(0).toUpperCase()}
                    </Text>
                  </View>
                  <Text style={styles.friendProfileName}>{selectedFriendProfile.identity.name}</Text>
                  <Text style={styles.friendProfileSub}>
                    {selectedFriendProfile.identity.username ? `@${selectedFriendProfile.identity.username}` : ''}
                  </Text>
                </View>

                {/* Public Metrics Display (Respecting Privacy) */}
                <View style={styles.friendMetricsGrid}>
                  <View style={styles.friendMetricTile}>
                    <Text style={styles.friendMetricVal}>
                      {selectedFriendProfile.metrics.consistency != null
                        ? `${Math.round(selectedFriendProfile.metrics.consistency)}%`
                        : '—'}
                    </Text>
                    <Text style={styles.friendMetricLabel}>Consistency</Text>
                  </View>

                  <View style={styles.friendMetricTile}>
                    <Text style={styles.friendMetricVal}>
                      {selectedFriendProfile.metrics.improvement_score != null
                        ? selectedFriendProfile.metrics.improvement_score.toFixed(1)
                        : '—'}
                    </Text>
                    <Text style={styles.friendMetricLabel}>Improvement</Text>
                  </View>

                  <View style={styles.friendMetricTile}>
                    <Text style={styles.friendMetricVal}>
                      {selectedFriendProfile.metrics.experiment_effectiveness != null
                        ? `${Math.round(selectedFriendProfile.metrics.experiment_effectiveness)}%`
                        : '—'}
                    </Text>
                    <Text style={styles.friendMetricLabel}>Effectiveness</Text>
                  </View>
                </View>

                {/* Only display Current Level if returned by backend */}
                {selectedFriendProfile.metrics.current_level && (
                  <View style={styles.sharedCard}>
                    <Text style={styles.sharedLabel}>SHARED LEVEL</Text>
                    <Text style={styles.sharedVal}>{selectedFriendProfile.metrics.current_level}</Text>
                  </View>
                )}

                {/* Only display Behavior Score if made visible by friend */}
                {selectedFriendProfile.metrics.behavior_score != null && (
                  <View style={styles.sharedCard}>
                    <Text style={styles.sharedLabel}>SHARED BEHAVIOR SCORE</Text>
                    <Text style={styles.sharedVal}>
                      {selectedFriendProfile.metrics.behavior_score.toFixed(0)}
                    </Text>
                  </View>
                )}

                {/* Milestones */}
                {selectedFriendProfile.milestones.length > 0 && (
                  <View style={styles.sharedCard}>
                    <Text style={styles.sharedLabel}>MILESTONES</Text>
                    {selectedFriendProfile.milestones.map((m, i) => (
                      <Text key={i} style={styles.sharedMilestone}>• {m}</Text>
                    ))}
                  </View>
                )}
              </ScrollView>
            )}
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  container: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 100,
  },
  identityHeaderCard: {
    backgroundColor: Colors.neutralCard,
    borderRadius: 16,
    padding: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 1,
  },
  identityLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  avatarCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: Colors.primaryContainer,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarInitial: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  userName: {
    fontSize: 15,
    fontWeight: '700',
    color: Colors.textStrong,
  },
  userHandle: {
    fontSize: 12,
    color: Colors.textSubtle,
  },
  logoutBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 10,
    backgroundColor: '#FEE2E2',
  },
  logoutText: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.accentCoral,
  },
  segmentedRail: {
    flexDirection: 'row',
    backgroundColor: 'rgba(234, 230, 244, 0.6)',
    borderRadius: 24,
    padding: 4,
    marginBottom: 16,
  },
  segmentBtn: {
    flex: 1,
    paddingVertical: 8,
    borderRadius: 20,
    alignItems: 'center',
  },
  segmentBtnActive: {
    backgroundColor: Colors.primary,
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 6,
    elevation: 2,
  },
  segmentText: {
    fontSize: 11,
    fontWeight: '500',
    color: Colors.textSubtle,
  },
  segmentTextActive: {
    fontWeight: '700',
    color: Colors.onPrimary,
  },
  tabContent: {
    gap: 16,
  },
  scoreHeroCard: {
    backgroundColor: Colors.primaryContainer,
    borderRadius: 16,
    padding: 16,
    gap: 10,
    shadowColor: Colors.primaryContainer,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 10,
    elevation: 3,
  },
  scoreHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  scoreLabel: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.primaryFixedDim,
    letterSpacing: 0.5,
  },
  scoreMetricRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: 8,
    marginTop: 4,
  },
  scoreNumber: {
    fontSize: 32,
    fontWeight: '700',
    color: Colors.onPrimary,
  },
  trendPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 108, 73, 0.3)',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
    gap: 4,
  },
  trendPillText: {
    fontSize: 11,
    fontWeight: '700',
    color: Colors.secondaryFixed,
  },
  scoreSubTitle: {
    fontSize: 13,
    color: Colors.primaryFixed,
    marginTop: 2,
  },
  vsBadge: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  vsBadgeText: {
    fontSize: 10,
    color: Colors.onPrimary,
  },
  card: {
    backgroundColor: Colors.neutralCard,
    borderRadius: 16,
    padding: 14,
    shadowColor: '#64748B',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.06,
    shadowRadius: 10,
    elevation: 2,
  },
  cardHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  cardIconBox: {
    width: 28,
    height: 28,
    borderRadius: 8,
    backgroundColor: Colors.surfaceTintViolet,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cardTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.textStrong,
    marginLeft: 6,
    flex: 1,
  },
  curveList: {
    gap: 8,
  },
  curveRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  curveDate: {
    fontSize: 11,
    color: Colors.textSubtle,
    width: 75,
  },
  curveScoreBar: {
    flex: 1,
    height: 8,
    borderRadius: 4,
    backgroundColor: Colors.surfaceContainerHigh,
    overflow: 'hidden',
  },
  curveFill: {
    height: '100%',
    borderRadius: 4,
  },
  curveTrend: {
    fontSize: 10,
    fontWeight: '600',
    color: Colors.textSubtle,
    width: 60,
    textAlign: 'right',
  },
  sectionHeaderTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: Colors.textStrong,
  },
  emptyPatternsCard: {
    backgroundColor: Colors.neutralCard,
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: Colors.neutralBorder,
    borderStyle: 'dashed',
    gap: 6,
  },
  emptyPatternsTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.textStrong,
  },
  emptyPatternsSubtitle: {
    fontSize: 11,
    color: Colors.textSubtle,
    textAlign: 'center',
    lineHeight: 16,
  },
  patternCard: {
    backgroundColor: Colors.neutralCard,
    borderRadius: 14,
    padding: 14,
    flexDirection: 'row',
    gap: 12,
  },
  patternIconBox: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: Colors.surfaceTintViolet,
    alignItems: 'center',
    justifyContent: 'center',
  },
  patternTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  patternTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textStrong,
  },
  patternTagMint: {
    backgroundColor: Colors.surfaceTintMint,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  patternTagMintText: {
    fontSize: 9,
    fontWeight: '700',
    color: Colors.secondary,
  },
  patternDesc: {
    fontSize: 11,
    color: Colors.textSubtle,
    marginTop: 4,
    lineHeight: 16,
  },
  patternMeta: {
    fontSize: 10,
    color: Colors.textMuted,
    marginTop: 4,
  },
  impactHeroCard: {
    backgroundColor: Colors.neutralCard,
    borderRadius: 16,
    padding: 14,
    gap: 14,
  },
  impactTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
  },
  gradeBox: {
    width: 60,
    height: 60,
    borderRadius: 16,
    backgroundColor: Colors.surfaceTintViolet,
    alignItems: 'center',
    justifyContent: 'center',
  },
  impactSubHeader: {
    fontSize: 11,
    color: Colors.textSubtle,
  },
  impactScoreBig: {
    fontSize: 24,
    fontWeight: '700',
    color: Colors.textStrong,
  },
  metricsRow: {
    flexDirection: 'row',
    gap: 8,
  },
  metricTile: {
    flex: 1,
    backgroundColor: Colors.surfaceContainerLow,
    borderRadius: 10,
    padding: 10,
  },
  metricVal: {
    fontSize: 14,
    fontWeight: '700',
    color: Colors.secondary,
  },
  metricLabel: {
    fontSize: 10,
    color: Colors.textSubtle,
    marginTop: 2,
  },
  milestoneRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  milestoneText: {
    fontSize: 12,
    color: Colors.textStrong,
  },
  addFriendHeaderBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: Colors.primary,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 12,
  },
  addFriendHeaderText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  emptyFriendsCard: {
    backgroundColor: Colors.surfaceContainerLow,
    borderRadius: 12,
    padding: 24,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginTop: 10,
  },
  emptyFriendsTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.textStrong,
  },
  emptyFriendsSubtitle: {
    fontSize: 11,
    color: Colors.textSubtle,
    textAlign: 'center',
  },
  friendRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: Colors.neutralBorder,
  },
  friendAvatar: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.surfaceTintViolet,
    alignItems: 'center',
    justifyContent: 'center',
  },
  friendInitial: {
    fontSize: 14,
    fontWeight: '700',
    color: Colors.primary,
  },
  friendName: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.textStrong,
  },
  friendSub: {
    fontSize: 10,
    color: Colors.textSubtle,
  },
  privacyLinkCard: {
    backgroundColor: Colors.surfaceContainer,
    borderRadius: 16,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    borderWidth: 1,
    borderColor: Colors.neutralBorder,
  },
  privacyLinkTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: Colors.textStrong,
    marginBottom: 2,
  },
  privacyLinkSubtitle: {
    fontSize: 11,
    color: Colors.textSubtle,
    lineHeight: 15,
  },
  emptyContainer: {
    padding: 20,
    alignItems: 'center',
    gap: 6,
  },
  emptyText: {
    fontSize: 11,
    color: Colors.textSubtle,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    padding: 20,
  },
  modalContent: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 20,
    gap: 12,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  modalTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: Colors.textStrong,
  },
  inputLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.textSubtle,
  },
  modalInput: {
    backgroundColor: '#F5F3FF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E2F7',
    paddingHorizontal: 14,
    paddingVertical: 10,
    fontSize: 14,
    color: Colors.textStrong,
  },
  modalSubmitBtn: {
    backgroundColor: Colors.primary,
    borderRadius: 14,
    paddingVertical: 12,
    alignItems: 'center',
    marginTop: 8,
  },
  modalSubmitText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  friendProfileHeader: {
    alignItems: 'center',
    marginVertical: 10,
    gap: 4,
  },
  friendProfileName: {
    fontSize: 16,
    fontWeight: '700',
    color: Colors.textStrong,
  },
  friendProfileSub: {
    fontSize: 12,
    color: Colors.textSubtle,
  },
  friendMetricsGrid: {
    flexDirection: 'row',
    gap: 8,
    marginVertical: 12,
  },
  friendMetricTile: {
    flex: 1,
    backgroundColor: '#F3F1FB',
    borderRadius: 10,
    padding: 10,
    alignItems: 'center',
  },
  friendMetricVal: {
    fontSize: 15,
    fontWeight: '700',
    color: Colors.secondary,
  },
  friendMetricLabel: {
    fontSize: 10,
    color: Colors.textSubtle,
    marginTop: 2,
  },
  sharedCard: {
    backgroundColor: '#F9F8FE',
    borderRadius: 10,
    padding: 10,
    marginBottom: 8,
  },
  sharedLabel: {
    fontSize: 9,
    fontWeight: '700',
    color: Colors.primary,
    letterSpacing: 0.5,
  },
  sharedVal: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.textStrong,
    marginTop: 2,
  },
  sharedMilestone: {
    fontSize: 11,
    color: Colors.textStrong,
    marginTop: 2,
  },
  incomingRequestsCard: {
    borderWidth: 1,
    borderColor: '#BAE6FD',
    backgroundColor: '#F0F9FF',
  },
  requestCountBadge: {
    backgroundColor: Colors.primary,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
    marginLeft: 6,
  },
  requestCountText: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '700',
  },
  requestItemRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: '#FFFFFF',
    padding: 10,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: Colors.neutralBorder,
  },
  requestAvatar: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: Colors.surfaceTintViolet,
    alignItems: 'center',
    justifyContent: 'center',
  },
  requestInitial: {
    fontSize: 15,
    fontWeight: '700',
    color: Colors.primary,
  },
  requestName: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textStrong,
  },
  requestHandle: {
    fontSize: 11,
    color: Colors.textSubtle,
  },
  requestActionButtons: {
    flexDirection: 'row',
    gap: 6,
  },
  acceptBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: Colors.secondary,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
  },
  acceptBtnText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
  },
  declineBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#FEE2E2',
    paddingHorizontal: 8,
    paddingVertical: 6,
    borderRadius: 8,
  },
  declineBtnText: {
    color: Colors.accentCoral,
    fontSize: 12,
    fontWeight: '600',
  },
  cancelBtn: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: '#F3F4F6',
  },
  cancelBtnText: {
    color: Colors.textSubtle,
    fontSize: 12,
    fontWeight: '600',
  },
  searchRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 8,
  },
  searchInputContainer: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F5F3FF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E2F7',
    paddingHorizontal: 12,
  },
  atSymbol: {
    fontSize: 15,
    fontWeight: '700',
    color: Colors.primary,
    marginRight: 4,
  },
  usernameInput: {
    flex: 1,
    paddingVertical: 10,
    fontSize: 14,
    color: Colors.textStrong,
  },
  searchActionBtn: {
    backgroundColor: Colors.primary,
    borderRadius: 12,
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  searchErrorBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#FFF1F2',
    padding: 10,
    borderRadius: 10,
    marginTop: 4,
  },
  searchErrorText: {
    fontSize: 12,
    color: Colors.accentCoral,
    flex: 1,
  },
  previewCard: {
    backgroundColor: '#F9F8FE',
    borderRadius: 14,
    padding: 14,
    borderWidth: 1,
    borderColor: '#E9E5F5',
    marginTop: 8,
  },
  previewHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  previewAvatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: Colors.primaryContainer,
    alignItems: 'center',
    justifyContent: 'center',
  },
  previewInitial: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  previewName: {
    fontSize: 15,
    fontWeight: '700',
    color: Colors.textStrong,
  },
  previewHandle: {
    fontSize: 12,
    color: Colors.primary,
    fontWeight: '600',
  },
  previewBio: {
    fontSize: 11,
    color: Colors.textSubtle,
    marginTop: 2,
    lineHeight: 15,
  },
  previewActionBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: Colors.primary,
    borderRadius: 12,
    paddingVertical: 10,
  },
  previewActionBtnText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '700',
  },
  statusPillNeutral: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#F1F5F9',
    borderRadius: 10,
    paddingVertical: 8,
  },
  statusPillNeutralText: {
    fontSize: 12,
    color: Colors.textSubtle,
    fontWeight: '600',
  },
  statusPillSuccess: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#ECFDF5',
    borderRadius: 10,
    paddingVertical: 8,
  },
  statusPillSuccessText: {
    fontSize: 12,
    color: Colors.secondary,
    fontWeight: '600',
  },
  statusPillPending: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#FEF3C7',
    borderRadius: 10,
    paddingVertical: 8,
  },
  statusPillPendingText: {
    fontSize: 12,
    color: '#D97706',
    fontWeight: '600',
  },
});
