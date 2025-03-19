from .models import ConversationContext, ChannelInput, AgentResponse, PatientInfo
from .telemetry import telemetry
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import asyncio
import json
import time

# In-memory store for conversation contexts
# In a production environment, this would be a database
contexts: Dict[str, ConversationContext] = {}

class ContextManager:
    def __init__(self):
        self.context_ttl = timedelta(hours=24)  # Context time-to-live

    async def get_context(self, user_id: str) -> Optional[ConversationContext]:
        """Retrieve the conversation context for a user"""
        with telemetry.tracer.start_as_current_span("get_context") as span:
            span.set_attributes({"user.id": user_id})
            
            if user_id in contexts:
                return contexts[user_id]
            return None
    
    async def create_or_update_context(
        self, 
        user_id: str, 
        conversation_history: List[dict], 
        metadata: dict = {},
        patient_info: Optional[PatientInfo] = None
    ) -> ConversationContext:
        """Create or update the conversation context for a user"""
        with telemetry.tracer.start_as_current_span("update_context") as span:
            start_time = time.time()
            
            span.set_attributes({
                "user.id": user_id,
                "context.history_length": len(conversation_history)
            })
            
            # Check if the context already exists
            if user_id in contexts:
                # Update existing context
                contexts[user_id].conversation_history = conversation_history
                contexts[user_id].last_updated = datetime.now()
                contexts[user_id].metadata.update(metadata)
                if patient_info:
                    contexts[user_id].patient_info = patient_info
            else:
                # Create new context
                contexts[user_id] = ConversationContext(
                    user_id=user_id,
                    conversation_history=conversation_history,
                    metadata=metadata,
                    patient_info=patient_info
                )
            
            # Record update time
            telemetry.record_response_time(
                (time.time() - start_time) * 1000,
                "context_update"
            )
            
            return contexts[user_id]
    
    async def append_to_history(self, user_id: str, message: dict) -> None:
        """Append a new message to the conversation history"""
        with telemetry.tracer.start_as_current_span("append_history") as span:
            span.set_attributes({
                "user.id": user_id,
                "message.role": message.get("role", "unknown")
            })
            
            # Get the current context
            context = await self.get_context(user_id)
            
            if not context:
                # Create a new context if it doesn't exist
                context = await self.create_or_update_context(user_id, [])
            
            # Append the message
            context.conversation_history.append(message)
            context.last_updated = datetime.now()
            
            # Limit history size
            if len(context.conversation_history) > 20:
                context.conversation_history = context.conversation_history[-20:]
            
            # No need to call create_or_update_context as we've modified the object in-place
    
    async def clear_context(self, user_id: str) -> None:
        """Clear the conversation context for a user"""
        with telemetry.tracer.start_as_current_span("clear_context") as span:
            span.set_attributes({"user.id": user_id})
            
            if user_id in contexts:
                # Preserve patient info when clearing context
                patient_info = contexts[user_id].patient_info
                contexts[user_id] = ConversationContext(
                    user_id=user_id,
                    conversation_history=[],
                    patient_info=patient_info
                )
            
            span.add_event("context_cleared")

    def cleanup_old_contexts(self):
        """Remove expired contexts to free up memory"""
        with telemetry.tracer.start_as_current_span("context_cleanup") as span:
            current_time = datetime.now()
            expired_contexts = [
                user_id for user_id, context in contexts.items()
                if current_time - context.last_updated > self.context_ttl
            ]
            
            for user_id in expired_contexts:
                del contexts[user_id]
            
            span.set_attributes({
                "context.cleaned_count": len(expired_contexts),
                "context.remaining_count": len(contexts)
            })

    async def get_context_summary(self, user_id: str) -> str:
        """Generate a summary of the conversation context"""
        context = await self.get_context(user_id)
        if not context or not context.conversation_history:
            return "No conversation history"
        
        last_messages = context.conversation_history[-3:]  # Get last 3 messages
        summary = []
        
        for msg in last_messages:
            role = msg["role"]
            content = msg["content"]
            timestamp = msg["timestamp"].strftime("%H:%M:%S")
            summary.append(f"[{timestamp}] {role}: {content[:100]}...")
        
        return "\n".join(summary)

    def _record_context_metrics(self, context: ConversationContext):
        # Record conversation length
        telemetry.meter.create_histogram(
            name="context.conversation_length",
            description="Number of messages in conversation",
            unit="1"
        ).record(len(context.conversation_history))
        
        # Record context age
        age = (datetime.now() - context.last_updated).total_seconds()
        telemetry.meter.create_histogram(
            name="context.age",
            description="Age of context in seconds",
            unit="s"
        ).record(age)

# Global instance
context_manager = ContextManager() 