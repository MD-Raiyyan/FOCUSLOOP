import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  SafeAreaView,
  ActivityIndicator,
  Modal,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Header } from '@/components/Header';
import { Colors } from '@/constants/theme';
import { useAuth } from '@/hooks/useAuth';
import { useTasks } from '@/hooks/useTasks';
import { useBehavior } from '@/hooks/useBehavior';
import { useExperiments } from '@/hooks/useExperiments';
import { CheckinStatus } from '@/types/checkin';
import { TaskFrequency } from '@/types/tasks';
import { formatCheckinDate, formatMinutes, getLocalDateString } from '@/utils/formatters';

export default function TodayScreen() {
  const router = useRouter();
  const { user } = useAuth();
  const todayDate = getLocalDateString();
  const {
    tasks,
    isLoading: tasksLoading,
    error: tasksError,
    createTask,
    checkinTask,
    deleteTask,
    inFlightTasks,
    checkins,
    checkinsLoading,
    checkinsError,
    refreshCheckins,
  } = useTasks();
  const { summary, isLoading: behaviorLoading, refresh: refreshBehavior } = useBehavior(todayDate);
  const { experiments } = useExperiments();

  const [activeFilter, setActiveFilter] = useState('All');
  const [aiPrompt, setAiPrompt] = useState('');

  // Task creation modal state
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [taskName, setTaskName] = useState('');
  const [taskCategory, setTaskCategory] = useState('Focus');
  const [taskPlannedTime, setTaskPlannedTime] = useState('09:00');
  const [taskDuration, setTaskDuration] = useState('30');
  const [taskFrequency, setTaskFrequency] = useState<TaskFrequency>('daily');
  const [isSubmittingTask, setIsSubmittingTask] = useState(false);

  // Status editing state for tasks that already have a check-in
  const [editingTaskId, setEditingTaskId] = useState<string | null>(null);

  // Check-in feedback state
  const [checkinMessage, setCheckinMessage] = useState<string | null>(null);

  const activeExperiment = experiments.find((exp) => exp.status === 'active');

  const handleCreateTask = async () => {
    if (!taskName.trim()) {
      Alert.alert('Required Field', 'Please enter a task name.');
      return;
    }
    try {
      setIsSubmittingTask(true);
      await createTask({
        name: taskName.trim(),
        category: taskCategory.trim() || 'Focus',
        planned_time: taskPlannedTime.trim() || '09:00',
        target_duration_minutes: taskDuration.trim() || '30',
        frequency: taskFrequency,
        active: true,
      });
      setTaskName('');
      setTaskFrequency('daily');
      setIsModalVisible(false);
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Failed to create task');
    } finally {
      setIsSubmittingTask(false);
    }
  };

  const handleCheckin = async (taskId: string, status: CheckinStatus) => {
    try {
      const res = await checkinTask(taskId, status);
      if (res) {
        setEditingTaskId(null);
        setCheckinMessage(`Check-in recorded as "${status}". Great job!`);
        setTimeout(() => setCheckinMessage(null), 3000);
        // Refresh authoritative behavior summary immediately for today's overview
        await refreshBehavior();
      }
    } catch (err: any) {
      Alert.alert('Check-in Failed', err.message || 'Could not record check-in.');
    }
  };

  const handleDeleteTask = (taskId: string, name: string) => {
    Alert.alert('Delete Task', `Are you sure you want to remove "${name}"?`, [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          try {
            await deleteTask(taskId);
          } catch (err: any) {
            Alert.alert('Error', err.message || 'Failed to delete task');
          }
        },
      },
    ]);
  };

  const handleAiSend = () => {
    if (!aiPrompt.trim()) return;
    router.push({
      pathname: '/(tabs)/ai-coach' as any,
      params: { initialPrompt: aiPrompt },
    });
    setAiPrompt('');
  };

  const filteredTasks = tasks.filter((t) => {
    if (activeFilter === 'All') return true;
    if (activeFilter === 'High Priority') return t.category?.toLowerCase().includes('deep') || t.category?.toLowerCase().includes('priority');
    if (activeFilter === 'Focus') return t.category?.toLowerCase().includes('focus');
    return true;
  });

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
              <Text style={styles.greetingText}>Hello, {user?.name || 'Explorer'}</Text>
              <Text style={styles.handWave}>👋</Text>
            </View>
            <Text style={styles.mainHeader}>Welcome Back</Text>
            <Text style={styles.subHeader}>Track verified focus sessions grounded in real data.</Text>
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

        {/* Check-in Notification Banner */}
        {checkinMessage && (
          <View style={styles.notificationBox}>
            <Ionicons name="checkmark-circle" size={18} color={Colors.secondary} />
            <Text style={styles.notificationText}>{checkinMessage}</Text>
          </View>
        )}

        {/* AI Quick Input Bar */}
        <View style={styles.aiBarContainer}>
          <View style={styles.aiIconCircle}>
            <Ionicons name="sparkles-outline" size={16} color={Colors.primary} />
          </View>
          <TextInput
            style={styles.aiInput}
            placeholder="Ask AI Coach grounded in your data..."
            placeholderTextColor={Colors.textMuted}
            value={aiPrompt}
            onChangeText={setAiPrompt}
            onSubmitEditing={handleAiSend}
          />
          <TouchableOpacity style={styles.aiSendButton} onPress={handleAiSend} activeOpacity={0.8}>
            <Ionicons name="arrow-up" size={16} color={Colors.onPrimary} />
          </TouchableOpacity>
        </View>

        {/* Today's Overview 4-Card Bento Grid */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Today's Overview</Text>
          <TouchableOpacity onPress={() => router.push('/insights')}>
            <Text style={styles.linkText}>View Insights</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.bentoGrid}>
          {/* Card 1: Completed Tasks */}
          <View style={[styles.bentoCard, { backgroundColor: Colors.surfaceTintViolet }]}>
            <View style={styles.cardTopRow}>
              <View style={styles.cardIconBox}>
                <Ionicons name="checkmark-circle" size={18} color={Colors.primary} />
              </View>
              <Text style={[styles.cardTag, { color: Colors.primary }]}>TASKS</Text>
            </View>
            <View style={styles.cardMetricRow}>
              <Text style={styles.statMetric}>
                {behaviorLoading ? '...' : (summary?.completed_tasks ?? 0)}
              </Text>
              <Text style={styles.statSubText}>Done</Text>
            </View>
            <Text style={styles.cardFooterText}>
              {summary && summary.total_tasks_tracked > 0
                ? `• ${Math.round(summary.completion_rate * 100)}% completion rate`
                : '• No check-ins yet today'}
            </Text>
          </View>

          {/* Card 2: Total Procrastination / Delay */}
          <View style={[styles.bentoCard, { backgroundColor: Colors.surfaceTintBlue }]}>
            <View style={styles.cardTopRow}>
              <View style={styles.cardIconBox}>
                <Ionicons name="pause-circle-outline" size={18} color={Colors.accentIndigo} />
              </View>
              <Text style={[styles.cardTag, { color: Colors.accentIndigo }]}>DELAY</Text>
            </View>
            <View style={styles.cardMetricRow}>
              <Text style={styles.statMetric}>
                {behaviorLoading ? '...' : (summary?.total_procrastination_minutes ?? 0)}
              </Text>
              <Text style={styles.statSubText}>mins</Text>
            </View>
            <Text style={styles.cardFooterText}>
              • {summary?.procrastination_count ?? 0} friction episodes
            </Text>
          </View>

          {/* Card 3: Start Lag */}
          <View style={[styles.bentoCard, { backgroundColor: Colors.surfaceTintMint }]}>
            <View style={styles.cardTopRow}>
              <View style={styles.cardIconBox}>
                <Ionicons name="flash" size={18} color={Colors.secondary} />
              </View>
              <Text style={[styles.cardTag, { color: Colors.secondary }]}>AVG LAG</Text>
            </View>
            <View style={styles.cardMetricRow}>
              <Text style={styles.statMetric}>
                {behaviorLoading
                  ? '...'
                  : summary?.average_start_delay_minutes != null
                  ? summary.average_start_delay_minutes.toFixed(0)
                  : '—'}
              </Text>
              <Text style={styles.statSubText}>
                {summary?.average_start_delay_minutes != null ? 'mins' : ''}
              </Text>
            </View>
            <Text style={[styles.cardFooterText, { color: Colors.secondary, fontWeight: '600' }]}>
              {summary?.average_start_delay_minutes != null
                ? `• Best: ${summary.best_focus_window || 'Morning'}`
                : '• No delay logged today'}
            </Text>
          </View>

          {/* Card 4: Active Loop Experiment */}
          <View style={[styles.bentoCard, { backgroundColor: Colors.surfaceTintAmber }]}>
            <View style={styles.cardTopRow}>
              <View style={styles.cardIconBox}>
                <Ionicons name="flask-outline" size={18} color={Colors.tertiaryContainer} />
              </View>
              <Text style={[styles.cardTag, { color: Colors.tertiaryContainer }]}>EXPERIMENT</Text>
            </View>
            <View style={styles.cardMetricRow}>
              <Text style={styles.statMetric}>
                {experiments.length}
              </Text>
              <Text style={styles.statSubText}>total</Text>
            </View>
            <Text style={[styles.cardFooterText, { color: Colors.tertiary, fontWeight: '600' }]}>
              • {activeExperiment ? 'Active cycle' : 'None active'}
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
                It's completely normal. Record a compassionate friction intercept without guilt.
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
            <Text style={styles.stuckMetaText}>Authoritative Backend Event</Text>
          </View>
        </View>

        {/* Active Behavioral Experiment Card */}
        {activeExperiment && (
          <View style={styles.experimentCard}>
            <View style={styles.cardTopRow}>
              <View style={styles.labHeaderTitle}>
                <View style={styles.labIconBox}>
                  <Ionicons name="flask-outline" size={16} color={Colors.primary} />
                </View>
                <Text style={styles.labTagText}>ACTIVE EXPERIMENT</Text>
              </View>
              <View style={styles.dayBadge}>
                <Text style={styles.dayBadgeText}>Active</Text>
              </View>
            </View>

            <Text style={styles.expTitle}>{activeExperiment.title}</Text>
            <Text style={styles.expDesc}>{activeExperiment.hypothesis}</Text>

            <View style={styles.progressContainer}>
              <View style={styles.progressLabelRow}>
                <Text style={styles.progressHighlight}>Target: {activeExperiment.target_metric}</Text>
                <Text style={styles.progressPercent}>{activeExperiment.target_value ?? '—'}</Text>
              </View>
            </View>
          </View>
        )}

        {/* Daily Loop Habits & Tasks Section Header */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Daily Loop Tasks</Text>
          <TouchableOpacity
            style={styles.addTaskBtn}
            onPress={() => setIsModalVisible(true)}
            activeOpacity={0.8}
          >
            <Ionicons name="add" size={16} color="#FFFFFF" />
            <Text style={styles.addTaskBtnText}>New Task</Text>
          </TouchableOpacity>
        </View>

        {/* Filter Chips */}
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={styles.filterScroll}
          contentContainerStyle={styles.filterContainer}
        >
          {['All', 'Focus', 'High Priority'].map((filter) => (
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
          {tasksLoading ? (
            <View style={styles.loadingBox}>
              <ActivityIndicator size="small" color={Colors.primary} />
              <Text style={styles.loadingText}>Loading tasks from backend...</Text>
            </View>
          ) : tasksError ? (
            <View style={styles.errorBox}>
              <Ionicons name="alert-circle-outline" size={24} color="#DC2626" />
              <Text style={styles.errorBoxText}>{tasksError}</Text>
            </View>
          ) : filteredTasks.length === 0 ? (
            <View style={styles.emptyTaskCard}>
              <Ionicons name="calendar-outline" size={28} color={Colors.textMuted} />
              <Text style={styles.emptyTaskTitle}>No tasks scheduled</Text>
              <Text style={styles.emptyTaskSubtitle}>
                Add a daily task to track your focus duration and completion check-ins.
              </Text>
              <TouchableOpacity
                style={styles.emptyAddBtn}
                onPress={() => setIsModalVisible(true)}
              >
                <Ionicons name="add-circle-outline" size={18} color={Colors.primary} />
                <Text style={styles.emptyAddBtnText}>Add Your First Task</Text>
              </TouchableOpacity>
            </View>
          ) : (
            filteredTasks.map((task) => (
              <View key={task.id} style={styles.taskCard}>
                <View style={styles.taskCardTop}>
                  <View style={styles.taskInfoLeft}>
                    <View style={styles.badgesRow}>
                      <View style={styles.categoryBadge}>
                        <Text style={styles.categoryBadgeText}>{task.category || 'Focus'}</Text>
                      </View>
                      <View
                        style={[
                          styles.frequencyBadge,
                          task.frequency === 'once' && styles.frequencyBadgeOnce,
                        ]}
                      >
                        <Ionicons
                          name={task.frequency === 'once' ? 'flag-outline' : 'repeat-outline'}
                          size={10}
                          color={task.frequency === 'once' ? '#D97706' : Colors.primary}
                        />
                        <Text
                          style={[
                            styles.frequencyBadgeText,
                            task.frequency === 'once' && styles.frequencyBadgeOnceText,
                          ]}
                        >
                          {task.frequency === 'once' ? 'One-time' : 'Daily'}
                        </Text>
                      </View>
                    </View>
                    <Text style={styles.taskTitle}>{task.name}</Text>
                    <View style={styles.taskMetaRow}>
                      <Ionicons name="time-outline" size={12} color={Colors.textSubtle} />
                      <Text style={styles.taskMeta}>
                        {task.planned_time || '09:00'} • {task.target_duration_minutes || '30'} mins
                      </Text>
                    </View>
                  </View>
                  <TouchableOpacity
                    onPress={() => handleDeleteTask(task.id, task.name)}
                    hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
                  >
                    <Ionicons name="trash-outline" size={18} color={Colors.textMuted} />
                  </TouchableOpacity>
                </View>

                {/* Occurrence State or Check-in Controls */}
                {task.today_status && editingTaskId !== task.id ? (
                  <View
                    style={[
                      styles.occurrenceStatusBox,
                      task.today_status === 'done' && styles.occurrenceDone,
                      task.today_status === 'partial' && styles.occurrencePartial,
                      task.today_status === 'missed' && styles.occurrenceMissed,
                    ]}
                  >
                    <View style={styles.occurrenceLeft}>
                      {task.today_status === 'done' && (
                        <>
                          <Ionicons name="checkmark-circle" size={16} color={Colors.secondary} />
                          <Text style={[styles.occurrenceText, { color: Colors.secondary }]}>
                            {task.frequency === 'once' ? '✓ Completed' : '✓ Completed today'}
                          </Text>
                        </>
                      )}
                      {task.today_status === 'partial' && (
                        <>
                          <Ionicons name="time" size={16} color={Colors.tertiary} />
                          <Text style={[styles.occurrenceText, { color: Colors.tertiary }]}>
                            ◐ Partial today
                          </Text>
                        </>
                      )}
                      {task.today_status === 'missed' && (
                        <>
                          <Ionicons name="close-circle" size={16} color={Colors.textMuted} />
                          <Text style={[styles.occurrenceText, { color: Colors.textMuted }]}>
                            × Missed today
                          </Text>
                        </>
                      )}
                    </View>
                    <TouchableOpacity
                      style={styles.changeStatusBtn}
                      onPress={() => setEditingTaskId(task.id)}
                      hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
                    >
                      <Text style={styles.changeStatusBtnText}>Change</Text>
                      <Ionicons name="pencil" size={11} color={Colors.primary} />
                    </TouchableOpacity>
                  </View>
                ) : (
                  <View style={styles.actionStrip}>
                    <View style={styles.actionStripHeader}>
                      <Text style={styles.actionStripLabel}>
                        {editingTaskId === task.id ? 'Change status:' : 'Check in:'}
                      </Text>
                      {editingTaskId === task.id && (
                        <TouchableOpacity onPress={() => setEditingTaskId(null)}>
                          <Text style={styles.cancelEditBtnText}>Cancel</Text>
                        </TouchableOpacity>
                      )}
                    </View>
                    <View style={styles.actionButtonsRow}>
                      <TouchableOpacity
                        style={[
                          styles.actionBtn,
                          { backgroundColor: Colors.surfaceTintMint },
                          inFlightTasks[task.id] && { opacity: 0.5 },
                        ]}
                        disabled={inFlightTasks[task.id]}
                        onPress={() => handleCheckin(task.id, 'done')}
                      >
                        <Ionicons name="checkmark-circle-outline" size={14} color={Colors.secondary} />
                        <Text style={[styles.actionBtnText, { color: Colors.secondary }]}>Done</Text>
                      </TouchableOpacity>

                      <TouchableOpacity
                        style={[
                          styles.actionBtn,
                          { backgroundColor: Colors.surfaceTintAmber },
                          inFlightTasks[task.id] && { opacity: 0.5 },
                        ]}
                        disabled={inFlightTasks[task.id]}
                        onPress={() => handleCheckin(task.id, 'partial')}
                      >
                        <Ionicons name="hourglass-outline" size={14} color={Colors.tertiary} />
                        <Text style={[styles.actionBtnText, { color: Colors.tertiary }]}>Partial</Text>
                      </TouchableOpacity>

                      <TouchableOpacity
                        style={[
                          styles.actionBtn,
                          { backgroundColor: Colors.surfaceContainer },
                          inFlightTasks[task.id] && { opacity: 0.5 },
                        ]}
                        disabled={inFlightTasks[task.id]}
                        onPress={() => handleCheckin(task.id, 'missed')}
                      >
                        <Ionicons name="close-circle-outline" size={14} color={Colors.textMuted} />
                        <Text style={[styles.actionBtnText, { color: Colors.textMuted }]}>Missed</Text>
                      </TouchableOpacity>
                    </View>
                  </View>
                )}
              </View>
            ))
          )}
        </View>

        {/* Recent Check-ins / Task History Section */}
        <View style={styles.sectionHeader}>
          <View style={styles.sectionTitleRow}>
            <Text style={styles.sectionTitle}>Recent Check-ins</Text>
            {checkins.length > 0 && (
              <View style={styles.countBadge}>
                <Text style={styles.countBadgeText}>{checkins.length}</Text>
              </View>
            )}
          </View>
          {checkins.length > 0 && (
            <TouchableOpacity
              onPress={() => refreshCheckins()}
              hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
            >
              <Ionicons name="refresh-outline" size={16} color={Colors.primary} />
            </TouchableOpacity>
          )}
        </View>

        <View style={styles.checkinHistoryList}>
          {checkinsLoading && checkins.length === 0 ? (
            <View style={styles.loadingBox}>
              <ActivityIndicator size="small" color={Colors.primary} />
              <Text style={styles.loadingText}>Loading check-ins...</Text>
            </View>
          ) : checkinsError ? (
            <View style={styles.errorBox}>
              <Ionicons name="alert-circle-outline" size={24} color="#DC2626" />
              <Text style={styles.errorBoxText}>{checkinsError}</Text>
              <TouchableOpacity
                style={styles.retryBtn}
                onPress={() => refreshCheckins()}
                activeOpacity={0.8}
              >
                <Ionicons name="refresh" size={14} color={Colors.primary} />
                <Text style={styles.retryBtnText}>Try again</Text>
              </TouchableOpacity>
            </View>
          ) : checkins.length === 0 ? (
            <View style={styles.emptyCheckinCard}>
              <Ionicons name="time-outline" size={28} color={Colors.textMuted} />
              <Text style={styles.emptyCheckinTitle}>No check-ins yet</Text>
              <Text style={styles.emptyCheckinSubtitle}>
                Complete a task and record a check-in to start building your history.
              </Text>
            </View>
          ) : (
            checkins.map((checkin) => {
              const matchedTask = tasks.find((t) => t.id === checkin.task_id);
              const taskTitle = matchedTask ? matchedTask.name : (checkin.notes ? checkin.notes : 'Focus Session');

              let statusColor: string = Colors.secondary;
              let statusBg: string = Colors.surfaceTintMint;
              let statusIcon: keyof typeof Ionicons.glyphMap = 'checkmark-circle';
              let statusLabel = 'Done';

              if (checkin.status === 'partial') {
                statusColor = Colors.tertiary;
                statusBg = Colors.surfaceTintAmber;
                statusIcon = 'hourglass-outline';
                statusLabel = 'Partial';
              } else if (checkin.status === 'missed') {
                statusColor = Colors.textMuted;
                statusBg = Colors.surfaceContainer;
                statusIcon = 'close-circle-outline';
                statusLabel = 'Missed';
              }

              return (
                <View key={checkin.id} style={styles.checkinCard}>
                  <View style={styles.checkinCardTop}>
                    <View style={{ flex: 1, marginRight: 8 }}>
                      <Text style={styles.checkinTaskTitle}>{taskTitle}</Text>
                      <Text style={styles.checkinTimeMeta}>
                        {formatCheckinDate(checkin.date, checkin.created_at)}
                      </Text>
                    </View>
                    <View style={[styles.statusBadge, { backgroundColor: statusBg }]}>
                      <Ionicons name={statusIcon} size={13} color={statusColor} />
                      <Text style={[styles.statusBadgeText, { color: statusColor }]}>
                        {statusLabel}
                      </Text>
                    </View>
                  </View>

                  <View style={styles.checkinMetricsRow}>
                    {checkin.start_delay_minutes != null && (
                      <View style={styles.checkinMetricItem}>
                        <Ionicons name="flash-outline" size={12} color={Colors.textSubtle} />
                        <Text style={styles.checkinMetricText}>
                          Start delay: <Text style={styles.checkinMetricValue}>{formatMinutes(checkin.start_delay_minutes)}</Text>
                        </Text>
                      </View>
                    )}
                    {checkin.duration_minutes != null && (
                      <View style={styles.checkinMetricItem}>
                        <Ionicons name="timer-outline" size={12} color={Colors.textSubtle} />
                        <Text style={styles.checkinMetricText}>
                          Duration: <Text style={styles.checkinMetricValue}>{formatMinutes(checkin.duration_minutes)}</Text>
                        </Text>
                      </View>
                    )}
                  </View>

                  {checkin.notes && matchedTask && (
                    <View style={styles.checkinNotesRow}>
                      <Ionicons name="document-text-outline" size={12} color={Colors.textSubtle} />
                      <Text style={styles.checkinNotesText} numberOfLines={2}>
                        {checkin.notes}
                      </Text>
                    </View>
                  )}
                </View>
              );
            })
          )}
        </View>
      </ScrollView>

      {/* Task Creation Modal */}
      <Modal visible={isModalVisible} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>New Task</Text>
              <TouchableOpacity onPress={() => setIsModalVisible(false)}>
                <Ionicons name="close" size={24} color={Colors.textStrong} />
              </TouchableOpacity>
            </View>

            <Text style={styles.inputLabel}>Task Name *</Text>
            <TextInput
              style={styles.modalInput}
              placeholder="e.g. Deep Work: Writing Algorithm"
              placeholderTextColor="#9896B0"
              value={taskName}
              onChangeText={setTaskName}
            />

            <Text style={styles.inputLabel}>Category</Text>
            <TextInput
              style={styles.modalInput}
              placeholder="e.g. Focus, Writing, Engineering"
              placeholderTextColor="#9896B0"
              value={taskCategory}
              onChangeText={setTaskCategory}
            />

            <View style={styles.inputRow}>
              <View style={{ flex: 1 }}>
                <Text style={styles.inputLabel}>Planned Time (HH:MM)</Text>
                <TextInput
                  style={styles.modalInput}
                  placeholder="09:00"
                  placeholderTextColor="#9896B0"
                  value={taskPlannedTime}
                  onChangeText={setTaskPlannedTime}
                />
              </View>
              <View style={{ width: 12 }} />
              <View style={{ flex: 1 }}>
                <Text style={styles.inputLabel}>Duration (mins)</Text>
                <TextInput
                  style={styles.modalInput}
                  placeholder="30"
                  placeholderTextColor="#9896B0"
                  keyboardType="numeric"
                  value={taskDuration}
                  onChangeText={setTaskDuration}
                />
              </View>
            </View>

            {/* Recurrence selection */}
            <Text style={styles.inputLabel}>When should this task repeat?</Text>
            <View style={styles.recurrenceRow}>
              <TouchableOpacity
                style={[
                  styles.recurrenceOption,
                  taskFrequency === 'once' && styles.recurrenceOptionActive,
                ]}
                onPress={() => setTaskFrequency('once')}
                activeOpacity={0.8}
              >
                <Ionicons
                  name="flag-outline"
                  size={16}
                  color={taskFrequency === 'once' ? Colors.primary : Colors.textMuted}
                />
                <Text
                  style={[
                    styles.recurrenceOptionText,
                    taskFrequency === 'once' && styles.recurrenceOptionTextActive,
                  ]}
                >
                  One-time
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[
                  styles.recurrenceOption,
                  taskFrequency === 'daily' && styles.recurrenceOptionActive,
                ]}
                onPress={() => setTaskFrequency('daily')}
                activeOpacity={0.8}
              >
                <Ionicons
                  name="repeat-outline"
                  size={16}
                  color={taskFrequency === 'daily' ? Colors.primary : Colors.textMuted}
                />
                <Text
                  style={[
                    styles.recurrenceOptionText,
                    taskFrequency === 'daily' && styles.recurrenceOptionTextActive,
                  ]}
                >
                  Every day
                </Text>
              </TouchableOpacity>
            </View>
            <Text style={styles.recurrenceHelperText}>
              {taskFrequency === 'once'
                ? 'Track this task once.'
                : 'Repeat this task every day.'}
            </Text>

            <TouchableOpacity
              style={[styles.modalSubmitBtn, isSubmittingTask && { opacity: 0.6 }]}
              onPress={handleCreateTask}
              disabled={isSubmittingTask}
            >
              {isSubmittingTask ? (
                <ActivityIndicator color="#FFFFFF" size="small" />
              ) : (
                <Text style={styles.modalSubmitText}>Save Task to Backend</Text>
              )}
            </TouchableOpacity>
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
  notificationBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: Colors.surfaceTintMint,
    borderRadius: 12,
    padding: 10,
    marginBottom: 16,
  },
  notificationText: {
    fontSize: 13,
    color: Colors.secondary,
    fontWeight: '600',
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
    fontSize: 12,
    fontWeight: '600',
    color: Colors.primary,
  },
  addTaskBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: Colors.primary,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 14,
  },
  addTaskBtnText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FFFFFF',
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
    fontSize: 26,
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
  emptyTaskCard: {
    backgroundColor: Colors.neutralCard,
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: Colors.neutralBorder,
    borderStyle: 'dashed',
  },
  emptyTaskTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textStrong,
    marginTop: 8,
  },
  emptyTaskSubtitle: {
    fontSize: 12,
    color: Colors.textSubtle,
    textAlign: 'center',
    marginTop: 4,
    lineHeight: 16,
    paddingHorizontal: 16,
  },
  emptyAddBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 14,
    paddingVertical: 8,
    paddingHorizontal: 14,
    backgroundColor: Colors.surfaceTintViolet,
    borderRadius: 16,
  },
  emptyAddBtnText: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.primary,
  },
  taskCard: {
    backgroundColor: Colors.neutralCard,
    borderRadius: 16,
    padding: 14,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.03,
    shadowRadius: 6,
    elevation: 1,
  },
  taskCardTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  taskInfoLeft: {
    flex: 1,
  },
  badgesRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 4,
  },
  categoryBadge: {
    alignSelf: 'flex-start',
    backgroundColor: Colors.surfaceTintViolet,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
  },
  categoryBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.primary,
  },
  frequencyBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    backgroundColor: '#F3F1FB',
    borderWidth: 1,
    borderColor: '#E2DCF8',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
  },
  frequencyBadgeOnce: {
    backgroundColor: '#FFF7ED',
    borderColor: '#FFEDD5',
  },
  frequencyBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.primary,
  },
  frequencyBadgeOnceText: {
    color: '#D97706',
  },
  taskTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.textStrong,
  },
  taskMetaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 4,
  },
  taskMeta: {
    fontSize: 11,
    color: Colors.textSubtle,
  },
  occurrenceStatusBox: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 10,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  occurrenceDone: {
    backgroundColor: Colors.surfaceTintMint,
    borderColor: 'rgba(16, 185, 129, 0.2)',
  },
  occurrencePartial: {
    backgroundColor: Colors.surfaceTintAmber,
    borderColor: 'rgba(245, 158, 11, 0.2)',
  },
  occurrenceMissed: {
    backgroundColor: Colors.surfaceContainer,
    borderColor: Colors.neutralBorder,
  },
  occurrenceLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  occurrenceText: {
    fontSize: 12,
    fontWeight: '700',
  },
  changeStatusBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    backgroundColor: 'rgba(255, 255, 255, 0.8)',
  },
  changeStatusBtnText: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.primary,
  },
  actionStrip: {
    marginTop: 10,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: Colors.neutralBorder,
  },
  actionStripHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  actionStripLabel: {
    fontSize: 11,
    color: Colors.textMuted,
  },
  cancelEditBtnText: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.primary,
  },
  actionButtonsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
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
    fontSize: 11,
    fontWeight: '600',
  },
  recurrenceRow: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 4,
  },
  recurrenceOption: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 10,
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: Colors.neutralBorder,
    backgroundColor: '#F8FAFC',
  },
  recurrenceOptionActive: {
    borderColor: Colors.primary,
    backgroundColor: Colors.surfaceTintViolet,
  },
  recurrenceOptionText: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.textMuted,
  },
  recurrenceOptionTextActive: {
    color: Colors.primary,
    fontWeight: '700',
  },
  recurrenceHelperText: {
    fontSize: 11,
    color: Colors.textSubtle,
    fontStyle: 'italic',
    marginTop: 2,
    marginBottom: 4,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 24,
    gap: 12,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  modalTitle: {
    fontSize: 18,
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
  inputRow: {
    flexDirection: 'row',
  },
  modalSubmitBtn: {
    backgroundColor: Colors.primary,
    borderRadius: 16,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 12,
  },
  modalSubmitText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  sectionTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  countBadge: {
    backgroundColor: Colors.surfaceTintViolet,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  countBadgeText: {
    fontSize: 11,
    fontWeight: '700',
    color: Colors.primary,
  },
  checkinHistoryList: {
    gap: 10,
    marginBottom: 20,
  },
  checkinCard: {
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
  checkinCardTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  checkinTaskTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textStrong,
  },
  checkinTimeMeta: {
    fontSize: 12,
    color: Colors.textSubtle,
    marginTop: 2,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  statusBadgeText: {
    fontSize: 11,
    fontWeight: '600',
  },
  checkinMetricsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
    marginTop: 10,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: Colors.neutralBorder,
  },
  checkinMetricItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  checkinMetricText: {
    fontSize: 11,
    color: Colors.textSubtle,
  },
  checkinMetricValue: {
    fontWeight: '600',
    color: Colors.textStrong,
  },
  checkinNotesRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 6,
    backgroundColor: Colors.surfaceContainerLow,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  checkinNotesText: {
    fontSize: 11,
    color: Colors.textSubtle,
    fontStyle: 'italic',
    flex: 1,
  },
  emptyCheckinCard: {
    backgroundColor: Colors.neutralCard,
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: Colors.neutralBorder,
    borderStyle: 'dashed',
  },
  emptyCheckinTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textStrong,
    marginTop: 8,
  },
  emptyCheckinSubtitle: {
    fontSize: 12,
    color: Colors.textSubtle,
    textAlign: 'center',
    marginTop: 4,
    lineHeight: 16,
    paddingHorizontal: 16,
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
});
