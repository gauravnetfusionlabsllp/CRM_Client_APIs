from django.shortcuts import render
from apps.core.DBConnection import *
from apps.core.serializers import *
from rest_framework.views import APIView
from rest_framework.status import *
from rest_framework.response import Response
from django.http import JsonResponse
from apps.core.WhatsAppLink import create_whatsapp_link
# Create your views here.



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