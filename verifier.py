"""
Scholarship Verification System - checks if a scholarship is legitimate.
Uses multiple heuristics to detect scams and verify authenticity.
"""
import re
from datetime import datetime, timedelta


# Red flags that indicate a potential scam
SCAM_FLAGS = {
    "guaranteed_win": {
        "patterns": [r"guaranteed", r"you will win", r"money back guarantee", r"100% guaranteed"],
        "weight": 0.3,
        "description": "Guarantees winning"
    },
    "application_fee": {
        "patterns": [r"application fee", r"processing fee", r"registration fee", r"pay to apply"],
        "weight": 0.3,
        "description": "Requires payment to apply"
    },
    "unsolicited_offer": {
        "patterns": [r"you have been selected", r"congratulations", r"you won", r"claim your prize"],
        "weight": 0.2,
        "description": "Unsolicited offer"
    },
    "high_pressure": {
        "patterns": [r"act now", r"limited time", r"expires today", r"last chance", r"hurry"],
        "weight": 0.15,
        "description": "High-pressure language"
    },
    "no_contact": {
        "patterns": [],
        "weight": 0.1,
        "description": "No contact information"
    },
    "vague_eligibility": {
        "patterns": [r"anyone can apply", r"no requirements", r"everyone qualifies"],
        "weight": 0.1,
        "description": "Vague eligibility criteria"
    },
    "too_good": {
        "patterns": [r"\$1,000,000", r"million dollar", r"unlimited funding"],
        "weight": 0.15,
        "description": "Too good to be true"
    }
}

# Positive signals that indicate legitimacy
LEGIT_SIGNALS = {
    "has_organization": {
        "patterns": [r"university", r"college", r"institute", r"foundation", r"government"],
        "weight": 0.2,
        "description": "From established organization"
    },
    "has_deadline": {
        "patterns": [r"deadline", r"due date", r"apply by", r"closes"],
        "weight": 0.15,
        "description": "Has clear deadline"
    },
    "has_eligibility": {
        "patterns": [r"eligibility", r"requirements", r"criteria", r"who can apply"],
        "weight": 0.15,
        "description": "Has clear eligibility criteria"
    },
    "has_contact": {
        "patterns": [r"contact", r"email", r"phone", r"address"],
        "weight": 0.1,
        "description": "Has contact information"
    },
    "has_application_process": {
        "patterns": [r"application process", r"how to apply", r"submit", r"documents required"],
        "weight": 0.15,
        "description": "Clear application process"
    },
    "known_provider": {
        "patterns": [r"fulbright", r"chevening", r"daad", r"erasmus", r"csc", r"mext", r"commonwealth"],
        "weight": 0.25,
        "description": "Known scholarship provider"
    }
}


def verify_scholarship(scholarship: dict) -> dict:
    """
    Verify if a scholarship is likely legitimate.
    
    Returns:
        {
            "is_legitimate": bool,
            "confidence_score": float (0-1),
            "scam_flags": list,
            "legit_signals": list,
            "recommendation": str
        }
    """
    text = f"{scholarship.get('title', '')} {scholarship.get('description', '')} {scholarship.get('url', '')}".lower()
    
    scam_score = 0
    scam_flags = []
    
    legit_score = 0
    legit_signals = []
    
    # Check for scam flags
    for flag_name, flag_info in SCAM_FLAGS.items():
        for pattern in flag_info["patterns"]:
            if re.search(pattern, text, re.I):
                scam_score += flag_info["weight"]
                scam_flags.append(flag_info["description"])
                break
    
    # Check for legitimate signals
    for signal_name, signal_info in LEGIT_SIGNALS.items():
        for pattern in signal_info["patterns"]:
            if re.search(pattern, text, re.I):
                legit_score += signal_info["weight"]
                legit_signals.append(signal_info["description"])
                break
    
    # Normalize scores
    max_scam = sum(f["weight"] for f in SCAM_FLAGS.values())
    max_legit = sum(s["weight"] for s in LEGIT_SIGNALS.values())
    
    scam_ratio = min(scam_score / max_scam, 1.0) if max_scam > 0 else 0
    legit_ratio = min(legit_score / max_legit, 1.0) if max_legit > 0 else 0
    
    # Calculate final confidence
    confidence = max(0, min(1, legit_ratio - scam_ratio * 0.5 + 0.5))
    
    # Determine recommendation
    if confidence >= 0.7:
        recommendation = "LIKELY LEGITIMATE - Proceed with application"
    elif confidence >= 0.5:
        recommendation = "UNCERTAIN - Verify additional details before applying"
    else:
        recommendation = "SUSPICIOUS - Exercise caution, verify independently"
    
    return {
        "is_legitimate": confidence >= 0.5,
        "confidence_score": round(confidence, 2),
        "scam_flags": scam_flags,
        "legit_signals": legit_signals,
        "recommendation": recommendation,
        "scam_ratio": round(scam_ratio, 2),
        "legit_ratio": round(legit_ratio, 2)
    }


def verify_scholarships_batch(scholarships: list[dict]) -> list[dict]:
    """
    Verify a batch of scholarships and add verification results.
    """
    verified = []
    for s in scholarships:
        verification = verify_scholarship(s)
        s["verification"] = verification
        verified.append(s)
    return verified


def get_verification_summary(scholarships: list[dict]) -> dict:
    """
    Get summary statistics for verified scholarships.
    """
    total = len(scholarships)
    legitimate = sum(1 for s in scholarships if s.get("verification", {}).get("is_legitimate", False))
    suspicious = total - legitimate
    
    avg_confidence = 0
    if total > 0:
        avg_confidence = sum(s.get("verification", {}).get("confidence_score", 0) for s in scholarships) / total
    
    return {
        "total": total,
        "legitimate": legitimate,
        "suspicious": suspicious,
        "legitimacy_rate": round(legitimate / total * 100, 1) if total > 0 else 0,
        "average_confidence": round(avg_confidence, 2)
    }
