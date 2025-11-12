from django.shortcuts import render

# Create your views here.
from rest_framework.views import  APIView
from apps.payment.models import *
from apps.payment.serializers import *
from django.http import JsonResponse, HttpResponseBadRequest
from rest_framework import status
from apps.payment.utils.decorators import check_user_permissions
from apps.payment.services.crm_apis import CRM
from apps.core.DBConnection import *

class FinancialTransaction(APIView):
    def get(self, request):
        response = {"status": "success", "errorcode": "", "reason": "", "result":"", "httpstatus": status.HTTP_200_OK}
        try:
            transactions = OrderDetails.objects.filter(status="SUCCESS").order_by("-created_at")
            serializer = OrderDetailsSerializer(transactions, many=True)

            response["result"] = serializer.data
            return JsonResponse(response, status=status.HTTP_200_OK, safe=False)

        except Exception as e:
            print("ERROR in FinancialTransaction:", str(e))
            
            response["status"] = "error"
            response["errorcode"] = 500
            response["reason"] = str(e)
            response["result"] = []
            response["httpstatus"] = status.HTTP_500_INTERNAL_SERVER_ERROR

            return JsonResponse(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def post(self, request):
        response = {"status": "success", "errorcode": "", "reason": "", "result": "", "httpstatus": status.HTTP_200_OK}
        try:
            __data = request.data.get('data')
            if __data:
                print(__data)
                limit = int(__data.get('limit', 10))
                offset = int(__data.get('start', 0))

                # --- Query for paginated data ---
                query = f"""
                    SELECT
                        u.first_name,
                        u.last_name,
                        bb.amount,
                        bu.external_id,
                        bb.ip,
                        bu.username,
                        bb.last_update_time,
                        bb.*
                    FROM broker_banking bb
                    LEFT JOIN users u 
                        ON u.id = bb.user_id
                    LEFT JOIN broker_user bu 
                        ON bu.id = bb.broker_user_id 
                        AND bu.user_id = u.id
                    ORDER BY bb.id DESC
                    LIMIT {limit} OFFSET {offset};
                """

                # --- Query for total count ---
                count_query = """
                    SELECT COUNT(*) AS total_records
                    FROM broker_banking bb
                    LEFT JOIN users u 
                        ON u.id = bb.user_id
                    LEFT JOIN broker_user bu 
                        ON bu.id = bb.broker_user_id 
                        AND bu.user_id = u.id;
                """

                # --- Fetch paginated data ---
                transaction_data = DBConnection._forFetchingJson(query, using='replica')

                # --- Fetch total count ---
                total_result = DBConnection._forFetchingJson(count_query, using='replica')
                total_records = total_result[0]['total_records'] if total_result else 0

                if transaction_data:
                    response["result"] = {
                        "records": transaction_data,
                        "totalRecords": total_records,
                        "limit": limit,
                        "offset": offset
                    }
                else:
                    response['errorcode'] = status.HTTP_400_BAD_REQUEST
                    response['httpstatus'] = response['errorcode']
                    response['reason'] = "DATA not found!"
                    response['status'] = "error"
                    return JsonResponse(response, status=response.get('httpstatus'))

            return JsonResponse(response, status=status.HTTP_200_OK, safe=False)

        except Exception as e:
            print("ERROR in FinancialTransaction:", str(e))
            response["status"] = "error"
            response["errorcode"] = 500
            response["reason"] = str(e)
            response["result"] = []
            response["httpstatus"] = status.HTTP_500_INTERNAL_SERVER_ERROR
            return JsonResponse(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        