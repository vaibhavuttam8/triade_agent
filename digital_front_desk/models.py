from pydantic import BaseModel
from typing import List
from datetime import datetime
from enum import Enum

class ChannelType(str, Enum):
    PHONE = "phone"
    CHAT = "chat"
    WEB_PORTAL = "web_portal"

class ChannelInput(BaseModel):
    channel_type: ChannelType
    message: str
    user_id: str
    timestamp: datetime = datetime.now()

class AgentResponse(BaseModel):
    response: str
    triage_score: float
    confidence_score: float
    suggested_actions: List[str]

class UrgencyLevel(int, Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class TriageResult(BaseModel):
    urgency_level: UrgencyLevel
    recommended_action: str
    reasoning: str
    requires_human_attention: bool

class ConversationContext(BaseModel):
    user_id: str
    conversation_history: List[dict]
    last_updated: datetime = datetime.now()
    metadata: dict = {}

class QueueItem(BaseModel):
    user_id: str
    urgency_level: UrgencyLevel
    timestamp: datetime = datetime.now()
    channel_type: ChannelType
    context_summary: str 