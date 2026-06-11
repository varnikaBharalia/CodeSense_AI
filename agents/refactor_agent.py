
import json
import asyncio
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.1,
    max_tokens=3000
)

REFACTOR_SYSTEM_PROMPT = """You are an expert software engineer tasked with refactoring code to fix all identified issues.

You will receive:
1. The original code
2. A list of bugs found
3. A list of security vulnerabilities found
4. A list of quality issues found

Your task:
- Rewrite the code to fix ALL identified issues
- Keep the same overall structure and purpose of the code
- Do NOT add features that weren't there — only fix problems
- Write clean, readable, well-documented code
- Add type hints where appropriate (for Python)
- Add docstrings to public functions
- Use proper error handling

Respond ONLY with a valid JSON object:
{
  "code": "The complete refactored code as a string",
  "summary": [
    "Change 1: description of what was fixed and why",
    "Change 2: ...",
    ...
  ]
}

The "code" field must be the COMPLETE refactored file, not just the changed parts.
The "summary" must list each meaningful change made, referencing the original issue.
"""


def _parse_refactor_response(text: str) -> dict:
   
    text = text.strip()
    
    if text.startswith("```"):
        first_newline = text.find("\n")
        last_fence    = text.rfind("```")
        if first_newline != -1 and last_fence > first_newline:
            text = text[first_newline:last_fence].strip()
    
    try:
        result = json.loads(text)
        if "code" in result:
            return result
        return {"code": "", "summary": ["Could not parse refactored code."]}
    except json.JSONDecodeError:
        
        return {
            "code": text,
            "summary": ["Refactored code generated (summary unavailable)"]
        }


async def run_refactor_agent(code: str, language: str, findings: dict) -> dict:
   
    def format_findings(findings_list: list, label: str) -> str:
        if not findings_list:
            return f"{label}: None found\n"
        lines = [f"{label}:"]
        for i, f in enumerate(findings_list, 1):
            severity = f.get('severity', 'info').upper()
            title    = f.get('title', 'Unknown issue')
            detail   = f.get('detail', '')
            lines.append(f"  {i}. [{severity}] {title}: {detail}")
        return "\n".join(lines)

    bugs_text     = format_findings(findings.get("bugs",     []), "BUGS")
    security_text = format_findings(findings.get("security", []), "SECURITY VULNERABILITIES")
    quality_text  = format_findings(findings.get("quality",  []), "QUALITY ISSUES")

    human_message = f"""Please refactor the following {language} code to fix all identified issues.

ORIGINAL CODE:
```{language.lower()}
{code}
```

ISSUES TO FIX:
{bugs_text}

{security_text}

{quality_text}

Produce a complete refactored version that fixes ALL of the above issues.
Return ONLY a JSON object with "code" and "summary" fields."""

    messages = [
        SystemMessage(content=REFACTOR_SYSTEM_PROMPT),
        HumanMessage(content=human_message)
    ]

    def _call_llm():
        response = llm.invoke(messages)
        return response.content

    raw_response = await asyncio.to_thread(_call_llm)
    return _parse_refactor_response(raw_response)