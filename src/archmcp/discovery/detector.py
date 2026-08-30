"""
Project and microservice boundary detector.

Discovers whether a directory is a monorepo, multi-microservice project,
or single standalone service, and detects tech stack / framework per service.

@author Shubham Upadhyay
@license MIT
"""

import os
import json
from dataclasses import dataclass, field
from typing import List, Optional, Set, Dict


@dataclass
class ServiceRoot:
    """Represents a discovered microservice or application module root."""
    id: str
    name: str
    path: str  # Relative path to root
    full_path: str  # Absolute filesystem path
    language: str
    framework: str
    manifest_files: List[str] = field(default_factory=list)
    description: str = ""


# Directories to always skip during scanning
IGNORED_DIRS: Set[str] = {
    ".git", ".venv", "venv", "env", "node_modules", "__pycache__",
    ".pytest_cache", "dist", "build", "target", "vendor", ".idea",
    ".vscode", "coverage", "htmlcov", ".mypy_cache", ".tox", ".eggs"
}


class ProjectDetector:
    """
    Scans a directory tree to identify microservice boundaries and technology stacks.
    """

    MANIFEST_MAP = {
        "package.json": ("JavaScript/TypeScript", "Node.js"),
        "pom.xml": ("Java", "Maven / Spring"),
        "build.gradle": ("Java/Kotlin", "Gradle"),
        "build.gradle.kts": ("Kotlin", "Gradle"),
        "go.mod": ("Go", "Go Module"),
        "Cargo.toml": ("Rust", "Cargo"),
        "requirements.txt": ("Python", "Python App"),
        "pyproject.toml": ("Python", "Python App"),
        "Pipfile": ("Python", "Pipenv"),
        "Gemfile": ("Ruby", "Ruby/Bundler"),
        "composer.json": ("PHP", "Composer"),
        "Dockerfile": ("Docker", "Containerized Service"),
        "docker-compose.yml": ("Docker", "Compose"),
        "compose.yaml": ("Docker", "Compose")
    }

    @classmethod
    def detect(cls, root_dir: str) -> List[ServiceRoot]:
        """
        Scans root_dir and discovers all distinct microservices or the root service.

        @param str root_dir: Root directory path
        @return List[ServiceRoot]: List of discovered microservice roots
        """
        root_dir = os.path.abspath(root_dir)
        if not os.path.exists(root_dir):
            raise FileNotFoundError(f"Scan path '{root_dir}' does not exist.")

        discovered_roots: Dict[str, ServiceRoot] = {}

        # 1. Check direct subdirectories for monorepo / microservices layout
        # Common layout folders: 'src/', 'services/', 'apps/', 'packages/', 'modules/', 'microservices/', 'cmd/'
        candidate_parent_dirs = ["", "src", "services", "apps", "packages", "modules", "microservices", "cmd"]

        for parent_rel in candidate_parent_dirs:
            parent_full = os.path.join(root_dir, parent_rel) if parent_rel else root_dir
            if not os.path.isdir(parent_full):
                continue

            try:
                entries = sorted(os.listdir(parent_full))
            except PermissionError:
                continue

            for entry in entries:
                if entry in IGNORED_DIRS:
                    continue
                entry_full = os.path.join(parent_full, entry)
                if not os.path.isdir(entry_full):
                    continue

                manifests = cls._find_manifests_in_dir(entry_full)
                if manifests:
                    rel_path = os.path.relpath(entry_full, root_dir).replace("\\", "/")
                    svc_id = cls._format_service_id(entry)
                    svc_name = cls._format_service_name(entry)
                    lang, framework, desc = cls._detect_stack(entry_full, manifests)

                    discovered_roots[rel_path] = ServiceRoot(
                        id=svc_id,
                        name=svc_name,
                        path=rel_path,
                        full_path=entry_full,
                        language=lang,
                        framework=framework,
                        manifest_files=manifests,
                        description=desc
                    )

        # 2. If subdirectories didn't produce multiple services, check root level
        if not discovered_roots:
            root_manifests = cls._find_manifests_in_dir(root_dir)
            folder_name = os.path.basename(root_dir) or "root-service"
            svc_id = cls._format_service_id(folder_name)
            svc_name = cls._format_service_name(folder_name)
            lang, framework, desc = cls._detect_stack(root_dir, root_manifests)

            discovered_roots["."] = ServiceRoot(
                id=svc_id,
                name=svc_name,
                path=".",
                full_path=root_dir,
                language=lang,
                framework=framework,
                manifest_files=root_manifests,
                description=desc
            )

        return list(discovered_roots.values())

    @classmethod
    def _find_manifests_in_dir(cls, directory: str) -> List[str]:
        """Finds known manifest files directly in the given directory."""
        found = []
        for filename in cls.MANIFEST_MAP.keys():
            if os.path.isfile(os.path.join(directory, filename)):
                found.append(filename)
        return found

    @classmethod
    def _format_service_id(cls, name: str) -> str:
        """Sanitizes service identifier (e.g. 'User Service' -> 'user-service')."""
        clean = name.lower().replace(" ", "-").replace("_", "-")
        # Ensure it has a meaningful id
        return clean or "service"

    @classmethod
    def _format_service_name(cls, name: str) -> str:
        """Formats human readable service name (e.g. 'user-service' -> 'User Service')."""
        parts = name.replace("-", " ").replace("_", " ").split()
        return " ".join([p.capitalize() for p in parts]) or "Service"

    @classmethod
    def _detect_stack(cls, directory: str, manifests: List[str]) -> (str, str, str):
        """
        Detects primary language, specific framework, and brief description.
        """
        # Node / JS / TS inspection
        if "package.json" in manifests:
            pkg_path = os.path.join(directory, "package.json")
            try:
                with open(pkg_path, "r", encoding="utf-8", errors="ignore") as f:
                    pkg = json.load(f)
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                desc = pkg.get("description", "")

                is_ts = "typescript" in deps or os.path.exists(os.path.join(directory, "tsconfig.json"))
                lang = "TypeScript" if is_ts else "Node.js"

                if "@nestjs/core" in deps:
                    return lang, "NestJS", desc or "NestJS enterprise microservice"
                elif "express" in deps:
                    return lang, "Express", desc or "Express REST microservice"
                elif "fastify" in deps:
                    return lang, "Fastify", desc or "Fastify high-performance service"
                elif "next" in deps:
                    return lang, "Next.js", desc or "Next.js fullstack application"
                elif "koa" in deps:
                    return lang, "Koa", desc or "Koa HTTP microservice"
                return lang, "Node.js Application", desc
            except Exception:
                return "JavaScript/TypeScript", "Node.js", ""

        # Python inspection
        if any(m in manifests for m in ["requirements.txt", "pyproject.toml", "Pipfile"]):
            content = ""
            for m in ["requirements.txt", "pyproject.toml", "Pipfile"]:
                m_path = os.path.join(directory, m)
                if os.path.isfile(m_path):
                    try:
                        with open(m_path, "r", encoding="utf-8", errors="ignore") as f:
                            content += f.read().lower() + "\n"
                    except Exception:
                        pass

            if "fastapi" in content:
                return "Python", "FastAPI", "High-performance FastAPI async microservice"
            elif "flask" in content:
                return "Python", "Flask", "Flask REST microservice"
            elif "django" in content:
                return "Python", "Django", "Django backend service"
            elif "celery" in content and "fastapi" not in content:
                return "Python", "Celery Worker", "Celery async background worker service"
            return "Python", "Python Application", "Python microservice"

        # Go inspection
        if "go.mod" in manifests:
            go_mod = os.path.join(directory, "go.mod")
            try:
                with open(go_mod, "r", encoding="utf-8", errors="ignore") as f:
                    c = f.read().lower()
                if "gin-gonic/gin" in c:
                    return "Go", "Gin", "Go Gin high-throughput microservice"
                elif "labstack/echo" in c:
                    return "Go", "Echo", "Go Echo microservice"
                elif "go-chi/chi" in c:
                    return "Go", "Chi", "Go Chi REST microservice"
                elif "gofiber/fiber" in c:
                    return "Go", "Fiber", "Go Fiber microservice"
                return "Go", "Go Service", "Go microservice"
            except Exception:
                return "Go", "Go Service", ""

        # Java / Kotlin inspection
        if any(m in manifests for m in ["pom.xml", "build.gradle", "build.gradle.kts"]):
            return "Java", "Spring Boot", "Enterprise Java / Spring Boot microservice"

        # Rust inspection
        if "Cargo.toml" in manifests:
            return "Rust", "Actix / Axum", "Rust high-performance service"

        # Ruby inspection
        if "Gemfile" in manifests:
            return "Ruby", "Ruby on Rails", "Ruby on Rails microservice"

        if "Dockerfile" in manifests:
            return "Docker", "Container Service", "Containerized application"

        return "Unknown", "General Service", "Microservice component"
