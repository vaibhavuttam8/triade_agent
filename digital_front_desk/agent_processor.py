from .models import ChannelInput, AgentResponse, TriageResult, QueueItem, ESILevel, ResourceType
from .telemetry import telemetry
from .triage import triage_engine
from .queue_manager import queue_manager
from .context_manager import context_manager
from .pdf_knowledge_base import pdf_knowledge_base
import openai
import time
import json
from typing import Tuple, List
import os
from dotenv import load_dotenv
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from datetime import datetime

load_dotenv()

class AgentProcessor:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"  
        
        # Enhanced system prompt with ESI triage algorithm
        self.system_prompt = """You are a medical front desk AI assistant. Your role is to:
1. Gather relevant information from patients
2. Assess the urgency of their situation using the Emergency Severity Index (ESI)
3. Provide immediate guidance for non-urgent cases
4. Escalate urgent cases to human medical staff
5. Maintain a professional and empathetic tone

You must follow the Emergency Severity Index (ESI) triage algorithm:

ESI LEVEL 1: Immediate life-saving intervention required.
- Examples: Cardiac/respiratory arrest, severe respiratory distress, unconsciousness, severe shock
- Action: Immediate escalation to emergency response team

ESI LEVEL 2: High-risk situation or severe pain/distress.
- Examples: Chest pain, difficulty breathing, altered mental status, severe pain, stroke symptoms
- Action: Priority routing to available healthcare provider

ESI LEVEL 3: Multiple resources needed but stable condition.
- Examples: Abdominal pain requiring labs and imaging, fractures needing x-rays and procedures
- Action: Schedule urgent consultation

ESI LEVEL 4: One resource needed.
- Examples: Simple laceration requiring sutures, sprain needing x-ray, medication prescription
- Action: Schedule non-urgent appointment

ESI LEVEL 5: No resources needed, lowest urgency.
- Examples: Minor cold symptoms, simple rash, medication refill with no complications
- Action: Provide self-care instructions and resources

Assessment guidelines:
1. First identify immediate life-threatening conditions (Level 1) or high-risk situations (Level 2)
2. For stable patients, predict required resources to determine Levels 3-5:
   - Labs, imaging, IV fluids, medications, procedures, specialty consultations count as resources
3. Consider vital signs (can up-triage if concerning)
4. Make special considerations for pediatric patients

When gathering information, ask specific questions to:
- Identify immediately life-threatening conditions
- Assess for high-risk situations
- Predict resource requirements
- Check vital signs indirectly through descriptions
- Understand illness timeline and progression

Always err on the side of caution when assessing medical situations."""

    async def process_input(self, channel_input: ChannelInput) -> Tuple[AgentResponse, TriageResult]:
        with telemetry.tracer.start_as_current_span("process_input") as span:
            start_time = time.time()
            
            try:
                # Get conversation context
                context = await context_manager.get_context(channel_input.user_id)
                
                # Update context with user input
                new_history = [
                    *(context.conversation_history if context else []),
                    {
                        "role": "user",
                        "content": channel_input.message,
                        "timestamp": datetime.now()
                    }
                ]
                await context_manager.create_or_update_context(
                    user_id=channel_input.user_id,
                    conversation_history=new_history
                )
                
                # Retrieve relevant ESI guidelines for the patient's symptoms
                esi_guidelines_context = ""
                if pdf_knowledge_base.loaded:
                    esi_guidelines_context = await pdf_knowledge_base.get_context_for_symptoms(channel_input.message)
                
                # Prepare conversation history for the AI
                messages = [
                    {"role": "system", "content": self.system_prompt}
                ]
                
                # Add relevant ESI guidelines if available
                if esi_guidelines_context:
                    messages.append({
                        "role": "system", 
                        "content": f"Reference the following specific ESI guidelines when assessing this patient:\n\n{esi_guidelines_context}"
                    })
                
                # Add relevant conversation history
                for msg in context.conversation_history[-5:]:  # Last 5 messages
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
                
                # Get AI response
                response = self._get_ai_response(messages)
                
                # Create agent response
                agent_response = AgentResponse(
                    response=response["content"],
                    triage_score=response["triage_score"],
                    confidence_score=response["confidence"],
                    suggested_actions=response["suggested_actions"],
                    esi_level=response.get("esi_level"),
                    expected_resources=response.get("expected_resources", []),
                    vital_signs_concerns=response.get("vital_signs_concerns", [])
                )
                
                # Update context with agent response
                new_history = [
                    *(context.conversation_history if context else []),
                    {
                        "role": "assistant",
                        "content": agent_response.response,
                        "timestamp": datetime.now()
                    }
                ]
                await context_manager.create_or_update_context(
                    user_id=channel_input.user_id,
                    conversation_history=new_history
                )
                
                # Process through triage engine
                triage_result = triage_engine.process(agent_response)
                
                # Add to queue if needed
                if triage_result.requires_human_attention:
                    queue_item = QueueItem(
                        user_id=channel_input.user_id,
                        urgency_level=triage_result.urgency_level,
                        esi_level=triage_result.esi_level,
                        channel_type=channel_input.channel_type,
                        context_summary=await context_manager.get_context_summary(channel_input.user_id)
                    )
                    queue_manager.add_to_queue(queue_item)
                
                # Record metrics
                processing_time = (time.time() - start_time) * 1000
                telemetry.record_response_time(processing_time, "agent_processor")
                
                span.set_attributes({
                    "processor.triage_score": agent_response.triage_score,
                    "processor.confidence_score": agent_response.confidence_score,
                    "processor.urgency_level": triage_result.urgency_level.value,
                    "processor.esi_level": triage_result.esi_level.value,
                    "processor.requires_human": triage_result.requires_human_attention,
                    "processor.processing_time_ms": processing_time,
                    "processor.used_knowledge_base": bool(esi_guidelines_context)
                })
                
                return agent_response, triage_result
                
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise

    def _get_ai_response(self, messages: list) -> dict:
        """Get response from OpenAI API with structured output"""
        with telemetry.tracer.start_as_current_span("ai_request") as span:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    functions=[{
                        "name": "process_medical_inquiry",
                        "description": "Process a medical inquiry and provide structured response with ESI triage",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "content": {
                                    "type": "string",
                                    "description": "The response message to the user"
                                },
                                "triage_score": {
                                    "type": "number",
                                    "description": "Urgency score from 0-1"
                                },
                                "esi_level": {
                                    "type": "integer",
                                    "enum": [1, 2, 3, 4, 5],
                                    "description": "ESI triage level (1=most urgent, 5=least urgent)"
                                },
                                "confidence": {
                                    "type": "number",
                                    "description": "Confidence in the assessment from 0-1"
                                },
                                "suggested_actions": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of suggested actions"
                                },
                                "expected_resources": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of expected resources needed (lab_test, imaging, iv_fluids, medication, specialist_consult, procedure, none)"
                                },
                                "vital_signs_concerns": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of vital sign concerns if any"
                                }
                            },
                            "required": ["content", "triage_score", "esi_level", "confidence", "suggested_actions"]
                        }
                    }],
                    function_call={"name": "process_medical_inquiry"}
                )
                
                # Parse the function call response
                function_args = response.choices[0].message.function_call.arguments
                function_response = json.loads(function_args)
                
                span.set_attributes({
                    "ai.model": self.model,
                    "ai.response_tokens": response.usage.total_tokens
                })
                
                return function_response
                
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise

# Global instance
agent_processor = AgentProcessor() 