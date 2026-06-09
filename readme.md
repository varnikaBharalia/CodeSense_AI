# ⚡ CodeSense AI

> An Intelligent Multi-Agent AI Code Review Platform that automatically detects bugs, security vulnerabilities, code quality issues, and generates refactored code using LLM-powered analysis.

🌐 **Live Demo:** https://codesense-ai-0nm6.onrender.com/

📂 **Repository:** https://github.com/varnikaBharalia/CodeSense_AI

---

# 📖 Overview

CodeSense AI is an AI-powered code review platform designed to help developers write cleaner, safer, and more maintainable code.

The application uses a **multi-agent architecture**, where each AI agent specializes in a different aspect of code review:

* 🐞 Bug Detection Agent
* 🔒 Security Analysis Agent
* 📊 Code Quality Agent
* ♻️ Refactoring Agent

These agents analyze source code independently and generate actionable feedback, risk assessments, quality scores, and improved code suggestions.

---

# ✨ Features

## 🐞 Bug Detection

Identifies:

* Logic errors
* Runtime risks
* Potential crashes
* Edge-case failures
* Incorrect programming patterns

---

## 🔒 Security Analysis

Detects common security vulnerabilities including:

* SQL Injection
* Command Injection
* Hardcoded Credentials
* Insecure Deserialization
* Broken Authentication
* Sensitive Data Exposure
* Security Misconfigurations

Based on OWASP security principles.

---

## 📊 Code Quality Review

Analyzes:

* Code readability
* Maintainability
* Naming conventions
* Complexity issues
* Best practice violations
* Architecture concerns

---

## ♻️ AI Refactoring

Automatically generates:

* Cleaner code
* Better structure
* Improved readability
* Refactored implementations
* Optimization suggestions

---

## 🎯 Language Auto Detection

Automatically identifies programming languages using:

* Pattern-based heuristics
* Syntax analysis
* Pygments lexer detection

Supports:

* Python
* JavaScript
* TypeScript
* Java
* C++
* C#
* Go
* PHP
* Ruby
* And more

---

## 📈 Code Health Scoring

Generates scores for:

| Category       | Description              |
| -------------- | ------------------------ |
| Bug Score      | Code correctness         |
| Security Score | Security posture         |
| Quality Score  | Maintainability          |
| Overall Score  | Weighted aggregate score |

### Scoring Logic

Severity penalties:

| Severity | Penalty |
| -------- | ------- |
| Critical | -20     |
| Warning  | -10     |
| Info     | -3      |

Weighted calculation:

* Bugs → 30%
* Security → 40%
* Quality → 30%

---

## 📄 Downloadable HTML Reports

Generate comprehensive reports containing:

* Findings summary
* Security analysis
* Bug reports
* Quality review
* Refactored code
* Score breakdown

Reports are fully self-contained HTML files.

---

# 🏗️ System Architecture

```text
User Code Input
       │
       ▼
Language Detection
       │
       ▼
─────────────────────────
Multi-Agent AI Pipeline
─────────────────────────

 ┌─────────────────┐
 │ Bug Agent       │
 └─────────────────┘

 ┌─────────────────┐
 │ Security Agent  │
 └─────────────────┘

 ┌─────────────────┐
 │ Quality Agent   │
 └─────────────────┘

 ┌─────────────────┐
 │ Refactor Agent  │
 └─────────────────┘

       │
       ▼

Score Calculator
       │
       ▼

Report Builder
       │
       ▼

Final Review Dashboard
```

---

# 🛠️ Tech Stack

## Frontend

* Streamlit
* HTML/CSS
* Custom Dark Theme UI

## Backend

* Python

## AI & LLM

* LangChain
* Groq API
* Llama 3.3 70B Versatile

## Utilities

* Pygments
* Python Dotenv
* Asyncio

## Deployment

* Render

---

# 📂 Project Structure

```text
CodeSense_AI
│
├── app.py
│
├── agents
│   ├── bug_agent.py
│   ├── security_agent.py
│   ├── quality_agent.py
│   └── refactor_agent.py
│
├── utils
│   ├── language_detect.py
│   ├── llm_utils.py
│   ├── score_calculator.py
│   └── report_builder.py
│
├── requirements.txt
├── render.yaml
└── .env
```

---

# ⚙️ Installation

## Clone Repository

```bash
git clone https://github.com/varnikaBharalia/CodeSense_AI.git

cd CodeSense_AI
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configure Environment Variables

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
```

---

## Run Locally

```bash
streamlit run app.py
```

Application will start at:

```text
http://localhost:8501
```

---

# 🚀 Deployment

This project is configured for deployment on Render.

### render.yaml

```yaml
services:
  - type: web
    name: codesense-ai
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

Deploy by:

1. Connecting GitHub repository to Render.
2. Adding `GROQ_API_KEY` in Render Environment Variables.
3. Deploying the service.

---

# 🧠 How It Works

### Step 1

User pastes source code into the application.

### Step 2

Language Detection module identifies the programming language.

### Step 3

Code is sent concurrently to:

* Bug Agent
* Security Agent
* Quality Agent
* Refactoring Agent

### Step 4

Agents generate structured JSON findings.

### Step 5

Score Calculator computes health scores.

### Step 6

Results are displayed through an interactive dashboard.

### Step 7

User downloads a complete HTML report.

---

# 📸 Screenshots

Add screenshots here:

```text
screenshots/
│
├── homepage.png
├── review_results.png
├── security_analysis.png
└── report_download.png
```

Example:

```md
![Homepage](screenshots/homepage.png)
```

---

# 🔮 Future Enhancements

* GitHub Repository Review
* Pull Request Analysis
* CI/CD Integration
* VS Code Extension
* Multi-file Project Analysis
* AI Auto-Fix Suggestions
* Team Collaboration
* Vulnerability Trend Tracking
* Custom Security Rules

---

# 👩‍💻 Author

### Varnika Bharalia

B.Tech Student | Full Stack Developer | AI Enthusiast

GitHub:
https://github.com/varnikaBharalia

LinkedIn:
(Add your LinkedIn profile here)

---

# ⭐ Support

If you found this project useful:

⭐ Star the repository

🍴 Fork the repository

📝 Share feedback

🚀 Contribute to improvements

---

## Built with ❤️ using Python, Streamlit, LangChain, Groq, and Llama 3.3 70B
