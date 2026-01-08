import requests
import os
import json
from apps.core.DBConnection import *
import time
import  uuid
from datetime import datetime

CRM_AUTH_TOKEN = os.environ.get('CRM_AUTH_TOKEN')
CRM_MANUAL_WITHDRAWAL_URL = os.environ.get('CRM_MANUAL_WITHDRAWAL_URL')
CRM_MANUAL_WITHDRAWAL_APPROVE_URL = os.environ.get("CRM_MANUAL_WITHDRAWAL_APPROVE_URL")
CRM_MANUAL_WITHDRAWAL_CANCEL_URL = os.environ.get("CRM_MANUAL_WITHDRAWAL_CANCEL_URL")
CRM_MANUAL_WITHDRAWAL_UPDATE_URL = os.environ.get("CRM_MANUAL_WITHDRAWAL_UPDATE_URL")
CRM_GET_TRANSACTIONS_URL = os.environ.get("CRM_GET_TRANSACTIONS_URL")

headers = {
    "Content-Type": "application/json",
    "x-crm-api-token": str(CRM_AUTH_TOKEN)
}

print("CRM_AUTH_TOKEN", CRM_AUTH_TOKEN)

class CRM:
    def initial_withdrawal(self, data):
        userid = data["userId"]
        print(data)

        getUserDataQuery = f"SELECT * FROM users where id={userid}"
        userData = DBConnection._forFetchingJson(getUserDataQuery, using='replica')
        userData = userData[0]

        # ✅ Only use usdAmount if present
        usdAmount = data.get("usdAmount")
        usdAmount = float(usdAmount) if usdAmount is not None else 0.0
        print(usdAmount,"-------------------150")

        # ✅ Safe amount
        amount = data.get("amount")
        amount = float(amount) if amount is not None else 0.0

        # ✅ Safe amountWithFees
        amount_with_fees = data.get("amountWithFees")
        amount_with_fees = float(amount_with_fees) if amount_with_fees is not None else amount

        # ✅ Fee calculation safe
        fees = amount_with_fees - amount

        # ✅ Amount logic depending on PSP
        if data.get("pspName") == "match2pay":
            final_amount = int(amount * 100)
        else:
            final_amount = int(amount * 100)

        payload = {
            "brokerUserId": data.get("brokerUserId"),
            "amount": final_amount,
            "method": "Crypto" if data.get('pspName') == 'match2pay' else "BonusProtectedPositionCashback",
            "fee": 0,
            "withdrawalSubType": 1,
            "comment": "Approved",
            "commentForUser": "W",
            "pspId": 13 if data.get('pspName') == 'match2pay' else 11,
            "status": "PendingManualApproval",
            "normalizedAmount": final_amount,
            "decisionTime": int(datetime.now().timestamp() * 1000),
            "caseNumber": "NA",
            "iban": "NA",
            "bankName": "NA",
            "bankSwiftCode": "NA",
            "caseOrigin": "NA",
            "withdrawalPurpose": "Personal funds withdrawal",
            "accountHolderName": userData.get("full_name", "test"),
            "bankCountry": "NA",
            "paymentCurrency": "USD",
            "registeredEmail": userData.get("email"),
            "registeredName": userData.get("full_name","test"),
            "blockedFromManualApproval": False
        }

        print("Payload--------------------", payload)

        try:
            response = requests.post(str(CRM_MANUAL_WITHDRAWAL_URL), json=payload ,headers=headers)
            if response.status_code == 200:
                print("Withdrawal request sent successfully!")
                return response.json()
            else:
                print(f"Error: {response.status_code}")
                print(response.text)
                return {'success': False }
        except Exception as e:
            print(f"Exception occurred: {e}")
            return {'success': False }
    
    def verify_withdrawal(self, withdrawalID, method, pspId):
        payload = {
            "brokerBankingId": withdrawalID,
            "method": method,
            "comment": "Approved",
            "pspId": pspId,
            "decisionTime": int(datetime.now().timestamp() * 1000)
        }
        print("Payload", payload)

        try:
            response = requests.post(str(CRM_MANUAL_WITHDRAWAL_APPROVE_URL), json=payload ,headers=headers)
            if response.status_code == 200:
                print("Withdrawal request sent successfully!")
                return response.json()
            else:
                print(f"Error: {response.status_code}")
                print(response.text)
                return {'success': False }
        except Exception as e:
            print(f"Exception occurred: {e}")
            return {'success': False }
    

    def update_crm_withdrawal(self, withdrawalID, pspTransactionId):
        payload = {
            "id": withdrawalID,
            "pspTransactionId": pspTransactionId
        }
        print("Payload", payload)

        try:
            response = requests.post(str(CRM_MANUAL_WITHDRAWAL_UPDATE_URL), json=payload ,headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                return {'success': False }
        except Exception as e:
            return {'success': False }
        
    def cancel_withdrawal(self, withdrawalID):
        payload = {
                "id": int(withdrawalID)
                }
        print("Payload", payload)
        try:
            response = requests.post(str(CRM_MANUAL_WITHDRAWAL_CANCEL_URL), json=payload ,headers=headers)
            if response.status_code == 200:
                print("Withdrawal request sent successfully!")
                return response.json()
            else:
                print(f"Error: {response.status_code}")
                print(response.text)
                return {'success': False }
        except Exception as e:
            print(f"Exception occurred: {e}")
            return {'success': False }
    
    def get_transactions(self, payload):
        try:
            print(str(CRM_GET_TRANSACTIONS_URL))
            print(payload)
            # headers['x-auth-token'] = 'c1a35cc7c389c9057f1ea6d5272155536cec413a193d54cb1e03de64ae553112'
            print(headers)
            response = requests.post(str(CRM_GET_TRANSACTIONS_URL), json=payload ,headers=headers)
            print(response)
            if response.status_code == 200:
                print(response.json())
                return response.json()
            else:
                print(f"Error: {response.status_code}")
                print(response.text)
                return {'success': False }
        except Exception as e:
            print(f"Exception occurred: {e}")
            return {'success': False }