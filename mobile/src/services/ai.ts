import { api } from './api';
import {
  AIExplanationRequest,
  AIExplanationResponse,
  ConversationResponse,
  MessageResponse,
} from '../types/chat';

export const aiService = {
  async explain(payload: AIExplanationRequest): Promise<AIExplanationResponse> {
    return api.post<AIExplanationResponse>('/api/v1/chat/explain', payload);
  },

  async createOrGetConversation(): Promise<ConversationResponse> {
    return api.post<ConversationResponse>('/api/v1/chat/conversations');
  },

  async getConversation(conversationId: string): Promise<ConversationResponse> {
    return api.get<ConversationResponse>(`/api/v1/chat/conversations/${conversationId}`);
  },

  async sendMessage(conversationId: string, content: string): Promise<MessageResponse> {
    return api.post<MessageResponse>(
      `/api/v1/chat/conversations/${conversationId}/messages`,
      { content }
    );
  },
};
