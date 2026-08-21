"""
ArchMCP - Developer CLI & Architecture Inspector.

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
from .storage.database import db

arch_service = ArchitectureService()
repo_service = RepositoryService()


def cmd_run(args):
    """
    Starts the Uvicorn ASGI HTTP/SSE server.

    @param argparse.Namespace args: CLI arguments
    @return None
    """
    print("=" * 65)
    print(f"🚀 Launching {settings.APP_NAME} (Remote MCP HTTP/SSE Server)")
    print(f"🌐 Remote SSE Endpoint : http://{settings.HOST}:{settings.PORT}/sse")
    print(f"📊 Web Visualizer      : http://{settings.HOST}:{settings.PORT}/dashboard")
    print(f"❤️  Health Probe        : http://{settings.HOST}:{settings.PORT}/health")
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

    args = parser.parse_args()
    if not args.command:
        cmd_run(args)
    else:
        args.func(args)


if __name__ == "__main__":
    main()
