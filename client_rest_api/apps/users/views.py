from django.shortcuts import render
from apps.core.DBConnection import *
from apps.core.serializers import *
from rest_framework.views import APIView
from rest_framework.status import *
from rest_framework.response import Response
from django.http import JsonResponse
from rest_framework import status
from apps.core.WhatsAppLink import create_whatsapp_link
from django.core.cache import cache


from apps.users.helpers.twilio_sending_message_helpers import send_text_message

# Create your views here.


class CheckUserPhoneNumber(APIView):

    def get(self, request):
        try:
            response = {"status": "success", "errorcode": "", "reason":"", "result": "", "httpstatus": status.HTTP_200_OK}

            phoneNo = request.query_params.get('ph')
            print(phoneNo,"------------------test")

            if not phoneNo:
                response['status'] = 'error'
                response['errorcode'] = status.HTTP_400_BAD_REQUEST
                response['reason'] =  "Phone Number is Required!!!"
                response['httpstatus'] = status.HTTP_400_BAD_REQUEST
                return Response(response, status=response.get('httpstatus'))

            res = send_text_message(phoneNo)

            if not res:
                response['status'] = 'error'
                response['errorcode'] = status.HTTP_400_BAD_REQUEST
                response['reason'] = "OTP not sent!!!"
                response['httpstatus'] = status.HTTP_400_BAD_REQUEST
                return Response(response, status=response.get('httpstatus'))
            
            response['result'] = f"OTP Send Successfully on {phoneNo}"
            return Response(response, status=response.get('httpstatus'))

        except Exception as e:
            print(f"Error in the Validation User Phone Number: {str(e)}")
            response['status'] = 'error'
            response['errorcode'] = status.HTTP_400_BAD_REQUEST
            response['reason'] = str(e)
            response['httpstatus'] = status.HTTP_400_BAD_REQUEST
            return Response(response, status=response.get('httpstatus'))
        

class VerifyUserPhoneNumber(APIView):

    def post(self, request):
        try:
            response = {"status": "success", "errorcode": "", "reason": "", "result": "", "httpstatus": status.HTTP_400_BAD_REQUEST}

            data = request.data.get('data')
            phoneNo = data.get('phoneNo')
            otp = data.get('otp')
            

            saved_otp = cache.get(f"otp_{phoneNo}")
            if saved_otp == otp:
                response['result'] = {
                    "msg": "OTP verified successfully"
                }

                return Response(response, status=response.get('httpstatus'))

            response['status'] = 'error'
            response['errorcode'] = status.HTTP_400_BAD_REQUEST
            response['reason'] = "Invalid OTP!!!!"
            response['httpstatus'] = status.HTTP_400_BAD_REQUEST
            return Response(response, status=response.get('httpstatus'))

        except Exception as e:
            print(f"Error in Verifing the Phone OTP: {str(e)}")
            response['status'] = 'error'
            response['errorcode'] = status.HTTP_400_BAD_REQUEST
            response['reason'] = str(e)
            response['httpstatus'] = status.HTTP_400_BAD_REQUEST
            return Response(response, status=response.get('httpstatus'))



class CheckEmail(APIView):

    def post(self, request):
        try:
            response = {"status": "success", "errorcode": "","reason": "", "result": "", "httpstatus": HTTP_200_OK}
            __data = request.data            
            
            # CHECKING IF THE REQUEST MESSAGE IS VALID OR NOT            
            postserializer = PostDataSerializer(data=__data)
            if not postserializer.is_valid():
                response["status"] = "error"
                response["reason"] = str(postserializer.errors)
                response["httpstatus"] = HTTP_400_BAD_REQUEST
            else:
                query = f"SELECT * FROM users where email ='{__data.get('data').get('email')}';"
                data = DBConnection._forFetchingJson(query, using='replica')
                if data:
                    response['httpstatus'] = HTTP_200_OK
                    response['status'] = "success"
                    response['result'] = "Email already exists!!!!!"
                else:
                    response['httpstatus'] = HTTP_200_OK
                    response['status'] = "success"
            
            return JsonResponse(response, status=response['httpstatus'])
        except Exception as e:
            response["status"] = "error"
            response["reason"] = str(e)
            response["httpstatus"] = HTTP_400_BAD_REQUEST
            return JsonResponse(response, status=response['httpstatus'])

class GenerateWPLink(APIView):
    def post(self, request):
        try:
            response = {"status": "success", "errorcode": "","reason": "", "result": "", "httpstatus": HTTP_200_OK}
            __data = request.data            
            
            # CHECKING IF THE REQUEST MESSAGE IS VALID OR NOT            
            postserializer = PostDataSerializer(data=__data)
            if not postserializer.is_valid():
                response["status"] = "error"
                response["reason"] = str(postserializer.errors)
                response["httpstatus"] = HTTP_400_BAD_REQUEST
            else:
                link_data = create_whatsapp_link(f"{__data.get('data').get('mobilenumber')}", "I'm interested in your car for sale")
                if link_data:
                    response['httpstatus'] = HTTP_200_OK
                    response['status'] = "success"
                    response['result'] = f"{link_data}"
                else:
                    response['httpstatus'] = HTTP_200_OK
                    response['status'] = "success"
                    response['result'] = f"Something went wrong!!!!!"
            
            return JsonResponse(response, status=response['httpstatus'])
        except Exception as e:
            response["status"] = "error"
            response["reason"] = str(e)
            response["httpstatus"] = HTTP_400_BAD_REQUEST
            return JsonResponse(response, status=response['httpstatus'])