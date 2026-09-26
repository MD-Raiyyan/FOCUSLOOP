import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  SafeAreaView,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Header } from '@/components/Header';
import { Colors } from '@/constants/theme';

export default function TodayScreen() {
  const router = useRouter();
  const [activeFilter, setActiveFilter] = useState('All');
  const [task2Status, setTask2Status] = useState<'In Progress' | 'Done' | 'Partial' | 'Deferred'>('In Progress');
  const [aiPrompt, setAiPrompt] = useState('');

  return (
    <SafeAreaView style={styles.safeArea}>
      <Header title="Today" />

      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Welcome Header */}
        <View style={styles.welcomeRow}>
          <View>
            <View style={styles.greetingRow}>
              <Text style={styles.greetingText}>Hello, Alex</Text>
              <Text style={styles.handWave}>👋</Text>
            </View>
            <Text style={styles.mainHeader}>Good Morning!</Text>
            <Text style={styles.subHeader}>Let's build your focus rhythm today.</Text>
          </View>
          <TouchableOpacity
            style={styles.mascotBadge}
            onPress={() => router.push('/ai-coach')}
            activeOpacity={0.8}
          >
            <Ionicons name="sparkles" size={24} color={Colors.primary} />
            <View style={styles.onlineDot} />
          </TouchableOpacity>
        </View>

        {/* AI Quick Input Bar */}
        <View style={styles.aiBarContainer}>
          <View style={styles.aiIconCircle}>
            <Ionicons name="sparkles-outline" size={16} color={Colors.primary} />
          </View>
          <TextInput
            style={styles.aiInput}
            placeholder="Ask AI Assistant or log a feeling..."
            placeholderTextColor={Colors.textMuted}
            value={aiPrompt}
            onChangeText={setAiPrompt}
          />
          <TouchableOpacity style={styles.aiActionIcon}>
            <Ionicons name="mic-outline" size={18} color={Colors.textSubtle} />
          </TouchableOpacity>
          <TouchableOpacity style={styles.aiSendButton} activeOpacity={0.8}>
            <Ionicons name="arrow-up" size={16} color={Colors.onPrimary} />
          </TouchableOpacity>
        </View>

        {/* Today's Overview 4-Card Bento Grid */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Today's Overview</Text>
          <TouchableOpacity>
            <Text style={styles.linkText}>Weekly Report</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.bentoGrid}>
          {/* Card 1: Tasks */}
          <View style={[styles.bentoCard, { backgroundColor: Colors.surfaceTintViolet }]}>
            <View style={styles.cardTopRow}>
              <View style={styles.cardIconBox}>
                <Ionicons name="checkmark-circle" size={18} color={Colors.primary} />
              </View>
              <Text style={[styles.cardTag, { color: Colors.primary }]}>TASKS</Text>
            </View>
            <View style={styles.cardMetricRow}>
              <Text style={styles.statMetric}>4</Text>
              <Text style={styles.statSubText}>/ 6 Done</Text>
            </View>
            <Text style={styles.cardFooterText}>• On schedule</Text>
          </View>

          {/* Card 2: Focus Time */}
          <View style={[styles.bentoCard, { backgroundColor: Colors.surfaceTintBlue }]}>
            <View style={styles.cardTopRow}>
              <View style={styles.cardIconBox}>
                <Ionicons name="time" size={18} color={Colors.accentIndigo} />
              </View>
              <Text style={[styles.cardTag, { color: Colors.accentIndigo }]}>FOCUS</Text>
            </View>
            <View style={styles.cardMetricRow}>
              <Text style={styles.statMetric}>3.8</Text>
              <Text style={styles.statSubText}>hrs</Text>
            </View>
            <Text style={styles.cardFooterText}>• Target: 4.5 hrs</Text>
          </View>

          {/* Card 3: Start Lag */}
          <View style={[styles.bentoCard, { backgroundColor: Colors.surfaceTintMint }]}>
            <View style={styles.cardTopRow}>
              <View style={styles.cardIconBox}>
                <Ionicons name="flash" size={18} color={Colors.secondary} />
              </View>
              <Text style={[styles.cardTag, { color: Colors.secondary }]}>START LAG</Text>
            </View>
            <View style={styles.cardMetricRow}>
              <Text style={styles.statMetric}>12</Text>
              <Text style={styles.statSubText}>mins</Text>
            </View>
            <Text style={[styles.cardFooterText, { color: Colors.secondary, fontWeight: '600' }]}>
              ↓ 57% faster today
            </Text>
          </View>

          {/* Card 4: Recovery / Sleep */}
          <View style={[styles.bentoCard, { backgroundColor: Colors.surfaceTintAmber }]}>
            <View style={styles.cardTopRow}>
              <View style={styles.cardIconBox}>
                <Ionicons name="moon" size={18} color={Colors.tertiaryContainer} />
              </View>
              <Text style={[styles.cardTag, { color: Colors.tertiaryContainer }]}>RECOVERY</Text>
            </View>
            <View style={styles.cardMetricRow}>
              <Text style={styles.statMetric}>7h 45</Text>
              <Text style={styles.statSubText}>m</Text>
            </View>
            <Text style={[styles.cardFooterText, { color: Colors.tertiary, fontWeight: '600' }]}>
              Well Rested ✨
            </Text>
          </View>
        </View>

        {/* Feeling Stuck / Delay Check Banner */}
        <View style={styles.stuckBanner}>
          <View style={styles.stuckHeader}>
            <View style={styles.stuckIconBox}>
              <Ionicons name="sparkles" size={20} color={Colors.accentCoral} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.stuckTitle}>Feeling stuck or delaying?</Text>
              <Text style={styles.stuckDesc}>
                It's completely normal. Check in with zero guilt and discover your loop breaker.
              </Text>
            </View>
          </View>
          <View style={styles.stuckFooter}>
            <TouchableOpacity
              style={styles.stuckBtn}
              onPress={() => router.push('/delay-log')}
              activeOpacity={0.8}
            >
              <Ionicons name="leaf-outline" size={16} color={Colors.accentCoral} />
              <Text style={styles.stuckBtnText}>Start Mindful Delay Check</Text>
            </TouchableOpacity>
            <Text style={styles.stuckMetaText}>Takes 2 mins • No shame</Text>
          </View>
        </View>

        {/* Active Behavioral Experiment Card */}
        <View style={styles.experimentCard}>
          <View style={styles.cardTopRow}>
            <View style={styles.labHeaderTitle}>
              <View style={styles.labIconBox}>
                <Ionicons name="flask-outline" size={16} color={Colors.primary} />
              </View>
              <Text style={styles.labTagText}>ACTIVE LOOP EXPERIMENT</Text>
            </View>
            <View style={styles.dayBadge}>
              <Text style={styles.dayBadgeText}>Day 4 of 7</Text>
            </View>
          </View>

          <Text style={styles.expTitle}>10-Min Micro-Start Buffer</Text>
          <Text style={styles.expDesc}>
            Start with just opening the doc for 2 minutes before the full block.
          </Text>

          <View style={styles.progressContainer}>
            <View style={styles.trackBackground}>
              <View style={[styles.trackFill, { width: '57%' }]} />
            </View>
            <View style={styles.progressLabelRow}>
              <Text style={styles.progressHighlight}>✨ Start delay reduced by 22 mins</Text>
              <Text style={styles.progressPercent}>57% done</Text>
            </View>
          </View>
        </View>

        {/* Daily Loop Habits & Tasks Section */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Daily Loop & Tasks</Text>
          <Text style={styles.subTextRight}>3 Remaining</Text>
        </View>

        {/* Filter Chips */}
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={styles.filterScroll}
          contentContainerStyle={styles.filterContainer}
        >
          {['All', 'High Priority', 'In Progress', 'Done'].map((filter) => (
            <TouchableOpacity
              key={filter}
              style={[
                styles.filterChip,
                activeFilter === filter && styles.filterChipActive,
              ]}
              onPress={() => setActiveFilter(filter)}
            >
              <Text
                style={[
                  styles.filterChipText,
                  activeFilter === filter && styles.filterChipTextActive,
                ]}
              >
                {filter}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* Task List */}
        <View style={styles.taskList}>
          {/* Task 1: Completed */}
          <View style={[styles.taskCard, { opacity: 0.85 }]}>
            <View style={styles.taskLeftRow}>
              <View style={[styles.taskIconBox, { backgroundColor: Colors.surfaceTintMint }]}>
                <Ionicons name="checkmark" size={18} color={Colors.secondary} />
              </View>
              <View style={styles.taskTextColumn}>
                <Text style={[styles.taskTitle, styles.completedText]}>Morning Deep Work Block</Text>
                <Text style={styles.taskMeta}>9:30 AM • Completed in 45m</Text>
              </View>
            </View>
            <View style={styles.doneBadge}>
              <Ionicons name="checkmark-done" size={14} color={Colors.secondary} />
              <Text style={styles.doneBadgeText}>Done</Text>
            </View>
          </View>

          {/* Task 2: In Progress with 1-Tap Quick Action Feedback Strip */}
          <View style={[styles.taskCard, styles.taskCardActive]}>
            <View style={styles.taskLeftRow}>
              <View style={[styles.taskIconBox, { backgroundColor: Colors.surfaceTintViolet }]}>
                <Ionicons name="create-outline" size={18} color={Colors.primary} />
              </View>
              <View style={styles.taskTextColumn}>
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                  <Text style={styles.taskTitle}>Drafting System Architecture</Text>
                  <View style={styles.pulseDot} />
                </View>
                <Text style={styles.taskMeta}>Started 2:15 PM • High Focus</Text>
              </View>
            </View>
            <View style={styles.inProgressBadge}>
              <Text style={styles.inProgressBadgeText}>{task2Status}</Text>
            </View>

            {/* 1-Tap Action Strip */}
            <View style={styles.actionStrip}>
              <Text style={styles.actionStripLabel}>Update:</Text>
              <TouchableOpacity
                style={[styles.actionBtn, { backgroundColor: Colors.surfaceTintMint }]}
                onPress={() => setTask2Status('Done')}
              >
                <Ionicons name="checkmark-circle-outline" size={14} color={Colors.secondary} />
                <Text style={[styles.actionBtnText, { color: Colors.secondary }]}>Done</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.actionBtn, { backgroundColor: Colors.surfaceTintViolet }]}
                onPress={() => setTask2Status('Partial')}
              >
                <Ionicons name="time-outline" size={14} color={Colors.primary} />
                <Text style={[styles.actionBtnText, { color: Colors.primary }]}>Partial</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.actionBtn, { backgroundColor: Colors.surfaceContainer }]}
                onPress={() => setTask2Status('Deferred')}
              >
                <Ionicons name="arrow-forward-outline" size={14} color={Colors.textSubtle} />
                <Text style={[styles.actionBtnText, { color: Colors.textSubtle }]}>Defer</Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* Task 3: Scheduled */}
          <View style={styles.taskCard}>
            <View style={styles.taskLeftRow}>
              <View style={[styles.taskIconBox, { backgroundColor: Colors.surfaceTintBlue }]}>
                <Ionicons name="code-slash-outline" size={18} color={Colors.accentIndigo} />
              </View>
              <View style={styles.taskTextColumn}>
                <Text style={styles.taskTitle}>Review PR & Code Specs</Text>
                <Text style={styles.taskMeta}>Scheduled 4:00 PM • 30m</Text>
              </View>
            </View>
            <TouchableOpacity style={styles.playBtn}>
              <Ionicons name="play" size={16} color={Colors.primary} />
            </TouchableOpacity>
          </View>
        </View>

        {/* Upcoming Schedule Snapshot */}
        <View style={styles.scheduleCard}>
          <View style={styles.cardTopRow}>
            <Text style={styles.sectionTitle}>Next Up Today</Text>
            <Text style={styles.subTextRight}>Sync with Calendar</Text>
          </View>
          <View style={styles.scheduleInner}>
            <View style={styles.accentBar} />
            <View style={{ flex: 1 }}>
              <Text style={styles.scheduleTitle}>Design System Review with Mia</Text>
              <Text style={styles.scheduleTime}>5:15 PM – 5:45 PM • Google Meet</Text>
            </View>
            <View style={styles.timeTag}>
              <Text style={styles.timeTagText}>in 45 min</Text>
            </View>
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
  welcomeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  greetingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  greetingText: {
    fontSize: 13,
    color: Colors.textSubtle,
  },
  handWave: {
    fontSize: 14,
  },
  mainHeader: {
    fontSize: 20,
    fontWeight: '700',
    color: Colors.textStrong,
    marginTop: 2,
  },
  subHeader: {
    fontSize: 13,
    color: Colors.textSubtle,
    marginTop: 2,
  },
  mascotBadge: {
    width: 48,
    height: 48,
    borderRadius: 16,
    backgroundColor: Colors.surfaceTintViolet,
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
    shadowColor: Colors.primaryContainer,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.12,
    shadowRadius: 8,
    elevation: 3,
  },
  onlineDot: {
    position: 'absolute',
    top: 6,
    right: 6,
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: Colors.secondary,
    borderWidth: 1.5,
    borderColor: '#FFFFFF',
  },
  aiBarContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.neutralCard,
    borderRadius: 24,
    paddingHorizontal: 12,
    paddingVertical: 6,
    marginBottom: 20,
    shadowColor: '#64748B',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.06,
    shadowRadius: 10,
    elevation: 2,
  },
  aiIconCircle: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: Colors.surfaceTintViolet,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 8,
  },
  aiInput: {
    flex: 1,
    fontSize: 13,
    color: Colors.textStrong,
    paddingVertical: 4,
  },
  aiActionIcon: {
    padding: 6,
  },
  aiSendButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: Colors.primaryContainer,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 6,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.textStrong,
  },
  linkText: {
    fontSize: 10,
    fontWeight: '600',
    color: Colors.primary,
  },
  subTextRight: {
    fontSize: 10,
    color: Colors.textSubtle,
  },
  bentoGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 20,
  },
  bentoCard: {
    width: '48%',
    borderRadius: 16,
    padding: 14,
    justifyContent: 'space-between',
    minHeight: 110,
  },
  cardTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cardIconBox: {
    width: 32,
    height: 32,
    borderRadius: 10,
    backgroundColor: Colors.neutralCard,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cardTag: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  cardMetricRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginTop: 8,
  },
  statMetric: {
    fontSize: 28,
    fontWeight: '700',
    color: Colors.textStrong,
  },
  statSubText: {
    fontSize: 13,
    color: Colors.textSubtle,
    marginLeft: 4,
  },
  cardFooterText: {
    fontSize: 11,
    color: Colors.textSubtle,
    marginTop: 4,
  },
  stuckBanner: {
    borderRadius: 16,
    backgroundColor: Colors.surfaceTintAmber,
    padding: 14,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: 'rgba(244, 63, 94, 0.1)',
  },
  stuckHeader: {
    flexDirection: 'row',
    gap: 12,
  },
  stuckIconBox: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: Colors.neutralCard,
    alignItems: 'center',
    justifyContent: 'center',
  },
  stuckTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.textStrong,
  },
  stuckDesc: {
    fontSize: 11,
    color: Colors.textSubtle,
    marginTop: 2,
    lineHeight: 16,
  },
  stuckFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 12,
    flexWrap: 'wrap',
    gap: 8,
  },
  stuckBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.neutralCard,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    gap: 6,
  },
  stuckBtnText: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.textStrong,
  },
  stuckMetaText: {
    fontSize: 11,
    color: Colors.textMuted,
  },
  experimentCard: {
    backgroundColor: Colors.neutralCard,
    borderRadius: 16,
    padding: 14,
    marginBottom: 20,
    shadowColor: '#64748B',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.06,
    shadowRadius: 10,
    elevation: 2,
  },
  labHeaderTitle: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  labIconBox: {
    width: 28,
    height: 28,
    borderRadius: 8,
    backgroundColor: Colors.surfaceTintViolet,
    alignItems: 'center',
    justifyContent: 'center',
  },
  labTagText: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.textSubtle,
    letterSpacing: 0.5,
  },
  dayBadge: {
    backgroundColor: Colors.surfaceTintViolet,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  dayBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.primary,
  },
  expTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.textStrong,
    marginTop: 10,
  },
  expDesc: {
    fontSize: 11,
    color: Colors.textSubtle,
    marginTop: 2,
  },
  progressContainer: {
    marginTop: 12,
  },
  trackBackground: {
    height: 8,
    borderRadius: 4,
    backgroundColor: Colors.surfaceContainerHigh,
    overflow: 'hidden',
  },
  trackFill: {
    height: '100%',
    borderRadius: 4,
    backgroundColor: Colors.primary,
  },
  progressLabelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 6,
  },
  progressHighlight: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.secondary,
  },
  progressPercent: {
    fontSize: 11,
    color: Colors.textMuted,
  },
  filterScroll: {
    marginBottom: 12,
  },
  filterContainer: {
    flexDirection: 'row',
    gap: 6,
  },
  filterChip: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: Colors.surfaceContainer,
  },
  filterChipActive: {
    backgroundColor: Colors.primary,
  },
  filterChipText: {
    fontSize: 10,
    fontWeight: '600',
    color: Colors.textSubtle,
  },
  filterChipTextActive: {
    color: Colors.onPrimary,
  },
  taskList: {
    gap: 10,
    marginBottom: 20,
  },
  taskCard: {
    backgroundColor: Colors.neutralCard,
    borderRadius: 16,
    padding: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.03,
    shadowRadius: 6,
    elevation: 1,
  },
  taskCardActive: {
    flexDirection: 'column',
    alignItems: 'stretch',
    borderWidth: 1,
    borderColor: 'rgba(99, 91, 255, 0.15)',
  },
  taskLeftRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flex: 1,
  },
  taskIconBox: {
    width: 36,
    height: 36,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  taskTextColumn: {
    flex: 1,
  },
  taskTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.textStrong,
  },
  completedText: {
    textDecorationLine: 'line-through',
    color: Colors.textMuted,
  },
  taskMeta: {
    fontSize: 11,
    color: Colors.textSubtle,
    marginTop: 2,
  },
  doneBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.surfaceTintMint,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    gap: 4,
  },
  doneBadgeText: {
    fontSize: 10,
    fontWeight: '600',
    color: Colors.secondary,
  },
  inProgressBadge: {
    backgroundColor: Colors.surfaceTintAmber,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 10,
    alignSelf: 'flex-start',
    marginTop: 4,
  },
  inProgressBadgeText: {
    fontSize: 10,
    fontWeight: '600',
    color: Colors.tertiaryContainer,
  },
  pulseDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: Colors.accentCoral,
  },
  actionStrip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 12,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: Colors.neutralBorder,
  },
  actionStripLabel: {
    fontSize: 11,
    color: Colors.textMuted,
    marginRight: 2,
  },
  actionBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 6,
    borderRadius: 10,
    gap: 4,
  },
  actionBtnText: {
    fontSize: 10,
    fontWeight: '600',
  },
  playBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: Colors.surfaceTintViolet,
    alignItems: 'center',
    justifyContent: 'center',
  },
  scheduleCard: {
    backgroundColor: Colors.neutralCard,
    borderRadius: 16,
    padding: 14,
    marginBottom: 20,
  },
  scheduleInner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.surfaceContainerLow,
    padding: 10,
    borderRadius: 12,
    gap: 10,
    marginTop: 8,
  },
  accentBar: {
    width: 4,
    height: 32,
    borderRadius: 2,
    backgroundColor: Colors.primary,
  },
  scheduleTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.textStrong,
  },
  scheduleTime: {
    fontSize: 11,
    color: Colors.textSubtle,
    marginTop: 2,
  },
  timeTag: {
    backgroundColor: Colors.neutralCard,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 10,
  },
  timeTagText: {
    fontSize: 10,
    fontWeight: '600',
    color: Colors.primary,
  },
});
