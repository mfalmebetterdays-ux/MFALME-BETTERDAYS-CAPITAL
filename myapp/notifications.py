import json
import requests
from django.http.response import JsonResponse
from django.core.mail import send_mail
from django.conf import settings

def sendsms(tel_no,message):
    print("sms to be sent to ",tel_no)
     
    url = 'https://portal.zettatel.com/SMSApi/send'
    
    try:
              
                
                #print(tel_no)
        payload = {
                "userid": "mfalme",
                "password": "Mfalme123",
                "senderid": "MFALME",
                "msgType": "text",
                "duplicatecheck": "true",
                "sendMethod": "quick",
                "sms": [
                    {
                        "mobile": [tel_no],
                        "msg": message
                    }
            
                ]
                }

        
        json_payload = json.dumps(payload)

        headers = {'Content-Type': 'application/json'}

        response = requests.post(url, headers=headers, data=json_payload)
    except:
        print("SMS not send :Error :{e}")

def sendproductsms(tel_no, product_names):
    print("sendproducts called")
    print(tel_no)
    product_list_str = ', '.join(product_names)
    print(product_list_str)
    message = f"Your payment for the following items has been received: {product_list_str}. Thank you for shopping with mfalmebetterdays!"
    sendsms(tel_no, message)
    message = f"The payment for the following items has been paid for by this phone :{tel_no}: {product_list_str}."
    sendsms(254706286667, message)

def sendemailuser(email,message):
    try:
        subject = 'Thank you'
        
  
        from_email = settings.EMAIL_HOST_USER 
        recipient_list = [email]
        send_mail(subject, message, from_email, recipient_list)
    except:
        print('email not sent Error :{e}')



def sendproductsemail(email,product_names):
    product_list_str = ', '.join(product_names)
    message = f"Your payment for the following items has been received: {product_list_str}. Thank you for shopping with us!"
    sendemailuser(email, message)
    message = f"The payment for the following items has been paid for by this email :{email}: {product_list_str}."
    sendemailuser('info@mfalmebetterdayscapital.com', message)
    

