from django.http import JsonResponse
from apps.core.DBConnection import *
from django.utils.deprecation import MiddlewareMixin

class AuthTokenMiddleware(MiddlewareMixin):

    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.whitelist = [
            '/admin', '/static', '/media', '/users',
            '/payment/match2pay-pay-out-webhook/',
            '/payment/match2pay-pay-in-webhook/',
            '/payment/cheezeepay-upi-payout-webhook/',
            '/payment/cheezeepay-upi-payin-webhook/',
            '/payment/jenapay-payin-webhook/'
        ]

    def process_request(self, request):

        if any(request.path.startswith(w) for w in self.whitelist):
            return None

        auth_token = request.headers.get("Auth-Token")

        if not auth_token:
            return JsonResponse(
                {"success": False, "error": "User Not Authorized! Token missing."},
                status=401
            )

        query = f"""
            SELECT user_id FROM auth_tokens
            WHERE auth_token = '{auth_token}' AND is_invalid = 0
        """
        session = DBConnection._forFetchingJson(query, using='replica')

        if not session:
            return JsonResponse(
                {"success": False, "error": "Invalid or expired token."},
                status=401
            )

        request.auth_token = auth_token
        request.session_user = session[0].get("user_id")

        return None
    


class GettingUnseriInfoMiddleware(MiddlewareMixin):

    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.target_urls = ['/payment/match2pay-pay-in']

    def process_request(self, request):

        if not any(request.path.startswith(url) for url in self.target_urls):
            return None
        
        if not request.headers.get("Auth-Token"):
            return JsonResponse({"error": "Invalid or expired token."}, status=401)

        query = f"""SELECT u.registration_app, u.email  FROM crmdb.users AS u where u.id={request.session_user}"""
        user_data = DBConnection._forFetchingJson(query, using='replica')
        request.registration_app = user_data[0].get("registration_app")
        return None