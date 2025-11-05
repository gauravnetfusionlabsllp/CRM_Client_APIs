from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView, csrf_exempt

from apps.payment.helpers.payment_signature_creater_helpers import get_sign, verify_sign
from apps.payment.constant.cheesee_pay_key_constant import PlatformPublicKey, MerchantPrivateKey, headers, CryptoPrivateKey, CryptoPublickey

import time
import os
import requests

from django.db import transaction
from django.utils.decorators import method_decorator
from rest_framework.parsers import JSONParser

from dotenv import load_dotenv

from apps.payment.helpers.payment_signature_creater_helpers import jena_pay_generate_signature
from apps.payment.helpers.match2pay_sign import generate_signature
load_dotenv()

from django.http import JsonResponse, HttpResponseBadRequest

from apps.core.serializers import PaymentRequestSerializer
import uuid
import json


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


# Create your views here.
# --------------------------- MATCH 2 PAY -----------------------------------
MATCH2PAY_PAYIN_URL = os.environ.get('MATCH2PAY_PAYIN_URL')
MATCH2PAY_API_SECRETE = os.environ.get('MATCH2PAY_API_SECRETE')
MATCH2PAY_PAY_API_TOKEN = os.environ.get('MATCH2PAY_PAY_API_TOKEN')
MATCH2PAY_CALLBACK_URL = os.environ.get('MATCH2PAY_CALLBACK_URL')
MATCH2PAY_FAILURE_URL = os.environ.get('MATCH2PAY_FAILURE_URL')
MATCH2PAY_SUCCESS_URL = os.environ.get('MATCH2PAY_SUCCESS_URL')

class Match2PayPayIn(APIView):
    def post(self, request):
        response = {"status": "success", "errorcode": "", "reason": "", "result":"", "httpstatus": status.HTTP_200_OK}
        try:
            request_body = request.data.get('data')
            serializer = PaymentRequestSerializer(data=request_body)
            if serializer.is_valid():
                # print(serializer.validated_data)
                serialized_data = serializer.validated_data
                serialized_data['apiToken'] = MATCH2PAY_PAY_API_TOKEN
                serialized_data['callbackUrl'] = MATCH2PAY_CALLBACK_URL
                serialized_data['currency'] = 'USD'
                serialized_data['failureUrl'] = MATCH2PAY_FAILURE_URL
                serialized_data['paymentCurrency'] = "USX"
                serialized_data['paymentGatewayName'] = "USDT TRC20"
                serialized_data['paymentMethod'] = "CRYPTO_AGENT"
                serialized_data['successUrl'] = MATCH2PAY_SUCCESS_URL
                serialized_data['timestamp'] = '1764149779000'
                serialized_data["signature"] = generate_signature(serialized_data, MATCH2PAY_API_SECRETE)
                headers = {'Content-Type': 'application/json'}
                response_data = requests.post(
                    MATCH2PAY_PAYIN_URL,
                    headers=headers,
                    data=json.dumps(serialized_data)
                )
                try:
                    data = response_data.json()
                except ValueError:
                    return Response(
                        {"error": "Invalid JSON response_data from Match2Pay", "raw": response_data.text},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                response['result'] = data
                return JsonResponse(response, status=status.HTTP_200_OK)
            else:
                print(serializer.errors)

        except Exception as e:
            print("ERROR in Match2PayPayIn: ", str(e))
        return JsonResponse(response, status=status.HTTP_200_OK)


class Match2PayPayInWebHook(APIView):
    def post(self, request):
        try:
            data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON")

        # Log or handle data
        print(f"Match2Pay callback received: {json.dumps(data, indent=2)}")

        # Example: extract key fields
        payment_id = data.get('paymentId')
        status = data.get('status')
        deposit_address = data.get('depositAddress')
        transaction_currency = data.get('transactionCurrency')
        final_amount = data.get('finalAmount')
        final_currency = data.get('finalCurrency')

        # Access the nested transaction info
        tx_info = data.get('cryptoTransactionInfo', [{}])[0]
        txid = tx_info.get('txid')
        confirmations = tx_info.get('confirmations')
        amount = tx_info.get('amount')
        processing_fee = tx_info.get('processingFee')
        conversion_rate = tx_info.get('conversionRate')

        # Example business logic
        if status == "PENDING":
            print(f"Transaction {txid} is pending with {confirmations} confirmations.")
            # You might mark it as pending in your database here

        elif status == "DONE":
            print(f"Transaction {txid} confirmed. Final amount: {final_amount} {final_currency}")
            # Update your database or mark deposit as confirmed

        else:
            print(f"Unknown status: {status}")

        # Always respond with HTTP 200 to acknowledge receipt
        return JsonResponse({"status": "ok"})

# ----------------------------Jena PAY-------------------------------------------
class JenaPayPayIn(APIView):

    def post(self, request):
        try:
            response = {"status": "success", "errorcode": "", "reason": "", "result":"", "httpstatus": status.HTTP_200_OK}

            data = request.data.get('data')
            amount = data.get('amount')
            userToken = data.get('userToken')
            userId = data.get('userId')

            

            amount = str(amount) + '.00'
            order = {
                "number": str(uuid.uuid4()).replace('-',''),
                "amount": str(amount),
                "currency": "USD",
                "description": "Amount for the Trading"
            }

            signature = jena_pay_generate_signature(order, JENA_PAY_PASSWORD)
    
            payload = {
                "merchant_key": JENA_PAY_MERCHANT_KEY,
                "operation": "purchase",
                "methods": ["card"],
                "session_expiry": 60,
                # "redirect_url": JENA_PAY_PAYIN_WEBHOOK_URL,
                "success_url": JENA_PAY_SUCCESS_URL,
                "cancel_url": JENA_PAY_CANCEL_URL,
                "expiry_url": JENA_PAY_EXPIRY_URL,
                "error_url": JENA_PAY_ERROR_URL,
                "url_target": "_blank",
                "customer":{
                    "name": str('Testing'),
                    "email": str('test1@gmail.com')
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

        
            response['result'] = {"data":data}
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error in JenaPayPayIn: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        


class JenaPayPayInCallBack(APIView):
    
    def post(self, request):
        try:
            response = {"status": "success", "errorcode": "", "reason": "", "result": "", "httpstatus": status.HTTP_200_OK}
            
            data = request.data
            order_number = data.get("order_number")[0]
            order_amount = data.get("order_amount")[0]
            order_currency = data.get("order_currency")[0]
            order_description = data.get("order_description")[0]
            order_hash = data.get("hash")[0]
            order_status = data.get("status")[0]
            order_date = data.get("date")[0]
            order_tranactionId = data.get("arn")[0]
 
            try:
                with transaction.atomic():
                    pass

            except Exception as e:
                return Response(f"Error in Transaction: {str(e)}")

            return Response({"msg":"Success"}, status=status.HTTP_200_OK)

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
        try:
            response = {"status": "success", "errorcode": "", "reason": "", "result": "", "httpstatus": status.HTTP_200_OK}
            data = request.data.get('data')
            amount = data.get('amount')

            payload = {
                "appId": os.environ['CHEEZEE_PAY_APP_ID'],
                "merchantId": os.environ['CHEEZEE_PAY_MERCHANT_ID'],
                "mchOrderNo": str(uuid.uuid4()).replace("-", ""),
                "paymentMode": "P2P",
                "amount": amount,
                "name": "brijesh",
                "timestamp": str(int(time.time() * 1000)),
                "notifyUrl": "https://trader.sgfx.com/sign-in",
                "returnUrl": CHEEZEE_PAY_RETURN_URL,
                "language": "en",
                "email": "test@gmail.com",
                "phone": "+91986475216"
            }


            payload['sign'] = get_sign(payload, MerchantPrivateKey)

            url = os.environ['PAYIN_URL']
            resp = requests.post(url, json=payload, headers=headers).json()
            
            if resp.get('code') != "000000":
                response['status'] = "error"
                response['errorcode'] = status.HTTP_400_BAD_REQUEST
                response['reason'] = 'Error inn Payment Check In.'
                response['httpstatus'] = status.HTTP_400_BAD_REQUEST
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            
            if verify_sign(resp.copy(), PlatformPublicKey):

                response['result'] = {
                    "data": resp,
                }

                return Response(response, status=response.get('httpstatus'))
        
            response['result'] = {
                "data": resp
            }

            return Response(response, status=response.get('httpstatus'))
        
        except Exception as e:
            print(f"Error in the Currency Pay In: {str(e)}")
            response['status'] = 'error'
            response['errorcode'] = status.HTTP_400_BAD_REQUEST
            response['reason'] = str(e)
            response['httpstatus'] = status.HTTP_400_BAD_REQUEST
            return Response(response, status=response.get('httpstatus'))
        

@method_decorator(csrf_exempt, name="dispatch")
class PayInCallBackWebhook(APIView):

    parser_classes = [JSONParser]

    def post(self, request):
        try:
            response = {"status": "success", "errorcode": "", "reason": "", "result": "", "httpstatus": status.HTTP_200_OK}

            param_map = request.data

            if not verify_sign(param_map, PlatformPublicKey):
                response['status'] = "error"
                response['errorcode'] = status.HTTP_400_BAD_REQUEST
                response['reason'] = "Invalid Signature"
                response['httpstatus'] = status.HTTP_400_BAD_REQUEST
                return Response(response, status=response.get('httpstatus'))
            
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

            try:
                with transaction.atomic():
                    mchOrderNo = str(uuid.UUID(param_map.get("mchOrderNo")))
                    
                    pass

            except Exception as e:
                return Response({"code": "400", "msg": "Order Not Found"}, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({"code": "200", "status": "success"}, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"Error in PayIn Webhook: {str(e)}")
            response['status'] = 'error'
            response['errorcode'] = status.HTTP_400_BAD_REQUEST
            response['reason'] = str(e)
            response['httpstatus'] = status.HTTP_400_BAD_REQUEST
            return Response(response, status=response.get('httpstatus'))
        

class CheezeePayUPIPayOut(APIView):

    def post(self, request):
        try:
            
            response = {"status": "success", "errorcode": "", "reason": "", "result": "", "httpstatus": status.HTTP_200_OK}

            data = request.data.get('data')
            amount = float(data.get("amount"))
           
            payload = {
                "appId": os.environ['CHEEZEE_PAY_APP_ID'],
                "merchantsId": os.environ['CHEEZEE_PAY_MERCHANT_ID'],
                "mchOrderNo": str(uuid.uuid4()).replace('-',''),  # your order ID
                "paymentMethod": "P2P_UPI",
                "amount": amount,
                "name": "Test",
                "email": "test@gmail.com",
                "notifyUrl": "",
                "payeeAccountInfos": {},
                "language": "en",
                "timestamp": str(int(time.time() * 1000))
            }

            payload['platSign'] = get_sign(payload, MerchantPrivateKey)

            url = os.environ['PAYOUT_URL']
            resp = requests.post(url, json=payload, headers=headers).json()

            if resp.get("code") == "0000000":
                if verify_sign(resp, PlatformPublicKey):
                    
                    return Response(resp, status=status.HTTP_200_OK)


            return Response({"Error":resp}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            print(f"Error in the Crypto PayOut Order: {str(e)}")
            return Response({"status":"error"}, status=status.HTTP_400_BAD_REQUEST)


        


class CheezeePayCryptoPayIn(APIView):
    def post(self, request):
        try:
            
            response = {"status":"success", "errorcode": "", "result":"", "reason": "", "httpstatus": status.HTTP_200_OK}

            data = request.data.get('data')
            amount = data.get('amount')
            # Step 2: Prepare payload for Cheezee Pay
            payload = {
                "customerMerchantsId": os.environ.get('CHEEZEE_PAY_CRYPTO_CUSTOMER_ID'),
                "merchantsId": os.environ.get('CHEEZEE_PAY_CRYPTO_MERCHANT_ID'),
                "chargeMoney": str(amount),   # amount from DB
                "moneyUnit": "USDT",
                "merchantsOrderId": str(uuid.uuid4()).replace("-",''),  # your order ID
                "netWork": "TRC20",
                "orderVersion": "v1.0",
                "timestamp": str(int(time.time() * 1000)),
            }
            payload["platSign"] = get_sign(payload, CryptoPrivateKey)

            # Step 3: Call Cheezee Pay API (sandbox domain for testing)
            url = "https://test2-openapi.91fafafa.com/api/business/createCollectionOrder"
            resp = requests.post(url, json=payload, headers=headers).json()

            print(resp)
            # Step 4: Verify response and return to frontend
            if resp.get("code") == "000000":
                print(resp)
                if verify_sign(resp, CryptoPublickey):

                    response['result'] = {
                        "data":resp
                    }
                    return Response(response, status=response.get('httpstatus'))

            response['status'] = 'error'
            response['errorcode'] = status.HTTP_400_BAD_REQUEST
            response['reason'] = 'Error Crypto Deposit!!'
            response['httpstatus'] = status.HTTP_400_BAD_REQUEST
            return Response(response, status=response.get('httpstatus'))

        except Exception as e:
            print(f"Error in CreateCryptoPayin: {str(e)}")
            response['status'] = 'error'
            response['errorcode'] = status.HTTP_400_BAD_REQUEST
            response['reason'] = str(e)
            response['httpstatus'] = status.HTTP_400_BAD_REQUEST
            return Response(response, status=response.get('httpstatus'))
