"""
╔══════════════════════════════════════════════════════════════╗
║             REPORT BUILDER — report_builder.py              ║
╚══════════════════════════════════════════════════════════════╝

WHAT THIS DOES:
───────────────
Converts the full review results dict into a self-contained
HTML file that users can download, share, and open in any browser.

WHY A SEPARATE REPORT?
──────────────────────
The Streamlit UI is interactive but session-based — close the
browser tab and the review is gone. The HTML report is a
permanent, shareable artifact of the code review.

"Self-contained" means:
  - All CSS is inline (no external stylesheet files needed)
  - All data is embedded in the HTML
  - One file, opens anywhere

USE CASE: Portfolio projects, code review documentation,
team sharing, audit trails.
"""

from datetime import datetime


def _severity_color(severity: str) -> str:
    """Returns a hex color for a given severity level."""
    return {
        "critical": "#ff5e5e",
        "warning":  "#f5a623",
        "info":     "#6c8fff",
    }.get(severity.lower(), "#8892b0")


def _issues_to_html(issues: list, category_name: str) -> str:
    """
    Converts a list of issue dicts into an HTML section.
    Each issue becomes a styled card with severity badge.
    """
    if not issues:
        return f"""
        <div class="no-issues">
            <span class="checkmark">✓</span> No {category_name.lower()} found
        </div>"""

    html_parts = []
    for issue in issues:
        severity  = issue.get("severity", "info").lower()
        color     = _severity_color(severity)
        title     = issue.get("title", "Issue")
        detail    = issue.get("detail", "")
        line      = issue.get("line")
        fix       = issue.get("fix", "")

        line_html = f'<div class="line-ref">📍 Line {line}</div>' if line else ""
        fix_html  = f'<div class="fix-box">💡 <strong>Fix:</strong> {fix}</div>' if fix else ""

        html_parts.append(f"""
        <div class="issue-card" style="border-left-color: {color};">
            <div class="issue-header">
                <span class="badge" style="background:{color}20;color:{color};
                      border:1px solid {color}40;">{severity.upper()}</span>
                <span class="issue-title">{title}</span>
            </div>
            <div class="issue-detail">{detail}</div>
            {line_html}
            {fix_html}
        </div>""")

    return "\n".join(html_parts)


def build_html_report(results: dict) -> str:
    """
    Builds a complete self-contained HTML report from review results.
    
    Args:
        results: The full review results dict from session state
    
    Returns:
        HTML string — the entire downloadable report file
    """
    scores    = results.get("scores", {})
    language  = results.get("language", "Unknown")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    code      = results.get("code", "")
    n_lines   = len(code.splitlines())

    bugs_html      = _issues_to_html(results.get("bugs",     []), "Bugs")
    security_html  = _issues_to_html(results.get("security", []), "Security Issues")
    quality_html   = _issues_to_html(results.get("quality",  []), "Quality Issues")

    refactored     = results.get("refactored", {})
    refactor_code  = refactored.get("code", "") if refactored else ""
    refactor_summary = refactored.get("summary", []) if refactored else []

    summary_items = "\n".join(
        f"<li>{change}</li>" for change in refactor_summary
    ) if refactor_summary else "<li>No summary available.</li>"

    refactor_section = f"""
    <div class="refactor-code">
        <pre><code>{refactor_code}</code></pre>
    </div>
    <div class="changes-list">
        <h4>Changes made:</h4>
        <ul>{summary_items}</ul>
    </div>
    """ if refactor_code else "<p>Refactored code was not generated.</p>"

    overall_score  = scores.get("overall",  0)
    bug_score      = scores.get("bugs",     0)
    security_score = scores.get("security", 0)
    quality_score  = scores.get("quality",  0)

    def score_label(s):
        if s >= 80: return ("Good",    "#3dd68c")
        if s >= 60: return ("Fair",    "#f5a623")
        return              ("Poor",    "#ff5e5e")

    o_label, o_color = score_label(overall_score)
    b_label, b_color = score_label(bug_score)
    s_label, s_color = score_label(security_score)
    q_label, q_color = score_label(quality_score)

    # ── Full HTML document ───────────────────────────────────────────────
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CodeSense AI — Code Review Report</title>
<style>
  /* Self-contained styles — no external dependencies */
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, 'Segoe UI', sans-serif;
    background: #0d0f14;
    color: #e8eaf6;
    line-height: 1.6;
    padding: 2rem;
  }}
  .container {{ max-width: 900px; margin: 0 auto; }}
  .header {{
    background: linear-gradient(135deg, #1a1f35, #0d1128);
    border: 1px solid #3a4f9a;
    border-radius: 16px;
    padding: 2rem;
    margin-bottom: 2rem;
  }}
  .header h1 {{ font-size: 1.8rem; color: #6c8fff; }}
  .header .meta {{
    color: #8892b0;
    font-size: 0.85rem;
    margin-top: 0.5rem;
    display: flex; gap: 1.5rem; flex-wrap: wrap;
  }}
  .scores-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin-bottom: 2rem;
  }}
  .score-box {{
    background: #141720;
    border: 1px solid #2a3050;
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
  }}
  .score-value {{
    font-size: 2.2rem;
    font-weight: 800;
    font-family: 'Courier New', monospace;
  }}
  .score-label {{
    color: #8892b0;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 0.2rem;
  }}
  .score-grade {{
    font-size: 0.8rem;
    font-weight: 600;
    margin-top: 0.3rem;
  }}
  .section {{
    background: #141720;
    border: 1px solid #2a3050;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
  }}
  .section h2 {{
    font-size: 1.1rem;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #2a3050;
    color: #b8c5ff;
  }}
  .issue-card {{
    background: #1c2030;
    border-left: 3px solid #2a3050;
    border-radius: 0 8px 8px 0;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
  }}
  .issue-header {{
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 0.4rem;
  }}
  .badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.7rem;
    font-weight: 700;
  }}
  .issue-title {{ font-weight: 600; font-size: 0.95rem; }}
  .issue-detail {{ color: #8892b0; font-size: 0.88rem; margin-top: 0.2rem; }}
  .line-ref {{
    color: #a9b7ff;
    font-family: monospace;
    font-size: 0.8rem;
    margin-top: 0.3rem;
  }}
  .fix-box {{
    background: rgba(108,143,255,0.08);
    border: 1px solid rgba(108,143,255,0.2);
    border-radius: 6px;
    padding: 0.5rem 0.8rem;
    margin-top: 0.5rem;
    font-size: 0.85rem;
    color: #b8c5ff;
  }}
  .no-issues {{
    color: #3dd68c;
    font-weight: 600;
    padding: 0.5rem 0;
  }}
  .checkmark {{ font-size: 1.1rem; }}
  .refactor-code {{
    background: #1c2030;
    border-radius: 8px;
    padding: 1.2rem;
    overflow-x: auto;
    margin-bottom: 1rem;
  }}
  .refactor-code pre {{
    font-family: 'Courier New', monospace;
    font-size: 0.85rem;
    color: #e8eaf6;
    white-space: pre-wrap;
  }}
  .changes-list h4 {{ color: #8892b0; margin-bottom: 0.5rem; }}
  .changes-list ul {{ padding-left: 1.5rem; color: #b8c5ff; font-size: 0.9rem; }}
  .changes-list li {{ margin-bottom: 0.3rem; }}
  .original-code {{
    background: #1c2030;
    border-radius: 8px;
    padding: 1.2rem;
    overflow-x: auto;
  }}
  .original-code pre {{
    font-family: 'Courier New', monospace;
    font-size: 0.85rem;
    color: #8892b0;
    white-space: pre-wrap;
  }}
  .footer {{
    text-align: center;
    color: #4a5568;
    font-size: 0.8rem;
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid #2a3050;
  }}
</style>
</head>
<body>
<div class="container">

  <!-- Header -->
  <div class="header">
    <h1>⚡ CodeSense AI — Code Review Report</h1>
    <div class="meta">
      <span>📅 {timestamp}</span>
      <span>🔤 {language}</span>
      <span>📄 {n_lines} lines</span>
      <span>Overall score: <strong style="color:{o_color}">{overall_score}/100</strong></span>
    </div>
  </div>

  <!-- Scores -->
  <div class="scores-grid">
    <div class="score-box">
      <div class="score-value" style="color:{o_color}">{overall_score}</div>
      <div class="score-label">Overall</div>
      <div class="score-grade" style="color:{o_color}">{o_label}</div>
    </div>
    <div class="score-box">
      <div class="score-value" style="color:{b_color}">{bug_score}</div>
      <div class="score-label">Bugs</div>
      <div class="score-grade" style="color:{b_color}">{b_label}</div>
    </div>
    <div class="score-box">
      <div class="score-value" style="color:{s_color}">{security_score}</div>
      <div class="score-label">Security</div>
      <div class="score-grade" style="color:{s_color}">{s_label}</div>
    </div>
    <div class="score-box">
      <div class="score-value" style="color:{q_color}">{quality_score}</div>
      <div class="score-label">Quality</div>
      <div class="score-grade" style="color:{q_color}">{q_label}</div>
    </div>
  </div>

  <!-- Bugs -->
  <div class="section">
    <h2>🐛 Bug Analysis ({len(results.get('bugs', []))} issues)</h2>
    {bugs_html}
  </div>

  <!-- Security -->
  <div class="section">
    <h2>🔒 Security Analysis ({len(results.get('security', []))} issues)</h2>
    {security_html}
  </div>

  <!-- Quality -->
  <div class="section">
    <h2>📊 Quality Analysis ({len(results.get('quality', []))} issues)</h2>
    {quality_html}
  </div>

  <!-- Refactored Code -->
  <div class="section">
    <h2>✨ Refactored Code</h2>
    {refactor_section}
  </div>

  <!-- Original Code -->
  <div class="section">
    <h2>📋 Original Code</h2>
    <div class="original-code">
      <pre><code>{code}</code></pre>
    </div>
  </div>

  <div class="footer">
    Generated by CodeSense AI · Powered by GPT-4o + LangChain
  </div>
</div>
</body>
</html>"""