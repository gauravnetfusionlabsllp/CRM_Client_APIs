from twilio.rest import Client
import os
import random
from django.core.cache import cache
from dotenv import load_dotenv
load_dotenv()


account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']

def send_text_message(phoneNo):
    try:
        formatNo = str("+"+phoneNo).replace(" ","")

        otp = str(random.randint(100000, 999999))
        cache.set(f"otp_{phoneNo}", otp, timeout=300)

        client = Client(account_sid, auth_token)

        verify = client.verify.v2.services("VAff903484b83a2edd030385728bb3d467").verifications.create(
            to=formatNo,
            channel="sms"
        )

        # message = client.messages.create(
        #     body = f"verify OTP!!! {otp}",
        #     from_ = "+18203007188",
        #     to = formatNo
        # )

        # print(message, "--------------------150")

        if not verify:
            return False

        return True
    
    except Exception as e:
        print(f"Error in Sending message from the Twilio: {str(e)}")
        return False
    

def verify_otp(phoneNo, otp):
    try:
        formatNo = str("+"+phoneNo).replace(" ","")
        client = Client(account_sid, auth_token)
        

        check = client.verify.v2.services("VAff903484b83a2edd030385728bb3d467").verification_checks.create(
            to=formatNo, 
            code=int(otp)
        )

        print(check.status,"----------------------")
        if not check:
            return False
        
        return True
    
    except Exception as e:
        print(f"Error in Verifing OTP from the Twilio: {str(e)}")
        return False