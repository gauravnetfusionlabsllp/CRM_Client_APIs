from django.http import JsonResponse
import mysql.connector

connection = mysql.connector.connect(
    host="spectra-replica-db.cxq42qwo0p8j.eu-west-1.rds.amazonaws.com",
    user="db_readonly",
    password="67JQUZHmxbmU4tMn",
    database="crmdb"
)

cursor = connection.cursor(dictionary=True)

class DynamicUserTokenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.ALLOWED_PATHS = [
            "/users/register-user/",
            "/users/check-email/",
            "/users/extract-document/",
            "/users/get-wp-verify-link/",
            "/users/phone-send-otp/",
            "/users/verify-phone-otp/",   
            "/users/visit",   
        ]

    def __call__(self, request):

        # Allow specific paths without token
        if any(request.path.startswith(p) for p in self.ALLOWED_PATHS):
            return self.get_response(request)

        # Get token from request
        token = request.headers.get("Auth-Token")

        if not token:
            return JsonResponse(
                {"success": False, "error": "User Not Authorized!!!"},
                status=401
            )

        # Check token in DB
        query = """
            SELECT t.* FROM crmdb.auth_tokens AS t where t.auth_token = %s
        """
        params = (token,)
        cursor.execute(query, params)
        exists = cursor.fetchone()
   
        if not exists:
            return JsonResponse(
                {"success": False, "error": "Invalid or expired token"},
                status=401
            )

        # Token is valid allow request
        return self.get_response(request)