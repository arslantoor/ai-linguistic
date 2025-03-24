from rest_framework import permissions

class IsProjectOwner(permissions.BasePermission):
    """
    Custom permission to allow only the owner to update/delete a project.
    """
    def has_object_permission(self, request, view, obj):
        return obj.created_by == request.user  # Only project owner can modify