"""
╔══════════════════════════════════════════════════════════════╗
║              BUG DETECTION AGENT — bug_agent.py             ║
╚══════════════════════════════════════════════════════════════╝

WHAT THIS AGENT DOES:
─────────────────────
This agent is a specialist. Its ONLY job is to find bugs:
  - Logic errors (wrong operator, wrong condition)
  - Runtime errors (division by zero, null pointer, index out of range)
  - Type errors (wrong type passed to function)
  - Unhandled exceptions (missing try/except)
  - Infinite loops / unreachable code
  - Resource leaks (files/connections not closed)

WHY A SEPARATE AGENT?
─────────────────────
Instead of one giant prompt that does everything, we use focused
specialist agents. This gives better results because:
  1. The LLM has ONE clear task — it doesn't get distracted
  2. We can tune the prompt specifically for bug detection
  3. We can run it in PARALLEL with other agents (saves time)
  4. Easier to improve/debug one agent without affecting others

HOW IT WORKS:
─────────────
1. Build a detailed system prompt explaining what bugs to find
2. Send the code + prompt to the LLM (via LangChain)
3. Parse the JSON response into a list of issue dicts
4. Return the list
"""

import json
import asyncio
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
load_dotenv()

# ══════════════════════════════════════════════════════════════════════════════
#  LLM INITIALIZATION
#  We create a single LLM instance at module level — this is more efficient
#  than creating a new instance on every function call.
#
#  model: gpt-4o gives best code analysis accuracy
#  temperature: 0 means deterministic — same code always gets same review.
#               Higher temperature = more creative but less consistent.
# ══════════════════════════════════════════════════════════════════════════════
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    max_tokens=2000
)

# ══════════════════════════════════════════════════════════════════════════════
#  SYSTEM PROMPT
#  This is the "personality" instruction given to the LLM.
#  It tells the LLM what role to play and HOW to format its output.
#
#  KEY DESIGN DECISIONS:
#  - We explicitly list categories of bugs to look for
#  - We require JSON output (makes parsing reliable)
#  - We define the exact JSON schema we want
#  - We say "ONLY report real bugs" to avoid false positives
# ══════════════════════════════════════════════════════════════════════════════
BUG_SYSTEM_PROMPT = """You are an expert software engineer specializing in bug detection and code correctness.

Your task is to analyze the provided code and find BUGS ONLY. Do not report style issues or security issues.

Look specifically for:
1. Logic errors — wrong conditions, operators, or algorithm implementation
2. Runtime exceptions — null/None dereference, division by zero, index out of bounds
3. Type mismatches — passing wrong types to functions, incorrect comparisons
4. Unhandled exceptions — missing try/except/catch around risky operations
5. Resource leaks — files, database connections, or sockets not properly closed
6. Infinite loops — loops with conditions that can never become false
7. Race conditions — shared mutable state without synchronization
8. Off-by-one errors — wrong loop bounds, fence-post errors
9. Dead code / unreachable code — code that can never execute

IMPORTANT RULES:
- ONLY report genuine bugs, not style preferences
- Be specific about WHY it's a bug, not just that it looks wrong
- Estimate the line number if visible
- Severity: "critical" = will crash or cause data loss, "warning" = may cause bugs under certain conditions, "info" = minor correctness concern

Respond ONLY with a valid JSON array. No explanation text, no markdown, no code fences.
Each object must have exactly these fields:
[
  {
    "title": "Short bug name (max 8 words)",
    "detail": "Clear explanation of why this is a bug and what happens when it occurs",
    "line": "Line number or range, e.g. '12' or '10-15', or null if unclear",
    "severity": "critical" | "warning" | "info",
    "fix": "Specific suggestion on how to fix this bug"
  }
]

If NO bugs are found, return an empty array: []
"""


# ══════════════════════════════════════════════════════════════════════════════
#  SAFE JSON PARSER
#  LLMs sometimes wrap JSON in markdown code fences (```json ... ```)
#  even when told not to. This function strips those and parses safely.
# ══════════════════════════════════════════════════════════════════════════════
def _parse_json_response(text: str) -> list:
    """
    Parses the LLM response into a Python list.
    
    Handles these cases:
    - Clean JSON:           [{"title": ...}]
    - Markdown wrapped:     ```json\n[{"title": ...}]\n```
    - Empty response:       Returns []
    - Parse error:          Returns [] with a warning issue
    """
    text = text.strip()
    
    # Strip markdown code fences if present
    if text.startswith("```"):
        # Find the first newline after the opening fence
        first_newline = text.find("\n")
        # Find the closing fence
        last_fence = text.rfind("```")
        if first_newline != -1 and last_fence > first_newline:
            text = text[first_newline:last_fence].strip()
    
    # Try to parse as JSON
    try:
        result = json.loads(text)
        # Ensure it's a list (sometimes LLM returns a dict instead)
        if isinstance(result, dict):
            return [result]
        if isinstance(result, list):
            return result
        return []
    except json.JSONDecodeError:
        # If parsing fails completely, return a single warning issue
        return [{
            "title": "Analysis parsing error",
            "detail": "Could not parse bug analysis response. Try again.",
            "line": None,
            "severity": "info",
            "fix": "Re-run the analysis"
        }]


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN AGENT FUNCTION
#  This is the async function called from app.py via asyncio.gather().
#
#  Why async?
#  ──────────
#  The LLM API call involves waiting for a network response.
#  While waiting, Python can switch to running other agents.
#  asyncio.to_thread() runs the synchronous LangChain call in a
#  thread pool so it doesn't block the event loop.
# ══════════════════════════════════════════════════════════════════════════════
async def run_bug_agent(code: str, language: str) -> list:
    """
    Async entry point for the bug detection agent.
    
    Args:
        code:     The source code string to analyze
        language: Programming language name (e.g., "Python")
    
    Returns:
        List of issue dicts: [{ title, detail, line, severity, fix }, ...]
    """
    # Build the human message — the actual code to review
    human_message = f"""Please analyze this {language} code for bugs:

```{language.lower()}
{code}
```

Remember: return ONLY a JSON array of bugs found."""

    # Build the messages list — this is how chat models receive input
    # SystemMessage sets the LLM's role/behavior
    # HumanMessage is the actual user request
    messages = [
        SystemMessage(content=BUG_SYSTEM_PROMPT),
        HumanMessage(content=human_message)
    ]

    # Run the synchronous LangChain call in a thread pool
    # This allows other agents to run simultaneously
    def _call_llm():
        response = llm.invoke(messages)
        return response.content  # Extract the text from the response object

    # asyncio.to_thread() — run blocking I/O in a separate thread
    # so the async event loop isn't blocked
    raw_response = await asyncio.to_thread(_call_llm)

    # Parse the JSON response into a Python list
    issues = _parse_json_response(raw_response)

    return issues