
import json
import asyncio
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
load_dotenv()





llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    max_tokens=2000
)


SECURITY_SYSTEM_PROMPT = """You are a senior application security engineer (AppSec) specializing in secure code review.

Your task is to analyze code for SECURITY VULNERABILITIES ONLY. Do not report bugs or style issues.

Focus on these vulnerability categories:

INJECTION (A03):
- SQL Injection: string concatenation in queries instead of parameterized queries
- Command Injection: user input passed to os.system(), exec(), subprocess without sanitization
- Template Injection: user input rendered in templates

CRYPTOGRAPHIC FAILURES (A02):
- Hardcoded credentials: passwords, API keys, tokens, secrets in source code
- Weak hashing: MD5, SHA1 for passwords (use bcrypt/argon2)
- Plaintext storage of sensitive data

ACCESS CONTROL (A01):
- Missing authentication checks on sensitive functions
- Privilege escalation possibilities
- Insecure direct object references

DATA EXPOSURE (A02):
- Logging of sensitive data (passwords, PII, tokens)
- Sensitive data in error messages
- Unencrypted sensitive data

INSECURE DESERIALIZATION (A08):
- Use of pickle.loads(), yaml.load() without safe_load, eval() on user input
- Deserializing untrusted data

BROKEN AUTHENTICATION (A07):
- Weak session management
- Insufficient password validation
- Missing rate limiting on auth endpoints

SECURITY MISCONFIGURATION (A05):
- Debug mode enabled in production
- Verbose error messages that expose internals
- Unnecessary permissions

SEVERITY DEFINITIONS:
- critical: Exploitable without authentication, can lead to RCE, data breach, or full system compromise
- warning: Exploitable under certain conditions, can lead to data exposure or privilege escalation
- info: Security best practice violation, may become exploitable in certain contexts

Respond ONLY with a valid JSON array. No explanation, no markdown fences.
Each object:
[
  {
    "title": "Short vulnerability name (max 8 words)",
    "detail": "Explanation of the vulnerability and its attack vector",
    "line": "Line number or null",
    "severity": "critical" | "warning" | "info",
    "fix": "Specific remediation steps"
  }
]

If NO vulnerabilities found, return: []
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


async def run_security_agent(code: str, language: str) -> list:
   
    human_message = f"""Perform a security analysis of this {language} code.
Look for all OWASP Top 10 vulnerabilities and security anti-patterns.

```{language.lower()}
{code}
```

Return ONLY a JSON array of security vulnerabilities."""

    messages = [
        SystemMessage(content=SECURITY_SYSTEM_PROMPT),
        HumanMessage(content=human_message)
    ]

    def _call_llm():
        response = llm.invoke(messages)
        return response.content

    raw_response = await asyncio.to_thread(_call_llm)
    return _parse_json_response(raw_response)