import requests
import os
from rest_framework import status
from apps.payment.helpers.payment_signature_creater_helpers import get_sign, verify_sign
from apps.payment.constant.cheesee_pay_key_constant import PlatformPublicKey, MerchantPrivateKey, headers

from apps.core.DBConnection import *

CHEEZEE_PAYOUT_WEBHOOK = os.environ['CHEEZEE_PAYOUT_WEBHOOK']

import time
from dotenv import load_dotenv
load_dotenv()

class CheezePayPSP:
    BASE_URL = "url"

    def payout(self, approval, amountWithFees):
        print("CheezePayPSP: called")
        try:
            response = {"status": "success", "errorcode": "", "reason": "", "result": "", "httpstatus": status.HTTP_200_OK}

            data = approval
            amount = amountWithFees

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

            print(data.ordertransaction.orderId, "---------------150")
            account_infos = {
                    "name": __user_data.get('full_name'),
                    "upiId": data.walletAddress
                }
            payload = {
                "appId": os.environ['CHEEZEE_PAY_APP_ID'],
                "merchantsId": os.environ['CHEEZEE_PAY_MERCHANT_ID'],
                "mchOrderNo": str(data.ordertransaction.orderId).replace("-",""),
                "paymentMethod": "P2P_UPI",
                "amount": amount,
                "name": __user_data.get('full_name'),
                "email": __user_data.get('email'),
                "notifyUrl": CHEEZEE_PAYOUT_WEBHOOK,
                "payeeAccountInfos": account_infos,
                "language": "en",
                "timestamp": str(int(time.time() * 1000))
            }
            payload['platSign'] = get_sign(payload, MerchantPrivateKey)

            url = os.environ['PAYOUT_URL']
            resp = requests.post(url, json=payload, headers=headers).json()
            print(resp,"---------------------------250")
            # return resp
            if resp.get("code") == "0000000":
                if verify_sign(resp, PlatformPublicKey):
                    print(resp,"-------------------------------150")
                    return resp
        
        except Exception as e:
            print(f"Error in the CheezeePay PayOut Order: {str(e)}")
            return False
            


        
