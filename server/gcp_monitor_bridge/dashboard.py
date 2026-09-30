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

        .robots-panel {
            background: rgba(30, 41, 59, 0.7);
            border-radius: 12px;
            padding: 14px 18px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            margin-bottom: 12px;
        }

        .robots-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .robots-title {
            font-size: 0.85rem;
            font-weight: 700;
            color: #f1f5f9;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .robots-count-badge {
            background: rgba(34, 197, 94, 0.15);
            color: #4ade80;
            font-size: 0.72rem;
            padding: 2px 8px;
            border-radius: 9999px;
            font-weight: 600;
            border: 1px solid rgba(34, 197, 94, 0.3);
        }

        .robots-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(310px, 1fr));
            gap: 12px;
        }

        .robot-card {
            background: #0f172a;
            border-radius: 10px;
            padding: 12px 16px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            display: flex;
            flex-direction: column;
            gap: 10px;
            transition: all 0.2s ease;
        }

        .robot-card:hover {
            border-color: rgba(56, 189, 248, 0.5);
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
        }

        .robot-card-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .robot-card-left {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .robot-status-dot {
            width: 9px;
            height: 9px;
            border-radius: 50%;
            background: #22c55e;
            box-shadow: 0 0 8px #22c55e;
            flex-shrink: 0;
        }

        .robot-status-dot.offline {
            background: #64748b;
            box-shadow: none;
        }

        .robot-name {
            font-size: 0.9rem;
            font-weight: 700;
            color: #f8fafc;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .robot-mac {
            font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
            font-size: 0.72rem;
            color: var(--text-dim);
        }

        .robot-meta {
            font-size: 0.7rem;
            color: var(--text-dim);
            margin-top: 1px;
        }

        .robot-target-badge {
            background: rgba(56, 189, 248, 0.15);
            color: #38bdf8;
            font-size: 0.75rem;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 6px;
            border: 1px solid rgba(56, 189, 248, 0.3);
            font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
            display: inline-block;
        }

        .robot-features-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-top: 6px;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            font-size: 0.72rem;
            color: var(--text-dim);
        }

        .feature-pills {
            display: flex;
            gap: 6px;
            align-items: center;
        }

        .feature-pill {
            background: rgba(255, 255, 255, 0.05);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.68rem;
        }

        .feature-pill.active {
            background: rgba(34, 197, 94, 0.1);
            color: #4ade80;
            border: 1px solid rgba(34, 197, 94, 0.2);
        }

        .btn-configure {
            background: rgba(56, 189, 248, 0.15);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.3);
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }

        .btn-configure:hover {
            background: rgba(56, 189, 248, 0.3);
            color: #fff;
        }

        .robot-empty {
            color: var(--text-dim);
            font-size: 0.8rem;
            font-style: italic;
            padding: 12px 0;
            text-align: center;
            grid-column: 1 / -1;
        }

        /* Modal Dialog Styling */
        .modal-backdrop {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(6px);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }

        .modal-backdrop.active {
            display: flex;
        }

        .modal-box {
            background: #131b2e;
            border: 1px solid rgba(56, 189, 248, 0.3);
            border-radius: 16px;
            max-width: 480px;
            width: 90%;
            padding: 24px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);
            display: flex;
            flex-direction: column;
            gap: 16px;
            animation: modalPop 0.2s ease-out;
        }

        @keyframes modalPop {
            from { transform: scale(0.95); opacity: 0; }
            to { transform: scale(1); opacity: 1; }
        }

        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            padding-bottom: 12px;
        }

        .modal-title {
            font-size: 1.1rem;
            font-weight: 700;
            color: #f8fafc;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .modal-close {
            background: none;
            border: none;
            color: var(--text-dim);
            font-size: 1.2rem;
            cursor: pointer;
            padding: 4px 8px;
            border-radius: 6px;
        }

        .modal-close:hover {
            color: #fff;
            background: rgba(255, 255, 255, 0.1);
        }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .form-label {
            font-size: 0.8rem;
            font-weight: 600;
            color: #94a3b8;
        }

        .form-input, .form-select {
            background: #090d16;
            border: 1px solid rgba(255, 255, 255, 0.12);
            color: #f8fafc;
            padding: 10px 12px;
            border-radius: 8px;
            font-size: 0.85rem;
            outline: none;
            transition: border-color 0.2s;
        }

        .form-input:focus, .form-select:focus {
            border-color: #38bdf8;
            box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2);
        }

        .switch-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px 12px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .switch-text {
            display: flex;
            flex-direction: column;
        }

        .switch-title {
            font-size: 0.85rem;
            font-weight: 600;
            color: #f1f5f9;
        }

        .switch-desc {
            font-size: 0.72rem;
            color: var(--text-dim);
        }

        .toggle-switch {
            position: relative;
            display: inline-block;
            width: 44px;
            height: 24px;
            flex-shrink: 0;
        }

        .toggle-switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }

        .toggle-slider {
            position: absolute;
            cursor: pointer;
            top: 0; left: 0; right: 0; bottom: 0;
            background-color: #334155;
            transition: .3s;
            border-radius: 24px;
        }

        .toggle-slider:before {
            position: absolute;
            content: "";
            height: 18px;
            width: 18px;
            left: 3px;
            bottom: 3px;
            background-color: white;
            transition: .3s;
            border-radius: 50%;
        }

        input:checked + .toggle-slider {
            background-color: #22c55e;
        }

        input:checked + .toggle-slider:before {
            transform: translateX(20px);
        }

        .modal-actions {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 8px;
            padding-top: 12px;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
        }

        .toast-msg {
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: #0f172a;
            border: 1px solid #22c55e;
            color: #f8fafc;
            padding: 12px 20px;
            border-radius: 10px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
            font-size: 0.85rem;
            display: none;
            align-items: center;
            gap: 10px;
            z-index: 2000;
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
                <!-- Connected Robots Fleet Panel -->
                <div class="robots-panel" id="robots-panel">
                    <div class="robots-header">
                        <span class="robots-title">🤖 Connected StackChan Fleet (Multi-Robot Routing)</span>
                        <div style="display:flex; align-items:center; gap:8px;">
                            <span class="robots-count-badge" id="robots-count">0 Online</span>
                            <button class="btn-configure" onclick="openAddRobotModal()" style="font-size:0.75rem; padding:4px 10px;">+ Pre-Register</button>
                        </div>
                    </div>
                    <div class="robots-grid" id="robots-container">
                        <div class="robot-empty">No physical StackChan currently reporting. Polling...</div>
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

        <!-- Robot Configuration Modal Dialog -->
        <div class="modal-backdrop" id="robot-modal" onclick="if(event.target===this) closeModal()">
            <div class="modal-box">
                <div class="modal-header">
                    <span class="modal-title" id="modal-title">⚙️ Configure StackChan</span>
                    <button class="modal-close" onclick="closeModal()">&times;</button>
                </div>
                
                <div class="form-group">
                    <label class="form-label">Robot MAC Address</label>
                    <input type="text" id="cfg-mac" class="form-input" style="font-family:ui-monospace; font-weight:600;" placeholder="44:1B:F6:E5:59:60">
                </div>

                <div class="form-group">
                    <label class="form-label">Robot Nickname / Desk Location</label>
                    <input type="text" id="cfg-name" class="form-input" placeholder="e.g. Bangkok Dev Desk">
                </div>

                <div class="form-group">
                    <label class="form-label">Assigned GCP Project (Routing Target)</label>
                    <select id="cfg-project" class="form-select"></select>
                </div>

                <div class="switch-row">
                    <div class="switch-text">
                        <span class="switch-title">🔔 Audible Incident Chimes</span>
                        <span class="switch-desc">Play tone on physical speaker when alert triggers</span>
                    </div>
                    <label class="toggle-switch">
                        <input type="checkbox" id="cfg-sound">
                        <span class="toggle-slider"></span>
                    </label>
                </div>

                <div class="switch-row">
                    <div class="switch-text">
                        <span class="switch-title">💳 Display Cloud Costs on Screen</span>
                        <span class="switch-desc">Show monthly GCP spending on robot LCD</span>
                    </div>
                    <label class="toggle-switch">
                        <input type="checkbox" id="cfg-billing">
                        <span class="toggle-slider"></span>
                    </label>
                </div>

                <div class="form-group">
                    <label class="form-label">Screen Display Mode</label>
                    <select id="cfg-mode" class="form-select">
                        <option value="standard">Standard Multi-Card</option>
                        <option value="ticker">1-Line Ticker Focus</option>
                        <option value="avatar_only">Ambient Avatar Only</option>
                    </select>
                </div>

                <div class="form-group">
                    <label class="form-label">Telemetry Refresh Interval</label>
                    <select id="cfg-interval" class="form-select">
                        <option value="10">10 Seconds (Fast)</option>
                        <option value="15">15 Seconds (Standard)</option>
                        <option value="30">30 Seconds</option>
                        <option value="60">60 Seconds (Low Power)</option>
                    </select>
                </div>

                <div class="modal-actions">
                    <button class="btn btn-crit" id="btn-delete-robot" onclick="deleteRobotConfig()" style="font-size:0.8rem; padding:8px 14px;">Delete Robot</button>
                    <div style="display:flex; gap:10px;">
                        <button class="btn btn-outline" onclick="closeModal()" style="font-size:0.8rem; padding:8px 14px; background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.12); color:#fff; border-radius:8px; cursor:pointer;">Cancel</button>
                        <button class="btn btn-ok" onclick="saveRobotConfig()" style="font-size:0.8rem; padding:8px 18px;">Save Settings</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Notification Toast -->
        <div class="toast-msg" id="toast-msg"></div>

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

        let availableProjects = ["ALL FLEET"];
        let robotsCache = [];

        function showToast(msg, isError = false) {
            const toast = document.getElementById('toast-msg');
            if (!toast) return;
            toast.innerText = msg;
            toast.style.borderColor = isError ? '#ef4444' : '#22c55e';
            toast.style.display = 'flex';
            setTimeout(() => {
                toast.style.display = 'none';
            }, 3500);
        }

        async function fetchRobots() {
            try {
                const resp = await fetch('/api/v1/gcp/robots');
                if (resp.status === 200) {
                    const data = await resp.json();
                    if (data.projects && Array.isArray(data.projects)) {
                        availableProjects = data.projects;
                    }
                    robotsCache = data.robots || [];
                    renderRobots(robotsCache);
                }
            } catch (e) {
                console.error("Robots fetch failed:", e);
            }
        }

        function renderRobots(robots) {
            const countBadge = document.getElementById('robots-count');
            const container = document.getElementById('robots-container');
            if (!container || !countBadge) return;

            const onlineCount = robots.filter(r => r.online).length;
            countBadge.innerText = `${onlineCount} Online / ${robots.length} Registered`;

            if (robots.length === 0) {
                container.innerHTML = `
                    <div class="robot-empty">
                        No StackChan registered yet. Connect a physical robot or click <strong>+ Pre-Register</strong> above.
                    </div>`;
                return;
            }

            let html = '';
            for (const r of robots) {
                const isOnline = r.online;
                const battStr = (r.battery !== null && r.battery !== undefined) ? `${r.charging ? '⚡' : '🔋'} ${r.battery}%` : '⚡ DC Power';
                const dotClass = isOnline ? 'robot-status-dot' : 'robot-status-dot offline';
                const timeText = (r.last_seen_sec_ago < 5) ? 'Just now' : (r.last_seen_sec_ago > 86400 ? 'Never' : `${r.last_seen_sec_ago}s ago`);
                const assignedProj = r.assigned_project || "ALL FLEET";
                const robotName = r.name || `StackChan-${r.mac.slice(-4)}`;

                html += `
                    <div class="robot-card">
                        <div class="robot-card-top">
                            <div class="robot-card-left">
                                <div class="${dotClass}" title="${isOnline ? 'Online' : 'Offline'}"></div>
                                <div>
                                    <div class="robot-name">${robotName}</div>
                                    <div class="robot-mac">${r.mac}</div>
                                    <div class="robot-meta">${r.ip} • Last seen: ${timeText}</div>
                                </div>
                            </div>
                            <div style="text-align:right;">
                                <span class="robot-target-badge" title="GCP Project Route">${assignedProj}</span>
                                <div class="robot-battery" style="color: ${isOnline ? '#22c55e' : '#64748b'};">${battStr}</div>
                            </div>
                        </div>

                        <div class="robot-features-row">
                            <div class="feature-pills">
                                <span class="feature-pill ${r.sound_alerts ? 'active' : ''}" title="Chime Audio Alerts">
                                    ${r.sound_alerts ? '🔔 Chime On' : '🔕 Chime Muted'}
                                </span>
                                <span class="feature-pill ${r.show_billing ? 'active' : ''}" title="Display Cloud Spending on LCD">
                                    ${r.show_billing ? '💳 Cost Shown' : '🙈 Cost Hidden'}
                                </span>
                                <span class="feature-pill" title="Screen Display Mode">
                                    📺 ${r.display_mode || 'standard'}
                                </span>
                                <span class="feature-pill" title="Poll Rate">
                                    ⏱️ ${r.poll_interval_sec || 15}s
                                </span>
                            </div>
                            <button class="btn-configure" onclick="openRobotConfigModal('${r.mac}')">
                                ⚙️ Configure
                            </button>
                        </div>
                    </div>
                `;
            }
            container.innerHTML = html;
        }

        function populateProjectDropdown(selectedProject) {
            const select = document.getElementById('cfg-project');
            if (!select) return;
            select.innerHTML = '';
            for (const p of availableProjects) {
                const opt = document.createElement('option');
                opt.value = p;
                opt.innerText = (p === 'ALL FLEET') ? '🌐 ALL FLEET (Full Cluster)' : `☁️ ${p}`;
                if (p === selectedProject) opt.selected = true;
                select.appendChild(opt);
            }
        }

        function openRobotConfigModal(mac) {
            const robot = robotsCache.find(r => r.mac.toUpperCase() === mac.toUpperCase()) || {
                mac: mac,
                name: `StackChan-${mac.slice(-4)}`,
                assigned_project: "ALL FLEET",
                sound_alerts: true,
                show_billing: true,
                display_mode: "standard",
                poll_interval_sec: 15
            };

            document.getElementById('modal-title').innerText = `⚙️ Configure ${robot.name}`;
            const macInput = document.getElementById('cfg-mac');
            macInput.value = robot.mac;
            macInput.disabled = true;

            document.getElementById('cfg-name').value = robot.name || '';
            populateProjectDropdown(robot.assigned_project || 'ALL FLEET');
            document.getElementById('cfg-sound').checked = (robot.sound_alerts !== false);
            document.getElementById('cfg-billing').checked = (robot.show_billing !== false);
            document.getElementById('cfg-mode').value = robot.display_mode || 'standard';
            document.getElementById('cfg-interval').value = String(robot.poll_interval_sec || 15);

            document.getElementById('btn-delete-robot').style.display = 'block';
            document.getElementById('robot-modal').classList.add('active');
        }

        function openAddRobotModal() {
            document.getElementById('modal-title').innerText = `➕ Pre-Register StackChan`;
            const macInput = document.getElementById('cfg-mac');
            macInput.value = '';
            macInput.disabled = false;
            macInput.placeholder = 'e.g. 44:1B:F6:E5:59:60';

            document.getElementById('cfg-name').value = 'Office StackChan';
            populateProjectDropdown('ALL FLEET');
            document.getElementById('cfg-sound').checked = true;
            document.getElementById('cfg-billing').checked = true;
            document.getElementById('cfg-mode').value = 'standard';
            document.getElementById('cfg-interval').value = '15';

            document.getElementById('btn-delete-robot').style.display = 'none';
            document.getElementById('robot-modal').classList.add('active');
        }

        function closeModal() {
            document.getElementById('robot-modal').classList.remove('active');
        }

        async function saveRobotConfig() {
            const mac = document.getElementById('cfg-mac').value.trim().toUpperCase();
            if (!mac) {
                alert("MAC Address is required");
                return;
            }

            const payload = {
                name: document.getElementById('cfg-name').value.trim() || undefined,
                assigned_project: document.getElementById('cfg-project').value,
                sound_alerts: document.getElementById('cfg-sound').checked,
                show_billing: document.getElementById('cfg-billing').checked,
                display_mode: document.getElementById('cfg-mode').value,
                poll_interval_sec: parseInt(document.getElementById('cfg-interval').value, 10)
            };

            try {
                const resp = await fetch(`/api/v1/gcp/robots/${encodeURIComponent(mac)}/config`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (resp.ok) {
                    showToast(`✅ Settings saved for ${payload.name || mac}`);
                    closeModal();
                    await fetchRobots();
                } else {
                    const err = await resp.json();
                    showToast(`❌ Error: ${err.detail || 'Failed to update'}`, true);
                }
            } catch (e) {
                console.error("Save config error:", e);
                showToast("❌ Network error saving configuration", true);
            }
        }

        async function deleteRobotConfig() {
            const mac = document.getElementById('cfg-mac').value.trim().toUpperCase();
            if (!mac) return;

            if (!confirm(`Are you sure you want to remove StackChan (${mac}) from the registry?`)) {
                return;
            }

            try {
                const resp = await fetch(`/api/v1/gcp/robots/${encodeURIComponent(mac)}`, {
                    method: 'DELETE'
                });
                if (resp.ok) {
                    showToast(`🗑️ StackChan (${mac}) removed`);
                    closeModal();
                    await fetchRobots();
                } else {
                    showToast("❌ Error deleting robot", true);
                }
            } catch (e) {
                console.error("Delete robot error:", e);
                showToast("❌ Network error deleting robot", true);
            }
        }

        async function loadLiveTelemetry() {
            isManualOverride = false;
            const data = await fetchTelemetry(currentProject);
            renderData(data);
            await fetchRobots();
        }

        // Auto-refresh loop every 5 seconds
        setInterval(async () => {
            if (!isManualOverride) {
                const data = await fetchTelemetry(currentProject);
                renderData(data);
            }
            fetchRobots();
        }, 5000);

        // Initial Load
        loadLiveTelemetry();

    </script>
</body>
</html>
"""
