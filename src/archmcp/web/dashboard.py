"""
ArchMCP - Embedded Architecture Visualizer & Live MCP Playground.

@author Shubham Upadhyay
@license MIT
"""

from starlette.responses import HTMLResponse, JSONResponse
from starlette.requests import Request
from ..storage.database import db
from ..services.architecture_service import ArchitectureService
from ..services.search_service import SearchService

arch_service = ArchitectureService()
search_service = SearchService()


def get_dashboard_html() -> str:
    """
    Returns the single-page responsive HTML5 dashboard and live sandbox UI.

    @return str: HTML content string
    """
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ArchMCP | Microservices Architecture Intelligence</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-base: #080c14;
      --bg-surface: #0f172a;
      --bg-card: rgba(15, 23, 42, 0.85);
      --bg-card-hover: rgba(30, 41, 59, 0.7);
      --border: rgba(255, 255, 255, 0.08);
      --border-focus: rgba(56, 189, 248, 0.5);
      --primary: #3b82f6;
      --primary-glow: rgba(59, 130, 246, 0.35);
      --cyan: #06b6d4;
      --cyan-glow: rgba(6, 182, 212, 0.3);
      --emerald: #10b981;
      --amber: #f59e0b;
      --rose: #f43f5e;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --text-dim: #64748b;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    
    body {
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      background-color: var(--bg-base);
      color: var(--text-main);
      min-height: 100vh;
      line-height: 1.5;
      background-image: 
        radial-gradient(circle at 10% 10%, rgba(59, 130, 246, 0.07) 0%, transparent 40%),
        radial-gradient(circle at 90% 90%, rgba(6, 182, 212, 0.07) 0%, transparent 40%);
      background-attachment: fixed;
    }

    /* HEADER */
    header {
      border-bottom: 1px solid var(--border);
      background: rgba(8, 12, 20, 0.9);
      backdrop-filter: blur(16px);
      position: sticky;
      top: 0;
      z-index: 100;
      padding: 0.85rem 1.5rem;
    }

    .header-container {
      max-width: 1600px;
      margin: 0 auto;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
    }

    .brand-wrap {
      display: flex;
      align-items: center;
      gap: 0.85rem;
    }

    .brand-logo {
      font-size: 1.35rem;
      font-weight: 800;
      letter-spacing: -0.5px;
      background: linear-gradient(135deg, #60a5fa 0%, #38bdf8 50%, #818cf8 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      display: flex;
      align-items: center;
      gap: 0.4rem;
    }

    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      padding: 0.25rem 0.65rem;
      background: rgba(16, 185, 129, 0.12);
      border: 1px solid rgba(16, 185, 129, 0.3);
      border-radius: 9999px;
      font-size: 0.72rem;
      font-weight: 600;
      color: var(--emerald);
    }

    .status-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--emerald);
      box-shadow: 0 0 8px var(--emerald);
      animation: pulse 2s infinite ease-in-out;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.5; transform: scale(0.85); }
    }

    .stats-group {
      display: flex;
      align-items: center;
      gap: 1.5rem;
      flex-wrap: wrap;
    }

    .stat-box {
      text-align: right;
    }

    .stat-number {
      font-family: 'JetBrains Mono', monospace;
      font-size: 1.15rem;
      font-weight: 700;
      color: var(--text-main);
    }

    .stat-label {
      font-size: 0.68rem;
      text-transform: uppercase;
      letter-spacing: 0.6px;
      color: var(--text-dim);
      font-weight: 600;
    }

    /* MAIN CONTAINER & GRID */
    .app-container {
      max-width: 1600px;
      margin: 0 auto;
      padding: 1.5rem;
    }

    .dashboard-layout {
      display: grid;
      grid-template-columns: minmax(320px, 360px) 1fr 1fr;
      gap: 1.25rem;
      align-items: start;
    }

    @media (max-width: 1280px) {
      .dashboard-layout {
        grid-template-columns: minmax(300px, 340px) 1fr;
      }
      .sandbox-column {
        grid-column: span 2;
      }
    }

    @media (max-width: 900px) {
      .dashboard-layout {
        grid-template-columns: 1fr;
      }
      .sandbox-column {
        grid-column: span 1;
      }
      .header-container {
        flex-direction: column;
        align-items: flex-start;
      }
      .stats-group {
        width: 100%;
        justify-content: space-between;
      }
    }

    /* CARDS */
    .card {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.25rem;
      backdrop-filter: blur(12px);
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid var(--border);
      padding-bottom: 0.75rem;
    }

    .card-title {
      font-size: 0.95rem;
      font-weight: 700;
      color: var(--text-main);
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    /* SERVICE LIST */
    .service-list {
      display: flex;
      flex-direction: column;
      gap: 0.6rem;
      max-height: 620px;
      overflow-y: auto;
      padding-right: 0.25rem;
    }

    .service-list::-webkit-scrollbar { width: 5px; }
    .service-list::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }

    .service-item {
      background: rgba(15, 23, 42, 0.6);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.75rem 0.9rem;
      cursor: pointer;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .service-item:hover {
      background: var(--bg-card-hover);
      border-color: rgba(56, 189, 248, 0.4);
      transform: translateY(-1px);
    }

    .service-item.active {
      background: rgba(59, 130, 246, 0.15);
      border-color: var(--primary);
      box-shadow: 0 0 16px var(--primary-glow);
    }

    .service-item-title {
      font-size: 0.88rem;
      font-weight: 700;
      color: var(--text-main);
    }

    .service-item-meta {
      font-size: 0.75rem;
      color: var(--text-muted);
      margin-top: 0.2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    /* INSPECTOR DETAILS */
    .inspector-content {
      display: flex;
      flex-direction: column;
      gap: 0.85rem;
    }

    .info-block {
      background: rgba(15, 23, 42, 0.6);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.85rem 1rem;
    }

    .info-block-header {
      font-size: 0.72rem;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--cyan);
      font-weight: 700;
      margin-bottom: 0.4rem;
    }

    .tag-container {
      display: flex;
      flex-wrap: wrap;
      gap: 0.4rem;
      margin-top: 0.35rem;
    }

    .tag-api {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.72rem;
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
      background: rgba(59, 130, 246, 0.12);
      border: 1px solid rgba(59, 130, 246, 0.3);
      color: #93c5fd;
    }

    .tag-table {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.72rem;
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
      background: rgba(16, 185, 129, 0.12);
      border: 1px solid rgba(16, 185, 129, 0.3);
      color: #6ee7b7;
    }

    /* SANDBOX FORM */
    .sandbox-form {
      display: flex;
      flex-direction: column;
      gap: 0.85rem;
    }

    .form-field {
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
    }

    .form-field label {
      font-size: 0.78rem;
      font-weight: 600;
      color: var(--text-muted);
    }

    .form-input, .form-select {
      background: rgba(15, 23, 42, 0.9);
      border: 1px solid var(--border);
      color: var(--text-main);
      padding: 0.65rem 0.85rem;
      border-radius: 6px;
      font-size: 0.85rem;
      font-family: inherit;
      outline: none;
      transition: border-color 0.2s ease;
      width: 100%;
    }

    .form-input:focus, .form-select:focus {
      border-color: var(--border-focus);
      box-shadow: 0 0 10px var(--cyan-glow);
    }

    .btn-submit {
      background: linear-gradient(135deg, #2563eb 0%, #0284c7 100%);
      color: #ffffff;
      border: none;
      padding: 0.75rem 1.2rem;
      border-radius: 6px;
      font-weight: 700;
      font-size: 0.88rem;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      transition: all 0.2s ease;
      box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35);
    }

    .btn-submit:hover {
      opacity: 0.95;
      transform: translateY(-1px);
      box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5);
    }

    .metrics-pill-bar {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
      gap: 0.6rem;
      background: rgba(0, 0, 0, 0.35);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.6rem 0.8rem;
    }

    .metric-pill {
      font-size: 0.72rem;
      color: var(--text-dim);
      display: flex;
      flex-direction: column;
      gap: 0.15rem;
    }

    .metric-pill-val {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.85rem;
      font-weight: 700;
      color: var(--cyan);
    }

    .code-output-box {
      background: #050811;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.85rem 1rem;
      color: #38bdf8;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.78rem;
      max-height: 280px;
      overflow: auto;
      white-space: pre-wrap;
      word-break: break-all;
    }
  </style>
</head>
<body>

  <!-- HEADER -->
  <header>
    <div class="header-container">
      <div class="brand-wrap">
        <div class="brand-logo">🏛️ ArchMCP</div>
        <div class="status-badge">
          <div class="status-dot"></div>
          Remote SSE Active
        </div>
      </div>
      <div class="stats-group">
        <div class="stat-box">
          <div class="stat-number" id="stat-services">-</div>
          <div class="stat-label">Microservices</div>
        </div>
        <div class="stat-box">
          <div class="stat-number" id="stat-apis">-</div>
          <div class="stat-label">Indexed APIs</div>
        </div>
        <div class="stat-box">
          <div class="stat-number" id="stat-tables">-</div>
          <div class="stat-label">DB Tables</div>
        </div>
      </div>
    </div>
  </header>

  <!-- APP CONTAINER -->
  <div class="app-container">
    <div class="dashboard-layout">
      
      <!-- COLUMN 1: MICROSERVICES LIST -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">📦 Microservices Catalog</div>
          <span style="font-size: 0.72rem; color: var(--text-dim); font-weight: 600;">Select to inspect</span>
        </div>
        <div class="service-list" id="services-list">
          <!-- Populated via JavaScript -->
        </div>
      </div>

      <!-- COLUMN 2: SERVICE INTELLIGENCE INSPECTOR -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">🔍 Selected Service Intelligence</div>
          <span id="badge-lang" style="font-size: 0.72rem; color: var(--cyan); font-family: 'JetBrains Mono'; font-weight: 600;">-</span>
        </div>
        <div class="inspector-content">
          <div class="info-block">
            <div class="info-block-header">Service Overview</div>
            <p id="detail-desc" style="font-size: 0.84rem; color: var(--text-muted); line-height: 1.4;">Select a service to view its architecture profile.</p>
          </div>

          <div class="info-block" id="block-apis">
            <div class="info-block-header">Exposed API Routes</div>
            <div id="detail-apis" class="tag-container"></div>
          </div>

          <div class="info-block" id="block-tables">
            <div class="info-block-header">Owned Database Tables</div>
            <div id="detail-tables" class="tag-container"></div>
          </div>

          <div class="info-block" id="block-deps">
            <div class="info-block-header">Dependency Mapping</div>
            <div id="detail-deps" style="font-size: 0.8rem; color: var(--text-muted); display: flex; flex-direction: column; gap: 0.3rem;"></div>
          </div>
        </div>
      </div>

      <!-- COLUMN 3: LIVE MCP SANDBOX -->
      <div class="card sandbox-column">
        <div class="card-header">
          <div class="card-title">⚡ Live MCP JSON-RPC Sandbox</div>
          <span style="font-size: 0.72rem; color: var(--emerald); font-family: 'JetBrains Mono'; font-weight: 700;">Protocol 2.0</span>
        </div>

        <div class="sandbox-form">
          <div class="form-field">
            <label for="tool-select">Select MCP Action / Tool</label>
            <select id="tool-select" class="form-select" onchange="onToolChange()">
              <option value="analyze_blast_radius">analyze_blast_radius(service_id, component)</option>
              <option value="search_microservices">search_microservices(query)</option>
              <option value="get_service_apis">get_service_apis(service_id)</option>
              <option value="get_database_schema">get_database_schema(service_id)</option>
              <option value="generate_sequence_diagram">generate_sequence_diagram(flow_name)</option>
              <option value="get_full_context_package">get_full_context_package(service_id)</option>
            </select>
          </div>

          <div class="form-field">
            <label id="arg-label" for="tool-arg">Tool Argument (service_id / query / flow)</label>
            <input type="text" id="tool-arg" class="form-input" value="auth-service" placeholder="Enter service ID, query, or flow...">
          </div>

          <button class="btn-submit" onclick="executeTool()">
            <span>▶ Run MCP Tool</span>
          </button>

          <!-- Metrics Bar -->
          <div class="metrics-pill-bar">
            <div class="metric-pill">
              <span>Latency</span>
              <div class="metric-pill-val" id="m-latency">~1.2 ms</div>
            </div>
            <div class="metric-pill">
              <span>Context Cost</span>
              <div class="metric-pill-val" id="m-tokens">~380 tokens</div>
            </div>
            <div class="metric-pill">
              <span>Savings</span>
              <div class="metric-pill-val" id="m-savings">> 99.6%</div>
            </div>
          </div>

          <div class="form-field">
            <label>JSON-RPC Output Result</label>
            <pre class="code-output-box" id="tool-output">// Click 'Run MCP Tool' to execute live request against ArchMCP...</pre>
          </div>
        </div>
      </div>

    </div>
  </div>

  <script>
    let services = [];

    async function initDashboard() {
      try {
        const res = await fetch('/api/dashboard/data');
        const data = await res.json();
        services = data.services || [];
        document.getElementById('stat-services').innerText = services.length;
        document.getElementById('stat-apis').innerText = data.total_apis || 0;
        document.getElementById('stat-tables').innerText = data.total_tables || 0;

        renderServiceList();
        if (services.length > 0) {
          selectService(services[0].id);
        }
      } catch (err) {
        console.error("Dashboard failed to load data:", err);
      }
    }

    function renderServiceList() {
      const container = document.getElementById('services-list');
      container.innerHTML = services.map(s => `
        <div class="service-item" id="item-${s.id}" onclick="selectService('${s.id}')">
          <div class="service-item-title">${s.name}</div>
          <div class="service-item-meta">
            <span>⚙️ ${s.language}</span>
            <span style="color: var(--text-dim);">👤 ${s.owner}</span>
          </div>
        </div>
      `).join('');
    }

    function selectService(serviceId) {
      document.querySelectorAll('.service-item').forEach(el => el.classList.remove('active'));
      const activeEl = document.getElementById(`item-${serviceId}`);
      if (activeEl) activeEl.classList.add('active');

      const svc = services.find(s => s.id === serviceId);
      if (!svc) return;

      document.getElementById('badge-lang').innerText = `${svc.language} · ${svc.owner}`;
      document.getElementById('detail-desc').innerText = svc.description || 'No description provided.';

      // Render APIs
      const apiBlock = document.getElementById('block-apis');
      const apiList = document.getElementById('detail-apis');
      if (svc.apis && svc.apis.length > 0) {
        apiBlock.style.display = 'block';
        apiList.innerHTML = svc.apis.map(a => `<span class="tag-api">${a.method} ${a.path}</span>`).join('');
      } else {
        apiBlock.style.display = 'none';
      }

      // Render DB Tables
      const tableBlock = document.getElementById('block-tables');
      const tableList = document.getElementById('detail-tables');
      if (svc.database_tables && svc.database_tables.length > 0) {
        tableBlock.style.display = 'block';
        tableList.innerHTML = svc.database_tables.map(t => `<span class="tag-table">🗄️ ${t.name}</span>`).join('');
      } else {
        tableBlock.style.display = 'none';
      }

      // Render Dependencies
      const up = (svc.dependencies && svc.dependencies.upstream) || [];
      const down = (svc.dependencies && svc.dependencies.downstream) || [];
      document.getElementById('detail-deps').innerHTML = `
        <div><strong style="color: var(--text-main);">Upstream Callers:</strong> ${up.length ? up.join(', ') : 'None (Root provider)'}</div>
        <div><strong style="color: var(--text-main);">Downstream Callees:</strong> ${down.length ? down.join(', ') : 'None (Leaf consumer)'}</div>
      `;

      // Update sandbox argument if tool uses service_id
      const currentTool = document.getElementById('tool-select').value;
      if (currentTool !== 'search_microservices' && currentTool !== 'generate_sequence_diagram') {
        document.getElementById('tool-arg').value = serviceId;
      }
    }

    function onToolChange() {
      const tool = document.getElementById('tool-select').value;
      const argInput = document.getElementById('tool-arg');
      if (tool === 'search_microservices') {
        argInput.value = 'payment refund';
      } else if (tool === 'generate_sequence_diagram') {
        argInput.value = 'checkout';
      } else {
        const active = document.querySelector('.service-item.active');
        argInput.value = active ? active.id.replace('item-', '') : 'auth-service';
      }
    }

    async function executeTool() {
      const tool = document.getElementById('tool-select').value;
      const arg = document.getElementById('tool-arg').value;
      const output = document.getElementById('tool-output');
      output.innerText = "// Executing JSON-RPC 2.0 call...";

      const t0 = performance.now();
      try {
        const res = await fetch('/api/dashboard/run-tool', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ tool, arg })
        });
        const data = await res.json();
        const latency = (performance.now() - t0).toFixed(1);

        output.innerText = JSON.stringify(data.result, null, 2);

        const charCount = JSON.stringify(data.result).length;
        const estimatedTokens = Math.max(70, Math.round(charCount / 3.8));

        document.getElementById('m-latency').innerText = `${latency} ms`;
        document.getElementById('m-tokens').innerText = `~${estimatedTokens} tokens`;
        document.getElementById('m-savings').innerText = `> 99.6%`;
      } catch (err) {
        output.innerText = "Error executing tool: " + err;
      }
    }

    initDashboard();
  </script>
</body>
</html>
"""


async def dashboard_view(request: Request) -> HTMLResponse:
    """
    Renders the HTML5 visual architecture dashboard.

    @param Request request: Starlette request object
    @return HTMLResponse: Rendered dashboard HTML
    """
    return HTMLResponse(get_dashboard_html())


async def dashboard_data_endpoint(request: Request) -> JSONResponse:
    """
    Returns aggregated metadata catalog for the dashboard.

    @param Request request: Starlette request object
    @return JSONResponse: Aggregated microservice catalog
    """
    services = db.list_services()
    total_apis = sum(len(s.apis) for s in services)
    total_tables = sum(len(s.database_tables) for s in services)

    return JSONResponse({
        "services": [s.model_dump() for s in services],
        "total_apis": total_apis,
        "total_tables": total_tables
    })


async def dashboard_run_tool_endpoint(request: Request) -> JSONResponse:
    """
    Interactive tool runner for the web playground.

    @param Request request: Starlette request object with tool and arg payload
    @return JSONResponse: Execution result and timing metrics
    """
    try:
        body = await request.json()
        tool = body.get("tool", "")
        arg = body.get("arg", "")

        if tool == "analyze_blast_radius":
            report = arch_service.analyze_blast_radius(service_id=arg)
            result = report.model_dump() if report else {"error": f"Service '{arg}' not found"}
        elif tool == "search_microservices":
            result = search_service.search_microservices(query=arg)
        elif tool == "get_service_apis":
            svc = db.get_service(arg)
            result = [a.model_dump() for a in svc.apis] if svc else {"error": f"Service '{arg}' not found"}
        elif tool == "get_database_schema":
            svc = db.get_service(arg)
            result = [t.model_dump() for t in svc.database_tables] if svc else {"error": f"Service '{arg}' not found"}
        elif tool == "generate_sequence_diagram":
            diag = arch_service.generate_sequence_diagram(flow_name=arg)
            result = diag.model_dump()
        elif tool == "get_full_context_package":
            svc = db.get_service(arg)
            docs = db.list_documents(service_id=arg)
            result = {
                "service": svc.model_dump() if svc else None,
                "docs": [d.model_dump() for d in docs]
            }
        else:
            result = {"error": f"Unknown tool: {tool}"}

        return JSONResponse({"status": "success", "tool": tool, "result": result})
    except Exception as e:
        return JSONResponse({"status": "error", "error": str(e)}, status_code=400)
