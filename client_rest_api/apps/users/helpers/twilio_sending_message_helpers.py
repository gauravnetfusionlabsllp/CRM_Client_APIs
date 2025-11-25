from twilio.rest import Client
import os
import random
from django.core.cache import cache
from dotenv import load_dotenv
load_dotenv()

from datetime import date

current_year = date.today().year

import smtplib
from email.message import EmailMessage
import os


account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']

def send_text_message(phoneNo, isCall):
    try:
        formatNo = str("+"+phoneNo).replace(" ","") 

        client = Client(account_sid, auth_token)

        if isCall:
            verify = client.verify.v2.services("VA8de15e0183a4ecb62cac8aa573591155").verifications.create(
                to=formatNo,
                channel="call",
                locale="en"
            )
        else:
            verify = client.verify.v2.services("VAff903484b83a2edd030385728bb3d467").verifications.create(
                to=formatNo,
                channel="sms",
            )
 
        if not verify:
            return False

        return True
    
    except Exception as e:
        print(f"Error in Sending message from the Twilio: {str(e)}")
        return False
    

def verify_otp(phoneNo, otp, isCall):
    try:
        formatNo = str("+"+phoneNo).replace(" ","")
        client = Client(account_sid, auth_token)
        

        if isCall:
            check = client.verify.v2.services("VA8de15e0183a4ecb62cac8aa573591155").verification_checks.create(
                to=formatNo, 
                code=int(otp)
            )
        else:
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
    



def generate_and_send_otp(email):
    try:
        otp = str(random.randint(100000, 999999))  # 6-digit OTP
        cache.set(f"otp_{email}", otp, timeout=600)  # Store for 5 mins
        
        msg = EmailMessage()
        msg['Subject'] = 'Your OTP Code'
        msg['From'] = os.environ.get('OUTLOOK_EMAIL')
        msg['To'] = email
        html_message = f'''<!DOCTYPE html>
                        <html lang="en">
                        <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <title>SGFX | OTP Verification</title>
                        </head>

                        <body style="margin:0;padding:0;background-color:#f3f4f6;font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#111827;">
                        <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
                            <tr>
                            <td align="center" style="padding:30px 10px;background:#f3f4f6;">
                                <table width="600" cellpadding="0" cellspacing="0" style="border-collapse:collapse;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 6px 20px rgba(0,0,0,0.08);">
                                
                                <!-- Header -->
                                <tr>
                                    <td align="center" style="background:linear-gradient(135deg,#2563eb,#7c3aed);padding:30px 20px;color:#ffffff;">
                                    <img src="https://res.cloudinary.com/dwry2erxf/image/upload/v1758530048/SGFX_logo_sgurnj.png" alt="{{APP_NAME}} Logo" width="80" style="display:block;margin-bottom:12px;">
                                    </td>
                                </tr>

                                <!-- Body -->
                                <tr>
                                    <td align="center" style="padding:30px 25px;text-align:center;">
                                    <h2 style="font-size:22px;font-weight:700;color:#111827;margin-bottom:12px;">Verify Your Identity</h2>
                                    <p style="font-size:16px;line-height:1.6;color:#4b5563;margin-bottom:20px;">
                                        We’ve generated a one-time password OTP for your verification. Please use the code below to continue. This code is valid for <strong>5 minutes</strong>.
                                    </p>

                                    <div style="display:inline-block;background:#f9fafb;border:2px dashed #dbeafe;border-radius:10px;padding:18px 28px;font-size:32px;font-weight:700;letter-spacing:6px;color:#1e3a8a;margin-bottom:18px;">
                                        OTP_CODE
                                    </div>


                                    <p style="font-size:14px;color:#6b7280;margin-top:18px;">
                                        Didn’t request this code? You can safely ignore this email or contact us at 
                                        <a href="mailto:sgfx@gmail.com" style="color:#2563eb;">Support@sgfx.com</a>.
                                    </p>
                                    </td>
                                </tr>

                                <!-- Footer -->
                                <tr>
                                    <td align="center" style="background:#f9fafb;padding:20px;text-align:center;font-size:13px;color:#9ca3af;">
                                    <p>© <span id="year">{current_year}</span> SGFX. All rights reserved.</p>
                                    <p>You received this email because you attempted to sign in or verify your account.</p>
                                    </td>
                                </tr>

                                </table>
                            </td>
                            </tr>
                        </table>
                        </body>
                        </html>'''
       
        # msg.set_content(f"Your OTP code is {otp}. It is valid for 30 minutes.") 
        msg.add_alternative(html_message.replace(('OTP_CODE'), otp), subtype='html')
        
        with smtplib.SMTP('smtp.office365.com', 587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(os.environ.get('OUTLOOK_EMAIL'), os.environ.get('OUTLOOK_PASSWORD'))
            smtp.send_message(msg)
            print("Email ")
        return True
    
    except Exception as e:
        print(f"Error in the Generating and Sending OTP: {str(e)}")
        return False