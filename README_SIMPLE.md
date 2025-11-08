# EHPA - Ethical Hacking Personal Assistant
## Complete Guide in Simple English

---

## 📚 Table of Contents
1. [What is This Project?](#what-is-this-project)
2. [How Does It Work?](#how-does-it-work)
3. [What Can It Do?](#what-can-it-do)
4. [Project Structure Explained](#project-structure-explained)
5. [Installation & Setup](#installation--setup)
6. [How to Use It](#how-to-use-it)
7. [Understanding the Components](#understanding-the-components)
8. [Example Walkthrough](#example-walkthrough)
9. [Troubleshooting](#troubleshooting)

---

## What is This Project?

### Simple Explanation

Imagine you want to check if a website or network is secure. Normally, you would need to:
1. Run many different security tools (like nmap, nikto, sqlmap)
2. Understand what each tool does
3. Read through hundreds of lines of output
4. Make decisions about what to test next
5. Write a report of what you found

**EHPA does all of this automatically using Artificial Intelligence!**

### What EHPA Means

- **E**thical - Only used for authorized/legal security testing
- **H**acking - Finding security weaknesses
- **P**ersonal - Your own AI assistant
- **A**ssistant - Helps you automatically

### Real-World Analogy

Think of EHPA like having a **security expert robot** that:
- 🤖 Thinks like a senior security professional (using AI)
- 🔧 Uses hacking tools automatically (nmap, nikto, etc.)
- 📊 Explains findings in simple language
- 💬 Chats with you to answer questions
- 📝 Writes professional security reports

---

## How Does It Work?

### The Big Picture

```
YOU (User)
    ↓
Ask questions or start scans through Web Dashboard or Chat
    ↓
EHPA AI Brain (Claude LLM)
    ↓
Decides what tools to use and how to use them
    ↓
Security Tools (nmap, nikto, sqlmap, etc.)
    ↓
Scan the target website/network
    ↓
Results come back
    ↓
EHPA AI Brain reads and understands the results
    ↓
Shows you easy-to-understand findings
```

### The Smart Parts (AI Brain)

EHPA uses **3 different AI "personalities"** working together:

#### 1. **The Planner (Reasoning Module)**
- **Role:** Senior security expert
- **Job:** Decides what to test and in what order
- **Example:** "I see a web server on port 80, let's scan it for vulnerabilities"

#### 2. **The Executor (Generation Module)**
- **Role:** Technical specialist
- **Job:** Creates the exact commands to run
- **Example:** "Run this command: `nmap -sV -sC target.com`"

#### 3. **The Analyzer (Parsing Module)**
- **Role:** Data expert
- **Job:** Reads tool outputs and finds important information
- **Example:** "Found SQL injection vulnerability with severity HIGH"

### How AI Makes Decisions

Instead of following rigid rules, EHPA **thinks** using Claude AI:

**Traditional Approach (Old Way):**
```
IF port 80 is open
  THEN run nikto
  THEN run gobuster
  THEN run...
```

**EHPA Approach (AI Way):**
```
AI looks at: "Port 80 is open, it's running Apache 2.4.41"
AI thinks: "Apache server detected. I should:
           1. Check for known Apache vulnerabilities
           2. Scan for web application issues
           3. Look for directory listings
           4. Test for SQL injection"
AI adapts: Changes strategy based on what it finds
```

---

## What Can It Do?

### 🎯 Main Features

#### 1. **Automated Security Testing (6 Phases)**

**Phase 1: Reconnaissance** (Information Gathering)
- What it does: Discovers what's on the target
- Tools used: nmap, amass, subfinder, theharvester
- Finds: Open ports, running services, subdomains, email addresses
- Example: "Found ports 22, 80, 443 open. Web server is Apache."

**Phase 2: Enumeration** (Detailed Investigation)
- What it does: Gets detailed information about services
- Tools used: gobuster, enum4linux, dnsenum
- Finds: Hidden directories, file listings, service configurations
- Example: "Found admin panel at /admin, backup files in /backup"

**Phase 3: Vulnerability Scanning** (Finding Weaknesses)
- What it does: Looks for known security problems
- Tools used: nikto, nuclei, wpscan
- Finds: SQL injection points, XSS vulnerabilities, outdated software
- Example: "Found SQL injection in login form, severity: HIGH"

**Phase 4: Exploitation** (Testing Vulnerabilities) ⚠️
- What it does: Verifies if vulnerabilities are real
- Tools used: sqlmap, metasploit
- **Important:** Only runs with your approval
- Example: "Confirmed SQL injection allows database access"

**Phase 5: Post-Exploitation** (After Getting Access) ⚠️
- What it does: Checks what an attacker could do
- Tools used: linpeas, winpeas
- **Important:** Requires special permission
- Example: "Found privilege escalation opportunity"

**Phase 6: Reporting** (Documentation)
- What it does: Creates professional security reports
- Formats: HTML (web page), JSON (data), Markdown (text)
- Includes: All findings, severity levels, how to fix issues
- Example: "Generated report with 5 vulnerabilities and remediation steps"

#### 2. **AI Chatbot**

You can **talk** to EHPA like a security expert:

```
You: "What is SQL injection?"
EHPA: "SQL injection is when an attacker inserts malicious code into
       database queries. For example, entering ' OR '1'='1 in a login
       form can bypass authentication. Would you like me to test for it?"

You: "Scan example.com"
EHPA: "I'll start a comprehensive scan of example.com. This will take
       about 10 minutes. I'll notify you when I find anything important."

You: "What did you find?"
EHPA: "I discovered 3 vulnerabilities:
       🔴 HIGH: SQL Injection in /login
       🟡 MEDIUM: Outdated Apache version
       🟢 LOW: Directory listing enabled"
```

#### 3. **Security News Feed (OSINT)**

EHPA automatically collects security news every hour from:
- ThreatPost
- TheHackerNews
- BleepingComputer
- Cybersecurity News

You see: Latest vulnerabilities, cyber attacks, security trends

#### 4. **Web Dashboard**

Beautiful visual interface showing:
- 📊 Statistics (how many critical/high/medium/low vulnerabilities)
- 🔄 Live progress (what tool is running right now)
- 💬 Chat interface (talk to EHPA)
- 📋 Findings list (all vulnerabilities found)
- 🛠️ Tools overview (what tools are available)
- 🌐 Security news (latest cyber threats)

#### 5. **Professional Reports**

Creates reports like real security consultants:

**HTML Report (Visual):**
```
┌─────────────────────────────────┐
│  PENETRATION TEST REPORT        │
│  Target: example.com            │
│  Date: 2025-11-08               │
├─────────────────────────────────┤
│  Executive Summary              │
│  • 5 vulnerabilities found      │
│  • 1 Critical, 2 High, 2 Medium │
│  • Immediate action required    │
├─────────────────────────────────┤
│  Vulnerability Details          │
│  [Critical] SQL Injection       │
│  [High] XSS in comment form     │
│  ...                            │
├─────────────────────────────────┤
│  Remediation Plan               │
│  1. Fix SQL injection (Priority 1)
│  2. Patch Apache (Priority 2)  │
└─────────────────────────────────┘
```

---

## Project Structure Explained

### What's in Each Folder?

```
ehpa-task1/
├── 📄 main.py                    # The file you run to start everything
├── 📄 requirements.txt           # List of software this needs
├── 📄 .env                       # Your secret API keys (don't share!)
│
├── 📁 src/                       # All the program code
│   │
│   ├── 📁 agents/                # 5 AI agents for each phase
│   │   ├── recon_agent.py       # Phase 1: Finds targets
│   │   ├── enum_agent.py        # Phase 2: Gets details
│   │   ├── vuln_agent.py        # Phase 3: Finds vulnerabilities
│   │   ├── exploit_agent.py     # Phase 4: Tests vulnerabilities
│   │   └── report_agent.py      # Phase 6: Creates reports
│   │
│   ├── 📁 chatbot/               # The AI chat system
│   │   ├── conversation_handler.py  # Manages chat conversations
│   │   ├── command_parser.py        # Understands your commands
│   │   ├── explainer.py             # Explains security concepts
│   │   └── context_manager.py       # Remembers conversation history
│   │
│   ├── 📁 modules/               # The 3 AI brains
│   │   ├── reasoning.py         # The Planner (what to do)
│   │   ├── generation.py        # The Executor (how to do it)
│   │   └── parsing.py           # The Analyzer (what was found)
│   │
│   ├── 📁 mcp/                   # Tool wrappers (makes tools easy to use)
│   │   ├── nmap_server.py       # For network scanning
│   │   ├── nikto_server.py      # For web vulnerability scanning
│   │   ├── sqlmap_server.py     # For SQL injection testing
│   │   ├── gobuster_server.py   # For finding hidden directories
│   │   ├── osint_tools.py       # For information gathering
│   │   ├── exploit_tools.py     # For testing vulnerabilities
│   │   └── post_exploit_tools.py # For privilege escalation
│   │
│   ├── 📁 api/                   # Web server (handles requests)
│   │   ├── server.py            # Main web server
│   │   ├── websocket.py         # Real-time chat server
│   │   ├── chat_routes.py       # Chat API endpoints
│   │   └── models.py            # Data structures
│   │
│   ├── 📁 orchestrator/          # Coordination center
│   │   ├── chatbot_manager.py   # Manages chatbot
│   │   └── osint_aggregator.py  # Collects security news
│   │
│   └── 📁 utils/                 # Helper tools
│       ├── logger.py            # Records what happens (logs)
│       └── reporter.py          # Creates reports
│
├── 📁 web/                       # Website/Dashboard
│   ├── 📁 templates/
│   │   └── dashboard.html       # The main webpage
│   └── 📁 static/
│       ├── 📁 css/
│       │   └── dashboard.css    # Makes it look pretty
│       └── 📁 js/
│           ├── dashboard.js     # Makes dashboard work
│           └── chat.js          # Makes chat work
│
├── 📁 configs/                   # Settings and configurations
│   ├── config.yaml              # Main settings
│   ├── tools.yaml               # Tool settings
│   ├── chatbot_prompts.yaml     # Chatbot response templates
│   ├── educational_content.yaml # Security lessons
│   └── osint_sources.yaml       # Security news sources
│
├── 📁 data/                      # Stored information
│   ├── 📁 sessions/             # Saved scan sessions
│   ├── 📁 findings/             # Discovered vulnerabilities
│   ├── 📁 reports/              # Generated reports
│   └── 📁 chat_history/         # Chatbot conversations
│
└── 📁 tests/                     # Tests to make sure everything works
```

### How Components Work Together

```
1. YOU access the Web Dashboard (web/)
        ↓
2. Dashboard talks to the API Server (api/)
        ↓
3. API Server asks the Orchestrator (core/)
        ↓
4. Orchestrator uses Agents (agents/) for each phase
        ↓
5. Agents ask the AI Modules (modules/) for help
        ↓
6. AI Modules tell Tools (mcp/) what to do
        ↓
7. Tools run security scans (nmap, nikto, etc.)
        ↓
8. Results go back up the chain
        ↓
9. You see findings on the Dashboard
```

---

## Installation & Setup

### Step-by-Step Installation

#### Prerequisites (What You Need First)

1. **Linux Computer** (preferably Kali Linux)
   - Why: Security tools work best on Linux
   - Alternative: Ubuntu, Debian, or use Windows WSL2

2. **Python 3.9 or newer**
   ```bash
   # Check if you have Python
   python3 --version
   # Should show: Python 3.9.x or higher
   ```

3. **Claude API Key** (from Anthropic)
   - Go to: https://console.anthropic.com/
   - Create account
   - Get your API key (starts with `sk-ant-`)
   - **Important:** Keep this secret!

4. **Security Tools** (if not on Kali Linux)
   ```bash
   # Install all needed tools
   sudo apt update
   sudo apt install nmap nikto sqlmap gobuster -y
   ```

#### Installation Steps

**Step 1: Get the Project**
```bash
# Go to your projects folder
cd ~/projects

# The project is already here: C:\Users\Kunal\OneDrive\Desktop\November\ehpa-task1
# So you just need to navigate to it
cd "C:\Users\Kunal\OneDrive\Desktop\November\ehpa-task1"
```

**Step 2: Create Python Environment**
```bash
# Create isolated Python environment
python3 -m venv venv

# Activate it (Linux)
source venv/bin/activate

# Activate it (Windows)
.\venv\Scripts\activate

# Your prompt should now show (venv)
```

**Step 3: Install Python Packages**
```bash
# Install all required packages
pip install -r requirements.txt

# This installs:
# - FastAPI (web server)
# - Anthropic (AI)
# - Uvicorn (server runner)
# - And 20+ other packages
```

**Step 4: Configure Your Settings**

Create a `.env` file:
```bash
# Create the file
nano .env

# Or on Windows
notepad .env
```

Add this content (replace `your-key-here`):
```env
# === REQUIRED ===
# Your Claude API key from Anthropic
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here

# === SECURITY ===
# Targets you're allowed to test
ALLOWED_TARGETS=scanme.nmap.org,testphp.vulnweb.com
REQUIRE_TARGET_APPROVAL=true

# === SERVER ===
# Where the server runs
API_HOST=0.0.0.0
API_PORT=8000

# === OPTIONAL ===
# Hexstrike MCP (if you have it)
HEXSTRIKE_API_KEY=your-hexstrike-key

# Shodan (for OSINT)
SHODAN_API_KEY=your-shodan-key
```

**Step 5: Test Everything Works**
```bash
# Test Python imports
python3 -c "import anthropic; print('✅ Anthropic OK')"
python3 -c "import fastapi; print('✅ FastAPI OK')"

# Test tools are installed
which nmap && echo "✅ nmap OK"
which nikto && echo "✅ nikto OK"
which sqlmap && echo "✅ sqlmap OK"

# If all show ✅, you're ready!
```

**Step 6: Start the Server**
```bash
# Simple way
python3 main.py

# Advanced way (with auto-reload during development)
uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

**Step 7: Check It's Running**

Open your web browser and go to:
- **Dashboard:** http://localhost:8000/dashboard
- **API Docs:** http://localhost:8000/api/docs
- **Health Check:** http://localhost:8000/api/health

If you see the dashboard, **congratulations!** 🎉

---

## How to Use It

### Method 1: Using the Web Dashboard (Easiest)

**Step 1: Open Dashboard**
```
In browser: http://localhost:8000/dashboard
```

**Step 2: Start a Scan**
1. Click "Start New Scan" button
2. Enter target: `scanme.nmap.org`
3. Select scope: ☑️ Network, ☑️ Web Application
4. Check: ☑️ I confirm I have authorization
5. Click "Start Scan"

**Step 3: Watch Progress**
- Progress bar shows: 0% → 100%
- Current task updates in real-time
- Notifications when vulnerabilities found

**Step 4: Chat with EHPA**
1. Click "Chat" tab
2. Type: "What vulnerabilities did you find?"
3. EHPA responds with detailed explanation
4. Ask: "How do I fix the SQL injection?"
5. EHPA explains remediation steps

**Step 5: View Results**
1. Click "Findings" tab
2. See all vulnerabilities sorted by severity
3. Filter by: Critical, High, Medium, Low
4. Click vulnerability to see details

**Step 6: Generate Report**
1. Click "Generate Report" button
2. Choose format: HTML, JSON, or Markdown
3. Report saves to `data/reports/` folder
4. Open in browser to see professional report

### Method 2: Using the Chat Interface

**Example Conversations:**

**1. Learn About Security:**
```
You: "What is XSS?"

EHPA: "XSS (Cross-Site Scripting) is when attackers inject malicious
       JavaScript into websites. When other users visit, the script runs
       in their browser and can steal cookies, sessions, or sensitive data.

       Example: <script>alert(document.cookie)</script>

       Would you like me to scan for XSS vulnerabilities?"
```

**2. Start Scans:**
```
You: "Scan scanme.nmap.org"

EHPA: "✅ Starting comprehensive scan of scanme.nmap.org

       Phase 1: Reconnaissance
       Running: nmap, amass, subfinder
       Estimated time: 10 minutes

       I'll update you as I discover findings!"
```

**3. Get Status Updates:**
```
You: "What's the status?"

EHPA: "⏳ Scan Progress: 65%

       Current Phase: Vulnerability Scanning
       Current Task: Running Nikto on port 80
       Completed: 8/12 tasks

       Findings so far:
       🔴 0 Critical
       🟠 2 High
       🟡 3 Medium
       🟢 1 Low"
```

**4. Ask Questions:**
```
You: "What's the most serious vulnerability?"

EHPA: "The most serious finding is:

       🔴 SQL Injection in Login Form
       Severity: HIGH (CVSS 8.5)
       Location: /login.php parameter 'username'

       Impact: An attacker could:
       - Access the entire database
       - Steal user credentials
       - Modify or delete data

       Fix: Use parameterized queries instead of string concatenation

       Would you like me to show you the code example?"
```

### Method 3: Using the API (For Developers)

**1. Start a Scan:**
```bash
curl -X POST "http://localhost:8000/api/v1/pentest/start" \
  -H "Content-Type: application/json" \
  -d '{
    "target": "scanme.nmap.org",
    "scope": ["network", "web"],
    "authorized": true
  }'
```

**Response:**
```json
{
  "session_id": "ptest_abc123",
  "target": "scanme.nmap.org",
  "status": "active",
  "current_phase": "reconnaissance"
}
```

**2. Check Progress:**
```bash
curl "http://localhost:8000/api/v1/pentest/ptest_abc123/status"
```

**3. Get Findings:**
```bash
curl "http://localhost:8000/api/v1/pentest/ptest_abc123/findings"
```

**4. Chat:**
```bash
curl -X POST "http://localhost:8000/api/v1/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain SQL injection",
    "session_id": "default"
  }'
```

---

## Understanding the Components

### How AI Makes It Smart

#### 1. The Reasoning Module (The Brain)

**What it does:**
- Looks at the current situation
- Decides what to do next
- Thinks strategically like a human expert

**Example Conversation with AI:**
```
EHPA: "I found ports 22, 80, 443 open on the target"

Reasoning Module thinks:
- Port 22 = SSH (secure shell)
- Port 80 = HTTP (web server)
- Port 443 = HTTPS (secure web server)

Decision: "Focus on the web server first because:
1. Web applications often have more vulnerabilities
2. Port 80 is HTTP (not encrypted) = easier to test
3. Can check for common web vulnerabilities"

Next action: "Run web vulnerability scanner (Nikto)"
```

#### 2. The Generation Module (The Technician)

**What it does:**
- Creates exact commands to run
- Chooses the right tool settings
- Explains what will happen

**Example:**
```
Task: "Scan web server for vulnerabilities"

Generation Module creates:
Command: nikto -h scanme.nmap.org -port 80 -ssl
Explanation:
  -h = target host
  -port = which port to scan
  -ssl = test HTTPS if available

Expected output: "List of web vulnerabilities"
```

#### 3. The Parsing Module (The Reader)

**What it does:**
- Reads messy tool output
- Finds important information
- Organizes it nicely

**Example:**
```
Tool output (messy):
+ OSVDB-3092: /admin/: This might be interesting...
+ OSVDB-3233: /icons/README: Apache default file found.
+ OSVDB-3268: /css/: Directory indexing found.
+ OSVDB-3288: /docs/: Directory indexing found.

Parsing Module extracts:
Vulnerabilities:
1. Title: "Admin panel exposed"
   Location: /admin/
   Severity: MEDIUM

2. Title: "Directory listing enabled"
   Location: /css/, /docs/
   Severity: LOW
```

### How Tools Are Wrapped (MCP Layer)

Instead of running tools directly, EHPA wraps them for consistency:

**Without MCP (Direct):**
```bash
# Different command for each tool
nmap -sV target.com
nikto -h target.com
sqlmap -u target.com/login --dbs
```

**With MCP (Wrapped):**
```python
# Same interface for all tools
result1 = nmap_tool.execute({"target": "target.com"})
result2 = nikto_tool.execute({"target": "target.com"})
result3 = sqlmap_tool.execute({"target": "target.com/login"})

# All results in same format:
{
  "tool": "nmap",
  "status": "success",
  "output": "...",
  "findings": [...]
}
```

**Benefits:**
✅ Easy to add new tools
✅ Consistent error handling
✅ Same output format
✅ Easy to test
✅ Safe execution

---

## Example Walkthrough

Let's walk through a complete example step-by-step:

### Scenario: Testing scanme.nmap.org

**Phase 1: Reconnaissance (Finding Things)**

```
[1] Reasoning Module decides:
    "Start with network scan to find open ports"

[2] Generation Module creates:
    Command: nmap -sV -sC scanme.nmap.org

[3] Nmap runs and outputs:
    PORT     STATE SERVICE  VERSION
    22/tcp   open  ssh      OpenSSH 7.9
    80/tcp   open  http     Apache/2.4.41
    9929/tcp open  nping-echo

[4] Parsing Module extracts:
    {
      "open_ports": [22, 80, 9929],
      "services": {
        "22": "SSH (OpenSSH 7.9)",
        "80": "HTTP (Apache 2.4.41)",
        "9929": "nping-echo"
      }
    }

[5] Session updated:
    Target now has 3 open ports discovered
```

**Phase 2: Enumeration (Getting Details)**

```
[1] Reasoning Module sees:
    "Web server on port 80 detected"
    Decision: "Find hidden directories and files"

[2] Generation Module creates:
    Command: gobuster dir -u http://scanme.nmap.org -w common.txt

[3] Gobuster runs and finds:
    /images (Status: 301)
    /shared (Status: 301)

[4] Parsing Module extracts:
    {
      "directories": [
        {"path": "/images", "status": 301},
        {"path": "/shared", "status": 301}
      ]
    }

[5] Session updated:
    2 directories discovered
```

**Phase 3: Vulnerability Scanning (Finding Problems)**

```
[1] Reasoning Module decides:
    "Scan web server for known vulnerabilities"

[2] Generation Module creates:
    Command: nikto -h scanme.nmap.org

[3] Nikto runs for 5 minutes and outputs:
    + OSVDB-3092: /admin/: Admin panel found
    + Apache/2.4.41 appears to be outdated
    + HTTP TRACE method is enabled

[4] Parsing Module extracts:
    {
      "vulnerabilities": [
        {
          "title": "Admin Panel Exposed",
          "severity": "MEDIUM",
          "cvss": 5.3,
          "description": "Admin panel accessible without authentication"
        },
        {
          "title": "Outdated Apache Version",
          "severity": "MEDIUM",
          "cvss": 5.0,
          "description": "Apache 2.4.41 has known vulnerabilities"
        }
      ]
    }

[5] You receive notification:
    🟡 MEDIUM vulnerability found: Admin Panel Exposed
    🟡 MEDIUM vulnerability found: Outdated Apache
```

**Phase 4: Reporting (Creating Documentation)**

```
[1] All findings collected:
    - 3 open ports
    - 2 directories
    - 2 vulnerabilities

[2] Report Agent creates:
    ┌─────────────────────────────────────┐
    │ PENETRATION TEST REPORT             │
    ├─────────────────────────────────────┤
    │ Target: scanme.nmap.org             │
    │ Date: 2025-11-08                    │
    │ Duration: 15 minutes                │
    │                                     │
    │ FINDINGS SUMMARY                    │
    │ Total Vulnerabilities: 2            │
    │ • Critical: 0                       │
    │ • High: 0                           │
    │ • Medium: 2 ⚠️                      │
    │ • Low: 0                            │
    │                                     │
    │ VULNERABILITY DETAILS               │
    │                                     │
    │ [MEDIUM] Admin Panel Exposed        │
    │ Location: /admin/                   │
    │ Impact: Unauthorized access risk    │
    │ Fix: Add authentication             │
    │                                     │
    │ [MEDIUM] Outdated Apache            │
    │ Version: 2.4.41                     │
    │ Impact: Known vulnerabilities       │
    │ Fix: Update to Apache 2.4.52+       │
    └─────────────────────────────────────┘

[3] Report saved to:
    data/reports/pentest_report_scanme_20251108.html
```

**Chatbot Interaction During Scan:**

```
[During scan at 45% progress]

You: "What have you found so far?"

EHPA: "I'm currently 45% through the scan. Here's what I've discovered:

       📊 Open Ports: 3
       - SSH on port 22
       - HTTP on port 80
       - Nping-echo on port 9929

       📂 Directories: 2
       - /images
       - /shared

       🔍 Vulnerabilities: 2 (Medium severity)

       Currently running: Web vulnerability scan with Nikto
       Estimated time remaining: 8 minutes"

You: "Should I be worried about these vulnerabilities?"

EHPA: "The vulnerabilities found are MEDIUM severity, not critical. Here's what they mean:

       1. Admin Panel Exposed
          Risk: Someone could try to access your admin area
          Urgency: Moderate - add authentication soon

       2. Outdated Apache
          Risk: Known security holes exist
          Urgency: Moderate - plan update within 2 weeks

       Neither allows immediate system compromise, but both should be fixed to improve security.

       Would you like detailed remediation steps?"
```

---

## Troubleshooting

### Common Problems and Solutions

#### Problem 1: Server Won't Start

**Symptom:**
```
Error: Port 8000 is already in use
```

**Solution:**
```bash
# Option 1: Kill the process using port 8000
sudo lsof -i :8000
sudo kill -9 <PID>

# Option 2: Use a different port
# Edit .env file:
API_PORT=8080

# Start again
python3 main.py
```

#### Problem 2: API Key Error

**Symptom:**
```
Error: ANTHROPIC_API_KEY not found
```

**Solution:**
```bash
# Check .env file exists
ls -la .env

# If not, create it:
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" > .env

# Check it's loaded:
python3 -c "import os; print(os.getenv('ANTHROPIC_API_KEY'))"
```

#### Problem 3: Tools Not Found

**Symptom:**
```
Error: nmap not found in PATH
```

**Solution:**
```bash
# Install missing tools
sudo apt update
sudo apt install nmap nikto sqlmap gobuster -y

# Verify installation
which nmap
which nikto
which sqlmap
which gobuster

# All should show a path like /usr/bin/nmap
```

#### Problem 4: Permission Denied

**Symptom:**
```
Error: Permission denied when running nmap
```

**Solution:**
```bash
# Some tools need root/admin privileges
# Option 1: Run entire server as root (not recommended)
sudo python3 main.py

# Option 2: Give specific permissions
sudo chmod +x /usr/bin/nmap
sudo setcap cap_net_raw,cap_net_admin=eip /usr/bin/nmap
```

#### Problem 5: Target Not Authorized

**Symptom:**
```
Error: Target not in allowed list
```

**Solution:**
```bash
# Edit .env file
nano .env

# Add your target (if you have permission!)
ALLOWED_TARGETS=scanme.nmap.org,testphp.vulnweb.com,yourtarget.com

# Save and restart server
```

#### Problem 6: Chat Not Working

**Symptom:**
- Messages don't send
- No response from bot

**Solution:**
```bash
# Check WebSocket connection
# Open browser console (F12) and look for:
"WebSocket connection failed"

# Check server logs for:
python3 main.py | grep -i websocket

# Restart server
```

#### Problem 7: Dashboard Won't Load

**Symptom:**
- Blank page
- 404 error

**Solution:**
```bash
# Check static files exist
ls web/templates/dashboard.html
ls web/static/css/dashboard.css
ls web/static/js/dashboard.js

# If missing, check INTEGRATION_GUIDE.md
# Make sure server_extensions.py is enabled

# Clear browser cache and reload
```

### Getting Help

If problems persist:

1. **Check Logs:**
   ```bash
   # Server logs
   tail -f logs/ehpa.log

   # Look for ERROR or WARNING messages
   ```

2. **Test Components:**
   ```bash
   # Test API
   curl http://localhost:8000/api/health

   # Should return: {"status": "healthy"}
   ```

3. **Verify Environment:**
   ```bash
   # Check Python version
   python3 --version  # Should be 3.9+

   # Check dependencies
   pip list | grep anthropic
   pip list | grep fastapi
   ```

4. **Read Documentation:**
   - API Docs: http://localhost:8000/api/docs
   - Integration Guide: INTEGRATION_GUIDE.md
   - Main README: README.md

---

## 🎯 Quick Reference

### Essential Commands

**Start Server:**
```bash
python3 main.py
```

**Access Points:**
```
Dashboard:  http://localhost:8000/dashboard
API Docs:   http://localhost:8000/api/docs
Health:     http://localhost:8000/api/health
```

**Common API Calls:**
```bash
# Start scan
curl -X POST http://localhost:8000/api/v1/pentest/start \
  -d '{"target":"scanme.nmap.org","scope":["network"],"authorized":true}'

# Check status
curl http://localhost:8000/api/v1/pentest/{session_id}/status

# Get findings
curl http://localhost:8000/api/v1/pentest/{session_id}/findings

# Chat
curl -X POST http://localhost:8000/api/v1/chat/message \
  -d '{"message":"What is SQL injection?"}'
```

### File Locations

```
Configs:     configs/
Logs:        logs/
Reports:     data/reports/
Sessions:    data/sessions/
Chat History: data/chat_history/
```

---

## 🎓 Summary

**EHPA is a complete AI-powered security testing system that:**

✅ **Automates penetration testing** through 6 phases
✅ **Uses AI** to make smart decisions
✅ **Provides a chatbot** to answer questions and explain concepts
✅ **Creates professional reports** automatically
✅ **Has a beautiful dashboard** for easy use
✅ **Stays updated** with latest security news
✅ **Works with 150+ security tools**

**Perfect for:**
- 🎓 Learning about cybersecurity
- 🔒 Testing your own websites/networks
- 📚 University projects
- 💼 Professional security assessments

**Remember:**
⚠️ Only test systems you have permission to test!
⚠️ Unauthorized hacking is illegal!

---

**Made with ❤️ for educational purposes**
**Version: 1.0.0 | November 2025**
