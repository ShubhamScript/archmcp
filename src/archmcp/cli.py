"""
ArchMCP - Developer CLI, Architecture Inspector & Key Management.

@author Shubham Upadhyay
@license MIT
"""

import sys
import argparse
import uvicorn

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from .config.settings import settings
from .main import app, initialize_knowledge_base
from .services.architecture_service import ArchitectureService
from .services.repository_service import RepositoryService
from .ingestion.openapi_importer import OpenAPIImporter
from .discovery.engine import RepositoryDiscoveryEngine
from .storage.database import db
from .auth.key_store import keystore
from .auth.permissions import ROLE_PROFILES, Scope

arch_service = ArchitectureService()
repo_service = RepositoryService()


def cmd_run(args):
    """
    Starts the Uvicorn ASGI HTTP/SSE server.

    @param argparse.Namespace args: CLI arguments
    @return None
    """
    print("=" * 65)
    print(f"🚀 Launching {settings.APP_NAME} (Enterprise MCP Server)")
    print(f"🌐 Remote SSE Endpoint : http://{settings.HOST}:{settings.PORT}/sse")
    print(f"📊 Web Visualizer      : http://{settings.HOST}:{settings.PORT}/dashboard")
    print(f"❤️  Health Probe        : http://{settings.HOST}:{settings.PORT}/health")
    print(f"🔒 Auth Enabled        : {settings.AUTH_ENABLED}")
    print(f"⚡ Rate Limit Enabled  : {settings.RATE_LIMIT_ENABLED} ({settings.RATE_LIMIT_PER_MINUTE} req/min)")
    print(f"🛡️ KeyStore File       : {settings.KEY_STORE_FILE}")
    print("=" * 65)
    uvicorn.run(app, host=settings.HOST, port=settings.PORT, log_level="info")


def cmd_explore(args):
    """
    Interactive terminal inspector for registered microservices.

    @param argparse.Namespace args: CLI arguments
    @return None
    """
    initialize_knowledge_base()
    services = db.list_services()
    print("\n" + "=" * 65)
    print("🏛️  ARCHMCP MICROSERVICES CATALOG EXPLORER")
    print("=" * 65)
    for s in services:
        print(f"\n📦 [{s.id}] {s.name}")
        print(f"   👤 Owner      : {s.owner}")
        print(f"   🛠️  Tech Stack : {s.language}")
        print(f"   🌐 APIs       : {len(s.apis)} endpoints")
        print(f"   🗄️  DB Tables  : {', '.join([t.name for t in s.database_tables]) or 'None'}")
        print(f"   🔗 Upstream   : {', '.join(s.dependencies.upstream) or 'None'}")
        print(f"   🔗 Downstream : {', '.join(s.dependencies.downstream) or 'None'}")
    print("\n" + "=" * 65 + "\n")


def cmd_blast_radius(args):
    """
    Calculates blast-radius impact analysis in the terminal.

    @param argparse.Namespace args: CLI arguments
    @return None
    """
    initialize_knowledge_base()
    service_id = args.service_id
    component = args.component or ""
    report = arch_service.analyze_blast_radius(service_id=service_id, component=component)
    if not report:
        print(f"❌ Error: Microservice '{service_id}' not found in registry.")
        sys.exit(1)

    print("\n" + "=" * 65)
    print(f"💥 BLAST RADIUS IMPACT REPORT: {service_id}")
    print("=" * 65)
    print(f"🎯 Target Component             : {report.changed_component}")
    print(f"⚠️  Impact Severity              : {report.impact_severity}")
    print(f"👥 Direct Dependent Services    : {', '.join(report.direct_dependent_services) or 'None'}")
    print(f"🔄 Transitive Multi-Hop Callers  : {', '.join(report.transitive_dependent_services) or 'None'}")
    print(f"🏢 Affected Teams to Notify     : {', '.join(report.affected_teams)}")
    print(f"📝 Risk Assessment              :\n   {report.risk_summary}")
    print("=" * 65 + "\n")


def cmd_import_openapi(args):
    """
    Imports OpenAPI spec from a URL or local file into the catalog.

    @param argparse.Namespace args: CLI arguments
    @return None
    """
    initialize_knowledge_base()
    target = args.target
    owner = args.owner or "Platform Team"
    print(f"⏳ Ingesting OpenAPI spec from: {target} ...")
    if target.startswith("http://") or target.startswith("https://"):
        svc = OpenAPIImporter.import_from_url(target, default_owner=owner)
    else:
        svc = OpenAPIImporter.import_from_file(target, default_owner=owner)

    print(f"✅ Successfully registered microservice '{svc.id}' ({svc.name}) with {len(svc.apis)} APIs.")


def cmd_scan(args):
    """
    Scans a local repository or monorepo to automatically discover all microservices,
    APIs, database schemas, message queues, background jobs, configs, docker services,
    and constructs the complete inter-service dependency graph.

    @param argparse.Namespace args: CLI arguments
    @return None
    """
    path = args.path
    persist = not args.no_save
    tenant_id = args.tenant or "default"
    owner = args.owner or "Engineering Team"
    out_format = args.format or "pretty"

    print("\n" + "=" * 65)
    print(f"🔍 SCANNING ARCHITECTURE: {path}")
    print("=" * 65)

    engine = RepositoryDiscoveryEngine(default_owner=owner, tenant_id=tenant_id)
    try:
        report = engine.discover(path, persist=persist, owner=owner)
    except Exception as e:
        print(f"❌ Discovery failed: {e}")
        sys.exit(1)

    if out_format == "json":
        output_content = report.model_dump_json(indent=2)
        print(output_content)
    elif out_format == "mermaid":
        output_content = report.mermaid_diagram
        print(output_content)
    elif out_format == "yaml":
        import yaml
        raw_list = [s.model_dump() for s in report.services]
        output_content = yaml.dump({"repositories": raw_list}, sort_keys=False)
        print(output_content)
    else:
        # Pretty terminal output
        project_type = "Monorepo / Multi-Service" if report.is_monorepo else "Single Microservice"
        print(f"📂 Scanned Path         : {report.scanned_path}")
        print(f"📦 Discovered Services  : {report.service_count} ({project_type})")
        print(f"🌐 API Routes           : {report.api_count} endpoints")
        print(f"🗄️  Database Tables      : {report.table_count} tables")
        print(f"📨 Message Queues       : {report.queue_count} event topics / queues")
        print(f"⏱️  Background Jobs      : {report.job_count} asynchronous tasks")
        print(f"🐳 Docker Services      : {report.docker_count} containers")
        print(f"⚙️  Config Variables     : {report.env_count} configuration keys")
        print(f"🔗 Inferred Channels    : {len(report.graph.edges)} cross-service channels")
        print("=" * 65)

        print("\n🏛️  DISCOVERED SERVICES ARCHITECTURE:")
        print("-" * 65)
        for s in report.services:
            print(f"\n📦 [{s.id}] {s.name}")
            if s.path:
                print(f"   📁 Path       : {s.path}")
            print(f"   🛠️  Tech Stack : {s.language}")
            if s.apis:
                ep_preview = ", ".join([f"{a.method} {a.path}" for a in s.apis[:3]])
                if len(s.apis) > 3:
                    ep_preview += f", ... (+{len(s.apis)-3} more)"
                print(f"   🌐 APIs       : {len(s.apis)} endpoints ({ep_preview})")
            if s.database_tables:
                print(f"   🗄️  DB Tables  : {', '.join([t.name for t in s.database_tables])}")
            if s.message_queues:
                q_desc = ", ".join([f"{q.broker_type} '{q.name}' ({q.role})" for q in s.message_queues])
                print(f"   📨 Queues     : {q_desc}")
            if s.background_jobs:
                print(f"   ⏱️  Jobs       : {', '.join([j.name for j in s.background_jobs])}")
            if s.dependencies.downstream:
                print(f"   🔗 Calls (↓)  : {', '.join(s.dependencies.downstream)}")
            if s.dependencies.upstream:
                print(f"   🔗 Called By  : {', '.join(s.dependencies.upstream)}")

        print("\n" + "=" * 65)
        print("🔄 INFERRED DISTRIBUTED SERVICE DEPENDENCY FLOW:")
        print("-" * 65)
        print(report.ascii_flow)
        print("=" * 65)

        if persist:
            print(f"\n✅ All {report.service_count} microservices saved to database & indexed into ArchMCP search engine.")
            print("💡 You can now query them via MCP tools, 'archmcp explore', or 'archmcp blast-radius <service_id>'.\n")

        output_content = report.model_dump_json(indent=2)

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output_content)
            print(f"💾 Saved architecture report to: {args.output}")
        except Exception as e:
            print(f"⚠️ Failed to write output file: {e}")


# -----------------------------------------------------------------------------
# KEY MANAGEMENT CLI COMMANDS
# -----------------------------------------------------------------------------

def cmd_keys_create(args):
    """Creates a new API key and displays the one-time raw secret token."""
    scopes = []
    if args.role and args.role in ROLE_PROFILES:
        scopes.extend(ROLE_PROFILES[args.role])
    if args.scopes:
        scopes.extend([s.strip() for s in args.scopes.split(",") if s.strip()])
    if not scopes:
        scopes = [Scope.ARCH_READ.value]

    scopes = list(set(scopes))

    record, raw_token = keystore.create_key(
        name=args.name,
        scopes=scopes,
        owner=args.owner or "admin",
        tenant_id=args.tenant or "default",
        environment=args.env or "live",
        expires_in_days=args.expires
    )

    print("\n" + "=" * 65)
    print("🔑 NEW API KEY CREATED")
    print("=" * 65)
    print(f"📌 Key ID (kid) : {record.kid}")
    print(f"🏷️  Name         : {record.name}")
    print(f"🏢 Tenant       : {record.tenant_id}")
    print(f"👤 Owner        : {record.owner}")
    print(f"🛡️ Scopes       : {', '.join(record.scopes)}")
    print(f"⏳ Expires At   : {record.expires_at or 'Never'}")
    print("-" * 65)
    print(f"🔐 RAW API TOKEN (SAVE NOW - NEVER SHOWN AGAIN):")
    print(f"   {raw_token}")
    print("=" * 65 + "\n")


def cmd_keys_list(args):
    """Lists existing API keys."""
    keys = keystore.list_keys(tenant_id=args.tenant, include_revoked=args.all)
    print("\n" + "=" * 65)
    print("🔑 CONFIGURED API KEYS IN KEYSTORE")
    print("=" * 65)
    if not keys:
        print("No API keys found. Use 'archmcp keys create --name <name>' to create one.")
    for k in keys:
        status_icon = "🟢" if k.is_valid() else ("🔴" if k.status.value == "revoked" else "🟡")
        print(f"\n{status_icon} [{k.kid}] {k.name}")
        print(f"   Status   : {k.status.value.upper()}")
        print(f"   Tenant   : {k.tenant_id}")
        print(f"   Owner    : {k.owner}")
        print(f"   Scopes   : {', '.join(k.scopes)}")
        print(f"   Created  : {k.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"   Expires  : {k.expires_at.strftime('%Y-%m-%d %H:%M:%S UTC') if k.expires_at else 'Never'}")
        print(f"   Last Used: {k.last_used_at.strftime('%Y-%m-%d %H:%M:%S UTC') if k.last_used_at else 'Never'}")
    print("\n" + "=" * 65 + "\n")


def cmd_keys_revoke(args):
    """Revokes an API key."""
    success = keystore.revoke_key(args.kid)
    if success:
        print(f"✅ Successfully revoked API key kid: {args.kid}")
    else:
        print(f"❌ Error: Key ID '{args.kid}' not found in KeyStore.")
        sys.exit(1)


def cmd_keys_rotate(args):
    """Rotates an API key."""
    res = keystore.rotate_key(args.kid, expires_in_days=args.expires)
    if not res:
        print(f"❌ Error: Key ID '{args.kid}' not found in KeyStore.")
        sys.exit(1)

    new_record, new_token = res
    print("\n" + "=" * 65)
    print(f"🔄 API KEY ROTATED (Old Key {args.kid} Revoked)")
    print("=" * 65)
    print(f"📌 New Key ID   : {new_record.kid}")
    print(f"🏷️  Name         : {new_record.name}")
    print(f"🛡️ Scopes       : {', '.join(new_record.scopes)}")
    print("-" * 65)
    print(f"🔐 NEW RAW API TOKEN (SAVE NOW - NEVER SHOWN AGAIN):")
    print(f"   {new_token}")
    print("=" * 65 + "\n")


def main():
    """
    CLI main parser and command dispatcher.

    @return None
    """
    parser = argparse.ArgumentParser(
        prog="archmcp",
        description="ArchMCP: Central Remote MCP Server for Microservices Architecture Intelligence"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: run
    p_run = subparsers.add_parser("run", help="Start the remote MCP HTTP/SSE server")
    p_run.set_defaults(func=cmd_run)

    # Command: explore
    p_exp = subparsers.add_parser("explore", help="Inspect all registered microservices in terminal")
    p_exp.set_defaults(func=cmd_explore)

    # Command: blast-radius
    p_blast = subparsers.add_parser("blast-radius", help="Calculate change blast-radius for a service")
    p_blast.add_argument("service_id", help="Target microservice ID (e.g. auth-service)")
    p_blast.add_argument("--component", default="", help="Specific endpoint or database table")
    p_blast.set_defaults(func=cmd_blast_radius)

    # Command: import-openapi
    p_imp = subparsers.add_parser("import-openapi", help="Import an OpenAPI/Swagger JSON or YAML spec")
    p_imp.add_argument("target", help="URL or local file path to openapi.json/yaml")
    p_imp.add_argument("--owner", default="Platform Team", help="Owning team name")
    p_imp.set_defaults(func=cmd_import_openapi)

    # Command: scan (Automatic Architecture Discovery)
    p_scan = subparsers.add_parser("scan", help="Automatically discover services, routes, DB schemas, queues, jobs, and dependencies")
    p_scan.add_argument("path", help="Path to project directory or monorepo to scan (e.g. './my-project', '.')")
    p_scan.add_argument("--output", "-o", help="Optional output file path to save architecture report")
    p_scan.add_argument("--format", choices=["pretty", "json", "yaml", "mermaid"], default="pretty", help="Output format")
    p_scan.add_argument("--no-save", action="store_true", help="Scan only without persisting to ArchMCP DB and search index")
    p_scan.add_argument("--tenant", default="default", help="Multi-tenant boundary identifier")
    p_scan.add_argument("--owner", default="Engineering Team", help="Default owner team for discovered microservices")
    p_scan.set_defaults(func=cmd_scan)

    # Command group: keys
    p_keys = subparsers.add_parser("keys", help="Manage API authentication keys")
    k_subs = p_keys.add_subparsers(dest="keys_command", help="Key operations")

    # keys create
    k_create = k_subs.add_parser("create", help="Create a new API key")
    k_create.add_argument("--name", required=True, help="Descriptive name (e.g. 'Claude Desktop')")
    k_create.add_argument("--role", choices=["admin", "architect", "developer", "viewer", "service_account"], help="Pre-packaged role")
    k_create.add_argument("--scopes", help="Comma-separated scopes (e.g. 'arch:read,arch:blast_radius')")
    k_create.add_argument("--owner", default="admin", help="Owner identity")
    k_create.add_argument("--tenant", default="default", help="Tenant organization ID")
    k_create.add_argument("--env", default="live", choices=["live", "test", "dev"], help="Environment")
    k_create.add_argument("--expires", type=int, help="Days until expiration")
    k_create.set_defaults(func=cmd_keys_create)

    # keys list
    k_list = k_subs.add_parser("list", help="List API keys")
    k_list.add_argument("--tenant", help="Filter by tenant ID")
    k_list.add_argument("--all", action="store_true", help="Include revoked and expired keys")
    k_list.set_defaults(func=cmd_keys_list)

    # keys revoke
    k_revoke = k_subs.add_parser("revoke", help="Revoke an API key")
    k_revoke.add_argument("kid", help="Key identifier (kid) to revoke")
    k_revoke.set_defaults(func=cmd_keys_revoke)

    # keys rotate
    k_rotate = k_subs.add_parser("rotate", help="Rotate an API key")
    k_rotate.add_argument("kid", help="Key identifier (kid) to rotate")
    k_rotate.add_argument("--expires", type=int, help="Days until new key expires")
    k_rotate.set_defaults(func=cmd_keys_rotate)

    args = parser.parse_args()
    if not args.command:
        cmd_run(args)
    elif args.command == "keys" and not getattr(args, "keys_command", None):
        p_keys.print_help()
    else:
        args.func(args)


if __name__ == "__main__":
    main()
