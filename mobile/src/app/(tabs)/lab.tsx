import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Header } from '@/components/Header';
import { Colors } from '@/constants/theme';
import { useExperiments } from '@/hooks/useExperiments';
import { ExperimentResultResponse } from '@/types/experiments';

export default function LabScreen() {
  const {
    experiments,
    isLoading,
    error,
    refreshExperiments,
    suggestExperiment,
    startExperiment,
    evaluateExperiment,
  } = useExperiments();

  const [isSuggesting, setIsSuggesting] = useState(false);
  const [startingId, setStartingId] = useState<string | null>(null);
  const [evaluatingId, setEvaluatingId] = useState<string | null>(null);
  const [latestEvaluation, setLatestEvaluation] = useState<ExperimentResultResponse | null>(null);

  const activeExperiment = experiments.find((exp) => exp.status === 'active') || null;

  const handleSuggest = async () => {
    try {
      setIsSuggesting(true);
      const updatedList = await suggestExperiment();
      const newest = updatedList && updatedList.length > 0 ? updatedList[0] : null;
      Alert.alert(
        'Protocol Generated',
        newest?.title
          ? `"${newest.title}" created based on your behavior patterns.`
          : 'New protocol suggestions generated based on your behavior patterns.'
      );
    } catch (err: any) {
      Alert.alert('Suggestion Notice', err.message || 'Could not generate experiment suggestion.');
    } finally {
      setIsSuggesting(false);
    }
  };

  const handleStart = async (id: string) => {
    try {
      setStartingId(id);
      await startExperiment(id);
      Alert.alert('Protocol Activated', 'Protocol is now active. Track your task check-ins during the observation window.');
    } catch (err: any) {
      Alert.alert('Activation Notice', err.message || 'Could not activate protocol.');
    } finally {
      setStartingId(null);
    }
  };

  const handleEvaluate = async (id: string) => {
    try {
      setEvaluatingId(id);
      const result = await evaluateExperiment(id);
      setLatestEvaluation(result);
      Alert.alert('Protocol Evaluated', result.result_summary || 'Evaluation completed successfully.');
    } catch (err: any) {
      Alert.alert('Evaluation Notice', err.message || 'Could not evaluate protocol.');
    } finally {
      setEvaluatingId(null);
    }
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
            <View
              style={[
                styles.runningBadge,
                !activeExperiment && { backgroundColor: Colors.surfaceContainer },
              ]}
            >
              <Text
                style={[
                  styles.runningText,
                  !activeExperiment && { color: Colors.textSubtle },
                ]}
              >
                {activeExperiment ? `Status: ${(activeExperiment.status || 'active').toUpperCase()}` : 'No Active Protocol'}
              </Text>
            </View>
            <View style={styles.labTag}>
              <Text style={styles.labTagText}>Lab</Text>
            </View>
          </View>

          {isLoading ? (
            <View style={styles.loadingBox}>
              <ActivityIndicator color={Colors.primary} size="small" />
              <Text style={styles.loadingText}>Loading protocol experiments...</Text>
            </View>
          ) : activeExperiment ? (
            <>
              <Text style={styles.heroTitle}>{activeExperiment.title}</Text>
              <Text style={styles.heroSub}>{activeExperiment.description}</Text>

              {/* Hypothesis Box */}
              <View style={styles.hypothesisBox}>
                <View style={styles.boxHeaderRow}>
                  <Ionicons name="bulb-outline" size={14} color={Colors.primary} />
                  <Text style={styles.boxHeaderText}>CORE HYPOTHESIS</Text>
                </View>
                <Text style={styles.hypothesisText}>{activeExperiment.hypothesis}</Text>
              </View>

              {/* Target Metric Box */}
              <View style={styles.triggerBox}>
                <Ionicons name="flash-outline" size={16} color={Colors.tertiary} />
                <View style={{ flex: 1 }}>
                  <Text style={styles.triggerTag}>TARGET METRIC</Text>
                  <Text style={styles.triggerText}>
                    {activeExperiment.target_metric}: Target {activeExperiment.target_value ?? '—'} (Baseline: {activeExperiment.baseline_value ?? '—'})
                  </Text>
                </View>
              </View>

              {/* Evaluate Button */}
              <TouchableOpacity
                style={styles.evaluateBtn}
                onPress={() => handleEvaluate(activeExperiment.id)}
                disabled={evaluatingId === activeExperiment.id}
              >
                {evaluatingId === activeExperiment.id ? (
                  <ActivityIndicator color="#FFFFFF" size="small" />
                ) : (
                  <>
                    <Ionicons name="analytics" size={16} color="#FFFFFF" />
                    <Text style={styles.evaluateBtnText}>Evaluate Protocol Outcome</Text>
                  </>
                )}
              </TouchableOpacity>
            </>
          ) : (
            <>
              <Text style={styles.heroTitle}>No Active Experiment</Text>
              <Text style={styles.heroSub}>
                Ask the FocusLoop engine to suggest an evidence-based intervention from your behavior patterns.
              </Text>

              <TouchableOpacity
                style={styles.suggestBtn}
                onPress={handleSuggest}
                disabled={isSuggesting}
              >
                {isSuggesting ? (
                  <ActivityIndicator color="#FFFFFF" size="small" />
                ) : (
                  <>
                    <Ionicons name="sparkles" size={16} color="#FFFFFF" />
                    <Text style={styles.suggestBtnText}>Suggest Behavioral Protocol</Text>
                  </>
                )}
              </TouchableOpacity>
            </>
          )}
        </View>

        {/* Latest Evaluation Result */}
        {latestEvaluation && (
          <View style={styles.evaluationCard}>
            <View style={styles.evalHeaderRow}>
              <View style={styles.evalIconBox}>
                <Ionicons name="ribbon-outline" size={18} color={Colors.secondary} />
              </View>
              <Text style={styles.evalTitle}>Latest Evaluation Result</Text>
            </View>
            <Text style={styles.evalSummary}>{latestEvaluation.result_summary}</Text>
            <View style={styles.evalMetricsRow}>
              <View style={styles.evalMetricTile}>
                <Text style={styles.evalMetricLabel}>Before</Text>
                <Text style={styles.evalMetricVal}>{latestEvaluation.before_value}</Text>
              </View>
              <View style={styles.evalMetricTile}>
                <Text style={styles.evalMetricLabel}>After</Text>
                <Text style={styles.evalMetricVal}>{latestEvaluation.after_value}</Text>
              </View>
              <View style={styles.evalMetricTile}>
                <Text style={styles.evalMetricLabel}>Change</Text>
                <Text style={[styles.evalMetricVal, { color: Colors.secondary }]}>
                  {latestEvaluation.percent_change != null ? `${latestEvaluation.percent_change.toFixed(1)}%` : `${latestEvaluation.change_value}`}
                </Text>
              </View>
            </View>
            <Text style={styles.evalConclusion}>Conclusion: {latestEvaluation.conclusion}</Text>
          </View>
        )}

        {/* Empirical Results / All Protocols Section */}
        <View style={styles.sectionHeader}>
          <View style={styles.sectionTitleRow}>
            <Ionicons name="analytics-outline" size={18} color={Colors.primary} />
            <Text style={styles.sectionTitle}>Behavioral Protocols ({experiments.length})</Text>
          </View>
          <TouchableOpacity onPress={handleSuggest} disabled={isSuggesting}>
            <Text style={styles.linkText}>+ New Suggestion</Text>
          </TouchableOpacity>
        </View>

        {experiments.length === 0 ? (
          <View style={styles.emptyCard}>
            <Ionicons name="flask-outline" size={28} color={Colors.textMuted} />
            <Text style={styles.emptyTitle}>No Protocols Generated Yet</Text>
            <Text style={styles.emptySubtitle}>
              Tap "Suggest Behavioral Protocol" above to let the backend generate an experiment from your logged sessions.
            </Text>
          </View>
        ) : (
          <View style={styles.experimentList}>
            {experiments.map((exp) => (
              <View key={exp.id} style={styles.expCard}>
                <View style={styles.expCardTop}>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.expItemTitle}>{exp.title}</Text>
                    <Text style={styles.expItemType}>
                      {exp.intervention_type} • Started: {exp.start_date}
                    </Text>
                  </View>
                  <View
                    style={[
                      styles.statusPill,
                      exp.status === 'completed' && { backgroundColor: Colors.surfaceTintMint },
                      exp.status === 'active' && { backgroundColor: Colors.secondaryFixed },
                    ]}
                  >
                    <Text
                      style={[
                        styles.statusPillText,
                        exp.status === 'completed' && { color: Colors.secondary, fontWeight: '700' },
                        exp.status === 'active' && { color: Colors.onSecondaryFixed, fontWeight: '700' },
                      ]}
                    >
                      {(exp.status || 'unknown').toUpperCase()}
                    </Text>
                  </View>
                </View>
                <Text style={styles.expItemDesc}>{exp.description}</Text>

                {/* If results exist */}
                {exp.results && exp.results.length > 0 && (
                  <View style={styles.expResultSnippet}>
                    <Ionicons name="checkmark-done" size={14} color={Colors.secondary} />
                    <Text style={styles.expResultText}>
                      {exp.results[0].conclusion.toUpperCase()}: {exp.results[0].metric_name} (
                      {exp.results[0].change_value != null ? `Change: ${exp.results[0].change_value}` : 'No change data'})
                    </Text>
                  </View>
                )}

                {/* Actions based on experiment status */}
                {exp.status === 'suggested' && (
                  <TouchableOpacity
                    style={styles.startBtn}
                    onPress={() => handleStart(exp.id)}
                    disabled={startingId === exp.id}
                  >
                    {startingId === exp.id ? (
                      <ActivityIndicator color="#FFFFFF" size="small" />
                    ) : (
                      <>
                        <Ionicons name="play" size={12} color="#FFFFFF" />
                        <Text style={styles.startBtnText}>Start Protocol</Text>
                      </>
                    )}
                  </TouchableOpacity>
                )}

                {exp.status === 'active' && (
                  <TouchableOpacity
                    style={styles.smallEvalBtn}
                    onPress={() => handleEvaluate(exp.id)}
                    disabled={evaluatingId === exp.id}
                  >
                    {evaluatingId === exp.id ? (
                      <ActivityIndicator color={Colors.primary} size="small" />
                    ) : (
                      <>
                        <Ionicons name="analytics" size={12} color={Colors.primary} />
                        <Text style={styles.smallEvalText}>Evaluate</Text>
                      </>
                    )}
                  </TouchableOpacity>
                )}
              </View>
            ))}
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
    marginTop: 4,
    lineHeight: 18,
  },
  hypothesisBox: {
    backgroundColor: Colors.surfaceContainerLow,
    borderRadius: 12,
    padding: 12,
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
    lineHeight: 18,
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
  evaluateBtn: {
    backgroundColor: Colors.primary,
    borderRadius: 14,
    paddingVertical: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 14,
  },
  evaluateBtnText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  suggestBtn: {
    backgroundColor: Colors.primaryContainer,
    borderRadius: 14,
    paddingVertical: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 14,
  },
  suggestBtnText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  evaluationCard: {
    backgroundColor: Colors.surfaceTintMint,
    borderRadius: 16,
    padding: 14,
    marginBottom: 20,
    gap: 8,
  },
  evalHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  evalIconBox: {
    width: 28,
    height: 28,
    borderRadius: 8,
    backgroundColor: Colors.neutralCard,
    alignItems: 'center',
    justifyContent: 'center',
  },
  evalTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: Colors.secondary,
  },
  evalSummary: {
    fontSize: 12,
    color: Colors.textStrong,
    lineHeight: 16,
  },
  evalMetricsRow: {
    flexDirection: 'row',
    gap: 8,
    marginVertical: 4,
  },
  evalMetricTile: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    padding: 8,
    alignItems: 'center',
  },
  evalMetricLabel: {
    fontSize: 10,
    color: Colors.textSubtle,
  },
  evalMetricVal: {
    fontSize: 14,
    fontWeight: '700',
    color: Colors.textStrong,
    marginTop: 2,
  },
  evalConclusion: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.secondary,
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
  linkText: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.primary,
  },
  emptyCard: {
    backgroundColor: Colors.neutralCard,
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: Colors.neutralBorder,
    borderStyle: 'dashed',
    gap: 8,
  },
  emptyTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textStrong,
  },
  emptySubtitle: {
    fontSize: 12,
    color: Colors.textSubtle,
    textAlign: 'center',
    lineHeight: 16,
    paddingHorizontal: 16,
  },
  experimentList: {
    gap: 10,
  },
  expCard: {
    backgroundColor: Colors.neutralCard,
    borderRadius: 14,
    padding: 14,
    gap: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 1,
  },
  expCardTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  expItemTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textStrong,
  },
  expItemType: {
    fontSize: 10,
    color: Colors.textSubtle,
    marginTop: 2,
  },
  statusPill: {
    backgroundColor: Colors.surfaceContainer,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
  },
  statusPillText: {
    fontSize: 10,
    fontWeight: '600',
    color: Colors.textSubtle,
  },
  expItemDesc: {
    fontSize: 12,
    color: Colors.textSubtle,
    lineHeight: 16,
  },
  expResultSnippet: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: Colors.surfaceTintMint,
    borderRadius: 8,
    padding: 8,
  },
  expResultText: {
    fontSize: 11,
    color: Colors.secondary,
    fontWeight: '500',
  },
  startBtn: {
    alignSelf: 'flex-start',
    backgroundColor: Colors.secondary,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 4,
  },
  startBtnText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  smallEvalBtn: {
    alignSelf: 'flex-start',
    backgroundColor: Colors.primaryFixed,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 4,
  },
  smallEvalText: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.primary,
  },
  loadingBox: {
    padding: 20,
    alignItems: 'center',
    gap: 8,
  },
  loadingText: {
    fontSize: 12,
    color: Colors.textSubtle,
  },
});
