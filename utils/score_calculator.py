"""
╔══════════════════════════════════════════════════════════════╗
║           SCORE CALCULATOR — score_calculator.py            ║
╚══════════════════════════════════════════════════════════════╝

WHAT THIS DOES:
───────────────
Converts the raw findings from all three agents into numeric
scores from 0–100. These scores power the circular progress
rings in the UI.

SCORING LOGIC:
──────────────
Each category starts at 100 (perfect) and we deduct points
for each issue found, with heavier penalties for higher severity.

PENALTY TABLE:
─────────────
  critical:  -20 points per issue
  warning:   -10 points per issue
  info:       -3 points per issue

Score is clamped to [0, 100] — can't go below 0.

OVERALL SCORE:
──────────────
Weighted average:
  - Bugs:     30% weight  (correctness is critical)
  - Security: 40% weight  (security is most important)
  - Quality:  30% weight  (quality affects maintainability)
"""


# ══════════════════════════════════════════════════════════════════════════════
#  PENALTY POINTS PER SEVERITY LEVEL
# ══════════════════════════════════════════════════════════════════════════════
PENALTIES = {
    "critical": 20,    # -20 per critical issue
    "warning":  10,    # -10 per warning
    "info":      3,    # -3 per info/suggestion
}

# Weights for the overall score calculation (must sum to 1.0)
WEIGHTS = {
    "bugs":     0.30,  # 30% — correctness
    "security": 0.40,  # 40% — security (highest weight)
    "quality":  0.30,  # 30% — maintainability
}


def _score_category(issues: list) -> int:
    """
    Calculates the score for a single category (bugs, security, or quality).
    
    Algorithm:
      start_score = 100
      for each issue:
          deduct PENALTIES[issue.severity]
      return max(0, start_score)
    
    Args:
        issues: List of issue dicts from an agent
    
    Returns:
        Integer score 0–100
    """
    score = 100
    
    for issue in issues:
        severity = issue.get("severity", "info").lower()
        # Get the penalty for this severity, default to info penalty if unknown
        penalty = PENALTIES.get(severity, PENALTIES["info"])
        score -= penalty
    
    # Clamp to [0, 100]
    return max(0, min(100, score))


def calculate_score(findings: dict) -> dict:
    """
    Calculates scores for all categories and an overall score.
    
    Args:
        findings: Dict with keys 'bugs', 'security', 'quality'
                  Each value is a list of issue dicts
    
    Returns:
        Dict with keys: 'bugs', 'security', 'quality', 'overall'
        All values are integers 0–100
    
    Example:
        findings = {
            "bugs":     [{"severity": "critical"}, {"severity": "warning"}],
            "security": [{"severity": "critical"}],
            "quality":  []
        }
        →  { "bugs": 70, "security": 80, "quality": 100, "overall": 82 }
    """
    bug_score      = _score_category(findings.get("bugs",     []))
    security_score = _score_category(findings.get("security", []))
    quality_score  = _score_category(findings.get("quality",  []))

    # Weighted average for overall score
    overall = (
        bug_score      * WEIGHTS["bugs"]     +
        security_score * WEIGHTS["security"] +
        quality_score  * WEIGHTS["quality"]
    )

    return {
        "bugs":     bug_score,
        "security": security_score,
        "quality":  quality_score,
        "overall":  round(overall),  # Round to nearest integer
    }