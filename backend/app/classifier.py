"""
Conservative, recall-favoring classifier for sensitive content.
False positives (flagging normal content as sensitive) are acceptable since that content still works fine
in the vault path, just without semantic/graph enrichment from Cognee.
False negatives (sensitive content slipping through as 'normal' and reaching Cognee) are the failure mode we're avoiding.
"""
import re
from typing import List, Tuple
from app.models import ClassificationResult

# Define regex patterns for sensitive content
PATTERNS = {
    "api_key": r"(?i)(?:sk-[a-z0-9]{20,}|akia[a-z0-9]{16}|(?:key|token|secret).{0,20}?[a-z0-9_-]{32,})",
    "email": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
    "credit_card": r"\b(?:\d[ -]*?){13,19}\b",
    "phone": r"(?:\+91[\s-]?[6789]\d{9}|\+(?:[0-9] ?){6,14}[0-9])",
    "keyword": r"(?i)\b(?:password|secret|private key|confidential|do not share|ssn|aadhaar)\b",
    "aadhaar": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"
}

# Compile patterns for performance
COMPILED_PATTERNS = {name: re.compile(pattern) for name, pattern in PATTERNS.items()}

def classify_chunk(text: str) -> ClassificationResult:
    """Classifies a chunk of text to detect sensitive content."""
    matched_types = set()
    
    for pattern_name, regex in COMPILED_PATTERNS.items():
        if regex.search(text):
            matched_types.add(pattern_name)
    
    is_sensitive = len(matched_types) > 0
    
    # Calculate confidence based on number of distinct matched pattern types
    # Let's say max confidence is reached at 3 distinct pattern types
    confidence = 0.0
    if is_sensitive:
        confidence = min(1.0, len(matched_types) / 3.0)
        
    return ClassificationResult(
        is_sensitive=is_sensitive,
        matched_patterns=list(matched_types),
        confidence=confidence
    )
