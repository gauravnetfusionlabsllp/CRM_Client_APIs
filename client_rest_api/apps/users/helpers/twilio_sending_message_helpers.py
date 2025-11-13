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

        client = Client(account_sid, auth_token)

        verify = client.verify.v2.services("VAff903484b83a2edd030385728bb3d467").verifications.create(
            to=formatNo,
            channel="sms"
        )
 
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

        if not check.valid:
            return False
        
        return True
    
    except Exception as e:
        print(f"Error in Verifing OTP from the Twilio: {str(e)}")
        return False