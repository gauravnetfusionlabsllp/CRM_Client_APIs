import requests
from rest_framework import status
from apps.core.DBConnection import *
from apps.payment.helpers.match2pay_sign import generate_signature
import os, json
from dotenv import load_dotenv
MATCH2PAY_PAYIN_URL = os.environ.get('MATCH2PAY_PAYIN_URL')
MATCH2PAY_PAYOUT_URL = os.environ.get('MATCH2PAY_PAYOUT_URL')
MATCH2PAY_API_SECRETE_M = os.environ.get('MATCH2PAY_API_SECRETE_M')
MATCH2PAY_API_SECRETE_S = os.environ.get('MATCH2PAY_API_SECRETE_S')
MATCH2PAY_PAY_API_TOKEN_M = os.environ.get('MATCH2PAY_PAY_API_TOKEN_M')
MATCH2PAY_PAY_API_TOKEN_S = os.environ.get('MATCH2PAY_PAY_API_TOKEN_S')
MATCH2PAY_PAYOUT_CALLBACK_URL = os.environ.get('MATCH2PAY_PAYOUT_CALLBACK_URL')
MATCH2PAY_FAILURE_URL = os.environ.get('MATCH2PAY_FAILURE_URL')
MATCH2PAY_SUCCESS_URL = os.environ.get('MATCH2PAY_SUCCESS_URL')

CRM_MANUAL_DEPOSIT_URL = os.environ.get('CRM_MANUAL_DEPOSIT_URL')
CRM_MANUAL_DEPOSIT_APPROVE_URL = os.environ.get('CRM_MANUAL_DEPOSIT_APPROVE_URL')
CRM_AUTH_TOKEN = os.environ.get('CRM_AUTH_TOKEN')
from apps.payment.services.psp_mat2pay_methods import payment_getway

class Match2PayPSP:
    BASE_URL = "url"

    def payout(self, approval, finalInrAmount=None):
        print("Match2PayPSP: called")
        response = {"status": "success", "errorcode": "", "reason": "", "result":"", "httpstatus": status.HTTP_200_OK}
        try:
            __data = approval
            print(__data.walletAddress)
            print(__data.amount)
            print(__data.userId)
            print(__data.email)
            print(__data.paymentMethod)
            query =f"""
                SELECT
                u.id, 
                u.first_name, 
                u.last_name, 
                u.full_name, 
                u.address, 
                u.country_iso, 
                u.registration_app,
                u.city, 
                u.state, 
                u.zip, 
                u.email, 
                u.telephone, 
                u.id AS user_id
                FROM crmdb.users AS u where u.id={__data.userId} and u.email='{__data.email}'
            """
            __user_data = DBConnection._forFetchingJson(query, using='replica')
            __user_data = __user_data[0]
            if __user_data.get('registration_app') == 2:
                MATCH2PAY_PAY_API_TOKEN = MATCH2PAY_PAY_API_TOKEN_S
                MATCH2PAY_API_SECRETE = MATCH2PAY_API_SECRETE_S
            else:
                MATCH2PAY_PAY_API_TOKEN = MATCH2PAY_PAY_API_TOKEN_M
                MATCH2PAY_API_SECRETE = MATCH2PAY_API_SECRETE_M
            print("MATCH2PAY_PAY_API_TOKEN with: ", MATCH2PAY_PAY_API_TOKEN)
            print("MATCH2PAY_API_SECRETE with: ", MATCH2PAY_API_SECRETE)
            request_body = {
                "amount": int(__data.amount),
                "apiToken": MATCH2PAY_PAY_API_TOKEN,
                "callbackUrl": MATCH2PAY_PAYOUT_CALLBACK_URL,
                "currency": str(payment_getway[__data.paymentMethod].get('currency')),
                "cryptoAddress": str(__data.walletAddress),  # 🔹 Replace with actual USDT TRC20 wallet address
                "customer": {
                    "firstName":str(__user_data.get('first_name')) if __user_data.get('first_name') else 'default',
                    "lastName":str(__user_data.get('last_name')) if __user_data.get('last_name') else 'default',
                    "address":{
                        "address": __user_data.get('address') if __user_data.get('address') else 'default',
                        "city": __user_data.get('city') if __user_data.get('city') else 'default',
                        "country": __user_data.get('country_iso') if __user_data.get('country_iso') else 'default',
                        "zipCode": __user_data.get('zip') if __user_data.get('zip') else 'default',
                        "state": __user_data.get('state') if __user_data.get('state') else 'default'
                    },
                    "contactInformation": {
                        "email":__user_data.get('email') if __user_data.get('email') else 'default',
                                "phoneNumber":__user_data.get('telephone') if __user_data.get('telephone') else 'default'
                    },
                    "locale": "en_US",
                    "dateOfBirth": "1990-01-01",
                    "tradingAccountLogin": "clientId_12345",
                    "tradingAccountUuid": "clientUid_67890"
                },
                "failureUrl": MATCH2PAY_FAILURE_URL,
                "paymentCurrency": str(payment_getway[__data.paymentMethod].get('paymentCurrency')),
                "paymentGatewayName": str(__data.paymentMethod),
                "paymentMethod": str(payment_getway[__data.paymentMethod].get('paymentMethod')),
                "successUrl": MATCH2PAY_SUCCESS_URL,
                "timestamp": "1764149779000"
            }
            print("request body ===========> ", request_body)
            request_body["signature"] = generate_signature(request_body, MATCH2PAY_API_SECRETE)
            # Prepare headers
            headers = {
                "Content-Type": "application/json"
            }

            # ✅ Send POST request
            response = requests.post(
                MATCH2PAY_PAYOUT_URL,
                headers=headers,
                data=json.dumps(request_body)
            )
            data = response.json()
            payment_id = data.get("paymentId") 
            if payment_id:
                # ✅ get the related order
                order = __data.ordertransactionid  
                if order:
                    order.transactionId = payment_id
                    order.save()
                    print("✅ Saved paymentId to OrderDetails:", payment_id)
                else:
                    print("⚠ No related order found for this withdrawal.")
            else:
                print("⚠ PSP response missing paymentId:", data)


            # ✅ Print response
            print(response.status_code)
            print(response.text)
            return data
        except Exception as e:
            print(str(e))

        # payload = {
        #     "amount": approval.amount,
        #     "currency": approval.currency,
        #     "walletAddress": approval.walletAddress,
        #     "referenceId": approval.id,
        # }

        # headers = {
        #     "Authorization": "Bearer BINANCE_API_KEY"
        # }

        # r = requests.post(self.BASE_URL, json=payload, headers=headers)
        # return r.json()
