# myapp/sasapay_utils.py
import requests
import json
import urllib3
import ssl
from django.conf import settings
import time
import socket
from requests.auth import HTTPBasicAuth

# Completely disable ALL SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
requests.packages.urllib3.disable_warnings()

# CRITICAL: Override SSL context globally
try:
    _create_unverified_https_context = ssl._create_unverified_context
    ssl._create_default_https_context = _create_unverified_https_context
except:
    pass

# Create a completely permissive session
class UltraPermissiveSession(requests.Session):
    def __init__(self):
        super().__init__()
        adapter = UltraPermissiveHTTPAdapter()
        self.mount('https://', adapter)
        self.mount('http://', adapter)

class UltraPermissiveHTTPAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        kwargs.pop('pool_block', None)
        kwargs.pop('key_pool_block', None)
        
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        try:
            context.minimum_version = ssl.TLSVersion.TLSv1_2
        except:
            pass
            
        kwargs['ssl_context'] = context
        kwargs['assert_hostname'] = False
        kwargs['cert_reqs'] = 'CERT_NONE'
        kwargs['retries'] = 3
        
        return super().init_poolmanager(*args, **kwargs)
    
    def proxy_manager_for(self, *args, **kwargs):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        kwargs['ssl_context'] = context
        kwargs['assert_hostname'] = False
        return super().proxy_manager_for(*args, **kwargs)

# Create global ultra-permissive session
ultra_session = UltraPermissiveSession()

# Network codes from documentation
NETWORK_CODES = {
    'SASAPAY': '0',
    'MPESA': '63902',
    'AIRTEL': '63903',
    'TKASH': '63907',
}

def get_sasapay_token():
    """Get OAuth token from SasaPay - Using OFFICIAL documentation"""
    
    print("🔑 Requesting SasaPay token using official API...")
    
    env = settings.SASAPAY_CONFIG.get('ENVIRONMENT', 'sandbox')
    print(f"📌 Current environment: {env}")
    
    if env == 'sandbox':
        base_url = "https://sandbox.sasapay.app"
    else:
        base_url = "https://api.sasapay.app"
    
    # Token endpoint with grant_type as query param (as per docs)
    token_url = f"{base_url}/api/v1/auth/token/"
    params = {'grant_type': 'client_credentials'}
    
    auth = HTTPBasicAuth(
        settings.SASAPAY_CONFIG['CLIENT_ID'],
        settings.SASAPAY_CONFIG['CLIENT_SECRET']
    )
    
    headers = {
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (compatible; MfalmeBot/1.0)',
    }
    
    print(f"🔄 Trying: {token_url}")
    
    try:
        response = ultra_session.get(
            token_url,
            params=params,
            auth=auth,
            headers=headers,
            timeout=30,
            verify=False
        )
        
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Response: status={data.get('status')}, detail={data.get('detail')}")
            
            access_token = data.get('access_token')
            if access_token:
                print(f"✅ SUCCESS! Token obtained")
                print(f"🔑 Token: {access_token[:20]}...")
                print(f"⏱️ Expires in: {data.get('expires_in')} seconds")
                print(f"📋 Scope: {data.get('scope')}")
                return access_token
            else:
                print(f"⚠️ No token in response: {data}")
        else:
            print(f"❌ HTTP {response.status_code}: {response.text[:200]}")
            
    except Exception as e:
        print(f"⚠️ Failed: {type(e).__name__} - {str(e)[:100]}")
    
    if settings.DEBUG:
        print("⚠️ Using MOCK token for development")
        return "mock_token_for_development"
    
    raise Exception("SasaPay connection failed. Please try Paystack instead.")

def initiate_c2b_payment(phone, amount, reference, description):
    """Initiate C2B payment for M-PESA/Airtel/T-Kash - Using OFFICIAL documentation"""
    
    print(f"💰 Initiating C2B payment: {amount} KES to {phone}")
    
    try:
        token = get_sasapay_token()
        
        env = settings.SASAPAY_CONFIG.get('ENVIRONMENT', 'sandbox')
        
        if env == 'sandbox':
            base_url = "https://sandbox.sasapay.app"
        else:
            base_url = "https://api.sasapay.app"
        
        # CORRECT ENDPOINT from documentation
        endpoint = f"{base_url}/api/v1/payments/request-payment/"
        
        # Format phone number
        phone = str(phone).strip()
        phone = ''.join(filter(str.isdigit, phone))
        
        # Convert to 254 format
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        elif phone.startswith('7') and len(phone) == 9:
            phone = '254' + phone
        elif phone.startswith('+254'):
            phone = phone[1:]
        
        # Default to M-PESA (most common)
        network_code = NETWORK_CODES['MPESA']
        
        # Try to detect network (optional)
        if phone.startswith('2547') or phone.startswith('2541'):
            network_code = NETWORK_CODES['MPESA']
        elif phone.startswith('2540'):
            network_code = NETWORK_CODES['SASAPAY']
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        # CORRECT PAYLOAD from documentation
        payload = {
            "MerchantCode": settings.SASAPAY_CONFIG.get('MERCHANT_CODE', '600980'),  # Get from settings
            "NetworkCode": network_code,
            "Transaction Fee": "0",
            "Currency": "KES",
            "Amount": f"{float(amount):.2f}",
            "CallBackURL": settings.SASAPAY_CONFIG.get('CALLBACK_URL'),
            "PhoneNumber": phone,
            "TransactionDesc": description[:50],
            "AccountReference": reference
        }
        
        print(f"📦 Sending to: {endpoint}")
        print(f"📦 Payload: {json.dumps(payload, indent=2)}")
        
        try:
            response = ultra_session.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=30,
                verify=False
            )
            
            print(f"📡 Response Status: {response.status_code}")
            
            if response.status_code in [200, 201, 202]:
                data = response.json()
                print(f"📊 Response data: {json.dumps(data, indent=2)}")
                
                if data.get('status') == True:
                    # Extract IDs as per documentation
                    return {
                        'success': True,
                        'transaction_id': data.get('TransactionReference', reference),
                        'checkout_id': data.get('CheckoutRequestID'),
                        'merchant_request_id': data.get('MerchantRequestID'),
                        'message': data.get('detail', 'STK Push sent. Check your phone.'),
                        'payment_gateway': data.get('PaymentGateway'),
                        'customer_message': data.get('CustomerMessage', '')
                    }
                else:
                    return {
                        'success': False,
                        'error': data.get('detail', 'Payment failed')
                    }
            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', error_msg)
                except:
                    error_msg = response.text[:200]
                    
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Connection error: {str(e)[:100]}'
            }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def process_sasapay_payment(checkout_request_id, merchant_code, verification_code):
    """Process payment with OTP for SasaPay users"""
    
    print(f"🔐 Processing SasaPay payment with OTP")
    
    try:
        token = get_sasapay_token()
        
        env = settings.SASAPAY_CONFIG.get('ENVIRONMENT', 'sandbox')
        
        if env == 'sandbox':
            base_url = "https://sandbox.sasapay.app"
        else:
            base_url = "https://api.sasapay.app"
        
        endpoint = f"{base_url}/api/v1/payments/process-payment/"
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        payload = {
            "CheckoutRequestID": checkout_request_id,
            "MerchantCode": merchant_code,
            "VerificationCode": verification_code
        }
        
        response = ultra_session.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=30,
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                'success': data.get('status', False),
                'message': data.get('detail', 'Transaction processed')
            }
        else:
            return {
                'success': False,
                'error': f"HTTP {response.status_code}"
            }
            
    except Exception as e:
        return {'success': False, 'error': str(e)}

def query_payment_status(transaction_id):
    """Query payment status - Note: Documentation doesn't specify status endpoint"""
    
    # For now, we'll rely on callbacks
    print(f"ℹ️ Payment status should be received via callback URL")
    print(f"📞 Callback URL: {settings.SASAPAY_CONFIG.get('CALLBACK_URL')}")
    
    return {
        'status': 'PENDING',
        'message': 'Check callback for status updates'
    }