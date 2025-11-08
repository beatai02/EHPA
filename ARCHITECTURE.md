# EHPA Task 1 - System Architecture

Detailed architecture documentation for the Backend Orchestration System.

---

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT LAYER                            │
│        (Task 2 Dashboard - To Be Built)                    │
│   - React/Vue Frontend                                      │
│   - Real-time status updates                               │
│   - Vulnerability visualization                            │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ HTTP/REST API
                   │ JSON Responses
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                  API LAYER (FastAPI)                        │
│                                                             │
│  Endpoints:                                                 │
│  ├─ POST   /api/v1/pentest/start                          │
│  ├─ POST   /api/v1/pentest/{id}/execute                   │
│  ├─ GET    /api/v1/pentest/{id}/status                    │
│  ├─ GET    /api/v1/pentest/{id}/findings                  │
│  ├─ GET    /api/v1/pentest/{id}/report                    │
│  └─ ...    (15 total endpoints)                           │
│                                                             │
│  Features:                                                  │
│  ├─ Request validation (Pydantic)                         │
│  ├─ Error handling                                         │
│  ├─ CORS support                                          │
│  └─ OpenAPI documentation                                  │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ Python Function Calls
                   │
┌──────────────────▼──────────────────────────────────────────┐
│              ORCHESTRATION LAYER                            │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │            ORCHESTRATOR (Main Engine)               │  │
│  │                                                     │  │
│  │  Responsibilities:                                  │  │
│  │  • Session lifecycle management                    │  │
│  │  • Module coordination                             │  │
│  │  • Workflow execution                              │  │
│  │  • State persistence                               │  │
│  │  • Progress tracking                               │  │
│  │                                                     │  │
│  │  Core Loop:                                        │  │
│  │  while not complete:                               │  │
│  │    1. Reasoning → plan_next_steps()               │  │
│  │    2. Generation → generate_command()             │  │
│  │    3. MCP Tools → execute()                       │  │
│  │    4. Parsing → parse_output()                    │  │
│  │    5. Update session                               │  │
│  │    6. Check phase transition                       │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │         SESSION MANAGER                             │  │
│  │                                                     │  │
│  │  Session State:                                     │  │
│  │  • session_id, target, scope                       │  │
│  │  • current_phase, progress                         │  │
│  │  • todo_list, completed_tasks                      │  │
│  │  • vulnerabilities, findings                       │  │
│  │  • conversation_history                            │  │
│  │  • target_info (IPs, ports, services)             │  │
│  │                                                     │  │
│  │  Methods:                                          │  │
│  │  • add_task(), complete_task()                     │  │
│  │  • add_vulnerability(), add_finding()              │  │
│  │  • advance_phase(), can_advance_phase()            │  │
│  │  • get_context_summary()                           │  │
│  │  • save(), load()                                  │  │
│  └─────────────────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ Async Function Calls
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                 LLM MODULE LAYER                            │
│         (Three Specialized Modules)                         │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────┐ │
│  │   REASONING     │  │   GENERATION    │  │  PARSING   │ │
│  │     MODULE      │  │     MODULE      │  │   MODULE   │ │
│  │                 │  │                 │  │            │ │
│  │ Role:           │  │ Role:           │  │ Role:      │ │
│  │ Senior Pentester│  │ Security        │  │ Data       │ │
│  │                 │  │ Engineer        │  │ Analyst    │ │
│  │ Responsibilities│  │ Responsibilities│  │ Resp.:     │ │
│  │ • Strategic     │  │ • Command       │  │ • Parse    │ │
│  │   planning      │  │   generation    │  │   output   │ │
│  │ • Phase         │  │ • Payload       │  │ • Extract  │ │
│  │   progression   │  │   creation      │  │   vulns    │ │
│  │ • Risk          │  │ • Flag          │  │ • Classify │ │
│  │   assessment    │  │   selection     │  │   severity │ │
│  │ • Finding       │  │ • Tool          │  │ • Structure│ │
│  │   analysis      │  │   expertise     │  │   data     │ │
│  │                 │  │                 │  │            │ │
│  │ LLM Config:     │  │ LLM Config:     │  │ LLM Config:│ │
│  │ • Temp: 0.7     │  │ • Temp: 0.5     │  │ • Temp:0.3 │ │
│  │ • Tokens: 2048  │  │ • Tokens: 1024  │  │ • Tok:2048 │ │
│  └────────┬────────┘  └────────┬────────┘  └──────┬─────┘ │
│           │                    │                   │       │
│           └────────────────────┼───────────────────┘       │
│                                │                           │
│                     All use Claude API                     │
│                     (anthropic.messages.create)            │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ Tool Execution Requests
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                MCP TOOL LAYER                               │
│         (Standardized Tool Interface)                       │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │            BASE MCP SERVER (Abstract)               │  │
│  │                                                     │  │
│  │  Interface Methods:                                 │  │
│  │  • get_tool_schema() → Dict                        │  │
│  │  • validate_params(params) → bool                  │  │
│  │  • build_command(params) → str                     │  │
│  │  • execute(params) → Dict                          │  │
│  │  • parse_output(output) → Dict                     │  │
│  │                                                     │  │
│  │  Common Features:                                   │  │
│  │  • Timeout management                              │  │
│  │  • Error handling                                  │  │
│  │  • Target authorization                            │  │
│  │  • Command sanitization                            │  │
│  │  • Async execution                                 │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   NMAP   │  │  NIKTO   │  │  SQLMAP  │  │ GOBUSTER │  │
│  │  SERVER  │  │  SERVER  │  │  SERVER  │  │  SERVER  │  │
│  │          │  │          │  │          │  │          │  │
│  │ Purpose: │  │ Purpose: │  │ Purpose: │  │ Purpose: │  │
│  │ Network  │  │ Web vuln │  │ SQL      │  │ Directory│  │
│  │ scanning │  │ scanning │  │ injection│  │ enum     │  │
│  │          │  │          │  │          │  │          │  │
│  │ Params:  │  │ Params:  │  │ Params:  │  │ Params:  │  │
│  │ • target │  │ • target │  │ • target │  │ • target │  │
│  │ • ports  │  │ • port   │  │ • url    │  │ • mode   │  │
│  │ • scan   │  │ • ssl    │  │ • level  │  │ • word   │  │
│  │   type   │  │ • tuning │  │ • risk   │  │   list   │  │
│  │ • timing │  │          │  │          │  │          │  │
│  │          │  │          │  │          │  │          │  │
│  │ Timeout: │  │ Timeout: │  │ Timeout: │  │ Timeout: │  │
│  │ 300s     │  │ 600s     │  │ 900s     │  │ 300s     │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │             │             │             │         │
└───────┼─────────────┼─────────────┼─────────────┼─────────┘
        │             │             │             │
        │  Shell Commands via subprocess.create_subprocess_shell()
        │             │             │             │
┌───────▼─────────────▼─────────────▼─────────────▼─────────┐
│               KALI LINUX TOOLS                              │
│                                                             │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐        │
│  │ nmap │  │nikto │  │sqlmap│  │gobu- │  │more  │        │
│  │      │  │      │  │      │  │ster  │  │tools │        │
│  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘        │
│                                                             │
│  Installed in: /usr/bin/                                   │
│  Executed with: proper privileges                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow Diagram

### Complete Penetration Test Workflow

```
User Request
    │
    ▼
┌──────────────────────┐
│ POST /pentest/start  │
│ {target, scope}      │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────────────────────────────────┐
│           CREATE SESSION                         │
│  • Generate session_id                           │
│  • Initialize target_info                        │
│  • Set phase = reconnaissance                    │
│  • Reasoning: plan_initial_tasks()               │
│    - LLM analyzes target and scope              │
│    - Returns 3-5 initial tasks                   │
│  • Add tasks to todo_list                        │
│  • Save session to disk                          │
└──────┬───────────────────────────────────────────┘
       │
       ▼ POST /pentest/{id}/execute
       │
┌──────▼───────────────────────────────────────────┐
│      WORKFLOW EXECUTION LOOP                     │
│                                                  │
│  while not completed:                            │
│    ┌──────────────────────────────────────┐    │
│    │ 1. GET NEXT TASK                     │    │
│    │    • Check todo_list                 │    │
│    │    • If empty, ask Reasoning for more│    │
│    └──────┬───────────────────────────────┘    │
│           │                                     │
│    ┌──────▼───────────────────────────────┐    │
│    │ 2. GENERATE COMMAND                  │    │
│    │    Generation Module:                │    │
│    │    • Takes task description          │    │
│    │    • LLM generates specific command  │    │
│    │    • Returns: command, explanation   │    │
│    └──────┬───────────────────────────────┘    │
│           │                                     │
│    ┌──────▼───────────────────────────────┐    │
│    │ 3. EXECUTE VIA MCP TOOL              │    │
│    │    MCP Tool Server:                  │    │
│    │    • Validate parameters             │    │
│    │    • Check authorization             │    │
│    │    • Build command                   │    │
│    │    • Execute async with timeout      │    │
│    │    • Return output                   │    │
│    └──────┬───────────────────────────────┘    │
│           │                                     │
│    ┌──────▼───────────────────────────────┐    │
│    │ 4. PARSE OUTPUT                      │    │
│    │    Parsing Module:                   │    │
│    │    • LLM analyzes tool output        │    │
│    │    • Extracts vulnerabilities        │    │
│    │    • Classifies severity             │    │
│    │    • Extracts target info            │    │
│    │    • Returns structured data         │    │
│    └──────┬───────────────────────────────┘    │
│           │                                     │
│    ┌──────▼───────────────────────────────┐    │
│    │ 5. UPDATE SESSION                    │    │
│    │    • Mark task completed             │    │
│    │    • Add vulnerabilities             │    │
│    │    • Update target_info              │    │
│    │    • Update progress %               │    │
│    │    • Save session                    │    │
│    └──────┬───────────────────────────────┘    │
│           │                                     │
│    ┌──────▼───────────────────────────────┐    │
│    │ 6. CHECK PHASE TRANSITION            │    │
│    │    Reasoning Module:                 │    │
│    │    • Analyze current progress        │    │
│    │    • LLM decides if ready to advance │    │
│    │    • If yes, advance to next phase   │    │
│    │    • Generate new phase tasks        │    │
│    └──────┬───────────────────────────────┘    │
│           │                                     │
│           └─────────▶ Continue loop            │
│                                                  │
└──────┬───────────────────────────────────────────┘
       │
       ▼ phase == "reporting"
       │
┌──────▼───────────────────────────────────────────┐
│           GENERATE REPORT                        │
│  • Reasoning: analyze_findings()                 │
│    - LLM provides executive summary              │
│    - Risk assessment                             │
│    - Recommendations                             │
│  • Reporter: generate_report()                   │
│    - Create HTML report                          │
│    - Create JSON export                          │
│  • Mark session as completed                     │
└──────┬───────────────────────────────────────────┘
       │
       ▼
   Report Ready
```

---

## 🧠 LLM Module Interaction

### How the Three Modules Work Together

```
                    ORCHESTRATOR
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
    REASONING       GENERATION       PARSING
      (What)          (How)          (Results)
         │               │               │
         │               │               │
    ┌────▼────┐     ┌────▼────┐    ┌────▼────┐
    │ Prompt: │     │ Prompt: │    │ Prompt: │
    │         │     │         │    │         │
    │ "Plan   │     │ "Gen    │    │ "Parse  │
    │  next   │     │  nmap   │    │  this   │
    │  steps" │     │  cmd"   │    │  output"│
    └────┬────┘     └────┬────┘    └────┬────┘
         │               │               │
         ▼               ▼               ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │   CLAUDE   │  │   CLAUDE   │  │   CLAUDE   │
    │    API     │  │    API     │  │    API     │
    │            │  │            │  │            │
    │ Temp: 0.7  │  │ Temp: 0.5  │  │ Temp: 0.3  │
    │ Tokens:2K  │  │ Tokens:1K  │  │ Tokens:2K  │
    └────┬────────┘  └────┬────┘    └────┬────┘
         │               │               │
         ▼               ▼               ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │ Response:  │  │ Response:  │  │ Response:  │
    │            │  │            │  │            │
    │ {tasks:[   │  │ {command:  │  │ {vulns:[   │
    │   {desc,   │  │   "nmap    │  │   {title,  │
    │    tool,   │  │    -sV     │  │    sever,  │
    │    priority│  │    ...",   │  │    cvss}   │
    │   }        │  │  explain}  │  │  ]}        │
    │ ]}         │  │            │  │            │
    └────┬────────┘  └────┬────┘    └────┬────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
                         ▼
                   ORCHESTRATOR
               (Combines results)
```

### Context Flow

```
Session Context
    │
    ├─▶ Reasoning Module
    │   • Sees full session state
    │   • Conversation history
    │   • All findings so far
    │   • Target information
    │   → Plans strategically
    │
    ├─▶ Generation Module
    │   • Sees current task
    │   • Recent context (1000 chars)
    │   • Target details
    │   → Generates tactical commands
    │
    └─▶ Parsing Module
        • Sees raw tool output
        • Tool name
        • Target info
        → Extracts structured data
```

---

## 💾 Data Models

### Core Data Structures

```python
Session
├── session_id: str
├── target: str
├── scope: List[str]
├── current_phase: PentestPhase
├── status: str
├── progress: float
├── created_at: datetime
├── started_at: datetime
├── completed_at: datetime
│
├── target_info: TargetInfo
│   ├── target: str
│   ├── ip_addresses: List[str]
│   ├── open_ports: List[int]
│   ├── services: Dict[int, str]
│   ├── technologies: List[str]
│   ├── operating_system: str
│   └── web_server: str
│
├── todo_list: List[Task]
│   └── Task
│       ├── task_id: str
│       ├── description: str
│       ├── tool: str
│       ├── command: str
│       ├── phase: PentestPhase
│       ├── status: TaskStatus
│       ├── priority: int
│       ├── output: str
│       └── findings_count: int
│
├── completed_tasks: List[Task]
├── failed_tasks: List[Task]
│
├── vulnerabilities: List[Vulnerability]
│   └── Vulnerability
│       ├── vuln_id: str
│       ├── title: str
│       ├── description: str
│       ├── severity: SeverityLevel
│       ├── cvss_score: float
│       ├── cve_id: str
│       ├── target: str
│       ├── port: int
│       ├── service: str
│       ├── url: str
│       ├── evidence: str
│       ├── remediation: str
│       ├── references: List[str]
│       ├── discovered_by: str
│       ├── discovered_at: datetime
│       ├── verified: bool
│       └── exploitable: bool
│
├── findings: List[Finding]
│   └── Finding
│       ├── finding_id: str
│       ├── category: str
│       ├── title: str
│       ├── description: str
│       ├── target: str
│       ├── data: Dict
│       └── discovered_by: str
│
└── conversation_history: List[ConversationMessage]
    └── ConversationMessage
        ├── role: str
        ├── content: str
        ├── module: str
        └── timestamp: datetime
```

---

## 🔐 Security Architecture

### Authorization Flow

```
User Request
    │
    ▼
┌──────────────────────┐
│  API Endpoint        │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────────────┐
│  Request Validation          │
│  • Pydantic models           │
│  • Type checking             │
│  • Required fields           │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│  Target Authorization Check  │
│  • Is target in whitelist?   │
│  • Is authorized=true?        │
│  • config.is_target_allowed() │
└──────┬───────────────────────┘
       │
       ▼ If authorized
       │
┌──────▼───────────────────────┐
│  Command Sanitization        │
│  • Remove dangerous chars    │
│  • Validate parameters       │
│  • Check injection attempts  │
└──────┬───────────────────────┘
       │
       ▼
┌──────▼───────────────────────┐
│  Audit Logging               │
│  • Log all commands          │
│  • Log all parameters        │
│  • Log target and user       │
└──────┬───────────────────────┘
       │
       ▼
┌──────▼───────────────────────┐
│  Rate Limiting               │
│  • Check concurrent scans    │
│  • Check requests/minute     │
│  • Apply backpressure        │
└──────┬───────────────────────┘
       │
       ▼
   Execute Tool
```

---

## 📊 State Machine

### Penetration Test Phases

```
    START
      │
      ▼
┌──────────────────┐
│ RECONNAISSANCE   │
│                  │
│ Tasks:           │
│ • Port scanning  │
│ • Service detect │
│ • Tech ID        │
└────┬─────────────┘
     │
     │ Reasoning: "Have we identified enough targets?"
     │            "Do we have service info?"
     │ → If yes, advance
     │
     ▼
┌──────────────────┐
│   SCANNING       │
│                  │
│ Tasks:           │
│ • Vuln scanning  │
│ • Dir enum       │
│ • Web testing    │
└────┬─────────────┘
     │
     │ Reasoning: "Did we find exploitable vulns?"
     │            "Should we try exploitation?"
     │ → If yes, advance
     │
     ▼
┌──────────────────┐
│  EXPLOITATION    │
│                  │
│ Tasks:           │
│ • SQL injection  │
│ • Exploit verify │
│ • Payload test   │
└────┬─────────────┘
     │
     │ Reasoning: "Have we verified key vulns?"
     │            "Ready for reporting?"
     │ → If yes, advance
     │
     ▼
┌──────────────────┐
│   REPORTING      │
│                  │
│ Tasks:           │
│ • Analyze finds  │
│ • Generate report│
│ • Create JSON    │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│   COMPLETED      │
└──────────────────┘
```

---

## 🛠️ Technology Stack

```
┌─────────────────────────────────────────┐
│          Application Layer              │
│                                         │
│  Python 3.9+                            │
│  └─ Type Hints (Full coverage)         │
│  └─ Async/Await (asyncio)              │
│  └─ Context Managers                    │
└─────────────────────────────────────────┘
         │
         ├─── Web Framework
         │    └─ FastAPI 0.109
         │       ├─ Pydantic validation
         │       ├─ OpenAPI/Swagger
         │       ├─ Async request handling
         │       └─ CORS middleware
         │
         ├─── LLM Integration
         │    └─ Anthropic SDK 0.18
         │       ├─ Claude Sonnet 4.5
         │       ├─ Async API calls
         │       └─ Streaming support
         │
         ├─── Data Validation
         │    └─ Pydantic 2.5
         │       ├─ BaseModel classes
         │       ├─ Field validation
         │       └─ JSON serialization
         │
         ├─── Logging
         │    └─ Python logging
         │       ├─ colorlog (colored output)
         │       ├─ JSON formatter
         │       └─ File rotation
         │
         ├─── Reporting
         │    └─ Jinja2 3.1
         │       ├─ HTML templates
         │       └─ Variable rendering
         │
         └─── HTTP Server
              └─ Uvicorn 0.27
                 ├─ ASGI server
                 ├─ Hot reload
                 └─ Multiple workers

┌─────────────────────────────────────────┐
│        External Services                │
│                                         │
│  Anthropic Claude API                   │
│  └─ Model: claude-sonnet-4-5-20250929  │
│  └─ Endpoint: api.anthropic.com         │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│        System Tools                     │
│                                         │
│  Kali Linux Tools                       │
│  ├─ nmap (network scanning)            │
│  ├─ nikto (web scanning)               │
│  ├─ sqlmap (SQL injection)             │
│  └─ gobuster (dir enumeration)         │
└─────────────────────────────────────────┘
```

---

## 📈 Performance Characteristics

### Concurrency Model

```
API Server (Uvicorn)
    │
    ├─ Worker 1 ─┐
    ├─ Worker 2  │ (Can scale to N workers)
    └─ Worker 3 ─┘
         │
         │ Each worker handles multiple requests concurrently
         │
         ├─ Request 1 (async)
         │   └─ await orchestrator.start_pentest()
         │       └─ await reasoning.plan_initial_tasks()
         │           └─ await anthropic.messages.create()
         │
         ├─ Request 2 (async)
         │   └─ await orchestrator.execute_workflow()
         │       └─ await tool.execute()
         │           └─ await asyncio.create_subprocess_shell()
         │
         └─ Request 3 (async)
             └─ session.get_status()  (fast, no I/O)
```

### Scalability Limits

| Resource | Limit | Reason |
|----------|-------|--------|
| Concurrent Scans | 3 (configurable) | CPU/network constraints |
| LLM Requests/min | 30 (configurable) | API rate limits |
| Session Storage | ~1000s | Disk space |
| Tool Timeout | 300-1800s | Per-tool configuration |
| API Response Time | <100ms | (except long-running ops) |

---

## 🔄 Error Handling Strategy

```
Error Occurs
    │
    ▼
┌────────────────────────────┐
│  Where did it occur?       │
└────┬───────────────────────┘
     │
     ├─▶ API Layer
     │   • HTTPException raised
     │   • Caught by FastAPI
     │   • Converted to JSON response
     │   • Status code set appropriately
     │
     ├─▶ Orchestrator
     │   • Try/except around each operation
     │   • Log error details
     │   • Mark task as failed
     │   • Update session state
     │   • Continue with next task
     │
     ├─▶ LLM Module
     │   • Retry once on failure
     │   • Fall back to defaults
     │   • Log warning
     │   • Return partial result
     │
     └─▶ MCP Tool
         • Timeout handling
         • Process kill on timeout
         • Return error in result dict
         • Don't crash orchestrator
```

---

## 📦 Deployment Architecture

### Development (Current)

```
Developer Machine
    │
    ├─ Python venv
    │  └─ EHPA application
    │     └─ Uvicorn server (1 worker)
    │        └─ Port 8000
    │
    └─ Local filesystem
       ├─ data/ (sessions, findings, reports)
       └─ logs/ (application logs)
```

### Production (Recommended)

```
Load Balancer
    │
    ├─ Server 1
    │  ├─ Nginx (reverse proxy)
    │  │  └─ Port 443 (HTTPS)
    │  │     └─ Forward to :8000
    │  │
    │  ├─ EHPA (systemd service)
    │  │  └─ Uvicorn (4 workers)
    │  │     └─ Port 8000
    │  │
    │  └─ Shared Storage (NFS)
    │     ├─ Sessions
    │     ├─ Findings
    │     └─ Reports
    │
    └─ Server 2 (identical)

Database (Future)
    └─ PostgreSQL
       ├─ Session metadata
       ├─ Vulnerability data
       └─ Audit logs
```

---

This architecture document provides a complete technical overview of the EHPA Task 1 system. For implementation details, see the source code and README.md.
