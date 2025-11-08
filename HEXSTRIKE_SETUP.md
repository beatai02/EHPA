# Hexstrike MCP Integration Guide

Complete guide for integrating Hexstrike MCP Server with EHPA to access 150+ security tools.

---

## 📋 Table of Contents

1. [What is Hexstrike MCP?](#what-is-hexstrike-mcp)
2. [Why Use Hexstrike?](#why-use-hexstrike)
3. [Installation Options](#installation-options)
4. [Quick Start](#quick-start)
5. [Configuration](#configuration)
6. [Available Tools](#available-tools)
7. [Usage Examples](#usage-examples)
8. [Troubleshooting](#troubleshooting)
9. [Alternative: Direct Tool Execution](#alternative-direct-tool-execution)

---

## What is Hexstrike MCP?

**Hexstrike MCP (Model Context Protocol)** is a unified interface that provides access to 150+ security tools through a single API. Instead of integrating each tool individually, EHPA connects to Hexstrike MCP once and gains access to all tools.

### Architecture

```
EHPA System
    ↓
Hexstrike MCP Client (src/mcp/hexstrike_wrapper.py)
    ↓
Hexstrike MCP Server (http://localhost:8888)
    ↓
150+ Security Tools (nmap, nikto, sqlmap, metasploit, etc.)
```

---

## Why Use Hexstrike?

### Benefits

✅ **Unified Interface**: One API for all tools
✅ **150+ Tools**: Access to comprehensive tool suite
✅ **Standardized Output**: Consistent response format
✅ **Auto-Discovery**: Tools registered automatically
✅ **Version Management**: Tool versions managed centrally
✅ **Execution Sandboxing**: Secure tool execution
✅ **Async Support**: Parallel tool execution
✅ **Error Handling**: Centralized timeout and error management

### Tool Categories

- **Network Scanning**: nmap, masscan, rustscan, zmap
- **Web Scanning**: nikto, nuclei, wpscan, whatweb
- **Directory Enumeration**: gobuster, dirb, ffuf, feroxbuster
- **Service Enumeration**: enum4linux, dnsenum, smbclient
- **OSINT**: theharvester, shodan, amass, subfinder, recon-ng
- **Exploitation**: metasploit, sqlmap, searchsploit
- **Password Cracking**: hashcat, john, hydra, medusa
- **Wireless**: aircrack-ng, wifite, reaver
- **Post-Exploitation**: mimikatz, bloodhound, linpeas, winpeas

---

## Installation Options

### Option 1: Cloud-Hosted Hexstrike MCP (Recommended)

If Hexstrike provides a hosted service:

```bash
# 1. Sign up at https://hexstrike.io/
# 2. Get your API key from dashboard
# 3. Add to .env
echo "HEXSTRIKE_API_KEY=your-key-here" >> .env
echo "HEXSTRIKE_MCP_URL=https://mcp.hexstrike.io" >> .env
```

### Option 2: Self-Hosted Hexstrike MCP Server

Run your own local Hexstrike MCP server:

```bash
# 1. Install Hexstrike MCP Server
pip install hexstrike-mcp-server

# OR using Docker
docker pull hexstrike/mcp-server:latest

# 2. Start the server
hexstrike-mcp serve --port 8888

# OR with Docker
docker run -d -p 8888:8888 \
  --name hexstrike-mcp \
  -v /var/run/docker.sock:/var/run/docker.sock \
  hexstrike/mcp-server:latest

# 3. Verify server is running
curl http://localhost:8888/health
```

### Option 3: Manual Installation from Source

```bash
# Clone Hexstrike MCP repository
git clone https://github.com/hexstrike/mcp-server.git
cd mcp-server

# Install dependencies
pip install -r requirements.txt

# Configure tools (Kali Linux tools should auto-detect)
cp config.example.yaml config.yaml

# Start server
python -m hexstrike_mcp.server --host 0.0.0.0 --port 8888
```

---

## Quick Start

### 1. Install Hexstrike Dependencies

```bash
# Install Hexstrike client libraries
pip install hexstrike-mcp-client>=1.0.0

# OR install with EHPA dev extras
pip install -e ".[hexstrike]"
```

### 2. Configure Environment

Edit your `.env` file:

```bash
# Hexstrike Configuration
HEXSTRIKE_ENABLED=true
HEXSTRIKE_MCP_URL=http://localhost:8888
HEXSTRIKE_API_KEY=your-api-key-here  # If required
```

### 3. Start Hexstrike MCP Server

```bash
# Using Docker (recommended)
docker run -d -p 8888:8888 \
  --name hexstrike-mcp \
  hexstrike/mcp-server:latest

# OR using Python
hexstrike-mcp serve --port 8888
```

### 4. Verify Connection

```bash
# Test connection
python -c "
import asyncio
from src.mcp.hexstrike_wrapper import HexstrikeMCPClient

async def test():
    client = HexstrikeMCPClient('http://localhost:8888')
    connected = await client.connect()
    if connected:
        tools = client.get_available_tools()
        print(f'✅ Connected! {len(tools)} tools available')
    else:
        print('❌ Connection failed')
    await client.close()

asyncio.run(test())
"
```

### 5. Start EHPA

```bash
# Start EHPA server (it will auto-connect to Hexstrike)
python main.py
```

You should see in the logs:
```
✅ Connected to Hexstrike MCP server
📋 150 tools available from Hexstrike
```

---

## Configuration

### EHPA Configuration (configs/tools.yaml)

```yaml
hexstrike:
  enabled: true
  mcp_url: "http://localhost:8888"
  api_key_env: "HEXSTRIKE_API_KEY"
  timeout: 300
  retry_attempts: 3
  fallback_to_direct: true  # Use direct tool execution if Hexstrike unavailable
```

### Hexstrike Server Configuration

Create `hexstrike-config.yaml`:

```yaml
# Hexstrike MCP Server Configuration

server:
  host: "0.0.0.0"
  port: 8888
  workers: 4

security:
  require_api_key: true
  allowed_ips:
    - "127.0.0.1"
    - "::1"
  rate_limit: 100  # requests per minute

tools:
  # Auto-detect Kali Linux tools
  auto_discover: true
  tool_paths:
    - /usr/bin
    - /usr/local/bin
    - /opt/

  # Tool-specific configurations
  nmap:
    max_ports: 65535
    default_timeout: 300

  metasploit:
    enabled: true
    require_approval: true

  sqlmap:
    enabled: true
    require_approval: true
    risk_level_limit: 2

logging:
  level: INFO
  format: json
  file: /var/log/hexstrike-mcp/server.log

execution:
  sandbox: true
  max_parallel_tasks: 10
  default_timeout: 600
```

---

## Available Tools

### Network Scanning Tools (9)

```python
# Via Hexstrike
await hexstrike.execute_tool("nmap", {
    "target": "192.168.1.1",
    "ports": "1-1000",
    "scan_type": "syn"
})

await hexstrike.execute_tool("masscan", {
    "target": "192.168.1.0/24",
    "ports": "1-65535",
    "rate": 10000
})

await hexstrike.execute_tool("rustscan", {
    "target": "192.168.1.1",
    "batch_size": 4500
})
```

**Available**: nmap, masscan, rustscan, zmap, unicornscan, hping3, ping, traceroute, whois

### Web Scanning Tools (15)

```python
# Nikto
await hexstrike.execute_tool("nikto", {
    "target": "http://example.com",
    "tuning": "all"
})

# Nuclei
await hexstrike.execute_tool("nuclei", {
    "target": "http://example.com",
    "severity": ["critical", "high"],
    "templates": "cves,vulnerabilities"
})

# WPScan
await hexstrike.execute_tool("wpscan", {
    "url": "http://wordpress-site.com",
    "enumerate": "vp,vt,u"  # plugins, themes, users
})
```

**Available**: nikto, nuclei, wpscan, whatweb, wafw00f, wapiti, skipfish, arachni, burpsuite, owasp-zap, dirb, dirbuster, gobuster, ffuf, feroxbuster

### OSINT Tools (12)

```python
# TheHarvester
await hexstrike.execute_tool("theharvester", {
    "domain": "example.com",
    "sources": ["google", "bing", "shodan"]
})

# Shodan
await hexstrike.execute_tool("shodan", {
    "query": "apache",
    "api_key": "your-shodan-key"
})

# Amass
await hexstrike.execute_tool("amass", {
    "domain": "example.com",
    "mode": "passive"
})
```

**Available**: theharvester, shodan, amass, subfinder, assetfinder, findomain, recon-ng, maltego, spiderfoot, censys, securitytrails, dnsdumpster

### Exploitation Tools (20+)

```python
# SQLMap
await hexstrike.execute_tool("sqlmap", {
    "url": "http://example.com/login.php?id=1",
    "level": 3,
    "risk": 2
})

# Metasploit (requires approval)
await hexstrike.execute_tool("metasploit", {
    "module": "exploit/windows/smb/ms17_010_eternalblue",
    "target": "192.168.1.100",
    "payload": "windows/x64/meterpreter/reverse_tcp"
})

# SearchSploit
await hexstrike.execute_tool("searchsploit", {
    "query": "Apache 2.4.49"
})
```

**Available**: sqlmap, metasploit, searchsploit, exploitdb, msfvenom, commix, xsser, beef, empire, covenant, cobalt-strike, etc.

### Full Tool List

Get the complete list programmatically:

```python
from src.mcp.hexstrike_wrapper import HexstrikeMCPClient

async def list_all_tools():
    async with HexstrikeMCPClient("http://localhost:8888") as client:
        tools = client.get_available_tools()
        print(f"Total tools: {len(tools)}")

        # Group by category
        from src.mcp.hexstrike_wrapper import HEXSTRIKE_TOOL_CATEGORIES
        for category, tool_list in HEXSTRIKE_TOOL_CATEGORIES.items():
            print(f"\n{category}:")
            for tool in tool_list:
                if tool in tools:
                    print(f"  ✅ {tool}")
                else:
                    print(f"  ❌ {tool} (not available)")
```

---

## Usage Examples

### Example 1: Single Tool Execution

```python
from src.mcp.hexstrike_wrapper import HexstrikeMCPClient
import asyncio

async def run_nmap_scan():
    client = HexstrikeMCPClient(
        mcp_url="http://localhost:8888",
        api_key="your-api-key"
    )

    # Connect
    await client.connect()

    # Execute nmap
    result = await client.execute_tool(
        "nmap",
        {
            "target": "scanme.nmap.org",
            "ports": "1-1000",
            "scan_type": "service",
            "timing": 4
        },
        timeout=300
    )

    print(f"Status: {result['status']}")
    print(f"Output: {result['output']}")
    print(f"Duration: {result['duration']}s")

    await client.close()

asyncio.run(run_nmap_scan())
```

### Example 2: Batch Tool Execution

```python
async def run_full_web_scan(url):
    client = HexstrikeMCPClient("http://localhost:8888")
    await client.connect()

    # Define all scans
    tasks = [
        {"tool": "whatweb", "params": {"url": url}},
        {"tool": "nikto", "params": {"target": url}},
        {"tool": "nuclei", "params": {"target": url, "severity": ["critical", "high"]}},
        {"tool": "wpscan", "params": {"url": url}} if "wordpress" in url else None
    ]

    # Remove None values
    tasks = [t for t in tasks if t]

    # Execute all in parallel
    results = await client.execute_batch(tasks)

    # Process results
    for result in results:
        print(f"\n{result['tool']}: {result['status']}")
        if result['status'] == 'success':
            print(f"Found {len(result.get('parsed', {}).get('vulnerabilities', []))} vulns")

    await client.close()

asyncio.run(run_full_web_scan("http://example.com"))
```

### Example 3: Integration with EHPA Orchestrator

```python
# In EHPA orchestrator
from src.core.orchestrator import Orchestrator

# The orchestrator automatically uses Hexstrike if enabled
orchestrator = Orchestrator()

# Start a pentest - tools will execute via Hexstrike
session = await orchestrator.start_pentest(
    target="scanme.nmap.org",
    scope=["network", "web"],
    authorized=True
)

# Execute workflow - all tools run through Hexstrike
await orchestrator.execute_workflow(session.session_id)
```

---

## Troubleshooting

### Issue 1: Connection Failed

**Symptom**: `❌ Failed to connect to Hexstrike MCP: Connection refused`

**Solutions**:
```bash
# Check if Hexstrike server is running
curl http://localhost:8888/health

# Check Docker container status
docker ps | grep hexstrike

# Check server logs
docker logs hexstrike-mcp

# Restart server
docker restart hexstrike-mcp
```

### Issue 2: Tool Not Found

**Symptom**: `Tool 'nmap' not in available tools list`

**Solutions**:
```bash
# Refresh tool list
curl http://localhost:8888/tools

# Check tool is installed
which nmap

# Restart Hexstrike to re-detect tools
docker restart hexstrike-mcp
```

### Issue 3: Authentication Failed

**Symptom**: `401 Unauthorized`

**Solutions**:
```bash
# Check API key in .env
cat .env | grep HEXSTRIKE_API_KEY

# Verify API key with server
curl -H "Authorization: Bearer your-api-key" \
  http://localhost:8888/tools
```

### Issue 4: Execution Timeout

**Symptom**: `Tool execution timeout after 300s`

**Solutions**:
```python
# Increase timeout for slow tools
result = await client.execute_tool(
    "nmap",
    {"target": "192.168.1.0/24"},
    timeout=900  # 15 minutes
)

# Or in .env
NMAP_TIMEOUT=900
```

### Issue 5: Hexstrike Unavailable

**Symptom**: Hexstrike server is down

**Solution**: EHPA automatically falls back to direct tool execution if configured:

```yaml
# configs/tools.yaml
hexstrike:
  fallback_to_direct: true
```

The system will use direct MCP tool servers (`src/mcp/*.py`) as fallback.

---

## Alternative: Direct Tool Execution

If you don't want to use Hexstrike, you can use direct tool execution:

### Disable Hexstrike

```bash
# In .env
HEXSTRIKE_ENABLED=false
```

### Direct MCP Tool Servers

EHPA includes built-in MCP servers for primary tools:
- `src/mcp/nmap_server.py`
- `src/mcp/nikto_server.py`
- `src/mcp/sqlmap_server.py`
- `src/mcp/gobuster_server.py`
- And more...

These execute tools directly without Hexstrike.

### Pros and Cons

**Hexstrike MCP:**
- ✅ 150+ tools
- ✅ Unified interface
- ✅ Auto-discovery
- ❌ Requires server
- ❌ Network dependency

**Direct Execution:**
- ✅ No server needed
- ✅ Lower latency
- ✅ Simpler setup
- ❌ Fewer tools (10-15)
- ❌ Manual integration for new tools

---

## Advanced Configuration

### Custom Tool Registration

Add custom tools to Hexstrike:

```yaml
# hexstrike-config.yaml
custom_tools:
  my_custom_scanner:
    binary_path: /opt/my-scanner/scan.sh
    category: web_scanning
    parameters:
      target:
        type: string
        required: true
    timeout: 600
```

### Load Balancing

Run multiple Hexstrike instances:

```bash
# Start multiple servers
docker run -d -p 8888:8888 --name hexstrike-1 hexstrike/mcp-server
docker run -d -p 8889:8888 --name hexstrike-2 hexstrike/mcp-server

# Configure EHPA to use multiple servers
# (requires custom load balancer implementation)
```

### Monitoring

Monitor Hexstrike performance:

```bash
# Server metrics endpoint
curl http://localhost:8888/metrics

# Response includes:
# - Total requests
# - Average execution time
# - Active tasks
# - Tool usage stats
```

---

## Resources

- **Hexstrike Documentation**: https://docs.hexstrike.io/mcp
- **MCP Protocol Spec**: https://modelcontextprotocol.io/
- **EHPA GitHub**: https://github.com/yourusername/ehpa-task1
- **Support**: Create issue at GitHub or contact support@hexstrike.io

---

## Quick Reference

```bash
# Start Hexstrike (Docker)
docker run -d -p 8888:8888 hexstrike/mcp-server

# Test connection
curl http://localhost:8888/health

# List tools
curl http://localhost:8888/tools

# Execute tool
curl -X POST http://localhost:8888/execute \
  -H "Content-Type: application/json" \
  -d '{"tool":"nmap","params":{"target":"scanme.nmap.org"}}'

# View logs
docker logs hexstrike-mcp

# Restart server
docker restart hexstrike-mcp

# Stop server
docker stop hexstrike-mcp
```

---

**Last Updated**: November 2025
**EHPA Version**: 1.0.0
**Hexstrike MCP Version**: 1.0.0+
