"""
StackChan GCP Monitor - Interactive Web Dashboard & Avatar Simulator
"""

def get_dashboard_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StackChan GCP Fleet Sentinel</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🤖</text></svg>">
    <style>
        :root {
            --bg-base: #0b0f19;
            --card-bg: rgba(30, 41, 59, 0.7);
            --card-border: rgba(56, 189, 248, 0.2);
            --text-main: #f8fafc;
            --text-dim: #94a3b8;
            --accent-blue: #38bdf8;
            --status-ok: #22c55e;
            --status-warn: #f59e0b;
            --status-crit: #ef4444;
            --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-base);
            background-image: 
                radial-gradient(at 0% 0%, rgba(56, 189, 248, 0.08) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(34, 197, 94, 0.05) 0px, transparent 50%);
            color: var(--text-main);
            font-family: var(--font-family);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 24px 16px;
        }

        .container {
            max-width: 1100px;
            width: 100%;
            display: flex;
            flex-direction: column;
            gap: 24px;
        }

        /* Header Bar */
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 24px;
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            backdrop-filter: blur(12px);
        }

        .logo-area {
            display: flex;
            align-items: center;
            gap: 14px;
        }

        .logo-badge {
            width: 42px;
            height: 42px;
            background: linear-gradient(135deg, #38bdf8, #0284c7);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            box-shadow: 0 0 16px rgba(56, 189, 248, 0.4);
        }

        .logo-text h1 {
            font-size: 1.25rem;
            font-weight: 700;
            letter-spacing: -0.02em;
        }

        .logo-text p {
            font-size: 0.8rem;
            color: var(--text-dim);
        }

        .fleet-status-pill {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px 14px;
            border-radius: 9999px;
            background: rgba(34, 197, 94, 0.1);
            border: 1px solid rgba(34, 197, 94, 0.3);
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--status-ok);
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: currentColor;
            box-shadow: 0 0 8px currentColor;
            animation: pulse 2s infinite ease-in-out;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.4; transform: scale(0.85); }
        }

        /* Main Grid: Avatar on Left, Metrics on Right */
        .dashboard-grid {
            display: grid;
            grid-template-columns: 340px 1fr;
            gap: 24px;
        }

        @media (max-width: 860px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
        }

        /* StackChan Avatar Box */
        .avatar-panel {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 20px;
            padding: 24px;
            display: flex;
            flex-direction: column;
            align-items: center;
            backdrop-filter: blur(12px);
            position: relative;
            overflow: hidden;
        }

        .speech-bubble {
            background: #1e293b;
            border: 1px solid rgba(56, 189, 248, 0.4);
            border-radius: 12px;
            padding: 10px 14px;
            font-size: 0.85rem;
            color: #e2e8f0;
            margin-bottom: 24px;
            text-align: center;
            width: 100%;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            position: relative;
            min-height: 48px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
        }

        .speech-bubble::after {
            content: '';
            position: absolute;
            bottom: -8px;
            left: 50%;
            transform: translateX(-50%);
            border-width: 8px 8px 0;
            border-style: solid;
            border-color: #1e293b transparent transparent transparent;
        }

        /* 3D Robot Head Simulator */
        .robot-stage {
            width: 180px;
            height: 180px;
            position: relative;
            margin-bottom: 20px;
            cursor: pointer;
            perspective: 600px;
        }

        .robot-head {
            width: 160px;
            height: 140px;
            background: #ffffff;
            border-radius: 36px 36px 42px 42px;
            position: absolute;
            top: 15px;
            left: 10px;
            box-shadow: 
                0 12px 24px rgba(0, 0, 0, 0.4),
                inset 0 -6px 8px rgba(0, 0, 0, 0.08),
                inset 0 4px 6px rgba(255, 255, 255, 0.8);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            animation: gentle-bob 3.5s infinite ease-in-out;
            transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
        }

        @keyframes gentle-bob {
            0%, 100% { transform: translateY(0) rotate(0deg); }
            50% { transform: translateY(-8px) rotate(1.5deg); }
        }

        .robot-head.shake {
            animation: head-panic 0.5s infinite alternate ease-in-out !important;
        }

        @keyframes head-panic {
            0% { transform: translateX(-6px) rotate(-4deg); }
            100% { transform: translateX(6px) rotate(4deg); }
        }

        .screen-face {
            width: 124px;
            height: 84px;
            background: #0f172a;
            border-radius: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            position: relative;
            box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.6);
            border: 2px solid #334155;
            overflow: hidden;
        }

        .eyes-row {
            display: flex;
            gap: 28px;
            align-items: center;
            margin-bottom: 8px;
        }

        .eye {
            width: 18px;
            height: 26px;
            background: var(--status-ok);
            border-radius: 10px;
            box-shadow: 0 0 12px currentColor;
            transition: all 0.25s ease;
        }

        /* Mood Expressions */
        .mood-ok .eye {
            background: #22c55e;
            box-shadow: 0 0 12px #22c55e;
            animation: eye-blink 4s infinite;
        }

        .mood-warning .eye {
            background: #f59e0b;
            box-shadow: 0 0 12px #f59e0b;
            height: 20px;
            border-radius: 6px;
        }

        .mood-critical .eye {
            background: #ef4444;
            box-shadow: 0 0 16px #ef4444;
            height: 28px;
            width: 22px;
            animation: eye-alarm 0.4s infinite alternate;
        }

        @keyframes eye-blink {
            0%, 94%, 98%, 100% { transform: scaleY(1); }
            96% { transform: scaleY(0.1); }
        }

        @keyframes eye-alarm {
            0% { transform: scale(0.9); opacity: 0.8; }
            100% { transform: scale(1.15); opacity: 1; }
        }

        .mouth {
            width: 16px;
            height: 6px;
            border-bottom: 3px solid #38bdf8;
            border-radius: 0 0 8px 8px;
            transition: all 0.25s ease;
        }

        .mood-warning .mouth {
            width: 10px;
            height: 10px;
            border: 2px solid #f59e0b;
            border-radius: 50%;
        }

        .mood-critical .mouth {
            width: 22px;
            height: 12px;
            border: 3px solid #ef4444;
            border-radius: 12px;
            background: #ef4444;
        }

        .cheeks {
            display: flex;
            justify-content: space-between;
            width: 90px;
            position: absolute;
            top: 48px;
        }

        .cheek {
            width: 10px;
            height: 6px;
            background: rgba(56, 189, 248, 0.4);
            border-radius: 50%;
        }

        .avatar-controls {
            display: flex;
            gap: 8px;
            margin-top: 12px;
            width: 100%;
        }

        .btn {
            flex: 1;
            padding: 8px 10px;
            border-radius: 8px;
            font-size: 0.75rem;
            font-weight: 600;
            cursor: pointer;
            border: 1px solid transparent;
            transition: all 0.2s ease;
            text-align: center;
        }

        .btn-ok { background: rgba(34, 197, 94, 0.15); color: #22c55e; border-color: rgba(34, 197, 94, 0.3); }
        .btn-ok:hover { background: rgba(34, 197, 94, 0.25); }

        .btn-warn { background: rgba(245, 158, 11, 0.15); color: #f59e0b; border-color: rgba(245, 158, 11, 0.3); }
        .btn-warn:hover { background: rgba(245, 158, 11, 0.25); }

        .btn-crit { background: rgba(239, 68, 68, 0.15); color: #ef4444; border-color: rgba(239, 68, 68, 0.3); }
        .btn-crit:hover { background: rgba(239, 68, 68, 0.25); }

        .btn-live { background: rgba(56, 189, 248, 0.15); color: #38bdf8; border-color: rgba(56, 189, 248, 0.3); }
        .btn-live:hover { background: rgba(56, 189, 248, 0.25); }

        /* Right Panel: Project Selector & Telemetry Cards */
        .metrics-panel {
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .tabs-row {
            display: flex;
            gap: 8px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 8px;
        }

        .tab-btn {
            background: transparent;
            color: var(--text-dim);
            border: none;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }

        .tab-btn:hover {
            color: var(--text-main);
            background: rgba(255, 255, 255, 0.05);
        }

        .tab-btn.active {
            color: var(--accent-blue);
            background: rgba(56, 189, 248, 0.15);
            border: 1px solid rgba(56, 189, 248, 0.3);
        }

        /* Metric Cards Grid */
        .cards-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
        }

        .card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 18px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            backdrop-filter: blur(8px);
            transition: transform 0.2s, border-color 0.2s;
        }

        .card:hover {
            transform: translateY(-2px);
            border-color: rgba(56, 189, 248, 0.4);
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .card-title {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-dim);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .card-icon {
            font-size: 1.2rem;
        }

        .card-val {
            font-size: 1.8rem;
            font-weight: 700;
            letter-spacing: -0.02em;
        }

        .card-subtext {
            font-size: 0.8rem;
            color: var(--text-dim);
            display: flex;
            justify-content: space-between;
        }

        .progress-bar-bg {
            width: 100%;
            height: 6px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 9999px;
            overflow: hidden;
        }

        .progress-bar-fill {
            height: 100%;
            background: var(--accent-blue);
            border-radius: 9999px;
            transition: width 0.5s ease-in-out;
        }

        /* Code/Integration Panel */
        .info-panel {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 16px 20px;
            font-size: 0.85rem;
            color: var(--text-dim);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
        }

        .curl-box {
            background: #0f172a;
            padding: 8px 12px;
            border-radius: 6px;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 0.78rem;
            color: #38bdf8;
            border: 1px solid rgba(255, 255, 255, 0.08);
            user-select: all;
        }

        footer {
            margin-top: auto;
            text-align: center;
            font-size: 0.8rem;
            color: var(--text-dim);
            padding: 16px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Top Navigation -->
        <header>
            <div class="logo-area">
                <div class="logo-badge">🤖</div>
                <div class="logo-text">
                    <h1>StackChan GCP Monitor</h1>
                    <p>M5Stack CoreS3 Autonomous Sentinel • Achtix Cloud</p>
                </div>
            </div>
            <div class="fleet-status-pill" id="fleet-badge">
                <div class="status-dot"></div>
                <span id="fleet-status-text">FLEET OPERATIONAL</span>
            </div>
        </header>

        <!-- Main Body -->
        <div class="dashboard-grid">
            <!-- Left: Avatar Simulator -->
            <div class="avatar-panel">
                <div class="speech-bubble" id="speech-bubble">
                    "All systems nominal! Monitoring insurverse-develop & insurverse-uat."
                </div>

                <div class="robot-stage" onclick="pokeRobot()">
                    <div class="robot-head" id="robot-head">
                        <div class="screen-face mood-ok" id="screen-face">
                            <div class="cheeks">
                                <div class="cheek"></div>
                                <div class="cheek"></div>
                            </div>
                            <div class="eyes-row">
                                <div class="eye"></div>
                                <div class="eye"></div>
                            </div>
                            <div class="mouth"></div>
                        </div>
                    </div>
                </div>

                <div style="font-size:0.8rem; color:var(--text-dim); margin-bottom:12px;">
                    StackChan Face Simulator (Tap head to poke!)
                </div>

                <div class="avatar-controls">
                    <button class="btn btn-ok" onclick="setMood('ok', 'Simulated: All systems green!')">Happy</button>
                    <button class="btn btn-warn" onclick="setMood('warning', 'Simulated: High CPU load warning!')">Worried</button>
                    <button class="btn btn-crit" onclick="setMood('critical', 'Simulated: Alert! Incident detected!')">Panic</button>
                    <button class="btn btn-live" onclick="loadLiveTelemetry()">Live Sync</button>
                </div>
            </div>

            <!-- Right: Project Tabs & Metrics Grid -->
            <div class="metrics-panel">
                <!-- Project Tabs -->
                <div class="tabs-row" id="tabs-container">
                    <button class="tab-btn active" onclick="switchProject(event, '')">ALL FLEET</button>
                    <button class="tab-btn" onclick="switchProject(event, 'insurverse-develop')">insurverse-develop</button>
                    <button class="tab-btn" onclick="switchProject(event, 'insurverse-uat')">insurverse-uat</button>
                </div>

                <!-- 6 Metric Cards -->
                <div class="cards-grid">
                    <!-- GKE Kubernetes -->
                    <div class="card">
                        <div class="card-header">
                            <span class="card-title">GKE Kubernetes</span>
                            <span class="card-icon">☸️</span>
                        </div>
                        <div class="card-val" id="val-gke-nodes">--</div>
                        <div class="card-subtext">
                            <span id="sub-gke-pods">Active Pods: --</span>
                            <span id="sub-gke-cpu">CPU: --%</span>
                        </div>
                        <div class="progress-bar-bg">
                            <div class="progress-bar-fill" id="bar-gke-cpu" style="width: 25%;"></div>
                        </div>
                    </div>

                    <!-- Compute Engine VMs -->
                    <div class="card">
                        <div class="card-header">
                            <span class="card-title">Compute Engine VMs</span>
                            <span class="card-icon">🖥️</span>
                        </div>
                        <div class="card-val" id="val-vm-count">--</div>
                        <div class="card-subtext">
                            <span id="sub-vm-status">Running / Total</span>
                            <span id="sub-vm-cpu">Avg CPU: --%</span>
                        </div>
                        <div class="progress-bar-bg">
                            <div class="progress-bar-fill" id="bar-vm-cpu" style="width: 20%; background:#22c55e;"></div>
                        </div>
                    </div>

                    <!-- Cloud SQL Instances -->
                    <div class="card">
                        <div class="card-header">
                            <span class="card-title">Cloud SQL Database</span>
                            <span class="card-icon">🗄️</span>
                        </div>
                        <div class="card-val" id="val-sql-count">--</div>
                        <div class="card-subtext">
                            <span id="sub-sql-status">Runnable Instances</span>
                            <span id="sub-sql-storage">Storage: 45%</span>
                        </div>
                        <div class="progress-bar-bg">
                            <div class="progress-bar-fill" id="bar-sql-storage" style="width: 45%; background:#38bdf8;"></div>
                        </div>
                    </div>

                    <!-- Cloud Run Services -->
                    <div class="card">
                        <div class="card-header">
                            <span class="card-title">Cloud Run Services</span>
                            <span class="card-icon">🚀</span>
                        </div>
                        <div class="card-val" id="val-run-count">--</div>
                        <div class="card-subtext">
                            <span id="sub-run-rps">Traffic: -- req/s</span>
                            <span style="color:#22c55e;">5xx: 0.0%</span>
                        </div>
                        <div class="progress-bar-bg">
                            <div class="progress-bar-fill" style="width: 35%; background:#38bdf8;"></div>
                        </div>
                    </div>

                    <!-- BigQuery Analytics -->
                    <div class="card">
                        <div class="card-header">
                            <span class="card-title">BigQuery Data</span>
                            <span class="card-icon">📊</span>
                        </div>
                        <div class="card-val" id="val-bq-slots">-- slots</div>
                        <div class="card-subtext">
                            <span id="sub-bq-billed">Billed: -- GB</span>
                            <span>Errors: 0</span>
                        </div>
                        <div class="progress-bar-bg">
                            <div class="progress-bar-fill" style="width: 15%; background:#a855f7;"></div>
                        </div>
                    </div>

                    <!-- Cloud Billing -->
                    <div class="card">
                        <div class="card-header">
                            <span class="card-title">Estimated Billing</span>
                            <span class="card-icon">💳</span>
                        </div>
                        <div class="card-val" id="val-billing-mtd">$--</div>
                        <div class="card-subtext">
                            <span id="sub-billing-today">Today: $--</span>
                            <span id="sub-billing-budget">Budget: --%</span>
                        </div>
                        <div class="progress-bar-bg">
                            <div class="progress-bar-fill" id="bar-billing-budget" style="width: 30%; background:#22c55e;"></div>
                        </div>
                    </div>
                </div>

                <!-- API & Device Integration Panel -->
                <div class="info-panel">
                    <div>
                        <strong>Device Hook:</strong> HTTP Basic Auth <code>stackchan1</code>
                    </div>
                    <div class="curl-box">
                        curl -H "Authorization: Basic &lt;credentials&gt;" https://stackchan.achtix.com/api/v1/gcp/status
                    </div>
                    <div id="sync-timer">Last poll: Just now</div>
                </div>
            </div>
        </div>

        <footer>
            StackChan GCP Monitor Bridge • Built with FastAPI & LVGL on ESP32-S3
        </footer>
    </div>

    <script>
        let currentProject = '';
        let lastLiveTelemetry = null;
        let lastLatencyMs = 0;
        let isManualOverride = false;

        async function fetchTelemetry(projectId = '') {
            try {
                const url = projectId ? `/api/v1/gcp/status?project=${encodeURIComponent(projectId)}` : '/api/v1/gcp/status';
                const t0 = performance.now();
                const resp = await fetch(url);
                lastLatencyMs = Math.round(performance.now() - t0);
                if (resp.status === 401) {
                    console.warn("Unauthorized on bridge API");
                    return null;
                }
                const data = await resp.json();
                lastLiveTelemetry = data;
                return data;
            } catch (err) {
                console.error("Telemetry fetch failed:", err);
                return null;
            }
        }

        function updateTabs(projectsSummary, activePid) {
            const container = document.getElementById('tabs-container');
            if (!container || !projectsSummary || projectsSummary.length === 0) return;

            // Only rebuild tabs if project list changed or not built
            const currentTabBtns = container.querySelectorAll('.tab-btn');
            if (currentTabBtns.length !== projectsSummary.length + 1) {
                let html = `<button class="tab-btn ${!activePid ? 'active' : ''}" onclick="switchProject(event, '')">ALL FLEET</button>`;
                for (const p of projectsSummary) {
                    const pid = p.project_id || '';
                    const isActive = (activePid === pid) ? 'active' : '';
                    html += `<button class="tab-btn ${isActive}" onclick="switchProject(event, '${pid}')">${pid}</button>`;
                }
                container.innerHTML = html;
            }
        }

        function renderData(data) {
            if (!data) return;

            // Header status
            const badge = document.getElementById('fleet-badge');
            const badgeText = document.getElementById('fleet-status-text');
            const status = data.status || 'ok';

            if (status === 'ok') {
                badge.style.color = 'var(--status-ok)';
                badge.style.borderColor = 'rgba(34, 197, 94, 0.3)';
                badge.style.background = 'rgba(34, 197, 94, 0.1)';
                badgeText.innerText = (data.project_id || 'FLEET') + ' NOMINAL';
            } else if (status === 'warning') {
                badge.style.color = 'var(--status-warn)';
                badge.style.borderColor = 'rgba(245, 158, 11, 0.3)';
                badge.style.background = 'rgba(245, 158, 11, 0.1)';
                badgeText.innerText = (data.project_id || 'FLEET') + ' WARNING';
            } else {
                badge.style.color = 'var(--status-crit)';
                badge.style.borderColor = 'rgba(239, 68, 68, 0.3)';
                badge.style.background = 'rgba(239, 68, 68, 0.1)';
                badgeText.innerText = (data.project_id || 'FLEET') + ' INCIDENT';
            }

            // Sync dynamic tabs if summary available
            if (data.projects_summary) {
                updateTabs(data.projects_summary, currentProject);
            }

            // Cards
            const gke = data.gke || {};
            document.getElementById('val-gke-nodes').innerText = (gke.nodes_up || 0) + ' Nodes';
            document.getElementById('sub-gke-pods').innerText = 'Pods: ' + (gke.pods_running || 0);
            document.getElementById('sub-gke-cpu').innerText = 'CPU: ' + (gke.cpu_pct || 0) + '%';
            document.getElementById('bar-gke-cpu').style.width = Math.min(100, (gke.cpu_pct || 20)) + '%';

            const vm = data.vm || {};
            document.getElementById('val-vm-count').innerText = (vm.instances_running || 0) + ' / ' + (vm.instances_total || 0);
            document.getElementById('sub-vm-cpu').innerText = 'Avg CPU: ' + (vm.avg_cpu_pct || 0) + '%';
            document.getElementById('bar-vm-cpu').style.width = Math.min(100, (vm.avg_cpu_pct || 20)) + '%';

            const sql = data.cloud_sql || {};
            document.getElementById('val-sql-count').innerText = (sql.instances_up || 0) + ' DBs';
            document.getElementById('sub-sql-storage').innerText = 'Storage: ' + (sql.storage_pct || 45) + '%';

            const run = data.cloud_run || {};
            document.getElementById('val-run-count').innerText = (run.services_count || 0) + ' Services';
            document.getElementById('sub-run-rps').innerText = 'Traffic: ' + (run.req_per_sec || 0) + ' req/s';

            const bq = data.bigquery || {};
            document.getElementById('val-bq-slots').innerText = (bq.slot_usage || 0) + ' Slots';
            document.getElementById('sub-bq-billed').innerText = 'Billed: ' + (bq.today_gb_billed || 0) + ' GB';

            const bill = data.billing || {};
            document.getElementById('val-billing-mtd').innerText = '$' + (bill.mtd_usd || 0).toFixed(2);
            document.getElementById('sub-billing-today').innerText = 'Today: $' + (bill.today_usd || 0).toFixed(2);
            document.getElementById('sub-billing-budget').innerText = 'Budget: ' + (bill.budget_pct || 0) + '%';
            document.getElementById('bar-billing-budget').style.width = Math.min(100, (bill.budget_pct || 20)) + '%';

            // Sync Mood if not manual override
            if (!isManualOverride) {
                if (status === 'ok') {
                    setMood('ok', `Nominal! Monitored ${data.is_fleet ? 'all ' + data.total_projects + ' projects' : data.project_id}.`);
                } else if (status === 'warning') {
                    setMood('warning', `Attention: Warning in ${data.project_id}!`);
                } else {
                    setMood('critical', `ALERT: Incident detected in ${data.project_id}!`);
                }
            }

            document.getElementById('sync-timer').innerHTML = 'Last poll: ' + new Date().toLocaleTimeString() + ' &bull; <span style="color:#38bdf8;font-weight:600;">⚡ ' + lastLatencyMs + 'ms</span>';
        }

        function setMood(mood, text) {
            const face = document.getElementById('screen-face');
            const head = document.getElementById('robot-head');
            const bubble = document.getElementById('speech-bubble');

            face.className = 'screen-face mood-' + mood;
            bubble.innerText = `"${text}"`;

            if (mood === 'critical') {
                head.classList.add('shake');
            } else {
                head.classList.remove('shake');
            }
        }

        function pokeRobot() {
            const head = document.getElementById('robot-head');
            head.style.transform = 'translateY(12px) rotate(5deg) scale(0.95)';
            setMood('ok', 'Tee-hee! That tickles! StackChan is watching your fleet!');
            setTimeout(() => {
                head.style.transform = '';
            }, 300);
        }

        async function switchProject(evt, pid) {
            currentProject = pid;
            isManualOverride = false;

            const tabs = document.querySelectorAll('.tab-btn');
            tabs.forEach(t => t.classList.remove('active'));
            if (evt && evt.currentTarget) {
                evt.currentTarget.classList.add('active');
            }

            const data = await fetchTelemetry(pid);
            renderData(data);
        }

        async function loadLiveTelemetry() {
            isManualOverride = false;
            const data = await fetchTelemetry(currentProject);
            renderData(data);
        }

        // Auto-refresh loop every 5 seconds
        setInterval(async () => {
            if (!isManualOverride) {
                const data = await fetchTelemetry(currentProject);
                renderData(data);
            }
        }, 5000);

        // Initial Load
        loadLiveTelemetry();
    </script>
</body>
</html>
"""
