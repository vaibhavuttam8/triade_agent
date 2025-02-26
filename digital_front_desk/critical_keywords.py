from typing import Set, Dict, List
import re

# Critical keywords with their contexts
CRITICAL_KEYWORDS: Dict[str, List[str]] = {
    "chest pain": [],
    "shortness of breath": [],
    "difficulty breathing": [],
    "severe headache": [],
    "vomiting blood": [],
    "coughing up blood": [],
    "severe abdominal pain": [],
    "difficulty speaking": [],
    "face numbness": [],
    "allergic reaction": [],
    "throat closing": [],
    "severe cramping": ["pregnancy"],  # Context specific
    "high fever": [],
    "stiff neck": [],
    "suicidal thoughts": [],
    "heart palpitations": [],
    "deep cut": [],
    "won't stop bleeding": [],
    "asthma attack": [],
    "unconscious": [],
    "vision loss": [],
    "severe eye pain": [],
    "lips turning blue": [],
    "sudden severe pain": [],
    "numbness and tingling": ["arm", "face"],  # Context specific
    "severe swelling": [],
    "difficulty swallowing": [],
    "panic attacks": [],
    "red, swollen, warm": ["skin"],  # Context specific
    "severe bleeding": []
}

def detect_critical_keywords(text: str) -> List[str]:
    """
    Detect critical keywords in the given text.
    Returns a list of detected critical keywords.
    """
    text = text.lower()
    detected_keywords = []
    
    for keyword, contexts in CRITICAL_KEYWORDS.items():
        if keyword.lower() in text:
            # If keyword has no specific context requirements
            if not contexts:
                detected_keywords.append(keyword)
            # If keyword has context requirements, check if any context is present
            elif any(context.lower() in text for context in contexts):
                detected_keywords.append(keyword)
    
    return detected_keywords

def is_critical_condition(text: str) -> bool:
    """
    Determine if the text contains any critical keywords.
    Returns True if critical keywords are found, False otherwise.
    """
    return len(detect_critical_keywords(text)) > 0 