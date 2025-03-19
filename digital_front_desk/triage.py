from .models import AgentResponse, TriageResult, UrgencyLevel, ESILevel, ResourceType
from .telemetry import telemetry
from .critical_keywords import detect_critical_keywords, is_critical_condition
import time
from typing import List, Dict, Set, Tuple

class TriageEngine:
    def __init__(self):
        # Life-threatening conditions (ESI Level 1)
        self.life_threatening_conditions = {
            'cardiac arrest', 'respiratory arrest', 'intubation', 'severe respiratory distress',
            'anaphylaxis', 'severe shock', 'unconscious', 'not breathing', 
            'stroke symptoms acute', 'severe trauma', 'severe bleeding'
        }
        
        # High-risk conditions (ESI Level 2)
        self.high_risk_conditions = {
            'chest pain', 'difficulty breathing', 'altered mental status', 'severe pain',
            'stroke symptoms', 'acute vision change', 'suicidal', 'homicidal', 
            'severe headache', 'high fever', 'overdose', 'acute confusion'
        }
        
        # Conditions likely requiring multiple resources (ESI Level 3)
        self.multiple_resource_indicators = {
            'abdominal pain', 'moderate pain', 'fracture', 'dehydration', 'dizziness',
            'persistent vomiting', 'infection', 'wound requiring sutures'
        }
        
        # Conditions likely requiring one resource (ESI Level 4)
        self.single_resource_indicators = {
            'simple laceration', 'sprain', 'minor infection', 'medication refill',
            'minor pain', 'rash without systemic symptoms'
        }
        
        # Common vital sign abnormalities requiring attention
        self.vital_sign_concerns = {
            'high heart rate', 'low heart rate', 'high blood pressure', 'low blood pressure',
            'high respiratory rate', 'low respiratory rate', 'high fever', 'low temperature',
            'low oxygen saturation'
        }
        
        # Pediatric-specific concerns
        self.pediatric_concerns = {
            'infant fever', 'child respiratory distress', 'child lethargy',
            'dehydration in child', 'failure to thrive'
        }
        
        # Map of predicted resources by condition
        self.resource_predictions: Dict[str, List[ResourceType]] = {
            'chest pain': [ResourceType.LAB_TEST, ResourceType.IMAGING, ResourceType.MEDICATION],
            'abdominal pain': [ResourceType.LAB_TEST, ResourceType.IMAGING],
            'fracture': [ResourceType.IMAGING, ResourceType.PROCEDURE],
            'laceration': [ResourceType.PROCEDURE],
            'headache': [ResourceType.MEDICATION],
            'fever': [ResourceType.LAB_TEST],
            'infection': [ResourceType.LAB_TEST, ResourceType.MEDICATION],
            'respiratory': [ResourceType.LAB_TEST, ResourceType.MEDICATION],
            'dizziness': [ResourceType.LAB_TEST],
            'rash': [ResourceType.MEDICATION],
        }

    def _detect_esi_level_1_conditions(self, text: str) -> bool:
        """
        Detect conditions requiring immediate life-saving interventions (ESI Level 1)
        """
        text = text.lower()
        return any(condition in text for condition in self.life_threatening_conditions)

    def _detect_esi_level_2_conditions(self, text: str) -> bool:
        """
        Detect high-risk conditions or severe pain/distress (ESI Level 2)
        """
        text = text.lower()
        return any(condition in text for condition in self.high_risk_conditions)

    def _predict_resource_needs(self, text: str) -> Tuple[List[ResourceType], int]:
        """
        Predict the number of resources needed based on the patient's condition.
        Returns a tuple of (resources, count) where resources is a list of predicted
        ResourceType objects and count is the total number of unique resources.
        """
        text = text.lower()
        resources: Set[ResourceType] = set()
        
        # Check for specific conditions and add their associated resources
        for condition, resource_list in self.resource_predictions.items():
            if condition in text:
                resources.update(resource_list)
        
        # Check for general resource indicators
        if any(indicator in text for indicator in self.multiple_resource_indicators):
            # Ensure at least 2 resources for level 3
            if len(resources) < 2:
                # Add generic resources to reach 2+
                if ResourceType.LAB_TEST not in resources:
                    resources.add(ResourceType.LAB_TEST)
                if ResourceType.IMAGING not in resources and len(resources) < 2:
                    resources.add(ResourceType.IMAGING)
        
        if len(resources) == 0 and any(indicator in text for indicator in self.single_resource_indicators):
            # Add a single generic resource for level 4
            resources.add(ResourceType.MEDICATION)
        
        return list(resources), len(resources)

    def _detect_vital_sign_concerns(self, text: str) -> List[str]:
        """
        Detect mentions of concerning vital signs that might indicate higher acuity
        """
        text = text.lower()
        return [concern for concern in self.vital_sign_concerns if concern in text]

    def _check_pediatric_considerations(self, text: str) -> bool:
        """
        Check for pediatric-specific concerns that might require up-triaging
        """
        text = text.lower()
        return any(concern in text for concern in self.pediatric_concerns)

    def _determine_esi_level(self, 
                             agent_triage_score: float, 
                             text: str, 
                             resource_count: int) -> ESILevel:
        """
        Determine ESI level based on:
        1. Life-threatening conditions (Level 1)
        2. High-risk situations (Level 2)
        3. Number of resources needed (Levels 3-5)
        4. Vital signs consideration
        5. Pediatric considerations
        """
        # Check for life-threatening conditions (ESI Level 1)
        if self._detect_esi_level_1_conditions(text) or agent_triage_score > 0.9:
            return ESILevel.LEVEL_1
        
        # Check for high-risk conditions (ESI Level 2)
        if self._detect_esi_level_2_conditions(text) or agent_triage_score > 0.7:
            return ESILevel.LEVEL_2
        
        # Check vital signs - may up-triage to Level 2 if concerning
        vital_concerns = self._detect_vital_sign_concerns(text)
        if vital_concerns and (agent_triage_score > 0.5 or resource_count >= 2):
            return ESILevel.LEVEL_2
        
        # Check pediatric considerations - may up-triage
        if self._check_pediatric_considerations(text) and agent_triage_score > 0.4:
            # Up-triage pediatric patients with concerning symptoms
            return ESILevel.LEVEL_2 if resource_count >= 1 else ESILevel.LEVEL_3
        
        # Resource-based triage for stable patients (Levels 3-5)
        if resource_count >= 2:
            return ESILevel.LEVEL_3
        elif resource_count == 1:
            return ESILevel.LEVEL_4
        else:
            return ESILevel.LEVEL_5

    def _map_esi_to_urgency(self, esi_level: ESILevel) -> UrgencyLevel:
        """Maps ESI levels to legacy UrgencyLevel for backward compatibility"""
        mapping = {
            ESILevel.LEVEL_1: UrgencyLevel.CRITICAL,
            ESILevel.LEVEL_2: UrgencyLevel.HIGH,
            ESILevel.LEVEL_3: UrgencyLevel.MEDIUM,
            ESILevel.LEVEL_4: UrgencyLevel.LOW,
            ESILevel.LEVEL_5: UrgencyLevel.LOW
        }
        return mapping[esi_level]

    def process(self, agent_response: AgentResponse) -> TriageResult:
        """Process the agent response to determine ESI triage level and requirements"""
        with telemetry.tracer.start_as_current_span("triage_process") as span:
            start_time = time.time()
            
            text = agent_response.response.lower()
            
            # Predict required resources
            expected_resources, resource_count = self._predict_resource_needs(text)
            
            # Detect vital sign concerns
            vital_concerns = self._detect_vital_sign_concerns(text)
            
            # Determine ESI level
            esi_level = self._determine_esi_level(
                agent_response.triage_score,
                text,
                resource_count
            )
            
            # Map ESI level to legacy urgency level for backward compatibility
            urgency_level = self._map_esi_to_urgency(esi_level)
            
            # Generate action mapping based on ESI level
            action_map = {
                ESILevel.LEVEL_1: "Immediate life-saving intervention required - transfer to emergency response",
                ESILevel.LEVEL_2: "High-risk situation - priority routing to available healthcare provider",
                ESILevel.LEVEL_3: "Multiple resources needed - schedule urgent consultation",
                ESILevel.LEVEL_4: "One resource needed - schedule non-urgent appointment",
                ESILevel.LEVEL_5: "No resources needed - provide self-care instructions and resources"
            }
            
            # Determine if human attention is required
            requires_human = esi_level in {ESILevel.LEVEL_1, ESILevel.LEVEL_2, ESILevel.LEVEL_3}
            
            # Create reasoning string
            reasoning = f"ESI Level {esi_level.value}: "
            
            if esi_level == ESILevel.LEVEL_1:
                reasoning += "Patient requires immediate life-saving intervention. "
            elif esi_level == ESILevel.LEVEL_2:
                reasoning += "High-risk situation or severe pain/distress identified. "
            elif esi_level == ESILevel.LEVEL_3:
                reasoning += f"Multiple resources needed ({resource_count}). "
            elif esi_level == ESILevel.LEVEL_4:
                reasoning += "One resource needed. "
            else:  # ESI Level 5
                reasoning += "No resources needed. "
                
            if vital_concerns:
                reasoning += f"Vital sign concerns: {', '.join(vital_concerns)}. "
            
            if expected_resources:
                reasoning += f"Expected resources: {', '.join([r.value for r in expected_resources])}."
            
            # Create triage result
            result = TriageResult(
                urgency_level=urgency_level,
                esi_level=esi_level,
                recommended_action=action_map[esi_level],
                reasoning=reasoning,
                requires_human_attention=requires_human,
                expected_resources=expected_resources,
                vital_signs_concerns=vital_concerns
            )
            
            # Record for telemetry
            telemetry.record_response_time(
                (time.time() - start_time) * 1000,  # Convert to milliseconds
                "triage_engine"
            )
            
            # Add trace attributes
            span.set_attributes({
                "triage.esi_level": esi_level.value,
                "triage.urgency_level": urgency_level.value,
                "triage.resource_count": resource_count,
                "triage.requires_human": requires_human,
            })
            
            return result

# Global instance
triage_engine = TriageEngine() 