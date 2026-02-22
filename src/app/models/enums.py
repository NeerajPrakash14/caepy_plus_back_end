"""Shared Enums for the application.

Defines enum types used across models and schemas.
"""
from enum import Enum


class UserRole(str, Enum):
    """User role enum for authorization.
    
    Attributes:
        ADMIN: Full system access, can manage all resources
        OPERATIONAL: Limited admin access for operational tasks
        USER: Regular doctor/user access (default for doctors)
    """
    ADMIN = "admin"
    OPERATIONAL = "operational"
    USER = "user"

    @classmethod
    def default(cls) -> "UserRole":
        """Return the default role for new users."""
        return cls.USER
