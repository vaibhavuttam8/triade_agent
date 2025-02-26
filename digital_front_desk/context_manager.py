from .models import ConversationContext, ChannelInput, AgentResponse
from .telemetry import telemetry
from typing import Dict, Optional
from datetime import datetime, timedelta

class ContextManager:
    def __init__(self):
        self.contexts: Dict[str, ConversationContext] = {}
        self.context_ttl = timedelta(hours=24)  # Context time-to-live

    def get_context(self, user_id: str) -> ConversationContext:
        with telemetry.tracer.start_as_current_span("context_get") as span:
            span.set_attributes({
                "context.user_id": user_id,
                "context.exists": user_id in self.contexts
            })
            
            if user_id not in self.contexts:
                self.contexts[user_id] = ConversationContext(
                    user_id=user_id,
                    conversation_history=[],
                    metadata={}
                )
            return self.contexts[user_id]

    def update_context(
        self,
        user_id: str,
        channel_input: Optional[ChannelInput] = None,
        agent_response: Optional[AgentResponse] = None
    ):
        with telemetry.tracer.start_as_current_span("context_update") as span:
            context = self.get_context(user_id)
            current_time = datetime.now()
            
            if channel_input:
                context.conversation_history.append({
                    "role": "user",
                    "content": channel_input.message,
                    "timestamp": current_time,
                    "channel": channel_input.channel_type
                })
            
            if agent_response:
                context.conversation_history.append({
                    "role": "assistant",
                    "content": agent_response.response,
                    "timestamp": current_time,
                    "triage_score": agent_response.triage_score,
                    "confidence_score": agent_response.confidence_score
                })
            
            context.last_updated = current_time
            
            # Record metrics
            self._record_context_metrics(context)
            
            span.set_attributes({
                "context.history_length": len(context.conversation_history),
                "context.last_updated": context.last_updated.isoformat()
            })

    def cleanup_old_contexts(self):
        """Remove contexts that haven't been updated within TTL"""
        with telemetry.tracer.start_as_current_span("context_cleanup") as span:
            current_time = datetime.now()
            expired_contexts = [
                user_id for user_id, context in self.contexts.items()
                if current_time - context.last_updated > self.context_ttl
            ]
            
            for user_id in expired_contexts:
                del self.contexts[user_id]
            
            span.set_attributes({
                "context.cleaned_count": len(expired_contexts),
                "context.remaining_count": len(self.contexts)
            })

    def get_context_summary(self, user_id: str) -> str:
        """Generate a summary of the conversation context"""
        context = self.get_context(user_id)
        if not context.conversation_history:
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