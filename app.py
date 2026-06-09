"""
╔══════════════════════════════════════════════════════════════╗
║              AI CODE REVIEWER — app.py                      ║
║  This is the MAIN ENTRY POINT of the application.           ║
║  It builds the entire Streamlit UI and connects all agents. ║
╚══════════════════════════════════════════════════════════════╝

HOW THIS FILE WORKS:
────────────────────
1. Streamlit renders the page top-to-bottom, re-running on each user interaction.
2. We use st.session_state to remember results between re-runs.
3. The user pastes code → clicks "Review" → three agents run in parallel
   (bug, security, quality) → results are merged → displayed in tabs.

Run with:  streamlit run app.py
"""

import streamlit as st          # The web framework — turns Python into a web app
import asyncio                  # For running multiple agents at the same time (concurrently)
import time                     # To measure how long the review takes
from datetime import datetime   # To timestamp each review
import os
# import os
from dotenv import load_dotenv  # 👈 Added this import

load_dotenv()

if not os.getenv("GROQ_API_KEY"):
    st.set_page_config(page_title="CodeSense AI", page_icon="⚡")
    st.error("⚠️ GROQ_API_KEY is not set. Add it to your .env file or Render environment variables.")
    st.stop()


# ── Our own modules ──────────────────────────────────────────────────────────
from agents.bug_agent      import run_bug_agent        # Finds logic/runtime bugs
from agents.security_agent import run_security_agent   # Finds vulnerabilities
from agents.quality_agent  import run_quality_agent    # Checks code style/quality
from agents.refactor_agent import run_refactor_agent   # Rewrites the code cleaner
from utils.language_detect import detect_language      # Auto-detects Python/JS/etc.
from utils.score_calculator import calculate_score     # Converts findings → 0–100 score
from utils.report_builder  import build_html_report    # Converts results → HTML report


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE CONFIGURATION
#  Must be the FIRST Streamlit call. Sets browser tab title, icon, layout.
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="CodeSense AI — Intelligent Code Review",
    page_icon="⚡",
    layout="wide",          # Use full browser width (not the narrow default)
    initial_sidebar_state="collapsed"
)


# ══════════════════════════════════════════════════════════════════════════════
#  CUSTOM CSS
#  Streamlit's default styling is functional but generic.
#  We inject CSS to create a dark, professional developer-focused theme.
#  Variables at the top make it easy to change the color palette later.
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ── CSS VARIABLES (Design tokens) ─────────────────────────────────────────
   These define the entire color palette. Change --accent to rebrand the app. */
:root {
    --bg-primary:    #0d0f14;   /* Darkest background — main page                */
    --bg-secondary:  #141720;   /* Cards, panels                                  */
    --bg-tertiary:   #1c2030;   /* Input boxes, code blocks                       */
    --bg-hover:      #232840;   /* Hover states                                   */
    --accent:        #6c8fff;   /* Primary brand color — blue-purple              */
    --accent-dim:    #3a4f9a;   /* Darker accent for borders                      */
    --success:       #3dd68c;   /* Green — used for low severity / good scores     */
    --warning:       #f5a623;   /* Amber — used for medium severity               */
    --danger:        #ff5e5e;   /* Red — used for critical issues                  */
    --text-primary:  #e8eaf6;   /* Main readable text                             */
    --text-secondary:#8892b0;   /* Muted labels, descriptions                     */
    --text-code:     #a9b7ff;   /* Color for code snippets inline                 */
    --border:        #2a3050;   /* Subtle dividers                                */
    --radius:        12px;      /* Consistent border-radius across components     */
    --font-mono:     'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
}

/* ── GLOBAL RESET ───────────────────────────────────────────────────────────
   Override Streamlit's white background everywhere */
.stApp, .main, [data-testid="stAppViewContainer"] {
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
}

/* Remove default Streamlit header padding */
.block-container { padding-top: 2rem !important; max-width: 1200px !important; }

/* ── HERO HEADER ────────────────────────────────────────────────────────────
   The big title banner at the top of the page */
.hero-header {
    background: linear-gradient(135deg, #1a1f35 0%, #0d1128 50%, #141020 100%);
    border: 1px solid var(--accent-dim);
    border-radius: 20px;
    padding: 2.5rem 3rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
/* Decorative glowing circle behind the header (pure CSS art) */
.hero-header::before {
    content: '';
    position: absolute;
    top: -50px; right: -50px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(108,143,255,0.15) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-title {
    font-size: 2.4rem;
    font-weight: 800;
    background: linear-gradient(135deg, #ffffff 0%, #6c8fff 60%, #a78bfa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0; letter-spacing: -0.5px;
}
.hero-subtitle {
    color: var(--text-secondary);
    font-size: 1.05rem;
    margin-top: 0.5rem;
}

/* ── CARDS ──────────────────────────────────────────────────────────────────
   Reusable card style for sections */
.card {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.5rem;
    margin-bottom: 1rem;
}

/* ── METRIC BOXES ───────────────────────────────────────────────────────────
   The score display boxes at the top of results */
.metric-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin-bottom: 1.5rem;
}
.metric-box {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.2rem;
    text-align: center;
    transition: border-color 0.2s;
}
.metric-box:hover { border-color: var(--accent-dim); }
.metric-value {
    font-size: 2rem;
    font-weight: 800;
    font-family: var(--font-mono);
}
.metric-label {
    color: var(--text-secondary);
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 0.3rem;
}

/* ── SEVERITY BADGES ────────────────────────────────────────────────────────
   Small colored pill labels: CRITICAL / WARNING / INFO */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.badge-critical { background: rgba(255,94,94,0.15); color: var(--danger);  border: 1px solid rgba(255,94,94,0.3); }
.badge-warning  { background: rgba(245,166,35,0.15); color: var(--warning); border: 1px solid rgba(245,166,35,0.3); }
.badge-info     { background: rgba(108,143,255,0.15); color: var(--accent); border: 1px solid rgba(108,143,255,0.3); }
.badge-good     { background: rgba(61,214,140,0.15); color: var(--success); border: 1px solid rgba(61,214,140,0.3); }

/* ── ISSUE CARDS ────────────────────────────────────────────────────────────
   Each individual finding card in the review results */
.issue-card {
    background: var(--bg-tertiary);
    border-left: 3px solid var(--border);
    border-radius: 0 8px 8px 0;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
    transition: border-left-color 0.2s;
}
.issue-card.critical { border-left-color: var(--danger); }
.issue-card.warning  { border-left-color: var(--warning); }
.issue-card.info     { border-left-color: var(--accent); }
.issue-title  { font-weight: 600; font-size: 0.95rem; margin-bottom: 0.3rem; }
.issue-detail { color: var(--text-secondary); font-size: 0.88rem; line-height: 1.6; }
.issue-line   {
    color: var(--text-code);
    font-family: var(--font-mono);
    font-size: 0.8rem;
    margin-top: 0.4rem;
}
.issue-fix {
    background: rgba(108,143,255,0.08);
    border: 1px solid rgba(108,143,255,0.2);
    border-radius: 6px;
    padding: 0.6rem 0.8rem;
    margin-top: 0.6rem;
    font-size: 0.85rem;
    color: #b8c5ff;
}

/* ── SCORE RING (circular progress) ─────────────────────────────────────────
   SVG circle that shows the overall score visually */
.score-ring-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 1.5rem;
}

/* ── CODE BLOCK OVERRIDE ─────────────────────────────────────────────────── */
.stCodeBlock, code, pre {
    font-family: var(--font-mono) !important;
    background: var(--bg-tertiary) !important;
}

/* ── BUTTON OVERRIDES ────────────────────────────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, var(--accent) 0%, #8b7cf8 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    padding: 0.7rem 2rem !important;
    transition: opacity 0.2s, transform 0.1s !important;
    width: 100% !important;
}
.stButton > button:hover { opacity: 0.9 !important; transform: translateY(-1px) !important; }
.stButton > button:active { transform: translateY(0) !important; }

/* ── TEXTAREA (code input box) ───────────────────────────────────────────── */
.stTextArea textarea {
    background: var(--bg-tertiary) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    font-family: var(--font-mono) !important;
    font-size: 0.88rem !important;
}
.stTextArea textarea:focus { border-color: var(--accent) !important; }

/* ── SELECTBOX / RADIO OVERRIDES ─────────────────────────────────────────── */
.stSelectbox > div > div {
    background: var(--bg-tertiary) !important;
    border-color: var(--border) !important;
    color: var(--text-primary) !important;
}

/* ── TAB OVERRIDES ───────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-secondary) !important;
    border-radius: 10px !important;
    padding: 4px !important;
    gap: 4px !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--text-secondary) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
.stTabs [aria-selected="true"] {
    background: var(--accent) !important;
    color: white !important;
}
.stTabs [data-baseweb="tab-panel"] {
    background: var(--bg-secondary) !important;
    border-radius: 0 0 10px 10px !important;
    padding: 1.5rem !important;
}

/* ── SPINNER OVERRIDE ────────────────────────────────────────────────────── */
.stSpinner > div { border-top-color: var(--accent) !important; }

/* ── PROGRESS BAR ────────────────────────────────────────────────────────── */
.stProgress > div > div { background: var(--accent) !important; }

/* ── HIDE STREAMLIT BRANDING ─────────────────────────────────────────────── */
#MainMenu, footer, header { visibility: hidden; }

/* ── LABEL COLORS ─────────────────────────────────────────────────────────  */
label, .stSelectbox label, .stTextArea label {
    color: var(--text-secondary) !important;
    font-size: 0.85rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}

/* ── DIVIDER ─────────────────────────────────────────────────────────────── */
hr { border-color: var(--border) !important; }

/* ── EXPANDER ────────────────────────────────────────────────────────────── */
.streamlit-expanderHeader {
    background: var(--bg-tertiary) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  SESSION STATE INITIALIZATION
#  Streamlit re-runs the whole script on every interaction.
#  Session state persists values across re-runs (like a simple database).
# ══════════════════════════════════════════════════════════════════════════════
if "review_results" not in st.session_state:
    st.session_state.review_results = None   # Will hold the analysis output dict
if "is_loading" not in st.session_state:
    st.session_state.is_loading = False      # Controls the loading spinner
if "review_time" not in st.session_state:
    st.session_state.review_time = None      # How many seconds the review took


# ══════════════════════════════════════════════════════════════════════════════
#  HELPER: SCORE RING
#  Renders a circular SVG progress ring showing the quality score.
#  score: 0-100, color: CSS color string
# ══════════════════════════════════════════════════════════════════════════════
def render_score_ring(score: int, label: str, color: str) -> str:
    """
    Returns an HTML string with an SVG circle progress indicator.
    
    How the SVG circle math works:
    - radius = 36px → circumference = 2π×36 ≈ 226px
    - stroke-dasharray = circumference (full circle as dashes)
    - stroke-dashoffset = circumference × (1 - score/100)
      → 0 offset = full circle filled, 226 offset = empty
    """
    radius = 36
    circumference = 2 * 3.14159 * radius  # ≈ 226.2
    offset = circumference * (1 - score / 100)   # How much of circle is "empty"
    
    return f"""
    <div class="score-ring-container">
        <svg width="90" height="90" viewBox="0 0 90 90">
            <!-- Background track (dim full circle) -->
            <circle cx="45" cy="45" r="{radius}"
                fill="none" stroke="#2a3050" stroke-width="7"/>
            <!-- Foreground arc (rotated -90° so it starts from top) -->
            <circle cx="45" cy="45" r="{radius}"
                fill="none" stroke="{color}" stroke-width="7"
                stroke-linecap="round"
                stroke-dasharray="{circumference:.1f}"
                stroke-dashoffset="{offset:.1f}"
                transform="rotate(-90 45 45)"/>
            <!-- Score number in the center -->
            <text x="45" y="50" text-anchor="middle"
                fill="{color}" font-size="18" font-weight="800"
                font-family="JetBrains Mono, monospace">{score}</text>
        </svg>
        <div style="color:#8892b0;font-size:0.75rem;text-transform:uppercase;
                    letter-spacing:0.5px;margin-top:0.3rem;">{label}</div>
    </div>
    """


# ══════════════════════════════════════════════════════════════════════════════
#  HELPER: RENDER ISSUES LIST
#  Takes a list of issue dicts and renders them as styled cards.
#  Each issue dict: { title, detail, line, severity, fix }
# ══════════════════════════════════════════════════════════════════════════════
def render_issues(issues: list, empty_message: str = "No issues found."):
    """
    Iterates over the issues list and renders each as a colored card.
    severity must be one of: 'critical', 'warning', 'info'
    """
    if not issues:
        # Green "all clear" message when nothing found
        st.markdown(f"""
        <div style="text-align:center;padding:2rem;color:#3dd68c;">
            <div style="font-size:2rem;">✓</div>
            <div style="margin-top:0.5rem;font-weight:600;">{empty_message}</div>
        </div>""", unsafe_allow_html=True)
        return

    for issue in issues:
        severity = issue.get("severity", "info").lower()
        # Map severity to CSS class and badge class
        badge_class = f"badge-{severity}"
        card_class  = severity

        # Build the optional "suggested fix" section
        fix_html = ""
        if issue.get("fix"):
            fix_html = f'<div class="issue-fix">💡 <strong>Fix:</strong> {issue["fix"]}</div>'

        # Build the optional line number reference
        line_html = ""
        if issue.get("line"):
            line_html = f'<div class="issue-line">📍 Line {issue["line"]}</div>'

        st.markdown(f"""
        <div class="issue-card {card_class}">
            <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.4rem;">
                <span class="badge {badge_class}">{severity}</span>
                <span class="issue-title">{issue.get("title","Issue")}</span>
            </div>
            <div class="issue-detail">{issue.get("detail","")}</div>
            {line_html}
            {fix_html}
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  ASYNC RUNNER
#  Python's asyncio lets us run multiple coroutines simultaneously.
#  This function runs all 3 agents in parallel so the total wait time
#  is ~max(agent_times) instead of sum(agent_times).
# ══════════════════════════════════════════════════════════════════════════════
async def run_all_agents(code: str, language: str) -> dict:
    """
    Runs bug, security, and quality agents concurrently using asyncio.gather().
    asyncio.gather() is like Promise.all() in JavaScript — it fires all tasks
    at once and waits for all to complete.
    
    Returns a dict with keys: bugs, security, quality
    """
    bug_task      = run_bug_agent(code, language)
    security_task = run_security_agent(code, language)
    quality_task  = run_quality_agent(code, language)

    # All three run AT THE SAME TIME here
    bugs, security, quality = await asyncio.gather(
        bug_task, security_task, quality_task
    )
    return {"bugs": bugs, "security": security, "quality": quality}


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN REVIEW FUNCTION
#  Called when user clicks the "Review Code" button.
#  Runs the async agents, then gets a refactored version sequentially.
# ══════════════════════════════════════════════════════════════════════════════
# def perform_review(code: str, language: str):
#     """
#     Orchestrates the full review pipeline:
#     1. Detect language (if 'Auto')
#     2. Run 3 agents concurrently
#     3. Run refactor agent (uses findings from step 2 as context)
#     4. Calculate scores
#     5. Store everything in session state
#     """
#     start_time = time.time()

#     # Step 1: Auto-detect language if user didn't specify
#     if language == "Auto Detect":
#         language = detect_language(code)

#     # Step 2: Run all analysis agents concurrently
#     # asyncio.run() starts a new event loop and blocks until complete
#     agent_results = asyncio.run(run_all_agents(code, language))

#     # Step 3: Run refactor agent (it gets the issues as context so it
#     # knows WHAT to fix, not just that things are wrong)
#     refactored = asyncio.run(
#         run_refactor_agent(code, language, agent_results)
#     )

#     # Step 4: Calculate numeric scores from the findings
#     scores = calculate_score(agent_results)

#     # Step 5: Package everything into one results dict
#     st.session_state.review_results = {
#         "code":       code,
#         "language":   language,
#         "bugs":       agent_results["bugs"],
#         "security":   agent_results["security"],
#         "quality":    agent_results["quality"],
#         "refactored": refactored,
#         "scores":     scores,
#         "timestamp":  datetime.now().strftime("%H:%M:%S")
#     }
#     st.session_state.review_time = round(time.time() - start_time, 1)




async def _full_pipeline(code: str, language: str, run_refactor: bool) -> tuple:
    """Single async pipeline — runs once, avoids double asyncio.run() crash."""
    agent_results = await run_all_agents(code, language)
    refactored = {}
    if run_refactor:
        refactored = await run_refactor_agent(code, language, agent_results)
    return agent_results, refactored


def perform_review(code: str, language: str, run_refactor: bool = True):
    """
    Orchestrates the full review pipeline with error handling.
    """
    try:
        start_time = time.time()

        if language == "Auto Detect":
            language = detect_language(code)

        # Single asyncio.run() — avoids RuntimeError on hosted environments
        agent_results, refactored = asyncio.run(
            _full_pipeline(code, language, run_refactor)
        )

        scores = calculate_score(agent_results)

        st.session_state.review_results = {
            "code":       code,
            "language":   language,
            "bugs":       agent_results["bugs"],
            "security":   agent_results["security"],
            "quality":    agent_results["quality"],
            "refactored": refactored,
            "scores":     scores,
            "timestamp":  datetime.now().strftime("%H:%M:%S")
        }
        st.session_state.review_time = round(time.time() - start_time, 1)

    except Exception as e:
        st.error(f"❌ Analysis failed: {str(e)}. Check your API key or try again.")



# ══════════════════════════════════════════════════════════════════════════════
#  UI — HERO HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero-header">
    <div class="hero-title">⚡ CodeSense AI</div>
    <div class="hero-subtitle">
        Intelligent multi-agent code review · Bugs · Security · Quality · Refactoring
    </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  UI — TWO-COLUMN LAYOUT
#  Left: code input + options
#  Right: results display
# ══════════════════════════════════════════════════════════════════════════════
left_col, right_col = st.columns([1, 1.4], gap="large")

# ─────────────────────────────────────────────────────
#  LEFT COLUMN — Input Panel
# ─────────────────────────────────────────────────────
with left_col:
    st.markdown('<div class="card">', unsafe_allow_html=True)

    # Language selector — 'Auto Detect' uses our language_detect utility
    language = st.selectbox(
        "Language",
        ["Auto Detect", "Python", "JavaScript", "TypeScript",
         "Java", "C++", "Go", "Rust", "PHP", "Ruby"],
        help="Select your programming language or let AI detect it automatically"
    )

    # The main code input area
    # height=400 gives comfortable space for medium-sized functions
#     code_input = st.text_area(
#         "Paste your code here",
#         height=400,
#         placeholder="""# Example: paste any code snippet
# def calculate_discount(price, discount):
#     result = price / discount   # Bug: division, not subtraction
#     password = "admin123"       # Security: hardcoded credential
#     return result
# """,
#         help="Paste any code snippet — functions, classes, or full files"
#     )



# Pre-fill textarea if a sample was clicked
    default_code = st.session_state.pop("sample_code", "")

    code_input = st.text_area(
        "Paste your code here",
        value=default_code,
        height=400,
        placeholder="""# Example: paste any code snippet

def calculate_discount(price, discount):
    result = price / discount   # Bug: division, not subtraction
    password = "admin123"       # Security: hardcoded credential
    return result
""",
        help="Paste any code snippet — functions, classes, or full files"
    )


    # Options row — two toggles side by side
    opt_col1, opt_col2 = st.columns(2)
    with opt_col1:
        # If True, refactor agent runs and produces cleaned code
        show_refactor = st.checkbox("Generate refactored code", value=True)
    with opt_col2:
        # If True, we display a downloadable HTML report at the end
        show_report = st.checkbox("Export HTML report", value=False)

    st.markdown("</div>", unsafe_allow_html=True)

    # ── REVIEW BUTTON ──────────────────────────────────────────────────────
    # if st.button("⚡ Review Code", type="primary"):
    #     if not code_input.strip():
    #         st.error("Please paste some code before reviewing.")
    #     elif len(code_input.strip()) < 20:
    #         st.warning("Code seems too short. Paste a real function or class.")
    #     else:
    #         # Show a spinner while the agents are working
    #         with st.spinner("Running multi-agent analysis..."):
    #             perform_review(code_input, language)
    #         st.rerun()   # Trigger a re-render to show results


    if st.button("⚡ Review Code", type="primary"):
        if not code_input.strip():
            st.error("Please paste some code before reviewing.")
        elif len(code_input.strip()) < 20:
            st.warning("Code seems too short. Paste a real function or class.")
        elif len(code_input.splitlines()) > 300:
            st.warning("⚠️ Code exceeds 300 lines. Trim it down for best results — the AI has a context limit.")
        else:
            with st.spinner("Running multi-agent analysis..."):
                perform_review(code_input, language, show_refactor)
            st.rerun()

    # ── SAMPLE CODE BUTTONS ──────────────────────────────────────────────
    # These let users try the app without typing any code
    st.markdown("#### Try a sample")
    s1, s2, s3 = st.columns(3)

    SAMPLE_PYTHON = '''import sqlite3

# BAD: Direct SQL injection vulnerability
def get_user(username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE name = '" + username + "'"
    cursor.execute(query)
    return cursor.fetchall()

# BAD: Hardcoded password  
DB_PASSWORD = "super_secret_123"

def login(user, pwd):
    if pwd == DB_PASSWORD:
        return True
    return False

# BAD: No error handling, no input validation
def divide(a, b):
    return a / b
'''

    SAMPLE_JS = '''// JavaScript: async issues + security problems
const API_KEY = "sk-live-abc123secret";  // Hardcoded secret

async function fetchUser(id) {
    // Missing await — returns a Promise, not the data
    const response = fetch(`/api/users/${id}`);
    const data = response.json();
    
    // XSS vulnerability: directly injecting user content into DOM
    document.getElementById("profile").innerHTML = data.bio;
    
    return data;
}

// Memory leak: interval never cleared
function startPolling() {
    setInterval(() => {
        fetchUser(1);
    }, 1000);
}
'''

    SAMPLE_JAVA = '''import java.io.*;

public class FileProcessor {
    // Bad: static mutable state (not thread-safe)
    static List<String> results = new ArrayList<>();
    
    public String readFile(String path) throws Exception {
        // Bad: resource leak — FileReader never closed
        FileReader fr = new FileReader(path);
        BufferedReader br = new BufferedReader(fr);
        String line = br.readLine();
        // Missing: br.close() or try-with-resources
        return line;
    }
    
    // Bad: catches Exception, hides all errors silently
    public void process(String data) {
        try {
            results.add(data.toUpperCase());
        } catch (Exception e) {
            // Swallowed exception — debugging nightmare
        }
    }
}
'''

    with s1:
        if st.button("Python", use_container_width=True):
            st.session_state["sample_code"] = SAMPLE_PYTHON
            st.rerun()
    with s2:
        if st.button("JavaScript", use_container_width=True):
            st.session_state["sample_code"] = SAMPLE_JS
            st.rerun()
    with s3:
        if st.button("Java", use_container_width=True):
            st.session_state["sample_code"] = SAMPLE_JAVA
            st.rerun()

    # If a sample was selected in a previous run, pre-fill the textarea
    # (Streamlit doesn't support direct textarea value injection after render,
    # so we show it as a read-only preview instead)
    # if "sample_code" in st.session_state:
    #     st.info("Sample loaded! Copy the code above into the input box.")
    #     st.code(st.session_state["sample_code"])
    if "sample_code" in st.session_state:        # line 644 — DELETE
        st.info("Sample loaded! Copy the code above into the input box.")  # line 645 — DELETE
        st.code(st.session_state["sample_code"])  # line 646 — DELETE

# ─────────────────────────────────────────────────────
#  RIGHT COLUMN — Results Panel
# ─────────────────────────────────────────────────────
with right_col:
    results = st.session_state.review_results

    if results is None:
        # ── EMPTY STATE (no review yet) ──────────────────────────────────
        st.markdown("""
        <div style="text-align:center;padding:4rem 2rem;color:#4a5568;">
            <div style="font-size:3rem;margin-bottom:1rem;">🔍</div>
            <div style="font-size:1.2rem;font-weight:600;color:#8892b0;">
                Waiting for code...
            </div>
            <div style="margin-top:0.5rem;font-size:0.9rem;">
                Paste code on the left and click Review
            </div>
            <div style="margin-top:2rem;display:grid;grid-template-columns:1fr 1fr;
                        gap:1rem;max-width:360px;margin-left:auto;margin-right:auto;">
                <div style="background:#141720;border:1px solid #2a3050;
                            border-radius:10px;padding:1rem;text-align:left;">
                    <div style="color:#ff5e5e;font-size:1.2rem;">🐛</div>
                    <div style="font-weight:600;margin-top:0.3rem;font-size:0.9rem;">Bug Detection</div>
                    <div style="color:#8892b0;font-size:0.8rem;margin-top:0.2rem;">Logic, runtime & type errors</div>
                </div>
                <div style="background:#141720;border:1px solid #2a3050;
                            border-radius:10px;padding:1rem;text-align:left;">
                    <div style="color:#f5a623;font-size:1.2rem;">🔒</div>
                    <div style="font-weight:600;margin-top:0.3rem;font-size:0.9rem;">Security Scan</div>
                    <div style="color:#8892b0;font-size:0.8rem;margin-top:0.2rem;">OWASP Top 10 vulnerabilities</div>
                </div>
                <div style="background:#141720;border:1px solid #2a3050;
                            border-radius:10px;padding:1rem;text-align:left;">
                    <div style="color:#6c8fff;font-size:1.2rem;">📊</div>
                    <div style="font-weight:600;margin-top:0.3rem;font-size:0.9rem;">Quality Grading</div>
                    <div style="color:#8892b0;font-size:0.8rem;margin-top:0.2rem;">SOLID, complexity, style</div>
                </div>
                <div style="background:#141720;border:1px solid #2a3050;
                            border-radius:10px;padding:1rem;text-align:left;">
                    <div style="color:#3dd68c;font-size:1.2rem;">✨</div>
                    <div style="font-weight:600;margin-top:0.3rem;font-size:0.9rem;">Auto Refactor</div>
                    <div style="color:#8892b0;font-size:0.8rem;margin-top:0.2rem;">Clean rewrite with fixes</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        # ── RESULTS DISPLAY ────────────────────────────────────────────────
        scores = results["scores"]

        # ── Review metadata bar ──────────────────────────────────────────
        review_time = st.session_state.review_time or "?"
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:1rem;
                    margin-bottom:1rem;font-size:0.82rem;color:#8892b0;">
            <span>🕐 Reviewed at {results['timestamp']}</span>
            <span>·</span>
            <span>⏱ {review_time}s</span>
            <span>·</span>
            <span>🔤 {results['language']}</span>
            <span>·</span>
            <span>{len(results['code'].splitlines())} lines</span>
        </div>
        """, unsafe_allow_html=True)

        # ── Score rings row ──────────────────────────────────────────────
        # Four score circles: Overall, Security, Quality, Bugs
        overall_score   = scores["overall"]
        security_score  = scores["security"]
        quality_score   = scores["quality"]
        bug_score       = scores["bugs"]

        # Pick color based on score range
        def score_color(s):
            if s >= 80: return "#3dd68c"   # Green  — good
            if s >= 60: return "#f5a623"   # Amber  — mediocre
            return "#ff5e5e"               # Red    — poor

        sc1, sc2, sc3, sc4 = st.columns(4)
        with sc1:
            st.markdown(render_score_ring(overall_score,  "Overall",  score_color(overall_score)),  unsafe_allow_html=True)
        with sc2:
            st.markdown(render_score_ring(bug_score,      "Bugs",     score_color(bug_score)),      unsafe_allow_html=True)
        with sc3:
            st.markdown(render_score_ring(security_score, "Security", score_color(security_score)), unsafe_allow_html=True)
        with sc4:
            st.markdown(render_score_ring(quality_score,  "Quality",  score_color(quality_score)),  unsafe_allow_html=True)

        st.divider()

        # ── Tabs: one per analysis area ──────────────────────────────────
        # Count issues for tab labels
        n_bugs     = len(results["bugs"])
        n_security = len(results["security"])
        n_quality  = len(results["quality"])

        tab_bugs, tab_security, tab_quality, tab_refactor = st.tabs([
            f"🐛 Bugs ({n_bugs})",
            f"🔒 Security ({n_security})",
            f"📊 Quality ({n_quality})",
            "✨ Refactored"
        ])

        # ── Bugs Tab ─────────────────────────────────────────────────────
        with tab_bugs:
            if n_bugs == 0:
                render_issues([], "No bugs detected!")
            else:
                st.markdown(f"**{n_bugs} issue(s) found** — review each carefully.")
                render_issues(results["bugs"])

        # ── Security Tab ─────────────────────────────────────────────────
        with tab_security:
            if n_security == 0:
                render_issues([], "No security vulnerabilities found!")
            else:
                st.markdown(f"**{n_security} vulnerability(ies) found** — address critical ones immediately.")
                render_issues(results["security"])

        # ── Quality Tab ──────────────────────────────────────────────────
        with tab_quality:
            if n_quality == 0:
                render_issues([], "Code quality looks great!")
            else:
                st.markdown(f"**{n_quality} quality suggestion(s)** — these improve maintainability.")
                render_issues(results["quality"])

        # ── Refactored Code Tab ──────────────────────────────────────────
        with tab_refactor:
            refactored = results.get("refactored", {})
            if refactored.get("code"):
                st.markdown("**Refactored version** — all issues addressed, clean and production-ready:")
                # st.code renders the code with syntax highlighting
                st.code(refactored["code"], language=results["language"].lower())

                if refactored.get("summary"):
                    with st.expander("What changed?"):
                        # Summary is a list of change descriptions
                        for change in refactored["summary"]:
                            st.markdown(f"- {change}")
            else:
                st.info("Enable 'Generate refactored code' and re-run to see the cleaned version.")

        # ── Export HTML Report ────────────────────────────────────────────
        if show_report:
            st.divider()
            html_report = build_html_report(results)
            st.download_button(
                label="📥 Download Full Report",
                data=html_report,
                file_name=f"code_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                mime="text/html",
                use_container_width=True
            )