from typing import Set, Dict, List, Tuple
import re

# ESI Level 1: Immediate life-saving intervention required
ESI_LEVEL_1_KEYWORDS: Dict[str, List[str]] = {
    "cardiac arrest": [],
    "respiratory arrest": [],
    "not breathing": [],
    "severe respiratory distress": [],
    "intubation needed": [],
    "anaphylaxis": [],
    "anaphylactic shock": [],
    "severe shock": [],
    "unconscious": [],
    "unresponsive": [],
    "active seizure": [],
    "severe trauma": [],
    "massive bleeding": [],
    "hemorrhage": [],
    "severe head injury": [],
    "drowning": [],
    "choking": [],
    "airway compromise": [],
    "severe burn": ["face", "airway"],
    "cardiac pain": ["severe"],
}

# ESI Level 2: High-risk situation or severe pain/distress
ESI_LEVEL_2_KEYWORDS: Dict[str, List[str]] = {
    "chest pain": [],
    "difficulty breathing": [],
    "shortness of breath": [],
    "altered mental status": [],
    "confused": ["suddenly", "acute"],
    "disoriented": ["suddenly", "acute"],
    "severe pain": [],
    "10 out of 10 pain": [],
    "stroke symptoms": [],
    "facial drooping": [],
    "slurred speech": [],
    "arm weakness": [],
    "vision loss": ["sudden", "acute"],
    "suicidal": [],
    "homicidal": [],
    "suicide attempt": [],
    "severe headache": ["worst", "sudden"],
    "high fever": ["child", "infant"],
    "overdose": [],
    "poisoning": [],
    "acute confusion": [],
    "severe allergic reaction": [],
    "severe dehydration": [],
    "diabetic": ["unresponsive", "emergency"],
    "trauma": ["significant"],
    "fracture": ["open", "compound"],
    "amputation": [],
    "pregnancy": ["bleeding", "severe pain"],
}

# Resource Prediction Keywords (for ESI Levels 3-5)
RESOURCE_KEYWORDS: Dict[str, List[str]] = {
    # Lab test resources
    "blood test": [],
    "urine test": [],
    "lab work": [],
    "cultures": [],
    "strep test": [],
    "flu test": [],
    "covid test": [],
    
    # Imaging resources
    "x-ray": [],
    "ultrasound": [],
    "ct scan": [],
    "mri": [],
    
    # IV fluids or medications
    "iv fluids": [],
    "intravenous": [],
    "iv medication": [],
    "antibiotic": ["iv"],
    
    # Procedures
    "stitches": [],
    "sutures": [],
    "wound care": [],
    "splint": [],
    "cast": [],
    "incision and drainage": [],
    "intubation": [],
    "catheter": [],
    
    # Specialist consultations
    "specialist": [],
    "cardiology": [],
    "neurology": [],
    "orthopedics": [],
    "surgery": [],
    "obgyn": [],
    "pediatric specialist": [],
}

# Vital sign concerns
VITAL_SIGN_KEYWORDS: Dict[str, List[str]] = {
    "high blood pressure": [],
    "low blood pressure": [],
    "tachycardia": [],
    "bradycardia": [],
    "heart rate": ["high", "rapid", "low", "slow"],
    "high temperature": [],
    "fever": ["high", "severe"],
    "hyperthermia": [],
    "hypothermia": [],
    "low temperature": [],
    "low oxygen": [],
    "oxygen saturation": ["low"],
    "respiratory rate": ["high", "rapid", "low", "slow"],
    "breathing rate": ["high", "rapid", "low", "slow"],
}

# Pediatric-specific concerns
PEDIATRIC_KEYWORDS: Dict[str, List[str]] = {
    "infant fever": [],
    "child respiratory distress": [],
    "child breathing difficulty": [],
    "child lethargy": [],
    "child unresponsive": [],
    "child dehydration": [],
    "failure to thrive": [],
    "child not eating": [],
    "child not drinking": [],
}

def detect_critical_keywords(text: str) -> List[str]:
    """
    Detect critical keywords in the given text.
    Returns a list of detected critical keywords.
    """
    text = text.lower()
    detected_keywords = []
    
    # Check ESI Level 1 keywords (most critical)
    for keyword, contexts in ESI_LEVEL_1_KEYWORDS.items():
        if keyword.lower() in text:
            # If keyword has no specific context requirements
            if not contexts:
                detected_keywords.append(f"ESI1:{keyword}")
            # If keyword has context requirements, check if any context is present
            elif any(context.lower() in text for context in contexts):
                detected_keywords.append(f"ESI1:{keyword}")
    
    # Check ESI Level 2 keywords (high risk)
    for keyword, contexts in ESI_LEVEL_2_KEYWORDS.items():
        if keyword.lower() in text:
            # If keyword has no specific context requirements
            if not contexts:
                detected_keywords.append(f"ESI2:{keyword}")
            # If keyword has context requirements, check if any context is present
            elif any(context.lower() in text for context in contexts):
                detected_keywords.append(f"ESI2:{keyword}")
    
    return detected_keywords

def is_critical_condition(text: str) -> bool:
    """
    Determine if the text contains any ESI Level 1 keywords.
    Returns True if ESI Level 1 critical keywords are found, False otherwise.
    """
    return any(keyword.startswith("ESI1:") for keyword in detect_critical_keywords(text))

def is_high_risk_condition(text: str) -> bool:
    """
    Determine if the text contains any ESI Level 2 keywords.
    Returns True if ESI Level 2 high-risk keywords are found, False otherwise.
    """
    return any(keyword.startswith("ESI2:") for keyword in detect_critical_keywords(text))

def detect_resource_keywords(text: str) -> List[str]:
    """
    Detect keywords related to resource needs.
    Returns a list of detected resource keywords.
    """
    text = text.lower()
    detected_keywords = []
    
    for keyword, contexts in RESOURCE_KEYWORDS.items():
        if keyword.lower() in text:
            if not contexts:
                detected_keywords.append(keyword)
            elif any(context.lower() in text for context in contexts):
                detected_keywords.append(keyword)
    
    return detected_keywords

def count_expected_resources(text: str) -> int:
    """
    Count the number of unique resources likely needed based on keywords.
    Returns an integer count of resources.
    """
    # Get unique resource types from detected keywords
    resource_keywords = detect_resource_keywords(text)
    
    # Map to resource categories
    resource_categories = set()
    
    for keyword in resource_keywords:
        if any(lab_term in keyword for lab_term in ["blood", "urine", "lab", "test", "culture"]):
            resource_categories.add("lab")
        elif any(imaging_term in keyword for imaging_term in ["x-ray", "ultrasound", "ct", "mri"]):
            resource_categories.add("imaging")
        elif any(iv_term in keyword for iv_term in ["iv", "intravenous"]):
            resource_categories.add("iv")
        elif any(procedure_term in keyword for procedure_term in ["stitches", "sutures", "wound", "splint", "cast", "drainage", "intubation", "catheter"]):
            resource_categories.add("procedure")
        elif any(specialist_term in keyword for specialist_term in ["specialist", "cardiology", "neurology", "orthopedics", "surgery", "obgyn", "pediatric"]):
            resource_categories.add("specialist")
    
    return len(resource_categories)

def detect_vital_sign_concerns(text: str) -> List[str]:
    """
    Detect keywords related to concerning vital signs.
    Returns a list of detected vital sign concerns.
    """
    text = text.lower()
    detected_concerns = []
    
    for keyword, contexts in VITAL_SIGN_KEYWORDS.items():
        if keyword.lower() in text:
            if not contexts:
                detected_concerns.append(keyword)
            elif any(context.lower() in text for context in contexts):
                detected_concerns.append(keyword)
    
    return detected_concerns

def has_pediatric_concerns(text: str) -> bool:
    """
    Determine if the text contains pediatric-specific concerns.
    Returns True if pediatric concern keywords are found, False otherwise.
    """
    text = text.lower()
    
    for keyword, contexts in PEDIATRIC_KEYWORDS.items():
        if keyword.lower() in text:
            if not contexts:
                return True
            elif any(context.lower() in text for context in contexts):
                return True
    
    return False 