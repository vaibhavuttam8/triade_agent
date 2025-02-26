export interface Message {
  type: 'user' | 'assistant';
  content: string;
  suggestedActions?: string[];  // Add optional suggested actions for assistant messages
  triageResult?: {
    urgencyLevel: string;
    recommendedAction: string;
    requiresHumanAttention: boolean;
  };
}

export interface ChatResponse {
  response: string;
  triage_result: {
    urgency_level: string;
    recommended_action: string;
    requires_human_attention: boolean;
  };
  suggested_actions: string[];
}

export interface ChatRequest {
  channel_type: 'phone' | 'chat' | 'web_portal';
  message: string;
  user_id: string;
} 