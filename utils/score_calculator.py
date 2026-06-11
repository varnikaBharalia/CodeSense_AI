
PENALTIES = {
    "critical": 20,    
    "warning":  10,    
    "info":      3, 
}

WEIGHTS = {
    "bugs":     0.30,  
    "security": 0.40,  
    "quality":  0.30, 
}


def _score_category(issues: list) -> int:
    
    score = 100
    
    for issue in issues:
        severity = issue.get("severity", "info").lower()
        penalty = PENALTIES.get(severity, PENALTIES["info"])
        score -= penalty
    
    return max(0, min(100, score))


def calculate_score(findings: dict) -> dict:
   
    bug_score      = _score_category(findings.get("bugs",     []))
    security_score = _score_category(findings.get("security", []))
    quality_score  = _score_category(findings.get("quality",  []))

    overall = (
        bug_score      * WEIGHTS["bugs"]     +
        security_score * WEIGHTS["security"] +
        quality_score  * WEIGHTS["quality"]
    )

    return {
        "bugs":     bug_score,
        "security": security_score,
        "quality":  quality_score,
        "overall":  round(overall),  
    }