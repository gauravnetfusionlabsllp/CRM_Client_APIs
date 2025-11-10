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
        data = request.data.get('data')
        userSelectedRegistrationAppId = data.get('userSelectedRegistrationAppId')

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
                return view_func(self, request, *args, **kwargs)
            else:
                return Response({"status": "error", "reason": "User Category is not Updated yet!!"})

    
        return view_func(self, request, *args, **kwargs)
         
    
    return wrapped_view
