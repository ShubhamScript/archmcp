# 🏛️ ArchMCP : Central Remote MCP Server for Microservices

ArchMCP connects your AI coding assistant (like Claude Desktop, Cursor, Google Antigravity, or VS Code) to your entire microservices architecture.

Instead of pasting entire repositories into prompt windows or having to manually explain how your services talk to each other, ArchMCP gives your AI a central place to look up APIs, database tables, message queues, and dependencies in real time.

---

## 🔍 Automatic Repository Discovery (`archmcp scan`)

You shouldn't have to manually write config files to explain your architecture. ArchMCP can scan your project folder and figure it out on its own.

Run:
```bash
archmcp scan ./my-project
```

ArchMCP scans your code or monorepo and automatically finds:
* **Services & Modules**: Monorepo folders, microservices, and frameworks (FastAPI, Flask, Express, NestJS, Spring Boot, Gin, Echo, Rails, etc.)
* **APIs & Routes**: HTTP endpoints and paths from Python, TypeScript/JavaScript, Go, Java, Rust, and Ruby code
* **Database Models & Tables**: Tables, columns, and relations from SQLAlchemy, Django, Prisma, TypeORM, Mongoose, GORM, JPA, and SQL files
* **Message Queues & Event Topics**: Kafka topics, RabbitMQ queues, SQS, and Redis pub/sub channels, including who produces and who consumes them
* **Background Jobs**: Celery tasks, BullMQ workers, Spring `@Scheduled`, Temporal workflows, and cron jobs
* **Docker Services**: Containers, port mappings, and dependencies from `docker-compose.yml` and `Dockerfile`
* **Configuration**: Keys and environment variables from `.env` and YAML config files (with secret values masked)
* **Dependencies & Call Flow**: Inferred links between services based on HTTP calls, shared queues, and config URLs:

```
user-service
    ↓ [HTTP/REST]
payment-service
    ↓ [Event: order.paid]
notification-service
```

---

## 💡 The Problem ArchMCP Solves

When you work on microservices with an AI assistant, the AI usually only sees the file or folder you currently have open.

For example, if you are writing code in `order-service` and ask your AI to charge a customer:
* It doesn't know what endpoint `payment-service` exposes or what payload it needs.
* It doesn't know what database tables `inventory-service` has.
* It doesn't know if changing an API will break `notification-service`.

Developers usually try two workarounds:
1. **Pasting everything into the prompt**: Wastes thousands of tokens, costs money, and fills context windows with noise.
2. **Cloning 20+ repos locally**: Hard to keep in sync across a team.

### How ArchMCP helps
ArchMCP runs as a shared or local MCP server. When your AI assistant needs context, it asks ArchMCP directly using standard MCP tools:
* *"Which service handles user payments?"* → uses `search_microservices`
* *"What columns are in the transactions table?"* → uses `get_database_schema`
* *"If I update `/api/v1/orders`, which services might break?"* → uses `analyze_blast_radius`
* *"What is the flow for checkout?"* → uses `generate_sequence_diagram`
* *"Scan our new project repo"* → uses `scan_repository`

---

## 🚀 Quickstart

### 1. Install
```bash
git clone https://github.com/ShubhamScript/archmcp.git
cd archmcp
pip install -e .[dev]
```

### 2. Run Tests
```bash
pytest -v
```

### 3. Scan a Project or Monorepo
```bash
# Scan any folder or project
archmcp scan ./my-project

# Or scan with Mermaid diagram output
archmcp scan ./my-project --format mermaid
```

### 4. Start the Server
```bash
archmcp run
```
Open **`http://localhost:8000/dashboard`** in your browser to view the visualizer and test queries.

---

## 🔌 Connecting to Your AI Assistant

### Google Antigravity IDE (`.agents/mcp_config.json`)
```json
{
  "mcpServers": {
    "archmcp": {
      "url": "http://127.0.0.1:8000/sse",
      "headers": {
        "Authorization": "Bearer arch_live_<YOUR_KEY_ID>_<YOUR_SECRET_TOKEN>"
      }
    }
  }
}
```

### Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "archmcp": {
      "url": "http://127.0.0.1:8000/sse",
      "headers": {
        "Authorization": "Bearer arch_live_<YOUR_KEY_ID>_<YOUR_SECRET_TOKEN>"
      }
    }
  }
}
```

### Cursor (`.cursor/mcp.json`)
```json
{
  "mcpServers": {
    "archmcp": {
      "url": "http://127.0.0.1:8000/sse?token=arch_live_<YOUR_KEY_ID>_<YOUR_SECRET_TOKEN>"
    }
  }
}
```

---

## ⌨️ CLI Commands

```bash
# Start server
archmcp run

# Scan a codebase or monorepo
archmcp scan ./path/to/project

# Explore registered services in terminal
archmcp explore

# Check blast radius when modifying a service
archmcp blast-radius auth-service

# Import an OpenAPI spec directly
archmcp import-openapi https://api.example.com/openapi.json

# API Key Management
archmcp keys create --name "My Laptop" --role developer
archmcp keys list
archmcp keys rotate <kid>
archmcp keys revoke <kid>
```

---

## 🛠️ MCP Tools Included

Your AI assistant has access to these tools out of the box:

| Tool | What it does |
| :--- | :--- |
| `scan_repository` | Scans a folder to discover services, APIs, DB schemas, queues, jobs, and dependency graphs |
| `search_microservices` | Search across services, routes, tables, and docs with keywords |
| `list_all_services` | Get a summary list of all tracked services |
| `get_service_details` | Get full metadata, tech stack, repo URL, and owner for a service |
| `get_service_apis` | List all API routes for a service |
| `get_database_schema` | Get tables and columns owned by a service |
| `get_service_dependencies` | Get upstream callers and downstream dependencies |
| `find_api_owner` | Find which service owns a specific route (e.g. `/payments/charge`) |
| `find_table_owner` | Find which service owns a database table |
| `analyze_blast_radius` | See all direct and indirect downstream services affected by a change |
| `generate_sequence_diagram` | Generates a Mermaid sequence diagram for workflows (e.g. checkout, refund) |
| `get_full_context_package` | Bundles metadata, schemas, and docs for AI code generation |

---

## 📁 Project Structure

```
archmcp/
├── src/archmcp/
│   ├── discovery/     # Automatic code scanner, route extractor, schema parser, dependency linker
│   ├── mcp/           # MCP tools, resources, prompts, and SSE endpoint
│   ├── auth/          # API key generation, hashing, rate limiting, and permission scopes
│   ├── services/      # Blast radius analysis, dependency graph, search
│   ├── storage/       # Fast in-memory database and keyword search index
│   ├── ingestion/     # OpenAPI spec importer and document parser
│   ├── web/           # Browser dashboard and visualizer
│   └── cli.py         # Command line interface
├── tests/             # Comprehensive pytest test suite (51 tests)
├── data/              # Default repositories.yaml catalog and keystore
└── docs/              # User manual and documentation
```

---

## 📄 License
MIT License.
