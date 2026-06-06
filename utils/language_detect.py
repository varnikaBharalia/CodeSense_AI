"""
╔══════════════════════════════════════════════════════════════╗
║          LANGUAGE DETECTION — language_detect.py            ║
╚══════════════════════════════════════════════════════════════╝

WHAT THIS DOES:
───────────────
When the user selects "Auto Detect", this module analyzes the
code and guesses the programming language.

APPROACH — Two-stage detection:
────────────────────────────────
Stage 1: KEYWORD/PATTERN HEURISTICS (fast, no API call needed)
  - Each language has unique syntax patterns
  - Python: def, import, :, indentation
  - JavaScript: const/let/var, =>, function, ;
  - Java: public class, void, System.out
  - etc.

Stage 2: PYGMENTS (if installed, more accurate)
  - Pygments is a Python syntax highlighter library
  - It has built-in language detection (lexer guessing)
  - Much more accurate than simple patterns
  - We use it as a fallback/confirmation

WHY LANGUAGE DETECTION MATTERS:
────────────────────────────────
The agent prompts say "analyze this {language} code". The language
name in the prompt helps the LLM apply the right mental model:
  - Python-specific issues: missing type hints, PEP 8 violations
  - JavaScript-specific: async/await mistakes, prototype issues
  - Java-specific: try-with-resources, checked exceptions
Without language info, the LLM still works but is less precise.
"""

import re


# ══════════════════════════════════════════════════════════════════════════════
#  PATTERN-BASED DETECTION
#  Each language has a list of regex patterns and keywords.
#  We score each language by how many patterns match.
# ══════════════════════════════════════════════════════════════════════════════

# Maps language name → list of (pattern, weight) tuples
# Higher weight = stronger signal for that language
LANGUAGE_PATTERNS = {
    "Python": [
        (r'\bdef\s+\w+\s*\(',  3),        # def function():
        (r'\bimport\s+\w+',    2),        # import module
        (r'\bfrom\s+\w+\s+import', 3),    # from module import
        (r':\s*$',             1),        # line ending with colon
        (r'\bprint\s*\(',      2),        # print()
        (r'\bself\b',          3),        # self parameter
        (r'\bNone\b',          2),        # None (not null, not nil)
        (r'\bTrue\b|\bFalse\b', 2),       # True/False (not true/false)
        (r'f".*?"',            2),        # f-strings
        (r'#.*$',              1),        # Python comments
    ],
    "JavaScript": [
        (r'\bconst\s+\w+\s*=', 3),        # const x =
        (r'\blet\s+\w+\s*=',   3),        # let x =
        (r'\bvar\s+\w+\s*=',   2),        # var x =
        (r'=>',                 3),        # arrow functions
        (r'\bconsole\.log\b',  3),        # console.log
        (r'\bdocument\.',      3),        # document.getElementById etc
        (r'===',               2),        # strict equality
        (r'\bfunction\s+\w+\(', 2),       # function name()
        (r'\.then\(',          2),        # promise chaining
        (r'\basync\s+function', 3),       # async function
    ],
    "TypeScript": [
        (r':\s*string\b',      3),        # : string type annotation
        (r':\s*number\b',      3),        # : number type annotation
        (r':\s*boolean\b',     3),        # : boolean type annotation
        (r'\binterface\s+\w+', 4),        # interface declaration
        (r'\btype\s+\w+\s*=',  3),        # type alias
        (r'<T>',               2),        # generics
        (r'\bReadonly<',       3),        # TypeScript utility types
        (r':\s*void\b',        2),        # : void return type
    ],
    "Java": [
        (r'\bpublic\s+class\b', 4),       # public class
        (r'\bprivate\s+\w+\s+\w+', 3),   # private type variable
        (r'\bSystem\.out\.',   4),        # System.out.println
        (r'\bString\[\]\s+args', 4),      # main method signature
        (r'\bnew\s+\w+\(',     2),        # new Object()
        (r'@Override',         3),        # annotations
        (r'\bimport\s+java\.',  4),       # Java standard library imports
        (r'\bvoid\s+\w+\s*\(', 2),        # void method
    ],
    "C++": [
        (r'#include\s*<',      4),        # #include <iostream>
        (r'\bstd::',           4),        # std::cout, std::vector
        (r'\bint\s+main\s*\(', 4),        # int main()
        (r'\bcout\s*<<',       4),        # cout << 
        (r'\bnamespace\s+\w+', 3),        # namespace declaration
        (r'\bvector<',         3),        # std::vector
        (r'->',                1),        # pointer arrow
        (r'::\w+',             2),        # scope resolution
    ],
    "Go": [
        (r'\bfunc\s+\w+\s*\(', 4),        # func name()
        (r'\bpackage\s+\w+',   4),        # package main
        (r':=',                3),        # short variable declaration
        (r'\bfmt\.',           3),        # fmt.Println
        (r'\bgoroutine\b',     4),        # goroutines
        (r'\bchan\b',          3),        # channels
        (r'\bgo\s+func\b',     4),        # go func()
    ],
    "Rust": [
        (r'\bfn\s+\w+\s*\(',   4),        # fn main()
        (r'\blet\s+mut\b',     4),        # let mut x
        (r'\bimpl\s+\w+',      4),        # impl block
        (r'\buse\s+std::',     4),        # use std::io
        (r'->.*?\{',           2),        # return type arrow
        (r'\bunwrap\(\)',       3),        # .unwrap()
        (r'\bSome\(|\bNone\b', 2),        # Option type
    ],
    "PHP": [
        (r'\$\w+',             3),        # PHP variables start with $
        (r'<\?php',            5),        # PHP opening tag
        (r'\becho\b',          3),        # echo statement
        (r'->',                1),        # object arrow (not unique)
        (r'\bfunction\s+\w+\(', 2),       # function declaration
        (r'\barray\s*\(',      3),        # array() (old style)
    ],
    "Ruby": [
        (r'\bdef\s+\w+',       3),        # def method
        (r'\bend\b',           3),        # end keyword
        (r'\bputs\b',          4),        # puts (Ruby print)
        (r'\bdo\s*\|',         3),        # block with |variables|
        (r'\battr_accessor\b', 5),        # Ruby accessor
        (r'\.each\s*\{',       3),        # .each do block
    ],
}


def detect_language(code: str) -> str:
    """
    Detects the programming language of a code snippet.
    
    Algorithm:
    1. Try pygments lexer guessing (most accurate if installed)
    2. Fall back to pattern scoring
    3. Default to "Python" if nothing matches
    
    Args:
        code: Source code string
    
    Returns:
        Language name string (e.g., "Python", "JavaScript")
    """
    # ── Stage 1: Try pygments (most accurate) ────────────────────────────
    try:
        from pygments.lexers import guess_lexer
        from pygments.util   import ClassNotFound
        
        lexer = guess_lexer(code)
        # Map pygments lexer names to our language names
        PYGMENTS_MAP = {
            "Python":     "Python",
            "Python 3":   "Python",
            "JavaScript": "JavaScript",
            "TypeScript": "TypeScript",
            "Java":       "Java",
            "C++":        "C++",
            "Go":         "Go",
            "Rust":       "Rust",
            "PHP":        "PHP",
            "Ruby":       "Ruby",
        }
        lexer_name = lexer.name
        for key, value in PYGMENTS_MAP.items():
            if key.lower() in lexer_name.lower():
                return value
    except (ImportError, Exception):
        pass  # pygments not installed or failed — fall through to patterns

    # ── Stage 2: Pattern scoring ─────────────────────────────────────────
    scores = {}   # language → total score
    
    for language, patterns in LANGUAGE_PATTERNS.items():
        score = 0
        for pattern, weight in patterns:
            # Count how many times the pattern appears
            matches = len(re.findall(pattern, code, re.MULTILINE))
            score += matches * weight
        if score > 0:
            scores[language] = score

    if not scores:
        return "Python"   # Safe default

    # Return the language with the highest score
    return max(scores, key=scores.get)