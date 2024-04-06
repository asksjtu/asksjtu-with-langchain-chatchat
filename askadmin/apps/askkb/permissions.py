from typing import Any
from ninja_extra import permissions, ControllerBase
from django.http import HttpRequest


class OwnerOrSuperuser(permissions.BasePermission):
    def __init__(self, permission: str) -> None:
        self._permission = permission

    def has_permission(self, request: HttpRequest, controller: ControllerBase) -> bool:
        return super().has_permission(request, controller)

    def has_object_permission(
        self, request: HttpRequest, controller: ControllerBase, obj: Any
    ) -> bool:
        if not request.auth:
            return False

        if request.auth.is_superuser:
            return True

        owner = getattr(obj, 'owner', None)
        if owner is None:
            return False

        return owner == request.auth
