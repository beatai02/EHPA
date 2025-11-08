/**
 * EHPA Dashboard JavaScript
 * Main dashboard functionality and API integration
 */

// API Configuration
const API_BASE_URL = 'http://localhost:8000';
const WS_URL = 'ws://localhost:8000/api/v1/chat/ws';

// Global State
let currentSession = null;
let websocket = null;
let activeTool = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeTabs();
    initializeWebSocket();
    loadInitialData();
    setupEventListeners();
});

// Tab Navigation
function initializeTabs() {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const tab = link.dataset.tab;
            switchTab(tab);
        });
    });
}

function switchTab(tabName) {
    // Update navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');

    // Load tab-specific data
    loadTabData(tabName);
}

function loadTabData(tabName) {
    switch(tabName) {
        case 'dashboard':
            loadDashboardData();
            break;
        case 'findings':
            loadAllFindings();
            break;
        case 'tools':
            loadTools();
            break;
        case 'osint':
            loadOSINT();
            break;
    }
}

// WebSocket Connection
function initializeWebSocket() {
    try {
        websocket = new WebSocket(WS_URL);

        websocket.onopen = () => {
            console.log('WebSocket connected');
            updateConnectionStatus(true);
        };

        websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        };

        websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            updateConnectionStatus(false);
        };

        websocket.onclose = () => {
            console.log('WebSocket disconnected');
            updateConnectionStatus(false);
            // Attempt reconnection after 5 seconds
            setTimeout(initializeWebSocket, 5000);
        };
    } catch (error) {
        console.error('WebSocket initialization failed:', error);
    }
}

function handleWebSocketMessage(data) {
    console.log('WebSocket message:', data);

    switch(data.type) {
        case 'progress':
            updateScanProgress(data.data);
            break;
        case 'vulnerability_found':
            addVulnerabilityNotification(data.data);
            break;
        case 'phase_complete':
            updatePhaseStatus(data.data);
            break;
        case 'scan_complete':
            handleScanComplete(data.data);
            break;
        case 'chat_response':
            addChatMessage('bot', data.data.message);
            break;
    }
}

function updateConnectionStatus(connected) {
    const indicator = document.getElementById('statusIndicator');
    if (connected) {
        indicator.innerHTML = '<i class="fas fa-circle"></i> Connected';
        indicator.style.color = 'var(--success-color)';
    } else {
        indicator.innerHTML = '<i class="fas fa-circle"></i> Disconnected';
        indicator.style.color = 'var(--danger-color)';
    }
}

// API Calls
async function apiRequest(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        showNotification('Error', error.message, 'error');
        throw error;
    }
}

// Load Initial Data
async function loadInitialData() {
    await loadDashboardData();
    await loadSessions();
}

async function loadDashboardData() {
    try {
        const health = await apiRequest('/api/health');
        console.log('System health:', health);

        // Load active sessions
        const sessions = await apiRequest('/api/v1/pentest/sessions');
        updateStats(sessions);

    } catch (error) {
        console.error('Failed to load dashboard data:', error);
    }
}

async function loadSessions() {
    try {
        const sessions = await apiRequest('/api/v1/pentest/sessions');

        if (sessions.sessions && sessions.sessions.length > 0) {
            currentSession = sessions.sessions[0];
            updateCurrentScan(currentSession);
        }
    } catch (error) {
        console.error('Failed to load sessions:', error);
    }
}

async function loadAllFindings() {
    if (!currentSession) {
        document.getElementById('allFindings').innerHTML = `
            <div class="empty-state">
                <i class="fas fa-shield-alt"></i>
                <p>No active session</p>
            </div>
        `;
        return;
    }

    try {
        const findings = await apiRequest(`/api/v1/pentest/${currentSession.session_id}/findings`);
        displayFindings(findings.vulnerabilities || []);
    } catch (error) {
        console.error('Failed to load findings:', error);
    }
}

async function loadTools() {
    const toolsGrid = document.getElementById('toolsGrid');

    const tools = [
        { name: 'nmap', icon: 'fa-network-wired', description: 'Network scanner' },
        { name: 'nikto', icon: 'fa-spider', description: 'Web vulnerability scanner' },
        { name: 'gobuster', icon: 'fa-folder', description: 'Directory enumeration' },
        { name: 'sqlmap', icon: 'fa-database', description: 'SQL injection tool' },
        { name: 'nuclei', icon: 'fa-atom', description: 'Template-based scanner' },
        { name: 'wpscan', icon: 'fa-wordpress', description: 'WordPress scanner' },
        { name: 'amass', icon: 'fa-sitemap', description: 'Subdomain enumeration' },
        { name: 'theharvester', icon: 'fa-search', description: 'OSINT gathering' },
    ];

    toolsGrid.innerHTML = tools.map(tool => `
        <div class="tool-card" onclick="showToolInfo('${tool.name}')">
            <h4>
                <i class="fas ${tool.icon}"></i>
                ${tool.name}
            </h4>
            <p>${tool.description}</p>
        </div>
    `).join('');
}

async function loadOSINT() {
    try {
        const osint = await apiRequest('/api/v1/osint/recent');
        displayOSINT(osint.items || []);
    } catch (error) {
        console.error('Failed to load OSINT data:', error);
        document.getElementById('osintFeed').innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Failed to load OSINT feeds</p>
            </div>
        `;
    }
}

// Update UI
function updateStats(data) {
    const vulnCounts = data.vulnerability_stats || { critical: 0, high: 0, medium: 0, low: 0 };

    document.getElementById('criticalCount').textContent = vulnCounts.critical || 0;
    document.getElementById('highCount').textContent = vulnCounts.high || 0;
    document.getElementById('mediumCount').textContent = vulnCounts.medium || 0;
    document.getElementById('lowCount').textContent = vulnCounts.low || 0;
}

function updateCurrentScan(session) {
    const currentScan = document.getElementById('currentScan');

    if (!session) {
        currentScan.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-search"></i>
                <p>No active scan</p>
                <button class="btn btn-primary" onclick="showStartScanDialog()">
                    <i class="fas fa-play"></i> Start New Scan
                </button>
            </div>
        `;
        return;
    }

    currentScan.innerHTML = `
        <div class="scan-active">
            <div class="scan-info">
                <div>
                    <strong>Target:</strong> ${session.target}<br>
                    <strong>Phase:</strong> ${session.phase}
                </div>
                <div>
                    <strong>Status:</strong> ${session.status}
                </div>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${session.progress || 0}%">
                    ${session.progress || 0}%
                </div>
            </div>
        </div>
    `;
}

function updateScanProgress(data) {
    const progressFill = document.querySelector('.progress-fill');
    if (progressFill) {
        progressFill.style.width = `${data.progress}%`;
        progressFill.textContent = `${data.progress}%`;
    }

    // Update current task if available
    if (data.current_task) {
        showNotification('Progress', data.current_task, 'info');
    }
}

function displayFindings(vulnerabilities) {
    const container = document.getElementById('allFindings');

    if (!vulnerabilities || vulnerabilities.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-shield-alt"></i>
                <p>No vulnerabilities found</p>
            </div>
        `;
        return;
    }

    container.innerHTML = vulnerabilities.map(vuln => `
        <div class="finding-card ${vuln.severity}">
            <div class="finding-header">
                <div class="finding-title">${vuln.title}</div>
                <span class="severity-badge ${vuln.severity}">${vuln.severity}</span>
            </div>
            <p><strong>Component:</strong> ${vuln.affected_component || 'Unknown'}</p>
            <p><strong>CVSS:</strong> ${vuln.cvss_score || 'N/A'}</p>
            ${vuln.cve_id ? `<p><strong>CVE:</strong> ${vuln.cve_id}</p>` : ''}
            <p>${vuln.description}</p>
            <p><strong>Remediation:</strong> ${vuln.remediation || 'No remediation available'}</p>
        </div>
    `).join('');
}

function displayOSINT(items) {
    const container = document.getElementById('osintFeed');

    if (!items || items.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-newspaper"></i>
                <p>No OSINT data available</p>
            </div>
        `;
        return;
    }

    container.innerHTML = items.slice(0, 20).map(item => `
        <div class="osint-item" style="margin-bottom: 1rem; padding: 1rem; background: var(--bg-darker); border-radius: 8px;">
            <h4>${item.title}</h4>
            <p style="color: var(--text-secondary); font-size: 0.9rem;">${item.source} - ${item.published}</p>
            <p>${item.description || ''}</p>
            ${item.link ? `<a href="${item.link}" target="_blank" style="color: var(--primary-color);">Read more →</a>` : ''}
        </div>
    `).join('');
}

// Start Scan
function showStartScanDialog() {
    document.getElementById('startScanModal').classList.add('active');
}

function closeStartScanDialog() {
    document.getElementById('startScanModal').classList.remove('active');
}

async function startScan() {
    const target = document.getElementById('targetInput').value.trim();
    const authorized = document.getElementById('authorizedCheck').checked;

    if (!target) {
        showNotification('Error', 'Please enter a target', 'error');
        return;
    }

    if (!authorized) {
        showNotification('Error', 'Please confirm authorization', 'error');
        return;
    }

    const scope = Array.from(document.querySelectorAll('input[name="scope"]:checked'))
        .map(cb => cb.value);

    try {
        const response = await apiRequest('/api/v1/pentest/start', {
            method: 'POST',
            body: JSON.stringify({
                target,
                scope,
                authorized
            })
        });

        currentSession = response;
        closeStartScanDialog();
        showNotification('Success', `Scan started on ${target}`, 'success');
        updateCurrentScan(currentSession);

    } catch (error) {
        showNotification('Error', error.message, 'error');
    }
}

// Notifications
function showNotification(title, message, type = 'info') {
    const container = document.getElementById('notifications');
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <strong>${title}</strong><br>
        ${message}
    `;

    container.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

function addVulnerabilityNotification(vuln) {
    showNotification(
        `${vuln.severity.toUpperCase()} Vulnerability`,
        vuln.title,
        vuln.severity === 'critical' ? 'error' : 'warning'
    );

    // Reload findings
    loadAllFindings();
}

function updatePhaseStatus(data) {
    showNotification('Phase Complete', `${data.phase} phase completed`, 'success');
    loadDashboardData();
}

function handleScanComplete(data) {
    showNotification('Scan Complete', 'Penetration test completed!', 'success');
    currentSession.status = 'completed';
    updateCurrentScan(currentSession);
    loadDashboardData();
}

// Event Listeners
function setupEventListeners() {
    // Findings filter
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const severity = btn.dataset.severity;
            filterFindings(severity);
        });
    });
}

function filterFindings(severity) {
    const findings = document.querySelectorAll('.finding-card');

    findings.forEach(finding => {
        if (severity === 'all' || finding.classList.contains(severity)) {
            finding.style.display = 'block';
        } else {
            finding.style.display = 'none';
        }
    });
}

function showToolInfo(toolName) {
    showNotification('Tool Info', `${toolName} - Click to execute`, 'info');
}

// Helper function to escape HTML
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Export functions for use in chat.js
window.dashboard = {
    updateStats,
    updateCurrentScan,
    showNotification,
    apiRequest
};
