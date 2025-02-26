from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .models import ChannelInput, AgentResponse, TriageResult, UrgencyLevel
from .agent_processor import agent_processor
from .queue_manager import queue_manager
from .context_manager import context_manager
from .telemetry import telemetry
from .critical_keywords import detect_critical_keywords
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
import time
from typing import Dict, Any

app = FastAPI(
    title="Digital Front Desk & Triage Agent",
    description="AI-powered medical front desk system for patient triage and routing",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app's URL
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.post("/inquiries", response_model=Dict[str, Any])
async def process_inquiry(channel_input: ChannelInput):
    """Process a new patient inquiry"""
    with telemetry.tracer.start_as_current_span("http_process_inquiry") as span:
        try:
            start_time = time.time()
            
            # Check for critical keywords
            critical_keywords = detect_critical_keywords(channel_input.message)
            
            try:
                # Try to process through agent
                agent_response, triage_result = await agent_processor.process_input(channel_input)
            except Exception as agent_error:
                # Fallback response if agent processing fails
                if critical_keywords:
                    # Create a basic response for critical conditions
                    triage_result = TriageResult(
                        urgency_level=UrgencyLevel.CRITICAL,
                        recommended_action="Immediate medical attention required",
                        reasoning="Critical keywords detected in message",
                        requires_human_attention=True
                    )
                    agent_response = AgentResponse(
                        response="I've detected potentially serious symptoms in your message. Please seek immediate medical attention or call emergency services.",
                        triage_score=1.0,
                        confidence_score=1.0,
                        suggested_actions=["Seek immediate medical attention", "Call emergency services"]
                    )
                else:
                    # Re-raise the error if no critical keywords
                    raise agent_error
            
            # If critical keywords were found, ensure high urgency
            if critical_keywords:
                triage_result.urgency_level = UrgencyLevel.CRITICAL
                triage_result.requires_human_attention = True
            
            # Record request processing time
            processing_time = (time.time() - start_time) * 1000
            telemetry.record_response_time(processing_time, "http_request")
            
            span.set_attributes({
                "http.status_code": 200,
                "http.processing_time_ms": processing_time,
                "critical_keywords_found": len(critical_keywords) > 0
            })
            
            return {
                "response": agent_response.response,
                "triage_result": {
                    "urgency_level": triage_result.urgency_level.name,
                    "recommended_action": triage_result.recommended_action,
                    "requires_human_attention": triage_result.requires_human_attention,
                    "critical_keywords_detected": critical_keywords if critical_keywords else []
                },
                "suggested_actions": agent_response.suggested_actions
            }
            
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/queue/status")
async def get_queue_status():
    """Get current queue status"""
    with telemetry.tracer.start_as_current_span("http_queue_status") as span:
        try:
            status = queue_manager.get_queue_status()
            span.set_attributes({"http.status_code": 200})
            return status
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/context/{user_id}")
async def get_user_context(user_id: str):
    """Get conversation context for a user"""
    with telemetry.tracer.start_as_current_span("http_get_context") as span:
        try:
            context = context_manager.get_context(user_id)
            span.set_attributes({
                "http.status_code": 200,
                "context.user_id": user_id
            })
            return {
                "user_id": context.user_id,
                "conversation_length": len(context.conversation_history),
                "last_updated": context.last_updated,
                "summary": context_manager.get_context_summary(user_id)
            }
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/queue/next")
async def get_next_queue_item():
    """Get the next item from the queue"""
    with telemetry.tracer.start_as_current_span("http_queue_next") as span:
        try:
            item = queue_manager.get_next_item()
            if item:
                span.set_attributes({
                    "http.status_code": 200,
                    "queue.item_found": True,
                    "queue.urgency_level": item.urgency_level.value
                })
                return {
                    "user_id": item.user_id,
                    "urgency_level": item.urgency_level.name,
                    "wait_time": (time.time() - item.timestamp.timestamp()),
                    "channel_type": item.channel_type,
                    "context_summary": item.context_summary
                }
            else:
                span.set_attributes({
                    "http.status_code": 404,
                    "queue.item_found": False
                })
                raise HTTPException(status_code=404, detail="No items in queue")
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise HTTPException(status_code=500, detail=str(e))

@app.delete("/queue/{user_id}")
async def remove_from_queue(user_id: str):
    """Remove a user from the queue"""
    with telemetry.tracer.start_as_current_span("http_queue_remove") as span:
        try:
            queue_manager.remove_from_queue(user_id)
            span.set_attributes({
                "http.status_code": 200,
                "queue.user_id": user_id
            })
            return {"status": "success", "message": f"User {user_id} removed from queue"}
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(channel_input: ChannelInput):
    """Process a chat message"""
    with telemetry.tracer.start_as_current_span("http_chat") as span:
        try:
            start_time = time.time()
            
            # Process the input through our agent
            agent_response, _ = await agent_processor.process_input(channel_input)
            
            # Record request processing time
            processing_time = (time.time() - start_time) * 1000
            telemetry.record_response_time(processing_time, "chat_request")
            
            span.set_attributes({
                "http.status_code": 200,
                "http.processing_time_ms": processing_time
            })
            
            return {
                "response": agent_response.response
            }
            
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise HTTPException(status_code=500, detail=str(e)) 