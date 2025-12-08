import json
import requests


def sendsms():
     
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
                        "mobile": [254799778177],
                        "msg": 'We have received your payment of 1 tickets.Download  your ticket here https://www.mfalmebetterdayscapital.com/download_ticket/517'
                    }
            
                ]
                }

        
        json_payload = json.dumps(payload)

        headers = {'Content-Type': 'application/json'}

        response = requests.post(url, headers=headers, data=json_payload)
        print(response.text)
    except:
        print("SMS not send :Error :{e}")

sendsms()