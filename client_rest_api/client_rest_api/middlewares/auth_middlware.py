from django.http import JsonResponse
from apps.core.DBConnection import *

class AuthTokenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.whitelist = [ '/admin', '/static', '/media', '/users','payment/cheezeepay-upi-payout-webhook/']

    def __call__(self, request):
        if any(request.path.startswith(w) for w in self.whitelist):
            return self.get_response(request)

        auth_token = request.headers.get("Auth-Token")

        if not auth_token:
            return JsonResponse({"success": False, "error": "User Not Authorized! Token missing."} ,status=401)

        query = (
            f"SELECT user_id FROM auth_tokens "
            f"WHERE auth_token = '{auth_token}' AND is_invalid = 0"
        )

        session = DBConnection._forFetchingJson(query, using='replica')

        if not session:
            return JsonResponse({"success": False, "error": "Invalid or expired token."},status=401)

        request.auth_token = auth_token
        request.session_user = session[0].get("user_id")
        # request.session_user_name = session[0].get("full_name")

        response = self.get_response(request)
        return response
