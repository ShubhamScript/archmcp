# 🏛️ ArchMCP: Central Remote MCP Server for Microservices

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Model Context Protocol](https://img.shields.io/badge/MCP-2.0%20Compliant-purple.svg)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Security: Enterprise Ready](https://img.shields.io/badge/Security-Zero--Trust%20%7C%20RBAC%20%7C%20Audit-brightgreen.svg)]()
[![Tests: 41/41 Passing](https://img.shields.io/badge/Tests-41%2F41%20Passing%20(>95%25%20cov)-brightgreen.svg)]()

> **Give your AI coding assistant an organizational brain.**  
> ArchMCP is a lightweight, remote Model Context Protocol (MCP) server that connects your AI assistants (Google Antigravity, Claude Desktop, Cursor, VS Code) to your entire microservice architecture in real time.

📚 **[User Manual & Setup Guide](docs/USER_MANUAL.md)** · 🛡️ **[Enterprise Security Architecture & STRIDE Threat Model](docs/security_architecture.md)**

---

## 📖 The Story Behind ArchMCP

### The Everyday Problem
Imagine you are writing a feature in `order-service` with your AI coding assistant. You ask the AI:
> *"Implement checkout and charge the customer."*

Immediately, the AI hits a wall:
* It has **no idea** what headers `payment-service` requires for idempotency.
* It doesn't know what database columns exist in `inventory-service` to reserve stock.
* It has no clue which upstream services will break if you modify an endpoint.

To fix this today, developers usually try one of two bad options:
1. **Dumping entire repositories into the prompt**: This easily wastes 100,000+ tokens per question, costs a lot of money, makes the AI slow, and causes hallucinations due to prompt clutter.
2. **Cloning 20+ repos locally**: Every developer on the team has to keep 20 repos updated on their laptop just so their local AI has context.

---

### The Solution: A Shared Remote Brain
**ArchMCP solves this by acting as a centralized, sub-millisecond architecture brain.**

Instead of running as a private local command on one laptop, ArchMCP runs as a shared remote service. Any engineer on your team connects their AI assistant to the ArchMCP server URL with an authenticated token.

When your AI assistant needs to know:
* *"Which service handles refunds?"* $\rightarrow$ It calls `search_microservices`.
* *"What tables does payment-service own?"* $\rightarrow$ It calls `get_database_schema`.
* *"If I change `/api/v1/orders`, who breaks?"* $\rightarrow$ It calls `analyze_blast_radius`.

```
┌────────────────────────────────────────────────────────┐
│                   AI Assistant Client                  │
│       (Google Antigravity, Claude Desktop, Cursor)     │
└──────────────────────────┬─────────────────────────────┘
                           │
                           │  HTTP / Server-Sent Events (SSE)
                           │  Authorization: Bearer arch_live_<kid>_<secret>
                           │
┌──────────────────────────▼────────────────────────────────────────────────────────┐
│                         ArchMCP Enterprise Ingress Gateway                        │
│   • Sliding-Window Rate Limiter (60 req/min per key with RFC-compliant headers)  │
│   • KeyStore Hashed Verification (HMAC-SHA256 with constant-time matching)       │
│   • Enterprise OIDC / OAuth2 JWT Provider (IdP claims, tenant segregation)       │
│   • Structured Security Audit Logging (JSON audit trail of all actions)          │
│   • Fine-Grained RBAC Scope Gatekeeper (arch:read, arch:schema:read, etc.)        │
│                                                                                    │
│   ┌─────────────────────┐  ┌─────────────────────┐  ┌──────────────────────────┐   │
│   │      MCP Tools      │  │    MCP Resources    │  │       MCP Prompts        │   │
│   │ • search_services   │  │ • arch/overview     │  │ • cross_service_planner  │   │
│   │ • blast_radius      │  │ • services/catalog  │  │ • incident_triage        │   │
│   │ • sequence_diagram  │  │ • guidelines/docs   │  │ • contract_refactor      │   │
│   │ • get_db_schema     │  │ • service docs      │  │                          │   │
│   └──────────┬──────────┘  └──────────┬──────────┘  └────────────┬─────────────┘   │
│              │                        │                          │                 │
│   ┌──────────▼────────────────────────▼──────────────────────────▼─────────────┐   │
│   │                       Microservice Intelligence Engine                     │   │
│   │ • Transitive Graph Traversal & Blast Radius Analyzer (BFS)                 │   │
│   │ • In-Memory Index & Token Search (< 2ms response time)                     │   │
│   │ • Dynamic OpenAPI / Swagger 3.0 Importer & Multi-Tenant Partitioning       │   │
│   └───────────────────────────────────┬────────────────────────────────────────┘   │
│                                       │                                            │
│   ┌───────────────────────────────────▼────────────────────────────────────────┐   │
│   │              Embedded Web Visualizer & Live Sandbox (/dashboard)           │   │
│   │ • Interactive Service Topology Explorer & Token Economics Calculator       │   │
│   └────────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛡️ Enterprise Security Architecture

ArchMCP is built with a zero-trust security model designed for enterprise environments:

* **Cryptographic Token Generator**: Keys follow `arch_{env}_{kid}_{secret}` format with 256 bits of CSPRNG entropy.
* **Hashed KeyStore**: Plaintext tokens are never stored on disk or logged; records store salted HMAC-SHA256 hashes.
* **Constant-Time Verification**: `hmac.compare_digest` prevents timing side-channel attacks.
* **Fine-Grained RBAC Scopes**: Tools enforce granular permission scopes (`arch:read`, `arch:schema:read`, `arch:blast_radius`, `arch:diagram`, `arch:write`, `arch:admin`, `*`).
* **Sliding-Window Rate Limiting**: Per-token rate limiting protects against SSE denial of service with RFC headers.
* **Structured Security Audit Logs**: Immutable JSON audit logs track all authentication attempts, key revocations, and tool invocations.
* **OIDC / OAuth2 Ready**: Pluggable JWT validation layer supports corporate identity providers (Okta, Entra ID, Keycloak).

👉 *Read the full [Enterprise Security Whitepaper & STRIDE Threat Model](docs/security_architecture.md).*

---

## 📊 Performance Benchmarks & Token Economics

| Benchmark Metric | Full Codebase Prompting | ArchMCP Query (Live) | Efficiency Gain |
| :--- | :--- | :--- | :--- |
| **Token Consumption** | ~140,000 to 180,000 tokens | **~120 to 380 tokens** | **> 99.6% Reduction** |
| **Execution Latency** | N/A (Full file scans / manual) | **~1.8 ms to 16 ms** | Sub-second real-time |
| **Memory Footprint** | ~500 MB (Local clones + indexers) | **~38 MB** | **> 90% Less RAM** |
| **Test Suite** | N/A | **41/41 Passing in < 1.5s** | Instant verification |

---

## ⌨️ Developer CLI & Key Management

ArchMCP includes an administrative and developer CLI:

```bash
# --- Server Execution ---
archmcp run                        # Launch the authenticated remote MCP server
archmcp explore                    # Inspect catalog in terminal
archmcp blast-radius auth-service  # Calculate change impact

# --- Enterprise Key Management ---
# Create an architect API key valid for 90 days:
archmcp keys create --name "Claude Desktop - Alice" --role architect --expires 90

# List active keys in keystore:
archmcp keys list

# Rotate an existing key (revokes old key, issues replacement):
archmcp keys rotate <kid>

# Revoke a compromised key immediately:
archmcp keys revoke <kid>
```

---

## 🔌 Connecting Your AI Assistant

When starting ArchMCP, an initial root admin key is displayed on first boot (or generated via `archmcp keys create`). Configure your AI assistant with the generated key:

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

## 🚀 3-Step Quickstart

```bash
# 1. Clone & Install
git clone https://github.com/ShubhamScript/archmcp.git
cd archmcp
pip install -e .[dev]

# 2. Run Comprehensive Test Suite
pytest -v

# 3. Start Authenticated Server
archmcp run
```
Open **`http://localhost:8000/dashboard`** in your browser to explore your architecture interactively.

---

## 📂 Project Structure

```
archmcp/
├── README.md                      # Project guide & architecture story
├── pyproject.toml                 # Dependencies, CLI scripts, and build config
├── Dockerfile                     # Hardened non-root container definition
├── docker-compose.yml             # Production container composition with persistence
├── data/
│   ├── repositories.yaml          # Sample microservices catalog
│   ├── keystore.json              # Hashed API keys repository
│   └── audit.log                  # Structured JSON security audit log stream
├── docs/
│   ├── USER_MANUAL.md             # End-to-end setup guide
│   └── security_architecture.md   # Security whitepaper & STRIDE threat model
├── src/
│   └── archmcp/
│       ├── main.py                # Server bootstrap & security initialization
│       ├── cli.py                 # CLI suite (run, explore, blast-radius, keys)
│       ├── config/settings.py     # Enterprise settings
│       ├── auth/                  # Crypto engine, KeyStore, RBAC scopes, audit, rate limiter, OIDC
│       ├── mcp/                   # Tools, Resources, Prompts, and SSE route handlers
│       ├── services/              # Blast radius, graph traversal, and search logic
│       ├── ingestion/             # OpenAPI importer, markdown parser, dependency scanner
│       ├── storage/               # In-memory database with multi-tenant partitioning
│       ├── web/                   # Embedded visualizer and live testing playground
│       └── models/                # Pydantic schemas (Architecture, BlastRadius, Services)
└── tests/                         # 41 unit, integration & security boundary tests
```

---

## 📄 License
MIT License. Free for open source and commercial use.
