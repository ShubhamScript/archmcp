"""
Background job and task scheduler extractor.

Discovers background processing tasks, asynchronous queues, and cron jobs
across Celery, BullMQ, Spring @Scheduled, Temporal, and standard schedulers.

@author Shubham Upadhyay
@license MIT
"""

import os
import re
from typing import List, Set, Dict
from ..models.discovery import BackgroundJobInfo

IGNORED_DIRS: Set[str] = {
    ".git", ".venv", "venv", "env", "node_modules", "__pycache__",
    ".pytest_cache", "dist", "build", "target", "vendor", ".idea",
    ".vscode", "coverage", "htmlcov", ".mypy_cache"
}


class JobExtractor:
    """
    Scans source files to extract background jobs, Celery tasks, and cron schedules.
    """

    # Celery tasks
    CELERY_TASK_PATTERN = re.compile(
        r"""@(?:shared_task|app\.task|celery\.task|celery_app\.task)[^)]*\)\s*\ndef\s+([a-zA-Z0-9_]+)\s*\(""",
        re.MULTILINE
    )
    CELERY_TASK_SIMPLE = re.compile(
        r"""@(?:shared_task|app\.task|celery\.task|celery_app\.task)\s*\ndef\s+([a-zA-Z0-9_]+)\s*\(""",
        re.MULTILINE
    )

    # Bull / BullMQ
    BULL_WORKER_PATTERN = re.compile(
        r"""new\s+(?:Worker|Queue)\s*\(\s*["']([a-zA-Z0-9_\-]+)["']""",
        re.IGNORECASE
    )
    BULL_PROCESS_PATTERN = re.compile(
        r"""(?:queue|worker)\.process\s*\(\s*(?:["']([a-zA-Z0-9_\-]+)["']\s*,\s*)?""",
        re.IGNORECASE
    )

    # Spring @Scheduled
    SPRING_SCHEDULED_PATTERN = re.compile(
        r"""@Scheduled\s*\((.*?)\)\s*\n\s*(?:public\s+)?void\s+([a-zA-Z0-9_]+)\s*\(""",
        re.DOTALL
    )

    # Node-cron / Agenda
    NODE_CRON_PATTERN = re.compile(
        r"""cron\.schedule\s*\(\s*["']([^"']+)["']\s*,\s*(?:async\s*)?\(\)\s*=>""",
        re.IGNORECASE
    )
    AGENDA_PATTERN = re.compile(
        r"""agenda\.define\s*\(\s*["']([a-zA-Z0-9_\-]+)["']""",
        re.IGNORECASE
    )

    # Temporal
    TEMPORAL_WORKFLOW = re.compile(
        r"""@(?:workflow\.defn|activity\.defn)\s*\n(?:async\s+)?def\s+([a-zA-Z0-9_]+)\s*\(""",
        re.MULTILINE
    )

    # APScheduler
    APSCHEDULER_PATTERN = re.compile(
        r"""@scheduler\.scheduled_job\s*\((.*?)\)\s*\ndef\s+([a-zA-Z0-9_]+)\s*\(""",
        re.DOTALL
    )

    @classmethod
    def extract_from_dir(cls, directory: str) -> List[BackgroundJobInfo]:
        """
        Scans directory for background jobs and scheduled tasks.

        @param str directory: Service or project root
        @return List[BackgroundJobInfo]: Extracted background jobs
        """
        jobs_dict: Dict[str, BackgroundJobInfo] = {}

        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext not in {".py", ".ts", ".js", ".java", ".kt", ".go", ".rb"}:
                    continue

                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, directory).replace("\\", "/")

                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        code = f.read()
                except Exception:
                    continue

                # 1. Python Celery & APScheduler & Temporal
                if ext == ".py":
                    for match in cls.CELERY_TASK_PATTERN.finditer(code):
                        task_name = match.group(1)
                        jobs_dict[task_name] = BackgroundJobInfo(
                            name=task_name,
                            job_type="Celery Task",
                            schedule="Asynchronous Event / Worker",
                            source_file=rel_path
                        )
                    for match in cls.CELERY_TASK_SIMPLE.finditer(code):
                        task_name = match.group(1)
                        jobs_dict[task_name] = BackgroundJobInfo(
                            name=task_name,
                            job_type="Celery Task",
                            schedule="Asynchronous Event / Worker",
                            source_file=rel_path
                        )
                    for match in cls.APSCHEDULER_PATTERN.finditer(code):
                        args, name = match.group(1), match.group(2)
                        jobs_dict[name] = BackgroundJobInfo(
                            name=name,
                            job_type="APScheduler Cron",
                            schedule=args.strip(),
                            source_file=rel_path
                        )
                    for match in cls.TEMPORAL_WORKFLOW.finditer(code):
                        name = match.group(1)
                        jobs_dict[name] = BackgroundJobInfo(
                            name=name,
                            job_type="Temporal Workflow/Activity",
                            schedule="Orchestrated Workflow",
                            source_file=rel_path
                        )

                # 2. Node / TypeScript (BullMQ, node-cron, Agenda)
                elif ext in {".ts", ".js"}:
                    for match in cls.BULL_WORKER_PATTERN.finditer(code):
                        q_name = match.group(1)
                        jobs_dict[f"bull:{q_name}"] = BackgroundJobInfo(
                            name=f"Bull Queue: {q_name}",
                            job_type="BullMQ Background Worker",
                            schedule="Redis-backed Queue",
                            source_file=rel_path
                        )
                    for match in cls.NODE_CRON_PATTERN.finditer(code):
                        cron_expr = match.group(1)
                        jobs_dict[f"cron:{cron_expr}:{rel_path}"] = BackgroundJobInfo(
                            name=f"Scheduled Cron ({cron_expr})",
                            job_type="Node Cron Job",
                            schedule=cron_expr,
                            source_file=rel_path
                        )
                    for match in cls.AGENDA_PATTERN.finditer(code):
                        job_name = match.group(1)
                        jobs_dict[job_name] = BackgroundJobInfo(
                            name=job_name,
                            job_type="Agenda Job",
                            schedule="MongoDB Scheduled Job",
                            source_file=rel_path
                        )

                # 3. Java / Kotlin (Spring @Scheduled)
                elif ext in {".java", ".kt"}:
                    for match in cls.SPRING_SCHEDULED_PATTERN.finditer(code):
                        sched_args, method_name = match.group(1), match.group(2)
                        jobs_dict[method_name] = BackgroundJobInfo(
                            name=method_name,
                            job_type="Spring @Scheduled",
                            schedule=sched_args.strip(),
                            source_file=rel_path
                        )

        return list(jobs_dict.values())
