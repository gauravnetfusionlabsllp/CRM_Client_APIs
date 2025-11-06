from twilio.rest import Client
import os

from dotenv import load_dotenv
load_dotenv()


account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
client = Client(account_sid, auth_token)

def send_text_message(phoneNo):
    try:
        message = client.messages(
            body = "This is Testing Message!!!",
            from_ = "",
            to = ""
        )

        print(message, "--------------------150")

        if not message:
            return False

        return True
    
    except Exception as e:
        print(f"Error in Sending message from the Twilio: {str(e)}")
        return False