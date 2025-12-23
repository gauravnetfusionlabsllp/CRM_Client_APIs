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
from rest_framework.response import Response

from apps.dashboard_admin.models import PSPRateUpdate
import  os, json, requests
from dotenv import load_dotenv
load_dotenv()

CRM_PUT_USER = os.environ['CRM_PUT_USER']
CRM_AUTH_TOKEN = os.environ.get('CRM_AUTH_TOKEN')
CRM_PUT_KYC = os.environ.get('CRM_PUT_KYC')
TELEGRAM_SETTINGS = os.environ.get('TELEGRAM_SETTINGS')
settings_data = json.loads(TELEGRAM_SETTINGS)

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
                limit = int(__data.get('limit', 10))
                offset = int(__data.get('start', 0))
                email = __data.get('email')
                paymentMethod = __data.get('payMethod')
                payStatus = str(__data.get('payStatus'))
                payType = str(__data.get('payType'))
                sd = __data.get('sd')
                ed = __data.get('ed')

                extra_filters = {}

                if email:
                    extra_filters['u.email'] = str(email)
                if paymentMethod:
                    extra_filters['bb.psp_name'] = paymentMethod
                if payStatus:
                    extra_filters['bb.status'] = payStatus
                if payType:
                    extra_filters['bb.type'] = payType
                if sd and ed:
                    extra_filters['bb.last_update_time_range'] = (sd, ed)
                

                conditions = []

                for key, value in extra_filters.items():
                    if key.endswith("_range"):
                        col = key.replace("_range", "")
                        start, end = value

                        if isinstance(start, str):
                            start = f"'{start}'"
                        if isinstance(end, str):
                            end = f"'{end}'"

                        conditions.append(f"{col} BETWEEN {start} AND {end}")

                    elif key == "u.email":
                        if isinstance(value, str):
                            safe_value = value.replace("'", "''")
                            conditions.append(f"u.email LIKE '%{safe_value}%'")

                    else:
                        # existing logic
                        if isinstance(value, str):
                            value = f"'{value}'"
                        conditions.append(f"{key} = {value}")
                
                where_clause = ""
                if conditions:
                    where_clause = "WHERE " + " AND ".join(conditions)


                # --- Query for paginated data ---
                query = f"""
                    SELECT
                        u.first_name,
                        u.email,
                        u.last_name,
                        bb.amount,
                        bu.external_id,
                        bb.ip,
                        bu.username,
                        bb.last_update_time,
                        bb.type,
                        bb.status,
                        bb.*
                    FROM broker_banking bb
                    LEFT JOIN users u 
                        ON u.id = bb.user_id
                    LEFT JOIN broker_user bu 
                        ON bu.id = bb.broker_user_id 
                        AND bu.user_id = u.id
                    {where_clause}
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
                    response['errorcode'] = status.HTTP_200_OK
                    response['httpstatus'] = response['errorcode']
                    response['result'] = []
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


class UpdatePSPRate(APIView):

    def post(self, request):
        try:
            response = {"status":"success", "errorcode":"", "reason":"", "result":"", "httpstatus": status.HTTP_200_OK}

            depositRate = request.query_params.get('depositRate')
            withdrawalRate = request.query_params.get('withdrawalRate')

            if not all([depositRate, withdrawalRate]):
                response['status'] = 'error'
                response['errorcode'] = status.HTTP_400_BAD_REQUEST
                response['reason'] = "Deposit and Withdrawal Rate is required!!!"
                response["httpstatus"] = status.HTTP_400_BAD_REQUEST
                return Response(response, status=response.get('httpstatus'))
            
            user_id = request.session_user

            if not user_id:
                response['status'] = 'error'
                response['errorcode'] = status.HTTP_400_BAD_REQUEST
                response['reason'] = "User Not Found!!!"
                response['httpstatus'] = status.HTTP_400_BAD_REQUEST
                return Response(response, status=response.get('httpstatus'))
            
            query =f"""
                        SELECT u.full_name, u.email FROM crmdb.users AS u where u.id = {user_id}
                    """
            
            data = DBConnection._forFetchingJson(query, using='replica')
            if not data:
                response['status'] = 'error'
                response['errorcode'] = status.HTTP_400_BAD_REQUEST
                response['reason'] = "Unable to fetch user details from the MySQL Database!!"
                response['httpstatus'] = status.HTTP_400_BAD_REQUEST
                return Response(response, status=response.get('httpstatus'))
            
            full_name = data[0].get('full_name', "None")
            email = data[0].get('email', "None")

            rec = PSPRateUpdate.objects.first()

            if rec:
                rec.updated_by = full_name
                rec.email = email
                rec.userId = str(user_id)
                rec.depositRate = depositRate
                rec.withdrawalRate = withdrawalRate
                rec.save()
            else:
                rec = PSPRateUpdate.objects.create(
                    updated_by=full_name,
                    email=email,
                    userId=str(user_id),
                    depositRate=depositRate,
                    withdrawalRate=withdrawalRate
                )

            response['reason'] = 'Deposit and Withdrawal rate updated Successfully!!!'
            response['result'] = {
                "depositRate": rec.depositRate,
                "withdrawalRate": rec.withdrawalRate,
                "updateBy": rec.updated_by
            }
            return Response(response, status=response.get('httpstatus'))

        except Exception as e:
            print(f"Error in Updating the PSP Rate: {str(e)}")
            response['status'] = 'error'
            response['errorcode'] = status.HTTP_400_BAD_REQUEST
            response['reason'] = str(e)
            response['httpstatus'] = status.HTTP_400_BAD_REQUEST
            return Response(response, status=response.get('httpstatus'))

    def get(self, request):
        try:
            response = {"status":"success", "errorcode":"", "reason":"", "result":"", "httpstatus": status.HTTP_200_OK}

            rec = PSPRateUpdate.objects.all()

            if not rec.exists():
                response['status'] = 'error'
                response['errorcode'] = status.HTTP_400_BAD_REQUEST
                response['reason'] = "No Record Found!!!"
                response['httpstatus'] = status.HTTP_400_BAD_REQUEST
                return Response(response, status=response.get('httpstatus'))

            response['result'] = {
                "update_by": rec[0].updated_by,
                "email" : rec[0].email,
                "depositRate": rec[0].depositRate,
                "withdrawalRate": rec[0].withdrawalRate
            }
            return Response(response, status=response.get('httpstatus'))

        except Exception as e:
            response['status'] = 'error'
            response['errorcode'] = status.HTTP_400_BAD_REQUEST
            response['reason'] = str(e)
            response['httpstatus'] = status.HTTP_400_BAD_REQUEST
            return Response(response, status=response.get('httpstatus'))



class KYCApprove(APIView):
    def post(self, request):
        response = {"status": "success", "errorcode": "","reason": "", "result": "", "httpstatus": status.HTTP_200_OK}
        try:
            user_id = request.session_user
            payload = {
                    "userId": user_id,
                    "kycRep": 1,
                    "kycStatus": 4,
                    "fnsStatus": 1,
                    "kycNote": "Approved via API",
                    "kycWorkflowStatus": 1,
                    "pepSanctions": 0,
                    "originOfFunds": 1,
                    "operatorId": 123,
                    "kycIdVerificationStatus": 1,
                    "kycPorVerificationStatus": 1,
                    "kycAccountStatus": 1,
                    "kycApprovalStatus": 1,
                    "kycIdFrontVerificationStatus": 1,
                    "kycIdBackVerificationStatus": 1,
                    "kycIdPassportVerificationStatus": 1,
                    "kycIdVisaVerificationStatus": 1,
                    "pendingInvestigation": False,
                    "taskRaised": False,
                    "kycScore": 100,
                    "kycLevel": 3,
                    "isIbAgreementSigned": True,
                    "userAgreementStatus": "Signed",
                    "userAgreementSentDate": 1700000000,
                    "userAgreementLastReminderDate": 1700000000,
                    "userAgreementSignedDate": 1700000000,
                    "showKycWarning": False,
                    "showKycInfo": False,
                    "isKycApproved": False,
                    "hasKycRep": True
                    }
            headers = {
                "Content-Type": "application/json",
                "x-crm-api-token": str(CRM_AUTH_TOKEN)
            }
            resp = requests.put(CRM_PUT_KYC, json=payload, headers=headers).json()
            response["status"] = "success"
            response["message"] = "KYC Approved.."
            response["httpstatus"] = status.HTTP_200_OK
            return JsonResponse(response, status=response['httpstatus'])
        except Exception as e:
            response["status"] = "error"
            response["reason"] = str(e)
            response["httpstatus"] = status.HTTP_400_BAD_REQUEST
            return JsonResponse(response, status=response['httpstatus'])


