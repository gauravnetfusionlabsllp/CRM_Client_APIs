from functools import wraps
from apps.core.DBConnection import *
import requests
from rest_framework.response import Response

import os

from dotenv import load_dotenv
load_dotenv()

CLIENT_USER_URL = os.environ['CLIENT_USER_URL']
X_CRM_API_TOKEN = os.environ['X_CRM_API_TOKEN']


def check_and_update_user_category(view_func):
    @wraps(view_func)
    def wrapped_view(self, request, *args, **kwargs):
        userSelectedRegistrationAppId = request.headers.get('userSelectedRegistrationAppId')

        if not userSelectedRegistrationAppId:
            return Response({"status": "error", "reason": "User Selected Registration App Id is Missing!!!"})

        if int(userSelectedRegistrationAppId) == 2:
            userToken = request.headers.get('Auth-Token')
            print(userToken,"-----------------")
            header = {
                "Content-Type": "application/json",
                "x-crm-api-token": userToken
            }
            payload = {
                "userSelectedRegistrationAppId" : 1
            }
            resp = requests.put(CLIENT_USER_URL, json=payload, headers=header).json()
            print(resp)
            if resp['result']['success']:
                userid =  request.session_user
                request_payload = {
                                "userId": userid,
                                "kycRep": 0,
                                "kycStatus": 0,
                                "fnsStatus": 0,
                                "kycNote": "KYC failed - Change Regulations",
                                "kycWorkflowStatus": 0,
                                "pepSanctions": 0,
                                "originOfFunds": 0,
                                "operatorId": 0,
                                "kycIdVerificationStatus": 0,
                                "kycPorVerificationStatus": 0,
                                "kycAccountStatus": 0,
                                "kycApprovalStatus": 0,
                                "kycIdFrontVerificationStatus": 0,
                                "kycIdBackVerificationStatus": 0,
                                "kycIdPassportVerificationStatus": 0,
                                "kycIdVisaVerificationStatus": 0,
                                "pendingInvestigation": False,
                                "taskRaised": False,
                                "kycScore": 0,
                                "kycLevel": 0,
                                "isIbAgreementSigned": False,
                                "userAgreementStatus": "Declined",
                                "userAgreementSentDate": 0,
                                "userAgreementLastReminderDate": 0,
                                "userAgreementSignedDate": 0
                                }

                resp = requests.put(CLIENT_USER_URL, json=request_payload, headers=header).json()
                return Response({"success": False, "error": "User shifted to the SLC to MU.."} ,status=201)
            else:
                return Response({"status": "error", "reason": "User Category is not Updated yet!!"})

    
        return view_func(self, request, *args, **kwargs)
         
    
    return wrapped_view
