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
        response = {"status": "success", "errorcode": "", "reason": "", "result":"", "httpstatus": status.HTTP_200_OK}
        try:
            __data = request.data.get('data')
            if __data:
                print(__data)
                # query = f"""

                #         """"
                # if not response_data.get("success"):
                #     response['errorcode'] = status.HTTP_400_BAD_REQUEST
                #     response['httpstatus'] = response['errorcode']
                #     response['reason'] = str(response_data["result"])
                #     response['status'] = "error"
                #     return JsonResponse(response, status=response.get('httpstatus'))
                # else :
                #     response["result"] = response_data
            return JsonResponse(response, status=status.HTTP_200_OK, safe=False)

        except Exception as e:
            print("ERROR in FinancialTransaction:", str(e))
            
            response["status"] = "error"
            response["errorcode"] = 500
            response["reason"] = str(e)
            response["result"] = []
            response["httpstatus"] = status.HTTP_500_INTERNAL_SERVER_ERROR

            return JsonResponse(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        