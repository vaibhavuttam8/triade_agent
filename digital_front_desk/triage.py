from .models import AgentResponse, TriageResult, UrgencyLevel
from .telemetry import telemetry
import time

class TriageEngine:
    def __init__(self):
        self.urgent_keywords = {
            'emergency', 'severe', 'critical', 'urgent', 'immediate',
            'chest pain', 'difficulty breathing', 'unconscious'
        }
        
        self.medium_keywords = {
            'pain', 'fever', 'injury', 'infection', 'chronic',
            'medication', 'prescription'
        }

    def _calculate_keyword_score(self, text: str) -> float:
        text = text.lower()
        urgent_matches = sum(1 for word in self.urgent_keywords if word in text)
        medium_matches = sum(1 for word in self.medium_keywords if word in text)
        
        # Weight urgent keywords more heavily
        return (urgent_matches * 0.7 + medium_matches * 0.3) / (len(self.urgent_keywords) + len(self.medium_keywords))

    def _determine_urgency_level(self, triage_score: float, confidence_score: float) -> UrgencyLevel:
        # Combine triage score with confidence and keyword analysis
        if triage_score > 0.8 and confidence_score > 0.7:
            return UrgencyLevel.CRITICAL
        elif triage_score > 0.6:
            return UrgencyLevel.HIGH
        elif triage_score > 0.4:
            return UrgencyLevel.MEDIUM
        else:
            return UrgencyLevel.LOW

    def process(self, agent_response: AgentResponse) -> TriageResult:
        with telemetry.tracer.start_as_current_span("triage_process") as span:
            start_time = time.time()
            
            # Calculate keyword-based score
            keyword_score = self._calculate_keyword_score(agent_response.response)
            
            # Combine with agent's triage score
            final_score = (keyword_score + agent_response.triage_score) / 2
            
            # Record the triage score metric
            telemetry.record_triage_score(final_score)
            
            # Determine urgency level
            urgency_level = self._determine_urgency_level(
                final_score, 
                agent_response.confidence_score
            )
            
            # Add trace attributes
            span.set_attributes({
                "triage.keyword_score": keyword_score,
                "triage.final_score": final_score,
                "triage.urgency_level": urgency_level.value
            })
            
            # Determine if human attention is needed
            requires_human = urgency_level in {UrgencyLevel.HIGH, UrgencyLevel.CRITICAL}
            
            # Generate recommended action based on urgency
            action_map = {
                UrgencyLevel.CRITICAL: "Immediate transfer to emergency response team",
                UrgencyLevel.HIGH: "Priority routing to available healthcare provider",
                UrgencyLevel.MEDIUM: "Schedule consultation within 24 hours",
                UrgencyLevel.LOW: "Provide self-care instructions and resources"
            }
            
            result = TriageResult(
                urgency_level=urgency_level,
                recommended_action=action_map[urgency_level],
                reasoning=f"Based on message content and AI analysis. "
                         f"Keyword score: {keyword_score:.2f}, "
                         f"Agent score: {agent_response.triage_score:.2f}",
                requires_human_attention=requires_human
            )
            
            # Record processing time
            telemetry.record_response_time(
                (time.time() - start_time) * 1000,  # Convert to milliseconds
                "triage_engine"
            )
            
            return result

# Global instance
triage_engine = TriageEngine() 