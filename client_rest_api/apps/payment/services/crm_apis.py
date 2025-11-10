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

headers = {
    "Content-Type": "application/json",
    "x-crm-api-token": str(CRM_AUTH_TOKEN)
}

print("CRM_AUTH_TOKEN", CRM_AUTH_TOKEN)

class CRM:
    def initial_withdrawal(self, data):
        userid = data["userId"]

        getUserDataQuery = f"SELECT * FROM users where id={userid}"
        userData = DBConnection._forFetchingJson(getUserDataQuery, using='replica')
        userData = userData[0]

        usdAmount = int(data.get('usdAmount'))
        fees = float(data.get('amountWithFees')) - float(data.get('amount'))

        payload = {
            "brokerUserId": data.get("brokerUserId"),
            "amount": int(data.get("amount") * 100) if data.get('pspName') == "match2pay" else int(usdAmount * 100),
            "fee": int(fees),
            "withdrawalSubType": 1,
            "comment": "Manual bank withdrawal",
            "commentForUser": "Your withdrawal is being processed",
            "pspId": 13 if data.get('pspName') == 'match2pay' else 11,
            "status": "PendingManualApproval",
            "normalizedAmount": int(data.get("amount") * 100) if data.get('pspName') == "match2pay" else int(usdAmount) * 100,
            "decisionTime":  int(datetime.now().timestamp() * 1000),
            "caseNumber": "NA",
            "iban": "NA",
            "bankName": "NA",
            "bankSwiftCode": "NA",
            "caseOrigin": "NA",
            "withdrawalPurpose": "Personal funds withdrawal",
            "accountHolderName": userData.get("full_name"),
            "bankCountry": "NA",
            "paymentCurrency": "USD",
            "registeredEmail": userData.get("email"),
            "registeredName": userData.get("full_name"),
            "blockedFromManualApproval": False
        }
        print("Payload", payload)

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
    
    def verify_withdrawal(self, withdrawalID):
        payload = {
            "brokerBankingId": int(withdrawalID),
            "method": "Crypto",
            "comment": "Testing",
            "pspTransactionId": str(uuid.uuid4()),
            "pspId": 12,
            "decisionTime": int(time.time())
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