import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Header } from '@/components/Header';
import { Colors } from '@/constants/theme';
import { procrastinationService } from '@/services/procrastination';
import { ProcrastinationEventResponse } from '@/types/procrastination';
import { useBehavior } from '@/hooks/useBehavior';
import { useTasks } from '@/hooks/useTasks';
import { useProcrastination } from '@/hooks/useProcrastination';
import { formatTimestamp, formatSeconds } from '@/utils/formatters';

export default function DelayLogScreen() {
  const router = useRouter();
  const { summary, refresh: refreshBehavior } = useBehavior();
  const { tasks } = useTasks();
  const {
    events,
    isLoading: eventsLoading,
    error: eventsError,
    fetchEvents,
    startEvent,
    endEvent,
  } = useProcrastination();

  const [activeEvent, setActiveEvent] = useState<ProcrastinationEventResponse | null>(null);
  const [seconds, setSeconds] = useState(0);
  const [isStarting, setIsStarting] = useState(false);
  const [isEnding, setIsEnding] = useState(false);
  const [isBreathing, setIsBreathing] = useState(false);
  const [completionNotice, setCompletionNotice] = useState<string | null>(null);

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (activeEvent) {
      timerRef.current = setInterval(() => {
        setSeconds((prev) => prev + 1);
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      setSeconds(0);
    }

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [activeEvent]);

  const formatTime = (totalSecs: number) => {
    const mins = Math.floor(totalSecs / 60);
    const secs = totalSecs % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  const handleStartEpisode = async () => {
    try {
      setIsStarting(true);
      setCompletionNotice(null);
      const firstTask = tasks[0];
      const event = await startEvent({
        task_id: firstTask ? firstTask.id : undefined,
        started_at: new Date().toISOString(),
        trigger_reason: 'Mindful Delay Check',
        notes: 'User initiated friction intercept',
      });
      setActiveEvent(event);
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Could not start delay episode');
    } finally {
      setIsStarting(false);
    }
  };

  const handleEndEpisode = async () => {
    if (!activeEvent) {
      // If no active event, redirect to tasks
      router.push('/');
      return;
    }

    try {
      setIsEnding(true);
      await endEvent(activeEvent.id, {
        ended_at: new Date().toISOString(),
        notes: `Ended with ${formatTime(seconds)} elapsed friction`,
      });
      setActiveEvent(null);
      setCompletionNotice(`Mindful pause concluded (${formatTime(seconds)}). Momentum restored!`);
      await refreshBehavior();
      setTimeout(() => {
        router.push('/');
      }, 1500);
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Could not finalize delay episode');
    } finally {
      setIsEnding(false);
    }
  };

  const handleBreathePress = () => {
    setIsBreathing(true);
    setTimeout(() => setIsBreathing(false), 3000);
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <Header title="Delay Log" />

      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Nudge Header */}
        <View style={styles.nudgeBanner}>
          <View style={styles.nudgeTopRow}>
            <View style={styles.nudgeTag}>
              <Ionicons name="leaf-outline" size={14} color={Colors.primary} />
              <Text style={styles.nudgeTagText}>COMPASSIONATE NUDGE</Text>
            </View>
            <View style={styles.livePulseRow}>
              <View style={[styles.pulseDot, activeEvent && { backgroundColor: Colors.accentCoral }]} />
              <Text style={styles.livePulseText}>
                {activeEvent ? 'Active Friction Tracking' : 'Ready to Pause'}
              </Text>
            </View>
          </View>
          <Text style={styles.mainTitle}>Friction Intercept</Text>
          <Text style={styles.subTitle}>
            No guilt. Authoritative backend event logging to gently understand resistance patterns.
          </Text>
        </View>

        {/* Completion notice */}
        {completionNotice && (
          <View style={styles.completionBanner}>
            <Ionicons name="sparkles" size={18} color={Colors.secondary} />
            <Text style={styles.completionText}>{completionNotice}</Text>
          </View>
        )}

        {/* Circular Gauge Card */}
        <View style={styles.gaugeCard}>
          <View style={styles.circularDial}>
            <View style={styles.dialInner}>
              <Text style={styles.timeDisplay}>{formatTime(seconds)}</Text>
              <Text style={styles.dialSubLabel}>
                {activeEvent ? 'Elapsed Friction (Live)' : 'Timer Inactive'}
              </Text>
              <View style={styles.driftBadge}>
                <Ionicons
                  name={activeEvent ? 'alert-circle-outline' : 'checkmark-outline'}
                  size={12}
                  color={activeEvent ? Colors.accentCoral : Colors.secondary}
                />
                <Text
                  style={[
                    styles.driftText,
                    { color: activeEvent ? Colors.accentCoral : Colors.secondary },
                  ]}
                >
                  {activeEvent ? `Event: #${activeEvent.id.slice(0, 8)}` : 'Zero active drift'}
                </Text>
              </View>
            </View>
          </View>

          {/* Intended Target Context */}
          <View style={styles.targetBox}>
            <View style={styles.targetHeader}>
              <Text style={styles.targetLabel}>SCHEDULED TARGET</Text>
              <View style={styles.frictionTag}>
                <Text style={[styles.frictionTagText, { color: Colors.textSubtle }]}>
                  {activeEvent ? 'In Delay Window' : 'Idle'}
                </Text>
              </View>
            </View>
            <View style={styles.targetTitleRow}>
              <View style={styles.terminalIcon}>
                <Ionicons name="terminal-outline" size={16} color={Colors.primary} />
              </View>
              <Text style={styles.targetTitle}>
                {tasks.length > 0 ? tasks[0].name : 'General Work Session'}
              </Text>
            </View>
          </View>
        </View>

        {/* Primary Ergonomic Actions */}
        <View style={styles.actionsContainer}>
          {activeEvent ? (
            <TouchableOpacity
              style={styles.btnReady}
              onPress={handleEndEpisode}
              disabled={isEnding}
              activeOpacity={0.85}
            >
              {isEnding ? (
                <ActivityIndicator color="#FFFFFF" size="small" />
              ) : (
                <>
                  <Ionicons name="checkmark-circle" size={22} color={Colors.onSecondary} />
                  <Text style={styles.btnReadyText}>I'm Ready to Start Task</Text>
                </>
              )}
            </TouchableOpacity>
          ) : (
            <TouchableOpacity
              style={[styles.btnStart, isStarting && { opacity: 0.6 }]}
              onPress={handleStartEpisode}
              disabled={isStarting}
              activeOpacity={0.85}
            >
              {isStarting ? (
                <ActivityIndicator color="#FFFFFF" size="small" />
              ) : (
                <>
                  <Ionicons name="play-circle-outline" size={22} color="#FFFFFF" />
                  <Text style={styles.btnStartText}>Start Mindful Delay Check</Text>
                </>
              )}
            </TouchableOpacity>
          )}

          <View style={styles.dualActionsRow}>
            <TouchableOpacity
              style={styles.btnBreathe}
              onPress={handleBreathePress}
              activeOpacity={0.8}
            >
              <Ionicons name="body-outline" size={18} color={Colors.secondary} />
              <Text style={styles.btnBreatheText}>
                {isBreathing ? 'Hold... Exhale' : '5-Min Breathe'}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.btnDismiss}
              onPress={() => router.push('/')}
              activeOpacity={0.8}
            >
              <Ionicons name="close-outline" size={18} color={Colors.onSurfaceVariant} />
              <Text style={styles.btnDismissText}>Dismiss Window</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* 2-Minute Cognitive Reset Card */}
        <View style={styles.resetCard}>
          <View style={styles.resetHeader}>
            <View style={styles.lightbulbBox}>
              <Ionicons name="bulb-outline" size={18} color={Colors.tertiary} />
            </View>
            <View style={{ flex: 1 }}>
              <View style={styles.resetTitleRow}>
                <Text style={styles.resetTitle}>2-MINUTE COGNITIVE RESET</Text>
                <View style={styles.microTag}>
                  <Text style={styles.microTagText}>Micro-Commitment</Text>
                </View>
              </View>
              <Text style={styles.resetDesc}>
                Starting is the hardest step. Would typing just a single bullet point or opening the blank workspace feel manageable right now?
              </Text>
            </View>
          </View>

          <View style={styles.choiceContainer}>
            <TouchableOpacity
              style={styles.choiceBtnPrimary}
              onPress={() => router.push('/')}
            >
              <View style={styles.choiceLeft}>
                <Ionicons name="create-outline" size={16} color={Colors.primary} />
                <Text style={styles.choiceTextPrimary}>Yes, open draft for 1 sentence</Text>
              </View>
              <Ionicons name="arrow-forward" size={16} color={Colors.primary} />
            </TouchableOpacity>
          </View>
        </View>

        {/* Telemetry Section (Honest Device State) */}
        <View style={styles.telemetrySection}>
          <View style={styles.telemetryHeader}>
            <Text style={styles.telemetryTitle}>DEVICE TELEMETRY STATUS</Text>
            <View style={styles.onDeviceTag}>
              <Ionicons name="lock-closed" size={12} color={Colors.textSubtle} />
              <Text style={styles.onDeviceText}>Privacy Protected</Text>
            </View>
          </View>

          <View style={styles.telemetryGrid}>
            <View style={styles.telemetryCard}>
              <View style={[styles.appIconBox, { backgroundColor: Colors.surfaceTintRose }]}>
                <Ionicons name="apps-outline" size={18} color={Colors.accentCoral} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.telemetryMetric}>Native OS Hook</Text>
                <Text style={styles.telemetrySub}>App Tracking Awaiting Permissions</Text>
              </View>
            </View>
          </View>
        </View>

        {/* Attribution Ledger Card */}
        <View style={styles.ledgerCard}>
          <View style={styles.ledgerHeader}>
            <View style={styles.ledgerTitleRow}>
              <View style={styles.shieldBox}>
                <Ionicons name="shield-checkmark" size={14} color={Colors.secondary} />
              </View>
              <Text style={styles.ledgerTitle}>Verified Friction Ledger</Text>
            </View>
            <View style={styles.auditBadge}>
              <Text style={styles.auditBadgeText}>Backend Verified</Text>
            </View>
          </View>

          <View style={styles.ledgerMetricsGrid}>
            <View style={styles.ledgerMetricTile}>
              <Text style={[styles.ledgerValue, { color: Colors.primary }]}>
                {summary?.procrastination_count ?? 0} Episodes
              </Text>
              <Text style={styles.ledgerSub}>Recorded Friction Checks</Text>
            </View>
            <View style={styles.ledgerMetricTile}>
              <Text style={styles.ledgerValue}>
                {summary?.total_procrastination_minutes ?? 0} Mins
              </Text>
              <Text style={styles.ledgerSub}>Total Paused Duration</Text>
            </View>
          </View>

          <Text style={styles.ledgerFooterNote}>
            🛡️ Your behavioral events are stored authoritatively on your FocusLoop backend. Zero automated verdicts are rendered without user confirmation.
          </Text>
        </View>

        {/* Recent Delay Episodes (Historical Procrastination Events) */}
        <View style={styles.historySectionHeader}>
          <View style={styles.historyTitleRow}>
            <Ionicons name="time-outline" size={16} color={Colors.primary} />
            <Text style={styles.historySectionTitle}>Recent Delay Episodes</Text>
            {events.length > 0 && (
              <View style={styles.historyCountBadge}>
                <Text style={styles.historyCountBadgeText}>{events.length}</Text>
              </View>
            )}
          </View>
          {events.length > 0 && (
            <TouchableOpacity
              onPress={() => fetchEvents()}
              hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
            >
              <Ionicons name="refresh-outline" size={16} color={Colors.primary} />
            </TouchableOpacity>
          )}
        </View>

        <View style={styles.historyList}>
          {eventsLoading && events.length === 0 ? (
            <View style={styles.loadingBox}>
              <ActivityIndicator size="small" color={Colors.primary} />
              <Text style={styles.loadingText}>Loading delay history...</Text>
            </View>
          ) : eventsError ? (
            <View style={styles.errorBox}>
              <Ionicons name="alert-circle-outline" size={24} color="#DC2626" />
              <Text style={styles.errorBoxText}>{eventsError}</Text>
              <TouchableOpacity
                style={styles.retryBtn}
                onPress={() => fetchEvents()}
                activeOpacity={0.8}
              >
                <Ionicons name="refresh" size={14} color={Colors.primary} />
                <Text style={styles.retryBtnText}>Try again</Text>
              </TouchableOpacity>
            </View>
          ) : events.length === 0 ? (
            <View style={styles.emptyHistoryCard}>
              <Ionicons name="shield-outline" size={28} color={Colors.textMuted} />
              <Text style={styles.emptyHistoryTitle}>No delay episodes yet</Text>
              <Text style={styles.emptyHistorySubtitle}>
                Your confirmed procrastination episodes will appear here.
              </Text>
            </View>
          ) : (
            events.map((event) => {
              const matchedTask = tasks.find((t) => t.id === event.task_id);
              const targetName = matchedTask
                ? matchedTask.name
                : (event.task_id ? 'Task Session' : 'Mindful Friction Intercept');

              return (
                <View key={event.id} style={styles.episodeCard}>
                  <View style={styles.episodeTopRow}>
                    <View style={{ flex: 1, marginRight: 8 }}>
                      <Text style={styles.episodeDate}>
                        {formatTimestamp(event.started_at || event.created_at)}
                      </Text>
                      <Text style={styles.episodeTarget}>{targetName}</Text>
                    </View>
                    <View style={styles.episodeBadge}>
                      <Ionicons name="pause-circle-outline" size={12} color={Colors.accentCoral} />
                      <Text style={styles.episodeBadgeText}>
                        {event.duration_seconds != null
                          ? formatSeconds(event.duration_seconds)
                          : (event.ended_at ? 'Concluded' : 'Active window')}
                      </Text>
                    </View>
                  </View>

                  <View style={styles.episodeDetailsRow}>
                    {event.trigger_reason && (
                      <View style={styles.episodeDetailItem}>
                        <Ionicons name="pricetag-outline" size={12} color={Colors.textSubtle} />
                        <Text style={styles.episodeDetailText}>
                          Trigger: <Text style={styles.episodeDetailValue}>{event.trigger_reason}</Text>
                        </Text>
                      </View>
                    )}
                    {event.duration_seconds != null && (
                      <View style={styles.episodeDetailItem}>
                        <Ionicons name="timer-outline" size={12} color={Colors.textSubtle} />
                        <Text style={styles.episodeDetailText}>
                          Duration: <Text style={styles.episodeDetailValue}>{formatSeconds(event.duration_seconds)}</Text>
                        </Text>
                      </View>
                    )}
                  </View>

                  {event.notes && (
                    <View style={styles.episodeNotesBox}>
                      <Ionicons name="chatbubble-ellipses-outline" size={12} color={Colors.textSubtle} />
                      <Text style={styles.episodeNotesText} numberOfLines={2}>
                        {event.notes}
                      </Text>
                    </View>
                  )}
                </View>
              );
            })
          )}
        </View>

        {/* Bottom Quote */}
        <Text style={styles.bottomQuote}>
          "Focus is a rhythm of wandering and gently returning."
        </Text>
      </ScrollView>
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
  nudgeBanner: {
    marginBottom: 16,
  },
  nudgeTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  nudgeTag: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.surfaceTintViolet,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    gap: 6,
  },
  nudgeTagText: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.primary,
    letterSpacing: 0.5,
  },
  livePulseRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  pulseDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: Colors.secondary,
  },
  livePulseText: {
    fontSize: 11,
    color: Colors.textSubtle,
  },
  mainTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: Colors.textStrong,
  },
  subTitle: {
    fontSize: 13,
    color: Colors.textSubtle,
    marginTop: 2,
    lineHeight: 18,
  },
  completionBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: Colors.surfaceTintMint,
    borderRadius: 12,
    padding: 12,
    marginBottom: 16,
  },
  completionText: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.secondary,
  },
  gaugeCard: {
    backgroundColor: Colors.neutralCard,
    borderRadius: 16,
    padding: 16,
    alignItems: 'center',
    marginBottom: 16,
    shadowColor: Colors.primaryContainer,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 12,
    elevation: 3,
  },
  circularDial: {
    width: 170,
    height: 170,
    borderRadius: 85,
    borderWidth: 8,
    borderColor: Colors.surfaceContainer,
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: 8,
  },
  dialInner: {
    alignItems: 'center',
  },
  timeDisplay: {
    fontSize: 32,
    fontWeight: '700',
    color: Colors.textStrong,
  },
  dialSubLabel: {
    fontSize: 11,
    color: Colors.textSubtle,
    marginTop: 2,
  },
  driftBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.surfaceTintRose,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
    marginTop: 4,
    gap: 4,
  },
  driftText: {
    fontSize: 10,
    fontWeight: '700',
  },
  targetBox: {
    width: '100%',
    backgroundColor: Colors.neutralCanvas,
    borderRadius: 12,
    padding: 12,
    marginTop: 12,
  },
  targetHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  targetLabel: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.textSubtle,
    letterSpacing: 0.5,
  },
  frictionTag: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.surfaceContainer,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
  },
  frictionTagText: {
    fontSize: 10,
    fontWeight: '600',
  },
  targetTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 6,
  },
  terminalIcon: {
    width: 28,
    height: 28,
    borderRadius: 8,
    backgroundColor: Colors.primaryFixed,
    alignItems: 'center',
    justifyContent: 'center',
  },
  targetTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textStrong,
  },
  actionsContainer: {
    gap: 10,
    marginBottom: 16,
  },
  btnStart: {
    height: 52,
    borderRadius: 26,
    backgroundColor: Colors.primary,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 10,
    elevation: 4,
  },
  btnStartText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  btnReady: {
    height: 52,
    borderRadius: 26,
    backgroundColor: Colors.secondary,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    shadowColor: Colors.secondary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 10,
    elevation: 4,
  },
  btnReadyText: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.onSecondary,
  },
  dualActionsRow: {
    flexDirection: 'row',
    gap: 10,
  },
  btnBreathe: {
    flex: 1,
    height: 44,
    borderRadius: 22,
    backgroundColor: Colors.surfaceTintMint,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  btnBreatheText: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.secondary,
  },
  btnDismiss: {
    flex: 1,
    height: 44,
    borderRadius: 22,
    backgroundColor: Colors.surfaceContainer,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  btnDismissText: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.onSurfaceVariant,
  },
  resetCard: {
    backgroundColor: Colors.neutralCard,
    borderRadius: 16,
    padding: 14,
    marginBottom: 16,
    shadowColor: '#64748B',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.06,
    shadowRadius: 10,
    elevation: 2,
  },
  resetHeader: {
    flexDirection: 'row',
    gap: 10,
  },
  lightbulbBox: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: Colors.surfaceTintAmber,
    alignItems: 'center',
    justifyContent: 'center',
  },
  resetTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  resetTitle: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.tertiary,
    letterSpacing: 0.5,
  },
  microTag: {
    backgroundColor: Colors.surfaceTintMint,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 8,
  },
  microTagText: {
    fontSize: 10,
    fontWeight: '600',
    color: Colors.secondary,
  },
  resetDesc: {
    fontSize: 12,
    color: Colors.textStrong,
    marginTop: 4,
    lineHeight: 18,
  },
  choiceContainer: {
    marginTop: 12,
    gap: 8,
  },
  choiceBtnPrimary: {
    backgroundColor: Colors.surfaceTintViolet,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  choiceLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  choiceTextPrimary: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.primary,
  },
  telemetrySection: {
    marginBottom: 16,
    gap: 10,
  },
  telemetryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  telemetryTitle: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.textSubtle,
    letterSpacing: 0.5,
  },
  onDeviceTag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  onDeviceText: {
    fontSize: 10,
    color: Colors.textSubtle,
  },
  telemetryGrid: {
    flexDirection: 'row',
    gap: 10,
  },
  telemetryCard: {
    flex: 1,
    backgroundColor: Colors.neutralCard,
    borderRadius: 12,
    padding: 12,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  appIconBox: {
    width: 32,
    height: 32,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  telemetryMetric: {
    fontSize: 13,
    fontWeight: '700',
    color: Colors.textStrong,
  },
  telemetrySub: {
    fontSize: 10,
    color: Colors.textSubtle,
    marginTop: 2,
  },
  ledgerCard: {
    backgroundColor: Colors.neutralCard,
    borderRadius: 12,
    padding: 12,
    marginBottom: 16,
    gap: 10,
  },
  ledgerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  ledgerTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  shieldBox: {
    width: 20,
    height: 20,
    borderRadius: 4,
    backgroundColor: Colors.secondaryFixed,
    alignItems: 'center',
    justifyContent: 'center',
  },
  ledgerTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: Colors.textStrong,
  },
  auditBadge: {
    backgroundColor: Colors.surfaceContainer,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  auditBadgeText: {
    fontSize: 10,
    fontWeight: '600',
    color: Colors.onSurfaceVariant,
  },
  ledgerMetricsGrid: {
    flexDirection: 'row',
    backgroundColor: Colors.neutralCanvas,
    borderRadius: 8,
    padding: 10,
    gap: 10,
  },
  ledgerMetricTile: {
    flex: 1,
  },
  ledgerValue: {
    fontSize: 14,
    fontWeight: '700',
    color: Colors.textStrong,
  },
  ledgerSub: {
    fontSize: 10,
    color: Colors.textSubtle,
    marginTop: 2,
  },
  ledgerFooterNote: {
    fontSize: 11,
    color: Colors.textSubtle,
    lineHeight: 16,
  },
  bottomQuote: {
    fontSize: 11,
    fontStyle: 'italic',
    color: Colors.textSubtle,
    textAlign: 'center',
    marginTop: 4,
  },
  historySectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
    marginTop: 8,
  },
  historyTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  historySectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: Colors.textStrong,
  },
  historyCountBadge: {
    backgroundColor: Colors.surfaceTintViolet,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  historyCountBadgeText: {
    fontSize: 11,
    fontWeight: '700',
    color: Colors.primary,
  },
  historyList: {
    gap: 10,
    marginBottom: 24,
  },
  loadingBox: {
    padding: 24,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  loadingText: {
    fontSize: 12,
    color: Colors.textSubtle,
  },
  errorBox: {
    backgroundColor: '#FEE2E2',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    gap: 6,
  },
  errorBoxText: {
    fontSize: 12,
    color: '#B91C1C',
    textAlign: 'center',
  },
  retryBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 8,
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: Colors.surfaceTintViolet,
    borderRadius: 12,
  },
  retryBtnText: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.primary,
  },
  emptyHistoryCard: {
    backgroundColor: Colors.neutralCard,
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: Colors.neutralBorder,
    borderStyle: 'dashed',
  },
  emptyHistoryTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textStrong,
    marginTop: 8,
  },
  emptyHistorySubtitle: {
    fontSize: 12,
    color: Colors.textSubtle,
    textAlign: 'center',
    marginTop: 4,
    lineHeight: 16,
    paddingHorizontal: 16,
  },
  episodeCard: {
    backgroundColor: Colors.neutralCard,
    borderRadius: 16,
    padding: 14,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.03,
    shadowRadius: 6,
    elevation: 1,
    borderWidth: 1,
    borderColor: Colors.neutralBorder,
  },
  episodeTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  episodeDate: {
    fontSize: 11,
    color: Colors.textSubtle,
  },
  episodeTarget: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textStrong,
    marginTop: 2,
  },
  episodeBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: Colors.surfaceTintRose,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  episodeBadgeText: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.accentCoral,
  },
  episodeDetailsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
    marginTop: 10,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: Colors.neutralBorder,
  },
  episodeDetailItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  episodeDetailText: {
    fontSize: 11,
    color: Colors.textSubtle,
  },
  episodeDetailValue: {
    fontWeight: '600',
    color: Colors.textStrong,
  },
  episodeNotesBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 6,
    backgroundColor: Colors.surfaceContainerLow,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  episodeNotesText: {
    fontSize: 11,
    color: Colors.textSubtle,
    fontStyle: 'italic',
    flex: 1,
  },
});
