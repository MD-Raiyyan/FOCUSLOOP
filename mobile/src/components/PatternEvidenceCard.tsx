import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors, Palette, Spacing } from '@/constants/theme';
import { PatternResponse, ContextComparisonPoint, TimeSeriesPoint } from '@/types/behavior';

interface PatternEvidenceCardProps {
  pattern: PatternResponse;
}

export function PatternEvidenceCard({ pattern }: PatternEvidenceCardProps) {
  const sup = pattern.supporting_metrics || {};
  const status = (pattern.status || 'active').toLowerCase();
  const confidence = (pattern.confidence || 'moderate').toLowerCase();
  const isInsufficient = Boolean(sup.insufficient_evidence);
  const contextPoints: ContextComparisonPoint[] = sup.context_comparison || [];
  const timeSeries: TimeSeriesPoint[] = sup.time_series || [];
  const historical = sup.historical_window;
  const recent = sup.recent_window;

  // Status badge styling
  const isPositive = pattern.pattern_type === 'morning_momentum';
  let statusBg: string = isPositive ? Colors.surfaceTintMint : Colors.surfaceTintAmber;
  let statusText: string = isPositive ? '#047857' : '#b45309'; // Amber-700
  let statusIcon: keyof typeof Ionicons.glyphMap = isPositive ? 'sunny-outline' : 'alert-circle-outline';
  let statusLabel = isPositive ? 'Active Momentum' : 'Active Friction';

  const isInactive = status === 'inactive' || Boolean(sup.insufficient_current_evidence);

  if (status === 'improving') {
    statusBg = Colors.surfaceTintMint;
    statusText = '#047857'; // Emerald-700
    statusIcon = 'trending-up-outline';
    statusLabel = 'Improving';
  } else if (status === 'weakening') {
    statusBg = Colors.surfaceTintAmber;
    statusText = '#b45309'; // Amber-700
    statusIcon = 'trending-down-outline';
    statusLabel = isPositive ? 'Weakening Momentum' : 'Weakening';
  } else if (isInactive) {
    statusBg = Colors.surfaceContainer;
    statusText = Colors.textMuted;
    statusIcon = 'help-circle-outline';
    statusLabel = 'Insufficient Recent Evidence';
  } else if (status === 'resolved') {
    statusBg = isPositive ? Colors.surfaceContainer : Colors.surfaceTintBlue;
    statusText = isPositive ? Colors.textMuted : '#1d4ed8'; // Blue-700
    statusIcon = 'checkmark-circle-outline';
    statusLabel = 'Resolved';
  } else if (status === 'archived') {
    statusBg = Colors.surfaceContainer;
    statusText = Colors.textMuted;
    statusIcon = 'archive-outline';
    statusLabel = 'Archived';
  }

  // Choose primary icon based on pattern_type
  let patternIcon: keyof typeof Ionicons.glyphMap = 'bulb-outline';
  if (pattern.pattern_type === 'afternoon_slump') {
    patternIcon = 'partly-sunny-outline';
  } else if (pattern.pattern_type === 'start_delay_resistance') {
    patternIcon = 'hourglass-outline';
  } else if (pattern.pattern_type === 'morning_momentum') {
    patternIcon = 'sunny-outline';
  } else if (pattern.pattern_type === 'primary_distraction') {
    patternIcon = 'phone-portrait-outline';
  }

  return (
    <View style={styles.card}>
      {/* Top Header Row */}
      <View style={styles.headerRow}>
        <View style={styles.iconBox}>
          <Ionicons name={patternIcon} size={20} color={Colors.primary} />
        </View>
        <View style={{ flex: 1 }}>
          <View style={styles.titleRow}>
            <Text style={styles.title} numberOfLines={2}>
              {pattern.title}
            </Text>
          </View>
          <View style={styles.badgesRow}>
            {/* Status Badge */}
            <View style={[styles.statusBadge, { backgroundColor: statusBg }]}>
              <Ionicons name={statusIcon} size={12} color={statusText} style={{ marginRight: 4 }} />
              <Text style={[styles.statusBadgeText, { color: statusText }]}>
                {statusLabel}
              </Text>
            </View>

            {/* Confidence Badge */}
            <View style={styles.confidenceBadge}>
              <Text style={styles.confidenceBadgeText}>
                {confidence.toUpperCase()} CONFIDENCE
              </Text>
            </View>

            {/* Sample Size Badge */}
            <View style={styles.sampleBadge}>
              <Text style={styles.sampleBadgeText}>
                n = {pattern.sample_size}
              </Text>
            </View>
          </View>
        </View>
      </View>

      {/* Description / Explanation */}
      <Text style={styles.description}>{pattern.description}</Text>

      {/* Insufficient Evidence Notice */}
      {isInactive && (
        <View style={styles.inactiveNoticeCard}>
          <Ionicons name="information-circle-outline" size={16} color={Colors.textMuted} style={{ marginRight: 6 }} />
          <Text style={styles.inactiveNoticeText}>
            We need more recent observations to know whether this pattern is still present.
          </Text>
        </View>
      )}

      {/* Historical vs Recent Window Comparison Callout if available */}
      {historical && recent && historical.value !== null && recent.value !== null && (
        <View style={styles.windowComparisonCard}>
          <View style={styles.windowCol}>
            <Text style={styles.windowLabel}>{historical.label}</Text>
            <Text style={styles.windowValue}>
              {historical.value} {historical.unit}
            </Text>
            <Text style={styles.windowSample}>n = {historical.sample_size} sessions</Text>
          </View>
          <View style={styles.windowArrow}>
            <Ionicons
              name={recent.value < historical.value ? 'arrow-down' : 'arrow-forward'}
              size={18}
              color={recent.value < historical.value ? '#047857' : Colors.textMuted}
            />
          </View>
          <View style={[styles.windowCol, { backgroundColor: Colors.surfaceTintMint }]}>
            <Text style={[styles.windowLabel, { color: '#047857' }]}>{recent.label}</Text>
            <Text style={[styles.windowValue, { color: '#047857' }]}>
              {recent.value} {recent.unit}
            </Text>
            <Text style={styles.windowSample}>n = {recent.sample_size} sessions</Text>
          </View>
        </View>
      )}

      {/* VISUAL EVIDENCE GRAPH SECTION */}
      {isInsufficient ? (
        <View style={styles.insufficientBox}>
          <Ionicons name="information-circle-outline" size={18} color={Colors.textMuted} />
          <Text style={styles.insufficientText}>
            Not enough evidence yet — tracking more sessions to establish pattern stability.
          </Text>
        </View>
      ) : (
        <View style={styles.graphContainer}>
          {/* 1. Context Comparison Graph (Morning vs Afternoon vs Evening) */}
          {contextPoints.length > 0 && (
            <View style={styles.contextGraphBox}>
              <Text style={styles.graphHeader}>Context Comparison</Text>
              {contextPoints.map((pt) => {
                const maxVal = Math.max(...contextPoints.map((p) => p.value), 1);
                const barWidthPercent = Math.min(100, Math.max(8, (pt.value / maxVal) * 100));
                const isAfternoon = pt.context === 'Afternoon';
                const isMorning = pt.context === 'Morning';

                let barColor: string = Colors.primary;
                if (pattern.pattern_type === 'afternoon_slump' && isAfternoon) {
                  barColor = Palette.accentCoral;
                } else if (isMorning && pattern.pattern_type === 'morning_momentum') {
                  barColor = '#059669';
                }

                return (
                  <View key={pt.context} style={styles.barRow}>
                    <Text style={styles.barLabel}>{pt.context}</Text>
                    <View style={styles.barTrack}>
                      <View
                        style={[
                          styles.barFill,
                          {
                            width: `${barWidthPercent}%`,
                            backgroundColor: barColor,
                          },
                        ]}
                      />
                    </View>
                    <Text style={styles.barValueText}>
                      {pt.value} {pt.unit}
                      <Text style={styles.barSampleText}> (n={pt.sample_size})</Text>
                    </Text>
                  </View>
                );
              })}
            </View>
          )}

          {/* 2. Real Time-Series Trend Graph */}
          {timeSeries.length > 1 && (
            <View style={styles.timeSeriesBox}>
              <View style={styles.timeSeriesHeaderRow}>
                <Text style={styles.graphHeader}>Daily Observation Trend</Text>
                <Text style={styles.realPointsBadge}>Real Evidence Points</Text>
              </View>
              <View style={styles.timelineRow}>
                {timeSeries.slice(-7).map((pt) => {
                  const maxVal = Math.max(...timeSeries.slice(-7).map((p) => p.value), 1);
                  const barHeight = Math.min(60, Math.max(12, (pt.value / maxVal) * 60));
                  const shortDate = pt.date.slice(5); // MM-DD

                  return (
                    <View key={pt.date} style={styles.timelineBarItem}>
                      <Text style={styles.timelineValText}>{pt.value}</Text>
                      <View style={styles.timelineBarTrack}>
                        <View
                          style={[
                            styles.timelineBarFill,
                            {
                              height: barHeight,
                              backgroundColor: Colors.primary,
                            },
                          ]}
                        />
                      </View>
                      <Text style={styles.timelineDateText}>{shortDate}</Text>
                    </View>
                  );
                })}
              </View>
            </View>
          )}
        </View>
      )}

      {/* Footer Trust Indicator */}
      <View style={styles.footerRow}>
        <Ionicons name="shield-checkmark-outline" size={12} color={Colors.textMuted} />
        <Text style={styles.footerText}>
          Backed by PostgreSQL check-in telemetry • No synthetic points
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.surfaceContainerLowest,
    borderRadius: 16,
    padding: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.surfaceContainer,
    gap: 12,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  iconBox: {
    width: 38,
    height: 38,
    borderRadius: 12,
    backgroundColor: Colors.surfaceContainer,
    alignItems: 'center',
    justifyContent: 'center',
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  title: {
    fontSize: 16,
    fontWeight: '700',
    color: Colors.textStrong,
    flex: 1,
  },
  badgesRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'center',
    gap: 6,
    marginTop: 2,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
  },
  statusBadgeText: {
    fontSize: 11,
    fontWeight: '700',
  },
  confidenceBadge: {
    paddingHorizontal: 7,
    paddingVertical: 3,
    borderRadius: 8,
    backgroundColor: Colors.surfaceContainer,
  },
  confidenceBadgeText: {
    fontSize: 10,
    fontWeight: '600',
    color: Colors.textSubtle,
    letterSpacing: 0.3,
  },
  sampleBadge: {
    paddingHorizontal: 7,
    paddingVertical: 3,
    borderRadius: 8,
    backgroundColor: Colors.surfaceContainer,
  },
  sampleBadgeText: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.textSubtle,
  },
  description: {
    fontSize: 13,
    lineHeight: 19,
    color: Colors.textSubtle,
  },
  windowComparisonCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.surfaceContainerLow,
    borderRadius: 12,
    padding: 8,
    gap: 8,
  },
  windowCol: {
    flex: 1,
    padding: 8,
    borderRadius: 8,
    backgroundColor: Colors.surfaceContainerLowest,
  },
  windowArrow: {
    paddingHorizontal: 4,
  },
  windowLabel: {
    fontSize: 10,
    fontWeight: '600',
    color: Colors.textMuted,
    textTransform: 'uppercase',
    marginBottom: 2,
  },
  windowValue: {
    fontSize: 15,
    fontWeight: '700',
    color: Colors.textStrong,
  },
  windowSample: {
    fontSize: 10,
    color: Colors.textMuted,
    marginTop: 2,
  },
  insufficientBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: Colors.surfaceContainer,
    padding: 10,
    borderRadius: 10,
  },
  insufficientText: {
    fontSize: 12,
    color: Colors.textMuted,
    flex: 1,
    lineHeight: 16,
  },
  graphContainer: {
    backgroundColor: Colors.surfaceContainerLow,
    borderRadius: 12,
    padding: Spacing.sm + 4,
    gap: 12,
  },
  graphHeader: {
    fontSize: 11,
    fontWeight: '700',
    color: Colors.textSubtle,
    textTransform: 'uppercase',
    letterSpacing: 0.4,
    marginBottom: 6,
  },
  contextGraphBox: {
    gap: 6,
  },
  barRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  barLabel: {
    width: 68,
    fontSize: 12,
    fontWeight: '600',
    color: Colors.textStrong,
  },
  barTrack: {
    flex: 1,
    height: 12,
    backgroundColor: Colors.surfaceContainer,
    borderRadius: 6,
    overflow: 'hidden',
  },
  barFill: {
    height: '100%',
    borderRadius: 6,
  },
  barValueText: {
    width: 78,
    textAlign: 'right',
    fontSize: 11,
    fontWeight: '700',
    color: Colors.textStrong,
  },
  barSampleText: {
    fontSize: 10,
    fontWeight: '400',
    color: Colors.textMuted,
  },
  timeSeriesBox: {
    gap: 6,
    paddingTop: 4,
    borderTopWidth: 1,
    borderTopColor: Colors.surfaceContainer,
  },
  timeSeriesHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  realPointsBadge: {
    fontSize: 9,
    fontWeight: '600',
    color: Colors.secondary,
    textTransform: 'uppercase',
    letterSpacing: 0.3,
  },
  timelineRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    justifyContent: 'space-between',
    height: 90,
    paddingTop: 10,
  },
  timelineBarItem: {
    alignItems: 'center',
    flex: 1,
    gap: 4,
  },
  timelineValText: {
    fontSize: 9,
    fontWeight: '700',
    color: Colors.textSubtle,
  },
  timelineBarTrack: {
    height: 60,
    justifyContent: 'flex-end',
    alignItems: 'center',
    width: 14,
  },
  timelineBarFill: {
    width: 10,
    borderRadius: 4,
  },
  timelineDateText: {
    fontSize: 9,
    fontWeight: '600',
    color: Colors.textMuted,
  },
  footerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 2,
  },
  footerText: {
    fontSize: 10,
    color: Colors.textMuted,
  },
  inactiveNoticeCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.surfaceContainer,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    marginTop: 6,
    marginBottom: 4,
  },
  inactiveNoticeText: {
    flex: 1,
    fontSize: 12,
    color: Colors.textMuted,
    lineHeight: 16,
  },
});
