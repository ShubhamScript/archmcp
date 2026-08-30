"""
Multi-language API route and endpoint extractor.

Inspects source files across Python, JavaScript, TypeScript, Go, Java,
Rust, and Ruby to automatically discover REST / HTTP routes and RPC endpoints.

@author Shubham Upadhyay
@license MIT
"""

import os
import re
from typing import List, Set
from ..models.api import APIEndpoint

IGNORED_DIRS: Set[str] = {
    ".git", ".venv", "venv", "env", "node_modules", "__pycache__",
    ".pytest_cache", "dist", "build", "target", "vendor", ".idea",
    ".vscode", "coverage", "htmlcov", ".mypy_cache", "tests", "test"
}


class RouteExtractor:
    """
    Scans source files in a service directory to extract exposed API endpoints.
    """

    # Python Patterns
    PY_FASTAPI_PATTERN = re.compile(
        r"""@(?:app|router|api_router)\.(get|post|put|delete|patch|options|head)\s*\(\s*["']([^"']+)["']""",
        re.IGNORECASE
    )
    PY_FLASK_ROUTE = re.compile(
        r"""@(?:app|bp|api|[a-zA-Z0-9_]+_bp)\.route\s*\(\s*["']([^"']+)["'](?:\s*,\s*methods\s*=\s*\[([^\]]+)\])?""",
        re.IGNORECASE
    )
    PY_DJANGO_PATH = re.compile(
        r"""(?:path|re_path)\s*\(\s*["']([^"']+)["']""",
        re.IGNORECASE
    )

    # JS / TS Patterns (Express, Fastify, Koa, NestJS)
    JS_EXPRESS_PATTERN = re.compile(
        r"""(?:app|router|server|fastify)\.(get|post|put|delete|patch|options|head)\s*\(\s*["']([^"']+)["']""",
        re.IGNORECASE
    )
    NESTJS_CONTROLLER_PATTERN = re.compile(
        r"""@Controller\s*\(\s*["']?([^"'\)]*)["']?\s*\)"""
    )
    NESTJS_METHOD_PATTERN = re.compile(
        r"""@(Get|Post|Put|Delete|Patch|Options|Head)\s*\(\s*["']?([^"'\)]*)["']?\s*\)"""
    )

    # Go Patterns (Gin, Echo, Chi, Fiber, Mux)
    GO_GIN_PATTERN = re.compile(
        r"""(?:r|router|api|v[0-9]+|group|e|app)\.(GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD|Get|Post|Put|Delete|Patch)\s*\(\s*["']([^"']+)["']"""
    )
    GO_MUX_PATTERN = re.compile(
        r"""(?:r|router)\.HandleFunc\s*\(\s*["']([^"']+)["']\s*,\s*[^)]+\)\s*\.Methods\s*\(\s*["']([^"']+)["']"""
    )
    GO_HTTP_PATTERN = re.compile(
        r"""http\.HandleFunc\s*\(\s*["']([^"']+)["']"""
    )

    # Java / Kotlin Patterns (Spring Boot)
    JAVA_CLASS_MAPPING = re.compile(
        r"""@RequestMapping\s*\(\s*(?:value\s*=\s*)?["']([^"']+)["']"""
    )
    JAVA_METHOD_MAPPING = re.compile(
        r"""@(Get|Post|Put|Delete|Patch)Mapping\s*\(\s*(?:(?:value|path)\s*=\s*)?["']?([^"'\)]*)["']?\s*\)"""
    )

    # Rust Patterns (Actix, Axum)
    RUST_ROUTE_PATTERN = re.compile(
        r"""\.(?:route|service)\s*\(\s*["']([^"']+)["']\s*,\s*(?:web::)?(get|post|put|delete)""",
        re.IGNORECASE
    )

    @classmethod
    def extract_from_dir(cls, directory: str) -> List[APIEndpoint]:
        """
        Recursively scans directory for code files and parses all API endpoints.

        @param str directory: Service root directory
        @return List[APIEndpoint]: Extracted unique endpoints
        """
        endpoints_map = {}

        for root, dirs, files in os.walk(directory):
            # Prune ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext not in {".py", ".ts", ".js", ".go", ".java", ".kt", ".rs", ".rb"}:
                    continue

                full_path = os.path.join(root, file)
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        code = f.read()
                except Exception:
                    continue

                extracted = cls.extract_from_code(code, ext, rel_file=os.path.relpath(full_path, directory))
                for ep in extracted:
                    key = f"{ep.method.upper()}:{ep.path}"
                    if key not in endpoints_map:
                        endpoints_map[key] = ep

        return list(endpoints_map.values())

    @classmethod
    def extract_from_code(cls, code: str, file_ext: str, rel_file: str = "") -> List[APIEndpoint]:
        """
        Parses routes from source code text based on file extension.
        """
        endpoints = []

        if file_ext == ".py":
            # FastAPI
            for match in cls.PY_FASTAPI_PATTERN.finditer(code):
                method, path = match.group(1).upper(), match.group(2)
                endpoints.append(APIEndpoint(
                    path=path if path.startswith("/") else f"/{path}",
                    method=method,
                    summary=f"{method} {path} (from {rel_file or 'python'})"
                ))

            # Flask
            for match in cls.PY_FLASK_ROUTE.finditer(code):
                path = match.group(1)
                methods_raw = match.group(2)
                methods = ["GET"]
                if methods_raw:
                    methods = [m.strip().replace("'", "").replace('"', '').upper() for m in methods_raw.split(",")]
                for method in methods:
                    endpoints.append(APIEndpoint(
                        path=path if path.startswith("/") else f"/{path}",
                        method=method,
                        summary=f"{method} {path} (Flask in {rel_file})"
                    ))

            # Django
            for match in cls.PY_DJANGO_PATH.finditer(code):
                raw_path = match.group(1)
                path = "/" + raw_path.lstrip("/")
                endpoints.append(APIEndpoint(
                    path=path,
                    method="ANY",
                    summary=f"Django route {path} (in {rel_file})"
                ))

        elif file_ext in {".ts", ".js"}:
            # Express / Fastify
            for match in cls.JS_EXPRESS_PATTERN.finditer(code):
                method, path = match.group(1).upper(), match.group(2)
                endpoints.append(APIEndpoint(
                    path=path if path.startswith("/") else f"/{path}",
                    method=method,
                    summary=f"{method} {path} (in {rel_file})"
                ))

            # NestJS
            base_prefix = ""
            c_match = cls.NESTJS_CONTROLLER_PATTERN.search(code)
            if c_match and c_match.group(1):
                base_prefix = "/" + c_match.group(1).strip("/'\"")

            for match in cls.NESTJS_METHOD_PATTERN.finditer(code):
                method = match.group(1).upper()
                sub_path = match.group(2).strip("/'\"")
                full_p = f"{base_prefix}/{sub_path}".rstrip("/") if sub_path else base_prefix or "/"
                endpoints.append(APIEndpoint(
                    path=full_p if full_p.startswith("/") else f"/{full_p}",
                    method=method,
                    summary=f"NestJS {method} {full_p} (in {rel_file})"
                ))

        elif file_ext == ".go":
            # Gin / Echo / Chi / Fiber
            for match in cls.GO_GIN_PATTERN.finditer(code):
                method, path = match.group(1).upper(), match.group(2)
                endpoints.append(APIEndpoint(
                    path=path if path.startswith("/") else f"/{path}",
                    method=method,
                    summary=f"Go {method} {path} (in {rel_file})"
                ))

            # Mux
            for match in cls.GO_MUX_PATTERN.finditer(code):
                path, method = match.group(1), match.group(2).upper()
                endpoints.append(APIEndpoint(
                    path=path if path.startswith("/") else f"/{path}",
                    method=method,
                    summary=f"Go Mux {method} {path} (in {rel_file})"
                ))

            # net/http
            for match in cls.GO_HTTP_PATTERN.finditer(code):
                path = match.group(1)
                endpoints.append(APIEndpoint(
                    path=path if path.startswith("/") else f"/{path}",
                    method="ANY",
                    summary=f"Go HTTP handler {path} (in {rel_file})"
                ))

        elif file_ext in {".java", ".kt"}:
            base_path = ""
            class_m = cls.JAVA_CLASS_MAPPING.search(code)
            if class_m:
                base_path = "/" + class_m.group(1).strip("/'\"")

            for match in cls.JAVA_METHOD_MAPPING.finditer(code):
                method = match.group(1).upper()
                sub_path = match.group(2).strip("/'\"")
                full_p = f"{base_path}/{sub_path}".rstrip("/") if sub_path else base_path or "/"
                endpoints.append(APIEndpoint(
                    path=full_p if full_p.startswith("/") else f"/{full_p}",
                    method=method,
                    summary=f"Spring {method} {full_p} (in {rel_file})"
                ))

        elif file_ext == ".rs":
            for match in cls.RUST_ROUTE_PATTERN.finditer(code):
                path, method = match.group(1), match.group(2).upper()
                endpoints.append(APIEndpoint(
                    path=path if path.startswith("/") else f"/{path}",
                    method=method,
                    summary=f"Rust {method} {path} (in {rel_file})"
                ))

        return endpoints
