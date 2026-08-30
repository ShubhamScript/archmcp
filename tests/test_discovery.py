"""
Unit and integration tests for Automatic Repository Discovery in ArchMCP.

@author Shubham Upadhyay
@license MIT
"""

import os
import shutil
import tempfile
import pytest
from unittest.mock import MagicMock

from archmcp.discovery.detector import ProjectDetector
from archmcp.discovery.route_extractor import RouteExtractor
from archmcp.discovery.schema_extractor import SchemaExtractor
from archmcp.discovery.queue_extractor import QueueExtractor
from archmcp.discovery.job_extractor import JobExtractor
from archmcp.discovery.config_extractor import ConfigExtractor
from archmcp.discovery.docker_extractor import DockerExtractor
from archmcp.discovery.dependency_linker import DependencyLinker
from archmcp.discovery.engine import RepositoryDiscoveryEngine
from archmcp.models.service import ServiceMetadata, ServiceDependencies
from archmcp.models.api import APIEndpoint
from archmcp.models.discovery import MessageQueueInfo, EnvVarInfo
from archmcp.storage.database import db
from archmcp.storage.vector_store import search_index
from archmcp.cli import main
from archmcp.mcp.server import create_mcp_server


@pytest.fixture
def mock_monorepo():
    """Creates a temporary realistic microservices monorepo for testing."""
    temp_dir = tempfile.mkdtemp(prefix="archmcp_test_monorepo_")

    # 1. Root docker-compose and .env
    with open(os.path.join(temp_dir, "docker-compose.yml"), "w", encoding="utf-8") as f:
        f.write("""
version: '3.8'
services:
  user-service:
    build: ./src/user-service
    ports:
      - "8001:8001"
    depends_on:
      - postgres
  payment-service:
    build: ./src/payment-service
    ports:
      - "8002:8002"
    depends_on:
      - kafka
      - user-service
  notification-service:
    build: ./src/notification-service
    depends_on:
      - kafka
  postgres:
    image: postgres:15
    ports:
      - "5432:5432"
  kafka:
    image: confluentinc/cp-kafka:latest
    ports:
      - "9092:9092"
""")

    with open(os.path.join(temp_dir, ".env"), "w", encoding="utf-8") as f:
        f.write("""
GLOBAL_STAGE=production
DATABASE_SECRET_KEY=supersecret123
""")

    src_dir = os.path.join(temp_dir, "src")
    os.makedirs(src_dir, exist_ok=True)

    # 2. user-service (Python / FastAPI)
    user_dir = os.path.join(src_dir, "user-service")
    os.makedirs(user_dir, exist_ok=True)
    with open(os.path.join(user_dir, "requirements.txt"), "w", encoding="utf-8") as f:
        f.write("fastapi>=0.100.0\nuvicorn\nsqlalchemy\nkafka-python\nrequests\n")
    with open(os.path.join(user_dir, "main.py"), "w", encoding="utf-8") as f:
        f.write("""
from fastapi import FastAPI
import requests
from kafka import KafkaProducer

app = FastAPI(title="User Service")
producer = KafkaProducer(bootstrap_servers='localhost:9092')

@app.get("/api/v1/users")
def list_users():
    return []

@app.post("/api/v1/users/register")
def register_user(email: str):
    producer.send(topic="user.registered", value=b"new_user")
    # Calls payment service to setup billing account
    requests.post("http://payment-service:8002/api/v1/payments/accounts", json={"email": email})
    return {"status": "ok"}
""")
    with open(os.path.join(user_dir, "models.py"), "w", encoding="utf-8") as f:
        f.write("""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    password_hash = Column(String)
""")

    # 3. payment-service (Node.js / Express)
    payment_dir = os.path.join(src_dir, "payment-service")
    os.makedirs(payment_dir, exist_ok=True)
    with open(os.path.join(payment_dir, "package.json"), "w", encoding="utf-8") as f:
        f.write('{"name": "payment-service", "description": "Processes charges and subscriptions", "dependencies": {"express": "^4.18.2", "kafkajs": "^2.2.4", "prisma": "^5.0.0"}}')
    with open(os.path.join(payment_dir, "server.js"), "w", encoding="utf-8") as f:
        f.write("""
const express = require('express');
const app = express();

app.post('/api/v1/payments/charge', (req, res) => {
    // produces order.paid topic
    kafkaProducer.send({ topic: 'order.paid', messages: [{ value: 'paid' }] });
    res.json({ success: true });
});

app.post('/api/v1/payments/accounts', (req, res) => {
    res.json({ accountId: 'acc_123' });
});
""")
    with open(os.path.join(payment_dir, "schema.prisma"), "w", encoding="utf-8") as f:
        f.write("""
model Transaction {
  id        Int      @id @default(autoincrement())
  amount    Float
  currency  String
  status    String
}
""")

    # 4. notification-service (Python / Celery Worker)
    notif_dir = os.path.join(src_dir, "notification-service")
    os.makedirs(notif_dir, exist_ok=True)
    with open(os.path.join(notif_dir, "requirements.txt"), "w", encoding="utf-8") as f:
        f.write("celery>=5.3.0\nredis\nkafka-python\n")
    with open(os.path.join(notif_dir, "tasks.py"), "w", encoding="utf-8") as f:
        f.write("""
from celery import Celery, shared_task
from kafka import KafkaConsumer

consumer = KafkaConsumer('order.paid', 'user.registered')

@shared_task
def send_email_receipt(order_id: str, email: str):
    print("Sending email...")

@shared_task
def send_welcome_sms(phone: str):
    print("Sending SMS...")
""")

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_detector_monorepo(mock_monorepo):
    """Test discovering multiple service roots in a monorepo."""
    roots = ProjectDetector.detect(mock_monorepo)
    assert len(roots) == 3

    ids = {r.id for r in roots}
    assert "user-service" in ids
    assert "payment-service" in ids
    assert "notification-service" in ids

    user_svc = next(r for r in roots if r.id == "user-service")
    assert user_svc.language == "Python"
    assert user_svc.framework == "FastAPI"

    pay_svc = next(r for r in roots if r.id == "payment-service")
    assert pay_svc.framework == "Express"

    notif_svc = next(r for r in roots if r.id == "notification-service")
    assert notif_svc.framework == "Celery Worker"


def test_route_extractor():
    """Test extracting API routes across different languages."""
    py_code = """
@app.get("/api/v1/items")
def get_items(): pass

@router.post('/api/v1/items/{id}')
def create_item(): pass
"""
    routes = RouteExtractor.extract_from_code(py_code, ".py")
    assert len(routes) == 2
    assert routes[0].method == "GET"
    assert routes[0].path == "/api/v1/items"
    assert routes[1].method == "POST"
    assert routes[1].path == "/api/v1/items/{id}"

    ts_code = """
@Controller('orders')
export class OrdersController {
    @Get(':id')
    getOrder() {}

    @Post()
    createOrder() {}
}
"""
    routes_ts = RouteExtractor.extract_from_code(ts_code, ".ts")
    assert len(routes_ts) == 2
    paths = {r.path for r in routes_ts}
    assert "/orders/:id" in paths
    assert "/orders" in paths

    go_code = """
r.GET("/health", healthHandler)
r.POST("/api/v2/charge", chargeHandler)
"""
    routes_go = RouteExtractor.extract_from_code(go_code, ".go")
    assert len(routes_go) == 2
    assert routes_go[0].method == "GET"
    assert routes_go[0].path == "/health"


def test_schema_extractor():
    """Test database schema and table extraction."""
    sql = """
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY,
    user_id UUID,
    total_amount DECIMAL(10,2)
);
"""
    tables = SchemaExtractor._parse_sql(sql, "migration.sql")
    assert len(tables) == 1
    assert tables[0].name == "orders"
    assert any("id" in col for col in tables[0].columns)

    prisma = """
model Customer {
  id    Int     @id @default(autoincrement())
  email String  @unique
  name  String?
}
"""
    prisma_tables = SchemaExtractor._parse_prisma(prisma, "schema.prisma")
    assert len(prisma_tables) == 1
    assert prisma_tables[0].name == "customers"


def test_queue_extractor():
    """Test extracting message queues and event topics."""
    py_code = """
producer.send(topic="payment.successful", value=b"{}")
consumer.subscribe(["user.registered"])
"""
    with tempfile.TemporaryDirectory() as tmp:
        fpath = os.path.join(tmp, "events.py")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(py_code)
        queues = QueueExtractor.extract_from_dir(tmp)
        assert len(queues) == 2
        q_names = {q.name: q.role for q in queues}
        assert q_names["payment.successful"] == "producer"
        assert q_names["user.registered"] == "consumer"


def test_job_extractor():
    """Test background jobs extraction."""
    py_code = """
@shared_task
def sync_orders():
    pass

@celery.task
def purge_cache():
    pass
"""
    with tempfile.TemporaryDirectory() as tmp:
        fpath = os.path.join(tmp, "worker.py")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(py_code)
        jobs = JobExtractor.extract_from_dir(tmp)
        assert len(jobs) == 2
        j_names = {j.name for j in jobs}
        assert "sync_orders" in j_names
        assert "purge_cache" in j_names


def test_config_extractor():
    """Test environment variable extractor and secret masking."""
    with tempfile.TemporaryDirectory() as tmp:
        env_file = os.path.join(tmp, ".env")
        with open(env_file, "w", encoding="utf-8") as f:
            f.write("""
APP_PORT=8000
DATABASE_PASSWORD=supersecret_pass
STRIPE_API_KEY=sk_live_12345
""")
        configs = ConfigExtractor.extract_from_dir(tmp)
        assert len(configs) == 3
        cfg_map = {c.key: c for c in configs}
        assert cfg_map["APP_PORT"].default_value == "8000"
        assert cfg_map["APP_PORT"].is_secret is False
        assert cfg_map["DATABASE_PASSWORD"].is_secret is True
        assert cfg_map["DATABASE_PASSWORD"].default_value == "********"
        assert cfg_map["STRIPE_API_KEY"].is_secret is True
        assert cfg_map["STRIPE_API_KEY"].default_value == "********"


def test_dependency_linker_flow():
    """Test linking services into a directional graph and generating ASCII/Mermaid flows."""
    user_svc = ServiceMetadata(
        id="user-service",
        name="User Service",
        language="Python / FastAPI",
        dependencies=ServiceDependencies(),
        apis=[APIEndpoint(path="/api/v1/users", method="GET", summary="Get users")],
        message_queues=[MessageQueueInfo(name="user.registered", broker_type="Kafka", role="producer")]
    )
    payment_svc = ServiceMetadata(
        id="payment-service",
        name="Payment Service",
        language="Node.js / Express",
        dependencies=ServiceDependencies(),
        apis=[APIEndpoint(path="/api/v1/payments/charge", method="POST", summary="Charge")],
        message_queues=[
            MessageQueueInfo(name="user.registered", broker_type="Kafka", role="consumer"),
            MessageQueueInfo(name="order.paid", broker_type="Kafka", role="producer")
        ]
    )
    notif_svc = ServiceMetadata(
        id="notification-service",
        name="Notification Service",
        language="Python / Celery",
        dependencies=ServiceDependencies(),
        message_queues=[MessageQueueInfo(name="order.paid", broker_type="Kafka", role="consumer")]
    )

    services = [user_svc, payment_svc, notif_svc]
    graph = DependencyLinker.link_services(services)

    assert len(graph.nodes) == 3
    # user-service -> payment-service (via topic user.registered)
    # payment-service -> notification-service (via topic order.paid)
    assert any(e.source == "user-service" and e.target == "payment-service" for e in graph.edges)
    assert any(e.source == "payment-service" and e.target == "notification-service" for e in graph.edges)

    assert "payment-service" in user_svc.dependencies.downstream
    assert "user-service" in payment_svc.dependencies.upstream
    assert "notification-service" in payment_svc.dependencies.downstream

    # Check ASCII & Mermaid diagram generation
    ascii_flow = DependencyLinker.generate_ascii_flow(graph)
    assert "user-service" in ascii_flow
    assert "payment-service" in ascii_flow
    assert "notification-service" in ascii_flow
    assert "↓" in ascii_flow

    mermaid = DependencyLinker.generate_mermaid_diagram(graph, services)
    assert "graph TD" in mermaid
    assert "user_service" in mermaid
    assert "payment_service" in mermaid


def test_full_discovery_engine(mock_monorepo):
    """Test running RepositoryDiscoveryEngine end-to-end on the mock monorepo."""
    from archmcp.main import initialize_knowledge_base
    engine = RepositoryDiscoveryEngine(default_owner="Core Platform", tenant_id="test-tenant")
    report = engine.discover(mock_monorepo, persist=True)

    assert report.service_count == 3
    assert report.is_monorepo is True
    assert report.api_count >= 3
    assert report.table_count >= 2
    assert report.queue_count >= 2
    assert report.job_count >= 2

    # Verify saved in database
    saved_services = db.list_services(tenant_id="test-tenant")
    assert len(saved_services) == 3

    # Verify vector search index
    search_results = search_index.search("payment charge", top_k=5)
    assert len(search_results) > 0
    assert any(r["id"] == "payment-service" for r in search_results)
    
    # Ensure default knowledge base is intact for other tests
    initialize_knowledge_base()


def test_cli_scan_command(mock_monorepo, monkeypatch, capsys):
    """Test running archmcp scan CLI command."""
    monkeypatch.setattr("sys.argv", ["archmcp", "scan", mock_monorepo, "--format", "pretty"])
    main()
    captured = capsys.readouterr()
    assert "SCANNING ARCHITECTURE" in captured.out
    assert "Discovered Services  : 3 (Monorepo / Multi-Service)" in captured.out
    assert "user-service" in captured.out
    assert "payment-service" in captured.out
    assert "notification-service" in captured.out
    assert "INFERRED DISTRIBUTED SERVICE DEPENDENCY FLOW:" in captured.out


@pytest.mark.asyncio
async def test_mcp_tool_scan_repository(mock_monorepo):
    """Test calling scan_repository via MCP server."""
    server = create_mcp_server()
    tools = await server.list_tools()
    tool_names = [t.name for t in tools]
    assert "scan_repository" in tool_names

    res = await server.call_tool("scan_repository", {"path": mock_monorepo, "persist": True, "owner": "Infra Team"})
    assert res is not None
    assert len(res.content) > 0
    res_str = res.content[0].text
    assert "user-service" in res_str
    assert "payment-service" in res_str
    assert "notification-service" in res_str

