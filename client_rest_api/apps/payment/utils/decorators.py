from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from ..models import Userpermissions


def check_user_permissions(view_func):
    @wraps(view_func)
    def _wrapped_view(self, request, *args, **kwargs):
        user = request.session_user
        
        if not user:
            return Response({"success": False, "error": "User not allowed! No valid user found."},status=403)

        permission = Userpermissions.objects.filter(userid=user).first()

        if not permission:
            return Response(
                {"success": False, "error": "User not allowed! Permission missing."},
                status=status.HTTP_403_FORBIDDEN
            )

        request.min_visible_amount = permission.min_visible_amount
        request.max_visible_amount = permission.max_visible_amount

        return view_func(self, request, *args, **kwargs)

    return _wrapped_view
