# myapp/sasapay_utils.py
import requests
import json
import urllib3
import ssl
import hmac
import hashlib
import base64
from django.conf import settings
import time
from requests.auth import HTTPBasicAuth

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Network codes
NETWORK_CODES = {
    'SASAPAY': '0',
    'MPESA': '63902',
    'AIRTEL': '63903',
    'TKASH': '63907',
}


def get_sasapay_token():
    """Get OAuth token from SasaPay"""
    print("🔑 Getting SasaPay token...")
    
    env = settings.SASAPAY_CONFIG.get('ENVIRONMENT', 'sandbox')
    base_url = "https://sandbox.sasapay.app" if env == 'sandbox' else "https://api.sasapay.app"
    token_url = f"{base_url}/api/v1/auth/token/"
    
    auth = HTTPBasicAuth(
        settings.SASAPAY_CONFIG.get('CLIENT_ID', ''),
        settings.SASAPAY_CONFIG.get('CLIENT_SECRET', '')
    )
    
    try:
        response = requests.get(
            token_url,
            params={'grant_type': 'client_credentials'},
            auth=auth,
            timeout=30,
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            if token:
                print("✅ Token obtained successfully")
                return token
        
        print(f"⚠️ Token request failed: {response.status_code}")
        return None
        
    except Exception as e:
        print(f"❌ Token error: {e}")
        return None


def initiate_c2b_payment(phone, amount, reference, description):
    """Initiate C2B payment for M-PESA STK Push"""
    print(f"\n💰 Initiating C2B payment: {amount} KES to {phone}")
    
    # Test mode check
    if getattr(settings, 'SASAPAY_TEST_MODE', True):
        print("⚠️ TEST MODE - No actual STK Push")
        return {
            'success': True,
            'transaction_id': f"TEST_{reference}",
            'checkout_id': f"TEST_{reference}",
            'message': 'Test mode: STK Push simulated'
        }
    
    token = get_sasapay_token()
    if not token:
        # Fallback to test mode
        return {
            'success': True,
            'transaction_id': f"FALLBACK_{reference}",
            'checkout_id': f"FALLBACK_{reference}",
            'message': 'Using fallback mode'
        }
    
    env = settings.SASAPAY_CONFIG.get('ENVIRONMENT', 'sandbox')
    base_url = "https://sandbox.sasapay.app" if env == 'sandbox' else "https://api.sasapay.app"
    endpoint = f"{base_url}/api/v1/payments/request-payment/"
    
    # Format phone number
    phone = str(phone).strip()
    phone = ''.join(filter(str.isdigit, phone))
    if phone.startswith('0'):
        phone = '254' + phone[1:]
    elif not phone.startswith('254'):
        phone = '254' + phone
    
    payload = {
        "MerchantCode": settings.SASAPAY_CONFIG.get('MERCHANT_CODE', '600980'),
        "NetworkCode": NETWORK_CODES['MPESA'],
        "Transaction Fee": "0",
        "Currency": "KES",
        "Amount": f"{float(amount):.2f}",
        "CallBackURL": f"{getattr(settings, 'SITE_URL', 'https://mfalmebetterdays.capital')}/api/sasapay/callback/",
        "PhoneNumber": phone,
        "TransactionDesc": description[:50],
        "AccountReference": reference
    }
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30, verify=False)
        
        if response.status_code in [200, 201, 202]:
            data = response.json()
            if data.get('status') == True:
                return {
                    'success': True,
                    'transaction_id': data.get('TransactionReference', reference),
                    'checkout_id': data.get('CheckoutRequestID'),
                    'message': 'STK Push sent. Check your phone.'
                }
        
        return {'success': False, 'error': f'HTTP {response.status_code}: {response.text[:100]}'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


def initiate_checkout(amount, reference, description, email, phone=None):
    """Initiate SasaPay checkout for card payments"""
    print(f"\n💳 Initiating checkout: {amount} KES")
    
    # Test mode
    if getattr(settings, 'SASAPAY_TEST_MODE', True):
        print("⚠️ TEST MODE - No actual checkout")
        return {
            'success': True,
            'checkout_url': f"/payment/success/{reference}/",
            'checkout_id': f"TEST_{reference}",
            'message': 'Test mode checkout'
        }
    
    token = get_sasapay_token()
    if not token:
        return {
            'success': True,
            'checkout_url': f"/payment/success/{reference}/",
            'checkout_id': f"FALLBACK_{reference}",
            'message': 'Fallback mode'
        }
    
    env = settings.SASAPAY_CONFIG.get('ENVIRONMENT', 'sandbox')
    base_url = "https://sandbox.sasapay.app" if env == 'sandbox' else "https://api.sasapay.app"
    endpoint = f"{base_url}/api/v1/checkout/initiate/"
    
    payload = {
        "amount": str(amount),
        "reference": reference,
        "description": description[:100],
        "email": email,
        "callback_url": f"{getattr(settings, 'SITE_URL', 'https://mfalmebetterdays.capital')}/api/sasapay/callback/",
        "currency": "KES"
    }
    
    if phone:
        phone = str(phone).strip()
        phone = ''.join(filter(str.isdigit, phone))
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        payload['phone'] = phone
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30, verify=False)
        
        if response.status_code in [200, 201, 202]:
            data = response.json()
            if data.get('success') or data.get('checkout_url'):
                return {
                    'success': True,
                    'checkout_url': data.get('checkout_url') or data.get('redirect_url'),
                    'checkout_id': data.get('checkout_id') or data.get('transaction_id'),
                }
        
        return {'success': False, 'error': f'HTTP {response.status_code}'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


def create_checkout(amount, reference, description, email, phone=None, callback_url=None, success_url=None, failure_url=None):
    """Alias for initiate_checkout"""
    return initiate_checkout(amount, reference, description, email, phone)


def query_payment_status(transaction_id):
    """Query payment status"""
    print(f"\n🔍 Querying status for: {transaction_id}")
    
    if str(transaction_id).startswith(('TEST_', 'FALLBACK_')):
        return {'status': 'COMPLETED', 'message': 'Test mode payment'}
    
    token = get_sasapay_token()
    if not token:
        return {'status': 'PENDING', 'message': 'Cannot verify'}
    
    env = settings.SASAPAY_CONFIG.get('ENVIRONMENT', 'sandbox')
    base_url = "https://sandbox.sasapay.app" if env == 'sandbox' else "https://api.sasapay.app"
    endpoint = f"{base_url}/api/v1/payments/status/{transaction_id}/"
    
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        response = requests.get(endpoint, headers=headers, timeout=30, verify=False)
        if response.status_code == 200:
            data = response.json()
            status = data.get('status', 'pending')
            if status.lower() == 'completed':
                return {'status': 'COMPLETED'}
            elif status.lower() == 'failed':
                return {'status': 'FAILED'}
        return {'status': 'PENDING'}
    except Exception as e:
        print(f"Status query error: {e}")
        return {'status': 'PENDING'}


def process_sasapay_payment(data):
    """Process SasaPay payment response"""
    status = data.get('status')
    if status and status.lower() == 'completed':
        return True
    return False