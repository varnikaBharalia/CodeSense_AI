
import re

LANGUAGE_PATTERNS = {
    "Python": [
        (r'\bdef\s+\w+\s*\(',  3),        
        (r'\bimport\s+\w+',    2),       
        (r'\bfrom\s+\w+\s+import', 3),   
        (r':\s*$',             1),
        (r'\bprint\s*\(',      2),        
        (r'\bself\b',          3),       
        (r'\bNone\b',          2),       
        (r'\bTrue\b|\bFalse\b', 2),      
        (r'f".*?"',            2),      
        (r'#.*$',              1),        
    ],
    "JavaScript": [
        (r'\bconst\s+\w+\s*=', 3),        
        (r'\blet\s+\w+\s*=',   3),        
        (r'\bvar\s+\w+\s*=',   2),        
        (r'=>',                 3),        
        (r'\bconsole\.log\b',  3),       
        (r'\bdocument\.',      3),       
        (r'===',               2),       
        (r'\bfunction\s+\w+\(', 2),      
        (r'\.then\(',          2),       
        (r'\basync\s+function', 3),       
    ],
    "TypeScript": [
        (r':\s*string\b',      3),       
        (r':\s*number\b',      3),       
        (r':\s*boolean\b',     3),      
        (r'\binterface\s+\w+', 4),      
        (r'\btype\s+\w+\s*=',  3),        
        (r'<T>',               2),       
        (r'\bReadonly<',       3),        
        (r':\s*void\b',        2),       
    ],
    "Java": [
        (r'\bpublic\s+class\b', 4),      
        (r'\bprivate\s+\w+\s+\w+', 3),   
        (r'\bSystem\.out\.',   4),        
        (r'\bString\[\]\s+args', 4),     
        (r'\bnew\s+\w+\(',     2),       
        (r'@Override',         3),      
        (r'\bimport\s+java\.',  4),      
        (r'\bvoid\s+\w+\s*\(', 2),        
    ],
    "C++": [
        (r'#include\s*<',      4),       
        (r'\bstd::',           4),        
        (r'\bint\s+main\s*\(', 4),      
        (r'\bcout\s*<<',       4),     
        (r'\bnamespace\s+\w+', 3),       
        (r'\bvector<',         3),      
        (r'->',                1),       
        (r'::\w+',             2),        
    ],
    "Go": [
        (r'\bfunc\s+\w+\s*\(', 4),      
        (r'\bpackage\s+\w+',   4),       
        (r':=',                3),       
        (r'\bfmt\.',           3),        
        (r'\bgoroutine\b',     4),   
        (r'\bchan\b',          3),      
        (r'\bgo\s+func\b',     4),       
    ],
    "Rust": [
        (r'\bfn\s+\w+\s*\(',   4),       
        (r'\blet\s+mut\b',     4),      
        (r'\bimpl\s+\w+',      4),       
        (r'\buse\s+std::',     4),     
        (r'->.*?\{',           2),       
        (r'\bunwrap\(\)',       3),        
        (r'\bSome\(|\bNone\b', 2),       
    ],
    "PHP": [
        (r'\$\w+',             3),
        (r'<\?php',            5),      
        (r'\becho\b',          3),      
        (r'->',                1),       
        (r'\bfunction\s+\w+\(', 2),       
        (r'\barray\s*\(',      3),        
    ],
    "Ruby": [
        (r'\bdef\s+\w+',       3),        
        (r'\bend\b',           3),        
        (r'\bputs\b',          4),        
        (r'\bdo\s*\|',         3),        
        (r'\battr_accessor\b', 5),        
        (r'\.each\s*\{',       3),        
    ],
}


def detect_language(code: str) -> str:
    
    try:
        from pygments.lexers import guess_lexer
        from pygments.util   import ClassNotFound
        
        lexer = guess_lexer(code)
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
        pass 

    scores = {}   
    
    for language, patterns in LANGUAGE_PATTERNS.items():
        score = 0
        for pattern, weight in patterns:
            matches = len(re.findall(pattern, code, re.MULTILINE))
            score += matches * weight
        if score > 0:
            scores[language] = score

    if not scores:
        return "Python"   

    return max(scores, key=scores.get)