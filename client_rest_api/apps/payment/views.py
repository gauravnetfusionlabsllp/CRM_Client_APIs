from datetime import datetime
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView, csrf_exempt

from apps.payment.helpers.payment_signature_creater_helpers import get_sign, verify_sign
from apps.payment.constant.cheesee_pay_key_constant import PlatformPublicKey, MerchantPrivateKey, headers, CryptoPrivateKey, CryptoPublickey
from django.core.cache import cache
import threading

from decimal import Decimal

import time
import os
import requests
import httpx
import asyncio
from asgiref.sync import async_to_sync, sync_to_async


from apps.payment.models import OrderDetails

from django.db import transaction
from django.utils.decorators import method_decorator
from rest_framework.parsers import JSONParser

from dotenv import load_dotenv

from apps.payment.helpers.payment_signature_creater_helpers import jena_pay_generate_signature
from apps.payment.helpers.match2pay_sign import generate_signature
load_dotenv()

from django.http import JsonResponse, HttpResponseBadRequest

from apps.core.serializers import PaymentRequestSerializer
from apps.payment.serializers import *
from apps.dashboard_admin.serializers import *
from apps.core.DBConnection import *
from apps.payment.services.psp_router import PSPRouter

from apps.users.helper.extractai import *
from apps.users.serializers import *
from apps.core.telegram_api import *



import mysql.connector

import uuid
import json
from django.utils import timezone
from .utils.decorators import check_user_permissions
from .services.crm_apis import CRM

from apps.users.helpers.twilio_sending_message_helpers import send_text_message, verify_otp, generate_and_send_otp


from apps.payment.constant.change_user_category_constant import check_and_update_user_category
from apps.payment.services.psp_mat2pay_methods import payment_getway
from apps.payment.constant.change_user_category_constant import *
from apps.users.helpers.twilio_sending_message_helpers import send_text_message, verify_otp



# ---------------Jena Pay--------------------------

JENA_PAY_PASSWORD = os.environ.get('JENA_PAY_PASSWORD')
JENA_PAY_MERCHANT_KEY = os.environ.get('JENA_PAY_MERCHANT_KEY')
JENA_PAY_PAYIN_URL = os.environ.get('JENA_PAY_PAYIN_URL')
JENA_PAY_PAYIN_WEBHOOK_URL = os.environ.get('JENA_PAY_PAYIN_WEBHOOK_URL')
JENA_PAY_SUCCESS_URL = os.environ.get('JENA_PAY_SUCCESS_URL')
JENA_PAY_CANCEL_URL = os.environ.get('JENA_PAY_CANCEL_URL')
JENA_PAY_EXPIRY_URL = os.environ.get('JENA_PAY_EXPIRY_URL')
JENA_PAY_ERROR_URL = os.environ.get('JENA_PAY_ERROR_URL')

# -------------------------Cheesee Pay-------------------------------

CHEEZEE_PAY_RETURN_URL = os.environ.get('CHEEZEE_PAY_RETURN_URL')
CHEEZEE_PAYIN_WEBHOOK = os.environ.get('CHEEZEE_PAYIN_WEBHOOK')



CRM_MANUAL_WITHDRAWAL_URL = os.environ.get('CRM_MANUAL_WITHDRAWAL_URL')

# -----------------------------DB Connectiosn----------------------------

connection = mysql.connector.connect(
    host= str(os.environ['CLIENT_DB_HOST']),
    user= str(os.environ['CLIENT_DB_USER']),
    password= str(os.environ['CLIENT_DB_PASSWORD']),
    database= str(os.environ['CLIENT_DB_DATABASE'])
)

CRM_PUT_USER = os.environ['CRM_PUT_USER']
CRM_AUTH_TOKEN = os.environ.get('CRM_AUTH_TOKEN')
CRM_PUT_KYC = os.environ.get('CRM_PUT_KYC')
TELEGRAM_SETTINGS = os.environ.get('TELEGRAM_SETTINGS')
teletram_ins = TelegramAPI()
# Create your views here.
# --------------------------- MATCH 2 PAY -----------------------------------
MATCH2PAY_PAYIN_URL = os.environ.get('MATCH2PAY_PAYIN_URL')
MATCH2PAY_API_SECRETE_S = os.environ.get('MATCH2PAY_API_SECRETE_S')
MATCH2PAY_API_SECRETE_M = os.environ.get('MATCH2PAY_API_SECRETE_M')
MATCH2PAY_PAY_API_TOKEN_S = os.environ.get('MATCH2PAY_PAY_API_TOKEN_S')
MATCH2PAY_PAY_API_TOKEN_M = os.environ.get('MATCH2PAY_PAY_API_TOKEN_M')
MATCH2PAY_CALLBACK_URL = os.environ.get('MATCH2PAY_CALLBACK_URL')
MATCH2PAY_FAILURE_URL = os.environ.get('MATCH2PAY_FAILURE_URL')
MATCH2PAY_SUCCESS_URL = os.environ.get('MATCH2PAY_SUCCESS_URL')

CRM_MANUAL_DEPOSIT_URL = os.environ.get('CRM_MANUAL_DEPOSIT_URL')
CRM_MANUAL_DEPOSIT_APPROVE_URL = os.environ.get('CRM_MANUAL_DEPOSIT_APPROVE_URL')
CRM_AUTH_TOKEN = os.environ.get('CRM_AUTH_TOKEN')

class Match2PayPayIn(APIView):
    def post(self, request):
        response = {"status": "success", "errorcode": "", "reason": "", "result":"", "httpstatus": status.HTTP_200_OK}
        try:
            print("request.registration_app --------", request.registration_app)
            if request.registration_app == 2:
                MATCH2PAY_API_SECRETE = MATCH2PAY_API_SECRETE_S
                MATCH2PAY_PAY_API_TOKEN = MATCH2PAY_PAY_API_TOKEN_S
            else:
                MATCH2PAY_API_SECRETE = MATCH2PAY_API_SECRETE_M
                MATCH2PAY_PAY_API_TOKEN = MATCH2PAY_PAY_API_TOKEN_M
            request_body = request.data.get('data')
            print("request_body: ", request_body)
            amount_with_fees = int(float(request_body.get('amount')))
            amount = int(float(request_body.get('amount')))
            authToken = request.headers.get('Auth-Token')
            # authToken = request_body.get('Auth-Token')
            brokerUserId = request_body.get('brokerUserId')

            print([amount, brokerUserId])
            if not all([amount, amount_with_fees, brokerUserId]):
                response['status'] = 'error'
                response['errorcode'] = status.HTTP_400_BAD_REQUEST
                response['reason'] = "Amount, Broker and brokerUserId are required fileds!!!"
                response['httpstatus'] = status.HTTP_400_BAD_REQUEST
                return Response(response, status=response.get('httpstatus'))

            query =f"""
                SELECT 
                    u.id, 
                    u.first_name, 
                    u.last_name, 
                    u.full_name, 
                    u.address, 
                    u.country_iso, 
                    u.city, 
                    u.state, 
                    u.zip, 
                    u.email, 
                    u.telephone, 
                    u.id AS user_id
                FROM crmdb.auth_tokens AS t
                JOIN crmdb.users AS u 
                    ON u.id = t.user_id
                WHERE 
                    t.auth_token = '{authToken}'
                    AND t.user_id IS NOT NULL
            """

            data = DBConnection._forFetchingJson(query, using='replica')
            data = data[0]
            trading_info_query =f"""
                                select id, external_id, user_id from crmdb.broker_user where id={brokerUserId}
                                """
            print(trading_info_query)
            trading_info_data = DBConnection._forFetchingJson(trading_info_query, using='replica')
            trading_info_data = trading_info_data[0]
            print(trading_info_data)

            payment_payload = {
                "amount":amount_with_fees,
                "customer":{
                            "firstName":str(data.get('first_name')) if data.get('first_name') else 'default',
                            "lastName":str(data.get('last_name')) if data.get('last_name') else 'default',
                            "address":{
                                "address": data.get('address') if data.get('address') else 'default',
                                "city": data.get('city') if data.get('city') else 'default',
                                "country": data.get('country_iso') if data.get('country_iso') else 'default',
                                "zipCode": data.get('zip') if data.get('zip') else 'default',
                                "state": data.get('state') if data.get('state') else 'default'
                            },
                            "contactInformation":{
                                "email":data.get('email') if data.get('email') else 'default',
                                "phoneNumber":data.get('telephone') if data.get('telephone') else 'default'
                            },
                            "locale":data.get('country_iso') if data.get('country_iso') else 'default',
                            "dateOfBirth": "04-05-2001",
                            "tradingAccountLogin": trading_info_data.get('external_id') if data.get('external_id') else 'default',
                            "tradingAccountUuid": data.get('id') if data.get('id') else 'default'

                        }
            }
            print(payment_payload)


            # request_body = request.data.get('data')
            serializer = PaymentRequestSerializer(data=payment_payload)
            print("MATCH2PAY_PAY_API_TOKEN: ", MATCH2PAY_PAY_API_TOKEN)
            print("MATCH2PAY_API_SECRETE: ", MATCH2PAY_API_SECRETE)
            if serializer.is_valid():
                # print(serializer.validated_data)
                serialized_data = serializer.validated_data
                serialized_data['apiToken'] = MATCH2PAY_PAY_API_TOKEN
                serialized_data['callbackUrl'] = MATCH2PAY_CALLBACK_URL
                serialized_data['currency'] = str(payment_getway[request_body.get('paymentGateway')].get('currency'))
                serialized_data['failureUrl'] = MATCH2PAY_FAILURE_URL
                serialized_data['paymentCurrency'] = str(payment_getway[request_body.get('paymentGateway')].get('paymentCurrency'))
                serialized_data['paymentGatewayName'] = str(request_body.get('paymentGateway'))
                serialized_data['paymentMethod'] = str(payment_getway[request_body.get('paymentGateway')].get('paymentMethod'))
                serialized_data['successUrl'] = MATCH2PAY_SUCCESS_URL
                serialized_data['timestamp'] = '1764149779000'
                serialized_data["signature"] = generate_signature(serialized_data, MATCH2PAY_API_SECRETE)
                headers = {'Content-Type': 'application/json'}
                response_data = requests.post(
                    MATCH2PAY_PAYIN_URL,
                    headers=headers,
                    data=json.dumps(serialized_data)
                )
                print("response_data========>", response_data.json())
                if response_data.json().get("status"):
                    try:
                        # data = response_data.json()
                        # store the order details in db =====================
                        if response_data.json():
                            payload = {
                                "userId": data.get('id'),
                                "full_name": data.get('full_name'),
                                "email": data.get('email'),
                                "brokerUserId": brokerUserId,
                                "transactionId": response_data.json().get("paymentId"), 
                                "amount": amount,
                                "pspName": "Match2Pay",
                                "tradingId":trading_info_data.get("external_id"),
                                "brokerBankingId":trading_info_data.get("id"),
                            }
                            
                            # send order request to antilope =====================
                            header = {
                                        "Content-Type": "application/json",
                                        "x-crm-api-token": str(CRM_AUTH_TOKEN)
                                    }
                            crm_payload = {
                                        "brokerUserId": brokerUserId,
                                        "amount": int(amount)*100,
                                        "method": "Crypto",
                                        "comment": "Deposit for Trading Account",
                                        "commentForUser": "Deposit for Trading Account",
                                        "pspId": 13 if request.registration_app == 2 else 16,
                                        "pspTransactionId": response_data.json().get("paymentId"),
                                        "status": "Pending",
                                        "normalizedAmount": int(amount)*100,
                                        "decisionTime": 0,
                                        "declineReason": "Manual",
                                        "brandExternalId": response_data.json().get("paymentId")
                                    }
                            print('crm_payload: 02', crm_payload)
                            crmRes = requests.post(str(CRM_MANUAL_DEPOSIT_URL), json=crm_payload, headers=header).json()
                            print("crmRes: 01", crmRes)
                            if crmRes['result']['success']:
                                payload['brokerBankingId'] = str(crmRes['result']['result']['id'])
                                payload['order_type'] = str("deposit")
                                print(payload)
                                serializer = OrderDetailsSerializer(data = payload)
                                if serializer.is_valid():
                                    serializer.save()
                                    print("order saved ================== 01")
                                else:
                                    print("ERROR in saving data in OrderDetailsSerializer: ", str(serializer.errors))

                                print("============== data hase been sent to the antilop =====================")
                            else:
                                response['status'] = 'error'
                                response['errorcode'] = status.HTTP_400_BAD_REQUEST
                                response['reason'] = "ERROR CRM API!!!!!!!"
                                response['httpstatus'] = status.HTTP_400_BAD_REQUEST


                    except ValueError:
                        return Response(
                            {"error": "Invalid JSON response_data from Match2Pay", "raw": response_data.text},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                
                data = response_data.json()
                data["cashierLink"] = data['checkoutUrl']
                response['result'] = data
                return JsonResponse(response, status=status.HTTP_200_OK)
            else:
                print(serializer.errors)

        except Exception as e:
            print("ERROR in Match2PayPayIn: ", str(e))
        return JsonResponse(response, status=status.HTTP_200_OK)

crm_api = CRM()

class BankTransfer(APIView):
    @check_and_update_user_category
    def post(self, request):
        response = {"status": "success", "errorcode": "", "reason": "", "result": "", "httpstatus": status.HTTP_201_CREATED}
        return Response(response, status=response.get('httpstatus'))

class WithdrawalRequest(APIView):
    @check_user_permissions
    def get(self, request):
        print("request.min_visible_amount", request.min_visible_amount)
        print("request.max_visible_amount", request.max_visible_amount)
        
        response = {"status": "success", "errorcode": "", "reason": "", "result": "", "httpstatus": status.HTTP_200_OK}
        try:
            extra_filters = {}

            # ✅ Get pagination params
            limit = int(request.query_params.get('limit', 10))
            offset = int(request.query_params.get('start', 0))
            email = request.query_params.get('email')
            psp = request.query_params.get('psp')
            firstApproval = request.query_params.get('firstApproval')
            secondApproval = request.query_params.get('secondApproval')

            if email:
                extra_filters['email'] = email
            if psp:
                extra_filters['pspName'] = psp
            if firstApproval:
                extra_filters['first_approval_action'] = firstApproval.title()
            if secondApproval:
                extra_filters['second_approval_action'] = firstApproval.title()

            print(extra_filters,"------------------")
            # ✅ extra_filters queryset
            approvals_qs = WithdrawalApprovals.objects.filter(
                amount__gte=request.min_visible_amount,
                amount__lte=request.max_visible_amount,
                otpVerified=True,
                **extra_filters
            ).exclude(pspName="manualpayment").order_by('-id')

            # ✅ Get total count before pagination
            total_records = approvals_qs.count()

            # ✅ Apply pagination
            paginated_approvals = approvals_qs[offset:offset + limit]

            # ✅ Serialize data
            serializer = WithdrawalApprovalSerializer(paginated_approvals, many=True)

            # ✅ Add results and pagination info
            response["result"] = {
                "records": serializer.data,
                "totalRecords": total_records,
                "limit": limit,
                "offset": offset
            }

            return Response(response, status=response.get('httpstatus'))

        except Exception as e:
            print("Error in WithdrawalApprovals GET:", str(e))
            response["status"] = "error"
            response["errorcode"] = status.HTTP_400_BAD_REQUEST
            response["reason"] = str(e)
            response["result"] = []
            response["httpstatus"] = status.HTTP_400_BAD_REQUEST
            return Response(response, status=response.get('httpstatus'))



    def post(self, request):
        try:
            response = {"status": "success", "errorcode": "", "reason": "", "result":"", "httpstatus": status.HTTP_200_OK}
            __data = request.data.get('data')
            withdrawalId  = request.data.get('withdrawalId')

            if not withdrawalId:
                response['status'] = "error"
                response['errorcode'] = status.HTTP_400_BAD_REQUEST
                response['reason'] = "Withdrawal Id is required!!"
            try:
                withObj = WithdrawalApprovals.objects.get(id=int(withdrawalId))
            except WithdrawalApprovals.DoesNotExist:
                response = {
                    'status': 'error',
                    'errorcode': status.HTTP_400_BAD_REQUEST,
                    'reason': "Such Transaction Doesn't Exist!!!",
                    'httpstatus': status.HTTP_400_BAD_REQUEST
                }
                return Response(response, status=response['httpstatus'])
            
            if not withObj.otpVerified:
                response['status'] = 'error'
                response['errorcode'] = status.HTTP_400_BAD_REQUEST
                response['reason'] = "Withdrawal Request is not Verified !!"
                response['httpstatus'] = status.HTTP_400_BAD_REQUEST
                return Response(response, status=response.get('httpstatus'))

            user_id = request.session_user
            # user_id = __data.get('user_id')
            __data["userId"] = user_id
            if __data:
                crmRes = crm_api.initial_withdrawal(__data)
                print("crmRes: ", crmRes)
                if not crmRes.get("success"):
                    response['errorcode'] = status.HTTP_400_BAD_REQUEST
                    response['httpstatus'] = response['errorcode']
                    response['reason'] = str(crmRes["result"])
                    response['status'] = "error"
                    return Response(response, status=response.get('httpstatus'))
                

                else :
                    order_payload = {
                        "userId" :  user_id,
                        "full_name" : __data.get('full_name', "test"),
                        "email" : __data["email"],
                        "brokerUserId" : __data["brokerUserId"],
                        "transactionId" : crmRes.get("result").get("id"),
                        "amount" : __data["amount"] if __data.get("pspName") == "cheezepay" else __data["amount"],
                        "order_type" : "withdrawal",
                        "status" : 'PENDING',
                        "tradingId" : crmRes.get("result").get("brokerUserExternalId"),
                        "brokerBankingId" : crmRes.get("result").get("id"),
                        "pspName" : __data.get('pspName'),
                        
                    }
                    order_seializer = OrderDetailsSerializer(data=order_payload)
                    if order_seializer.is_valid():
                        instance = order_seializer.save()
                        created_id = instance.id
                        __data['ordertransactionid'] = created_id
                    else:
                        print("ERROR in saving data in order_seializer withdrawal request: ", str(order_seializer.errors))
                    response['result'] = "Withdrawal request hase been sent to admin...!!"

                __data["brokerBankingId"] = crmRes.get("result").get("id")
                if __data.get("pspName") == "cheezepay":
                    __data["amount"] = __data.get("amount")
                elif __data.get("pspName") == "match2pay":
                    __data["walletAddress"] = __data.get("bankDetails").get('walletAddress')
                    __data["paymentMethod"] = __data.get("bankDetails").get('paymentGateway')
                    
                __data['full_name'] = "Test"
                serializer = WithdrawalApprovalSerializer(withObj, data=__data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                else:
                    response['status'] = 'error'
                    response['errorcode'] = status.HTTP_400_BAD_REQUEST
                    response['reason'] = str(serializer.errors)
                    response['httpstatus'] = status.HTTP_400_BAD_REQUEST
            return Response(response, status=response.get('httpstatus'))
        except Exception as e:
            response['status'] = 'error'
            response['errorcode'] = status.HTTP_400_BAD_REQUEST
            response['reason'] = str(e)
            response['httpstatus'] = status.HTTP_400_BAD_REQUEST
            return Response(response, status=response.get('httpstatus'))
    
    @check_user_permissions
    def patch(self, request, pk=None):
        try:
            response = {"status": "success", "errorcode": "", "reason": "", "result":"", "httpstatus": status.HTTP_200_OK}
            __data = request.data.get('data')
            finalInrAmount = __data.get('finalInrAmount')
            # usdAmount = __data.get('usdAmount')
            if __data:
                response_message = {}
                serializer = WithdrawalApprovalActionSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)

                event = serializer.validated_data["event"]
                data = serializer.validated_data["data"]

                action = data.get("action")        # ✅ true/false
                note = data.get("note", "")

                user_id = request.session_user

                try:
                    approval = WithdrawalApprovals.objects.get(pk=pk)
                except WithdrawalApprovals.DoesNotExist:
                    return Response({"status": "error", "reason": "Invalid ID"}, status=404)
                
                if not (request.min_visible_amount <= approval.amount <= request.max_visible_amount):
                    response['status'] = 'error'
                    response['errorcode'] = 403
                    response['reason'] = "You dont have permission to modify this transection!!!"
                    response['httpstatus'] = 403
                    return Response(response, status=response['httpstatus'])

                # ✅ Stage 1 (auto-detected)
                if approval.first_approval_by is None:
                    approval.first_approval_by = user_id
                    approval.first_approval_action = action
                    approval.first_approval_note = note
                    approval.first_approval_at = timezone.now()
                    approval.save()

                    response['errorcode'] = status.HTTP_200_OK
                    if action:
                        response['reason'] = str("Transaction approved.")
                    else:
                        crmRes = crm_api.cancel_withdrawal(approval.brokerBankingId)
                        if not crmRes.get("success"):
                            response['errorcode'] = status.HTTP_400_BAD_REQUEST
                            response['httpstatus'] = response['errorcode']
                            response['reason'] = str(crmRes["result"])
                        else :
                            order = approval.ordertransactionid
                            if order:
                                order.status = "CANCELLED"
                                order.save()
                            response_message['crm_api'] = "Withdrawal request hase been declined!!"
                        response['reason'] = str("Transaction declined.")
                        response['httpstatus'] = status.HTTP_200_OK
                    return Response(response, status=response.get("httpstatus"))


                # -------------------------------
                # ✅ SECOND APPROVAL
                # -------------------------------
                # ✅ Stage 2 (auto-detected)
                if approval.first_approval_by and  approval.first_approval_by == user_id:
                    response['status'] = 'error'
                    response['errorcode'] = status.HTTP_400_BAD_REQUEST
                    response['reason'] = str("You have already approved this transaction.")
                    response['httpstatus'] = status.HTTP_400_BAD_REQUEST
                    return Response(response, status=400)
                    
                if approval.second_approval_by is None:
                    approval.second_approval_by = user_id
                    approval.second_approval_action = action
                    approval.second_approval_note = note
                    approval.second_approval_at = timezone.now()
                    approval.save()

                    # ✅ If second stage NOT approved → STOP here
                    if not action:
                        crmRes = crm_api.cancel_withdrawal(approval.brokerBankingId)
                        # print("crmRes", crmRes)
                        if not crmRes.get("success"):
                            response['errorcode'] = status.HTTP_400_BAD_REQUEST
                            response['httpstatus'] = response['errorcode']
                            response['reason'] = str(crmRes["result"])
                        else :
                            order = approval.ordertransactionid
                            if order:
                                order.status = "CANCELLED"
                                order.save()
                            response_message['crm_api'] = "Withdrawal request hase been declined!!"

                        response['status'] = 'error'
                        response['errorcode'] = status.HTTP_200_OK
                        response['reason'] = str("Transaction declined.")
                        response['httpstatus'] = status.HTTP_200_OK
                        return Response(response, status=200)

                    if action:
                        try:
                            psp = PSPRouter.get_psp(approval.pspName)
                        except Exception as e:
                            response['status'] = 'error'
                            response['errorcode'] = status.HTTP_400_BAD_REQUEST
                            response['reason'] = str(e)
                            response['httpstatus'] = status.HTTP_400_BAD_REQUEST
                            return Response(response, status=400)
                        try:
                            psp_response = psp.payout(approval, finalInrAmount)
                            print("PSP Response:", psp_response)
                            if isinstance(psp_response, dict) and psp_response.get("success") is True or psp_response.get('msg') == "success":
                                response_message["psp_payout"] = "Payout Successful!"
                                print("✅ Payout Successful!")
                            elif isinstance(psp_response, dict) and psp_response.get("success") is False:
                                response_message["psp_payout"] = "Payout Failed!"
                                print("❌ Payout Failed:", psp_response.get("errorMessage"))
                            elif hasattr(psp_response, "status_code"):
                                if psp_response.status_code != 200:
                                    response_message["psp_payout"] = "Payout Failed!"
                                    print("❌ HTTP Error:", psp_response.status_code)
                                body = psp_response.json()
                                if body.get("success") is False:
                                    response_message["psp_payout"] = "Payout Failed!"

                                response_message["psp_payout"] = "Payout Successful!"
                            else:
                                # 4. Unexpected format
                                print("❌ Unexpected PSP response format:", psp_response)
                                response_message["psp_payout"] = "Unexpected response format"

                        except Exception as e:
                            print("❌ EXCEPTION during payout:", str(e))
                            response['status'] = 'error'
                            response["errorcode"] = status.HTTP_400_BAD_REQUEST
                            response['reason'] = f"Error During Payout: {str(e)}"
                            response['httpstatus'] = status.HTTP_400_BAD_REQUEST
                            return Response(response, status=response.get('httpstatus'))

                        # # crmRes = crm_api.verify_withdrawal(approval.brokerBankingId)
                        # # print("crmRes", crmRes)
                        # if not crmRes.get("success"):
                        #     response['errorcode'] = status.HTTP_400_BAD_REQUEST
                        #     response['httpstatus'] = response['errorcode']
                        #     response['reason'] = str(crmRes["result"])
                        # else :
                        #     print("------------------250")
                        #     response_message['crm_api'] = "Withdrawal request hase been Successfully Completed On CRM!!"
                        response_message["api_response"] = f"Withdrawal {pk} approved in stage 2 ✅ (FINAL)"
                        response["result"] = response_message
                    else:
                        response["result"] = f"Withdrawal {pk} declined in stage 2 ❌"

                    return Response(response, status=200)
            return Response(response, status=response.get('httpstatus'))
        except WithdrawalApprovals.DoesNotExist:
            response['status'] = 'error'
            response['errorcode'] = status.HTTP_400_BAD_REQUEST
            response['reason'] = str("Withdrawal request not found")
            response['httpstatus'] = status.HTTP_400_BAD_REQUEST
            return Response(response, status=response.get('httpstatus'))
        except Exception as e:
            response['status'] = 'error'
            response['errorcode'] = status.HTTP_400_BAD_REQUEST
            response['reason'] = str(e)
            response['httpstatus'] = status.HTTP_400_BAD_REQUEST
            return Response(response, status=response.get('httpstatus'))

class Match2PayPayOutWebHook(APIView):
    def post(self, request):
        try:
            data = json.loads(request.body.decode("utf-8"))
            print("✅ Payout Webhook Received:", json.dumps(data, indent=2))
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON")

        # -----------------------------
        # ✅ Extract important fields
        # -----------------------------
        payment_id = data.get("paymentId")                       # tempTransactionId = paymentId
        status = data.get("status")                              # DONE or PENDING
        final_amount = data.get("finalAmount")
        final_currency = data.get("finalCurrency")

        crypto_tx_info = data.get("cryptoTransactionInfo", [])
        tx_info = crypto_tx_info[0] if crypto_tx_info else {}
        txid = tx_info.get("txid")
        confirmations = tx_info.get("confirmations")

        # -----------------------------
        # ✅ Locate order record
        # -----------------------------
        try:
            order = OrderDetails.objects.get(transactionId=payment_id)
        except OrderDetails.DoesNotExist:
            print("❌ No order found for paymentId:", payment_id)
            return JsonResponse({"status": "ok"})

        # -----------------------------
        # ✅ Handle PENDING status
        # -----------------------------
        if status == "PENDING":
            print(f"⏳ Payout {txid} pending with {confirmations} confirmations.")
            # You may store pending status in DB if needed
            return JsonResponse({"status": "ok"})

        # -----------------------------
        # ✅ Handle DONE (Completed)
        # -----------------------------
        if status == "DONE":
            print(f"✅ Payout {txid} DONE. Final Amount: {final_amount} {final_currency}")

            # ✅ Update OrderDetails → SUCCESS
            serializer = OrderDetailsSerializer(order, data={"status": "SUCCESS"}, partial=True)
            if serializer.is_valid():
                try:
                    serializer.save()
                except Exception as e:
                    print("❌ Error saving order:", e)
            else:
                print("Serializer Errors:", serializer.errors)

            # -----------------------------
            # ✅ Notify CRM (Withdrawal Approve)
            # -----------------------------
            payload = {
                "brokerBankingId": int(order.brokerBankingId),
                "method": "Crypto",
                "comment": "Withdrawal Sent Successfully",
                "pspTransactionId": str(payment_id),
                "pspId": 12,
                "decisionTime": int(time.time())
            }
            print(order.brokerBankingId)
            crmRes = crm_api.verify_withdrawal(
                int(order.brokerBankingId),
                method=8,
                transactionId=str(payment_id),
                pspId=13
            )
            print("crmRes: ", crmRes)
            if not crmRes.get("success"):
                print("ERROR in verify_withdrawal Match2PayPayOutWebHook")
            else :
                print("Withdrawal request hase been Successfully Completed On CRM!!")

            return JsonResponse({"status": "ok"})
        # -----------------------------
        # ✅ Other statuses
        # -----------------------------
        print("ℹ️ Status:", status, "- no action performed")

        return JsonResponse({"status": "ok"})

        

class Match2PayPayInWebHook(APIView):
    def post(self, request):
        try:
            data = json.loads(request.body.decode('utf-8'))
            print(data)
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON")

        # Log callback
        print(f"Match2Pay callback received: {json.dumps(data, indent=2)}")

        # Key fields
        payment_id = data.get('paymentId')
        status = data.get('status')
        deposit_address = data.get('depositAddress')
        transaction_currency = data.get('transactionCurrency')
        final_amount = data.get('finalAmount')
        final_currency = data.get('finalCurrency')

        # Safely access nested transaction info
        crypto_tx_info = data.get('cryptoTransactionInfo', [])
        tx_info = crypto_tx_info[0] if crypto_tx_info else None

        if tx_info:
            txid = tx_info.get('txid')
            confirmations = tx_info.get('confirmations')
            amount = tx_info.get('amount')
            processing_fee = tx_info.get('processingFee')
            conversion_rate = tx_info.get('conversionRate')
        else:
            txid = confirmations = amount = processing_fee = conversion_rate = None

        # Business logic
        if status == "PENDING":
            print(f"Transaction {txid} is pending with {confirmations} confirmations.")
            # mark as pending in DB

        elif status == "DONE":
            print(f"Transaction {txid} confirmed. Final amount: {final_amount} {final_currency}")
            record = OrderDetails.objects.get(transactionId=payment_id)
            if record:
                status_update = {
                    "status": "SUCCESS"
                }
                serializer = OrderDetailsSerializer(record, data=status_update, partial=True)
                if serializer.is_valid():
                    try:
                        serializer.save()
                        print("Record updated successfully")
                    except Exception as save_exception:
                        print(f"Error saving record: {save_exception}")
                else:
                    print(f"Serializer validation errors: {serializer.errors}")
                payload = {
                    "brokerBankingId": record.brokerBankingId,
                    "method" : "Crypto",
                    "comment": "Deposit for Trading Account Approved",
                    "pspTransactionId" : str(payment_id),
                    "decisionTime" : int(datetime.now().timestamp() * 1000)
                }
                print(payload, "==================== 01")
                header = {
                    "Content-Type": "application/json",
                    "x-crm-api-token": str(CRM_AUTH_TOKEN)
                }

                crmRes = requests.post(str(CRM_MANUAL_DEPOSIT_APPROVE_URL), json=payload, headers=header).json()
                print(crmRes)
                if crmRes.get('success'):
                    print("order suucess on aintilope============== ")
            else:
                print("No record found with the provided payment_id: ", payment_id)
                    
            # mark deposit as confirmed

        else:
            print(f"Status {status} - no action needed yet.")

        return JsonResponse({"status": "ok"})


# ----------------------------Jena PAY-------------------------------------------
class JenaPayPayIn(APIView):
    
    def post(self, request):
        try:
            response = {"status": "success", "errorcode": "", "reason": "", "result":"", "httpstatus": status.HTTP_200_OK}

            data = request.data.get('data')
            amount = data.get('amount')
            amountWithFees = data.get('amountWithFees')
            authToken = request.headers.get('Auth-Token')
            brokerUserId = data.get('brokerUserId')

            if not all([amount, authToken, brokerUserId, amountWithFees]):
                response['status'] = 'error'
                response['errorcode'] = status.HTTP_400_BAD_REQUEST
                response['reason'] = "Amount, Broker and brokerUserId are required fileds!!!"
                response['httpstatus'] = status.HTTP_400_BAD_REQUEST
                return Response(response, status=response.get('httpstatus'))

            user_id = request.session_user
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT u.full_name, u.email, u.telephone, u.id FROM crmdb.users AS u where u.id = %s
            """

            params = (str(user_id),)
            cursor.execute(query, params)
            userData = cursor.fetchone()

            if not userData:
                response['status'] = 'error'
                response['errorcode'] = status.HTTP_401_UNAUTHORIZED
                response['reason'] = "User Deatils Not Found!"
                response['httpstatus'] = status.HTTP_401_UNAUTHORIZED
                return Response(response, status=response.get('httpstatus'))

            ordRec = OrderDetails.objects.create(
                userId = str(userData.get('id')),
                full_name = str(userData.get('full_name')),
                email = str(userData.get('email')),
                brokerUserId = str(brokerUserId),
                amount = amount,
                pspName = "JenaPay",
                order_type = "deposit"
             )

            # if userIdData:

            amountWithFees = str(amountWithFees)
            order = {
                "number": str(ordRec.orderId).replace('-',''),
                "amount": str(amountWithFees),
                "currency": "USD",
                "description": "Amount for the Trading"
            }

            signature = jena_pay_generate_signature(order, JENA_PAY_PASSWORD)
    
            payload = {
                "merchant_key": JENA_PAY_MERCHANT_KEY,
                "operation": "purchase",
                "methods": ["card"],
                "session_expiry": 60,
                "redirect_url": JENA_PAY_PAYIN_WEBHOOK_URL,
                "success_url": JENA_PAY_SUCCESS_URL,
                "cancel_url": JENA_PAY_CANCEL_URL,
                "expiry_url": JENA_PAY_EXPIRY_URL,
                "error_url": JENA_PAY_ERROR_URL,
                "url_target": "_blank",
                "customer":{
                    "name": ordRec.full_name,
                    "email": ordRec.email
                },
                "req_token": False,
                "hash": signature,
                "order": order
            }

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            url = JENA_PAY_PAYIN_URL
            resp = requests.post(url, headers=headers, json=payload)
            
            if resp.status_code != 200:
                response['status'] = "error"
                response['errorcode'] = status.HTTP_400_BAD_REQUEST
                response['reason'] = "Jena Pay PayIN URL Failed!!"
                response['httpstatus'] = status.HTTP_400_BAD_REQUEST
                return Response(response, status=response.get('httpstatus')) 
            
            data = resp.json()
            
            if "redirect_url" in data:
                data["cashierLink"] = data.pop("redirect_url")

            header = {
                "Content-Type": "application/json",
                "x-crm-api-token": str(CRM_AUTH_TOKEN)
            }

            payload = {
                "brokerUserId": brokerUserId,
                "amount": int(float(amount))*100,
                "method": 19,
                "comment": "Deposit for Trading Account",
                "commentForUser": "Deposit for Trading Account",
                "pspId": 15,
                "pspTransactionId": order.get('number'),
                "status": "Pending",
                "normalizedAmount": int(float(amount))*100,
                "decisionTime": 0,
                "declineReason": "string",
                "brandExternalId": order.get('number')
            }

            crmRes = requests.post(str(CRM_MANUAL_DEPOSIT_URL), json=payload, headers=header).json()

            if crmRes['result']['success']:
                ordRec.brokerBankingId = str(crmRes['result']['result']['id'])
                ordRec.save()
                response['result'] = {"data":data, "crmRes": crmRes}

                return Response(response, status=response.get('httpstatus'))
            
            response['status'] = 'error'
            response['errorcode'] = status.HTTP_400_BAD_REQUEST
            response['reason'] = "Payment Failed!!!"
            response['httpstatus'] = status.HTTP_400_BAD_REQUEST
            return Response(response, response.get('httpstatus'))

        except Exception as e:
            print(f"Error in JenaPayPayIn: {str(e)}")
            response['status'] = 'error'
            response['errorcode'] = status.HTTP_400_BAD_REQUEST
            response['reason'] = str(e)
            response['httpstatus'] = status.HTTP_400_BAD_REQUEST
            return Response(response, status=response.get('httpstatus'))
        


class JenaPayPayInCallBack(APIView):
    
    def post(self, request):
        try:
            response = {"status": "success", "errorcode": "", "reason": "", "result": "", "httpstatus": status.HTTP_200_OK}
            
            data = request.data
            print(data,"-----------------------")
            order_number = data.get("order_number")
            order_amount = data.get("order_amount")
            order_currency = data.get("order_currency")
            order_description = data.get("order_description")
            order_hash = data.get("hash")
            order_status = data.get("order_status")
            order_date = data.get("date")
            order_tranactionId = data.get("id", "")
            print(order_number, order_amount, order_currency, order_description, order_hash, order_status, order_tranactionId)
            
            orderId = str(uuid.UUID(order_number))
            orderData = (
                    OrderDetails.objects
                    .get(orderId=orderId)
                )
            
            if orderData.status == "SUCCESS":
                return Response({"code": "200", "msg": "Already processed"}, status=status.HTTP_200_OK)

            if orderData.status == "PENDING" and order_status == "settled":
                print("--------------------255")
                payload = {
                    "brokerBankingId": orderData.brokerBankingId,
                    "method" : 19,
                    "comment": "Deposit for Trading Account Approved",
                    "pspTransactionId" : str(order_number),
                    "decisionTime" : int(datetime.now().timestamp() * 1000)
                }

                header = {
                    "Content-Type": "application/json",
                    "x-crm-api-token": str(CRM_AUTH_TOKEN)
                }

                crmRes = requests.post(str(CRM_MANUAL_DEPOSIT_APPROVE_URL), json=payload, headers=header).json()

                print(crmRes,"--------------------")

                if crmRes.get('success'):
                    orderData.status = "SUCCESS"
                    orderData.transactionId = str(order_tranactionId)
                    orderData.tradingId = str(crmRes['result']['brokerUserExternalId'])
                    orderData.save()
                    print("SUCCESS ---------------------------")
                    return Response({"code": "200", "msg": "success"}, status=status.HTTP_200_OK)


            return Response({"code": "200", "msg": "Invalid Request"}, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error in PayIn Webhook: {str(e)}")
            response['status'] = 'error'
            response['errorcode'] = status.HTTP_400_BAD_REQUEST
            response['reason'] = str(e)
            response['httpstatus'] = status.HTTP_400_BAD_REQUEST
            return Response(response, status=response.get('httpstatus'))
        
# ------------------------------------------------------Cheesee Pay-----------------------------------------------------

class CheezeePayUPIPayIN(APIView):

    def post(self, request):
        """Sync entrypoint (DRF-compatible), wraps async logic."""
        return async_to_sync(self._async_post)(request)

    async def _async_post(self, request):
        try:
            response = {
                "status": "success",
                "errorcode": "",
                "reason": "",
                "result": "",
                "httpstatus": status.HTTP_200_OK
            }

            data = request.data.get('data', {})
            amount = data.get('amount')
            amountWithFees = data.get('amountWithFees')
            usdAmount = data.get('usdAmount')
            authToken = request.headers.get('Auth-Token')
            brokerUserId = data.get('brokerUserId')

            if not all([amount, authToken, brokerUserId, amountWithFees]):
                response.update({
                    "status": "error",
                    "errorcode": status.HTTP_400_BAD_REQUEST,
                    "reason": "Amount, Broker, and brokerUserId are required fields!!!",
                    "httpstatus": status.HTTP_400_BAD_REQUEST
                })
                return Response(response, status=response["httpstatus"])

            user_id = request.session_user

            # Fetch user data asynchronously
            userData = await self.get_user_data(user_id)
            if not userData:
                response.update({
                    "status": "error",
                    "errorcode": status.HTTP_401_UNAUTHORIZED,
                    "reason": "User Details Not Found!",
                    "httpstatus": status.HTTP_401_UNAUTHORIZED
                })
                return Response(response, status=response["httpstatus"])

            # Create order record (use sync_to_async to avoid blocking)
            OrderDetails_create = sync_to_async(OrderDetails.objects.create)
            ordRec = await OrderDetails_create(
                userId=str(userData.get('id')),
                full_name=str(userData.get('full_name')),
                email=str(userData.get('email')),
                brokerUserId=str(brokerUserId),
                amount=amount,
                pspName="CheezeePay UPI",
                order_type="deposit"
            )

            payload = {
                "appId": os.environ['CHEEZEE_PAY_APP_ID'],
                "merchantId": os.environ['CHEEZEE_PAY_MERCHANT_ID'],
                "mchOrderNo": str(ordRec.orderId).replace("-", ''),
                "paymentMode": "P2P",
                "amount": amountWithFees,
                "name": str(ordRec.full_name),
                "timestamp": str(int(time.time() * 1000)),
                "notifyUrl": CHEEZEE_PAYIN_WEBHOOK,
                "returnUrl": CHEEZEE_PAY_RETURN_URL,
                "language": "en",
                "email": str(ordRec.email),
                "phone": str(userData.get('telephone'))
            }

            payload['sign'] = get_sign(payload, MerchantPrivateKey)
            url = os.environ['PAYIN_URL']

            # Async HTTP call
            async with httpx.AsyncClient(timeout=5) as client:
                cheezee_resp = await client.post(url, json=payload, headers=headers)

            resp = cheezee_resp.json()

            if resp.get('code') != "000000":
                response.update({
                    "status": "error",
                    "errorcode": status.HTTP_400_BAD_REQUEST,
                    "reason": "Error in Payment Check In.",
                    "httpstatus": status.HTTP_400_BAD_REQUEST
                })
                return Response(response, status=response["httpstatus"])


            crm_payload = {
                "brokerUserId": brokerUserId,
                "amount": int(usdAmount * 100),
                "method": 17,
                "comment": "Deposit for Trading Account",
                "commentForUser": "Deposit for Trading Account",
                "pspId": 11,
                "pspTransactionId": payload.get('mchOrderNo'),
                "status": "Pending",
                "normalizedAmount": int(usdAmount * 100),
                "decisionTime": 0,
                "declineReason": "Cheezee Pay",
                "brandExternalId": payload.get('mchOrderNo')
            }

            header = {
                "Content-Type": "application/json",
                "x-crm-api-token": str(CRM_AUTH_TOKEN)
            }

            async with httpx.AsyncClient(timeout=5) as client:
                crmRes = (await client.post(str(CRM_MANUAL_DEPOSIT_URL), json=crm_payload, headers=header)).json()

            if crmRes.get("result", {}).get("success"):
                ordRec.brokerBankingId = str(crmRes["result"]["result"]["id"])
                await sync_to_async(ordRec.save)()
                response["result"] = {"data": resp, "crmAPI": crmRes}
                return Response(response, status=response["httpstatus"])

            response['status'] = "error"
            response['errorcode'] = status.HTTP_400_BAD_REQUEST
            response['httpstatus'] =  status.HTTP_400_BAD_REQUEST
            response['reason'] = "Error in Procceding the request!!!"
            return Response(response, status=response["httpstatus"])

        except Exception as e:
            print(f"Error in CheezeePay Pay In: {str(e)}")
            response.update({
                "status": "error",
                "errorcode": status.HTTP_400_BAD_REQUEST,
                "reason": str(e),
                "httpstatus": status.HTTP_400_BAD_REQUEST
            })
            return Response(response, status=response["httpstatus"])


    async def get_user_data(self, user_id):
        """Fetch user data asynchronously."""
        @sync_to_async
        def fetch():
            with connection.cursor(dictionary=True) as cursor:
                query = """
                    SELECT u.full_name, u.email, u.telephone, u.id
                    FROM crmdb.users AS u WHERE u.id = %s
                """
                cursor.execute(query, (str(user_id),))
                return cursor.fetchone()

        return await fetch()



@method_decorator(csrf_exempt, name="dispatch")
class CheezeePayInCallBackWebhook(APIView):

    parser_classes = [JSONParser]

    def post(self, request):
        try:
            response = {"status": "success", "errorcode": "", "reason": "", "result": "", "httpstatus": status.HTTP_200_OK}
            param_map = request.data
            print(param_map)
            merchantId = param_map.get("merchantId")
            mchOrderNo = param_map.get("mchOrderNo")
            platOrderNo = param_map.get("platOrderNo")
            orderStatus = param_map.get("orderStatus")
            payAmount = param_map.get("payAmount")
            amountCurrency = param_map.get("amountCurrency")
            fee = param_map.get("fee")
            feeCurrency = param_map.get("feeCurrency")
            payer_upi_id = param_map.get("payerUpiId", "")
            gmt_end = param_map.get("gmtEnd")

            orderId = str(uuid.UUID(mchOrderNo))
            orderData = OrderDetails.objects.get(orderId = orderId)

            if orderData.status == "SUCCESS":
                return Response({"code": "200", "msg": "Already processed"}, status=status.HTTP_200_OK)

            if orderData.status == "PENDING" and int(orderStatus) == 1:
                payload = {
                    "brokerBankingId":  orderData.brokerBankingId,
                    "method" : 17,
                    "comment": "Deposit for Trading Account Approved",
                    "pspTransactionId" : str(mchOrderNo),
                    "decisionTime" : int(datetime.now().timestamp() * 1000)
                }

                header = {
                    "Content-Type": "application/json",
                    "x-crm-api-token": str(CRM_AUTH_TOKEN)
                }
                    
                crmRes = requests.post(str(CRM_MANUAL_DEPOSIT_APPROVE_URL), json=payload, headers=header).json()

                # os.makedirs("crm_logs", exist_ok=True)
                # filename = f"crm_logs/crm_response_{orderData.orderId}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

                # with open(filename, "w", encoding="utf-8") as f:
                #     json.dump(crmRes, f, indent=4, ensure_ascii=False)

                if crmRes.get('success'):
                    orderData.transactionId = str(platOrderNo)
                    orderData.status = "SUCCESS"
                    orderData.tradingId = str(crmRes['result']['brokerUserExternalId'])
                    orderData.save()
                    print("--------------------Successs")
                    return Response({"code": "200", "msg": "success"}, status=status.HTTP_200_OK)
            
            
            return Response({"code": "400", "status": "failed"}, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"Error in PayIn Webhook: {str(e)}")
            response['status'] = 'error'
            response['errorcode'] = status.HTTP_400_BAD_REQUEST
            response['reason'] = str(e)
            response['httpstatus'] = status.HTTP_400_BAD_REQUEST
            return Response(response, status=response.get('httpstatus'))
        



@method_decorator(csrf_exempt, name="dispatch")
class CheezeePayOutWebhook(APIView):

    parser_classes = [JSONParser]

    def post(self, request):
        try:
            response = {"status": "success", "errorcode": "", "reason": "", "result": "", "httpstatus": status.HTTP_200_OK}
            param_map = request.data
   
            merchantId = param_map.get("merchantId")
            mchOrderNo = param_map.get("mchOrderNo")
            platOrderNo = param_map.get("platOrderNo")
            orderStatus = param_map.get("orderStatus")
            payAmount = param_map.get("payAmount")
            amountCurrency = param_map.get("amountCurrency")
            fee = param_map.get("fee")
            feeCurrency = param_map.get("feeCurrency")
            payer_upi_id = param_map.get("payerUpiId", "")
            gmt_end = param_map.get("gmtEnd")


            orderId = str(uuid.UUID(mchOrderNo))
            orderData = OrderDetails.objects.get(orderId = orderId)

            if orderData.status == "SUCCESS":
                return Response({"code": "200", "msg": "Already processed"}, status=status.HTTP_200_OK)
            
            print(orderStatus,"------------------350")

            if orderData.status == "PENDING" and int(orderStatus) == 1:
                crmRes = crm_api.verify_withdrawal(
                    int(orderData.brokerBankingId),
                    method=17,
                    transactionId=str(mchOrderNo),
                    pspId=11
                )
                if crmRes.get('success'):
                    orderData.transactionId = str(platOrderNo)
                    orderData.status = "SUCCESS"
                    orderData.tradingId = str(crmRes['result']['brokerUserExternalId'])
                    orderData.save()
                    print("--------------------Successs")
                    return Response({"code": "200", "msg": "success"}, status=status.HTTP_200_OK)
            
            
            return Response({"code": "400", "status": "failed"}, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error in the Cheezee Pay Webhook Call : {str(e)}")
            response['status'] = 'error'
            response['errorcode'] = status.HTTP_400_BAD_REQUEST
            response['reason'] = str(e)
            response['httpstatus'] = status.HTTP_400_BAD_REQUEST
            return Response(response, status=response.get('httpstatus'))


class CheezeePayUPIPayOut(APIView):

    def post(self, request):
        try:
            response = {"status":"error", "errorcode": "", "reason": "", "result": "", "httpstatus": status.HTTP_200_OK}
            amount = 900
            account_infos = {
                "name": "CheezeePayTest",
                "accountNumber": "10002993920002",
                "ifscCode": "SBIN0001537",
                "accountType": "india",
                "bankName": "visa",
                "branchName": "branch"
            }
            
            payload = {
                "appId": os.environ['CHEEZEE_PAY_APP_ID'],
                "merchantId": os.environ['CHEEZEE_PAY_MERCHANT_ID'],
                "mchOrderNo": str("12345432"),
                "paymentMethod": "BANK_IN",
                "amount": str(amount),
                "name": "testing",
                # "phone": "+911234567890",
                "email": "testing@gmail.com",
                "notifyUrl": os.environ['CHEEZEE_PAYOUT_WEBHOOK'],
                "payeeAccountInfos": json.dumps([account_infos]),
                "language": "en",
                "timestamp": str(int(time.time() * 1000))
            }

            payload['sign'] = get_sign(payload, MerchantPrivateKey)

            url = os.environ['PAYOUT_URL']
            resp = requests.post(url, json=payload, headers=headers).json()
            print(resp,"---------------------------250")
            # return resp
            if resp.get("code") == "0000000":
                if verify_sign(resp, PlatformPublicKey):
                    print(resp,"-------------------------------150")
                    return Response(resp, status=response.get('httpstatus'))

            return Response(response, status=response.get('httpstatus'))
        except Exception as e:
            print(f"Error in the Sending the Withdrawal Pending Request: {str(e)}")
            response['status'] = 'error'
            response['errorcode'] = status.HTTP_400_BAD_REQUEST
            response['reason'] = str(e)
            response['httpstatus'] = status.HTTP_400_BAD_REQUEST
            return Response(response, status=response.get('httpstatus'))




class BankingDetailsRequest(APIView):
    # @check_user_permissions
    def get(self, request):
        response = {"status": "success", "errorcode": "", "reason": "", "result": "", "httpstatus": status.HTTP_200_OK}
        try:
            # ✅ Optional filtering by userid or pspName
            userid = request.session_user
            print('userid: ', userid)
            pspName = request.query_params.get('pspName', None)

            queryset = BankingDetails.objects.all().order_by('-id')

            if userid:
                queryset = queryset.filter(userid=userid)
            if pspName:
                queryset = queryset.filter(pspName=pspName)

            # ✅ Serialize all matching records
            serializer = BankingDetailsSerializer(queryset, many=True)

            response["result"] = {
                "records": serializer.data,
                "totalRecords": queryset.count()
            }

            return Response(response, status=response.get('httpstatus'))

        except Exception as e:
            response["status"] = "error"
            response["errorcode"] = status.HTTP_400_BAD_REQUEST
            response["reason"] = str(e)
            response["result"] = []
            response["httpstatus"] = status.HTTP_400_BAD_REQUEST
            return Response(response, status=response.get('httpstatus'))

    # @check_user_permissions
    def post(self, request):
        response = {"status": "success", "errorcode": "", "reason": "", "result": "", "httpstatus": status.HTTP_200_OK}
        try:
            __data = request.data.get('data', {})
            user_id = request.session_user  # assuming your session stores user id
            __data["userid"] = user_id

            # Set timestamps
            __data["created_at"] = timezone.now()
            __data["updated_at"] = timezone.now()

            # Map wallet details for crypto payments
            if __data.get("paymentMethod") == "crypto" and "bankDetails" in __data:
                __data["walletAddress"] = __data["bankDetails"].get("walletAddress")
                __data["paymentMethod"] = __data.get("paymentMethod")

            print(__data)
            serializer = BankingDetailsSerializer(data=__data)
            if serializer.is_valid():
                serializer.save()
                response["result"] = "Banking details added successfully."
            else:
                response["status"] = "error"
                response["errorcode"] = status.HTTP_400_BAD_REQUEST
                response["reason"] = str(serializer.errors)
                response["httpstatus"] = status.HTTP_400_BAD_REQUEST

            return Response(response, status=response.get('httpstatus'))

        except Exception as e:
            response["status"] = "error"
            response["errorcode"] = status.HTTP_400_BAD_REQUEST
            response["reason"] = str(e)
            response["result"] = []
            response["httpstatus"] = status.HTTP_400_BAD_REQUEST
            return Response(response, status=response.get('httpstatus'))







class ChangeRegulation(APIView):
    def post(self, request):
        try:
            response = {"status": "success", "errorcode": "","reason": "", "result": "", "httpstatus": status.HTTP_200_OK}
            __data = request.data            
            settings_data = json.loads(TELEGRAM_SETTINGS)
            ref_link = request.headers.get("Ref-Link", "")

            # print("HEADER UUID:", repr(clean_uuid))

            try:
                query = f"""
                        SELECT bu.username, bu.first_name, bu.last_name, bu.external_id  FROM crmdb.broker_user AS bu where bu.user_id ={request.session_user}
                    """
                new_user_data = DBConnection._forFetchingJson(query, using='replica')


                clean_uuid = str(uuid.UUID(ref_link))
                user_obj = ChangeReguslationLog.objects.get(uuid=clean_uuid)
                query = f"""
                        SELECT bu.username, bu.first_name, bu.last_name, bu.external_id  FROM crmdb.broker_user AS bu where bu.username ='{user_obj.old_email}'
                    """
                old_user_data = DBConnection._forFetchingJson(query, using='replica')
                
                mssg = register_client_message(old_user_data, new_user_data)
                teletram_ins.send_telegram_message(settings_data.get('convert_client_info_bot'), mssg)

                if user_obj.old_email:
                    userid =  request.session_user
                    payload = {
                                    "registrationAppId": "1",
                                    "id": userid
                                }
                    headers = {
                                    "Content-Type": "application/json",
                                    "x-crm-api-token": str(CRM_AUTH_TOKEN)
                                }
                    resp = requests.put(CRM_PUT_USER, json=payload, headers=headers).json()
                    if resp['success']:
                        response['httpstatus'] = status.HTTP_200_OK
                        response['status'] = "success"
                        response['result'] = f"{request.session_user} is shifted to the MU regulation!!"
                    else:
                        response['httpstatus'] = status.HTTP_200_OK
                        response['status'] = "success"
                        response['result'] = f"Something went wrong!!!!!"
                    
            except ChangeReguslationLog.DoesNotExist:
                print("ERROR in : ChangeReguslationLog" )

                # if link_data:
                # else:
            
            return JsonResponse(response, status=response['httpstatus'])
        except Exception as e:
            response["status"] = "error"
            response["reason"] = str(e)
            response["httpstatus"] = status.HTTP_400_BAD_REQUEST
            return JsonResponse(response, status=response['httpstatus'])
        




#     def post(self, request):
#         try:
            
#             response = {"status": "success", "errorcode": "", "reason": "", "result": "", "httpstatus": status.HTTP_200_OK}

#             data = request.data.get('data')
#             amount = float(data.get("amount"))

#             account_infos = {
#                 "name": "testing",
#                 "accountNumber": "12345678901",
#                 "ifscCode" : "SBIN00247573",
#                 "accountType": "saving",
#                 "banckName": "SBI",
#                 "branchName": "Mumbai Branch" 
#             }
#             payload = {
#                 "appId": os.environ['CHEEZEE_PAY_APP_ID'],
#                 "merchantsId": os.environ['CHEEZEE_PAY_MERCHANT_ID'],
#                 "mchOrderNo": str(uuid.uuid4()).replace('-',''),  # your order ID
#                 "paymentMethod": "BANK_IN",
#                 "amount": amount,
#                 "name": "Test",
#                 "email": "test@gmail.com",
#                 "notifyUrl": "",
#                 "payeeAccountInfos": {},
#                 "language": "en",
#                 "timestamp": str(int(time.time() * 1000))
#             }
#             payload['payeeAccountInfos'] = account_infos
#             payload['platSign'] = get_sign(payload, MerchantPrivateKey)

#             url = os.environ['PAYOUT_URL']
#             resp = requests.post(url, json=payload, headers=headers).json()

#             if resp.get("code") == "0000000":
#                 if verify_sign(resp, PlatformPublicKey):
                    
#                     return Response(resp, status=status.HTTP_200_OK)

#             response['status'] = 'error'
#             response['errorcode'] = status.HTTP_400_BAD_REQUEST
#             response['reason'] = "Withdrawal request got failed!!!"
#             response['httpstatus'] = status.HTTP_400_BAD_REQUEST
#             return Response(response, status=response.get('httpstatus'))
        
#         except Exception as e:
#             print(f"Error in the CheezeePay PayOut Order: {str(e)}")
#             response['status'] = 'error'
#             response['errorcode'] = status.HTTP_400_BAD_REQUEST
#             response['reason'] = str(e)
#             response['httpstatus'] = status.HTTP_400_BAD_REQUEST
#             return Response(response, status=response.get('httpstatus'))
        




        


# class CheezeePayCryptoPayIn(APIView):
#     def post(self, request):
#         try:
            
#             response = {"status":"success", "errorcode": "", "result":"", "reason": "", "httpstatus": status.HTTP_200_OK}

#             data = request.data.get('data')
#             amount = data.get('amount')
#             # Step 2: Prepare payload for Cheezee Pay
#             payload = {
#                 "customerMerchantsId": os.environ.get('CHEEZEE_PAY_CRYPTO_CUSTOMER_ID'),
#                 "merchantsId": os.environ.get('CHEEZEE_PAY_CRYPTO_MERCHANT_ID'),
#                 "chargeMoney": str(amount),   # amount from DB
#                 "moneyUnit": "USDT",
#                 "merchantsOrderId": str(uuid.uuid4()).replace("-",''),  # your order ID
#                 "netWork": "TRC20",
#                 "orderVersion": "v1.0",
#                 "timestamp": str(int(time.time() * 1000)),
#             }
#             payload["platSign"] = get_sign(payload, CryptoPrivateKey)

#             # Step 3: Call Cheezee Pay API (sandbox domain for testing)
#             url = "https://test2-openapi.91fafafa.com/api/business/createCollectionOrder"
#             resp = requests.post(url, json=payload, headers=headers).json()

#             print(resp)
#             # Step 4: Verify response and return to frontend
#             if resp.get("code") == "000000":
#                 print(resp)
#                 if verify_sign(resp, CryptoPublickey):

#                     response['result'] = {
#                         "data":resp
#                     }
#                     return Response(response, status=response.get('httpstatus'))

#             response['status'] = 'error'
#             response['errorcode'] = status.HTTP_400_BAD_REQUEST
#             response['reason'] = 'Error Crypto Deposit!!'
#             response['httpstatus'] = status.HTTP_400_BAD_REQUEST
#             return Response(response, status=response.get('httpstatus'))

#         except Exception as e:
#             print(f"Error in CreateCryptoPayin: {str(e)}")
#             response['status'] = 'error'
#             response['errorcode'] = status.HTTP_400_BAD_REQUEST
#             response['reason'] = str(e)
#             response['httpstatus'] = status.HTTP_400_BAD_REQUEST
#             return Response(response, status=response.get('httpstatus'))


class SendWithdrawalRequestOTP(APIView):

    def post(self, request):
        try:
            response = {"status": "success", "errorcode": "", "result": "", "reason": "", "httpstatus": status.HTTP_200_OK}

            data = request.data.get('data')
            isCall = int(data.get('isCall', 0))
            userId = request.session_user
            query = f"""SELECT u.telephone_prefix, u.telephone, u.email FROM crmdb.users AS u where u.id = {int(userId)}"""

            userData = DBConnection._forFetchingJson(query, using='replica')
            if not userData:
                response['status'] = 'error'
                response['reason'] = 'User Record Does not Exist!!!'
                response['errorcode'] = status.HTTP_400_BAD_REQUEST
                response['httpstatus'] = status.HTTP_400_BAD_REQUEST
                return Response(response, status=response.get('httpstatus'))

            userData = userData[0]
            formatNumber = str(userData.get('telephone_prefix'))+ str(userData.get('telephone'))

            print(formatNumber, "-----------------------150")
            res = send_text_message(formatNumber, isCall)

            if res:
                withdrawalObj = WithdrawalApprovals.objects.create(
                    userId = data.get('user_id'),
                    brokerUserId = data.get('brokerUserId'),
                    email = data.get('email'),
                    amount = data.get('amount'),
                    walletAddress = data.get('walletAddress'),
                    currency = data.get('currency'),
                    pspName = data.get('pspName'),
                    bankDetails = data.get('bankDetails')
                )
                withdrawalObj.save()

                response['reason'] = 'OTP Send Successfully!!!'
                response['result'] = {
                    "withdrawalId" : withdrawalObj.id
                }
                return Response(response, status=response.get('httpstatus'))
            
            else:
                email = userData.get('email')
                resEmail = generate_and_send_otp(email)
                withdrawalObj = WithdrawalApprovals.objects.create(
                    userId = data.get('user_id'),
                    brokerUserId = data.get('brokerUserId'),
                    email = data.get('email'),
                    amount = data.get('amount'),
                    walletAddress = data.get('walletAddress'),
                    currency = data.get('currency'),
                    pspName = data.get('pspName'),
                    bankDetails = data.get('bankDetails')
                )
                withdrawalObj.save()
                if resEmail:
                    response['reason'] = "OTP sent on the register Email Id!!!"
                    response['result'] = {
                        "withdrawalId" : withdrawalObj.id
                    }
                    return Response(response, status=response.get('httpstatus'))

            response['status'] = 'error'
            response['errorcode'] = status.HTTP_200_OK
            response['reason'] = "Failed to send otp, you can continue via call!!!"
            response['httpstatus'] = status.HTTP_200_OK
            return Response(response, status=response.get('httpstatus'))

        except Exception as e:
            print(f"Error in the Sending the withdrawal request OTP: {str(e)}")
            response['status'] = 'error'
            response['errorcode'] = status.HTTP_400_BAD_REQUEST
            response['reason'] = str(e)
            response['httpstatus'] = status.HTTP_400_BAD_REQUEST
            return Response(response, status=response.get('httpstatus'))
        

class VerifyWithdrawalOTP(APIView):

    def post(self, request):
        try:
            response = {"status":"success", "errorcode": "", "reason": "", "result": "", "httpstatus": status.HTTP_200_OK}

            data = request.data.get('data')
            phoneNo = data.get('phoneNo')
            otp = data.get('otp')
            withdrawalId = int(data.get('withdrawalId'))
            isCall = int(data.get('isCall', 0))
            email = data.get('email')
            


            if not all([phoneNo, otp, withdrawalId, email]):
                response['status'] = 'error'
                response['errorcode'] = status.HTTP_400_BAD_REQUEST
                response['reason'] = 'Phone No, Email, OTP, isCall and Withdrawal Id are required!!'
                response['httpstatus'] = status.HTTP_400_BAD_REQUEST
                return Response(response, status=response.get('httpstatus'))
            
            try:
                withObj = WithdrawalApprovals.objects.get(id=withdrawalId)
            except WithdrawalApprovals.DoesNotExist:
                response = {
                    'status': 'error',
                    'errorcode': status.HTTP_400_BAD_REQUEST,
                    'reason': "Such Transaction Doesn't Exist!!!",
                    'httpstatus': status.HTTP_400_BAD_REQUEST
                }
                return Response(response, status=response['httpstatus'])
            

            res = verify_otp(phoneNo, otp, isCall)
            
            if res:
                if not withObj.otpVerified:
                    withObj.otpVerified = True
                    withObj.save()
                    response['reason'] = "OTP Verified Successfully!!!!"
                    return Response(response, status=response.get('httpstatus'))
                
                response['reason'] = "Withdrawal Order Already Verified!!"
                return Response(response, status=response.get('httpstatus'))
            else: 
                saved_otp = cache.get(f"otp_{email}", 0)
                print(saved_otp, otp)
                if int(saved_otp) == int(otp):
                    if not withObj.otpVerified:
                        withObj.otpVerified = True
                        withObj.save()
                    response['reason'] = "OTP Verified Successfully!!!!"
                    return Response(response, status=response.get('httpstatus'))

            response['status'] = 'error'
            response['errorcode'] = status.HTTP_400_BAD_REQUEST
            response['reason'] = "Invalid OTP!!!!"
            response['httpstatus'] = status.HTTP_400_BAD_REQUEST
            return Response(response, status=response.get('httpstatus'))

        except Exception as e:
            print(f"Error in verifing in the Withdrawal OTP : {str(e)}")
            response['status'] = 'error'
            response['errorcode'] = status.HTTP_400_BAD_REQUEST
            response['reason'] = str(e)
            response['httpstatus'] = status.HTTP_400_BAD_REQUEST
            return Response(response, status=response.get('httpstatus'))
        

class CancelWithdrawalRequest(APIView):

    def delete(self, request):
        try:
            response = {"status":"success", "errorcode": "", "reason": "", "result": "", "httpstatus": status.HTTP_200_OK}

            transId = request.query_params.get('transId')
            
            if not transId:
                response['status'] = 'error'
                response['errorcode'] = status.HTTP_400_BAD_REQUEST
                response['reason'] = "Transaction Id is required!!!"
                response['httpstatus'] = status.HTTP_400_BAD_REQUEST
                return Response(response, status=response.get('httpstatus'))
            
            withdrawalRes = CRM()
            res = withdrawalRes.cancel_withdrawal(withdrawalID=transId)

            if not res['success']:
                response['status'] = 'error'
                response['errorcode'] = status.HTTP_400_BAD_REQUEST
                response['reason'] = "Unable to cancel pending request!!!"
                response['httpstatus'] = status.HTTP_400_BAD_REQUEST
                return Response(response, status=response.get('httpstatus'))
            

            order = OrderDetails.objects.filter(brokerBankingId=transId).first()

            if order:
                WithdrawalApprovals.objects.filter(ordertransactionid=order).delete()
                order.delete()
                response['result'] = "Withdrawal Request Cancelled Successfully!!!"
                return Response(response, status=response.get('httpstatus'))
            else:
                response['status'] = 'error'
                response['errorcode'] = status.HTTP_400_BAD_REQUEST
                response['reason'] = "Failed to cancel withdrawal request!!!"
                response['httpstatus'] = status.HTTP_400_BAD_REQUEST
                return Response(response, status=response.get('httpstatus'))

        except Exception as e:
            print(f"Error in cancelling the Withdrawal Request: {str(e)}")
            response['status'] = 'error'
            response['errorcode'] = status.HTTP_400_BAD_REQUEST
            response['reason'] = str(e)
            response['httpstatus'] = status.HTTP_400_BAD_REQUEST
            return Response(response, status=response.get('httpstatus'))
