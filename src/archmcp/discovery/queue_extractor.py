"""
Message queue and event stream extractor.

Discovers event topics and messaging queues across Kafka, RabbitMQ,
AWS SQS/SNS, Redis PubSub, Celery, and NATS.

@author Shubham Upadhyay
@license MIT
"""

import os
import re
from typing import List, Set, Dict
from ..models.discovery import MessageQueueInfo

IGNORED_DIRS: Set[str] = {
    ".git", ".venv", "venv", "env", "node_modules", "__pycache__",
    ".pytest_cache", "dist", "build", "target", "vendor", ".idea",
    ".vscode", "coverage", "htmlcov", ".mypy_cache"
}


class QueueExtractor:
    """
    Scans source files to extract message queue topics and event channels.
    """

    # Kafka patterns
    KAFKA_SEND_PY = re.compile(
        r"""(?:producer\.send|publish|produce)\s*\(\s*(?:topic\s*=\s*)?["']([a-zA-Z0-9_\-\.]+)["']""",
        re.IGNORECASE
    )
    KAFKA_SUB_PY = re.compile(
        r"""(?:consumer\.subscribe|subscribe)\s*\(\s*(?:\[\s*)?["']([a-zA-Z0-9_\-\.]+)["']""",
        re.IGNORECASE
    )
    KAFKA_JS = re.compile(
        r"""(?:topic)\s*:\s*["']([a-zA-Z0-9_\-\.]+)["']"""
    )
    KAFKA_JAVA = re.compile(
        r"""@KafkaListener\s*\(\s*(?:topics\s*=\s*)?["']([a-zA-Z0-9_\-\.]+)["']"""
    )

    # RabbitMQ / AMQP patterns
    RABBIT_QUEUE = re.compile(
        r"""queue_declare\s*\(\s*(?:queue\s*=\s*)?["']([a-zA-Z0-9_\-\.]+)["']""",
        re.IGNORECASE
    )
    RABBIT_PUBLISH = re.compile(
        r"""basic_publish\s*\([^)]*routing_key\s*=\s*["']([a-zA-Z0-9_\-\.]+)["']""",
        re.IGNORECASE
    )
    RABBIT_CONSUME = re.compile(
        r"""basic_consume\s*\([^)]*queue\s*=\s*["']([a-zA-Z0-9_\-\.]+)["']""",
        re.IGNORECASE
    )
    RABBIT_JAVA = re.compile(
        r"""@RabbitListener\s*\(\s*(?:queues\s*=\s*)?["']([a-zA-Z0-9_\-\.]+)["']"""
    )

    # Redis PubSub patterns
    REDIS_PUB = re.compile(
        r"""(?:redis|r|client)\.publish\s*\(\s*["']([a-zA-Z0-9_\-\.]+)["']""",
        re.IGNORECASE
    )
    REDIS_SUB = re.compile(
        r"""(?:pubsub|ps|client)\.subscribe\s*\(\s*["']([a-zA-Z0-9_\-\.]+)["']""",
        re.IGNORECASE
    )

    # SQS / SNS
    AWS_SNS_TOPIC = re.compile(
        r"""(?:publish|send_message)\s*\([^)]*TopicArn=["'][^"']*[:/]([a-zA-Z0-9_\-]+)["']""",
        re.IGNORECASE
    )

    @classmethod
    def extract_from_dir(cls, directory: str) -> List[MessageQueueInfo]:
        """
        Scans directory for messaging queues and event topics.

        @param str directory: Service or project root
        @return List[MessageQueueInfo]: Extracted messaging queues
        """
        queues_dict: Dict[str, MessageQueueInfo] = {}

        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext not in {".py", ".ts", ".js", ".go", ".java", ".kt", ".yaml", ".yml", ".json"}:
                    continue

                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, directory).replace("\\", "/")

                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                except Exception:
                    continue

                # 1. Kafka
                if "kafka" in content.lower() or ext in {".py", ".ts", ".js", ".java"}:
                    for m in cls.KAFKA_SEND_PY.finditer(content):
                        topic = m.group(1)
                        if cls._is_valid_topic(topic):
                            key = f"kafka:{topic}:producer"
                            queues_dict[key] = MessageQueueInfo(
                                name=topic, broker_type="Kafka", role="producer", source_file=rel_path
                            )

                    for m in cls.KAFKA_SUB_PY.finditer(content):
                        topic = m.group(1)
                        if cls._is_valid_topic(topic):
                            key = f"kafka:{topic}:consumer"
                            queues_dict[key] = MessageQueueInfo(
                                name=topic, broker_type="Kafka", role="consumer", source_file=rel_path
                            )

                    if ext in {".ts", ".js"} and "kafka" in content.lower():
                        for m in cls.KAFKA_JS.finditer(content):
                            topic = m.group(1)
                            if cls._is_valid_topic(topic):
                                role = "consumer" if "consumer" in content.lower() else "producer"
                                key = f"kafka:{topic}:{role}"
                                queues_dict[key] = MessageQueueInfo(
                                    name=topic, broker_type="Kafka", role=role, source_file=rel_path
                                )

                    for m in cls.KAFKA_JAVA.finditer(content):
                        topic = m.group(1)
                        if cls._is_valid_topic(topic):
                            key = f"kafka:{topic}:consumer"
                            queues_dict[key] = MessageQueueInfo(
                                name=topic, broker_type="Kafka", role="consumer", source_file=rel_path
                            )

                # 2. RabbitMQ
                if "amqp" in content.lower() or "rabbit" in content.lower() or "pika" in content.lower():
                    for m in cls.RABBIT_QUEUE.finditer(content):
                        q = m.group(1)
                        if cls._is_valid_topic(q):
                            queues_dict[f"rabbit:{q}:producer"] = MessageQueueInfo(
                                name=q, broker_type="RabbitMQ", role="producer", source_file=rel_path
                            )
                    for m in cls.RABBIT_PUBLISH.finditer(content):
                        q = m.group(1)
                        if cls._is_valid_topic(q):
                            queues_dict[f"rabbit:{q}:producer"] = MessageQueueInfo(
                                name=q, broker_type="RabbitMQ", role="producer", source_file=rel_path
                            )
                    for m in cls.RABBIT_CONSUME.finditer(content):
                        q = m.group(1)
                        if cls._is_valid_topic(q):
                            queues_dict[f"rabbit:{q}:consumer"] = MessageQueueInfo(
                                name=q, broker_type="RabbitMQ", role="consumer", source_file=rel_path
                            )
                    for m in cls.RABBIT_JAVA.finditer(content):
                        q = m.group(1)
                        if cls._is_valid_topic(q):
                            queues_dict[f"rabbit:{q}:consumer"] = MessageQueueInfo(
                                name=q, broker_type="RabbitMQ", role="consumer", source_file=rel_path
                            )

                # 3. Redis PubSub
                if "redis" in content.lower():
                    for m in cls.REDIS_PUB.finditer(content):
                        ch = m.group(1)
                        if cls._is_valid_topic(ch):
                            queues_dict[f"redis:{ch}:producer"] = MessageQueueInfo(
                                name=ch, broker_type="Redis PubSub", role="producer", source_file=rel_path
                            )
                    for m in cls.REDIS_SUB.finditer(content):
                        ch = m.group(1)
                        if cls._is_valid_topic(ch):
                            queues_dict[f"redis:{ch}:consumer"] = MessageQueueInfo(
                                name=ch, broker_type="Redis PubSub", role="consumer", source_file=rel_path
                            )

        return list(queues_dict.values())

    @staticmethod
    def _is_valid_topic(name: str) -> bool:
        """Filters out code literals that are not real queue/topic names."""
        if not name or len(name) < 2:
            return False
        if name.startswith(("http://", "https://", "/", ".")):
            return False
        if name.lower() in {"utf-8", "true", "false", "none", "null", "get", "post", "json"}:
            return False
        return True
