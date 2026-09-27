import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  Animated,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '@/constants/theme';
import { useAuth } from '@/hooks/useAuth';
import { useOnboarding } from '@/hooks/useOnboarding';

const TOTAL_STEPS = 7;

const GOAL_CATEGORIES = [
  { id: 'Study consistently', label: 'Study consistently', icon: 'school-outline' },
  { id: 'Improve focus', label: 'Improve focus', icon: 'timer-outline' },
  { id: 'Manage time', label: 'Manage time', icon: 'alarm-outline' },
  { id: 'Build my career', label: 'Build my career', icon: 'briefcase-outline' },
  { id: 'Learn a skill', label: 'Learn a skill', icon: 'bulb-outline' },
  { id: 'Improve fitness', label: 'Improve fitness', icon: 'fitness-outline' },
  { id: 'Build a project', label: 'Build a project', icon: 'code-slash-outline' },
  { id: 'Build better routines', label: 'Build better routines', icon: 'repeat-outline' },
  { id: 'Other', label: 'Other', icon: 'sparkles-outline' },
];

const TIME_WINDOWS = ['Morning', 'Afternoon', 'Evening', 'Night', 'It changes'];

const DAILY_DURATIONS = [
  'Under 30 minutes',
  '30–60 minutes',
  '1–2 hours',
  '2–4 hours',
  '4+ hours',
];

const CHALLENGES_OPTIONS = [
  'Delaying tasks',
  'Phone/social media distraction',
  'Losing focus',
  'Inconsistent routine',
  'Poor planning',
  'Not knowing where to start',
  'Low energy',
  'Overthinking',
];

const INTERESTS_OPTIONS = [
  'Coding',
  'Reading',
  'Fitness',
  'Gaming',
  'Creative work',
  'Music',
  'Social activities',
];

export default function OnboardingScreen() {
  const router = useRouter();
  const { user, refreshUser } = useAuth();
  const { data, isLoading: isFetching, isSaving, saveStep, completeOnboarding } = useOnboarding();

  const [currentStep, setCurrentStep] = useState(1);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Form State
  const [name, setName] = useState('');
  const [ageRange, setAgeRange] = useState('');
  const [gender, setGender] = useState('');

  const [goalCategory, setGoalCategory] = useState('');
  const [goalDescription, setGoalDescription] = useState('');
  const [customGoalCategory, setCustomGoalCategory] = useState('');

  const [preferredTime, setPreferredTime] = useState('');
  const [dailyDuration, setDailyDuration] = useState('');

  const [selectedChallenges, setSelectedChallenges] = useState<string[]>([]);
  const [customChallenge, setCustomChallenge] = useState('');

  const [selectedInterests, setSelectedInterests] = useState<string[]>([]);
  const [customInterest, setCustomInterest] = useState('');

  // Fade animation between steps
  const fadeAnim = useRef(new Animated.Value(1)).current;

  // Initialize or resume from server state
  useEffect(() => {
    if (data) {
      if (data.name) setName(data.name);
      else if (user?.name) setName(user.name);

      if (data.age_range) setAgeRange(data.age_range);
      if (data.gender) setGender(data.gender);

      if (data.goal) {
        setGoalCategory(data.goal.category || '');
        setGoalDescription(data.goal.description || '');
      }

      if (data.routine) {
        if (data.routine.preferred_time_window) setPreferredTime(data.routine.preferred_time_window);
        if (data.routine.daily_available_duration) setDailyDuration(data.routine.daily_available_duration);
      }

      if (data.challenges && data.challenges.length > 0) {
        setSelectedChallenges(data.challenges.map((c) => c.challenge_text));
      }

      if (data.interests && data.interests.length > 0) {
        setSelectedInterests(data.interests.map((i) => i.interest_text));
      }

      // Resume step if available
      const savedStep = parseInt(data.onboarding_step, 10);
      if (!isNaN(savedStep) && savedStep >= 1 && savedStep <= TOTAL_STEPS) {
        setCurrentStep(savedStep);
      }
    } else if (user?.name) {
      setName(user.name);
    }
  }, [data, user]);

  const animateTransition = (callback: () => void) => {
    Animated.sequence([
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: 150,
        useNativeDriver: true,
      }),
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 200,
        useNativeDriver: true,
      }),
    ]).start();
    callback();
  };

  const handleNext = async () => {
    setErrorMessage(null);

    // Step-specific validations
    if (currentStep === 2) {
      if (!name.trim()) {
        setErrorMessage('Please enter your name.');
        return;
      }
      await saveStep({
        step: '3',
        name: name.trim(),
        age_range: ageRange || undefined,
        gender: gender || undefined,
      });
    } else if (currentStep === 3) {
      const activeCat = goalCategory === 'Other' ? customGoalCategory.trim() : goalCategory;
      if (!activeCat) {
        setErrorMessage('Please select or specify a goal category.');
        return;
      }
      if (!goalDescription.trim()) {
        setErrorMessage('Please briefly describe what you want to accomplish.');
        return;
      }
      await saveStep({
        step: '4',
        goal_category: activeCat,
        goal_description: goalDescription.trim(),
      });
    } else if (currentStep === 4) {
      if (!preferredTime) {
        setErrorMessage('Please select your preferred time window.');
        return;
      }
      if (!dailyDuration) {
        setErrorMessage('Please select your realistic daily availability.');
        return;
      }
      await saveStep({
        step: '5',
        preferred_time_window: preferredTime,
        daily_available_duration: dailyDuration,
      });
    } else if (currentStep === 5) {
      const challengesToSave = [...selectedChallenges];
      if (customChallenge.trim() && !challengesToSave.includes(customChallenge.trim())) {
        challengesToSave.push(customChallenge.trim());
      }
      if (challengesToSave.length === 0) {
        setErrorMessage('Please select at least one challenge or focus area.');
        return;
      }
      await saveStep({
        step: '6',
        challenges: challengesToSave,
      });
    } else if (currentStep === 6) {
      const interestsToSave = [...selectedInterests];
      if (customInterest.trim() && !interestsToSave.includes(customInterest.trim())) {
        interestsToSave.push(customInterest.trim());
      }
      await saveStep({
        step: '7',
        interests: interestsToSave,
      });
    }

    if (currentStep < TOTAL_STEPS) {
      animateTransition(() => setCurrentStep((prev) => prev + 1));
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      animateTransition(() => setCurrentStep((prev) => prev - 1));
    }
  };

  const handleFinish = async () => {
    try {
      setErrorMessage(null);
      const success = await completeOnboarding();
      if (success) {
        await refreshUser();
        router.replace('/(tabs)');
      } else {
        setErrorMessage('Unable to finalize onboarding. Please try again.');
      }
    } catch (err: any) {
      setErrorMessage(err?.message || 'Failed to complete onboarding');
    }
  };

  const toggleChallenge = (item: string) => {
    if (selectedChallenges.includes(item)) {
      setSelectedChallenges(selectedChallenges.filter((c) => c !== item));
    } else {
      setSelectedChallenges([...selectedChallenges, item]);
    }
  };

  const toggleInterest = (item: string) => {
    if (selectedInterests.includes(item)) {
      setSelectedInterests(selectedInterests.filter((i) => i !== item));
    } else {
      setSelectedInterests([...selectedInterests, item]);
    }
  };

  if (isFetching && !data) {
    return (
      <SafeAreaView style={styles.centerLoading}>
        <ActivityIndicator size="large" color={Colors.primary} />
        <Text style={styles.loadingText}>Loading your FocusLoop profile...</Text>
      </SafeAreaView>
    );
  }

  const effectiveCategory = goalCategory === 'Other' && customGoalCategory.trim()
    ? customGoalCategory.trim()
    : goalCategory;

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.flex}
      >
        {/* ── Top Header / Progress Indicator ── */}
        <View style={styles.header}>
          {currentStep > 1 ? (
            <TouchableOpacity onPress={handleBack} style={styles.backBtn} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
              <Ionicons name="arrow-back" size={24} color="#1A1848" />
            </TouchableOpacity>
          ) : (
            <View style={styles.brandIconRow}>
              <Ionicons name="infinite" size={22} color={Colors.primary} />
              <Text style={styles.brandText}>FOCUSLOOP</Text>
            </View>
          )}

          <View style={styles.stepBadge}>
            <Text style={styles.stepBadgeText}>Step {currentStep} of {TOTAL_STEPS}</Text>
          </View>
        </View>

        {/* ── Animated Progress Bar ── */}
        <View style={styles.progressBarTrack}>
          <View style={[styles.progressBarFill, { width: `${(currentStep / TOTAL_STEPS) * 100}%` }]} />
        </View>

        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          <Animated.View style={[styles.stepContainer, { opacity: fadeAnim }]}>
            {/* ── Error Banner ── */}
            {errorMessage && (
              <View style={styles.errorBox}>
                <Ionicons name="alert-circle" size={18} color="#DC2626" />
                <Text style={styles.errorText}>{errorMessage}</Text>
              </View>
            )}

            {/* ════════════════════════════════════════
                SCREEN 1 — WELCOME
            ════════════════════════════════════════ */}
            {currentStep === 1 && (
              <View style={styles.welcomeCard}>
                <View style={styles.welcomeIconCircle}>
                  <Ionicons name="sparkles" size={38} color={Colors.primary} />
                </View>
                <Text style={styles.title}>Welcome to FocusLoop 👋</Text>
                <Text style={styles.subtitle}>
                  Before we start, let's understand what you're working toward.
                </Text>
                <Text style={styles.bodyDescription}>
                  FocusLoop uses your starting context together with your real behavior over time to help you build focus and conquer distraction.
                </Text>

                <View style={styles.featurePill}>
                  <Ionicons name="shield-checkmark" size={18} color={Colors.primary} />
                  <Text style={styles.featurePillText}>Private, personalized, and grounded in evidence</Text>
                </View>

                <TouchableOpacity
                  style={styles.primaryBtn}
                  onPress={() => animateTransition(() => setCurrentStep(2))}
                  activeOpacity={0.85}
                >
                  <Text style={styles.primaryBtnText}>Let's Begin</Text>
                  <Ionicons name="arrow-forward" size={18} color="#FFFFFF" />
                </TouchableOpacity>
              </View>
            )}

            {/* ════════════════════════════════════════
                SCREEN 2 — BASIC PROFILE CONTEXT
            ════════════════════════════════════════ */}
            {currentStep === 2 && (
              <View style={styles.card}>
                <Text style={styles.title}>Basic Profile Context 👤</Text>
                <Text style={styles.subtitle}>
                  Tell us a bit about yourself. Only your name is required.
                </Text>

                <Text style={styles.fieldLabel}>Display / Full Name *</Text>
                <View style={styles.inputBox}>
                  <Ionicons name="person-outline" size={20} color="#9896B0" style={styles.inputIcon} />
                  <TextInput
                    style={styles.inputText}
                    placeholder="Your Name"
                    placeholderTextColor="#9896B0"
                    value={name}
                    onChangeText={setName}
                  />
                </View>

                <Text style={styles.fieldLabel}>Age Range (Optional)</Text>
                <View style={styles.chipsRow}>
                  {['Under 18', '18–24', '25–34', '35–44', '45+'].map((range) => {
                    const isSelected = ageRange === range;
                    return (
                      <TouchableOpacity
                        key={range}
                        style={[styles.chip, isSelected && styles.chipSelected]}
                        onPress={() => setAgeRange(isSelected ? '' : range)}
                        activeOpacity={0.7}
                      >
                        <Text style={[styles.chipText, isSelected && styles.chipTextSelected]}>
                          {range}
                        </Text>
                      </TouchableOpacity>
                    );
                  })}
                </View>

                <Text style={styles.fieldLabel}>Gender (Optional)</Text>
                <View style={styles.chipsRow}>
                  {['Female', 'Male', 'Non-binary', 'Prefer not to say'].map((gen) => {
                    const isSelected = gender === gen;
                    return (
                      <TouchableOpacity
                        key={gen}
                        style={[styles.chip, isSelected && styles.chipSelected]}
                        onPress={() => setGender(isSelected ? '' : gen)}
                        activeOpacity={0.7}
                      >
                        <Text style={[styles.chipText, isSelected && styles.chipTextSelected]}>
                          {gen}
                        </Text>
                      </TouchableOpacity>
                    );
                  })}
                </View>

                <View style={styles.privacyNoteBox}>
                  <Ionicons name="information-circle-outline" size={16} color="#64748B" />
                  <Text style={styles.privacyNoteText}>
                    Demographic context is strictly private and never used to calculate your behavior scores or levels.
                  </Text>
                </View>

                <TouchableOpacity
                  style={[styles.primaryBtn, isSaving && styles.btnDisabled]}
                  onPress={handleNext}
                  disabled={isSaving}
                  activeOpacity={0.85}
                >
                  {isSaving ? (
                    <ActivityIndicator color="#FFFFFF" size="small" />
                  ) : (
                    <>
                      <Text style={styles.primaryBtnText}>Continue</Text>
                      <Ionicons name="arrow-forward" size={18} color="#FFFFFF" />
                    </>
                  )}
                </TouchableOpacity>
              </View>
            )}

            {/* ════════════════════════════════════════
                SCREEN 3 — PRIMARY GOAL
            ════════════════════════════════════════ */}
            {currentStep === 3 && (
              <View style={styles.card}>
                <Text style={styles.title}>What's Your Main Focus? 🎯</Text>
                <Text style={styles.subtitle}>
                  What are you mainly trying to improve right now?
                </Text>

                <View style={styles.categoriesGrid}>
                  {GOAL_CATEGORIES.map((cat) => {
                    const isSelected = goalCategory === cat.id;
                    return (
                      <TouchableOpacity
                        key={cat.id}
                        style={[styles.categoryCard, isSelected && styles.categoryCardSelected]}
                        onPress={() => setGoalCategory(cat.id)}
                        activeOpacity={0.75}
                      >
                        <Ionicons
                          name={cat.icon as any}
                          size={22}
                          color={isSelected ? Colors.primary : '#64748B'}
                        />
                        <Text style={[styles.categoryText, isSelected && styles.categoryTextSelected]}>
                          {cat.label}
                        </Text>
                      </TouchableOpacity>
                    );
                  })}
                </View>

                {goalCategory === 'Other' && (
                  <View style={styles.inputBox}>
                    <Ionicons name="create-outline" size={20} color="#9896B0" style={styles.inputIcon} />
                    <TextInput
                      style={styles.inputText}
                      placeholder="Specify your goal category"
                      placeholderTextColor="#9896B0"
                      value={customGoalCategory}
                      onChangeText={setCustomGoalCategory}
                    />
                  </View>
                )}

                <Text style={[styles.fieldLabel, { marginTop: 14 }]}>
                  What specifically are you trying to accomplish? *
                </Text>
                <View style={[styles.inputBox, styles.inputBoxMulti]}>
                  <TextInput
                    style={[styles.inputText, styles.inputMultiText]}
                    placeholder="e.g., Prepare for final exams, build portfolio..."
                    placeholderTextColor="#9896B0"
                    value={goalDescription}
                    onChangeText={setGoalDescription}
                    multiline
                    numberOfLines={2}
                  />
                </View>

                <Text style={styles.helperText}>
                  You can update or change your active goal at any time inside FocusLoop.
                </Text>

                <TouchableOpacity
                  style={[styles.primaryBtn, isSaving && styles.btnDisabled]}
                  onPress={handleNext}
                  disabled={isSaving}
                  activeOpacity={0.85}
                >
                  {isSaving ? (
                    <ActivityIndicator color="#FFFFFF" size="small" />
                  ) : (
                    <>
                      <Text style={styles.primaryBtnText}>Continue</Text>
                      <Ionicons name="arrow-forward" size={18} color="#FFFFFF" />
                    </>
                  )}
                </TouchableOpacity>
              </View>
            )}

            {/* ════════════════════════════════════════
                SCREEN 4 — AVAILABLE TIME / ROUTINE
            ════════════════════════════════════════ */}
            {currentStep === 4 && (
              <View style={styles.card}>
                <Text style={styles.title}>Your Routine & Time ⏰</Text>
                <Text style={styles.subtitle}>
                  Lightweight context that helps FocusLoop interpret your actual daily rhythm.
                </Text>

                <Text style={styles.fieldLabel}>When do you usually have time for your goal?</Text>
                <View style={styles.chipsRow}>
                  {TIME_WINDOWS.map((window) => {
                    const isSelected = preferredTime === window;
                    return (
                      <TouchableOpacity
                        key={window}
                        style={[styles.chip, isSelected && styles.chipSelected]}
                        onPress={() => setPreferredTime(window)}
                        activeOpacity={0.7}
                      >
                        <Text style={[styles.chipText, isSelected && styles.chipTextSelected]}>
                          {window}
                        </Text>
                      </TouchableOpacity>
                    );
                  })}
                </View>

                <Text style={[styles.fieldLabel, { marginTop: 16 }]}>
                  How much time can you realistically give each day?
                </Text>
                <View style={styles.chipsRow}>
                  {DAILY_DURATIONS.map((dur) => {
                    const isSelected = dailyDuration === dur;
                    return (
                      <TouchableOpacity
                        key={dur}
                        style={[styles.chip, isSelected && styles.chipSelected]}
                        onPress={() => setDailyDuration(dur)}
                        activeOpacity={0.7}
                      >
                        <Text style={[styles.chipText, isSelected && styles.chipTextSelected]}>
                          {dur}
                        </Text>
                      </TouchableOpacity>
                    );
                  })}
                </View>

                <View style={styles.privacyNoteBox}>
                  <Ionicons name="hourglass-outline" size={16} color="#64748B" />
                  <Text style={styles.privacyNoteText}>
                    FocusLoop will compare intended time with actual measured behavior without forcing rigid schedules.
                  </Text>
                </View>

                <TouchableOpacity
                  style={[styles.primaryBtn, isSaving && styles.btnDisabled]}
                  onPress={handleNext}
                  disabled={isSaving}
                  activeOpacity={0.85}
                >
                  {isSaving ? (
                    <ActivityIndicator color="#FFFFFF" size="small" />
                  ) : (
                    <>
                      <Text style={styles.primaryBtnText}>Continue</Text>
                      <Ionicons name="arrow-forward" size={18} color="#FFFFFF" />
                    </>
                  )}
                </TouchableOpacity>
              </View>
            )}

            {/* ════════════════════════════════════════
                SCREEN 5 — SELF-REPORTED CHALLENGES
            ════════════════════════════════════════ */}
            {currentStep === 5 && (
              <View style={styles.card}>
                <Text style={styles.title}>Common Roadblocks 🚧</Text>
                <Text style={styles.subtitle}>
                  What usually gets in your way? (Select all that apply)
                </Text>

                <View style={styles.chipsRow}>
                  {CHALLENGES_OPTIONS.map((item) => {
                    const isSelected = selectedChallenges.includes(item);
                    return (
                      <TouchableOpacity
                        key={item}
                        style={[styles.chip, isSelected && styles.chipSelected]}
                        onPress={() => toggleChallenge(item)}
                        activeOpacity={0.7}
                      >
                        <Ionicons
                          name={isSelected ? 'checkmark-circle' : 'add-circle-outline'}
                          size={16}
                          color={isSelected ? Colors.primary : '#64748B'}
                          style={{ marginRight: 6 }}
                        />
                        <Text style={[styles.chipText, isSelected && styles.chipTextSelected]}>
                          {item}
                        </Text>
                      </TouchableOpacity>
                    );
                  })}
                </View>

                <Text style={[styles.fieldLabel, { marginTop: 12 }]}>Add another challenge (optional)</Text>
                <View style={styles.inputBox}>
                  <Ionicons name="create-outline" size={20} color="#9896B0" style={styles.inputIcon} />
                  <TextInput
                    style={styles.inputText}
                    placeholder="Custom challenge..."
                    placeholderTextColor="#9896B0"
                    value={customChallenge}
                    onChangeText={setCustomChallenge}
                  />
                </View>

                <View style={styles.privacyNoteBox}>
                  <Ionicons name="bookmark-outline" size={16} color="#64748B" />
                  <Text style={styles.privacyNoteText}>
                    Stored as self-reported starting areas. The AI Coach will compare them with real evidence over time.
                  </Text>
                </View>

                <TouchableOpacity
                  style={[styles.primaryBtn, isSaving && styles.btnDisabled]}
                  onPress={handleNext}
                  disabled={isSaving}
                  activeOpacity={0.85}
                >
                  {isSaving ? (
                    <ActivityIndicator color="#FFFFFF" size="small" />
                  ) : (
                    <>
                      <Text style={styles.primaryBtnText}>Continue</Text>
                      <Ionicons name="arrow-forward" size={18} color="#FFFFFF" />
                    </>
                  )}
                </TouchableOpacity>
              </View>
            )}

            {/* ════════════════════════════════════════
                SCREEN 6 — OPTIONAL INTERESTS / HOBBIES
            ════════════════════════════════════════ */}
            {currentStep === 6 && (
              <View style={styles.card}>
                <View style={styles.tagBadge}>
                  <Text style={styles.tagBadgeText}>OPTIONAL</Text>
                </View>
                <Text style={styles.title}>Hobbies & Interests 🎨</Text>
                <Text style={styles.subtitle}>
                  What activities matter to you outside your main goal?
                </Text>

                <View style={styles.chipsRow}>
                  {INTERESTS_OPTIONS.map((item) => {
                    const isSelected = selectedInterests.includes(item);
                    return (
                      <TouchableOpacity
                        key={item}
                        style={[styles.chip, isSelected && styles.chipSelected]}
                        onPress={() => toggleInterest(item)}
                        activeOpacity={0.7}
                      >
                        <Ionicons
                          name={isSelected ? 'heart' : 'heart-outline'}
                          size={16}
                          color={isSelected ? Colors.primary : '#64748B'}
                          style={{ marginRight: 6 }}
                        />
                        <Text style={[styles.chipText, isSelected && styles.chipTextSelected]}>
                          {item}
                        </Text>
                      </TouchableOpacity>
                    );
                  })}
                </View>

                <Text style={[styles.fieldLabel, { marginTop: 12 }]}>Add another interest</Text>
                <View style={styles.inputBox}>
                  <Ionicons name="add-outline" size={20} color="#9896B0" style={styles.inputIcon} />
                  <TextInput
                    style={styles.inputText}
                    placeholder="Custom hobby or passion..."
                    placeholderTextColor="#9896B0"
                    value={customInterest}
                    onChangeText={setCustomInterest}
                  />
                </View>

                <Text style={styles.helperText}>
                  Hobbies are strictly for personalization and helping the AI Coach understand your work-life balance.
                </Text>

                <TouchableOpacity
                  style={[styles.primaryBtn, isSaving && styles.btnDisabled]}
                  onPress={handleNext}
                  disabled={isSaving}
                  activeOpacity={0.85}
                >
                  {isSaving ? (
                    <ActivityIndicator color="#FFFFFF" size="small" />
                  ) : (
                    <>
                      <Text style={styles.primaryBtnText}>Review Summary</Text>
                      <Ionicons name="arrow-forward" size={18} color="#FFFFFF" />
                    </>
                  )}
                </TouchableOpacity>
              </View>
            )}

            {/* ════════════════════════════════════════
                SCREEN 7 — FINAL ONBOARDING SUMMARY
            ════════════════════════════════════════ */}
            {currentStep === 7 && (
              <View style={styles.card}>
                <View style={styles.summaryBadge}>
                  <Ionicons name="flag-outline" size={16} color={Colors.primary} />
                  <Text style={styles.summaryBadgeText}>Starting Blueprint</Text>
                </View>
                <Text style={styles.title}>Here's Your Starting Point 🌟</Text>
                <Text style={styles.subtitle}>
                  Everything is customizable anytime. FocusLoop will adapt as you build momentum.
                </Text>

                {/* Summary Table */}
                <View style={styles.summaryBox}>
                  <View style={styles.summaryItem}>
                    <Text style={styles.summaryLabel}>Primary Goal</Text>
                    <Text style={styles.summaryValue}>
                      {effectiveCategory || 'General Focus'}
                      {goalDescription ? ` — ${goalDescription}` : ''}
                    </Text>
                  </View>

                  <View style={styles.summaryDivider} />

                  <View style={styles.summaryItem}>
                    <Text style={styles.summaryLabel}>Preferred Window</Text>
                    <Text style={styles.summaryValue}>{preferredTime || 'Flexible'}</Text>
                  </View>

                  <View style={styles.summaryDivider} />

                  <View style={styles.summaryItem}>
                    <Text style={styles.summaryLabel}>Daily Availability</Text>
                    <Text style={styles.summaryValue}>{dailyDuration || '1–2 hours'}</Text>
                  </View>

                  {selectedChallenges.length > 0 && (
                    <>
                      <View style={styles.summaryDivider} />
                      <View style={styles.summaryItem}>
                        <Text style={styles.summaryLabel}>Self-Reported Focus Areas</Text>
                        <Text style={styles.summaryValue}>
                          {selectedChallenges.join(', ')}
                        </Text>
                      </View>
                    </>
                  )}

                  {selectedInterests.length > 0 && (
                    <>
                      <View style={styles.summaryDivider} />
                      <View style={styles.summaryItem}>
                        <Text style={styles.summaryLabel}>Interests & Passions</Text>
                        <Text style={styles.summaryValue}>
                          {selectedInterests.join(', ')}
                        </Text>
                      </View>
                    </>
                  )}
                </View>

                <Text style={styles.disclaimerText}>
                  Your starting point can evolve. FocusLoop will learn from what you actually do over time.
                </Text>

                <TouchableOpacity
                  style={[styles.primaryBtn, isSaving && styles.btnDisabled]}
                  onPress={handleFinish}
                  disabled={isSaving}
                  activeOpacity={0.85}
                >
                  {isSaving ? (
                    <ActivityIndicator color="#FFFFFF" size="small" />
                  ) : (
                    <>
                      <Ionicons name="rocket-outline" size={20} color="#FFFFFF" />
                      <Text style={styles.primaryBtnText}>Start FocusLoop</Text>
                    </>
                  )}
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.editBtn}
                  onPress={() => animateTransition(() => setCurrentStep(2))}
                  activeOpacity={0.7}
                >
                  <Text style={styles.editBtnText}>Edit Starting Details</Text>
                </TouchableOpacity>
              </View>
            )}
          </Animated.View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  safeArea: {
    flex: 1,
    backgroundColor: '#F3F1FB',
  },
  centerLoading: {
    flex: 1,
    backgroundColor: '#F3F1FB',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 14,
    color: '#64748B',
    fontWeight: '500',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: 8,
  },
  brandIconRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  brandText: {
    fontSize: 16,
    fontWeight: '800',
    color: Colors.primary,
    letterSpacing: 2,
  },
  backBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: '#E5E2F7',
  },
  stepBadge: {
    backgroundColor: '#EBE7FD',
    paddingVertical: 4,
    paddingHorizontal: 12,
    borderRadius: 12,
  },
  stepBadgeText: {
    fontSize: 12,
    fontWeight: '700',
    color: Colors.primary,
  },
  progressBarTrack: {
    width: '100%',
    height: 4,
    backgroundColor: '#E5E2F7',
  },
  progressBarFill: {
    height: 4,
    backgroundColor: Colors.primaryContainer,
    borderRadius: 2,
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 40,
  },
  stepContainer: {
    width: '100%',
  },
  welcomeCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    padding: 24,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E5E2F7',
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.08,
    shadowRadius: 16,
    elevation: 3,
  },
  welcomeIconCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#EDE9FE',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    padding: 22,
    borderWidth: 1,
    borderColor: '#E5E2F7',
    shadowColor: '#1A1848',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.06,
    shadowRadius: 14,
    elevation: 3,
  },
  title: {
    fontSize: 22,
    fontWeight: '800',
    color: '#1A1848',
    marginBottom: 6,
  },
  subtitle: {
    fontSize: 14,
    color: '#64748B',
    marginBottom: 18,
    lineHeight: 20,
  },
  bodyDescription: {
    fontSize: 14,
    color: '#464555',
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 20,
    paddingHorizontal: 8,
  },
  featurePill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#F5F3FF',
    borderWidth: 1,
    borderColor: '#DDD6FE',
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 16,
    marginBottom: 28,
  },
  featurePillText: {
    fontSize: 13,
    color: Colors.primary,
    fontWeight: '600',
  },
  fieldLabel: {
    fontSize: 14,
    fontWeight: '700',
    color: '#1A1848',
    marginBottom: 8,
  },
  helperText: {
    fontSize: 12,
    color: '#94A3B8',
    marginTop: 6,
    marginBottom: 16,
    lineHeight: 16,
  },
  inputBox: {
    width: '100%',
    height: 52,
    backgroundColor: '#F5F3FF',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#E5E2F7',
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    marginBottom: 14,
  },
  inputBoxMulti: {
    height: 72,
    alignItems: 'flex-start',
    paddingVertical: 10,
  },
  inputIcon: {
    marginRight: 10,
  },
  inputText: {
    flex: 1,
    fontSize: 15,
    color: '#1A1848',
  },
  inputMultiText: {
    textAlignVertical: 'top',
  },
  chipsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 16,
  },
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F5F3FF',
    paddingVertical: 9,
    paddingHorizontal: 14,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#E5E2F7',
  },
  chipSelected: {
    backgroundColor: '#EDE9FE',
    borderColor: '#8B5CF6',
  },
  chipText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#464555',
  },
  chipTextSelected: {
    color: Colors.primary,
    fontWeight: '700',
  },
  categoriesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    marginBottom: 14,
  },
  categoryCard: {
    width: '48%',
    backgroundColor: '#F5F3FF',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#E5E2F7',
    padding: 14,
    alignItems: 'center',
    gap: 8,
  },
  categoryCardSelected: {
    backgroundColor: '#EDE9FE',
    borderColor: '#8B5CF6',
  },
  categoryText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#464555',
    textAlign: 'center',
  },
  categoryTextSelected: {
    color: Colors.primary,
    fontWeight: '700',
  },
  tagBadge: {
    alignSelf: 'flex-start',
    backgroundColor: '#EDE9FE',
    paddingVertical: 3,
    paddingHorizontal: 8,
    borderRadius: 8,
    marginBottom: 8,
  },
  tagBadgeText: {
    fontSize: 10,
    fontWeight: '800',
    color: Colors.primary,
    letterSpacing: 0.5,
  },
  privacyNoteBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    padding: 12,
    borderRadius: 12,
    marginBottom: 20,
  },
  privacyNoteText: {
    flex: 1,
    fontSize: 12,
    color: '#64748B',
    lineHeight: 17,
  },
  summaryBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    alignSelf: 'flex-start',
    backgroundColor: '#EDE9FE',
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: 10,
    marginBottom: 10,
  },
  summaryBadgeText: {
    fontSize: 12,
    fontWeight: '700',
    color: Colors.primary,
  },
  summaryBox: {
    backgroundColor: '#F8FAFC',
    borderRadius: 18,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    padding: 16,
    marginBottom: 16,
  },
  summaryItem: {
    paddingVertical: 6,
  },
  summaryLabel: {
    fontSize: 12,
    color: '#94A3B8',
    fontWeight: '600',
    marginBottom: 3,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  summaryValue: {
    fontSize: 14,
    fontWeight: '700',
    color: '#1A1848',
    lineHeight: 20,
  },
  summaryDivider: {
    height: 1,
    backgroundColor: '#E2E8F0',
    marginVertical: 6,
  },
  disclaimerText: {
    fontSize: 13,
    color: '#64748B',
    textAlign: 'center',
    marginBottom: 20,
    lineHeight: 18,
    fontStyle: 'italic',
  },
  primaryBtn: {
    width: '100%',
    height: 52,
    backgroundColor: Colors.primaryContainer,
    borderRadius: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    shadowColor: Colors.primaryContainer,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.3,
    shadowRadius: 10,
    elevation: 4,
  },
  btnDisabled: {
    opacity: 0.65,
  },
  primaryBtnText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  editBtn: {
    width: '100%',
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 8,
  },
  editBtnText: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.primaryContainer,
  },
  errorBox: {
    width: '100%',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: '#FEE2E2',
    borderWidth: 1,
    borderColor: '#FCA5A5',
    borderRadius: 14,
    paddingVertical: 10,
    paddingHorizontal: 14,
    marginBottom: 14,
  },
  errorText: {
    flex: 1,
    fontSize: 13,
    color: '#B91C1C',
    fontWeight: '500',
  },
});
