import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  SafeAreaView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Header } from '@/components/Header';
import { Colors } from '@/constants/theme';
import { aiService } from '@/services/ai';
import { ConversationResponse, MessageResponse, AIExplanationResponse } from '@/types/chat';

export default function AICoachScreen() {
  const params = useLocalSearchParams<{ initialPrompt?: string }>();
  const [conversation, setConversation] = useState<ConversationResponse | null>(null);
  const [messages, setMessages] = useState<MessageResponse[]>([]);
  const [inputText, setInputText] = useState(params.initialPrompt || '');
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [activeExplanation, setActiveExplanation] = useState<AIExplanationResponse | null>(null);

  const scrollRef = useRef<ScrollView | null>(null);

  useEffect(() => {
    async function loadConversation() {
      try {
        setIsLoadingHistory(true);
        const convo = await aiService.createOrGetConversation();
        setConversation(convo);
        setMessages(convo.messages || []);
      } catch (err: any) {
        Alert.alert('AI Companion Notice', err.message || 'Could not load conversation session.');
      } finally {
        setIsLoadingHistory(false);
      }
    }
    loadConversation();
  }, []);

  const handleSend = async () => {
    const textToSend = inputText.trim();
    if (!textToSend || !conversation || isSending) return;

    // Optimistic local user message
    const tempUserMsg: MessageResponse = {
      id: `temp-${Date.now()}`,
      conversation_id: conversation.id,
      sender: 'user',
      content: textToSend,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setInputText('');
    setIsSending(true);

    try {
      const assistantReply = await aiService.sendMessage(conversation.id, textToSend);
      setMessages((prev) => [...prev, assistantReply]);
      setTimeout(() => {
        scrollRef.current?.scrollToEnd({ animated: true });
      }, 100);
    } catch (err: any) {
      Alert.alert('AI Error', err.message || 'Could not get response from AI coach.');
    } finally {
      setIsSending(false);
    }
  };

  const handleExplain = async (question: string) => {
    try {
      setIsSending(true);
      const explanation = await aiService.explain({ question });
      setActiveExplanation(explanation);
    } catch (err: any) {
      Alert.alert('Explanation Error', err.message || 'Could not build behavioral explanation.');
    } finally {
      setIsSending(false);
    }
  };

  const handlePillSelect = (inquiryText: string) => {
    setInputText(inquiryText);
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <Header title="AI Coach" />

      <ScrollView
        ref={scrollRef}
        style={styles.container}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Top Context & Grounded Status Banner */}
        <View style={styles.privacyBanner}>
          <View style={styles.privacyHeaderRow}>
            <View style={styles.activeContextTag}>
              <View style={styles.greenPulse} />
              <Text style={styles.activeContextText}>Grounded AI Context</Text>
            </View>
            <View style={styles.privateTag}>
              <Ionicons name="shield-checkmark-outline" size={14} color={Colors.secondary} />
              <Text style={styles.privateTagText}>Deterministic Evidence</Text>
            </View>
          </View>
          <Text style={styles.privacySubText}>
            Every answer is constructed strictly from verified database records of your tasks, check-ins, and delay episodes.
          </Text>
        </View>

        {/* Structured Explanation Banner (if available) */}
        {activeExplanation && (
          <View style={styles.explanationCard}>
            <View style={styles.expHeaderRow}>
              <Ionicons name="sparkles" size={18} color={Colors.primary} />
              <Text style={styles.expTitle}>{activeExplanation.title}</Text>
              <TouchableOpacity onPress={() => setActiveExplanation(null)}>
                <Ionicons name="close" size={18} color={Colors.textMuted} />
              </TouchableOpacity>
            </View>
            <Text style={styles.expBody}>{activeExplanation.explanation}</Text>
            {activeExplanation.suggested_micro_experiment && (
              <View style={styles.microExpBox}>
                <Ionicons name="flask-outline" size={14} color={Colors.secondary} />
                <Text style={styles.microExpText}>
                  Micro-Experiment: {activeExplanation.suggested_micro_experiment}
                </Text>
              </View>
            )}
          </View>
        )}

        {/* Suggested Inquiries Scroll */}
        <View style={styles.suggestedContainer}>
          <View style={styles.suggestedHeaderRow}>
            <Text style={styles.suggestedLabel}>VERIFIED INQUIRIES</Text>
            <TouchableOpacity onPress={() => handleExplain('Analyze my recent focus patterns')}>
              <Text style={styles.realtimeText}>Request Deep Analysis</Text>
            </TouchableOpacity>
          </View>

          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.pillsScroll}
          >
            {[
              { label: 'Why am I delaying task initiation?', icon: 'flask-outline' },
              { label: 'Suggest a micro-start routine', icon: 'sunny-outline' },
              { label: 'What is my best focus window?', icon: 'time-outline' },
              { label: 'How to build momentum today?', icon: 'trending-up-outline' },
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
          {isLoadingHistory ? (
            <View style={styles.loadingBox}>
              <ActivityIndicator color={Colors.primary} size="small" />
              <Text style={styles.loadingText}>Restoring companion conversation...</Text>
            </View>
          ) : messages.length === 0 ? (
            <View style={styles.emptyChatBox}>
              <View style={styles.emptyChatIconCircle}>
                <Ionicons name="chatbubble-ellipses-outline" size={32} color={Colors.primary} />
              </View>
              <Text style={styles.emptyChatTitle}>FocusLoop AI Companion</Text>
              <Text style={styles.emptyChatSubtitle}>
                Ask questions or choose a suggested topic above. The companion retrieves your verified focus metrics before answering.
              </Text>
            </View>
          ) : (
            messages.map((msg) => (
              <View
                key={msg.id}
                style={
                  msg.sender === 'user'
                    ? styles.userBubbleWrapper
                    : styles.aiMessageWrapper
                }
              >
                {msg.sender === 'user' ? (
                  <>
                    <View style={styles.userBubble}>
                      <Text style={styles.userBubbleText}>{msg.content}</Text>
                    </View>
                    <View style={styles.userMetaRow}>
                      <Ionicons name="checkmark-done" size={14} color={Colors.primary} />
                    </View>
                  </>
                ) : (
                  <>
                    <View style={styles.aiAvatarCircle}>
                      <Ionicons name="hardware-chip-outline" size={18} color="#FFFFFF" />
                    </View>
                    <View style={styles.aiAnswerCard}>
                      <Text style={styles.aiAnswerBody}>{msg.content}</Text>
                    </View>
                  </>
                )}
              </View>
            ))
          )}

          {isSending && (
            <View style={styles.aiMessageWrapper}>
              <View style={styles.aiAvatarCircle}>
                <Ionicons name="hardware-chip-outline" size={18} color="#FFFFFF" />
              </View>
              <View style={[styles.aiAnswerCard, { paddingVertical: 12 }]}>
                <ActivityIndicator size="small" color={Colors.primary} />
                <Text style={{ fontSize: 11, color: Colors.textSubtle, marginTop: 4 }}>
                  Consulting behavioral context...
                </Text>
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
              onSubmitEditing={handleSend}
            />
            <TouchableOpacity
              style={[styles.sendBtn, (!inputText.trim() || isSending) && { opacity: 0.5 }]}
              onPress={handleSend}
              disabled={!inputText.trim() || isSending}
              activeOpacity={0.8}
            >
              <Ionicons name="arrow-up" size={18} color="#FFFFFF" />
            </TouchableOpacity>
          </View>
          <Text style={styles.inputFooterText}>
            🔒 Answers strictly grounded in your deterministic backend data.
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
    lineHeight: 16,
  },
  explanationCard: {
    backgroundColor: Colors.surfaceTintViolet,
    borderRadius: 16,
    padding: 14,
    marginBottom: 16,
    gap: 8,
  },
  expHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  expTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: Colors.primary,
    flex: 1,
    marginLeft: 6,
  },
  expBody: {
    fontSize: 12,
    color: Colors.textStrong,
    lineHeight: 18,
  },
  microExpBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#FFFFFF',
    padding: 8,
    borderRadius: 8,
    marginTop: 4,
  },
  microExpText: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.secondary,
    flex: 1,
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
    fontSize: 11,
    fontWeight: '600',
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
    minHeight: 200,
  },
  loadingBox: {
    padding: 30,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  loadingText: {
    fontSize: 12,
    color: Colors.textSubtle,
  },
  emptyChatBox: {
    backgroundColor: Colors.surfaceContainerLowest,
    borderRadius: 16,
    padding: 28,
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: 12,
    borderWidth: 1,
    borderColor: Colors.neutralBorder,
    borderStyle: 'dashed',
  },
  emptyChatIconCircle: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: Colors.surfaceTintViolet,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  emptyChatTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: Colors.textStrong,
    marginBottom: 6,
  },
  emptyChatSubtitle: {
    fontSize: 12,
    color: Colors.textSubtle,
    textAlign: 'center',
    lineHeight: 18,
    paddingHorizontal: 12,
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
  },
  aiAnswerBody: {
    fontSize: 13,
    color: Colors.textStrong,
    lineHeight: 20,
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
    fontSize: 13,
    color: Colors.textStrong,
    marginLeft: 8,
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
