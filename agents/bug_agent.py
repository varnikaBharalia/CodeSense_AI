
import json
import asyncio
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
load_dotenv()
import asyncio
from langchain_core.messages import SystemMessage, HumanMessage
from utils.llm_utils import get_llm, parse_json_response   # ← use shared utils


llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    max_tokens=2000
)


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

def _parse_json_response(text: str) -> list:
   
    text = text.strip()
    
    if text.startswith("```"):
        first_newline = text.find("\n")
        last_fence = text.rfind("```")
        if first_newline != -1 and last_fence > first_newline:
            text = text[first_newline:last_fence].strip()
    
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return [result]
        if isinstance(result, list):
            return result
        return []
    except json.JSONDecodeError:
        return [{
            "title": "Analysis parsing error",
            "detail": "Could not parse bug analysis response. Try again.",
            "line": None,
            "severity": "info",
            "fix": "Re-run the analysis"
        }]

async def run_bug_agent(code: str, language: str) -> list:
   
    human_message = f"""Please analyze this {language} code for bugs:

```{language.lower()}
{code}
```

Remember: return ONLY a JSON array of bugs found."""

    messages = [
        SystemMessage(content=BUG_SYSTEM_PROMPT),
        HumanMessage(content=human_message)
    ]

    def _call_llm():
        response = get_llm().invoke(messages)  
        return response.content  
    raw_response = await asyncio.to_thread(_call_llm)

    issues = parse_json_response(raw_response)    

    return issues