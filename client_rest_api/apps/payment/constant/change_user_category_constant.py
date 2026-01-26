from functools import wraps
from apps.core.DBConnection import *
import requests
from rest_framework.response import Response

from apps.core.DBConnection import *
from apps.core.telegram_api import *
from apps.users.models import RegistrationLog
from apps.users.serializers import RegistrationLogSerializer, ChangeReguslationLogSerializer
import os
import json
import uuid
from dotenv import load_dotenv
load_dotenv()

CLIENT_USER_URL = os.environ['CLIENT_USER_URL']
X_CRM_API_TOKEN = os.environ['X_CRM_API_TOKEN']

CRM_PUT_USER = os.environ['CRM_PUT_USER']
CRM_AUTH_TOKEN = os.environ.get('CRM_AUTH_TOKEN')
CRM_PUT_KYC = os.environ.get('CRM_PUT_KYC')


TELEGRAM_SETTINGS = os.environ.get('TELEGRAM_SETTINGS')

teletram_ins = TelegramAPI()

def create_client_message(data):
    # assume all records belong to same client
    first = data[0]

    name = f"{first['first_name']} {first['last_name']}"
    email = first['username']
    trading_ids = ", ".join([d['external_id'] for d in data])

    msg = (
        f"*Client Name:* {name}\n"
        f"*Email:* {email}\n\n"
        f"*Trading IDs:* {trading_ids}\n\n"
        "This client wants to switch their account from *Saint Lucia* regulation to *Mauritius* regulation."
    )
    return msg


def error_response(phoneNo, email, msg):
    msg = (
        f"*Phone No:* {phoneNo}\n"
        f"*Email:* {email}\n"
        f"*ERROR:* {msg}!!!!\n"
    )
    return msg


def register_client_message(old_data, new_data):
    # assume all records belong to same client
    first = old_data[0]

    name = f"{first['first_name']} {first['last_name']}"
    email = first['username']
    trading_ids = ", ".join([d['external_id'] for d in old_data])

    new_first = new_data[0]

    new_name = f"{new_first['first_name']} {new_first['last_name']}"
    new_email = new_first['username']
    new_trading_ids = ", ".join([d['external_id'] for d in new_data])


    msg = (
        f"*Old Account Details:* \n"
        f"*Client Name:* {name}\n"
        f"*Email:* {email}\n\n"
        f"*Trading IDs:* {trading_ids}\n\n"
        f"*New Account Details:* \n"
        f"*Client Name:* {new_name}\n"
        f"*Email:* {new_email}\n\n"
        f"*Trading IDs:* {new_trading_ids}\n\n"
        "This client has been switch their account from *Saint Lucia* regulation to *Mauritius* regulation."
    )
    return msg



def change_group_message(prev_user, new_user, prev_id, new_id):
    """
    Generate a message for when a client's MT5 group is changed.
    
    prev_user: object returned by manager.UserGet(prev_id)
    new_user: object returned by manager.UserGet(new_id)
    """
    old_name = f"{prev_user.FirstName} {prev_user.LastName}"
    old_group = prev_user.Group

    new_name = f"{new_user.FirstName} {new_user.LastName}"
    new_group = new_user.Group

    msg = (
        f"*Account Group Change Notification:*\n\n"
        f"*Client Name:* {old_name}\n"
        f"*Previous Group:* {old_group}\n\n"
        f"*Previous id:* {prev_id}\n\n"
        f"*New Account Details:*\n"
        f"*Client Name:* {new_name}\n"
        f"*New Group:* {new_group}\n\n"
        f"*New id:* {new_id}\n\n"
        "This client has had their account group updated successfully."
    )
    return msg


def check_and_update_user_category(view_func):
    @wraps(view_func)
    def wrapped_view(self, request, *args, **kwargs):
        try:
            response = {"status": "success", "errorcode": "", "reason":"", "result": ""}
            data = json.loads(TELEGRAM_SETTINGS)
            print("===============",data)
                        # SELECT bu.username, bu.first_name, bu.last_name, bu.external_id  FROM crmdb.broker_user AS bu where bu.user_id ={request.session_user} and bu.broker_id=1001

            # fetching user info================
            query = f"""
                        SELECT bu.username, bu.first_name, bu.last_name, bu.external_id  FROM crmdb.broker_user AS bu where bu.user_id ={request.session_user}
                    """
            user_data = DBConnection._forFetchingJson(query, using='replica')
            new_uuid = uuid.uuid4()
            reqdata = {
                    "old_email": user_data[0].get("username", ""),
                    "uuid": str(new_uuid),
                }
            print(reqdata)
            serializer = ChangeReguslationLogSerializer(data=reqdata)
            if serializer.is_valid():
                serializer.save()
                print(serializer.validated_data, '------- 01')
                mssg = create_client_message(user_data)
                teletram_ins.send_telegram_message(data.get('convert_client_info_bot'), mssg)
                print(mssg)
            if not serializer.is_valid():
                print("ERRORS:", serializer.errors)
        except Exception as e:
            print("ERROR in check_and_update_user_category: ", str(e))
        
        print("=================== 01")
        response["result"] = {
            "uuid":new_uuid,
            "old_email":user_data[0].get('username','')
        }
        return Response(response, status=200)
            
        return view_func(self, request, *args, **kwargs)
         
    
    return wrapped_view

# def check_and_update_user_category(view_func):
#     @wraps(view_func)
#     def wrapped_view(self, request, *args, **kwargs):
#         userSelectedRegistrationAppId = request.headers.get('userSelectedRegistrationAppId')

#         if not userSelectedRegistrationAppId:
#             return Response({"status": "error", "reason": "User Selected Registration App Id is Missing!!!"})

#         if int(userSelectedRegistrationAppId) == 2:
#             userToken = request.headers.get('Auth-Token')
#             headers = {
#                 "Content-Type": "application/json",
#                 "x-crm-api-token": str(CRM_AUTH_TOKEN)
#             }
#             userid =  request.session_user
#             payload = {
#                 "registrationAppId": "1",
#                 "id": userid
#             }
#             resp = requests.put(CRM_PUT_USER, json=payload, headers=headers).json()
#             if resp['success']:
#                 request_payload = {
#                     "userId": userid,
#                     "kycRep": 0,
#                     "kycStatus": 0,
#                     "fnsStatus": 0,
#                     "kycNote": "KYC failed - Change Regulations",
#                     "kycWorkflowStatus": 0,
#                     "pepSanctions": 0,
#                     "originOfFunds": 0,
#                     "operatorId": 0,
#                     "kycIdVerificationStatus": 0,
#                     "kycPorVerificationStatus": 0,
#                     "kycAccountStatus": 0,
#                     "kycApprovalStatus": 0,
#                     "kycIdFrontVerificationStatus": 0,
#                     "kycIdBackVerificationStatus": 0,
#                     "kycIdPassportVerificationStatus": 0,
#                     "kycIdVisaVerificationStatus": 0,
#                     "pendingInvestigation": True,
#                     "taskRaised": True,
#                     "kycScore": 0,
#                     "kycLevel": 0,
#                     "isIbAgreementSigned": True,
#                     "userAgreementStatus": "Declined",
#                     "userAgreementSentDate": 0,
#                     "userAgreementLastReminderDate": 0,
#                     "userAgreementSignedDate": 0
#                     }
#                 # resp = requests.put(CLIENT_USER_URL, json=request_payload, headers=header).json()
#                 resp = requests.put(CRM_PUT_KYC, json=request_payload, headers=headers).json()
#                 return Response({"success": False, "error": "User shifted to the SLC to MU.."} ,status=201)
#             else:
#                 return Response({"status": "error", "reason": "User Category is not Updated yet!!"})

    
#         return view_func(self, request, *args, **kwargs)
         
    
#     return wrapped_view
