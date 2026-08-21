# 📘 ArchMCP User Manual & Developer Guide

Welcome to the comprehensive **ArchMCP User Manual**. This guide walks you through installation, configuration, connecting your AI coding assistants, using the CLI and web visualizer, and troubleshooting.

---

## 📑 Table of Contents
1. [Prerequisites & System Requirements](#1-prerequisites--system-requirements)
2. [Installation & Setup](#2-installation--setup)
   - [Method A: Local Python Environment (Recommended for Dev)](#method-a-local-python-environment)
   - [Method B: Docker & Docker Compose (Recommended for Teams)](#method-b-docker--docker-compose)
3. [Configuration Guide](#3-configuration-guide)
   - [Environment Variables (.env)](#environment-variables-env)
   - [Managing Authentication Tokens](#managing-authentication-tokens)
   - [Registering Microservices (YAML & OpenAPI)](#registering-microservices)
4. [Connecting Your AI Coding Assistants](#4-connecting-your-ai-coding-assistants)
   - [Google Antigravity IDE](#google-antigravity-ide)
   - [Anthropic Claude Desktop](#anthropic-claude-desktop)
   - [Cursor IDE](#cursor-ide)
   - [VS Code (Cline / Roo Code / Continue)](#vs-code-cline--roo-code--continue)
5. [Everyday Developer Workflows](#5-everyday-developer-workflows)
   - [1. Searching Architecture & Schemas](#1-searching-architecture--schemas)
   - [2. Pre-PR Blast Radius Analysis](#2-pre-pr-blast-radius-analysis)
   - [3. Generating Workflow Sequence Diagrams](#3-generating-workflow-sequence-diagrams)
   - [4. Using Built-in MCP Prompts](#4-using-built-in-mcp-prompts)
6. [Interactive Web Visualizer (/dashboard)](#6-interactive-web-visualizer-dashboard)
7. [Developer CLI Reference](#7-developer-cli-reference)
8. [Troubleshooting & FAQs](#8-troubleshooting--faqs)

---

## 1. Prerequisites & System Requirements

* **Operating System**: Linux, macOS, or Windows 10/11.
* **Python**: Version 3.10, 3.11, 3.12, 3.13, or 3.14.
* **Docker** *(Optional)*: Docker Engine 20.10+ and Docker Compose v2.

---

## 2. Installation & Setup

### Method A: Local Python Environment

```bash
# 1. Clone the repository
git clone https://github.com/ShubhamScript/archmcp.git
cd archmcp

# 2. Create and activate a virtual environment
# On Linux/macOS:
python3 -m venv .venv
source .venv/bin/activate

# On Windows (PowerShell):
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install ArchMCP in editable mode with development dependencies
pip install -e .[dev]

# 4. Verify installation by running tests
pytest -v

# 5. Start the server
archmcp run
```

The server will start on `http://localhost:8000`.

---

### Method B: Docker & Docker Compose

Ideal for hosting ArchMCP on an internal server or shared team virtual machine:

```bash
# Start container in background
docker compose up -d --build

# Check logs
docker compose logs -f

# Verify health check
curl http://localhost:8000/health
```

---

## 3. Configuration Guide

### Environment Variables (`.env`)
Copy the example file:
```bash
cp .env.example .env
```

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `APP_NAME` | `ArchMCP-Server` | Name advertised to AI clients during MCP handshake |
| `HOST` | `0.0.0.0` | Bind address (`0.0.0.0` for all interfaces, `127.0.0.1` for local only) |
| `PORT` | `8000` | HTTP / SSE port |
| `AUTH_ENABLED` | `true` | Set `false` to disable token verification in local dev |
| `AUTH_TOKENS` | `["dev-token-secret-123"]` | JSON array of authorized Bearer tokens |
| `REPOSITORIES_FILE`| `data/repositories.yaml` | Path to the microservices metadata YAML file |

---

### Registering Microservices

#### Option 1: Static YAML (`data/repositories.yaml`)
Add your services with their owned APIs, database tables, and dependencies:

```yaml
version: "1.0"
repositories:
  - id: "billing-service"
    name: "Billing & Subscription Service"
    repo_url: "https://github.com/company/billing-service"
    owner: "FinTech Team"
    language: "Go / Gin"
    description: "Manages recurring SaaS plans, invoices, and payment method updates."
    dependencies:
      upstream: ["auth-service", "payment-service"]
      downstream: ["notification-service"]
    database_tables:
      - name: "subscriptions"
        description: "Customer recurring plans and billing cycle state"
        columns: ["id (UUID, PK)", "customer_id (UUID)", "plan (ENUM)", "status (VARCHAR)"]
    apis:
      - path: "/api/v1/subscriptions"
        method: "POST"
        summary: "Create subscription"
        description: "Initiates subscription with trial period and billing date."
```

#### Option 2: Dynamic OpenAPI / Swagger Import
Import directly from a live URL or local specification file:

```bash
# Ingest from remote URL
archmcp import-openapi https://petstore.swagger.io/v2/swagger.json --owner "Commerce Team"

# Ingest from local YAML file
archmcp import-openapi ./specs/warehouse-service.yaml --owner "Logistics Team"
```

---

## 4. Connecting Your AI Coding Assistants

### Google Antigravity IDE
Add the configuration to `.agents/mcp_config.json` in your workspace root:

```json
{
  "mcpServers": {
    "archmcp": {
      "url": "http://localhost:8000/sse",
      "headers": {
        "Authorization": "Bearer dev-token-secret-123"
      }
    }
  }
}
```

---

### Anthropic Claude Desktop
Open your Claude configuration file:
* **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
* **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add the server:
```json
{
  "mcpServers": {
    "archmcp": {
      "url": "http://127.0.0.1:8000/sse",
      "headers": {
        "Authorization": "Bearer dev-token-secret-123"
      }
    }
  }
}
```
*Restart Claude Desktop to activate the tools.*

---

### Cursor IDE
Open **Settings** $\rightarrow$ **Features** $\rightarrow$ **MCP Servers** $\rightarrow$ **Add New MCP Server**:
* **Name**: `archmcp`
* **Type**: `SSE`
* **URL**: `http://localhost:8000/sse?token=dev-token-secret-123`

---

### VS Code (Cline / Roo Code / Continue)
In your Cline / Roo Code MCP settings (`cline_mcp_settings.json`):
```json
{
  "mcpServers": {
    "archmcp": {
      "url": "http://127.0.0.1:8000/sse",
      "headers": {
        "Authorization": "Bearer dev-token-secret-123"
      }
    }
  }
}
```

---

## 5. Everyday Developer Workflows

### 1. Searching Architecture & Schemas
When chatting with your AI assistant, simply ask natural questions:
* *"Which service owns user authentication and what database table holds password hashes?"*
* *"Show me all endpoints exposed by order-service."*
* The AI will automatically trigger `search_microservices` or `get_service_apis` in < 2ms without prompt bloat.

---

### 2. Pre-PR Blast Radius Analysis
Before refactoring a database column or changing an API route, ask your AI:
* *"I am about to change `/api/v1/auth/verify` in auth-service. What is the blast radius and which teams should I notify?"*
* The AI triggers `analyze_blast_radius`, performs a transitive graph search, and provides you with the list of direct and indirect consumers.

---

### 3. Generating Workflow Sequence Diagrams
To visualize a complex multi-service workflow:
* *"Generate a sequence diagram for the checkout and order fulfillment flow."*
* The AI calls `generate_sequence_diagram(flow_name="checkout")` and renders a clean Mermaid.js diagram directly in your chat.

---

### 4. Using Built-in MCP Prompts
In Claude Desktop or Antigravity, click the Prompt selector or type:
* `/cross_service_feature_planner`: Generates end-to-end multi-repo feature blueprints.
* `/distributed_incident_triage`: Diagnoses production outages across service dependency chains.
* `/api_contract_refactor`: Generates a 4-phase zero-downtime migration blueprint.

---

## 6. Interactive Web Visualizer (`/dashboard`)

ArchMCP includes an embedded, responsive browser dashboard at **`http://localhost:8000/dashboard`**:

![ArchMCP Interactive Dashboard & Live Sandbox](dashboard.png)

1. **Topology View**: Click on any service card (`auth-service`, `order-service`, `payment-service`) to view its tech stack, owner, exposed APIs, database tables, and upstream/downstream callers.
2. **Live MCP Sandbox**: Select any tool (`analyze_blast_radius`, `search_microservices`, `get_service_apis`), enter an argument, and click **▶ Run MCP Tool**.
3. **Real-Time Performance Metrics**: Displays live execution latency (e.g. `12.4 ms`), context token consumption (`~120 tokens`), and live token savings vs full codebase prompting (`> 99.6%`).

---

## 7. Developer CLI Reference

```bash
# Start the Remote MCP HTTP/SSE server
archmcp run

# Inspect all registered microservices in your terminal
archmcp explore

# Calculate breaking change impact for a service
archmcp blast-radius auth-service

# Filter blast radius for a specific endpoint
archmcp blast-radius order-service --component /api/v1/orders

# Import an OpenAPI or Swagger specification from URL
archmcp import-openapi https://petstore.swagger.io/v2/swagger.json --owner "Commerce Team"

# Import an OpenAPI spec from a local file
archmcp import-openapi ./path/to/openapi.yaml --owner "Platform Team"
```

---

## 8. Troubleshooting & FAQs

### Q: I get a `401 Unauthorized` error when connecting from Cursor or Claude.
* **Cause**: Authentication is enabled and the token is missing or incorrect.
* **Fix**:
  1. Verify the token in your client matches `AUTH_TOKENS` in `.env` (default: `dev-token-secret-123`).
  2. For clients that don't support custom headers, pass the token as a URL query parameter: `http://localhost:8000/sse?token=dev-token-secret-123`.

### Q: How do I disable authentication for local testing?
* In `.env`, set `AUTH_ENABLED=false` and restart the server.

### Q: Port 8000 is already in use by another service.
* In `.env`, change `PORT=8080` (or any free port) and restart ArchMCP.

### Q: Can I run ArchMCP without Docker?
* Yes! Simply install Python 3.10+ and run `pip install -e .` followed by `archmcp run`.

---

## 🤝 Contributing
Contributions are welcome! Please submit an issue or pull request on [GitHub](https://github.com/ShubhamScript/archmcp).
