# EHPA - Ethical Hacking Personal Assistant
## Complete Guide in Simple English

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

 Check It's Running**

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

EHPA: "Starting comprehensive scan of scanme.nmap.org

       Phase 1: Reconnaissance
       Running: nmap, amass, subfinder
       Estimated time: 10 minutes

       I'll update you as I discover findings!"
```

**3. Get Status Updates:**
```
You: "What's the status?"

EHPA: " Scan Progress: 65%

       Current Phase: Vulnerability Scanning
       Current Task: Running Nikto on port 80
       Completed: 8/12 tasks

       Findings so far:
        0 Critical
        2 High
        3 Medium
        1 Low"
```

**4. Ask Questions:**
```
You: "What's the most serious vulnerability?"

EHPA: "The most serious finding is:

       SQL Injection in Login Form
       Severity: HIGH (CVSS 8.5)
       Location: /login.php parameter 'username'

       Impact: An attacker could:
       - Access the entire database
       - Steal user credentials
       - Modify or delete data

       Fix: Use parameterized queries instead of string concatenation

       Would you like me to show you the code example?"
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


#### 3. The Parsing Module (The Reader)

**What it does:**
- Reads messy tool output
- Finds important information
- Organizes it nicely

```

**Benefits:**
 Easy to add new tools
 Consistent error handling
 Same output format
 Easy to test
 Safe execution

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

You receive notification:
     MEDIUM vulnerability found: Admin Panel Exposed
     MEDIUM vulnerability found: Outdated Apache
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

## Summary

**EHPA is a complete AI-powered security testing system that:**

 **Automates penetration testing** through 6 phases
 **Uses AI** to make smart decisions
 **Provides a chatbot** to answer questions and explain concepts
 **Creates professional reports** automatically
 **Has a beautiful dashboard** for easy use
 **Stays updated** with latest security news
 **Works with 150+ security tools**

**Perfect for:**
-  Learning about cybersecurity
-  Testing your own websites/networks
-  University projects
-  Professional security assessments

---

**Made with ❤️ for educational purposes**
**Version: 1.0.0 | November 2025**
