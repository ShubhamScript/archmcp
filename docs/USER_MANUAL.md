# 📘 ArchMCP User Manual

A simple guide to install, configure, scan repositories, and connect your AI coding assistants to ArchMCP.

---

## Table of Contents
1. [Prerequisites](#1-prerequisites)
2. [Installation & Setup](#2-installation--setup)
3. [Scanning Repositories (Auto Discovery)](#3-scanning-repositories-auto-discovery)
4. [Connecting Your AI Coding Assistants](#4-connecting-your-ai-coding-assistants)
   - [Google Antigravity IDE](#google-antigravity-ide)
   - [Anthropic Claude Desktop](#anthropic-claude-desktop)
   - [Cursor IDE](#cursor-ide)
   - [VS Code](#vs-code-cline--roo-code--continue)
5. [CLI Commands](#5-cli-commands)
6. [How to Use in Everyday Coding](#6-how-to-use-in-everyday-coding)
7. [Web Dashboard (/dashboard)](#7-web-dashboard-dashboard)
8. [Troubleshooting & FAQs](#8-troubleshooting--faqs)

---

## 1. Prerequisites

* **Operating System**: Linux, macOS, or Windows 10/11
* **Python**: 3.10, 3.11, 3.12, 3.13, or 3.14
* **Docker** *(Optional)*: If you prefer running inside containers

---

## 2. Installation & Setup

### Local Setup

```bash
# 1. Clone the repo
git clone https://github.com/ShubhamScript/archmcp.git
cd archmcp

# 2. Create virtual environment
# On Linux/macOS:
python3 -m venv .venv
source .venv/bin/activate

# On Windows (PowerShell):
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install
pip install -e .[dev]

# 4. Run tests to verify
pytest -v

# 5. Start the server
archmcp run
```

The server will start on `http://localhost:8000`.

---

## 3. Scanning Repositories (Auto Discovery)

You don't need to manually write YAML files. You can just point ArchMCP to your project or monorepo folder:

```bash
# Scan any project folder
archmcp scan ./my-project

# Output as a Mermaid diagram
archmcp scan ./my-project --format mermaid

# Save report to a file
archmcp scan ./my-project --output architecture.json
```

ArchMCP automatically finds:
- All services and their frameworks (FastAPI, Express, Spring Boot, Gin, etc.)
- API routes and HTTP methods
- Database models (SQLAlchemy, Django, Prisma, TypeORM, SQL files, etc.)
- Kafka topics, RabbitMQ queues, and Redis pub/sub channels
- Background jobs and Celery tasks
- Docker containers and dependencies
- Inferred service-to-service call graph

---

## 4. Connecting Your AI Coding Assistants

### Google Antigravity IDE
Add to `.agents/mcp_config.json`:
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

### Anthropic Claude Desktop
Add to `claude_desktop_config.json` (in `%APPDATA%\Claude` on Windows, or `~/Library/Application Support/Claude` on macOS):
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

### Cursor IDE
In **Settings** → **Features** → **MCP Servers** → **Add New MCP Server**:
* **Name**: `archmcp`
* **Type**: `SSE`
* **URL**: `http://localhost:8000/sse?token=dev-token-secret-123`

### VS Code (Cline / Roo Code / Continue)
In your MCP settings JSON:
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

## 5. CLI Commands

```bash
# Start server
archmcp run

# Scan code
archmcp scan ./path/to/project

# Explore services in terminal
archmcp explore

# Calculate change impact before making a change
archmcp blast-radius auth-service

# Import OpenAPI spec
archmcp import-openapi https://api.example.com/openapi.json

# API Key management
archmcp keys create --name "My Laptop"
archmcp keys list
archmcp keys revoke <kid>
```

---

## 6. How to Use in Everyday Coding

When chatting with your AI assistant, just ask your normal questions:
* *"Which service handles billing, and what database table does it use?"*
* *"Show me all endpoints in order-service."*
* *"If I change `/api/v1/auth/verify`, which other services will be affected?"*
* *"Show me the checkout sequence flow diagram."*
* *"Scan our new repo at /path/to/repo."*

The AI uses ArchMCP's tools to fetch only what it needs without dumping whole files into your prompt.

---

## 7. Web Dashboard (`/dashboard`)

Visit `http://localhost:8000/dashboard` in your browser. It gives you a clean view of all registered microservices, database schemas, APIs, and an interactive tool tester.

---

## 8. Troubleshooting & FAQs

**Q: AI assistant says connection refused.**  
Make sure `archmcp run` is running on `http://localhost:8000`.

**Q: Authentication error.**  
Make sure the token in your config matches one created with `archmcp keys create` or the default dev token in `.env`.

**Q: Can I scan multiple folders?**  
Yes, run `archmcp scan <path>` for each folder or scan a monorepo root containing all services.
