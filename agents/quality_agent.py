"""
╔══════════════════════════════════════════════════════════════╗
║           CODE QUALITY AGENT — quality_agent.py             ║
╚══════════════════════════════════════════════════════════════╝

WHAT THIS AGENT DOES:
─────────────────────
Reviews code quality, readability, and maintainability.
Unlike bugs (correctness) or security (safety), quality issues
are about how GOOD the code is to work with long-term.

WHAT QUALITY MEANS HERE:
─────────────────────────
1. SOLID Principles (for OOP):
   - S: Single Responsibility — one class/function does one thing
   - O: Open/Closed — open for extension, closed for modification
   - L: Liskov Substitution — subclasses behave like parent classes
   - I: Interface Segregation — don't force implementing unused methods
   - D: Dependency Inversion — depend on abstractions, not concretions

2. Complexity:
   - Cyclomatic complexity (too many branches/conditions in one function)
   - Deeply nested code (pyramid of doom)
   - Functions that are too long (> 40-50 lines usually)

3. Naming:
   - Variables named 'x', 'temp', 'data' without context
   - Functions named 'process', 'handle', 'do_thing'
   - Magic numbers (what is 86400? → should be SECONDS_PER_DAY)

4. Documentation:
   - Missing docstrings on public functions/classes
   - Missing type hints in Python
   - Outdated or misleading comments

5. DRY Principle (Don't Repeat Yourself):
   - Copy-pasted code blocks
   - Similar functions that could be generalized

6. Error Handling:
   - Bare `except:` clauses (catches everything including SystemExit)
   - Missing error handling entirely
   - Overly broad exception handling
"""
import json
import asyncio
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.schema import SystemMessage, HumanMessage

load_dotenv()
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    max_tokens=2000
)


QUALITY_SYSTEM_PROMPT = """You are a senior software architect specializing in code quality, clean code principles, and software design.

Your task is to analyze code for QUALITY AND MAINTAINABILITY ISSUES ONLY. Do not report bugs or security vulnerabilities.

Evaluate these quality dimensions:

SOLID PRINCIPLES:
- Single Responsibility: functions/classes doing too many things
- Open/Closed: hardcoded logic that's hard to extend without modification
- Dependency Inversion: tight coupling, hardcoded dependencies instead of injection

COMPLEXITY & READABILITY:
- Cyclomatic complexity: functions with too many if/else/switch branches (>10 paths is too high)
- Deeply nested code: more than 3-4 levels of indentation
- Functions that are too long (> 50 lines)
- Complex boolean expressions that could be extracted to named functions

NAMING & CLARITY:
- Single-letter variables outside of loops (i, j in loops is acceptable)
- Vague function names (process, handle, do_stuff, data)
- Magic numbers/strings — unexplained literals that should be named constants
- Misleading names — variables/functions that do different things than they're named

CODE DUPLICATION (DRY violations):
- Repeated code blocks that should be extracted into a helper function
- Similar functions doing nearly the same thing

DOCUMENTATION:
- Missing docstrings on public functions, classes, or modules
- Missing type hints in Python (for functions with non-obvious types)
- Outdated/wrong comments that contradict the code

ERROR HANDLING:
- Bare except/catch clauses that swallow all errors
- Missing error handling in risky operations
- Exception handling that's too broad or too silent

SEVERITY:
- critical: Will definitely cause maintenance nightmares or team confusion
- warning: Reduces code quality significantly, should be fixed soon
- info: Best practice suggestion, nice to have

Return ONLY a valid JSON array. No markdown, no extra text.
[
  {
    "title": "Short quality issue name (max 8 words)",
    "detail": "Why this hurts code quality or maintainability",
    "line": "Line number or null",
    "severity": "critical" | "warning" | "info",
    "fix": "Specific refactoring suggestion"
  }
]

If code quality is good, return: []
"""


def _parse_json_response(text: str) -> list:
    text = text.strip()
    if text.startswith("```"):
        first_newline = text.find("\n")
        last_fence    = text.rfind("```")
        if first_newline != -1 and last_fence > first_newline:
            text = text[first_newline:last_fence].strip()
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return [result]
        return result if isinstance(result, list) else []
    except json.JSONDecodeError:
        return []


async def run_quality_agent(code: str, language: str) -> list:
    """
    Async code quality grader.
    
    Args:
        code:     Source code to grade
        language: Programming language (affects language-specific quality rules)
    
    Returns:
        List of quality issue dicts
    """
    human_message = f"""Review this {language} code for quality, maintainability, and clean code principles.

```{language.lower()}
{code}
```

Focus on SOLID principles, complexity, naming, documentation, and DRY violations.
Return ONLY a JSON array of quality issues."""

    messages = [
        SystemMessage(content=QUALITY_SYSTEM_PROMPT),
        HumanMessage(content=human_message)
    ]

    def _call_llm():
        response = llm.invoke(messages)
        return response.content

    raw_response = await asyncio.to_thread(_call_llm)
    return _parse_json_response(raw_response)