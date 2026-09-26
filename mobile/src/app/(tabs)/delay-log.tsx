import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Header } from '@/components/Header';
import { Colors } from '@/constants/theme';

export default function DelayLogScreen() {
  const router = useRouter();
  const [seconds, setSeconds] = useState(18 * 60 + 45);
  const [isReadyStarted, setIsReadyStarted] = useState(false);
  const [isBreathing, setIsBreathing] = useState(false);

  // Live timer tick to simulate mindful real-time awareness
  useEffect(() => {
    const timer = setInterval(() => {
      setSeconds((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTime = (totalSecs: number) => {
    const mins = Math.floor(totalSecs / 60);
    const secs = totalSecs % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  const handleReadyPress = () => {
    setIsReadyStarted(true);
    setTimeout(() => {
      router.push('/');
    }, 1200);
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
              <View style={styles.pulseDot} />
              <Text style={styles.livePulseText}>Adaptive Pause</Text>
            </View>
          </View>
          <Text style={styles.mainTitle}>Friction Intercept</Text>
          <Text style={styles.subTitle}>No guilt. Just clear awareness to gently reset your momentum.</Text>
        </View>

        {/* Circular Gauge Card */}
        <View style={styles.gaugeCard}>
          <View style={styles.circularDial}>
            <View style={styles.dialInner}>
              <Text style={styles.timeDisplay}>{formatTime(seconds)}</Text>
              <Text style={styles.dialSubLabel}>Elapsed Friction</Text>
              <View style={styles.driftBadge}>
                <Ionicons name="trending-up" size={12} color={Colors.accentCoral} />
                <Text style={styles.driftText}>+2m drift</Text>
              </View>
            </View>
          </View>

          {/* Intended Target Context */}
          <View style={styles.targetBox}>
            <View style={styles.targetHeader}>
              <Text style={styles.targetLabel}>SCHEDULED TARGET</Text>
              <View style={styles.frictionTag}>
                <View style={styles.redDot} />
                <Text style={styles.frictionTagText}>High Friction</Text>
              </View>
            </View>
            <View style={styles.targetTitleRow}>
              <View style={styles.terminalIcon}>
                <Ionicons name="terminal-outline" size={16} color={Colors.primary} />
              </View>
              <Text style={styles.targetTitle}>Drafting Architecture Spec</Text>
            </View>
          </View>
        </View>

        {/* Primary Ergonomic Actions */}
        <View style={styles.actionsContainer}>
          <TouchableOpacity
            style={[
              styles.btnReady,
              isReadyStarted && { backgroundColor: Colors.primary },
            ]}
            onPress={handleReadyPress}
            activeOpacity={0.85}
          >
            <Ionicons
              name={isReadyStarted ? 'sparkles' : 'checkmark-circle'}
              size={22}
              color={Colors.onSecondary}
            />
            <Text style={styles.btnReadyText}>
              {isReadyStarted ? "Let's Flow! Redirecting..." : "I'm Ready to Start Task"}
            </Text>
          </TouchableOpacity>

          <View style={styles.dualActionsRow}>
            <TouchableOpacity
              style={styles.btnBreathe}
              onPress={handleBreathePress}
              activeOpacity={0.8}
            >
              <Ionicons
                name="body-outline"
                size={18}
                color={Colors.secondary}
              />
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
                Starting is the only real barrier. Would typing just a single bullet point or opening the blank workspace feel manageable right now?
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

            <TouchableOpacity style={styles.choiceBtnSecondary}>
              <View style={styles.choiceLeft}>
                <Ionicons name="git-branch-outline" size={16} color={Colors.textSubtle} />
                <Text style={styles.choiceTextSecondary}>Still feeling stuck (Break it down)</Text>
              </View>
              <Ionicons name="options-outline" size={16} color={Colors.textSubtle} />
            </TouchableOpacity>
          </View>
        </View>

        {/* Telemetry Section */}
        <View style={styles.telemetrySection}>
          <View style={styles.telemetryHeader}>
            <Text style={styles.telemetryTitle}>CONTEXTUAL TELEMETRY (LOCAL)</Text>
            <View style={styles.onDeviceTag}>
              <Ionicons name="lock-closed" size={12} color={Colors.textSubtle} />
              <Text style={styles.onDeviceText}>On-device only</Text>
            </View>
          </View>

          <View style={styles.telemetryGrid}>
            <View style={styles.telemetryCard}>
              <View style={[styles.appIconBox, { backgroundColor: Colors.surfaceTintRose }]}>
                <Ionicons name="logo-youtube" size={18} color={Colors.accentCoral} />
              </View>
              <View>
                <Text style={styles.telemetryMetric}>12m active</Text>
                <Text style={styles.telemetrySub}>YouTube Feed</Text>
              </View>
            </View>

            <View style={styles.telemetryCard}>
              <View style={[styles.appIconBox, { backgroundColor: Colors.surfaceTintBlue }]}>
                <Ionicons name="chatbubbles-outline" size={18} color={Colors.accentSky} />
              </View>
              <View>
                <Text style={styles.telemetryMetric}>4m active</Text>
                <Text style={styles.telemetrySub}>Social & Feeds</Text>
              </View>
            </View>
          </View>

          {/* Sleep Telemetry Banner */}
          <View style={styles.sleepBanner}>
            <View style={styles.sleepIconBox}>
              <Ionicons name="bed-outline" size={16} color={Colors.tertiary} />
            </View>
            <View style={{ flex: 1 }}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                <Text style={styles.sleepTitle}>5h 40m Sleep Recorded</Text>
                <View style={styles.resourceBadge}>
                  <Text style={styles.resourceText}>Reduced Resource</Text>
                </View>
              </View>
              <Text style={styles.sleepDesc}>
                Short sleep elevates executive friction and start resistance. Lower your expectations for today's opening 10 minutes.
              </Text>
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
              <Text style={styles.ledgerTitle}>Attribution Ledger</Text>
            </View>
            <View style={styles.auditBadge}>
              <Text style={styles.auditBadgeText}>Audit Ready</Text>
            </View>
          </View>

          <View style={styles.ledgerMetricsGrid}>
            <View style={styles.ledgerMetricTile}>
              <Text style={[styles.ledgerValue, { color: Colors.primary }]}>1 Episode</Text>
              <Text style={styles.ledgerSub}>User-Confirmed Log</Text>
            </View>
            <View style={styles.ledgerMetricTile}>
              <Text style={styles.ledgerValue}>0 Overrides</Text>
              <Text style={styles.ledgerSub}>Algorithmic Presumptions</Text>
            </View>
          </View>

          <Text style={styles.ledgerFooterNote}>
            🛡️ Your data remains 100% on-device. Zero automated verdicts are stored without explicit confirmation.
          </Text>
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
    color: Colors.accentCoral,
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
    backgroundColor: Colors.surfaceTintRose,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
    gap: 4,
  },
  redDot: {
    width: 4,
    height: 4,
    borderRadius: 2,
    backgroundColor: Colors.accentCoral,
  },
  frictionTagText: {
    fontSize: 10,
    fontWeight: '600',
    color: Colors.accentCoral,
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
  choiceBtnSecondary: {
    backgroundColor: Colors.neutralCanvas,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  choiceTextSecondary: {
    fontSize: 12,
    color: Colors.textSubtle,
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
    padding: 10,
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
  },
  sleepBanner: {
    backgroundColor: Colors.surfaceTintAmber,
    borderRadius: 12,
    padding: 12,
    flexDirection: 'row',
    gap: 10,
  },
  sleepIconBox: {
    width: 28,
    height: 28,
    borderRadius: 8,
    backgroundColor: Colors.tertiaryFixed,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sleepTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: Colors.tertiary,
  },
  resourceBadge: {
    backgroundColor: 'rgba(129, 81, 0, 0.1)',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  resourceText: {
    fontSize: 9,
    fontWeight: '600',
    color: Colors.tertiary,
  },
  sleepDesc: {
    fontSize: 11,
    color: Colors.tertiary,
    marginTop: 4,
    lineHeight: 16,
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
});
