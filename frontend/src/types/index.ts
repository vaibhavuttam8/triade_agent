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

export interface PatientInfo {
  user_id: string;
  age?: number;
  sex?: string;
  previous_conditions?: string[];
  allergies?: string[];
  medications?: string[];
  contact_info?: {
    email?: string;
    phone?: string;
    address?: string;
  };
}

export interface ChatResponse {
  response: string;
  triage_result: {
    urgency_level: string;
    recommended_action: string;
    requires_human_attention: boolean;
    critical_keywords_detected?: string[];
  };
  suggested_actions: string[];
}

export interface ChatRequest {
  channel_type: 'phone' | 'chat' | 'web_portal';
  message: string;
  user_id: string;
  patient_info?: PatientInfo;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user_id: string;
}

export interface RegisterResponse {
  message: string;
  user_id: string;
}

export interface AuthState {
  isAuthenticated: boolean;
  token: string | null;
  user_id: string | null;
  patientInfo: PatientInfo | null;
} 