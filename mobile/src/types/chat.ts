export interface MessageCreate {
  content: string;
}

export interface MessageResponse {
  id: string;
  conversation_id: string;
  sender: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export interface ConversationResponse {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: MessageResponse[];
}

export interface AIExplanationRequest {
  pattern_id?: string | null;
  question?: string | null;
}

export interface AIExplanationResponse {
  title: string;
  explanation: string;
  deterministic_context: Record<string, any>;
  suggested_micro_experiment?: string | null;
  tone: string;
}
