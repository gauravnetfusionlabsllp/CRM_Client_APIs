import requests
import os
from rest_framework import status
from apps.payment.helpers.payment_signature_creater_helpers import get_sign, verify_sign
from apps.payment.constant.cheesee_pay_key_constant import PlatformPublicKey, MerchantPrivateKey, headers

from apps.core.DBConnection import *
import json

import logging
import logging.config
from django.conf import settings
logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger('custom_logger')

CHEEZEE_PAYOUT_WEBHOOK = os.environ['CHEEZEE_PAYOUT_WEBHOOK']
print(CHEEZEE_PAYOUT_WEBHOOK,"---------------------------WEBHOOK")

import time
from dotenv import load_dotenv
load_dotenv()

class CheezePayPSP:
    BASE_URL = "url"

    def payout(self, approval, finalInrAmount):
        print("CheezePayPSP: called")
        try:
            response = {"status": "success", "errorcode": "", "reason": "", "result": "", "httpstatus": status.HTTP_200_OK}

            data = approval
            # print(data, "------------------250")
            bankDetails = data.bankDetails

            amount = finalInrAmount

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
                FROM crmdb.users AS u where u.id={data.userId} and u.email='{data.email}'
            """
            __user_data = DBConnection._forFetchingJson(query, using='replica')
            __user_data = __user_data[0]

            print(data.ordertransactionid.orderId, "---------------Order Id")
            account_infos = {
                    "name":bankDetails.get('accountName'),
                    "accountNumber": bankDetails.get('accountNumber'),
                    "ifscCode": bankDetails.get('ifscCode'),
                    "accountType": bankDetails.get('accountType'),
                    "bankName": bankDetails.get('bankName'),
                    "branchName": bankDetails.get('branchName')
                }
            payload = {
                "appId": os.environ['CHEEZEE_PAY_APP_ID'],
                "merchantId": os.environ['CHEEZEE_PAY_MERCHANT_ID'],
                "mchOrderNo": str(data.ordertransactionid.orderId).replace("-",""),
                "paymentMethod": "P2P_BANK_IN",
                "amount": str(amount),
                "name": __user_data.get('full_name'),
                "email": __user_data.get('email'),
                "notifyUrl": CHEEZEE_PAYOUT_WEBHOOK,
                "payeeAccountInfos": json.dumps([account_infos]),
                "language": "en",
                "timestamp": str(int(time.time() * 1000))
            }
            payload['sign'] = get_sign(payload, MerchantPrivateKey)
            print(payload,"--------------------------------")
            url = os.environ['PAYOUT_URL']
            resp = requests.post(url, json=payload, headers=headers).json()
            print(resp,"---------------------------250")
            # return resp
            if resp.get("code") == "000000":
                print(resp,"-------------------------------150")
                return resp

            logger.error(f"Error in Cheezee pay withdrawal: {resp}")
            return resp
        
        except Exception as e:
            logger.error(f"Error in the CheezeePay PayOut Order: {str(e)}")
            return False
            


        
