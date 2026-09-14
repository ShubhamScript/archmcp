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
6. [Available MCP Tools & Annotations](#6-available-mcp-tools--annotations)
7. [How to Use in Everyday Coding](#7-how-to-use-in-everyday-coding)
8. [Web Dashboard (/dashboard)](#8-web-dashboard-dashboard)
9. [Troubleshooting & FAQs](#9-troubleshooting--faqs)

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

## 6. Available MCP Tools & Annotations
<a id="available-mcp-tools-annotations"></a>

ArchMCP exposes 12 production-grade MCP tools. Each tool includes explicit **titles**, **parameter descriptions with validation constraints**, and strict **behavioral annotations** compliant with OpenAI's directory and MCP 2025/2026 specifications:

* **`readOnlyHint`**: Indicates whether invoking the tool alters the environment (`true` enables AI hosts like Claude Desktop and Cursor to execute queries without prompting the user for approval).
* **`destructiveHint`**: Confirms whether an operation can destroy data (`false` across all tools confirms zero risk of data loss).
* **`idempotentHint`**: Indicates whether identical repeated invocations produce the same state, enabling safe AI retry loops.
* **`openWorldHint`**: Restricts tool domain reasoning to the local organization graph rather than open internet queries.

### Tool Directory

| Tool Name | Display Title | Description | Read-Only | Destructive | Idempotent | Open World | Scope |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| `search_microservices` | Search Microservices & Knowledge | Semantic & keyword search across services, routes, schemas, and docs | `true` | `false` | `true` | `false` | `arch:read` |
| `list_all_services` | List All Registered Services | Returns a catalog of registered microservices with tech stacks & owners | `true` | `false` | `true` | `false` | `arch:read` |
| `get_service_details` | Get Service Metadata Details | Retrieves complete metadata, repository URL, owner, and language | `true` | `false` | `true` | `false` | `arch:read` |
| `get_service_apis` | Get Service API Endpoints | Lists all REST and gRPC API endpoints exposed by a microservice | `true` | `false` | `true` | `false` | `arch:read` |
| `get_service_dependencies` | Get Service Dependencies Graph | Returns upstream (callers) and downstream (callees) dependency maps | `true` | `false` | `true` | `false` | `arch:read` |
| `get_database_schema` | Get Service Database Schema | Inspects database tables, columns, data types, and primary/foreign keys | `true` | `false` | `true` | `false` | `arch:schema:read` |
| `find_api_owner` | Find API Route Owner | Discovers which microservice owns or handles a route pattern or keyword | `true` | `false` | `true` | `false` | `arch:read` |
| `find_table_owner` | Find Database Table Owner | Reverse lookup to locate which microservice owns a given table name | `true` | `false` | `true` | `false` | `arch:schema:read` |
| `get_full_context_package` | Get Full Microservice Context Package | Aggregates service metadata, docs, and implementation guidelines | `true` | `false` | `true` | `false` | `arch:read` |
| `analyze_blast_radius` | Analyze Architecture Blast Radius | Computes transitive dependency impact & severity for API or service changes | `true` | `false` | `true` | `false` | `arch:blast_radius` |
| `generate_sequence_diagram` | Generate Multi-Service Sequence Diagram | Generates Mermaid sequence diagram models for end-to-end flows | `true` | `false` | `true` | `false` | `arch:diagram` |
| `scan_repository` | Scan Repository Architecture & Discovery | Discovers routes, schemas, queues, jobs, and builds dependency graph | `false` | `false` | `true` | `false` | `arch:read` |

---

## 7. How to Use in Everyday Coding

When chatting with your AI assistant, just ask your normal questions:
* *"Which service handles billing, and what database table does it use?"*
* *"Show me all endpoints in order-service."*
* *"If I change `/api/v1/auth/verify`, which other services will be affected?"*
* *"Show me the checkout sequence flow diagram."*
* *"Scan our new repo at /path/to/repo."*

The AI uses ArchMCP's tools to fetch only what it needs without dumping whole files into your prompt.

---

## 8. Web Dashboard (`/dashboard`)

Visit `http://localhost:8000/dashboard` in your browser. It gives you a clean view of all registered microservices, database schemas, APIs, and an interactive tool tester.

---

## 9. Troubleshooting & FAQs

**Q: AI assistant says connection refused.**  
Make sure `archmcp run` is running on `http://localhost:8000`.

**Q: Authentication error.**  
Make sure the token in your config matches one created with `archmcp keys create` or the default dev token in `.env`.

**Q: Can I scan multiple folders?**  
Yes, run `archmcp scan <path>` for each folder or scan a monorepo root containing all services.
