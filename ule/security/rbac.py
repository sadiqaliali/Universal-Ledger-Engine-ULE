"""Role-Based Access Control for ULE."""

from typing import Optional, Set
from ule.core.exceptions import AuthenticationError


class RBAC:
    """Role-Based Access Control."""
    
    ROLES = {
        "admin": {"read", "write", "delete", "admin", "audit"},
        "write": {"read", "write", "audit"},
        "user": {"read", "audit"},
        "readonly": {"read"}
    }
    
    def __init__(self, db_connection):
        self._conn = db_connection
        self._user_permissions: dict = {}
    
    def get_user_permissions(self, username: str) -> Set[str]:
        """Get permissions for user."""
        if username in self._user_permissions:
            return self._user_permissions[username]
        
        cursor = self._conn.execute(
            "SELECT role FROM _users WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        
        if not row:
            return set()
        
        role = row[0]
        permissions = self.ROLES.get(role, set())
        self._user_permissions[username] = permissions
        return permissions
    
    def check_permission(self, username: str, permission: str) -> bool:
        """Check if user has permission."""
        permissions = self.get_user_permissions(username)
        return permission in permissions
    
    def grant_permission(self, username: str, permission: str) -> None:
        """Grant additional permission to user."""
        # For simplicity, we just change the role
        # In production, you'd have a separate permissions table
        if permission == "write":
            self._conn.execute(
                "UPDATE _users SET role = 'write' WHERE username = ?",
                (username,)
            )
            self._conn.commit()
            self._user_permissions[username] = self.ROLES["write"]
    
    def revoke_permission(self, username: str, permission: str) -> None:
        """Revoke permission from user."""
        if permission == "write":
            self._conn.execute(
                "UPDATE _users SET role = 'user' WHERE username = ?",
                (username,)
            )
            self._conn.commit()
            self._user_permissions[username] = self.ROLES["user"]
