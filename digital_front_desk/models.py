from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

class ChannelType(str, Enum):
    PHONE = "phone"
    CHAT = "chat"
    WEB_PORTAL = "web_portal"

class PatientInfo(BaseModel):
    user_id: str
    age: Optional[int] = None
    sex: Optional[str] = None
    previous_conditions: Optional[List[str]] = []
    allergies: Optional[List[str]] = []
    medications: Optional[List[str]] = []
    contact_info: Optional[dict] = {}

class ChannelInput(BaseModel):
    channel_type: ChannelType
    message: str
    user_id: str
    timestamp: datetime = datetime.now()
    patient_info: Optional[PatientInfo] = None

class AgentResponse(BaseModel):
    response: str
    triage_score: float
    confidence_score: float
    suggested_actions: List[str]
    esi_level: Optional[int] = None
    expected_resources: Optional[List[str]] = []
    vital_signs_concerns: Optional[List[str]] = []

class ESILevel(int, Enum):
    """
    Emergency Severity Index (ESI) triage levels:
    LEVEL_1: Immediate life-saving intervention required
    LEVEL_2: High-risk situation or severe pain/distress
    LEVEL_3: Multiple resources needed, stable condition
    LEVEL_4: One resource needed
    LEVEL_5: No resources needed, lowest urgency
    """
    LEVEL_1 = 1  # Immediate life-saving intervention
    LEVEL_2 = 2  # High-risk situation, severe pain
    LEVEL_3 = 3  # Multiple resources needed
    LEVEL_4 = 4  # One resource needed
    LEVEL_5 = 5  # No resources needed

class UrgencyLevel(int, Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class ResourceType(str, Enum):
    """Types of resources that may be needed during an ED visit"""
    LAB_TEST = "lab_test"
    IMAGING = "imaging"
    IV_FLUIDS = "iv_fluids"
    MEDICATION = "medication"
    SPECIALIST_CONSULT = "specialist_consult"
    PROCEDURE = "procedure"
    NONE = "none"

class TriageResult(BaseModel):
    urgency_level: UrgencyLevel
    esi_level: ESILevel
    recommended_action: str
    reasoning: str
    requires_human_attention: bool
    expected_resources: List[ResourceType] = []
    vital_signs_concerns: List[str] = []

class ConversationContext(BaseModel):
    user_id: str
    conversation_history: List[dict]
    last_updated: datetime = datetime.now()
    metadata: dict = {}
    patient_info: Optional[PatientInfo] = None

class QueueItem(BaseModel):
    user_id: str
    urgency_level: UrgencyLevel
    esi_level: ESILevel
    timestamp: datetime = datetime.now()
    channel_type: ChannelType
    context_summary: str
    patient_info: Optional[PatientInfo] = None 