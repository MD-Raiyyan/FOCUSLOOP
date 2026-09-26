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

export default function InsightsScreen() {
  const [activeSegment, setActiveSegment] = useState<'Overview' | 'Impact' | 'Peer'>('Overview');
  const [selectedTimeRange, setSelectedTimeRange] = useState('Week');

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
              Overview & Trends
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.segmentBtn, activeSegment === 'Impact' && styles.segmentBtnActive]}
            onPress={() => setActiveSegment('Impact')}
          >
            <Text style={[styles.segmentText, activeSegment === 'Impact' && styles.segmentTextActive]}>
              Experiment Impact
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

        {/* OVERVIEW & TRENDS VIEW */}
        {activeSegment === 'Overview' && (
          <View style={styles.tabContent}>
            {/* Top Productivity Score Hero Card */}
            <View style={styles.scoreHeroCard}>
              <View style={styles.scoreHeaderRow}>
                <View>
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
                    <Ionicons name="analytics-outline" size={14} color={Colors.primaryFixedDim} />
                    <Text style={styles.scoreLabel}>PRODUCTIVITY & FOCUS SCORE</Text>
                  </View>
                  <View style={styles.scoreMetricRow}>
                    <Text style={styles.scoreNumber}>88%</Text>
                    <View style={styles.trendPill}>
                      <Ionicons name="trending-up" size={12} color={Colors.secondaryFixed} />
                      <Text style={styles.trendPillText}>+14%</Text>
                    </View>
                  </View>
                  <Text style={styles.scoreSubTitle}>Excellent consistency</Text>
                </View>
                <View style={styles.vsBadge}>
                  <Text style={styles.vsBadgeText}>vs last week</Text>
                </View>
              </View>

              {/* Sparkline Visual Placeholder */}
              <View style={styles.sparklineBar}>
                <Text style={styles.sparklineText}>📈 Steady Flow State Trajectory</Text>
              </View>
            </View>

            {/* Time Range Selector */}
            <View style={styles.timeRangeRail}>
              {['Day', 'Week', 'Month', 'Year'].map((range) => (
                <TouchableOpacity
                  key={range}
                  style={[
                    styles.timeRangeBtn,
                    selectedTimeRange === range && styles.timeRangeBtnActive,
                  ]}
                  onPress={() => setSelectedTimeRange(range)}
                >
                  <Text
                    style={[
                      styles.timeRangeText,
                      selectedTimeRange === range && styles.timeRangeTextActive,
                    ]}
                  >
                    {range}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            {/* Time Distribution Donut Card */}
            <View style={styles.card}>
              <View style={styles.cardHeaderRow}>
                <View style={styles.cardIconBox}>
                  <Ionicons name="pie-chart-outline" size={16} color={Colors.primary} />
                </View>
                <Text style={styles.cardTitle}>Time Distribution</Text>
              </View>

              <View style={styles.donutContentRow}>
                {/* Donut representation */}
                <View style={styles.donutCircle}>
                  <Text style={styles.donutVal}>18.5</Text>
                  <Text style={styles.donutSub}>Total hrs</Text>
                </View>

                {/* Legend list */}
                <View style={styles.legendList}>
                  <View style={styles.legendRow}>
                    <View style={[styles.legendDot, { backgroundColor: Colors.accentIndigo }]} />
                    <Text style={styles.legendLabel}>Deep Work</Text>
                    <Text style={styles.legendVal}>8.5h (46%)</Text>
                  </View>
                  <View style={styles.legendRow}>
                    <View style={[styles.legendDot, { backgroundColor: Colors.secondary }]} />
                    <Text style={styles.legendLabel}>Tasks Done</Text>
                    <Text style={styles.legendVal}>4.5h (24%)</Text>
                  </View>
                  <View style={styles.legendRow}>
                    <View style={[styles.legendDot, { backgroundColor: Colors.primaryFixedDim }]} />
                    <Text style={styles.legendLabel}>Micro-Start</Text>
                    <Text style={styles.legendVal}>3.0h (16%)</Text>
                  </View>
                  <View style={styles.legendRow}>
                    <View style={[styles.legendDot, { backgroundColor: Colors.accentCoral }]} />
                    <Text style={styles.legendLabel}>Delay Log</Text>
                    <Text style={styles.legendVal}>2.5h (14%)</Text>
                  </View>
                </View>
              </View>
            </View>

            {/* Daily Focus Rhythm 7-Day Bar Chart */}
            <View style={styles.card}>
              <View style={styles.cardHeaderRow}>
                <View style={[styles.cardIconBox, { backgroundColor: Colors.surfaceTintMint }]}>
                  <Ionicons name="bar-chart-outline" size={16} color={Colors.secondary} />
                </View>
                <Text style={styles.cardTitle}>Daily Focus Rhythm</Text>
              </View>

              <View style={styles.barChartContainer}>
                <View style={styles.chartBarsRow}>
                  {[
                    { day: 'Mon', p: 60, a: 52 },
                    { day: 'Tue', p: 68, a: 65 },
                    { day: 'Wed', p: 80, a: 95, active: true },
                    { day: 'Thu', p: 75, a: 70 },
                    { day: 'Fri', p: 70, a: 58 },
                    { day: 'Sat', p: 40, a: 35 },
                    { day: 'Sun', p: 45, a: 48 },
                  ].map((item, i) => (
                    <View key={i} style={styles.barCol}>
                      <View style={styles.barPair}>
                        <View style={[styles.barPlanned, { height: item.p * 0.7 }]} />
                        <View
                          style={[
                            styles.barActual,
                            { height: item.a * 0.7 },
                            item.active && { backgroundColor: Colors.primary },
                          ]}
                        />
                      </View>
                      <Text style={[styles.barDayText, item.active && { color: Colors.primary, fontWeight: '700' }]}>
                        {item.day}
                      </Text>
                    </View>
                  ))}
                </View>

                <Text style={styles.chartAvgText}>
                  Average actual focus: <Text style={{ fontWeight: '700', color: Colors.textStrong }}>2.64 hrs / day</Text>
                </Text>
              </View>
            </View>

            {/* Key Behavioral Patterns Cards */}
            <View style={{ gap: 10 }}>
              <Text style={styles.sectionHeaderTitle}>Key Behavioral Patterns</Text>

              {/* Pattern 1 */}
              <View style={styles.patternCard}>
                <View style={[styles.patternIconBox, { backgroundColor: Colors.surfaceTintMint }]}>
                  <Ionicons name="sunny-outline" size={18} color={Colors.secondary} />
                </View>
                <View style={{ flex: 1 }}>
                  <View style={styles.patternTopRow}>
                    <Text style={styles.patternTitle}>Best Focus Window</Text>
                    <View style={styles.patternTagMint}>
                      <Text style={styles.patternTagMintText}>92% Completion</Text>
                    </View>
                  </View>
                  <Text style={styles.patternDesc}>
                    <Text style={{ fontWeight: '700' }}>9:00 AM – 11:30 AM</Text> shows your highest flow state and fastest completion pace.
                  </Text>
                </View>
              </View>

              {/* Pattern 2 */}
              <View style={styles.patternCard}>
                <View style={[styles.patternIconBox, { backgroundColor: Colors.surfaceTintAmber }]}>
                  <Ionicons name="warning-outline" size={18} color={Colors.tertiary} />
                </View>
                <View style={{ flex: 1 }}>
                  <View style={styles.patternTopRow}>
                    <Text style={styles.patternTitle}>Main Friction Trigger</Text>
                    <View style={styles.patternTagAmber}>
                      <Text style={styles.patternTagAmberText}>Energy Dip</Text>
                    </View>
                  </View>
                  <Text style={styles.patternDesc}>
                    Hesitation peaks <Text style={{ fontWeight: '700' }}>post-lunch (2:00 PM)</Text> whenever previous night sleep was under 6h.
                  </Text>
                </View>
              </View>

              {/* Pattern 3 */}
              <View style={styles.patternCard}>
                <View style={[styles.patternIconBox, { backgroundColor: Colors.surfaceTintViolet }]}>
                  <Ionicons name="checkmark-done-circle-outline" size={18} color={Colors.primary} />
                </View>
                <View style={{ flex: 1 }}>
                  <View style={styles.patternTopRow}>
                    <Text style={styles.patternTitle}>Top Intervention</Text>
                    <View style={styles.patternTagMint}>
                      <Text style={styles.patternTagMintText}>-57% Friction</Text>
                    </View>
                  </View>
                  <Text style={styles.patternDesc}>
                    Activating the <Text style={{ fontWeight: '700' }}>10-Min Micro-Start Buffer</Text> unblocked 11 out of 13 delayed tasks this week.
                  </Text>
                </View>
              </View>
            </View>
          </View>
        )}

        {/* EXPERIMENT IMPACT VIEW */}
        {(activeSegment === 'Impact' || activeSegment === 'Overview') && activeSegment !== 'Overview' && (
          <View style={styles.tabContent}>
            {/* Center Hero Badge: Grade & Score */}
            <View style={styles.impactHeroCard}>
              <View style={styles.impactTopRow}>
                <View style={styles.gradeBox}>
                  <Text style={styles.gradeLetter}>A</Text>
                  <Text style={styles.gradeSub}>Top Tier</Text>
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.impactSubHeader}>Hesitation Defeated</Text>
                  <View style={{ flexDirection: 'row', alignItems: 'baseline', gap: 2 }}>
                    <Text style={styles.impactScoreBig}>94</Text>
                    <Text style={{ fontSize: 13, color: Colors.textSubtle }}>/ 100</Text>
                  </View>
                  <Text style={{ fontSize: 11, color: Colors.secondary, fontWeight: '600' }}>
                    ↑ +18 pts vs 30-day baseline
                  </Text>
                </View>
              </View>

              {/* 3 Micro-Metrics Row */}
              <View style={styles.metricsRow}>
                <View style={styles.metricTile}>
                  <Text style={styles.metricVal}>-58%</Text>
                  <Text style={styles.metricLabel}>Latency (was 38m)</Text>
                </View>
                <View style={styles.metricTile}>
                  <Text style={[styles.metricVal, { color: Colors.primary }]}>4/4</Text>
                  <Text style={styles.metricLabel}>Habits Adopted</Text>
                </View>
                <View style={styles.metricTile}>
                  <Text style={[styles.metricVal, { color: Colors.tertiary }]}>14.2h</Text>
                  <Text style={styles.metricLabel}>Friction Reclaimed</Text>
                </View>
              </View>
            </View>

            {/* Verified Experiments Protocols Deck */}
            <View style={{ gap: 10 }}>
              <Text style={styles.sectionHeaderTitle}>Verified Experiments</Text>

              {/* Protocol 1: Micro-Start */}
              <View style={styles.card}>
                <View style={styles.cardHeaderRow}>
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                    <View style={[styles.cardIconBox, { backgroundColor: Colors.surfaceTintViolet }]}>
                      <Ionicons name="timer-outline" size={18} color={Colors.primary} />
                    </View>
                    <View>
                      <Text style={styles.cardTitle}>10-Min Micro-Start Buffer</Text>
                      <Text style={{ fontSize: 10, color: Colors.textSubtle }}>Protocol #04 • Cognitive Momentum</Text>
                    </View>
                  </View>
                  <View style={styles.gradeBadge}>
                    <Text style={styles.gradeBadgeText}>Grade A+</Text>
                  </View>
                </View>

                <View style={styles.comparisonBox}>
                  <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 6 }}>
                    <Text style={{ fontSize: 10, color: Colors.textSubtle }}>Start Hesitation Reduction</Text>
                    <Text style={{ fontSize: 10, fontWeight: '700', color: Colors.secondary }}>+92% Efficacy</Text>
                  </View>
                  <View style={{ gap: 6 }}>
                    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                      <Text style={{ fontSize: 10, color: Colors.textSubtle, width: 50 }}>Baseline</Text>
                      <View style={{ flex: 1, height: 8, backgroundColor: Colors.surfaceContainer, borderRadius: 4, overflow: 'hidden' }}>
                        <View style={{ width: '85%', height: '100%', backgroundColor: Colors.outlineVariant, borderRadius: 4 }} />
                      </View>
                      <Text style={{ fontSize: 10, color: Colors.textSubtle, width: 30, textAlign: 'right' }}>38m</Text>
                    </View>
                    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                      <Text style={{ fontSize: 10, color: Colors.primary, fontWeight: '700', width: 50 }}>Buffered</Text>
                      <View style={{ flex: 1, height: 8, backgroundColor: Colors.surfaceContainer, borderRadius: 4, overflow: 'hidden' }}>
                        <View style={{ width: '28%', height: '100%', backgroundColor: Colors.primary, borderRadius: 4 }} />
                      </View>
                      <Text style={{ fontSize: 10, color: Colors.primary, fontWeight: '700', width: 30, textAlign: 'right' }}>12m</Text>
                    </View>
                  </View>
                </View>
              </View>

              {/* Protocol 2: Box Breathing */}
              <View style={styles.card}>
                <View style={styles.cardHeaderRow}>
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                    <View style={[styles.cardIconBox, { backgroundColor: Colors.surfaceTintRose }]}>
                      <Ionicons name="body-outline" size={18} color={Colors.accentCoral} />
                    </View>
                    <View>
                      <Text style={styles.cardTitle}>5-Min Box Breathing</Text>
                      <Text style={{ fontSize: 10, color: Colors.textSubtle }}>Protocol #02 • Somatic Down-Regulation</Text>
                    </View>
                  </View>
                  <View style={[styles.gradeBadge, { backgroundColor: Colors.surfaceTintAmber }]}>
                    <Text style={[styles.gradeBadgeText, { color: Colors.tertiary }]}>Grade B+</Text>
                  </View>
                </View>
                <Text style={{ fontSize: 11, color: Colors.textSubtle, marginTop: 4 }}>
                  Task initiation stress down by 41%. Average delay shrank from 29m baseline to 19m.
                </Text>
              </View>
            </View>

            {/* Behavioral Mastery Tier Stepper */}
            <View style={styles.card}>
              <Text style={{ fontSize: 10, fontWeight: '700', color: Colors.primary, letterSpacing: 0.5 }}>EVOLUTION PATH</Text>
              <Text style={styles.cardTitle}>Behavioral Mastery Tier</Text>
              <View style={{ marginTop: 8 }}>
                <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 4 }}>
                  <Text style={{ fontSize: 10, color: Colors.textSubtle }}>Apprentice</Text>
                  <Text style={{ fontSize: 10, color: Colors.textSubtle }}>Loop Builder</Text>
                  <Text style={{ fontSize: 10, color: Colors.primary, fontWeight: '600' }}>Specialist</Text>
                  <Text style={{ fontSize: 10, color: Colors.primary, fontWeight: '700' }}>Master II</Text>
                </View>
                <View style={{ height: 8, backgroundColor: Colors.surfaceContainerHigh, borderRadius: 4, overflow: 'hidden' }}>
                  <View style={{ width: '78%', height: '100%', backgroundColor: Colors.primary, borderRadius: 4 }} />
                </View>
              </View>
            </View>
          </View>
        )}

        {/* PEER CIRCLES VIEW */}
        {activeSegment === 'Peer' && (
          <View style={styles.tabContent}>
            <View style={styles.card}>
              <View style={styles.cardHeaderRow}>
                <Text style={styles.cardTitle}>Focus Circle Grades</Text>
                <View style={styles.patternTagMint}>
                  <Text style={styles.patternTagMintText}>Active Circle</Text>
                </View>
              </View>
              <Text style={{ fontSize: 11, color: Colors.textSubtle, marginTop: 2 }}>
                Zero toxic comparison. Grounded purely in friction reduction & protocol consistency.
              </Text>

              {/* Leaderboard List */}
              <View style={{ gap: 8, marginTop: 12 }}>
                {/* Rank 1 */}
                <View style={styles.peerCardHighlight}>
                  <View style={styles.peerLeft}>
                    <View style={styles.rankBadgeActive}>
                      <Text style={{ fontSize: 10, fontWeight: '700', color: Colors.onPrimary }}>1</Text>
                    </View>
                    <View>
                      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
                        <Text style={styles.peerName}>Alex Chen (You)</Text>
                        <View style={styles.gradeTagPrimary}><Text style={styles.gradeTagText}>A+</Text></View>
                      </View>
                      <Text style={styles.peerSub}>Micro-Start Buffer • 🔥 12-day streak</Text>
                    </View>
                  </View>
                  <View style={{ alignItems: 'flex-end' }}>
                    <Text style={styles.peerPts}>94 pts</Text>
                    <Text style={{ fontSize: 10, color: Colors.secondary, fontWeight: '600' }}>-58% delay</Text>
                  </View>
                </View>

                {/* Rank 2 */}
                <View style={styles.peerCard}>
                  <View style={styles.peerLeft}>
                    <View style={styles.rankBadge}><Text style={{ fontSize: 10, fontWeight: '700', color: Colors.textStrong }}>2</Text></View>
                    <View>
                      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
                        <Text style={styles.peerName}>Maya Patel</Text>
                        <View style={styles.gradeTagViolet}><Text style={{ fontSize: 9, fontWeight: '700', color: Colors.primary }}>A</Text></View>
                      </View>
                      <Text style={styles.peerSub}>Pomodoro Split • 🔥 9-day streak</Text>
                    </View>
                  </View>
                  <View style={{ alignItems: 'flex-end' }}>
                    <Text style={styles.peerPts}>91 pts</Text>
                    <Text style={{ fontSize: 10, color: Colors.secondary, fontWeight: '600' }}>-49% delay</Text>
                  </View>
                </View>

                {/* Rank 3 */}
                <View style={styles.peerCard}>
                  <View style={styles.peerLeft}>
                    <View style={styles.rankBadge}><Text style={{ fontSize: 10, fontWeight: '700', color: Colors.textStrong }}>3</Text></View>
                    <View>
                      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
                        <Text style={styles.peerName}>Liam Davies</Text>
                        <View style={styles.gradeTagViolet}><Text style={{ fontSize: 9, fontWeight: '700', color: Colors.primary }}>A-</Text></View>
                      </View>
                      <Text style={styles.peerSub}>Morning Walk Primer • 🔥 7-day streak</Text>
                    </View>
                  </View>
                  <View style={{ alignItems: 'flex-end' }}>
                    <Text style={styles.peerPts}>88 pts</Text>
                    <Text style={{ fontSize: 10, color: Colors.secondary, fontWeight: '600' }}>-42% delay</Text>
                  </View>
                </View>

                {/* Rank 4 */}
                <View style={styles.peerCard}>
                  <View style={styles.peerLeft}>
                    <View style={styles.rankBadge}><Text style={{ fontSize: 10, fontWeight: '700', color: Colors.textStrong }}>4</Text></View>
                    <View>
                      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
                        <Text style={styles.peerName}>Sarah Lin</Text>
                        <View style={styles.patternTagAmber}><Text style={styles.patternTagAmberText}>B+</Text></View>
                      </View>
                      <Text style={styles.peerSub}>Digital Sunset • 4-day streak</Text>
                    </View>
                  </View>
                  <View style={{ alignItems: 'flex-end' }}>
                    <Text style={styles.peerPts}>84 pts</Text>
                    <Text style={{ fontSize: 10, color: Colors.secondary, fontWeight: '600' }}>-35% delay</Text>
                  </View>
                </View>
              </View>

              {/* Collaborative Action Row */}
              <View style={{ flexDirection: 'row', gap: 10, marginTop: 14 }}>
                <TouchableOpacity style={styles.btnNudge}>
                  <Ionicons name="sparkles-outline" size={14} color={Colors.primary} />
                  <Text style={{ fontSize: 12, fontWeight: '600', color: Colors.primary }}>Nudge Circle</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.btnShare}>
                  <Ionicons name="share-outline" size={14} color={Colors.onPrimary} />
                  <Text style={{ fontSize: 12, fontWeight: '600', color: Colors.onPrimary }}>Share Protocol</Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>
        )}
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
  sparklineBar: {
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.15)',
  },
  sparklineText: {
    fontSize: 11,
    color: Colors.primaryFixedDim,
  },
  timeRangeRail: {
    flexDirection: 'row',
    backgroundColor: Colors.surfaceContainerHigh,
    padding: 3,
    borderRadius: 20,
    justifyContent: 'space-between',
  },
  timeRangeBtn: {
    flex: 1,
    paddingVertical: 6,
    borderRadius: 16,
    alignItems: 'center',
  },
  timeRangeBtnActive: {
    backgroundColor: Colors.primary,
  },
  timeRangeText: {
    fontSize: 11,
    color: Colors.textSubtle,
  },
  timeRangeTextActive: {
    fontWeight: '600',
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
  donutContentRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    gap: 12,
  },
  donutCircle: {
    width: 100,
    height: 100,
    borderRadius: 50,
    borderWidth: 12,
    borderColor: Colors.accentIndigo,
    alignItems: 'center',
    justifyContent: 'center',
  },
  donutVal: {
    fontSize: 20,
    fontWeight: '700',
    color: Colors.textStrong,
  },
  donutSub: {
    fontSize: 10,
    color: Colors.textSubtle,
  },
  legendList: {
    gap: 6,
    flex: 1,
  },
  legendRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  legendDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  legendLabel: {
    fontSize: 11,
    color: Colors.textStrong,
    marginLeft: 6,
    flex: 1,
  },
  legendVal: {
    fontSize: 10,
    color: Colors.textSubtle,
  },
  barChartContainer: {
    marginTop: 4,
  },
  chartBarsRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    justifyContent: 'space-between',
    height: 110,
    paddingHorizontal: 4,
  },
  barCol: {
    alignItems: 'center',
    gap: 6,
  },
  barPair: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 3,
  },
  barPlanned: {
    width: 8,
    borderRadius: 4,
    backgroundColor: Colors.surfaceVariant,
  },
  barActual: {
    width: 8,
    borderRadius: 4,
    backgroundColor: Colors.primaryContainer,
  },
  barDayText: {
    fontSize: 10,
    color: Colors.textSubtle,
  },
  chartAvgText: {
    fontSize: 11,
    color: Colors.textSubtle,
    textAlign: 'center',
    marginTop: 12,
  },
  sectionHeaderTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: Colors.textStrong,
  },
  patternCard: {
    backgroundColor: Colors.neutralCard,
    borderRadius: 16,
    padding: 14,
    flexDirection: 'row',
    gap: 12,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.03,
    shadowRadius: 6,
    elevation: 1,
  },
  patternIconBox: {
    width: 36,
    height: 36,
    borderRadius: 10,
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
  patternTagAmber: {
    backgroundColor: Colors.surfaceTintAmber,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  patternTagAmberText: {
    fontSize: 9,
    fontWeight: '700',
    color: Colors.tertiary,
  },
  patternDesc: {
    fontSize: 11,
    color: Colors.textSubtle,
    marginTop: 4,
    lineHeight: 16,
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
  gradeLetter: {
    fontSize: 28,
    fontWeight: '700',
    color: Colors.primary,
  },
  gradeSub: {
    fontSize: 9,
    fontWeight: '700',
    color: Colors.secondary,
    marginTop: -2,
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
  gradeBadge: {
    backgroundColor: Colors.surfaceTintMint,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 10,
  },
  gradeBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.secondary,
  },
  comparisonBox: {
    backgroundColor: Colors.surfaceContainerLow,
    borderRadius: 10,
    padding: 10,
    marginTop: 8,
  },
  peerCard: {
    backgroundColor: Colors.surfaceContainerLow,
    borderRadius: 12,
    padding: 10,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  peerCardHighlight: {
    backgroundColor: Colors.surfaceTintViolet,
    borderRadius: 12,
    padding: 10,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderWidth: 1,
    borderColor: 'rgba(99, 91, 255, 0.2)',
  },
  peerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  rankBadge: {
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: Colors.surfaceContainerHighest,
    alignItems: 'center',
    justifyContent: 'center',
  },
  rankBadgeActive: {
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: Colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  peerName: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.textStrong,
  },
  peerSub: {
    fontSize: 10,
    color: Colors.textSubtle,
    marginTop: 2,
  },
  peerPts: {
    fontSize: 13,
    fontWeight: '700',
    color: Colors.textStrong,
  },
  gradeTagPrimary: {
    backgroundColor: Colors.primary,
    paddingHorizontal: 6,
    paddingVertical: 1,
    borderRadius: 6,
  },
  gradeTagViolet: {
    backgroundColor: Colors.surfaceTintViolet,
    paddingHorizontal: 6,
    paddingVertical: 1,
    borderRadius: 6,
  },
  gradeTagText: {
    fontSize: 9,
    fontWeight: '700',
    color: Colors.onPrimary,
  },
  btnNudge: {
    flex: 1,
    backgroundColor: Colors.surfaceTintViolet,
    paddingVertical: 10,
    borderRadius: 20,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  btnShare: {
    flex: 1,
    backgroundColor: Colors.primary,
    paddingVertical: 10,
    borderRadius: 20,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
});
