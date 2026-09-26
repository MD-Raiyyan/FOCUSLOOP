import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Header } from '@/components/Header';
import { Colors } from '@/constants/theme';

export default function LabScreen() {
  const [isCheckedIn, setIsCheckedIn] = useState(false);

  const handleCheckIn = () => {
    setIsCheckedIn(true);
    setTimeout(() => setIsCheckedIn(false), 2000);
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <Header title="Lab" />

      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Active Experiment Hero Banner */}
        <View style={styles.heroBanner}>
          <View style={styles.heroHeaderRow}>
            <View style={styles.runningBadge}>
              <View style={styles.pulseDot} />
              <Text style={styles.runningText}>Running • Day 4 of 7</Text>
            </View>
            <View style={styles.labTag}>
              <Text style={styles.labTagText}>Lab #04</Text>
            </View>
          </View>

          <Text style={styles.heroTitle}>10-Minute Micro-Start Buffer</Text>
          <Text style={styles.heroSub}>Behavioral nudge testing inertia breaker algorithms</Text>

          {/* Progress Track */}
          <View style={styles.progressSection}>
            <View style={styles.progressTextRow}>
              <Text style={styles.progressLabel}>Experiment Cycle</Text>
              <Text style={styles.progressPercent}>57% completed</Text>
            </View>
            <View style={styles.trackBackground}>
              <View style={[styles.trackFill, { width: '57%' }]} />
            </View>
          </View>

          {/* Hypothesis Box */}
          <View style={styles.hypothesisBox}>
            <View style={styles.boxHeaderRow}>
              <Ionicons name="bulb-outline" size={14} color={Colors.primary} />
              <Text style={styles.boxHeaderText}>CORE HYPOTHESIS</Text>
            </View>
            <Text style={styles.hypothesisText}>
              Committing to just 10 minutes of low-stakes drafting on hard tasks reduces start delay by 40%.
            </Text>
          </View>

          {/* Trigger Rule Box */}
          <View style={styles.triggerBox}>
            <Ionicons name="flash-outline" size={16} color={Colors.tertiary} />
            <View style={{ flex: 1 }}>
              <Text style={styles.triggerTag}>TRIGGER RULE</Text>
              <Text style={styles.triggerText}>
                Activates automatically when afternoon initiation latency exceeds 20 minutes.
              </Text>
            </View>
          </View>
        </View>

        {/* Empirical Results Section */}
        <View style={styles.sectionHeader}>
          <View style={styles.sectionTitleRow}>
            <Ionicons name="analytics-outline" size={18} color={Colors.primary} />
            <Text style={styles.sectionTitle}>Empirical Results So Far</Text>
          </View>
          <View style={styles.confidenceBadge}>
            <Text style={styles.confidenceText}>High Confidence (86%)</Text>
          </View>
        </View>

        {/* Comparison Tiles */}
        <View style={styles.tilesGrid}>
          {/* Baseline Tile */}
          <View style={styles.tile}>
            <View style={styles.tileHeader}>
              <Text style={styles.tileLabel}>HISTORICAL</Text>
              <View style={styles.tileIconCircle}>
                <Ionicons name="time-outline" size={12} color={Colors.textSubtle} />
              </View>
            </View>
            <View style={styles.tileMetricRow}>
              <Text style={styles.tileMetricSubtle}>38</Text>
              <Text style={styles.unitText}>m</Text>
            </View>
            <Text style={styles.tileSub}>Baseline avg latency</Text>
          </View>

          {/* Current Protocol Tile */}
          <View style={[styles.tile, { backgroundColor: Colors.surfaceTintMint }]}>
            <View style={styles.tileHeader}>
              <Text style={[styles.tileLabel, { color: Colors.secondary }]}>CURRENT</Text>
              <View style={[styles.tileIconCircle, { backgroundColor: Colors.secondaryContainer }]}>
                <Ionicons name="trending-down" size={12} color={Colors.secondary} />
              </View>
            </View>
            <View style={styles.tileMetricRow}>
              <Text style={[styles.tileMetricSubtle, { color: Colors.secondary }]}>16</Text>
              <Text style={[styles.unitText, { color: Colors.secondary }]}>m</Text>
            </View>
            <Text style={[styles.tileSub, { color: Colors.secondary, fontWeight: '700' }]}>
              ↓ -57% start delay!
            </Text>
          </View>
        </View>

        {/* Trend Step Chart Card */}
        <View style={styles.chartCard}>
          <View style={styles.tileHeader}>
            <Text style={styles.tileLabel}>INITIATION FRICTION TREND</Text>
            <Text style={[styles.confidenceText, { color: Colors.secondary }]}>Consistently dropping</Text>
          </View>

          <View style={styles.chartBarsRow}>
            {/* Step 1: Baseline */}
            <View style={styles.chartBarCol}>
              <Text style={styles.barValue}>38m</Text>
              <View style={[styles.barVisual, { height: 50, backgroundColor: Colors.surfaceVariant }]} />
              <Text style={styles.barLabel}>Baseline</Text>
            </View>

            {/* Step 2: Day 2 */}
            <View style={styles.chartBarCol}>
              <Text style={[styles.barValue, { color: Colors.primary }]}>19m</Text>
              <View style={[styles.barVisual, { height: 30, backgroundColor: Colors.primaryFixedDim }]} />
              <Text style={styles.barLabel}>Day 2</Text>
            </View>

            {/* Step 3: Today */}
            <View style={styles.chartBarCol}>
              <Text style={[styles.barValue, { color: Colors.secondary, fontWeight: '700' }]}>12m</Text>
              <View style={[styles.barVisual, { height: 18, backgroundColor: Colors.secondaryFixedDim }]} />
              <Text style={[styles.barLabel, { color: Colors.textStrong, fontWeight: '600' }]}>Today</Text>
            </View>
          </View>

          <View style={styles.chartFooter}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
              <View style={styles.greenDot} />
              <Text style={styles.chartFooterText}>Statistical Significance reached</Text>
            </View>
            <TouchableOpacity>
              <Text style={styles.fullChartLink}>Full Chart</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Recent Test Sessions List */}
        <View style={styles.sectionHeader}>
          <View style={styles.sectionTitleRow}>
            <Ionicons name="flask-outline" size={18} color={Colors.primary} />
            <Text style={styles.sectionTitle}>Recent Test Sessions</Text>
          </View>
          <Text style={styles.subTextRight}>3 recorded</Text>
        </View>

        <View style={styles.sessionsList}>
          {/* Session 1 */}
          <View style={styles.sessionCard}>
            <View style={styles.sessionLeft}>
              <View style={[styles.sessionIcon, { backgroundColor: Colors.surfaceTintViolet }]}>
                <Ionicons name="document-text-outline" size={16} color={Colors.primary} />
              </View>
              <View>
                <Text style={styles.sessionTitle}>Drafting System Spec</Text>
                <Text style={styles.sessionMeta}>Today, 2:30 PM • 12m delay</Text>
              </View>
            </View>
            <View style={styles.workedBadge}>
              <Ionicons name="checkmark-circle" size={12} color={Colors.secondary} />
              <Text style={styles.workedBadgeText}>Worked</Text>
            </View>
          </View>

          {/* Session 2 */}
          <View style={styles.sessionCard}>
            <View style={styles.sessionLeft}>
              <View style={[styles.sessionIcon, { backgroundColor: Colors.surfaceTintBlue }]}>
                <Ionicons name="terminal-outline" size={16} color={Colors.accentIndigo} />
              </View>
              <View>
                <Text style={styles.sessionTitle}>Code Review Sprint</Text>
                <Text style={styles.sessionMeta}>Yesterday, 4:00 PM • 19m delay</Text>
              </View>
            </View>
            <View style={styles.partialBadge}>
              <Ionicons name="time-outline" size={12} color={Colors.tertiary} />
              <Text style={styles.partialBadgeText}>Partial</Text>
            </View>
          </View>

          {/* Session 3 */}
          <View style={styles.sessionCard}>
            <View style={styles.sessionLeft}>
              <View style={[styles.sessionIcon, { backgroundColor: Colors.surfaceTintRose }]}>
                <Ionicons name="server-outline" size={16} color={Colors.accentCoral} />
              </View>
              <View>
                <Text style={styles.sessionTitle}>Database Migration</Text>
                <Text style={styles.sessionMeta}>2 days ago • 15m delay</Text>
              </View>
            </View>
            <View style={styles.workedBadge}>
              <Ionicons name="checkmark-circle" size={12} color={Colors.secondary} />
              <Text style={styles.workedBadgeText}>Worked</Text>
            </View>
          </View>
        </View>

        {/* AI Coach Insights Box */}
        <View style={styles.aiInsightBox}>
          <View style={styles.aiAvatarCircle}>
            <Ionicons name="sparkles" size={16} color={Colors.onPrimary} />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.aiInsightHeader}>FocusLoop Engine Insight</Text>
            <Text style={styles.aiInsightText}>
              The 10-minute micro-start significantly lowers task resistance, especially following nights with {'<'}6h sleep. You are <Text style={styles.boldPrimary}>3 days away</Text> from concluding this experiment!
            </Text>
          </View>
        </View>

        {/* Action Buttons */}
        <View style={styles.actionsGroup}>
          <TouchableOpacity
            style={[styles.btnPrimary, isCheckedIn && { backgroundColor: Colors.secondary }]}
            onPress={handleCheckIn}
            activeOpacity={0.8}
          >
            <Ionicons name={isCheckedIn ? 'checkmark-circle' : 'add-circle-outline'} size={18} color={Colors.onPrimary} />
            <Text style={styles.btnPrimaryText}>
              {isCheckedIn ? 'Check-in Logged!' : 'Log Protocol Check-in'}
            </Text>
          </TouchableOpacity>

          <View style={styles.secondaryActionsRow}>
            <TouchableOpacity style={styles.btnSecondary}>
              <Ionicons name="options-outline" size={16} color={Colors.onSurfaceVariant} />
              <Text style={styles.btnSecondaryText}>Adjust Rule</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.btnAdopt}>
              <Ionicons name="ribbon-outline" size={16} color={Colors.secondary} />
              <Text style={styles.btnAdoptText}>Conclude & Adopt</Text>
            </TouchableOpacity>
          </View>
        </View>
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
  heroBanner: {
    backgroundColor: Colors.neutralCard,
    borderRadius: 16,
    padding: 16,
    marginBottom: 20,
    shadowColor: Colors.primaryContainer,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 10,
    elevation: 2,
  },
  heroHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  runningBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.secondaryFixed,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    gap: 6,
  },
  pulseDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: Colors.secondary,
  },
  runningText: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.onSecondaryFixed,
  },
  labTag: {
    backgroundColor: Colors.surfaceTintViolet,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 10,
  },
  labTagText: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.primary,
  },
  heroTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: Colors.textStrong,
  },
  heroSub: {
    fontSize: 12,
    color: Colors.textSubtle,
    marginTop: 2,
  },
  progressSection: {
    marginTop: 12,
    gap: 4,
  },
  progressTextRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  progressLabel: {
    fontSize: 10,
    color: Colors.textSubtle,
  },
  progressPercent: {
    fontSize: 10,
    fontWeight: '600',
    color: Colors.primary,
  },
  trackBackground: {
    height: 8,
    borderRadius: 4,
    backgroundColor: Colors.surfaceContainer,
    overflow: 'hidden',
  },
  trackFill: {
    height: '100%',
    borderRadius: 4,
    backgroundColor: Colors.primaryContainer,
  },
  hypothesisBox: {
    backgroundColor: Colors.surfaceContainerLow,
    borderRadius: 12,
    padding: 10,
    marginTop: 12,
  },
  boxHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  boxHeaderText: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.primary,
    letterSpacing: 0.5,
  },
  hypothesisText: {
    fontSize: 12,
    color: Colors.onSurface,
    marginTop: 4,
    lineHeight: 16,
  },
  triggerBox: {
    backgroundColor: Colors.surfaceTintAmber,
    borderRadius: 12,
    padding: 10,
    marginTop: 8,
    flexDirection: 'row',
    gap: 8,
    alignItems: 'flex-start',
  },
  triggerTag: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.tertiary,
    letterSpacing: 0.5,
  },
  triggerText: {
    fontSize: 11,
    color: Colors.onSurface,
    marginTop: 2,
    lineHeight: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  sectionTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: Colors.textStrong,
  },
  confidenceBadge: {
    backgroundColor: Colors.surfaceTintMint,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  confidenceText: {
    fontSize: 10,
    fontWeight: '600',
    color: Colors.secondary,
  },
  subTextRight: {
    fontSize: 10,
    color: Colors.textSubtle,
  },
  tilesGrid: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 12,
  },
  tile: {
    flex: 1,
    backgroundColor: Colors.neutralCard,
    borderRadius: 12,
    padding: 12,
    justifyContent: 'space-between',
    minHeight: 100,
  },
  tileHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  tileLabel: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.textMuted,
    letterSpacing: 0.5,
  },
  tileIconCircle: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: Colors.surfaceContainer,
    alignItems: 'center',
    justifyContent: 'center',
  },
  tileMetricRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginVertical: 4,
  },
  tileMetricSubtle: {
    fontSize: 28,
    fontWeight: '700',
    color: Colors.textSubtle,
  },
  unitText: {
    fontSize: 12,
    color: Colors.textSubtle,
    marginLeft: 2,
  },
  tileSub: {
    fontSize: 10,
    color: Colors.outline,
  },
  chartCard: {
    backgroundColor: Colors.neutralCard,
    borderRadius: 12,
    padding: 12,
    marginBottom: 20,
  },
  chartBarsRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    justifyContent: 'space-around',
    height: 80,
    marginTop: 12,
  },
  chartBarCol: {
    alignItems: 'center',
    gap: 4,
  },
  barValue: {
    fontSize: 10,
    color: Colors.textMuted,
  },
  barVisual: {
    width: 28,
    borderRadius: 6,
  },
  barLabel: {
    fontSize: 10,
    color: Colors.textSubtle,
  },
  chartFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 12,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: Colors.neutralBorder,
  },
  greenDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: Colors.secondary,
  },
  chartFooterText: {
    fontSize: 10,
    color: Colors.textSubtle,
  },
  fullChartLink: {
    fontSize: 10,
    fontWeight: '600',
    color: Colors.primary,
  },
  sessionsList: {
    gap: 8,
    marginBottom: 20,
  },
  sessionCard: {
    backgroundColor: Colors.neutralCard,
    borderRadius: 12,
    padding: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  sessionLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  sessionIcon: {
    width: 32,
    height: 32,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sessionTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.textStrong,
  },
  sessionMeta: {
    fontSize: 10,
    color: Colors.textSubtle,
    marginTop: 2,
  },
  workedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.surfaceTintMint,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 10,
    gap: 4,
  },
  workedBadgeText: {
    fontSize: 10,
    fontWeight: '600',
    color: Colors.secondary,
  },
  partialBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.surfaceTintAmber,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 10,
    gap: 4,
  },
  partialBadgeText: {
    fontSize: 10,
    fontWeight: '600',
    color: Colors.tertiary,
  },
  aiInsightBox: {
    backgroundColor: Colors.surfaceTintViolet,
    borderRadius: 12,
    padding: 12,
    flexDirection: 'row',
    gap: 10,
    marginBottom: 20,
  },
  aiAvatarCircle: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: Colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  aiInsightHeader: {
    fontSize: 11,
    fontWeight: '700',
    color: Colors.primary,
  },
  aiInsightText: {
    fontSize: 12,
    color: Colors.onSurface,
    marginTop: 2,
    lineHeight: 16,
  },
  boldPrimary: {
    fontWeight: '700',
    color: Colors.primary,
  },
  actionsGroup: {
    gap: 10,
  },
  btnPrimary: {
    height: 48,
    borderRadius: 24,
    backgroundColor: Colors.primaryContainer,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    shadowColor: Colors.primaryContainer,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 3,
  },
  btnPrimaryText: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.onPrimary,
  },
  secondaryActionsRow: {
    flexDirection: 'row',
    gap: 10,
  },
  btnSecondary: {
    flex: 1,
    height: 44,
    borderRadius: 22,
    backgroundColor: Colors.surfaceContainerHigh,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  btnSecondaryText: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.onSurfaceVariant,
  },
  btnAdopt: {
    flex: 1,
    height: 44,
    borderRadius: 22,
    backgroundColor: Colors.surfaceTintMint,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  btnAdoptText: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.secondary,
  },
});
