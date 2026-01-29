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
import uuid
from apps.dashboard_admin.models import WithdrawalApprovals

import tempfile
import os
from apps.users.helper.extractai import *
from apps.users.serializers import *
from apps.core.telegram_api import *
import requests
from dotenv import load_dotenv
import json

from apps.payment.constant.change_user_category_constant import *
from apps.users.helpers.twilio_sending_message_helpers import send_text_message, verify_otp, generate_and_send_otp, get_saved_otp
from apps.core.WebEngage import *
timestamp = current_webengage_time(offset_hours=-8)
# Create your views here.

load_dotenv()

CRM_PUT_USER = os.environ['CRM_PUT_USER']
CRM_AUTH_TOKEN = os.environ.get('CRM_AUTH_TOKEN')
CRM_PUT_KYC = os.environ.get('CRM_PUT_KYC')
TELEGRAM_SETTINGS = os.environ.get('TELEGRAM_SETTINGS')
settings_data = json.loads(TELEGRAM_SETTINGS)

teletram_ins = TelegramAPI()

import logging
import logging.config
from django.conf import settings
logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger('custom_logger')

class CheckUserPhoneNumber(APIView):

    def get(self, request):
        try:
            response = {"status": "success", "errorcode": "", "reason":"", "result": "", "httpstatus": status.HTTP_200_OK}
            phoneNo = request.query_params.get('ph')
            isCall = int(request.query_params.get('isCall',0))
            email = request.query_params.get('email')
            print(phoneNo,isCall,"------------------test")

            if not all([phoneNo]):
                response['status'] = 'error'
                response['errorcode'] = status.HTTP_400_BAD_REQUEST
                response['reason'] =  "Phone Number and Email are Required!!!"
                response['httpstatus'] = status.HTTP_400_BAD_REQUEST
                return Response(response, status=response.get('httpstatus'))

            res = send_text_message(phoneNo, isCall)

            if not res:
                emailRes = generate_and_send_otp(email)
                if not emailRes:
                    response['status'] = 'error'
                    response['errorcode'] = status.HTTP_400_BAD_REQUEST
                    response['reason'] = "OTP not sent!!!"
                    response['httpstatus'] = status.HTTP_400_BAD_REQUEST
                    return Response(response, status=response.get('httpstatus'))
                mssg = error_response(phoneNo, email, "Requested for registration!!!")
                teletram_ins.send_telegram_message(settings_data.get('convert_client_info_bot'), mssg)
                response['reason'] = "OTP sent on your Email ID!!!"
                return Response(response, status=response.get('httpstatus'))
            mssg = error_response(phoneNo, email, "Requested for registration!!!")
            teletram_ins.send_telegram_message(settings_data.get('convert_client_info_bot'), mssg)
            response['result'] = f"OTP Send Successfully on {phoneNo}"
            return Response(response, status=response.get('httpstatus'))

        except Exception as e:
            print(f"Error in the Validation User Phone Number: {str(e)}")
            response['status'] = 'error'
            response['errorcode'] = status.HTTP_400_BAD_REQUEST
            response['reason'] = str(e)
            response['httpstatus'] = status.HTTP_400_BAD_REQUEST
            phoneNo = request.query_params.get('ph')
            email = request.query_params.get('email')
            mssg = error_response(phoneNo, email, str(e))
            teletram_ins.send_telegram_message(settings_data.get('convert_client_info_bot'), mssg)
            return Response(response, status=response.get('httpstatus'))
        

class VerifyUserPhoneNumber(APIView):

    def post(self, request):
        try:
            response = {"status": "success", "errorcode": "", "reason": "", "result": "", "httpstatus": status.HTTP_200_OK}

            event = request.data.get('event')
            data = request.data.get('data')
            phoneNo = data.get('phoneNo')
            otp = data.get('otp')
            isCall = data.get('isCall', 0)
            email = data.get('email')

            if not all([phoneNo, otp, email]):
                response['status'] = 'error'
                response['errorcode'] = status.HTTP_400_BAD_REQUEST
                response['reason'] = "Phone No, OTP and Email are Required"
                response['httpstatus'] = status.HTTP_400_BAD_REQUEST
                return Response(response, status=response.get('httpstatus'))

            
            if event == "withdrawal-OTP":
                transId = data.get('transId')
                if not transId:
                    response['status'] = 'error'
                    response['errorcode'] = status.HTTP_400_BAD_REQUEST
                    response['reason'] = "Transaction ID is Required!!!"
                    response['httpstatus'] = status.HTTP_400_BAD_REQUEST
                    return Response(response, status=response.get('httpstatus'))
                
                try:
                    withObj = WithdrawalApprovals.objects.get(brokerBankingId=transId)
                except WithdrawalApprovals.DoesNotExist:
                    response = {
                        'status': 'error',
                        'errorcode': status.HTTP_400_BAD_REQUEST,
                        'reason': "Such Transaction Doesn't Exist!!!",
                        'httpstatus': status.HTTP_400_BAD_REQUEST
                    }
                    return Response(response, status=response['httpstatus'])
                
                res = verify_otp(phoneNo, otp, isCall)
                if res:
                    if not withObj.otpVerified:
                        withObj.otpVerified = True
                        withObj.save()
                        response['reason'] = "OTP Verified Successfully!!!!"
                        return Response(response, status=response.get('httpstatus'))
                    
                    response['reason'] = "Withdrawal Order Already Verified!!"
                    return Response(response, status=response.get('httpstatus'))
                
                
                response['status'] = 'error'
                response['errorcode'] = status.HTTP_400_BAD_REQUEST
                response['reason'] = "Invalid OTP!!!!"
                response['httpstatus'] = status.HTTP_400_BAD_REQUEST
                return Response(response, status=response.get('httpstatus'))
            
            res = verify_otp(phoneNo, otp, isCall)
            if res:
                mssg = error_response(phoneNo, email, "OTP Verified Successfully")
                teletram_ins.send_telegram_message(settings_data.get('convert_client_info_bot'), mssg)
                response['reason'] = "OTP Verified Successfully!!!!"
                return Response(response, status=response.get('httpstatus'))
            
            else:
                saved_otp = get_saved_otp(email)

                if not saved_otp:
                    response['reason'] = "Failed to Verify OTP!!!!"
                    response['status'] = 'error'
                    response['errorcode'] = status.HTTP_400_BAD_REQUEST
                    response['httpstatus'] = status.HTTP_400_BAD_REQUEST
                    return Response(response, status=response.get('httpstatus'))


                if int(saved_otp) == int(otp):
                    mssg = error_response(phoneNo, email, "OTP Verified Successfully")
                    teletram_ins.send_telegram_message(settings_data.get('convert_client_info_bot'), mssg)
                    response['reason'] = "OTP Verified Successfully!!!!"
                    return Response(response, status=response.get('httpstatus'))

            response['status'] = 'error'
            response['errorcode'] = status.HTTP_400_BAD_REQUEST
            response['reason'] = "Invalid OTP!!!!"
            response['httpstatus'] = status.HTTP_400_BAD_REQUEST
            
            mssg = error_response(phoneNo, email, "Entered Invalid OTP")
            teletram_ins.send_telegram_message(settings_data.get('convert_client_info_bot'), mssg)
            return Response(response, status=response.get('httpstatus'))

        except Exception as e:
            print(f"Error in Verifing the Phone OTP: {str(e)}")
            response['status'] = 'error'
            response['errorcode'] = status.HTTP_400_BAD_REQUEST
            response['reason'] = str(e)
            response['httpstatus'] = status.HTTP_400_BAD_REQUEST
            data = request.data.get('data')
            phoneNo = data.get('phoneNo')
            email = data.get('email')
            mssg = error_response(phoneNo, email, str(e))
            teletram_ins.send_telegram_message(settings_data.get('convert_client_info_bot'), mssg)
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

            print("data --- ", __data)
            response_data = requests.post(CRM_REGISTER_URL, json=__data, headers=headers)
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
                            
                            location = {
                                "country": __data.get('countryIso',''),
                                "city": __data.get('city',''),
                                "region": __data.get('state',''),
                                "locality": __data.get('full_address',''),
                                "postalCode": __data.get('zip',''),
                            }
                            try:
                                wbres = upsert_user(
                                    user_id=__data.get('email'),
                                    first_name=__data.get('firstName'),
                                    last_name=__data.get('lastName'),
                                    email=__data.get('email'),
                                    phone=str(__data.get('telephonePrefix'))+str(__data.get('telephone')),
                                    location=location
                                )
                                if (wbres or {}).get('response', {}).get('status') == 'queued':
                                    print("data has been saved in wbres -----------")
                                else:
                                    print("something went wrong in wbres")

                                wbregres = registration_completed(
                                    user_id=__data.get('email'),
                                    source=__data.get('registrationDeviceType'),
                                    timestamp=timestamp
                                    )
                                if (wbregres or {}).get('response', {}).get('status') == 'queued':
                                    print("data has been saved in wbregres -----------")
                                else:
                                    print("something went wrong in wbregres")
                            except Exception as e:
                                print("WB upsert failed", e)

                            
                            serializer.save()
                            mssg = error_response(__data.get('telephone'), __data.get('email'), "Registered Successfully!!!")
                            teletram_ins.send_telegram_message(settings_data.get('convert_client_info_bot'), mssg)
                            print("Record updated successfully")
                        except Exception as save_exception:
                            print(f"Error saving record: {save_exception}")
                            wbregres = registration_failed(user_id=__data.get('email'),failure_reason= str(save_exception),timestamp=timestamp)
                            if (wbregres or {}).get('response', {}).get('status') == 'queued':
                                print("data has been saved in wbregres -----------")
                            else:
                                print("something went wrong in wbregres")
                    else:
                        print(f"Serializer validation errors: {serializer.errors}")
                        wbregres = registration_failed(user_id=__data.get('email'),failure_reason= str(serializer.errors),timestamp=timestamp)
                        if (wbregres or {}).get('response', {}).get('status') == 'queued':
                            print("data has been saved in wbregres -----------")
                        else:
                            print("something went wrong in wbregres")
                else:
                    print("No record found with the provided email")
                    wbregres = registration_failed(user_id=__data.get('email'),failure_reason= "No record found with the provided email",timestamp=timestamp)
                    if (wbregres or {}).get('response', {}).get('status') == 'queued':
                        print("data has been saved in wbregres -----------")
                    else:
                        print("something went wrong in wbregres")
                    
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
            __data = request.data.get('data')  
            mssg = error_response(__data.get('email'), __data.get('telephone'), str(e))
            teletram_ins.send_telegram_message(settings_data.get('convert_client_info_bot'), mssg)
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
                    response['result'] = "Email Does not Exist!!!"
            
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
                    print("=============== data saved ===================")
                else:
                    print(serializer.errors)
            os.remove(tmp_path)

            # 5️⃣ Return result from helper
            return JsonResponse(result, status=result.get("httpstatus", HTTP_200_OK))
            
            return JsonResponse(response, status=response['httpstatus'])
        except Exception as e:
            response["status"] = "error"
            response["reason"] = str(e)
            response["httpstatus"] = HTTP_400_BAD_REQUEST
            return JsonResponse(response, status=response['httpstatus'])


class ChangeRegulation(APIView):
    def post(self, request):
        try:
            response = {"status": "success", "errorcode": "","reason": "", "result": "", "httpstatus": HTTP_200_OK}
            __data = request.data            
            ref_link = request.headers.get("Ref-Link", "")

            # print("HEADER UUID:", repr(clean_uuid))

            try:
                query = f"""
                        SELECT bu.username, bu.first_name, bu.last_name, bu.external_id  FROM crmdb.broker_user AS bu where bu.user_id ={request.session_user}
                    """
                new_user_data = DBConnection._forFetchingJson(query, using='replica')


                clean_uuid = str(uuid.UUID(ref_link))
                user_obj = ChangeReguslationLog.objects.get(uuid=clean_uuid)
                query = f"""
                        SELECT bu.username, bu.first_name, bu.last_name, bu.external_id  FROM crmdb.broker_user AS bu where bu.username ={user_obj.old_email}
                    """
                old_user_data = DBConnection._forFetchingJson(query, using='replica')
                
                mssg = create_client_message(old_user_data, new_user_data)
                teletram_ins.send_telegram_message(settings_data.get('convert_client_info_bot'), mssg)

                print("FOUND OBJECT:", user_obj)
                if user_obj.old_email:
                    userid =  request.session_user
                    payload = {
                                    "registrationAppId": "1",
                                    "id": userid
                                }
                    headers = {
                                    "Content-Type": "application/json",
                                    "x-crm-api-token": str(CRM_AUTH_TOKEN)
                                }
                    resp = requests.put(CRM_PUT_USER, json=payload, headers=headers).json()
                    if resp['success']:
                        response['httpstatus'] = HTTP_200_OK
                        response['status'] = "success"
                        response['result'] = f"{request.session_user} is shifted to the MU regulation!!"
                    else:
                        response['httpstatus'] = HTTP_200_OK
                        response['status'] = "success"
                        response['result'] = f"Something went wrong!!!!!"
                    
            except ChangeReguslationLog.DoesNotExist:
                print("NO OBJECT FOUND")

                # if link_data:
                # else:
            
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


class VisitView(APIView):
    def get(self, request):
        try:
            response = {"status": "success", "errorcode": "","reason": "", "result": "", "httpstatus": HTTP_200_OK}
            affid = request.GET.get("affid")
            p6 = request.GET.get("p6")   

            
            query =f"""
                select v.creation_time, v.id from affiliate a left join visit v on a.id=v.affiliate_id where a.external_id ={affid} order by creation_time desc limit 1
            """
            print("query", query)

            data = DBConnection._forFetchingJson(query, using='replica')
            print("data", data)
             
            
            if not data or len(data) == 0:
                response["status"] = "error"
                response["reason"] = "No visitor found!!"
                response["httpstatus"] = 404
            else:
                response['httpstatus'] = HTTP_200_OK
                response['status'] = "success"
                response['result'] = data[0].get("id")   

            
            return JsonResponse(response, status=response['httpstatus'])
        except Exception as e:
            response["status"] = "error"
            response["reason"] = str(e)
            response["httpstatus"] = 500
            return JsonResponse(response, status=response['httpstatus'])
        

  
# class User_Regulation_Error_Logs(APIView): 

#     def post(self, request):
#         try:
#             response = {"status": "success", "errorcode": "", "result": "", "reason": "", "httpstatus": status.HTTP_200_OK}

class User_Regulation_Error_Logs(APIView): 

    def post(self, request):
        try:
            response = {"status": "success", "errorcode": "", "result": "", "reason": "", "httpstatus": status.HTTP_200_OK}

            data = request.data.get('data')

            if not data:
                logger.error(f"Error Regulation Data not Found!!!")
                response['status'] = 'error'
                response['reason'] = "Regulation Data not found!!!"
                return Response(response, status=response.get('httpstatus'))
            

            logger.error(f"Regulation Data: {data}")
            return Response(response, status=response.get('httpstatus'))

        except Exception as e:
            logger.error(f"Error in User Regulation: {str(e)}", exc_info=True)
            response['status'] = 'error'
            response['errorcode'] = status.HTTP_400_BAD_REQUEST
            response['reason'] = str(e)
            response['httpstatus'] = status.HTTP_400_BAD_REQUEST
            return Response(response, status=response.get('httpstatus'))
class KYCStatusView(APIView):
    def post(self, request):
        try:
            response = {"status": "success", "errorcode": "","reason": "", "result": "", "httpstatus": HTTP_200_OK}
            # __data = request.data    
            user_id = request.session_user
            if not user_id:
                response['status'] = 'error'
                response['errorcode'] = status.HTTP_400_BAD_REQUEST
                response['reason'] = "User Not Found!!!"
                response['httpstatus'] = status.HTTP_400_BAD_REQUEST
                return Response(response, status=response.get('httpstatus'))
            
            query =f"""
                        SELECT u.full_name, u.email FROM crmdb.users AS u where u.id = {user_id}
                    """
            data = DBConnection._forFetchingJson(query, using='replica')
            if not data:
                response['status'] = 'error'
                response['errorcode'] = status.HTTP_400_BAD_REQUEST
                response['reason'] = "Unable to fetch user details from the MySQL Database!!"
                response['httpstatus'] = status.HTTP_400_BAD_REQUEST
                return Response(response, status=response.get('httpstatus'))
            
            full_name = data[0].get('full_name', "None")
            email = data[0].get('email', "None")
            print(email)
        except Exception as e:
            response["status"] = "error"
            response["reason"] = str(e)
            response["httpstatus"] = HTTP_400_BAD_REQUEST
            return JsonResponse(response, status=response['httpstatus'])
            return Response(response, status=response.get('httpstatus'))
