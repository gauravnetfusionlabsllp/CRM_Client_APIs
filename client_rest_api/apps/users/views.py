from django.shortcuts import render
from apps.core.DBConnection import *
from apps.core.serializers import *
from rest_framework.views import APIView
from rest_framework.status import *
from rest_framework.response import Response
from django.http import JsonResponse
from rest_framework import status
from apps.core.WhatsAppLink import create_whatsapp_link
import tempfile
import os
from apps.users.helper.extractai import *
from apps.users.serializers import *
import requests
from dotenv import load_dotenv
import json

from apps.users.helpers.twilio_sending_message_helpers import send_text_message

# Create your views here.

load_dotenv()

class CheckUserPhoneNumber(APIView):

    def get(self, request):
        try:
            response = {"status": "success", "errorcode": "", "reason":"", "result": "", "httpstatus": status.HTTP_200_OK}

            phoneNo = request.query_params.get('ph')

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



class RegisterView(APIView):

    def post(self, request):
        try:
            response = {"status": "success", "errorcode": "","reason": "", "result": "", "httpstatus": HTTP_200_OK}
            __data = request.data.get('data')            
            
            print(__data.get('email'))
            
            CRM_REGISTER_URL = os.getenv("CRM_REGISTER_URL")
            # Headers for the external API
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            register_payload = {
                "email":__data.get('email'),
                "password":__data.get('password'),
                "firstName":__data.get('firstName'),
                "lastName":__data.get('lastName'),
                "telephone":__data.get('telephone'),
                "telephonePrefix":__data.get('telephonePrefix'),
                "countryIso":__data.get('countryIso'),
                "languageIso":__data.get('languageIso'),
            }
            response_data = requests.post(CRM_REGISTER_URL, json=register_payload, headers=headers)
            try:
                res_json = response_data.json()
            except Exception:
                res_json = {"raw_response": response_data.text}
            if res_json.get('success') == True:
                try:
                    record = RegistrationLog.objects.get(email=__data.get('email'))
                except RegistrationLog.DoesNotExist:
                    record = None
                if record:
                    log_update = {
                        'wpotpverified': __data.get('wpotpverified', record.wpotpverified),
                        'wpqrverified': __data.get('wpqrverified', record.wpqrverified),
                        'smsotpverified': __data.get('smsotpverified', record.smsotpverified),
                    }
                    serializer = RegistrationLogSerializer(record, data=log_update, partial=True)
                    if serializer.is_valid():
                        try:
                            serializer.save()
                            print("Record updated successfully")
                        except Exception as save_exception:
                            print(f"Error saving record: {save_exception}")
                    else:
                        print(f"Serializer validation errors: {serializer.errors}")
                else:
                    print("No record found with the provided email")
                    
                response['httpstatus'] = HTTP_200_OK
                response['status'] = "success"
                response['result'] = res_json.get('result')
            else:
                response["status"] = "error"
                response["reason"] = res_json.get('error')
                response["httpstatus"] = HTTP_400_BAD_REQUEST

            return JsonResponse(response, status=response['httpstatus'])
        except Exception as e:
            response["status"] = "error"
            response["reason"] = str(e)
            response["httpstatus"] = HTTP_400_BAD_REQUEST
            return JsonResponse(response, status=response['httpstatus'])

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



class ExtractDocumentData(APIView):

    def post(self, request):
        try:
            response = {"status": "success", "errorcode": "","reason": "", "result": "", "httpstatus": HTTP_200_OK}
            __data = request.data            
            print(__data)
            
            # CHECKING IF THE REQUEST MESSAGE IS VALID OR NOT            
            # postserializer = PostDataSerializer(data=__data)
            # if not postserializer.is_valid():
            #     response["status"] = "error"
            #     response["reason"] = str(postserializer.errors)
            #     response["httpstatus"] = HTTP_400_BAD_REQUEST
            # else:
            uploaded_file = request.FILES.get("file")
            if not uploaded_file:
                response["status"] = "error"
                response["reason"] = "No file provided in request."
                response["httpstatus"] = HTTP_400_BAD_REQUEST
                return JsonResponse(response, status=response["httpstatus"])

            # 2️⃣ Save to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                for chunk in uploaded_file.chunks():
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name

            # Optional: get document hint (e.g., PAN / AADHAAR)
            doc_hint = request.data.get("event", "")

            # 3️⃣ Call your helper function
            result = extract_from_image(tmp_path, doc_hint)

            # 4️⃣ Clean up
            if result.get('httpstatus')==200:
                result.get('result')['email'] = __data.get('email') 
                print(result)
                serializer = RegistrationLogSerializer(data=result.get('result'))
                if serializer.is_valid():
                    serializer.save()
            os.remove(tmp_path)

            # 5️⃣ Return result from helper
            return JsonResponse(result, status=result.get("httpstatus", HTTP_200_OK))
            
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