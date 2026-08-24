"""
ArchMCP - Fine-Grained Role-Based Access Control (RBAC) & Scopes.

Defines granular security scopes for MCP tools, resources, and administrative operations.

@author Shubham Upadhyay
@license MIT
"""

from typing import List, Set, Union
from enum import Enum


class Scope(str, Enum):
    """
    Standard hierarchical permission scopes for ArchMCP.
    """
    ALL = "*"
    ARCH_READ = "arch:read"
    ARCH_SCHEMA_READ = "arch:schema:read"
    ARCH_BLAST_RADIUS = "arch:blast_radius"
    ARCH_DIAGRAM = "arch:diagram"
    ARCH_CONTEXT = "arch:context"
    ARCH_WRITE = "arch:write"
    ARCH_ADMIN = "arch:admin"
    ARCH_AUDIT = "arch:audit"


# Standard pre-packaged role profiles
ROLE_PROFILES = {
    "admin": [Scope.ALL.value],
    "architect": [
        Scope.ARCH_READ.value,
        Scope.ARCH_SCHEMA_READ.value,
        Scope.ARCH_BLAST_RADIUS.value,
        Scope.ARCH_DIAGRAM.value,
        Scope.ARCH_CONTEXT.value,
        Scope.ARCH_WRITE.value,
    ],
    "developer": [
        Scope.ARCH_READ.value,
        Scope.ARCH_SCHEMA_READ.value,
        Scope.ARCH_DIAGRAM.value,
        Scope.ARCH_CONTEXT.value,
    ],
    "viewer": [
        Scope.ARCH_READ.value,
    ],
    "service_account": [
        Scope.ARCH_READ.value,
        Scope.ARCH_WRITE.value,
    ]
}


def has_required_scopes(
    granted_scopes: List[str],
    required_scopes: Union[List[str], Set[str], str]
) -> bool:
    """
    Evaluates whether the caller's granted scopes satisfy the required permission scopes.
    Supports wildcard '*' superuser scope.

    @param List[str] granted_scopes: Scopes associated with the authenticated caller
    @param Union[List[str], Set[str], str] required_scopes: Scopes needed to execute the operation
    @return bool: True if authorized, False otherwise
    """
    if not granted_scopes:
        return False

    granted_set = set(granted_scopes)

    # Superuser wildcard grant satisfies everything
    if Scope.ALL.value in granted_set or "*" in granted_set:
        return True

    if isinstance(required_scopes, str):
        req_set = {required_scopes}
    else:
        req_set = set(required_scopes)

    # All required scopes must be present in granted scopes
    return req_set.issubset(granted_set)
