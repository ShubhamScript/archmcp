"""
Docker and container infrastructure extractor.

Extracts container service definitions, base images, port bindings,
and dependencies from docker-compose.yml and Dockerfile manifests.

@author Shubham Upadhyay
@license MIT
"""

import os
import re
from typing import List, Set, Dict
import yaml
from ..models.discovery import DockerServiceInfo

IGNORED_DIRS: Set[str] = {
    ".git", ".venv", "venv", "env", "node_modules", "__pycache__",
    ".pytest_cache", "dist", "build", "target", "vendor", ".idea",
    ".vscode", "coverage", "htmlcov", ".mypy_cache"
}


class DockerExtractor:
    """
    Scans directory trees for Docker Compose and Dockerfile specifications.
    """

    EXPOSE_PATTERN = re.compile(r"""^EXPOSE\s+(.*)$""", re.MULTILINE | re.IGNORECASE)
    FROM_PATTERN = re.compile(r"""^FROM\s+([^\s]+)""", re.MULTILINE | re.IGNORECASE)

    @classmethod
    def extract_from_dir(cls, directory: str) -> List[DockerServiceInfo]:
        """
        Scans directory for Docker Compose and Dockerfile specifications.

        @param str directory: Service or project root
        @return List[DockerServiceInfo]: Discovered docker services
        """
        services_dict: Dict[str, DockerServiceInfo] = {}

        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, directory).replace("\\", "/")

                # 1. docker-compose files
                if file in {"docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"}:
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            data = yaml.safe_load(f)
                        if isinstance(data, dict) and "services" in data:
                            raw_services = data["services"]
                            if isinstance(raw_services, dict):
                                for s_name, s_cfg in raw_services.items():
                                    if not isinstance(s_cfg, dict):
                                        continue
                                    img = s_cfg.get("image") or (s_cfg.get("build") if isinstance(s_cfg.get("build"), str) else "custom-build")
                                    ports = [str(p) for p in s_cfg.get("ports", [])]
                                    deps = s_cfg.get("depends_on", [])
                                    if isinstance(deps, dict):
                                        deps = list(deps.keys())
                                    elif not isinstance(deps, list):
                                        deps = [str(deps)]

                                    env = s_cfg.get("environment", [])
                                    if isinstance(env, dict):
                                        env = [f"{k}={v}" for k, v in env.items()]

                                    services_dict[s_name] = DockerServiceInfo(
                                        service_name=s_name,
                                        image=img,
                                        ports=ports,
                                        depends_on=deps,
                                        environment=[e.split("=")[0] for e in env if isinstance(e, str)],
                                        source_file=rel_path
                                    )
                    except Exception:
                        pass

                # 2. Dockerfile
                elif file in {"Dockerfile", "Containerfile"} or file.endswith(".dockerfile"):
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        from_m = cls.FROM_PATTERN.search(content)
                        base_img = from_m.group(1) if from_m else "scratch"
                        expose_m = cls.EXPOSE_PATTERN.findall(content)
                        ports = []
                        for exp in expose_m:
                            ports.extend(exp.strip().split())

                        folder_name = os.path.basename(os.path.dirname(full_path)) or "app"
                        if folder_name not in services_dict:
                            services_dict[folder_name] = DockerServiceInfo(
                                service_name=folder_name,
                                image=base_img,
                                ports=ports,
                                depends_on=[],
                                environment=[],
                                source_file=rel_path
                            )
                    except Exception:
                        pass

        return list(services_dict.values())
