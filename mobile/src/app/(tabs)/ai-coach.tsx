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
import { Ionicons } from '@expo/vector-icons';
import { Header } from '@/components/Header';
import { Colors } from '@/constants/theme';

export default function AICoachScreen() {
  const [inputText, setInputText] = useState('');
  const [isRuleApplied, setIsRuleApplied] = useState(false);
  const [isRuleDismissed, setIsRuleDismissed] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: '1',
      sender: 'user',
      text: 'Why did you recommend the 10-Minute Micro-Start Buffer experiment for afternoon sprints?',
      time: '2:15 PM',
    },
  ]);

  const handleSend = () => {
    if (!inputText.trim()) return;
    const userMsg = {
      id: Date.now().toString(),
      sender: 'user',
      text: inputText,
      time: 'Just now',
    };
    setMessages((prev) => [...prev, userMsg]);
    setInputText('');
  };

  const handlePillSelect = (inquiryText: string) => {
    setInputText(inquiryText);
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <Header title="AI Coach" />

      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Top Context & Privacy Pill Banner */}
        <View style={styles.privacyBanner}>
          <View style={styles.privacyHeaderRow}>
            <View style={styles.activeContextTag}>
              <View style={styles.greenPulse} />
              <Text style={styles.activeContextText}>AI Context Active • 182 Local Data Points</Text>
            </View>
            <View style={styles.privateTag}>
              <Ionicons name="shield-checkmark-outline" size={14} color={Colors.secondary} />
              <Text style={styles.privateTagText}>Local & Private</Text>
            </View>
          </View>
          <Text style={styles.privacySubText}>
            Grounded in your real task, screen, and sleep telemetry. Zero generic fluff.
          </Text>
        </View>

        {/* Horizontal Suggested Inquiries Scroll */}
        <View style={styles.suggestedContainer}>
          <View style={styles.suggestedHeaderRow}>
            <Text style={styles.suggestedLabel}>SUGGESTED INQUIRIES</Text>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
              <Ionicons name="flash-outline" size={12} color={Colors.primary} />
              <Text style={styles.realtimeText}>Real-time Sync</Text>
            </View>
          </View>

          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.pillsScroll}
          >
            {[
              { label: 'Why was 10m Micro-Start recommended?', icon: 'flask-outline' },
              { label: 'When is my best focus window?', icon: 'sunny-outline' },
              { label: 'How does my sleep affect my start delay?', icon: 'moon-outline' },
              { label: 'Show my 30-day completion trend', icon: 'trending-up-outline' },
            ].map((item, idx) => (
              <TouchableOpacity
                key={idx}
                style={styles.inquiryPill}
                onPress={() => handlePillSelect(item.label)}
                activeOpacity={0.8}
              >
                <Ionicons name={item.icon as any} size={14} color={Colors.primary} />
                <Text style={styles.inquiryPillText}>{item.label}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>

        {/* Conversational Feed */}
        <View style={styles.chatFeed}>
          {messages.map((msg) => (
            <View key={msg.id} style={styles.userBubbleWrapper}>
              <View style={styles.userBubble}>
                <Text style={styles.userBubbleText}>{msg.text}</Text>
              </View>
              <View style={styles.userMetaRow}>
                <Text style={styles.metaTime}>{msg.time}</Text>
                <Ionicons name="checkmark-done" size={14} color={Colors.primary} />
              </View>
            </View>
          ))}

          {/* AI Coach Answer Card */}
          <View style={styles.aiMessageWrapper}>
            <View style={styles.aiAvatarCircle}>
              <Ionicons name="hardware-chip-outline" size={18} color={Colors.onPrimaryContainer} />
            </View>

            <View style={styles.aiAnswerCard}>
              <View style={styles.cardHeaderRow}>
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                  <Text style={styles.engineTitle}>Behavioral Engine</Text>
                  <View style={styles.blueDot} />
                  <Text style={styles.engineVer}>v2.4 Grounded</Text>
                </View>
                <Text style={styles.metaTime}>Just now</Text>
              </View>

              <Text style={styles.aiAnswerBody}>
                Based on your verified activity over the last 14 days, I isolated a recurring{' '}
                <Text style={styles.coralText}>38-minute start delay</Text> specifically on{' '}
                <Text style={styles.boldText}>High-Difficulty tasks</Text> scheduled between 1:30 PM and 3:30 PM.
              </Text>

              {/* Supporting Evidence Box */}
              <View style={styles.evidenceBox}>
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
                  <Ionicons name="search-outline" size={14} color={Colors.primary} />
                  <Text style={styles.evidenceTitle}>SUPPORTING EVIDENCE</Text>
                </View>
                <View style={styles.evidenceItem}>
                  <View style={styles.coralBullet} />
                  <Text style={styles.evidenceText}>
                    <Text style={styles.boldText}>Sleep Correlation:</Text> On days with {'<'}6h sleep, afternoon delay lengthened by <Text style={styles.coralText}>+49 minutes</Text>.
                  </Text>
                </View>
                <View style={styles.evidenceItem}>
                  <View style={styles.coralBullet} />
                  <Text style={styles.evidenceText}>
                    <Text style={styles.boldText}>App Context:</Text> 16m YouTube and 6m Twitter were logged during verified hesitation windows.
                  </Text>
                </View>
              </View>

              {/* Result So Far Box */}
              <View style={styles.resultBox}>
                <View style={styles.resultHeaderRow}>
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                    <Ionicons name="checkmark-circle-outline" size={16} color={Colors.secondary} />
                    <Text style={styles.resultTitle}>Result so far (Day 4 of 7)</Text>
                  </View>
                  <View style={styles.pBadge}>
                    <Text style={styles.pBadgeText}>p = 0.03</Text>
                  </View>
                </View>
                <Text style={styles.resultBody}>
                  By committing to just 10 low-stakes minutes, your observed latency dropped from 38m down to{' '}
                  <Text style={styles.secondaryBold}>16m</Text> (<Text style={styles.secondaryBold}>-57% latency reduction</Text>).
                </Text>

                {/* Inline Comparison Latency Bar */}
                <View style={styles.comparisonBars}>
                  <View style={styles.barLabelRow}>
                    <Text style={styles.barLabelText}>Baseline Hesitation</Text>
                    <Text style={styles.barLabelVal}>38 min</Text>
                  </View>
                  <View style={styles.barTrack}>
                    <View style={[styles.barFill, { width: '78%', backgroundColor: Colors.accentCoral }]} />
                  </View>

                  <View style={[styles.barLabelRow, { marginTop: 6 }]}>
                    <Text style={styles.barLabelText}>Protocol #04 Sprint</Text>
                    <Text style={[styles.barLabelVal, { color: Colors.secondary }]}>16 min (-57%)</Text>
                  </View>
                  <View style={styles.barTrack}>
                    <View style={[styles.barFill, { width: '33%', backgroundColor: Colors.secondary }]} />
                  </View>
                </View>
              </View>

              {/* Deep-dive Action CTA Buttons */}
              <View style={styles.ctaButtonsRow}>
                <TouchableOpacity style={styles.ctaBtnViolet}>
                  <Ionicons name="book-outline" size={14} color={Colors.primary} />
                  <Text style={styles.ctaBtnVioletText}>View Protocol Spec</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.ctaBtnContainer}>
                  <Ionicons name="list-outline" size={14} color={Colors.textStrong} />
                  <Text style={styles.ctaBtnContainerText}>Inspect 14 Episodes</Text>
                </TouchableOpacity>
              </View>

              {/* Feedback footer */}
              <View style={styles.feedbackRow}>
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
                  <Ionicons name="lock-closed" size={12} color={Colors.textMuted} />
                  <Text style={styles.feedbackText}>Calculated on device</Text>
                </View>
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                  <Text style={styles.feedbackText}>Helpful?</Text>
                  <TouchableOpacity style={styles.thumbBtn}>
                    <Ionicons name="thumbs-up-outline" size={12} color={Colors.textSubtle} />
                  </TouchableOpacity>
                  <TouchableOpacity style={styles.thumbBtn}>
                    <Ionicons name="thumbs-down-outline" size={12} color={Colors.textSubtle} />
                  </TouchableOpacity>
                </View>
              </View>
            </View>
          </View>

          {/* Interactive Dynamic Rule proposal card */}
          {!isRuleDismissed && (
            <View style={[styles.ruleProposalCard, isRuleApplied && { opacity: 0.8 }]}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                <Ionicons name="options-outline" size={16} color={Colors.accentIndigo} />
                <Text style={styles.ruleHeader}>Autonomous Routine Tuning</Text>
              </View>
              <Text style={styles.ruleBody}>
                <Text style={{ fontWeight: '700' }}>Adaptive Sleep Rule:</Text> Extend buffer delay threshold to 25m on well-rested days ({'>'}7.5h sleep)?
              </Text>

              <View style={styles.ruleBtnRow}>
                <TouchableOpacity
                  style={[styles.applyRuleBtn, isRuleApplied && { backgroundColor: Colors.secondary }]}
                  onPress={() => setIsRuleApplied(true)}
                >
                  <Ionicons name="checkmark-circle" size={16} color={Colors.onPrimary} />
                  <Text style={styles.applyRuleBtnText}>
                    {isRuleApplied ? 'Applied to Protocol #04' : 'Apply Dynamic Rule'}
                  </Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.dismissBtn}
                  onPress={() => setIsRuleDismissed(true)}
                >
                  <Text style={styles.dismissBtnText}>Dismiss</Text>
                </TouchableOpacity>
              </View>
            </View>
          )}
        </View>

        {/* Input Bar */}
        <View style={styles.inputBarContainer}>
          <View style={styles.inputInner}>
            <Ionicons name="sparkles" size={18} color={Colors.primary} />
            <TextInput
              style={styles.textInput}
              placeholder="Ask about patterns, habits, or focus..."
              placeholderTextColor={Colors.textMuted}
              value={inputText}
              onChangeText={setInputText}
            />
            <TouchableOpacity style={styles.micBtn}>
              <Ionicons name="mic-outline" size={18} color={Colors.textSubtle} />
            </TouchableOpacity>
            <TouchableOpacity style={styles.sendBtn} onPress={handleSend} activeOpacity={0.8}>
              <Ionicons name="arrow-up" size={18} color={Colors.onPrimaryContainer} />
            </TouchableOpacity>
          </View>
          <Text style={styles.inputFooterText}>
            🔒 Answers strictly grounded in your deterministic local data.
          </Text>
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
  privacyBanner: {
    backgroundColor: Colors.surfaceContainerLowest,
    borderRadius: 16,
    padding: 14,
    marginBottom: 16,
    shadowColor: '#64748B',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.06,
    shadowRadius: 10,
    elevation: 2,
  },
  privacyHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  activeContextTag: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.surfaceTintMint,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    gap: 6,
  },
  greenPulse: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: Colors.secondary,
  },
  activeContextText: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.secondary,
  },
  privateTag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  privateTagText: {
    fontSize: 10,
    fontWeight: '600',
    color: Colors.secondary,
  },
  privacySubText: {
    fontSize: 11,
    color: Colors.textSubtle,
    marginTop: 6,
  },
  suggestedContainer: {
    marginBottom: 16,
  },
  suggestedHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  suggestedLabel: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.textSubtle,
    letterSpacing: 0.5,
  },
  realtimeText: {
    fontSize: 10,
    fontWeight: '500',
    color: Colors.primary,
  },
  pillsScroll: {
    flexDirection: 'row',
    gap: 8,
  },
  inquiryPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.surfaceContainerLowest,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    gap: 6,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.03,
    shadowRadius: 6,
    elevation: 1,
  },
  inquiryPillText: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.onSurface,
  },
  chatFeed: {
    gap: 16,
    marginBottom: 16,
  },
  userBubbleWrapper: {
    alignItems: 'flex-end',
    paddingLeft: 32,
  },
  userBubble: {
    backgroundColor: Colors.surfaceTintViolet,
    padding: 14,
    borderRadius: 16,
    borderTopRightRadius: 4,
    shadowColor: Colors.primaryContainer,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 2,
  },
  userBubbleText: {
    fontSize: 13,
    color: Colors.textStrong,
    lineHeight: 18,
  },
  userMetaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 4,
    marginRight: 4,
  },
  metaTime: {
    fontSize: 10,
    color: Colors.textMuted,
  },
  aiMessageWrapper: {
    flexDirection: 'row',
    gap: 10,
  },
  aiAvatarCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.primaryContainer,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 2,
  },
  aiAnswerCard: {
    flex: 1,
    backgroundColor: Colors.surfaceContainerLowest,
    borderRadius: 16,
    borderTopLeftRadius: 4,
    padding: 14,
    shadowColor: '#64748B',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.08,
    shadowRadius: 12,
    elevation: 3,
    gap: 12,
  },
  cardHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  engineTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: Colors.primary,
  },
  blueDot: {
    width: 4,
    height: 4,
    borderRadius: 2,
    backgroundColor: Colors.primaryContainer,
  },
  engineVer: {
    fontSize: 10,
    color: Colors.textMuted,
  },
  aiAnswerBody: {
    fontSize: 13,
    color: Colors.textStrong,
    lineHeight: 20,
  },
  coralText: {
    fontWeight: '700',
    color: Colors.accentCoral,
  },
  boldText: {
    fontWeight: '700',
    color: Colors.textStrong,
  },
  secondaryBold: {
    fontWeight: '700',
    color: Colors.secondary,
  },
  evidenceBox: {
    backgroundColor: Colors.surfaceContainerLow,
    borderRadius: 12,
    padding: 10,
    gap: 6,
  },
  evidenceTitle: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.primary,
    letterSpacing: 0.5,
  },
  evidenceItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 6,
  },
  coralBullet: {
    width: 4,
    height: 4,
    borderRadius: 2,
    backgroundColor: Colors.accentCoral,
    marginTop: 6,
  },
  evidenceText: {
    fontSize: 11,
    color: Colors.onSurfaceVariant,
    lineHeight: 16,
    flex: 1,
  },
  resultBox: {
    backgroundColor: Colors.surfaceTintMint,
    borderRadius: 12,
    padding: 10,
    gap: 8,
  },
  resultHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  resultTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.onSecondaryFixedVariant,
  },
  pBadge: {
    backgroundColor: Colors.secondaryFixed,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  pBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.onSecondaryFixed,
  },
  resultBody: {
    fontSize: 11,
    color: Colors.onSecondaryFixedVariant,
    lineHeight: 16,
  },
  comparisonBars: {
    gap: 4,
    marginTop: 4,
  },
  barLabelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  barLabelText: {
    fontSize: 10,
    color: Colors.onSecondaryFixedVariant,
  },
  barLabelVal: {
    fontSize: 10,
    fontWeight: '600',
    color: Colors.onSecondaryFixedVariant,
  },
  barTrack: {
    height: 8,
    borderRadius: 4,
    backgroundColor: Colors.surfaceContainerHighest,
    overflow: 'hidden',
  },
  barFill: {
    height: '100%',
    borderRadius: 4,
  },
  ctaButtonsRow: {
    flexDirection: 'row',
    gap: 8,
  },
  ctaBtnViolet: {
    flex: 1,
    backgroundColor: Colors.surfaceTintViolet,
    paddingVertical: 8,
    borderRadius: 20,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
  },
  ctaBtnVioletText: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.primary,
  },
  ctaBtnContainer: {
    flex: 1,
    backgroundColor: Colors.surfaceContainer,
    paddingVertical: 8,
    borderRadius: 20,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
  },
  ctaBtnContainerText: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.textStrong,
  },
  feedbackRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 4,
  },
  feedbackText: {
    fontSize: 10,
    color: Colors.textMuted,
  },
  thumbBtn: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: Colors.surfaceContainerLow,
    alignItems: 'center',
    justifyContent: 'center',
  },
  ruleProposalCard: {
    marginLeft: 46,
    backgroundColor: Colors.surfaceTintBlue,
    borderRadius: 12,
    padding: 12,
    gap: 8,
  },
  ruleHeader: {
    fontSize: 12,
    fontWeight: '700',
    color: Colors.accentIndigo,
  },
  ruleBody: {
    fontSize: 12,
    color: Colors.textStrong,
    lineHeight: 16,
  },
  ruleBtnRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 4,
  },
  applyRuleBtn: {
    flex: 1,
    backgroundColor: Colors.primary,
    paddingVertical: 8,
    borderRadius: 20,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  applyRuleBtnText: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.onPrimary,
  },
  dismissBtn: {
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  dismissBtnText: {
    fontSize: 11,
    color: Colors.textSubtle,
  },
  inputBarContainer: {
    marginTop: 12,
  },
  inputInner: {
    backgroundColor: Colors.surfaceContainerLowest,
    borderRadius: 24,
    paddingHorizontal: 14,
    paddingVertical: 6,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: Colors.primaryContainer,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.1,
    shadowRadius: 14,
    elevation: 3,
  },
  textInput: {
    flex: 1,
    fontSize: 12,
    color: Colors.textStrong,
    marginLeft: 8,
  },
  micBtn: {
    padding: 6,
  },
  sendBtn: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: Colors.primaryContainer,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 4,
  },
  inputFooterText: {
    fontSize: 10,
    color: Colors.textMuted,
    textAlign: 'center',
    marginTop: 8,
  },
});
