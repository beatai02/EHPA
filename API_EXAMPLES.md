# API Examples

Complete examples for all EHPA Task 1 API endpoints.

Base URL: `http://localhost:8000/api/v1`

## Authentication

Currently no authentication required (add for production).

## 1. Health Check

Check if the API is running.

```bash
curl http://localhost:8000/api/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-11-05T10:30:00",
  "services": {
    "orchestrator": "running",
    "llm_reasoning": "available",
    "llm_generation": "available",
    "llm_parsing": "available",
    "mcp_tools": "4 tools available"
  }
}
```

## 2. Start Penetration Test

Create a new pentest session.

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
  "session_id": "ptest_abc123def456",
  "target": "scanme.nmap.org",
  "status": "active",
  "current_phase": "reconnaissance",
  "created_at": "2025-11-05T10:30:00",
  "message": "Penetration test session created. Use /api/v1/pentest/ptest_abc123def456/execute to start workflow."
}
```

## 3. Execute Workflow

Start the automated orchestration loop.

```bash
curl -X POST "http://localhost:8000/api/v1/pentest/ptest_abc123def456/execute"
```

**Response:**
```json
{
  "session_id": "ptest_abc123def456",
  "message": "Workflow execution started in background",
  "status": "running"
}
```

## 4. Get Session Status

Monitor pentest progress.

```bash
curl "http://localhost:8000/api/v1/pentest/ptest_abc123def456/status"
```

**Response:**
```json
{
  "session_id": "ptest_abc123def456",
  "target": "scanme.nmap.org",
  "phase": "scanning",
  "status": "active",
  "progress": 45.5,
  "current_task": "Running nikto scan on port 80",
  "tasks_pending": 3,
  "tasks_completed": 5,
  "findings_count": 12,
  "vulnerabilities_count": 2,
  "duration_minutes": 8.5
}
```

## 5. Get Session Statistics

Detailed session statistics.

```bash
curl "http://localhost:8000/api/v1/pentest/ptest_abc123def456/statistics"
```

**Response:**
```json
{
  "session_id": "ptest_abc123def456",
  "target": "scanme.nmap.org",
  "phase": "scanning",
  "progress": 45.5,
  "duration_minutes": 8.5,
  "tasks": {
    "total": 10,
    "pending": 3,
    "completed": 6,
    "failed": 1
  },
  "findings": {
    "vulnerabilities": 3,
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 0,
    "informational": 0,
    "general_findings": 15
  }
}
```

## 6. Get All Tasks

View task list (pending, completed, failed).

```bash
curl "http://localhost:8000/api/v1/pentest/ptest_abc123def456/tasks"
```

**Response:**
```json
{
  "session_id": "ptest_abc123def456",
  "tasks": {
    "pending": [
      {
        "task_id": "task_xyz789",
        "description": "Run sqlmap on login form",
        "tool": "sqlmap",
        "status": "pending",
        "priority": 2
      }
    ],
    "completed": [
      {
        "task_id": "task_abc123",
        "description": "Scan ports with nmap",
        "tool": "nmap",
        "status": "completed",
        "findings_count": 5
      }
    ],
    "failed": []
  },
  "total_pending": 1,
  "total_completed": 6,
  "total_failed": 0
}
```

## 7. Execute Single Task

Manually execute a specific task.

```bash
curl -X POST "http://localhost:8000/api/v1/pentest/ptest_abc123def456/execute-task" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "task_xyz789"
  }'
```

**Response:**
```json
{
  "task_id": "task_xyz789",
  "status": "completed",
  "findings_count": 2,
  "output_preview": "Starting sqlmap scan...\nParameter 'username' appears to be injectable...",
  "message": "Task task_xyz789 executed successfully"
}
```

## 8. Get Findings

Retrieve all vulnerabilities and findings.

```bash
curl "http://localhost:8000/api/v1/pentest/ptest_abc123def456/findings"
```

**Response:**
```json
{
  "session_id": "ptest_abc123def456",
  "total_vulnerabilities": 3,
  "critical": 0,
  "high": 1,
  "medium": 2,
  "low": 0,
  "informational": 0,
  "vulnerabilities": [
    {
      "vuln_id": "vuln_a1b2c3d4",
      "title": "SQL Injection in login form",
      "description": "The 'username' parameter is vulnerable to boolean-based SQL injection",
      "severity": "high",
      "cvss_score": 8.5,
      "cve_id": null,
      "target": "scanme.nmap.org",
      "port": 443,
      "service": "https",
      "url": "https://scanme.nmap.org/login",
      "evidence": "sqlmap identified boolean-based blind SQL injection in 'username' parameter",
      "remediation": "Use parameterized queries or prepared statements. Never concatenate user input into SQL queries.",
      "references": [
        "https://owasp.org/www-community/attacks/SQL_Injection"
      ],
      "discovered_by": "sqlmap",
      "discovered_at": "2025-11-05T10:35:00",
      "verified": false,
      "exploitable": true
    },
    {
      "vuln_id": "vuln_e5f6g7h8",
      "title": "Outdated Apache version detected",
      "description": "Server is running Apache 2.4.41 which has known vulnerabilities",
      "severity": "medium",
      "cvss_score": 5.3,
      "target": "scanme.nmap.org",
      "port": 80,
      "service": "http",
      "evidence": "Server: Apache/2.4.41 (Ubuntu)",
      "remediation": "Update Apache to the latest stable version",
      "discovered_by": "nmap",
      "discovered_at": "2025-11-05T10:32:00"
    }
  ],
  "general_findings": 15
}
```

## 9. Pause Session

Pause an active pentest.

```bash
curl -X POST "http://localhost:8000/api/v1/pentest/ptest_abc123def456/pause"
```

**Response:**
```json
{
  "session_id": "ptest_abc123def456",
  "status": "paused",
  "message": "Session paused successfully"
}
```

## 10. Resume Session

Resume a paused pentest.

```bash
curl -X POST "http://localhost:8000/api/v1/pentest/ptest_abc123def456/resume"
```

**Response:**
```json
{
  "session_id": "ptest_abc123def456",
  "status": "resuming",
  "message": "Session resume initiated"
}
```

## 11. Generate Report

Create a comprehensive HTML/JSON report.

```bash
curl "http://localhost:8000/api/v1/pentest/ptest_abc123def456/report"
```

**Response:**
```json
{
  "session_id": "ptest_abc123def456",
  "report_path": "/home/user/projects/ehpa-task1/data/reports/pentest_report_ptest_abc123def456_20251105_103000.html",
  "report_url": null,
  "generated_at": "2025-11-05T10:40:00",
  "message": "Report generated successfully"
}
```

## 12. List All Sessions

Get all pentest sessions.

```bash
curl "http://localhost:8000/api/v1/pentest/sessions"
```

**Response:**
```json
{
  "sessions": [
    {
      "session_id": "ptest_abc123def456",
      "target": "scanme.nmap.org",
      "phase": "completed",
      "status": "completed",
      "progress": 100.0,
      "created_at": "2025-11-05T10:30:00",
      "vulnerabilities_count": 3
    },
    {
      "session_id": "ptest_xyz789abc123",
      "target": "testphp.vulnweb.com",
      "phase": "scanning",
      "status": "active",
      "progress": 55.0,
      "created_at": "2025-11-05T11:00:00",
      "vulnerabilities_count": 1
    }
  ],
  "total": 2
}
```

## 13. Delete Session

Remove a session (soft delete).

```bash
curl -X DELETE "http://localhost:8000/api/v1/pentest/ptest_abc123def456"
```

**Response:**
```json
{
  "session_id": "ptest_abc123def456",
  "message": "Session deleted successfully"
}
```

## 14. Get Configuration

View system configuration (non-sensitive).

```bash
curl "http://localhost:8000/api/v1/config"
```

**Response:**
```json
{
  "llm": {
    "model": "claude-sonnet-4-5-20250929",
    "max_tokens": 4096,
    "temperature": 0.7
  },
  "security": {
    "require_target_approval": true,
    "max_concurrent_scans": 3
  },
  "tools": {
    "nmap": "available",
    "nikto": "available",
    "sqlmap": "available",
    "gobuster": "available"
  }
}
```

## 15. List Available Tools

Get information about pentesting tools.

```bash
curl "http://localhost:8000/api/v1/tools"
```

**Response:**
```json
{
  "tools": [
    {
      "tool_name": "nmap",
      "binary_path": "/usr/bin/nmap",
      "default_flags": ["-sV", "-sC", "-T4"],
      "max_timeout": 300,
      "output_format": "xml",
      "schema": {
        "name": "nmap",
        "description": "Network reconnaissance and port scanning",
        "parameters": {
          "target": {
            "type": "string",
            "required": true,
            "description": "Target IP address or domain"
          }
        }
      }
    }
  ],
  "total": 4
}
```

## Error Responses

### 400 Bad Request

```json
{
  "error": "Target not authorized for testing",
  "timestamp": "2025-11-05T10:30:00"
}
```

### 404 Not Found

```json
{
  "error": "Session not found: ptest_invalid123",
  "timestamp": "2025-11-05T10:30:00"
}
```

### 500 Internal Server Error

```json
{
  "error": "Internal server error",
  "detail": "Failed to execute task: Tool timeout",
  "timestamp": "2025-11-05T10:30:00"
}
```

## Python Client Example

Complete example using the API:

```python
import requests
import time
import json

class EHPAClient:
    def __init__(self, base_url="http://localhost:8000/api/v1"):
        self.base_url = base_url

    def start_pentest(self, target, scope=["network"], authorized=True):
        """Start a new penetration test"""
        response = requests.post(
            f"{self.base_url}/pentest/start",
            json={
                "target": target,
                "scope": scope,
                "authorized": authorized
            }
        )
        return response.json()

    def execute_workflow(self, session_id):
        """Start workflow execution"""
        response = requests.post(
            f"{self.base_url}/pentest/{session_id}/execute"
        )
        return response.json()

    def get_status(self, session_id):
        """Get session status"""
        response = requests.get(
            f"{self.base_url}/pentest/{session_id}/status"
        )
        return response.json()

    def get_findings(self, session_id):
        """Get findings"""
        response = requests.get(
            f"{self.base_url}/pentest/{session_id}/findings"
        )
        return response.json()

    def generate_report(self, session_id):
        """Generate report"""
        response = requests.get(
            f"{self.base_url}/pentest/{session_id}/report"
        )
        return response.json()

    def wait_for_completion(self, session_id, poll_interval=10):
        """Wait for pentest to complete"""
        while True:
            status = self.get_status(session_id)
            print(f"Phase: {status['phase']}, Progress: {status['progress']:.1f}%")

            if status['phase'] == 'completed' or status['status'] == 'completed':
                break

            time.sleep(poll_interval)


# Usage
client = EHPAClient()

# Start pentest
session = client.start_pentest("scanme.nmap.org")
session_id = session['session_id']
print(f"Started session: {session_id}")

# Execute workflow
client.execute_workflow(session_id)

# Wait for completion
client.wait_for_completion(session_id)

# Get findings
findings = client.get_findings(session_id)
print(f"\nFound {findings['total_vulnerabilities']} vulnerabilities:")
for vuln in findings['vulnerabilities']:
    print(f"  [{vuln['severity'].upper()}] {vuln['title']}")

# Generate report
report = client.generate_report(session_id)
print(f"\nReport generated: {report['report_path']}")
```

## WebSocket Support (Future)

Real-time updates will be available via WebSocket:

```javascript
// Future implementation
const ws = new WebSocket('ws://localhost:8000/api/v1/pentest/ptest_abc123/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
};
```

---

For more details, see the [Interactive API Documentation](http://localhost:8000/api/docs).
