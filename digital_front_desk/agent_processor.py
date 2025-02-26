from .models import ChannelInput, AgentResponse, TriageResult, QueueItem
from .telemetry import telemetry
from .triage import triage_engine
from .queue_manager import queue_manager
from .context_manager import context_manager
import openai
import time
import json
from typing import Tuple
import os
from dotenv import load_dotenv
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

load_dotenv()

class AgentProcessor:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4-turbo-preview"  # Can be configured based on needs
        
        # System prompt for the AI agent
        self.system_prompt = """You are a medical front desk AI assistant. Your role is to:
1. Gather relevant information from patients
2. Assess the urgency of their situation
3. Provide immediate guidance for non-urgent cases
4. Escalate urgent cases to human medical staff
5. Maintain a professional and empathetic tone

Always err on the side of caution when assessing medical situations."""

    async def process_input(self, channel_input: ChannelInput) -> Tuple[AgentResponse, TriageResult]:
        with telemetry.tracer.start_as_current_span("process_input") as span:
            start_time = time.time()
            
            try:
                # Get conversation context
                context = context_manager.get_context(channel_input.user_id)
                
                # Update context with user input
                context_manager.update_context(
                    user_id=channel_input.user_id,
                    channel_input=channel_input
                )
                
                # Prepare conversation history for the AI
                messages = [
                    {"role": "system", "content": self.system_prompt}
                ]
                
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
                    suggested_actions=response["suggested_actions"]
                )
                
                # Update context with agent response
                context_manager.update_context(
                    user_id=channel_input.user_id,
                    agent_response=agent_response
                )
                
                # Process through triage engine
                triage_result = triage_engine.process(agent_response)
                
                # Add to queue if needed
                if triage_result.requires_human_attention:
                    queue_item = QueueItem(
                        user_id=channel_input.user_id,
                        urgency_level=triage_result.urgency_level,
                        channel_type=channel_input.channel_type,
                        context_summary=context_manager.get_context_summary(channel_input.user_id)
                    )
                    queue_manager.add_to_queue(queue_item)
                
                # Record metrics
                processing_time = (time.time() - start_time) * 1000
                telemetry.record_response_time(processing_time, "agent_processor")
                
                span.set_attributes({
                    "processor.triage_score": agent_response.triage_score,
                    "processor.confidence_score": agent_response.confidence_score,
                    "processor.urgency_level": triage_result.urgency_level.value,
                    "processor.requires_human": triage_result.requires_human_attention,
                    "processor.processing_time_ms": processing_time
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
                        "description": "Process a medical inquiry and provide structured response",
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
                                "confidence": {
                                    "type": "number",
                                    "description": "Confidence in the assessment from 0-1"
                                },
                                "suggested_actions": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of suggested actions"
                                }
                            },
                            "required": ["content", "triage_score", "confidence", "suggested_actions"]
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