"""
Environment variable and configuration extractor.

Discovers environment configurations across .env files, YAML/properties configs,
and source code references, while masking sensitive secrets.

@author Shubham Upadhyay
@license MIT
"""

import os
import re
from typing import List, Set, Dict, Optional
import yaml
from ..models.discovery import EnvVarInfo

IGNORED_DIRS: Set[str] = {
    ".git", ".venv", "venv", "env", "node_modules", "__pycache__",
    ".pytest_cache", "dist", "build", "target", "vendor", ".idea",
    ".vscode", "coverage", "htmlcov", ".mypy_cache"
}

SECRET_KEYWORDS = {"secret", "password", "token", "key", "auth", "credential", "private", "cert", "api_key", "jwt"}


class ConfigExtractor:
    """
    Extracts environment variables and configuration settings.
    """

    ENV_LINE_PATTERN = re.compile(
        r"""^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$"""
    )
    OS_GETENV_PY = re.compile(
        r"""(?:os\.getenv|os\.environ\.get|os\.environ\[)\s*\(?\s*["']([A-Za-z_][A-Za-z0-9_]*)["'](?:\s*,\s*["']?([^"'\)]*)["']?)?"""
    )
    PROCESS_ENV_JS = re.compile(
        r"""process\.env\.([A-Za-z_][A-Za-z0-9_]*)"""
    )
    OS_GETENV_GO = re.compile(
        r"""os\.Getenv\s*\(\s*["']([A-Za-z_][A-Za-z0-9_]*)["']\s*\)"""
    )

    @classmethod
    def extract_from_dir(cls, directory: str) -> List[EnvVarInfo]:
        """
        Scans directory for config files and code env references.

        @param str directory: Service or project root
        @return List[EnvVarInfo]: Discovered configuration keys
        """
        env_dict: Dict[str, EnvVarInfo] = {}

        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, directory).replace("\\", "/")
                ext = os.path.splitext(file)[1].lower()

                # 1. .env files
                if file.startswith(".env") or file.endswith(".env"):
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            for line in f:
                                line = line.strip()
                                if not line or line.startswith("#"):
                                    continue
                                m = cls.ENV_LINE_PATTERN.match(line)
                                if m:
                                    k, val = m.group(1), m.group(2).strip("\"'")
                                    is_secret = cls._is_secret(k)
                                    masked_val = "********" if (is_secret and val) else val
                                    env_dict[k] = EnvVarInfo(
                                        key=k,
                                        default_value=masked_val,
                                        is_secret=is_secret,
                                        source_file=rel_path
                                    )
                    except Exception:
                        pass

                # 2. application.properties / application.yml
                elif file in {"application.properties", "config.properties"}:
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            for line in f:
                                line = line.strip()
                                if not line or line.startswith("#"):
                                    continue
                                if "=" in line:
                                    k, val = line.split("=", 1)
                                    k, val = k.strip(), val.strip()
                                    is_sec = cls._is_secret(k)
                                    env_dict[k] = EnvVarInfo(
                                        key=k,
                                        default_value="********" if (is_sec and val) else val,
                                        is_secret=is_sec,
                                        source_file=rel_path
                                    )
                    except Exception:
                        pass

                elif file in {"application.yml", "application.yaml", "config.yaml", "config.yml"}:
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            data = yaml.safe_load(f)
                        if isinstance(data, dict):
                            cls._flatten_yaml(data, "", rel_path, env_dict)
                    except Exception:
                        pass

                # 3. Source code os.getenv / process.env references
                elif ext in {".py", ".ts", ".js", ".go"}:
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            code = f.read()
                        if ext == ".py":
                            for m in cls.OS_GETENV_PY.finditer(code):
                                k = m.group(1)
                                default_v = m.group(2) or None
                                if k not in env_dict:
                                    is_sec = cls._is_secret(k)
                                    env_dict[k] = EnvVarInfo(
                                        key=k,
                                        default_value="********" if is_sec else default_v,
                                        is_secret=is_sec,
                                        source_file=rel_path
                                    )
                        elif ext in {".ts", ".js"}:
                            for m in cls.PROCESS_ENV_JS.finditer(code):
                                k = m.group(1)
                                if k not in env_dict:
                                    is_sec = cls._is_secret(k)
                                    env_dict[k] = EnvVarInfo(
                                        key=k,
                                        default_value="********" if is_sec else None,
                                        is_secret=is_sec,
                                        source_file=rel_path
                                    )
                        elif ext == ".go":
                            for m in cls.OS_GETENV_GO.finditer(code):
                                k = m.group(1)
                                if k not in env_dict:
                                    is_sec = cls._is_secret(k)
                                    env_dict[k] = EnvVarInfo(
                                        key=k,
                                        default_value="********" if is_sec else None,
                                        is_secret=is_sec,
                                        source_file=rel_path
                                    )
                    except Exception:
                        pass

        return list(env_dict.values())

    @classmethod
    def _flatten_yaml(cls, d: dict, prefix: str, source_file: str, out_dict: dict) -> None:
        for k, v in d.items():
            full_k = f"{prefix}.{k}" if prefix else str(k)
            if isinstance(v, dict):
                cls._flatten_yaml(v, full_k, source_file, out_dict)
            else:
                is_sec = cls._is_secret(full_k)
                val_str = str(v)
                out_dict[full_k] = EnvVarInfo(
                    key=full_k,
                    default_value="********" if (is_sec and val_str) else val_str,
                    is_secret=is_sec,
                    source_file=source_file
                )

    @staticmethod
    def _is_secret(key: str) -> bool:
        k_lower = key.lower()
        return any(sec in k_lower for sec in SECRET_KEYWORDS)
