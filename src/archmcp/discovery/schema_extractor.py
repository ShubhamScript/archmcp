"""
Database schema, tables, and ORM model extractor.

Discovers database tables, fields, and primary keys across SQLAlchemy,
Django, Prisma, TypeORM, Mongoose, GORM, JPA, and raw SQL schemas/migrations.

@author Shubham Upadhyay
@license MIT
"""

import os
import re
from typing import List, Set, Dict
from ..models.database_table import DatabaseTable

IGNORED_DIRS: Set[str] = {
    ".git", ".venv", "venv", "env", "node_modules", "__pycache__",
    ".pytest_cache", "dist", "build", "target", "vendor", ".idea",
    ".vscode", "coverage", "htmlcov", ".mypy_cache"
}


class SchemaExtractor:
    """
    Scans directory trees for ORM models, Prisma schemas, and SQL migration files.
    """

    # SQL CREATE TABLE Pattern
    SQL_CREATE_TABLE = re.compile(
        r"""CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?["'`]?([a-zA-Z0-9_]+)["'`]?\s*\((.*?)\);""",
        re.IGNORECASE | re.DOTALL
    )

    # Prisma model Pattern
    PRISMA_MODEL = re.compile(
        r"""model\s+([a-zA-Z0-9_]+)\s*\{(.*?)\}""",
        re.DOTALL
    )

    # SQLAlchemy Patterns
    SQLALCHEMY_TABLENAME = re.compile(
        r"""__tablename__\s*=\s*["']([a-zA-Z0-9_]+)["']"""
    )
    SQLALCHEMY_COLUMN = re.compile(
        r"""([a-zA-Z0-9_]+)\s*=\s*(?:mapped_column|Column)\s*\((.*?)\)"""
    )
    SQLALCHEMY_CLASS = re.compile(
        r"""class\s+([a-zA-Z0-9_]+)\s*\(\s*(?:Base|db\.Model|DeclarativeBase|SQLModel)[^)]*\):"""
    )

    # Django ORM Patterns
    DJANGO_MODEL = re.compile(
        r"""class\s+([a-zA-Z0-9_]+)\s*\(\s*models\.Model\s*\):"""
    )
    DJANGO_FIELD = re.compile(
        r"""([a-zA-Z0-9_]+)\s*=\s*models\.([a-zA-Z0-9_]+Field)\s*\("""
    )

    # TypeORM Patterns
    TYPEORM_ENTITY = re.compile(
        r"""@Entity\s*\(\s*(?:["']([a-zA-Z0-9_]+)["'])?\s*\)\s*(?:export\s+)?class\s+([a-zA-Z0-9_]+)"""
    )

    # Mongoose Patterns
    MONGOOSE_MODEL = re.compile(
        r"""(?:mongoose\.)?model\s*\(\s*["']([a-zA-Z0-9_]+)["']"""
    )

    # JPA / Hibernate Patterns
    JPA_TABLE = re.compile(
        r"""@Table\s*\(\s*name\s*=\s*["']([a-zA-Z0-9_]+)["']\s*\)"""
    )
    JPA_ENTITY = re.compile(
        r"""@Entity\s+(?:public\s+)?class\s+([a-zA-Z0-9_]+)"""
    )

    # GORM Patterns
    GORM_STRUCT = re.compile(
        r"""type\s+([a-zA-Z0-9_]+)\s+struct\s*\{(.*?)\}""",
        re.DOTALL
    )

    @classmethod
    def extract_from_dir(cls, directory: str) -> List[DatabaseTable]:
        """
        Recursively scans directory for database tables and ORM schemas.

        @param str directory: Service or project root
        @return List[DatabaseTable]: Extracted database tables
        """
        tables_dict: Dict[str, DatabaseTable] = {}

        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

            for file in files:
                full_path = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()

                # 1. Prisma Schema File
                if file.endswith(".prisma"):
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        for t in cls._parse_prisma(content, file):
                            tables_dict[t.name.lower()] = t
                    except Exception:
                        pass

                # 2. Raw SQL / Migrations
                elif ext == ".sql":
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        for t in cls._parse_sql(content, file):
                            tables_dict[t.name.lower()] = t
                    except Exception:
                        pass

                # 3. Python files (SQLAlchemy / Django / SQLModel)
                elif ext == ".py":
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        for t in cls._parse_python_models(content, file):
                            tables_dict[t.name.lower()] = t
                    except Exception:
                        pass

                # 4. JS/TS files (TypeORM / Mongoose)
                elif ext in {".ts", ".js"}:
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        for t in cls._parse_js_models(content, file):
                            tables_dict[t.name.lower()] = t
                    except Exception:
                        pass

                # 5. Java files (JPA / Hibernate)
                elif ext in {".java", ".kt"}:
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        for t in cls._parse_java_models(content, file):
                            tables_dict[t.name.lower()] = t
                    except Exception:
                        pass

                # 6. Go files (GORM)
                elif ext == ".go":
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        for t in cls._parse_go_models(content, file):
                            tables_dict[t.name.lower()] = t
                    except Exception:
                        pass

        return list(tables_dict.values())

    @classmethod
    def _parse_sql(cls, sql_text: str, filename: str) -> List[DatabaseTable]:
        tables = []
        for match in cls.SQL_CREATE_TABLE.finditer(sql_text):
            table_name = match.group(1).strip('"\'`')
            body = match.group(2)
            cols = []
            for line in body.splitlines():
                line = line.strip().rstrip(",")
                if not line or line.upper().startswith(("PRIMARY KEY", "FOREIGN KEY", "CONSTRAINT", "INDEX", "KEY")):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    cols.append(f"{parts[0]} ({parts[1]})")
                elif len(parts) == 1:
                    cols.append(parts[0])

            tables.append(DatabaseTable(
                name=table_name,
                description=f"Relational table extracted from SQL migration ({filename})",
                columns=cols or ["id (PRIMARY KEY)"]
            ))
        return tables

    @classmethod
    def _parse_prisma(cls, prisma_text: str, filename: str) -> List[DatabaseTable]:
        tables = []
        for match in cls.PRISMA_MODEL.finditer(prisma_text):
            model_name = match.group(1)
            body = match.group(2)
            cols = []
            for line in body.splitlines():
                line = line.strip()
                if not line or line.startswith("//") or line.startswith("@@"):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    col_name, col_type = parts[0], parts[1]
                    cols.append(f"{col_name} ({col_type})")

            tables.append(DatabaseTable(
                name=model_name.lower() + "s" if not model_name.endswith("s") else model_name.lower(),
                description=f"Prisma model '{model_name}' ({filename})",
                columns=cols
            ))
        return tables

    @classmethod
    def _parse_python_models(cls, py_text: str, filename: str) -> List[DatabaseTable]:
        tables = []

        # SQLAlchemy __tablename__
        for tbl_match in cls.SQLALCHEMY_TABLENAME.finditer(py_text):
            table_name = tbl_match.group(1)
            cols = []
            for col_match in cls.SQLALCHEMY_COLUMN.finditer(py_text):
                cols.append(col_match.group(1))
            tables.append(DatabaseTable(
                name=table_name,
                description=f"SQLAlchemy ORM table defined in {filename}",
                columns=cols or ["id", "created_at"]
            ))

        # Django Models
        for model_match in cls.DJANGO_MODEL.finditer(py_text):
            model_name = model_match.group(1)
            cols = ["id (PK)"]
            for field_match in cls.DJANGO_FIELD.finditer(py_text):
                cols.append(f"{field_match.group(1)} ({field_match.group(2)})")
            tables.append(DatabaseTable(
                name=model_name.lower() + "s" if not model_name.endswith("s") else model_name.lower(),
                description=f"Django Model '{model_name}' in {filename}",
                columns=cols
            ))

        return tables

    @classmethod
    def _parse_js_models(cls, js_text: str, filename: str) -> List[DatabaseTable]:
        tables = []
        # TypeORM
        for match in cls.TYPEORM_ENTITY.finditer(js_text):
            table_name = match.group(1) or match.group(2).lower() + "s"
            tables.append(DatabaseTable(
                name=table_name,
                description=f"TypeORM entity in {filename}",
                columns=["id (PK)"]
            ))

        # Mongoose
        for match in cls.MONGOOSE_MODEL.finditer(js_text):
            model_name = match.group(1)
            tables.append(DatabaseTable(
                name=model_name.lower() + "s" if not model_name.endswith("s") else model_name.lower(),
                description=f"Mongoose collection '{model_name}' in {filename}",
                columns=["_id (ObjectId)", "createdAt", "updatedAt"]
            ))

        return tables

    @classmethod
    def _parse_java_models(cls, java_text: str, filename: str) -> List[DatabaseTable]:
        tables = []
        table_name = None
        tbl_match = cls.JPA_TABLE.search(java_text)
        if tbl_match:
            table_name = tbl_match.group(1)
        else:
            entity_match = cls.JPA_ENTITY.search(java_text)
            if entity_match:
                table_name = entity_match.group(1).lower() + "s"

        if table_name:
            tables.append(DatabaseTable(
                name=table_name,
                description=f"JPA / Hibernate Entity table in {filename}",
                columns=["id (BIGINT, PK)"]
            ))
        return tables

    @classmethod
    def _parse_go_models(cls, go_text: str, filename: str) -> List[DatabaseTable]:
        tables = []
        for match in cls.GORM_STRUCT.finditer(go_text):
            struct_name = match.group(1)
            body = match.group(2)
            if "gorm:" in body or "gorm.Model" in body:
                tables.append(DatabaseTable(
                    name=struct_name.lower() + "s" if not struct_name.endswith("s") else struct_name.lower(),
                    description=f"GORM struct '{struct_name}' in {filename}",
                    columns=["id (uint, PK)"]
                ))
        return tables
